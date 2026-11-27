#!/bin/sh
echo "=== backlight devices ==="
for b in /sys/class/backlight/*; do
    echo "$b type=$(cat $b/type 2>/dev/null) max=$(cat $b/max_brightness) cur=$(cat $b/brightness)"
done
echo
echo "=== gsd power ==="
ps aux | grep -E "gsd-power|gsd-backlight|gnome-settings" | grep -v grep | head -5
echo
echo "=== gsd brightness via dbus ==="
runuser -u dandelion -- env XDG_RUNTIME_DIR=/run/user/1000 \
  busctl --user get-property org.gnome.SettingsDaemon.Power /org/gnome/SettingsDaemon/Power org.gnome.SettingsDaemon.Power.Screen Brightness 2>&1 | head -5
echo
echo "=== journal backlight ==="
journalctl -b --no-pager 2>/dev/null | grep -iE "backlight|brightness" | tail -8
