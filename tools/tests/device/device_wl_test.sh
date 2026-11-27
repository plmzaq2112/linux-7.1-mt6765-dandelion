#!/bin/sh
# Wayland compositor + test client, end to end, on the phone.
# The client outlives the compositor so the final readback still sees the
# mapped surfaces (the compositor verifies its last presented buffer).
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

VK_KMS_SECS=24 VK_COMP_VERIFY=1 ./vk_wl > /tmp/vkwl.txt 2>&1 &
CPID=$!
sleep 4
WL_CLIENT_SECS=40 ./wl_test_client > /tmp/wlclient.txt 2>&1 &
CLPID=$!
wait $CPID
kill $CLPID 2>/dev/null
wait $CLPID 2>/dev/null

echo "== compositor"
grep -E 'wl: (mapped|listening|pointer)|textures:|presented|verify: onscreen|verify: surf|verify: slot|zero-copy' /tmp/vkwl.txt | tail -24
echo "== client"
grep -E 'client: ' /tmp/wlclient.txt | head -20
echo DONE
