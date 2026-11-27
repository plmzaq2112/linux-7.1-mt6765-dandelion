#!/bin/sh
# A/B: is the 42 fps caused by idling or by frame-callback pacing?
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

run() {
    label="$1"; shift
    env "$@" VK_KMS_SECS=8 ./vk_wl > /tmp/vkwl_ab.txt 2>&1 &
    CPID=$!
    sleep 3
    WL_CLIENT_SURFACES=1 WL_CLIENT_SECS=15 ./wl_test_client > /tmp/wlclient_ab.txt 2>&1 &
    CLPID=$!
    wait $CPID
    kill $CLPID 2>/dev/null; wait $CLPID 2>/dev/null
    printf "%-24s " "$label"
    grep -E 'presented' /tmp/vkwl_ab.txt | sed 's/.*presented/presented/'
}

run "idle enabled" VK_X=1
run "idle disabled" VK_WL_NOIDLE=1
echo DONE
