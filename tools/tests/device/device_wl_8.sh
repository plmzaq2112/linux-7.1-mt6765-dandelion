#!/bin/sh
# Scale test: 8 Wayland toplevels, animated, composited at vsync.
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export VK_KMS_DRM=/dev/dri/card1
export XDG_RUNTIME_DIR=/tmp/vk-wl-run
export WAYLAND_DISPLAY=wayland-vk

rm -rf "$XDG_RUNTIME_DIR"
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"

systemctl stop greetd
trap 'systemctl start greetd' EXIT
sleep 3

VK_KMS_SECS=18 VK_COMP_VERIFY=1 ./vk_wl > /tmp/vkwl8.txt 2>&1 &
CPID=$!
sleep 3
WL_CLIENT_SURFACES=8 WL_CLIENT_SECS=30 ./wl_test_client > /tmp/wlclient8.txt 2>&1 &
CLPID=$!
wait $CPID
kill $CLPID 2>/dev/null
wait $CLPID 2>/dev/null

echo "== compositor"
grep -E 'mapped surface|presented|verify: surf|verify: slot|avg:' /tmp/vkwl8.txt | tail -14
echo "== client"
grep -cE 'client: surf[0-7] configure' /tmp/wlclient8.txt
echo DONE
