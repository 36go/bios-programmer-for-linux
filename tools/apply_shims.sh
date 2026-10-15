#!/usr/bin/env bash
#
# Re-apply the Linux/libUSB shims to a copy of the original AsProgrammer source.
#
# The original AsProgrammer binds to Windows DLLs (CH341DLL.DLL, CH347DLL.DLL,
# FTD2XX.DLL). This script restores those three units from a pristine upstream
# checkout and rewrites them so the project builds on Linux without any DLLs:
#
#   * ch347dll.pas  -> all external declarations replaced with no-op stubs
#   * D2XXUnit.pas  -> all external declarations inlined as no-op stubs
#   * ch341dll.pas  -> externals removed, CH341 API re-implemented on libUSB
#
# Usage:
#   UPSTREAM=/path/to/AsProgrammer/software ./apply_shims.sh /path/to/linux/src
#
# UPSTREAM must point at the original repository's "software" directory that
# still contains the untouched ch341dll.pas / ch347dll.pas / D2XXUnit.pas.
#
set -euo pipefail

UPSTREAM="${UPSTREAM:?set UPSTREAM to the original AsProgrammer 'software' directory}"
DEST="${1:?usage: UPSTREAM=... apply_shims.sh <dest-src-dir>}"
HERE="$(cd "$(dirname "$0")" && pwd)"

cp "$UPSTREAM/ch341dll.pas" "$DEST/ch341dll.pas"
cp "$UPSTREAM/ch347dll.pas" "$DEST/ch347dll.pas"
cp "$UPSTREAM/D2XXUnit.pas" "$DEST/D2XXUnit.pas"

python3 "$HERE/stub_unit.py" impl   "$DEST/ch347dll.pas"
python3 "$HERE/stub_unit.py" inline "$DEST/D2XXUnit.pas"
python3 "$HERE/patch_ch341.py"      "$DEST/ch341dll.pas"

echo "shims applied to $DEST"
