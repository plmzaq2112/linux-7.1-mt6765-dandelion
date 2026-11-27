#!/bin/sh
set -e
R=/tmp/pvr-vk
export VK_ICD_FILENAMES=$R/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=$R
export VK_KMS_DRM=/dev/dri/card1
export XDG_RUNTIME_DIR=/run/user/0
export WAYLAND_DISPLAY=wayland-vk
mkdir -p $XDG_RUNTIME_DIR
chmod 700 $XDG_RUNTIME_DIR

systemctl stop greetd 2>/dev/null || true
sleep 1
rm -f $XDG_RUNTIME_DIR/$WAYLAND_DISPLAY $XDG_RUNTIME_DIR/$WAYLAND_DISPLAY.lock \
      /tmp/vkwl_kbd.txt /tmp/wlcli_kbd.txt

restore() {
    kill $CK 2>/dev/null || true
    kill $CC 2>/dev/null || true
    kill $CP 2>/dev/null || true
    systemctl start greetd 2>/dev/null || true
}
trap restore EXIT INT TERM

# Virtual keyboard: creates node immediately, injects after 8s.
$R/uinput_kbd 8000 > /tmp/uinput_kbd.txt 2>&1 &
CK=$!
sleep 1
KBD_DEV=$(for e in /sys/class/input/event*/device/name; do
  n=$(cat "$e" 2>/dev/null); case "$n" in *vk-wl-test-kbd*) echo "/dev/input/${e#/sys/class/input/}";; esac
done | sed 's#/device/name##' | head -1)
echo "kbd_dev=$KBD_DEV"
export VK_WL_KBD="$KBD_DEV"

$R/vk_wl --verify > /tmp/vkwl_kbd.txt 2>&1 &
CP=$!
sleep 3

WL_CLIENT_SECS=12 $R/wl_test_client > /tmp/wlcli_kbd.txt 2>&1 &
CC=$!
sleep 14

kill $CC 2>/dev/null || true
wait $CC 2>/dev/null || true
kill $CP 2>/dev/null || true
wait $CP 2>/dev/null || true
kill $CK 2>/dev/null || true
wait $CK 2>/dev/null || true

echo "=== uinput ==="
tail -5 /tmp/uinput_kbd.txt
echo "=== compositor kbd ==="
grep -E 'kbd:|seat|wl_keyboard' /tmp/vkwl_kbd.txt | head -15
echo "=== client kbd ==="
grep -E 'keymap|keyboard|key |modifiers|focus' /tmp/wlcli_kbd.txt | head -30
echo "=== verify ==="
grep -E 'verify: surf|verify: slot' /tmp/vkwl_kbd.txt | tail -5
echo "=== done ==="
