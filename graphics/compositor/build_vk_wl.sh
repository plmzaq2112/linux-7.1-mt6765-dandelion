#!/bin/bash
set -e
W=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion
M="$HOME/AI_Project/Redmi_9A/mesa-pvr"
L="$W/logs"
P="$L/wl-proto"
SR="$W/logs/wlsys"

mkdir -p "$P"
wayland-scanner private-code "$W/src/wayland/wl/xdg-shell.xml" "$P/xdg-shell-protocol.c"
wayland-scanner server-header "$W/src/wayland/wl/xdg-shell.xml" "$P/xdg-shell-server-protocol.h"
wayland-scanner client-header "$W/src/wayland/wl/xdg-shell.xml" "$P/xdg-shell-client-protocol.h"
wayland-scanner private-code "$W/src/wayland/wl/linux-dmabuf-unstable-v1.xml" "$P/linux-dmabuf-unstable-v1-protocol.c"
wayland-scanner server-header "$W/src/wayland/wl/linux-dmabuf-unstable-v1.xml" "$P/linux-dmabuf-unstable-v1-server-protocol.h"
wayland-scanner client-header "$W/src/wayland/wl/linux-dmabuf-unstable-v1.xml" "$P/linux-dmabuf-unstable-v1-client-protocol.h"

if [ ! -f "$L/comp_vert_spv.h" ] || [ "$W/src/wayland/comp.vert" -nt "$L/comp_vert_spv.h" ]; then
    glslangValidator -V "$W/src/wayland/comp.vert" -o "$L/comp.vert.spv"
    glslangValidator -V "$W/src/wayland/comp.frag" -o "$L/comp.frag.spv"
    python3 "$W/scripts/spv_to_header.py" comp_vert_spv "$L/comp.vert.spv" "$L/comp_vert_spv.h"
    python3 "$W/scripts/spv_to_header.py" comp_frag_spv "$L/comp.frag.spv" "$L/comp_frag_spv.h"
fi

# XKB keymap: generated once on the build host, embedded in the compositor.
if [ ! -f "$L/xkb_keymap.h" ] || [ "$W/src/wayland/wl/xkbmk.c" -nt "$L/xkb_keymap.h" ]; then
    gcc -O2 "$W/src/wayland/wl/xkbmk.c" -lxkbcommon -o "$L/xkbmk"
    "$L/xkbmk" > "$L/xkb_keymap.txt"
    python3 "$W/src/wayland/wl/keymap_to_header.py" "$L/xkb_keymap.txt" "$L/xkb_keymap.h"
fi

CFLAGS="-O2 -g0 -I$L -I$M/include -I/usr/include/libdrm -I$P -I$W/src/wayland -I$W/scripts"
# aarch64 libwayland/ffi taken from the phone (logs/wlsys); link by path so no
# symlinks are needed on the Windows drive.
WLLIBS="$SR/libwayland-server.so.0.22.0 $SR/libffi.so.8.1.4"
WLCLLIBS="$SR/libwayland-client.so.0.22.0 $SR/libffi.so.8.1.4"
XKBC="$SR/libxkbcommon.so.0.0.0"

aarch64-linux-gnu-gcc $CFLAGS \
    "$W/src/wayland/vk_wl.c" "$W/src/wayland/wl/wl_backend.c" "$P/xdg-shell-protocol.c" \
    "$P/linux-dmabuf-unstable-v1-protocol.c" \
    "$L/libvulkan.so.1" $WLLIBS -Wl,-rpath-link,"$SR" \
    -L /usr/lib/aarch64-linux-gnu -ldrm -lm -o "$L/vk_wl"

aarch64-linux-gnu-gcc $CFLAGS \
    "$W/src/wayland/wl/wl_test_client.c" "$P/xdg-shell-protocol.c" \
    "$P/linux-dmabuf-unstable-v1-protocol.c" \
    $WLCLLIBS $XKBC -Wl,-rpath-link,"$SR" \
    -L /usr/lib/aarch64-linux-gnu -ldrm -lm -o "$L/wl_test_client"

aarch64-linux-gnu-gcc -O2 -g0 "$W/src/wayland/wl/uinput_kbd.c" -o "$L/uinput_kbd"

ls -l "$L/vk_wl" "$L/wl_test_client" "$L/uinput_kbd"
