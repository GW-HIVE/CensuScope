#!/usr/bin/env python3
"""Launch build_reference_data.sh or grid_search.sh and log system load while it runs.

Every --interval seconds this records:
  - work in flight: running CensuScope containers (by Docker label) and
    host-visible blastn / makeblastdb / sqlite3 / curl processes
  - CPU: busy % and iowait % since the last sample, load average
  - RAM: used / total, swap used
  - pressure stall info (PSI) for CPU, memory, and IO, if the kernel has it

Outputs, in --logdir (default ./run_logs), all named <script>_<stamp>.*:
  .out           the script's own stdout/stderr
  .metrics.tsv   one row per sample (for plotting)
  .monitor.log   human-readable samples, warnings, and an end-of-run summary

Examples:
  ./run_monitored.py build -- --dry-run
  ./run_monitored.py build -- slimNT filtered_nt
  ./run_monitored.py --interval 30 grid -- -q inputs/reads.fa \\
      -d ../databases/output/slimNT/slimNT -s 100,1000 -i 5,10 -j 4

Detached:
  nohup ./run_monitored.py grid -- ... > /dev/null 2>&1 &
  kill "$(cat run_logs/run_monitored.pid)"   # stops the script and its containers

Uses only the Python standard library and Linux /proc.
"""

import argparse
import datetime as dt
import os
import signal
import subprocess
import sys
import time

REPO_DIR = os.path.dirname(os.path.abspath(__file__))

SCRIPTS = {
    "build": ("build_reference_data.sh", "censuscope-build"),
    "grid": ("grid_search.sh", "censuscope-grid"),
}

WATCHED_PROCS = ("blastn", "makeblastdb", "sqlite3", "curl")

# Thresholds that produce a WARNING line in the monitor log.
WARN_MEM_PCT = 90.0
WARN_SWAP_GB = 1.0
WARN_PSI_MEM_FULL = 5.0

COLUMNS = (
    ["timestamp", "elapsed_s", "containers"]
    + list(WATCHED_PROCS)
    + [
        "cpu_busy_pct", "cpu_iowait_pct", "load1", "load5", "ncpu",
        "mem_used_gb", "mem_total_gb", "mem_used_pct", "swap_used_gb",
        "psi_cpu_some10", "psi_mem_some10", "psi_mem_full10", "psi_io_some10",
    ]
)


# ── /proc readers ─────────────────────────────────────────────────────────

def read_cpu_times():
    """Return (busy, iowait, total) jiffies from the aggregate cpu line."""
    with open("/proc/stat") as f:
        fields = [int(x) for x in f.readline().split()[1:]]
    # user nice system idle iowait irq softirq steal [guest guest_nice]
    fields = fields[:8] + [0] * (8 - len(fields[:8]))
    idle, iowait = fields[3], fields[4]
    total = sum(fields)
    return total - idle - iowait, iowait, total


def read_meminfo():
    info = {}
    with open("/proc/meminfo") as f:
        for line in f:
            key, rest = line.split(":", 1)
            info[key] = int(rest.split()[0])  # kB
    return info


def read_psi(resource):
    """Return {'some': avg10, 'full': avg10} or {} if PSI is unavailable."""
    out = {}
    try:
        with open(f"/proc/pressure/{resource}") as f:
            for line in f:
                kind, *pairs = line.split()
                vals = dict(p.split("=") for p in pairs)
                out[kind] = float(vals["avg10"])
    except (OSError, ValueError, KeyError):
        pass
    return out


def count_procs(names):
    counts = dict.fromkeys(names, 0)
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            with open(f"/proc/{pid}/comm") as f:
                comm = f.read().strip()
        except OSError:
            continue
        if comm in counts:
            counts[comm] += 1
    return counts


def count_containers(label_key):
    try:
        res = subprocess.run(
            ["docker", "ps", "-q", "--filter", f"label={label_key}"],
            capture_output=True, text=True, timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if res.returncode != 0:
        return None
    return len(res.stdout.split())


# ── Sampling ──────────────────────────────────────────────────────────────

class Sampler:
    def __init__(self, label_key, start):
        self.label_key = label_key
        self.start = start
        self.ncpu = os.cpu_count() or 1
        self.prev_cpu = read_cpu_times()
        self.peaks = {}

    def sample(self):
        now = time.time()
        busy, iowait, total = read_cpu_times()
        pb, pi, pt = self.prev_cpu
        self.prev_cpu = (busy, iowait, total)
        dt_total = max(total - pt, 1)

        mem = read_meminfo()
        mem_total = mem["MemTotal"] / 1048576
        mem_used = (mem["MemTotal"] - mem.get("MemAvailable", mem["MemFree"])) / 1048576
        swap_used = (mem.get("SwapTotal", 0) - mem.get("SwapFree", 0)) / 1048576
        with open("/proc/loadavg") as f:
            load1, load5 = (float(x) for x in f.read().split()[:2])
        psi_cpu, psi_mem, psi_io = read_psi("cpu"), read_psi("memory"), read_psi("io")

        row = {
            "timestamp": dt.datetime.fromtimestamp(now).isoformat(timespec="seconds"),
            "elapsed_s": int(now - self.start),
            "containers": count_containers(self.label_key),
            **count_procs(WATCHED_PROCS),
            "cpu_busy_pct": 100.0 * (busy - pb) / dt_total,
            "cpu_iowait_pct": 100.0 * (iowait - pi) / dt_total,
            "load1": load1,
            "load5": load5,
            "ncpu": self.ncpu,
            "mem_used_gb": mem_used,
            "mem_total_gb": mem_total,
            "mem_used_pct": 100.0 * mem_used / mem_total,
            "swap_used_gb": swap_used,
            "psi_cpu_some10": psi_cpu.get("some"),
            "psi_mem_some10": psi_mem.get("some"),
            "psi_mem_full10": psi_mem.get("full"),
            "psi_io_some10": psi_io.get("some"),
        }
        for key in ("containers", *WATCHED_PROCS, "cpu_busy_pct", "load1",
                    "mem_used_gb", "mem_used_pct", "swap_used_gb", "psi_mem_full10"):
            v = row[key]
            if v is not None and v > self.peaks.get(key, (float("-inf"),))[0]:
                self.peaks[key] = (v, row["timestamp"])
        return row


def fmt(v, nd=1):
    if v is None:
        return "NA"
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    return str(v)


def fmt_elapsed(s):
    s = int(s)
    return f"{s // 3600}h{s % 3600 // 60:02d}m{s % 60:02d}s"


def human_line(r):
    procs = " ".join(f"{p}={r[p]}" for p in WATCHED_PROCS if r[p])
    psi = ""
    if r["psi_cpu_some10"] is not None:
        psi = (f" | PSI cpu {fmt(r['psi_cpu_some10'])} mem {fmt(r['psi_mem_some10'])}"
               f"/{fmt(r['psi_mem_full10'])} io {fmt(r['psi_io_some10'])}")
    return (
        f"[{r['timestamp'][11:]}] +{fmt_elapsed(r['elapsed_s'])} "
        f"containers={fmt(r['containers'])}{' ' + procs if procs else ''} | "
        f"CPU {fmt(r['cpu_busy_pct'], 0)}% (iowait {fmt(r['cpu_iowait_pct'], 0)}%) "
        f"load {fmt(r['load1'])}/{r['ncpu']} | "
        f"RAM {fmt(r['mem_used_gb'])}/{fmt(r['mem_total_gb'], 0)} GB "
        f"({fmt(r['mem_used_pct'], 0)}%) swap {fmt(r['swap_used_gb'])} GB{psi}"
    )


def warnings_for(r):
    w = []
    if r["mem_used_pct"] >= WARN_MEM_PCT:
        w.append(f"RAM {r['mem_used_pct']:.0f}% used")
    if r["swap_used_gb"] >= WARN_SWAP_GB:
        w.append(f"swap in use ({r['swap_used_gb']:.1f} GB)")
    if (r["psi_mem_full10"] or 0) >= WARN_PSI_MEM_FULL:
        w.append(f"memory pressure: all tasks stalled {r['psi_mem_full10']:.1f}% of last 10s")
    if r["load1"] > 2 * r["ncpu"]:
        w.append(f"load {r['load1']:.0f} is over 2x the {r['ncpu']} CPUs")
    return w


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
        usage="%(prog)s [options] {build,grid} [-- SCRIPT_ARGS...]",
    )
    parser.add_argument("-i", "--interval", type=float, default=60,
                        help="seconds between samples (default: 60)")
    parser.add_argument("-o", "--logdir", default="run_logs",
                        help="directory for logs (default: ./run_logs)")
    parser.add_argument("script", choices=sorted(SCRIPTS),
                        help="build = build_reference_data.sh, grid = grid_search.sh")
    parser.add_argument("script_args", nargs=argparse.REMAINDER,
                        help="arguments passed to the script (after --)")
    args = parser.parse_args()
    if args.interval <= 0:
        parser.error("--interval must be positive")
    script_args = args.script_args
    if script_args and script_args[0] == "--":
        script_args = script_args[1:]

    script_name, label_key = SCRIPTS[args.script]
    script_path = os.path.join(REPO_DIR, script_name)
    if not os.access(script_path, os.X_OK):
        sys.exit(f"Error: {script_path} not found or not executable")

    os.makedirs(args.logdir, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    base = os.path.join(args.logdir, f"{args.script}_{stamp}")
    out_path, tsv_path, log_path = base + ".out", base + ".metrics.tsv", base + ".monitor.log"
    pid_path = os.path.join(args.logdir, "run_monitored.pid")

    log_f = open(log_path, "a", buffering=1)

    def log(msg):
        print(msg, flush=True)
        log_f.write(msg + "\n")

    tsv_f = open(tsv_path, "w", buffering=1)
    tsv_f.write("\t".join(COLUMNS) + "\n")
    out_f = open(out_path, "wb")

    cmd = [script_path] + script_args
    start = time.time()
    log(f"[{dt.datetime.now():%F %T}] Launching: {' '.join(cmd)}")
    log(f"  host:     {os.uname().nodename} ({os.cpu_count()} CPUs)")
    log(f"  interval: {args.interval:g}s")
    log(f"  output:   {out_path}")
    log(f"  metrics:  {tsv_path}")
    log(f"  log:      {log_path}")

    # New session: a terminal Ctrl-C reaches only this monitor, which then
    # sends a single SIGTERM to the script (both scripts clean up their
    # containers on TERM).
    child = subprocess.Popen(cmd, stdout=out_f, stderr=subprocess.STDOUT,
                             stdin=subprocess.DEVNULL, start_new_session=True)
    with open(pid_path, "w") as f:
        f.write(f"{os.getpid()}\n")
    log(f"  pid:      monitor {os.getpid()}, script {child.pid}  (stop with: kill $(cat {pid_path}))")

    stop_requests = []

    def on_signal(signum, _frame):
        stop_requests.append(signum)
        if len(stop_requests) == 1:
            log(f"[{dt.datetime.now():%F %T}] Received {signal.Signals(signum).name}; "
                f"sending SIGTERM to script (signal again to force-kill)")
            try:
                os.kill(child.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        else:
            log(f"[{dt.datetime.now():%F %T}] Force-killing script process group")
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)

    sampler = Sampler(label_key, start)
    n_samples = 0
    n_warnings = 0
    # Short baseline so the first sample's CPU % covers a real interval.
    time.sleep(min(1.0, args.interval))
    try:
        next_sample = time.time()
        while True:
            if time.time() >= next_sample:
                row = sampler.sample()
                n_samples += 1
                tsv_f.write("\t".join(fmt(row[c], 2) for c in COLUMNS) + "\n")
                line = human_line(row)
                for w in warnings_for(row):
                    n_warnings += 1
                    line += f"\n  WARNING: {w}"
                log(line)
                next_sample = time.time() + args.interval
            try:
                child.wait(timeout=max(0.1, min(next_sample - time.time(), 5)))
                break
            except subprocess.TimeoutExpired:
                continue
    finally:
        rc = child.wait()
        end = time.time()
        # Final sample so short runs still have a closing data point.
        row = sampler.sample()
        tsv_f.write("\t".join(fmt(row[c], 2) for c in COLUMNS) + "\n")
        log(human_line(row))

        status = f"exit {rc}" if rc >= 0 else f"killed by {signal.Signals(-rc).name}"
        log("")
        log(f"[{dt.datetime.now():%F %T}] {script_name} finished: {status}, "
            f"wall {fmt_elapsed(end - start)}, {n_samples + 1} samples, {n_warnings} warnings")
        log("Peaks:")
        labels = {
            "containers": "containers in flight",
            **{p: f"{p} processes" for p in WATCHED_PROCS},
            "cpu_busy_pct": "CPU busy %",
            "load1": "load (1 min)",
            "mem_used_gb": "RAM used (GB)",
            "mem_used_pct": "RAM used %",
            "swap_used_gb": "swap used (GB)",
            "psi_mem_full10": "memory stall % (PSI full)",
        }
        for key, label in labels.items():
            if key in sampler.peaks:
                v, when = sampler.peaks[key]
                log(f"  {label:<28} {fmt(v)}  at {when}")
        log(f"Script output: {out_path}")
        for f in (tsv_f, out_f, log_f):
            f.close()
        try:
            os.remove(pid_path)
        except OSError:
            pass

    sys.exit(rc if rc >= 0 else 128 - rc)


if __name__ == "__main__":
    main()
