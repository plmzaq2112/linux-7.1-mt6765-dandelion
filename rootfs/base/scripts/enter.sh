#!/bin/bash
# Enter the arm64 Ubuntu rootfs via proot+qemu (no root needed).
# Usage: ./enter.sh /path/inside/rootfs/script.sh
set -e
cd "$(dirname "$0")"
exec env PROOT_NO_SECCOMP=1 ./proot -0 -r ./rootfs -q ./qemu-aarch64-static \
    -b /proc -b /dev -b /sys -b /etc/resolv.conf -w / \
    /usr/bin/env -i HOME=/root PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    TERM=xterm LANG=C.UTF-8 DEBIAN_FRONTEND=noninteractive \
    /bin/bash "$@"
