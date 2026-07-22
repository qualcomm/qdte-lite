#!/usr/bin/env bash
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
#
# Fail if any file contains non-ASCII characters. This project keeps all
# sources, docs and scripts ASCII-only so diffs, greps and terminals behave
# predictably everywhere.
#
# Usage:
#   check_unicode_symbols.sh --check --all-files   # scan all tracked files
#   check_unicode_symbols.sh --check FILE...       # scan the given files
#
# --check is accepted for interface symmetry (the script only ever checks).
set -euo pipefail

all_files=0
files=()
for arg in "$@"; do
    case "$arg" in
        --check)     ;;               # report-and-fail is the only mode
        --all-files) all_files=1 ;;
        --*)         echo "unknown option: $arg" >&2; exit 2 ;;
        *)           files+=("$arg") ;;
    esac
done

if [[ "$all_files" -eq 1 || "${#files[@]}" -eq 0 ]]; then
    mapfile -t files < <(git ls-files)
fi

found=0
for f in "${files[@]}"; do
    [[ -f "$f" ]] || continue
    if LC_ALL=C grep -nP "[^\x00-\x7F]" "$f" >/dev/null 2>&1; then
        found=1
        echo "non-ASCII characters in $f:"
        LC_ALL=C grep -nP "[^\x00-\x7F]" "$f" | sed 's/^/  /'
    fi
done

if [[ "$found" -ne 0 ]]; then
    echo "ERROR: non-ASCII characters found (see above)." >&2
    exit 1
fi

echo "ascii check: OK (${#files[@]} files)"
