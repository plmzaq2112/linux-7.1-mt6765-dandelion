#!/bin/sh
echo "== wayland-protocols"
ls /usr/share/wayland-protocols/stable/xdg-shell/ 2>&1
echo "== libs"
ls /usr/lib/aarch64-linux-gnu/ | grep libffi 2>&1
ls /usr/lib/aarch64-linux-gnu/ | grep libexpat 2>&1
echo "== wayland programs"
ls /usr/bin | grep -i wayland 2>&1
echo "== shells/clients"
ls /usr/bin | grep -iE 'weston|foot|sway|labwc|cage|gtk4|gtk3' 2>&1
echo "== phoc idle"
ls -d /usr/share/phoc 2>&1
