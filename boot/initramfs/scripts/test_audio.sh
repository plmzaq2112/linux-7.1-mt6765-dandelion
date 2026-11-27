#!/bin/sh
# Run on device after boot (root). Loads audio modules in a controlled way.
set -x
cd /root/audio || exit 1

echo "== pstore (previous crash) =="
ls -l /sys/fs/pstore/ 2>/dev/null
for f in /sys/fs/pstore/dmesg-ramoops-*; do
    [ -f "$f" ] || continue
    echo "--- $f (tail) ---"
    tail -60 "$f"
done

echo "== load common + afe =="
insmod snd-soc-mtk-common.ko
insmod snd-soc-mt6765-pcm.ko
echo "afe rc=$?"
sleep 1
dmesg | tail -30
echo "== cards =="
cat /proc/asound/cards 2>/dev/null
