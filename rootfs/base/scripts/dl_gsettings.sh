#!/bin/sh
set -e
export DEBIAN_FRONTEND=noninteractive
apt-get install --download-only -y --no-install-recommends libglib2.0-bin dconf-cli >/tmp/aptdl3.log 2>&1 || { tail -20 /tmp/aptdl3.log; exit 1; }
grep '^Get:' /tmp/aptdl3.log
