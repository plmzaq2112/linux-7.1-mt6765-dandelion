#!/bin/sh
U=dandelion
R=/run/user/1000
D=unix:path=/run/user/1000/bus
B=/sys/class/backlight/backlight

echo "=== gsd brightness get ==="
runuser -u $U -- env XDG_RUNTIME_DIR=$R DBUS_SESSION_BUS_ADDRESS=$D \
  busctl --user get-property org.gnome.SettingsDaemon.Power /org/gnome/SettingsDaemon/Power org.gnome.SettingsDaemon.Power.Screen Brightness 2>&1 | head -3

echo "=== set 50 via gsd ==="
runuser -u $U -- env XDG_RUNTIME_DIR=$R DBUS_SESSION_BUS_ADDRESS=$D \
  busctl --user set-property org.gnome.SettingsDaemon.Power /org/gnome/SettingsDaemon/Power org.gnome.SettingsDaemon.Power.Screen Brightness i 50 2>&1 | head -3
sleep 1
echo "sysfs cur=$(cat $B/brightness)"
cat /sys/kernel/debug/pwm | sed -n '2,4p'

echo "=== set 10 via gsd ==="
runuser -u $U -- env XDG_RUNTIME_DIR=$R DBUS_SESSION_BUS_ADDRESS=$D \
  busctl --user set-property org.gnome.SettingsDaemon.Power /org/gnome/SettingsDaemon/Power org.gnome.SettingsDaemon.Power.Screen Brightness i 10 2>&1 | head -3
sleep 1
echo "sysfs cur=$(cat $B/brightness)"
cat /sys/kernel/debug/pwm | sed -n '2,4p'
