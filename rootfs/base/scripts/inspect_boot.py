import os

R = os.path.expanduser("~/ubuntu/rootfs")

def show(path, follow=True):
    p = os.path.join(R, path)
    if not os.path.lexists(p):
        print("MISSING", path)
        return
    if os.path.islink(p):
        tgt = os.readlink(p)
        real = os.path.realpath(p)
        print(f"LINK   {path} -> {tgt}   exists={os.path.exists(p)}")
        if os.path.exists(p):
            print(f"       real={os.path.relpath(real, R)} exec={os.access(p, os.X_OK)}")
    else:
        print(f"FILE   {path} size={os.path.getsize(p)} exec={os.access(p, os.X_OK)}")

for p in ["sbin/init", "usr/lib/systemd/systemd", "lib/systemd/systemd",
          "etc/systemd/system/default.target", "etc/fstab", "etc/machine-id",
          "etc/systemd/system/sysinit.target.wants/ubuntu-unmark.service",
          "etc/systemd/system/graphical.target.wants/ubuntu-mark.service",
          "lib/ld-linux-aarch64.so.1", "usr/lib/ld-linux-aarch64.so.1",
          "etc/systemd/system/focaltech-touch.service",
          "usr/libexec/phosh"]:
    show(p)

print("\n--- fstab ---")
print(open(os.path.join(R, "etc/fstab")).read())
print("--- machine-id ---")
print(repr(open(os.path.join(R, "etc/machine-id")).read()))
print("--- units ---")
for n in ("ubuntu-unmark.service", "ubuntu-mark.service"):
    print("###", n)
    print(open(os.path.join(R, "etc/systemd/system", n)).read())
