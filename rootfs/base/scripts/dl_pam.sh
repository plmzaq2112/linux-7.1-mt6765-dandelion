#!/bin/sh
set -e
export DEBIAN_FRONTEND=noninteractive
apt-get install --download-only -y --reinstall libpam-modules libpam-modules-bin libpam-runtime libpam0g >/tmp/aptdl4.log 2>&1 || { tail -20 /tmp/aptdl4.log; exit 1; }
grep '^Get:' /tmp/aptdl4.log
