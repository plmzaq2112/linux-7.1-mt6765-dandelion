p = "/mnt/p41/etc/init.d/rcS"
s = open(p).read()

old = "[ -x /sbin/udevd ] && /sbin/udevd --daemon 2>/dev/null\n[ -x /sbin/udevadm ] && udevadm trigger 2>/dev/null && udevadm settle 2>/dev/null\n"
new = "[ -x /sbin/udevd ] && /sbin/udevd --daemon 2>/dev/null\ntimeout 20 udevadm trigger 2>/dev/null\ntimeout 20 udevadm settle 2>/dev/null\n"
assert old in s, "udev block not found"
s = s.replace(old, new, 1)
open(p, "w").write(s)
print("udev timeouts added")
print(s[s.find("# --- udev"):s.find("# --- touch")])
