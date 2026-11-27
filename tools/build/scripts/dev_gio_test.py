#!/usr/bin/env python3
import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib

addr = "unix:path=/run/user/1000/bus"
conn = Gio.DBusConnection.new_for_address_sync(
    addr,
    Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT |
    Gio.DBusConnectionFlags.MESSAGE_BUS_CONNECTION,
    None, None)

def setp(pct):
    conn.call_sync(
        "org.gnome.SettingsDaemon.Power",
        "/org/gnome/SettingsDaemon/Power",
        "org.freedesktop.DBus.Properties",
        "Set",
        GLib.Variant("(ssv)", ("org.gnome.SettingsDaemon.Power.Screen",
                               "Brightness", GLib.Variant("i", pct))),
        None,
        Gio.DBusCallFlags.NONE,
        3000, None)

def getp():
    r = conn.call_sync(
        "org.gnome.SettingsDaemon.Power",
        "/org/gnome/SettingsDaemon/Power",
        "org.freedesktop.DBus.Properties",
        "Get",
        GLib.Variant("(ss)", ("org.gnome.SettingsDaemon.Power.Screen", "Brightness")),
        None, Gio.DBusCallFlags.NONE, 3000, None)
    return r.unpack()[0]

print("before", getp())
setp(40)
print("after", getp())
