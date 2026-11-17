#!/bin/bash
#
# Grid search over CensuScope sample size (reads per iteration) and iteration
# count. Each grid point runs in its own Docker container; several points run
# concurrently (see --jobs).
#
# Each grid point gets its own host directory mounted as /app/temp_dirs, so
# concurrent runs cannot collide on CensuScope's second-resolution timestamp
# directory.
#
# Example:
#   ./grid_search.sh \
#     --query inputs/slimNT_reads_15000x150.fa \
#     --database blastdb/slimNT \
#     --sizes 100,500,1000,5000 \
#     --iterations 5,10,20,50 \
#     --replicates 3 \
#     --jobs 4
#
# To keep it running after logout:
#   nohup ./grid_search.sh ... > grid.log 2>&1 &
#
# To stop a detached grid (kills its running containers too):
#   kill "$(cat grid_runs/grid_<stamp>/grid.pid)"
#
# Output layout:
#   <outdir>/grid_<stamp>/
#     grid.pid                        PID of this script, for stopping the grid
#     params.txt                      settings used for this grid
#     manifest.tsv                    one row per grid point: exit code, wall time, results dir
#     s<size>_i<iters>_r<rep>/
#       stdout.log                    container stdout/stderr
#       <censuscope timestamp>/results/   taxonomy_table.tsv, accession_table.tsv, ...

set -Eeuo pipefail

usage() {
    cat <<'EOF'
Usage: grid_search.sh -q QUERY -d DB_PREFIX -s SIZES -i ITERATIONS [options]

Required:
  -q, --query PATH        Input FASTA/FASTQ file (host path)
  -d, --database PREFIX   BLAST DB prefix (host path, e.g. blastdb/slimNT).
                          The DB's directory must also contain taxonomy.db.
  -s, --sizes LIST        Comma-separated sample sizes (reads per iteration)
  -i, --iterations LIST   Comma-separated iteration counts

Options:
  -r, --replicates N      Runs per grid point (default: 1). Runs are stochastic.
  -j, --jobs N            Grid points to run concurrently
                          (default: nproc/10, minimum 1; each blastn uses 10 threads)
  -c, --cpus N            Docker --cpus limit per container (default: no limit)
  -t, --tax-depth RANK    kingdom|phylum|class|order|family|genus|species
                          (default: species)
  -o, --outdir DIR        Parent output directory (default: ./grid_runs)
  -I, --image NAME        Docker image (default: censuscope)
  -n, --dry-run           Print the docker commands without running them
  -h, --help              Show this help
EOF
}

die() { echo "Error: $*" >&2; exit 1; }

need_arg() { [[ $# -ge 2 && -n "$2" ]] || die "option $1 requires a value"; }

# ── Defaults ──────────────────────────────────────────────────────────────

QUERY=""
DB=""
SIZES=""
ITERS=""
REPS=1
JOBS=$(( $(nproc) / 10 ))
(( JOBS >= 1 )) || JOBS=1
CPUS=""
TAX_DEPTH="species"
OUT_ROOT="$(pwd)/grid_runs"
IMAGE="censuscope"
DRY_RUN=0

# ── Parse arguments ───────────────────────────────────────────────────────

while (( $# )); do
    case "$1" in
        -q|--query)       need_arg "$@"; QUERY="$2"; shift 2 ;;
        -d|--database)    need_arg "$@"; DB="$2"; shift 2 ;;
        -s|--sizes)       need_arg "$@"; SIZES="$2"; shift 2 ;;
        -i|--iterations)  need_arg "$@"; ITERS="$2"; shift 2 ;;
        -r|--replicates)  need_arg "$@"; REPS="$2"; shift 2 ;;
        -j|--jobs)        need_arg "$@"; JOBS="$2"; shift 2 ;;
        -c|--cpus)        need_arg "$@"; CPUS="$2"; shift 2 ;;
        -t|--tax-depth)   need_arg "$@"; TAX_DEPTH="$2"; shift 2 ;;
        -o|--outdir)      need_arg "$@"; OUT_ROOT="$2"; shift 2 ;;
        -I|--image)       need_arg "$@"; IMAGE="$2"; shift 2 ;;
        -n|--dry-run)     DRY_RUN=1; shift ;;
        -h|--help)        usage; exit 0 ;;
        *)                usage >&2; die "unknown option: $1" ;;
    esac
done

[[ -n "$QUERY" ]] || { usage >&2; die "--query is required"; }
[[ -n "$DB"    ]] || { usage >&2; die "--database is required"; }
[[ -n "$SIZES" ]] || { usage >&2; die "--sizes is required"; }
[[ -n "$ITERS" ]] || { usage >&2; die "--iterations is required"; }

# ── Validate ──────────────────────────────────────────────────────────────

is_posint() { [[ "$1" =~ ^[1-9][0-9]*$ ]]; }

IFS=',' read -r -a SIZE_LIST <<< "$SIZES"
IFS=',' read -r -a ITER_LIST <<< "$ITERS"
for v in "${SIZE_LIST[@]}" "${ITER_LIST[@]}" "$REPS" "$JOBS"; do
    is_posint "$v" || die "expected a positive integer, got '$v'"
done

case "$TAX_DEPTH" in
    kingdom|phylum|class|order|family|genus|species) ;;
    *) die "invalid --tax-depth '$TAX_DEPTH'" ;;
esac

[[ -f "$QUERY" ]] || die "query file not found: $QUERY"
QUERY_ABS="$(realpath "$QUERY")"
QUERY_DIR="$(dirname "$QUERY_ABS")"
QUERY_NAME="$(basename "$QUERY_ABS")"

DB_ABS="$(realpath -m "$DB")"
DB_DIR="$(dirname "$DB_ABS")"
DB_NAME="$(basename "$DB_ABS")"
compgen -G "${DB_ABS}.n*" > /dev/null || die "no BLAST nucleotide DB files found at ${DB_ABS}.n*"
[[ -f "$DB_DIR/taxonomy.db" ]] || echo "Warning: $DB_DIR/taxonomy.db not found; taxonomy will be skipped" >&2

if (( ! DRY_RUN )); then
    command -v docker > /dev/null || die "docker not found"
    docker image inspect "$IMAGE" > /dev/null 2>&1 || die "docker image '$IMAGE' not found"
fi

# CensuScope copies the whole file and ignores --iterations when
# sample size >= total reads, so those grid points are skipped.
count_reads() {
    case "$(head -c1 "$1")" in
        ">") grep -c '^>' "$1" ;;
        "@") echo $(( $(wc -l < "$1") / 4 )) ;;
        *)   die "unrecognised format (first char not '>' or '@'): $1" ;;
    esac
}
TOTAL_READS="$(count_reads "$QUERY_ABS")"

# ── Build grid (largest size*iterations first, for better packing) ────────

GRID=()
for size in "${SIZE_LIST[@]}"; do
    if (( size >= TOTAL_READS )); then
        echo "Skipping sample size $size: >= total reads ($TOTAL_READS)" >&2
        continue
    fi
    for iters in "${ITER_LIST[@]}"; do
        for (( rep = 1; rep <= REPS; rep++ )); do
            GRID+=("$(( size * iters )) $size $iters $rep")
        done
    done
done
(( ${#GRID[@]} )) || die "no grid points to run"
mapfile -t GRID < <(printf '%s\n' "${GRID[@]}" | sort -k1,1nr -k2,2n -k3,3n -k4,4n)

GRID_ID="$(date +%Y%m%d_%H%M%S)"
GRID_DIR="$(realpath -m "$OUT_ROOT")/grid_${GRID_ID}"

CPU_ARGS=()
[[ -n "$CPUS" ]] && CPU_ARGS=(--cpus "$CPUS")

# ── Run one grid point ────────────────────────────────────────────────────

run_point() {
    local size=$1 iters=$2 rep=$3
    local tag="s${size}_i${iters}_r${rep}"
    local dir="$GRID_DIR/$tag"

    local cmd=(
        docker run --rm
        --label "censuscope-grid=$GRID_ID"
        --name "csgrid_${GRID_ID}_${tag}"
        ${CPU_ARGS[@]+"${CPU_ARGS[@]}"}
        -v "$DB_DIR:/app/blastdb:ro"
        -v "$QUERY_DIR:/app/inputs:ro"
        -v "$dir:/app/temp_dirs"
        "$IMAGE"
        --iterations "$iters"
        --sample-size "$size"
        --tax-depth "$TAX_DEPTH"
        --query_path "/app/inputs/$QUERY_NAME"
        --database "/app/blastdb/$DB_NAME"
    )

    if (( DRY_RUN )); then
        printf '%q ' "${cmd[@]}"; echo
        return 0
    fi

    mkdir -p "$dir"
    echo "[$(date +%T)] start $tag"
    local start rc=0 elapsed results
    start=$(date +%s)
    "${cmd[@]}" > "$dir/stdout.log" 2>&1 || rc=$?
    elapsed=$(( $(date +%s) - start ))
    results=$(find "$dir" -mindepth 2 -maxdepth 2 -type d -name results -print -quit)

    # Single short line with O_APPEND: safe for concurrent writers.
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
        "$size" "$iters" "$rep" "$rc" "$elapsed" "${results:-NA}" >> "$GRID_DIR/manifest.tsv"
    echo "[$(date +%T)] done  $tag (exit $rc, ${elapsed}s)"
}

# ── Dry run ───────────────────────────────────────────────────────────────

if (( DRY_RUN )); then
    echo "# ${#GRID[@]} grid points, $TOTAL_READS reads in query, output -> $GRID_DIR"
    for point in "${GRID[@]}"; do
        read -r _ size iters rep <<< "$point"
        run_point "$size" "$iters" "$rep"
    done
    exit 0
fi

# ── Run ───────────────────────────────────────────────────────────────────

mkdir -p "$GRID_DIR"
echo $$ > "$GRID_DIR/grid.pid"

cleanup() {
    echo "Interrupted; stopping grid containers..." >&2
    docker ps -q --filter "label=censuscope-grid=$GRID_ID" | xargs -r docker kill > /dev/null
    exit 130
}
trap cleanup INT TERM

{
    echo "date:        $(date -Is)"
    echo "query:       $QUERY_ABS ($TOTAL_READS reads)"
    echo "database:    $DB_ABS"
    echo "image:       $IMAGE"
    echo "tax_depth:   $TAX_DEPTH"
    echo "sizes:       $SIZES"
    echo "iterations:  $ITERS"
    echo "replicates:  $REPS"
    echo "jobs:        $JOBS"
    echo "cpus:        ${CPUS:-unlimited}"
    echo "grid_points: ${#GRID[@]}"
} > "$GRID_DIR/params.txt"
printf 'sample_size\titerations\treplicate\texit_code\twall_seconds\tresults_dir\n' > "$GRID_DIR/manifest.tsv"

echo "Running ${#GRID[@]} grid points, $JOBS at a time -> $GRID_DIR"

for point in "${GRID[@]}"; do
    read -r _ size iters rep <<< "$point"
    while (( $(jobs -rp | wc -l) >= JOBS )); do
        wait -n || true
    done
    run_point "$size" "$iters" "$rep" &
done
wait

failed=$(awk -F'\t' 'NR > 1 && $4 != 0' "$GRID_DIR/manifest.tsv" | wc -l)
echo "Finished: ${#GRID[@]} grid points, $failed failed. Manifest: $GRID_DIR/manifest.tsv"
(( failed == 0 ))
