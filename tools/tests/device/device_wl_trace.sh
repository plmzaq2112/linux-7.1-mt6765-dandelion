#!/bin/sh
# Short trace: when are frame callbacks sent vs when do commits arrive?
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export VK_KMS_DRM=/dev/dri/card1
export XDG_RUNTIME_DIR=/tmp/vk-wl-run
export WAYLAND_DISPLAY=wayland-vk

pkill -f vk_wl 2>/dev/null
pkill -f wl_test_client 2>/dev/null
rm -rf "$XDG_RUNTIME_DIR"
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"
systemctl stop greetd
trap 'pkill -f vk_wl 2>/dev/null; pkill -f wl_test_client 2>/dev/null; systemctl start greetd' EXIT
sleep 3

VK_WL_TRACE=1 VK_KMS_SECS=6 timeout 9 ./vk_wl > /tmp/vkwl_tr.txt 2>&1 &
CPID=$!
sleep 2
WL_CLIENT_FREERUN=1 WL_CLIENT_SURFACES=1 WL_CLIENT_SECS=3 timeout 6 \
    ./wl_test_client > /tmp/wlc_tr.txt 2>&1
wait $CPID
echo "== trace (t = ms)"
grep -E 'wl: (cb|commit) t=' /tmp/vkwl_tr.txt | tail -30
echo "== waits"
grep -E 'vkDeviceWaitIdle avg' /tmp/vkwl_tr.txt | tail -3
echo DONE
