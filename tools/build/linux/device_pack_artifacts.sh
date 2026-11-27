#!/bin/sh
# Package device-side build products (tests, debug modules, oracles) into a tarball.
set -e
cd /tmp || exit 1
rm -f /tmp/pvr-artifacts.tar.gz

tar czf /tmp/pvr-artifacts.tar.gz \
    -C / \
    --exclude='*.core' \
    tmp/pvr-vk \
    root/pvrsrvkm.ko.orig \
    root/pvrsrvkm-hwrt.ko \
    root/pvrsrvkm-rgn.ko \
    root/pvrsrvkm-dmabuf.ko \
    root/pvrsrvkm-kicktime.ko \
    root/pvrsrvkm-stream.ko \
    root/pvrsrvkm-stream2.ko \
    root/gles_clear \
    root/gles_triangle \
    root/gles_depth \
    root/dev_gles_clear_full.sh \
    root/dev_gles_golden.sh \
    root/dev_gles_tri_golden.sh \
    2>/dev/null || true

ls -l /tmp/pvr-artifacts.tar.gz
tar tzf /tmp/pvr-artifacts.tar.gz | wc -l
echo "=== contents (top) ==="
tar tzf /tmp/pvr-artifacts.tar.gz | head -20
