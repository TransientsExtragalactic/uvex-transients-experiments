#!/usr/bin/env bash
# Run the infant-SNe transient simulation for each LMLZ_WIDE cadence.
#
# Each run starts from an empty working directory (so no old checkpoint is reused), and its four
# outputs are moved into products/ under flat names:
#     products/infant_sne_<cadence>_{final_catalog,exposure,photometry,event_summary}.ecsv
#
# Usage:   code/run_infant_sne.sh [cadence ...]        (default: 6h 1d 2d 4d 10d)
# Env:     UVEX_TRANSIENTS   the uvex-transients executable (default: uvex-transients)
#          LOG_LEVEL         passed to --log-level (default: the CLI's own)
#
# The configs point at products/chips.ds9, the field-of-view definition used with the schedules.
set -u

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cli="${UVEX_TRANSIENTS:-uvex-transients}"
products=(final_catalog exposure photometry event_summary)

if (($#)); then cadences=("$@"); else cadences=(6h 1d 2d 4d 10d); fi

cd "$root" || exit 1
if [[ ! -e products/chips.ds9 ]]; then
    echo "error: products/chips.ds9 not found in $root" >&2
    exit 1
fi
mkdir -p products
failed=()

for cad in "${cadences[@]}"; do
    config="configs/infant_sne_${cad}.yaml"
    if [[ ! -f "$config" ]]; then
        echo "=== $cad: no such config: $config" >&2
        failed+=("$cad")
        continue
    fi

    work="$(mktemp -d "${TMPDIR:-/tmp}/infant_sne_${cad}.XXXXXX")"
    echo "=== $cad: infant_sne ($(date '+%H:%M:%S')), working in $work ==="
    args=(run "$config" --out-dir "$work")
    [[ -n "${LOG_LEVEL:-}" ]] && args=(--log-level "$LOG_LEVEL" "${args[@]}")

    if "$cli" "${args[@]}" 2>&1 | tee "$work/run.log"; [[ ${PIPESTATUS[0]} -eq 0 ]]; then
        missing=()
        for name in "${products[@]}"; do
            [[ -f "$work/$name.ecsv" ]] || missing+=("$name")
        done
        if ((${#missing[@]})); then
            echo "=== $cad: FAILED, missing outputs: ${missing[*]} (kept $work)" >&2
            failed+=("$cad")
            continue
        fi
        for name in "${products[@]}"; do
            mv "$work/$name.ecsv" "products/infant_sne_${cad}_${name}.ecsv"
        done
        rm -rf "$work"
        echo "=== $cad: done ==="
    else
        echo "=== $cad: FAILED (log and partial output kept in $work)" >&2
        failed+=("$cad")
    fi
done

if ((${#failed[@]})); then
    echo "Failed: ${failed[*]}" >&2
    exit 1
fi
echo "All infant_sne runs finished."
