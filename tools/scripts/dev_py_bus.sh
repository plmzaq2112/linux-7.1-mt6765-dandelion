#!/bin/sh
python3 - <<'PY'
ok = []
try:
    import gi
    from gi.repository import Gio, GLib
    ok.append("gi")
except Exception as e:
    print("gi:", e)
try:
    import dbus
    ok.append("dbus")
except Exception as e:
    print("dbus:", e)
try:
    import dbus_next
    ok.append("dbus_next")
except Exception as e:
    pass
print("available:", ok)
PY
