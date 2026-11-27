#!/bin/sh
set -e
export DEBIAN_FRONTEND=noninteractive
touch /root/dlmarker
sleep 1
apt-get update >/tmp/aptupd.log 2>&1 || true
apt-get install --download-only -y --no-install-recommends \
    gnome-session-bin gnome-settings-daemon gnome-settings-daemon-common \
    >/tmp/aptdl.log 2>&1 || { tail -20 /tmp/aptdl.log; exit 1; }
echo "=== new debs ==="
find /var/cache/apt/archives -name '*.deb' -newer /root/dlmarker -printf '%f\n' | sort
echo "=== total ==="
find /var/cache/apt/archives -name '*.deb' -newer /root/dlmarker | wc -l
