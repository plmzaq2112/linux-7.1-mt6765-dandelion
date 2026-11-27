import os

D = os.path.expanduser("~/dandelion-ubuntu")
R = os.path.join(D, "rootfs")

# fstab: root on userdata (p41)
with open(os.path.join(R, "etc/fstab"), "w") as f:
    f.write("""# <file system> <mount point> <type> <options> <dump> <pass>
/dev/mmcblk0p41  /            ext4  defaults,noatime  0 1
proc             /proc        proc  defaults          0 0
sysfs            /sys         sysfs defaults          0 0
devpts           /dev/pts     devpts defaults         0 0
tmpfs            /tmp         tmpfs  defaults          0 0
""")

# marker used by the initramfs to accept this partition
open(os.path.join(R, "etc/dandelion-rootfs-ok"), "w").write("ubuntu-dandelion\n")

# machine-id (systemd refuses to boot without one in some images)
os.makedirs(os.path.join(R, "etc"), exist_ok=True)
open(os.path.join(R, "etc/machine-id"), "w").write("0123456789abcdef0123456789abcdef\n")

print("fstab, rootfs marker and machine-id written")
