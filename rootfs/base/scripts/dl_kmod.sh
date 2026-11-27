#!/bin/sh
set -e
export DEBIAN_FRONTEND=noninteractive
rm -f /root/dlmarker2
touch /root/dlmarker2
sleep 1
apt-get install --download-only -y kmod >/tmp/aptdl2.log 2>&1 || { tail -20 /tmp/aptdl2.log; exit 1; }
grep -c '^Get:' /tmp/aptdl2.log || true
ls /var/cache/apt/archives/ | grep -E '^kmod|^libkmod' || true
