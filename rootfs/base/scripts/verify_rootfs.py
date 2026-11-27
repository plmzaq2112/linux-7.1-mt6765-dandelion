import os

D = os.path.expanduser("~/dandelion-ubuntu")
R = os.path.join(D, "rootfs")

checks = [
    "usr/bin/phosh",
    "usr/bin/phoc",
    "usr/share/wayland-sessions/phosh.desktop",
    "etc/greetd/config.toml",
    "lib/modules/focaltech_ts.ko",
    "lib/firmware/focaltech_ab_ts_fw_helitai.bin",
    "etc/systemd/system/focaltech-touch.service",
    "etc/systemd/system/multi-user.target.wants/greetd.service",
    "etc/systemd/system/multi-user.target.wants/focaltech-touch.service",
    "etc/systemd/system/multi-user.target.wants/seatd.service",
    "sbin/init",
    "etc/fstab",
]
for c in checks:
    p = os.path.join(R, c)
    print(("OK   " if os.path.exists(p) else "MISS ") + c)

# greetd config content
p = os.path.join(R, "etc/greetd/config.toml")
print("\n--- greetd config ---")
print(open(p).read() if os.path.exists(p) else "(missing)")

# size without proot artifacts
import subprocess
print("rootfs size:", subprocess.run(["du", "-sh", "--exclude=host-rootfs", R],
                                     capture_output=True, text=True).stdout.strip())
