#!/bin/sh
# run on device as root; inspect audio stack
E="env XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus"
echo "=== tools ==="
for c in wpctl pactl pw-play paplay gst-launch-1.0 tinyplay speaker-test; do
    printf '%s: ' "$c"
    command -v "$c" || echo missing
done
echo "=== wpctl status ==="
sudo -u dandelion $E wpctl status 2>&1 | head -40
echo "=== pactl cards ==="
sudo -u dandelion $E pactl list cards 2>&1 | head -30
