#!/bin/sh
# Idle + damage tracking: a static client must make the compositor go idle;
# a partial-damage client must keep all three slots in sync.
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

echo "== static client: compositor should idle"
VK_KMS_SECS=12 VK_COMP_VERIFY=1 ./vk_wl > /tmp/vkwl_idle.txt 2>&1 &
CPID=$!
sleep 3
WL_CLIENT_STATIC=1 WL_CLIENT_SURFACES=1 WL_CLIENT_SECS=20 ./wl_test_client > /tmp/wlclient_idle.txt 2>&1 &
CLPID=$!
wait $CPID
kill $CLPID 2>/dev/null
wait $CLPID 2>/dev/null
grep -E 'presented|cpu:|verify: slot' /tmp/vkwl_idle.txt | tail -5

echo "== animated (full damage) client: baseline"
VK_KMS_SECS=10 VK_COMP_VERIFY=1 ./vk_wl > /tmp/vkwl_anim.txt 2>&1 &
CPID=$!
sleep 3
WL_CLIENT_SURFACES=1 WL_CLIENT_SECS=20 ./wl_test_client > /tmp/wlclient_anim.txt 2>&1 &
CLPID=$!
wait $CPID
kill $CLPID 2>/dev/null
wait $CLPID 2>/dev/null
grep -E 'presented|cpu:' /tmp/vkwl_anim.txt | tail -3

echo "== partial damage client: only small rects uploaded, slots in sync"
VK_KMS_SECS=10 VK_COMP_VERIFY=1 ./vk_wl > /tmp/vkwl_part.txt 2>&1 &
CPID=$!
sleep 3
WL_CLIENT_PARTIAL=1 WL_CLIENT_SURFACES=1 WL_CLIENT_SECS=20 ./wl_test_client > /tmp/wlclient_part.txt 2>&1 &
CLPID=$!
wait $CPID
kill $CLPID 2>/dev/null
wait $CLPID 2>/dev/null
grep -E 'surface upload|presented|cpu:|verify: surf|verify: slot' /tmp/vkwl_part.txt | tail -12
echo DONE
