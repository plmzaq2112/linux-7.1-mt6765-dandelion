#!/bin/sh
# Cleanup + one-shot fps attribution measurement.
# Everything is bounded by timeout so this script can never hang.
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

run_case() {
    label="$1"; n="$2"; shift 2
    timeout 14 env VK_KMS_SECS=8 ./vk_wl > /tmp/vkwl_c.txt 2>&1 &
    CPID=$!
    sleep 2
    timeout 10 env "$@" WL_CLIENT_SURFACES="$n" WL_CLIENT_SECS=6 \
        ./wl_test_client > /tmp/wlc_c.txt 2>&1
    wait $CPID
    printf "%-22s " "$label"
    grep -E 'presented' /tmp/vkwl_c.txt | sed 's/.*presented/presented/'
    grep -E 'cpu:' /tmp/vkwl_c.txt | sed 's/.*cpu:/  cpu:/'
    grep -E 'avg:' /tmp/vkwl_c.txt | sed 's/.*avg:/  avg:/'
    grep -E 'exiting' /tmp/wlc_c.txt | sed 's/.*client/client/'
}

run_case "1 surf callback" 1
run_case "1 surf freerun" 1 WL_CLIENT_FREERUN=1
run_case "8 surf callback" 8
echo DONE
