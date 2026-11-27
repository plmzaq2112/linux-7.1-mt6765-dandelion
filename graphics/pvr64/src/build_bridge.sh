#!/bin/bash
# Build the glibc-side PowerVR bridge libraries (libEGL.so.1, libGLESv2.so.2,
# libgbm.so.1) for phoc/wlroots.  Output: dist/vendor-pvr64/bridge/
set -euo pipefail
[ -f "$0" ] && cd "$(dirname "$0")/../.."   # else: run from repo root
SRC=src/pvr64
VEND=dist/vendor-pvr64/patched/lib64
OUT=dist/vendor-pvr64/bridge
CC=${CC:-aarch64-linux-gnu-gcc}
CFLAGS="-O2 -fPIC -Wall -Wextra -fvisibility=hidden -shared"
mkdir -p "$OUT"

$CC $CFLAGS -Wl,-soname,libgbm.so.1 -o "$OUT/libgbm.so.1" $SRC/pvr_gbm.c
$CC $CFLAGS -Wl,-soname,libEGL.so.1 -o "$OUT/libEGL.so.1" $SRC/pvr_egl.c -ldl -lpthread
$CC $CFLAGS -Wl,-soname,libGLESv2.so.2 -o "$OUT/libGLESv2.so.2" $SRC/pvr_glesv2.c \
	-Wl,--no-as-needed -L"$VEND/egl" -l:libGLESv2_mtk.so -Wl,--allow-shlib-undefined -ldl

for f in "$OUT"/*.so.*; do
	echo "== $f"
	aarch64-linux-gnu-readelf -dW "$f" | grep -E 'NEEDED|SONAME'
	aarch64-linux-gnu-objdump -T "$f" | grep -oE 'GLIBC_[0-9.]+' | sort -uV | tail -1
done
