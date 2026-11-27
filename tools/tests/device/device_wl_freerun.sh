#!/bin/sh
# Isolate the bottleneck: callback-driven vs free-running client.
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
    set -- "$@" 
    VK_KMS_SECS=7 ./vk_wl > /tmp/vkwl_fr.txt 2>&1 &
    CPID=$!
    sleep 2
    env "$@" WL_CLIENT_SURFACES=1 WL_CLIENT_SECS=12 ./wl_test_client > /dev/null 2>&1 &
    CLPID=$!
    wait $CPID
    kill $CLPID 2>/dev/null; wait $CLPID 2>/dev/null
    printf "%-18s " "$label"
    grep -E 'presented' /tmp/vkwl_fr.txt | sed 's/.*presented/presented/'
    grep -E 'cpu:' /tmp/vkwl_fr.txt | sed 's/.*cpu:/  cpu:/'
}

run callback
run freerun WL_CLIENT_FREERUN=1
echo DONE
