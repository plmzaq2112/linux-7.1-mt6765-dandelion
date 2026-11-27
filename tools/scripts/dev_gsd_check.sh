#!/bin/sh
UID_=1000
U=dandelion
R=/run/user/$UID_
run_gsd() {
    runuser -u $U -- env XDG_RUNTIME_DIR=$R DBUS_SESSION_BUS_ADDRESS=unix:path=$R/bus \
        busctl --user "$@"
}
PROP=org.gnome.SettingsDaemon.Power.Screen
OBJ=/org/gnome/SettingsDaemon/Power
IFACE=org.gnome.SettingsDaemon.Power

echo "before: $(run_gsd get-property $IFACE $OBJ $PROP Brightness)"
run_gsd set-property $IFACE $OBJ $PROP Brightness i 25
sleep 2
echo "sysfs: $(cat /sys/class/backlight/panel-backlight/brightness)"
echo "after: $(run_gsd get-property $IFACE $OBJ $PROP Brightness)"
run_gsd set-property $IFACE $OBJ $PROP Brightness i 80
sleep 2
echo "sysfs2: $(cat /sys/class/backlight/panel-backlight/brightness)"
echo "after2: $(run_gsd get-property $IFACE $OBJ $PROP Brightness)"
