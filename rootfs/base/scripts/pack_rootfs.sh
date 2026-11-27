#!/bin/bash
# Pack the Ubuntu rootfs for streaming onto p41.
# Excludes proot's host-rootfs bind dir and runtime virtual filesystems.
set -e
cd "$(dirname "$0")"
rm -f ubuntu-rootfs.tar.gz
tar --numeric-owner \
    --exclude=./host-rootfs \
    --exclude=./proc/* \
    --exclude=./sys/* \
    --exclude=./dev/* \
    --exclude=./run/* \
    --exclude=./tmp/* \
    -czf ubuntu-rootfs.tar.gz -C rootfs .
ls -lh ubuntu-rootfs.tar.gz
echo "files: $(tar -tzf ubuntu-rootfs.tar.gz | wc -l)"
echo "md5: $(md5sum ubuntu-rootfs.tar.gz | cut -d' ' -f1)"
