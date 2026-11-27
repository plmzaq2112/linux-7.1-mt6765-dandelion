import os, subprocess, sys

D = os.path.expanduser("~/dandelion-ubuntu")
script = sys.argv[1]

cmd = [
    os.path.join(D, "proot"), "-0",
    "-r", os.path.join(D, "rootfs"),
    "-q", os.path.join(D, "qemu-aarch64-static"),
    "-b", "/proc", "-b", "/dev", "-b", "/sys", "-b", "/etc/resolv.conf",
    "-w", "/",
    "/usr/bin/env", "-i",
    "HOME=/root",
    "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
    "TERM=xterm", "LANG=C.UTF-8", "DEBIAN_FRONTEND=noninteractive",
    "/bin/bash", script,
]
env = dict(os.environ)
env["PROOT_NO_SECCOMP"] = "1"
sys.exit(subprocess.call(cmd, env=env))
