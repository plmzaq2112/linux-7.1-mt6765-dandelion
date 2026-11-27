#!/bin/bash
set -e
BOOT="/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline"/rootfs/ubuntu/boot/boot-console2.img
WORK=/tmp/dtwork
rm -rf "$WORK"; mkdir -p "$WORK"
python3 - "$BOOT" "$WORK/live.dtb" <<'PY'
import struct, sys
src, dst = sys.argv[1], sys.argv[2]
d = open(src,'rb').read()
page = struct.unpack_from('<I', d, 36)[0]
ks = struct.unpack_from('<I', d, 8)[0]
rs = struct.unpack_from('<I', d, 16)[0]
ds = struct.unpack_from('<I', d, 1648)[0]
au = lambda x,p: ((x+p-1)//p)*p
dt = page + au(ks,page) + au(rs,page)
open(dst,'wb').write(d[dt:dt+ds])
print('dtb', ds)
PY
dtc -I dtb -O dts "$WORK/live.dtb" -o "$WORK/live.dts" 2>/dev/null
echo "=== keypad node ==="
grep -n -A28 'keyboard@10010000' "$WORK/live.dts" | head -36
echo "=== gpio-keys node ==="
grep -n -A28 'gpio-keys {' "$WORK/live.dts" | head -36
echo "=== keypad pinctrl ==="
grep -n -i -B2 -A12 'kpd' "$WORK/live.dts" | head -40
