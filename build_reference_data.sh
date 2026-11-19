#!/bin/bash
#
# Build CensuScope's reference data with the Docker image:
#   - taxonomy.db              (entrypoint `build-taxonomy`)
#   - one BLAST nucleotide DB  (entrypoint `build-blast` / makeblastdb)
#     per input FASTA
#
# Directory layout (sibling of this repository by default; see --root):
#
#   ../databases/
#     input/<BaseDB>/<name>.fa          reference FASTAs (.fa, .fasta, .fna)
#     output/taxonomy/                  taxonomy.db + NCBI downloads (CensuScopeDB/)
#     output/<BaseDB>/<name>.n*         BLAST DB files
#     output/<BaseDB>/taxonomy.db       hard link to output/taxonomy/taxonomy.db
#     output/logs/build_<stamp>.log     run log (everything below is also echoed)
#     output/logs/build_<stamp>/        one log per build step
#
# Each output/<BaseDB>/ directory is ready to mount as /app/blastdb, e.g.
#   ./grid_search.sh --database ../databases/output/slimNT/slimNT ...
#
# Previously built databases are skipped. A build is "done" when its
# completion marker (output/<BaseDB>/.<name>.complete, or
# output/taxonomy/.taxonomy.complete) exists and the FASTA has not changed
# since. Interrupted builds leave a .building marker and are rebuilt.
# Existing databases without a marker (built before this script) are
# verified and adopted if they pass.
#
# Examples:
#   ./build_reference_data.sh --dry-run          # show what would be built
#   ./build_reference_data.sh                    # everything in input/
#   ./build_reference_data.sh slimNT filtered_nt # only these BaseDBs
#   ./build_reference_data.sh slimNT/slimNT_v2   # one FASTA
#
# Detached (the log file has everything):
#   nohup ./build_reference_data.sh > /dev/null 2>&1 &
#   kill "$(cat ../databases/output/logs/build.pid)"   # stop it

set -Eeuo pipefail
shopt -s nullglob

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    cat <<'EOF'
Usage: build_reference_data.sh [options] [TARGET ...]

Builds taxonomy.db and BLAST nucleotide databases for CensuScope.

TARGET is a BaseDB name (every FASTA in input/<BaseDB>/) or BaseDB/name
(input/<BaseDB>/<name>.fa). With no targets, every FASTA under input/ is used.

Options:
  -r, --root DIR          Databases root containing input/ and output/
                          (default: <repo>/../databases)
  -j, --jobs N            Build steps to run concurrently (default: 4)
  -I, --image NAME        Docker image (default: censuscope)
      --force             Rebuild everything selected (implies both below)
      --force-taxonomy    Re-download NCBI data and rebuild taxonomy.db
      --force-blast       Rebuild the selected BLAST databases
      --skip-taxonomy     Do not build taxonomy.db
      --skip-blast        Do not build BLAST databases
  -n, --dry-run           Show what would be built or skipped, then exit
  -h, --help              Show this help
EOF
}

die() { echo "Error: $*" >&2; exit 1; }
warn() { echo "Warning: $*" >&2; }
need_arg() { [[ $# -ge 2 && -n "$2" ]] || die "option $1 requires a value"; }
ts() { date '+%F %T'; }
fmt_dur() { printf '%dh%02dm%02ds' $(( $1 / 3600 )) $(( $1 % 3600 / 60 )) $(( $1 % 60 )); }

# ── Defaults ──────────────────────────────────────────────────────────────

ROOT="$SCRIPT_DIR/../databases"
JOBS=4
IMAGE="censuscope"
FORCE_TAX=0
FORCE_BLAST=0
DO_TAX=1
DO_BLAST=1
DRY_RUN=0
TARGETS=()

# ── Parse arguments ───────────────────────────────────────────────────────

while (( $# )); do
    case "$1" in
        -r|--root)         need_arg "$@"; ROOT="$2"; shift 2 ;;
        -j|--jobs)         need_arg "$@"; JOBS="$2"; shift 2 ;;
        -I|--image)        need_arg "$@"; IMAGE="$2"; shift 2 ;;
        --force)           FORCE_TAX=1; FORCE_BLAST=1; shift ;;
        --force-taxonomy)  FORCE_TAX=1; shift ;;
        --force-blast)     FORCE_BLAST=1; shift ;;
        --skip-taxonomy)   DO_TAX=0; shift ;;
        --skip-blast)      DO_BLAST=0; shift ;;
        -n|--dry-run)      DRY_RUN=1; shift ;;
        -h|--help)         usage; exit 0 ;;
        --)                shift; TARGETS+=("$@"); break ;;
        -*)                usage >&2; die "unknown option: $1" ;;
        *)                 TARGETS+=("$1"); shift ;;
    esac
done

(( DO_TAX || DO_BLAST )) || die "--skip-taxonomy and --skip-blast together leave nothing to do"
[[ "$JOBS" =~ ^[1-9][0-9]*$ ]] || die "--jobs must be a positive integer, got '$JOBS'"

ROOT="$(realpath -m "$ROOT")"
IN_ROOT="$ROOT/input"
OUT_ROOT="$ROOT/output"
TAX_DIR="$OUT_ROOT/taxonomy"
LOG_ROOT="$OUT_ROOT/logs"

valid_name() { [[ "$1" =~ ^[A-Za-z0-9._-]+$ ]]; }

# ── Discover BLAST targets ────────────────────────────────────────────────

FASTA_EXTS=(fa fasta fna)
TASKS=()   # "base<TAB>name<TAB>fasta"

add_fasta() {
    local base=$1 f=$2 name
    name="$(basename "$f")"; name="${name%.*}"
    valid_name "$base" || die "invalid BaseDB directory name '$base' (letters, digits, . _ - only)"
    valid_name "$name" || die "invalid FASTA name '$name' in $IN_ROOT/$base (letters, digits, . _ - only)"
    local t
    for t in ${TASKS[@]+"${TASKS[@]}"}; do
        [[ "$t" == "$base"$'\t'"$name"$'\t'* ]] || continue
        [[ "${t##*$'\t'}" == "$f" ]] && return 0
        die "two FASTAs map to the same database $base/$name: ${t##*$'\t'} and $f"
    done
    TASKS+=("$base"$'\t'"$name"$'\t'"$f")
}

scan_base() {   # $1 = BaseDB, $2 = name or empty for all
    local base=$1 want=${2:-} ext f found=0
    [[ -d "$IN_ROOT/$base" ]] || die "no such BaseDB: $IN_ROOT/$base"
    for ext in "${FASTA_EXTS[@]}"; do
        for f in "$IN_ROOT/$base/"*."$ext".{gz,bz2,xz,zst}; do
            warn "skipping compressed file (makeblastdb needs uncompressed FASTA): $f"
        done
        if [[ -n "$want" ]]; then
            f="$IN_ROOT/$base/$want.$ext"
            [[ -f "$f" ]] && { add_fasta "$base" "$f"; found=1; }
        else
            for f in "$IN_ROOT/$base/"*."$ext"; do
                [[ -f "$f" ]] && { add_fasta "$base" "$f"; found=1; }
            done
        fi
    done
    (( found )) || die "no FASTA found for target '$base${want:+/$want}' in $IN_ROOT/$base"
}

if (( DO_BLAST )); then
    [[ -d "$IN_ROOT" ]] || die "input directory not found: $IN_ROOT (expected $IN_ROOT/<BaseDB>/<name>.fa)"
    if (( ${#TARGETS[@]} )); then
        for t in "${TARGETS[@]}"; do
            t="${t%/}"
            if [[ "$t" == */* ]]; then
                scan_base "${t%%/*}" "${t#*/}"
            else
                scan_base "$t"
            fi
        done
    else
        for d in "$IN_ROOT"/*/; do
            d="${d%/}"
            scan_base "$(basename "$d")"
        done
        (( ${#TASKS[@]} )) || die "no FASTA files found under $IN_ROOT/<BaseDB>/"
    fi
elif (( ${#TARGETS[@]} )); then
    warn "targets ignored with --skip-blast"
fi

if (( ! DRY_RUN )); then
    command -v docker > /dev/null || die "docker not found"
    docker image inspect "$IMAGE" > /dev/null 2>&1 \
        || die "docker image '$IMAGE' not found (build it with: docker build -t $IMAGE .)"
    IMAGE_ID="$(docker image inspect --format '{{.Id}}' "$IMAGE")"
fi

# ── State checks (what is built, what needs building) ─────────────────────

# Prints "skip <reason>", "check <reason>", or "build <reason>".
tax_state() {
    if (( FORCE_TAX )); then echo "build (forced)"
    elif [[ -e "$TAX_DIR/.taxonomy.building" ]]; then echo "build (previous build incomplete)"
    elif [[ -f "$TAX_DIR/.taxonomy.complete" && -s "$TAX_DIR/taxonomy.db" ]]; then echo "skip (built)"
    elif [[ -s "$TAX_DIR/taxonomy.db" ]]; then echo "check (existing taxonomy.db, no marker)"
    else echo "build (new)"
    fi
}

blast_state() {   # base name fasta
    local out="$OUT_ROOT/$1" name=$2 fasta=$3 marker
    marker="$out/.$name.complete"
    local files=("$out/$name".n*)
    if (( FORCE_BLAST )); then echo "build (forced)"
    elif [[ -e "$out/.$name.building" ]]; then echo "build (previous build incomplete)"
    elif [[ -f "$marker" ]]; then
        if [[ "$fasta" -nt "$marker" ]] \
           || [[ "$(sed -n 's/^size=//p' "$marker")" != "$(stat -c %s "$fasta")" ]]; then
            echo "build (FASTA changed since last build)"
        elif (( ${#files[@]} == 0 )); then
            echo "build (marker present but DB files missing)"
        else
            echo "skip (built)"
        fi
    elif (( ${#files[@]} )); then echo "check (existing DB files, no marker)"
    else echo "build (new)"
    fi
}

verify_taxonomy() {   # dir containing taxonomy.db
    docker run --rm --entrypoint sh -v "$1:/app/blastdb:ro" "$IMAGE" -c '
        db=/app/blastdb/taxonomy.db
        for t in accession_taxid nodes names hosts; do
            n=$(sqlite3 -readonly "$db" "SELECT count(*) FROM (SELECT 1 FROM \"$t\" LIMIT 1);" 2>/dev/null) || n=0
            if [ "$n" = 1 ]; then echo "  table $t: ok"; else echo "  table $t: MISSING or empty"; exit 1; fi
        done'
}

verify_blast() {   # base name
    docker run --rm --entrypoint blastdbcmd -v "$OUT_ROOT/$1:/app/blastdb:ro" "$IMAGE" \
        -db "/app/blastdb/$2" -info 2>&1 | sed 's/^/  /'
}

write_marker() {   # marker-file how [fasta]
    {
        echo "$2=$(date -Is)"
        echo "image=${IMAGE_ID:-unknown}"
        if [[ -n "${3:-}" ]]; then
            echo "fasta=$3"
            echo "size=$(stat -c %s "$3")"
        fi
    } > "$1"
}

# ── Plan ──────────────────────────────────────────────────────────────────

RUN_TAX=0
RUN_BLAST=()      # indexes into TASKS
PLAN=()           # human-readable lines

if (( DO_TAX )); then
    state="$(tax_state)"
    PLAN+=("taxonomy.db"$'\t'"$state")
    [[ "$state" == build* ]] && RUN_TAX=1
fi
for i in "${!TASKS[@]}"; do
    IFS=$'\t' read -r base name fasta <<< "${TASKS[$i]}"
    state="$(blast_state "$base" "$name" "$fasta")"
    PLAN+=("$base/$name"$'\t'"$state")
    [[ "$state" == build* ]] && RUN_BLAST+=("$i")
done

print_plan() {
    local line
    for line in "${PLAN[@]}"; do
        printf '  %-40s %s\n' "${line%%$'\t'*}" "${line#*$'\t'}"
    done
}

if (( DRY_RUN )); then
    echo "Databases root: $ROOT"
    print_plan
    echo "(\"check\" entries are verified at run time and either adopted or rebuilt)"
    exit 0
fi

# ── Lock, logging, signal handling ────────────────────────────────────────

mkdir -p "$OUT_ROOT" "$LOG_ROOT"
PID_FILE="$LOG_ROOT/build.pid"
if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    die "another build is running (PID $(cat "$PID_FILE"), $PID_FILE)"
fi

STAMP="$(date +%Y%m%d_%H%M%S)"
LOG="$LOG_ROOT/build_${STAMP}.log"
STEP_LOG_DIR="$LOG_ROOT/build_${STAMP}"
STATUS="$STEP_LOG_DIR/status.tsv"
mkdir -p "$STEP_LOG_DIR"
printf 'step\texit_code\twall_seconds\tlog\n' > "$STATUS"

exec > >(tee -a "$LOG") 2>&1

echo $$ > "$PID_FILE"
LABEL="censuscope-build=$STAMP"
PIDS=()

cleanup() {
    echo "[$(ts)] Interrupted; stopping build steps and containers..."
    (( ${#PIDS[@]} )) && kill "${PIDS[@]}" 2>/dev/null
    docker ps -q --filter "label=$LABEL" | xargs -r docker kill > /dev/null
    rm -f "$PID_FILE"
    exit 130
}
trap cleanup INT TERM
trap 'rm -f "$PID_FILE"' EXIT

DOCKER_RUN=(docker run --rm --label "$LABEL" --user "$(id -u):$(id -g)")

# ── Header ────────────────────────────────────────────────────────────────

echo "CensuScope reference data build"
echo "  date:      $(date -Is)"
echo "  host:      $(hostname)"
echo "  image:     $IMAGE (${IMAGE_ID:0:19})"
echo "  root:      $ROOT"
echo "  log:       $LOG"
echo "  step logs: $STEP_LOG_DIR/"
echo "  jobs:      $JOBS"
echo "  free disk: $(df -h --output=avail "$OUT_ROOT" | tail -1 | tr -d ' ')"
echo "  tools:"
docker run --rm --entrypoint sh "$IMAGE" -c \
    'echo "    $(python3 --version)"; echo "    $(blastn -version | head -1)"; echo "    sqlite3 $(sqlite3 --version | cut -d" " -f1)"' \
    || echo "    (could not query tool versions)"
echo
echo "Plan:"
print_plan

# ── Adopt pre-existing databases that have no marker ──────────────────────

if (( DO_TAX )) && [[ "$(tax_state)" == check* ]]; then
    echo
    echo "[$(ts)] Checking existing $TAX_DIR/taxonomy.db"
    if verify_taxonomy "$TAX_DIR"; then
        write_marker "$TAX_DIR/.taxonomy.complete" adopted
        echo "  adopted"
    else
        echo "  failed verification; will rebuild"
        RUN_TAX=1
    fi
fi

for i in "${!TASKS[@]}"; do
    IFS=$'\t' read -r base name fasta <<< "${TASKS[$i]}"
    [[ "$(blast_state "$base" "$name" "$fasta")" == check* ]] || continue
    echo
    echo "[$(ts)] Checking existing BLAST DB $base/$name"
    newest="$(ls -t "$OUT_ROOT/$base/$name".n* | head -1)"
    if [[ "$fasta" -nt "$newest" ]]; then
        echo "  FASTA is newer than the DB files; will rebuild"
        RUN_BLAST+=("$i")
    elif verify_blast "$base" "$name"; then
        write_marker "$OUT_ROOT/$base/.$name.complete" adopted "$fasta"
        echo "  adopted"
    else
        echo "  failed verification; will rebuild"
        RUN_BLAST+=("$i")
    fi
done

# ── Build steps (each runs in a background subshell) ──────────────────────

build_taxonomy() {
    mkdir -p "$TAX_DIR" || return
    : > "$TAX_DIR/.taxonomy.building" || return
    # Remove any old or partial DB so build_database.sh cannot treat it as up to date.
    rm -f "$TAX_DIR/.taxonomy.complete" "$TAX_DIR/taxonomy.db" "$TAX_DIR/temp.db" || return
    local args=()
    (( FORCE_TAX )) && args=(--force)
    "${DOCKER_RUN[@]}" -v "$TAX_DIR:/app/blastdb" "$IMAGE" \
        build-taxonomy ${args[@]+"${args[@]}"} || return
    echo "Verifying taxonomy.db"
    verify_taxonomy "$TAX_DIR" || return
    write_marker "$TAX_DIR/.taxonomy.complete" built || return
    rm -f "$TAX_DIR/.taxonomy.building"
}

build_blast() {   # base name fasta
    local base=$1 name=$2 fasta=$3 out="$OUT_ROOT/$1"
    mkdir -p "$out" || return
    : > "$out/.$name.building" || return
    rm -f "$out/.$name.complete" "$out/$name".n* "$out/$name".[0-9]*.n* || return
    "${DOCKER_RUN[@]}" \
        -v "$(dirname "$fasta"):/app/fasta:ro" \
        -v "$out:/app/blastdb" \
        "$IMAGE" build-blast "/app/fasta/$(basename "$fasta")" "/app/blastdb/$name" || return
    echo "Verifying BLAST DB"
    verify_blast "$base" "$name" || return
    write_marker "$out/.$name.complete" built "$fasta" || return
    rm -f "$out/.$name.building"
}

run_step() {   # label log-file command...
    local label=$1 log=$2; shift 2
    local start rc=0 elapsed
    trap - INT TERM
    echo "[$(ts)] START $label  ->  $log"
    start=$(date +%s)
    "$@" > "$log" 2>&1 || rc=$?
    elapsed=$(( $(date +%s) - start ))
    echo "[$(ts)] END   $label: exit $rc, $(fmt_dur "$elapsed")"
    printf '%s\t%s\t%s\t%s\n' "$label" "$rc" "$elapsed" "$log" >> "$STATUS"
}

QUEUE=()   # "taxonomy.db" or an index into TASKS
(( RUN_TAX )) && QUEUE+=("taxonomy.db")
for i in ${RUN_BLAST[@]+"${RUN_BLAST[@]}"}; do
    QUEUE+=("$i")
done

echo
if (( ${#QUEUE[@]} == 0 )); then
    echo "[$(ts)] Nothing to build."
else
    echo "[$(ts)] Running ${#QUEUE[@]} build step(s), $JOBS at a time"
    for q in "${QUEUE[@]}"; do
        while mapfile -t running < <(jobs -rp); (( ${#running[@]} >= JOBS )); do
            wait -n "${running[@]}" 2>/dev/null || true
        done
        if [[ "$q" == "taxonomy.db" ]]; then
            run_step "taxonomy.db" "$STEP_LOG_DIR/taxonomy.log" build_taxonomy &
        else
            IFS=$'\t' read -r base name fasta <<< "${TASKS[$q]}"
            run_step "$base/$name" "$STEP_LOG_DIR/${base}__${name}.log" \
                build_blast "$base" "$name" "$fasta" &
        fi
        PIDS+=($!)
    done
    for p in "${PIDS[@]}"; do
        wait "$p" 2>/dev/null || true
    done
fi

# ── Link taxonomy.db into each BLAST output directory ─────────────────────

# Every BaseDB targeted this run, plus every existing output/<BaseDB>/ with a
# built BLAST DB, so a rebuilt taxonomy.db reaches all of them.
declare -A BASES=()
for t in ${TASKS[@]+"${TASKS[@]}"}; do
    BASES["${t%%$'\t'*}"]=1
done
for m in "$OUT_ROOT"/*/.*.complete; do
    d="$(basename "$(dirname "$m")")"
    [[ "$d" == taxonomy || "$d" == logs ]] || BASES["$d"]=1
done

if (( ${#BASES[@]} )); then
    echo
    echo "[$(ts)] Linking taxonomy.db into BLAST output directories"
    src="$TAX_DIR/taxonomy.db"
    if [[ -f "$TAX_DIR/.taxonomy.complete" && -s "$src" ]]; then
        for base in "${!BASES[@]}"; do
            dst="$OUT_ROOT/$base/taxonomy.db"
            mkdir -p "$OUT_ROOT/$base"
            if [[ "$src" -ef "$dst" ]]; then
                echo "  $base: already linked"
            elif ln -f "$src" "$dst" 2>/dev/null; then
                echo "  $base: linked"
            elif cp --reflink=auto "$src" "$dst.tmp" && mv -f "$dst.tmp" "$dst"; then
                echo "  $base: copied (hard link not possible across filesystems)"
            else
                echo "  $base: FAILED to link or copy taxonomy.db"
                printf '%s\t%s\t%s\t%s\n' "link $base/taxonomy.db" 1 0 "-" >> "$STATUS"
            fi
        done
    else
        echo "  skipped: no complete taxonomy.db in $TAX_DIR"
        echo "  (CensuScope runs against these databases will have no taxonomy until it is built)"
    fi
fi

# ── Summary ───────────────────────────────────────────────────────────────

echo
echo "════════════════════════════════════════════════════════════════════"
echo "[$(ts)] Summary"
echo "════════════════════════════════════════════════════════════════════"
failed=0
if (( DO_TAX )); then
    if [[ -f "$TAX_DIR/.taxonomy.complete" ]]; then
        echo "  OK      taxonomy.db  ($(du -h "$TAX_DIR/taxonomy.db" | cut -f1))"
    else
        echo "  FAILED  taxonomy.db  (see $STEP_LOG_DIR/taxonomy.log)"
        failed=$(( failed + 1 ))
    fi
fi
for t in ${TASKS[@]+"${TASKS[@]}"}; do
    IFS=$'\t' read -r base name fasta <<< "$t"
    if [[ -f "$OUT_ROOT/$base/.$name.complete" && ! -e "$OUT_ROOT/$base/.$name.building" ]]; then
        echo "  OK      $base/$name  ->  --database $OUT_ROOT/$base/$name"
    else
        echo "  FAILED  $base/$name  (see $STEP_LOG_DIR/${base}__${name}.log)"
        failed=$(( failed + 1 ))
    fi
done
failed=$(( failed + $(awk -F'\t' 'NR > 1 && $1 ~ /^link / && $2 != 0' "$STATUS" | wc -l) ))
echo
if (( failed )); then
    echo "[$(ts)] $failed failure(s). Log: $LOG"
    exit 1
fi
echo "[$(ts)] Done. Log: $LOG"
