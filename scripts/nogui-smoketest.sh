#!/usr/bin/env bash
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
#
# Headless (--nogui) smoke test.
#
# Exercises the command-line contract downstream automation relies on:
# edit a property inside each of two real Qualcomm boot containers and read
# it back from the rebuilt ELF with fdtdump, then re-edit qdte's own output
# to prove a reassembled container can be opened again.
#
# Public fixtures are downloaded once into .test/fixtures; outputs go to
# .test/out. Requires: qdte (installed) and fdtdump (device-tree-compiler).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TESTDIR="$ROOT/.test"
FIXTURES="$TESTDIR/fixtures"
OUT="$TESTDIR/out"
WORK="$TESTDIR/work"
mkdir -p "$FIXTURES" "$OUT" "$WORK"

# Public "test-device" boot images from Qualcomm Software Center.
XBL_ZIP_URL="https://softwarecenter.qualcomm.com/nexus/generic/product/chip/tech-package/QCM6490_bootbinaries.1.0/qcm6490_bootbinaries.1.0-test-device-public/00126/QCM6490_bootbinaries_00126.zip"
XBL_ELF_IN_ZIP="QCM6490_bootbinaries/xbl_config.elf"
XBL_DTB="pre-ddr-kodiak-1.0.dtb"

UEFI_ZIP_URL="https://softwarecenter.qualcomm.com/nexus/generic/product/chip/tech-package/QRB2210_bootbinaries.1.0/qrb2210_bootbinaries.1.0-test-device-public/00010/Agatti_bootbinaries.zip"
UEFI_ELF_IN_ZIP="Agatti_bootbinaries/uefi_dtbs.elf"
UEFI_DTB="qcom,uefi-agatti-1.0.dtb"

fetch() {  # url  member-in-zip  destination-file
    local url="$1" member="$2" dest="$3"
    if [[ -f "$dest" ]]; then
        return
    fi
    echo "downloading $(basename "$dest") ..."
    local tmp
    tmp="$(mktemp -d)"
    curl -fsSL -o "$tmp/archive.zip" "$url"
    unzip -o -j "$tmp/archive.zip" "$member" -d "$FIXTURES"
    rm -rf "$tmp"
}

fetch "$XBL_ZIP_URL" "$XBL_ELF_IN_ZIP" "$FIXTURES/xbl_config.elf"
fetch "$UEFI_ZIP_URL" "$UEFI_ELF_IN_ZIP" "$FIXTURES/uefi_dtbs.elf"

# Reassembly drops a stray copy of the artifact (and a raw/ dir) into the
# working directory; run from a scratch dir under .test so nothing lands in
# the repo. All paths below are absolute, so cd is safe.
cd "$WORK"

# Resolve the qdte entry point: the installed console script, else the module.
if command -v qdte >/dev/null 2>&1; then
    QDTE=(qdte)
else
    QDTE=(python -m qdte)
fi

edit() {  # input-elf  output-name  modify-spec
    "${QDTE[@]}" --nogui --allow_unsigned \
        --input_file "$1" \
        --output_path "$OUT" --output_file "$2" \
        --modify "$3" >/dev/null
}

verify() {  # elf  grep-pattern  label
    test -f "$1" || { echo "FAIL: $3 - no output produced"; exit 1; }
    fdtdump --scan "$1" 2>/dev/null | grep "$2" >/dev/null \
        || { echo "FAIL: $3 - property not found in output"; exit 1; }
    echo "PASS: $3"
}

# xbl_config.elf: reassembled via the unsigned GenXBLConfig path. The hex
# literal also exercises the int(val, 0) parsing.
edit "$FIXTURES/xbl_config.elf" xbl_config.elf \
    "$XBL_DTB/soc/ddr_common_dt/ddr_log_level_dt=0x7"
verify "$OUT/xbl_config.elf" "ddr_log_level_dt = <0x00000007>" "xbl_config.elf"

# uefi_dtbs.elf: a pure-DTB container rebuilt natively.
edit "$FIXTURES/uefi_dtbs.elf" uefi_dtbs.elf \
    "$UEFI_DTB/soc/quantum_dt/enter_quantum=0x1"
verify "$OUT/uefi_dtbs.elf" "enter_quantum = <0x00000001>" "uefi_dtbs.elf"

# Round-trip: qdte's own natively reassembled output (single LOAD phdr,
# p_align 0) must itself open and re-edit.
edit "$OUT/uefi_dtbs.elf" uefi_dtbs2.elf \
    "$UEFI_DTB/soc/quantum_dt/enter_quantum=0x2"
verify "$OUT/uefi_dtbs2.elf" "enter_quantum = <0x00000002>" "round-trip reassembly"

echo "nogui smoke test: OK"
