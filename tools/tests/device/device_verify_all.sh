#!/bin/sh
# Full verification sweep, all steps bounded by the individual scripts.
echo "######## 1. vk_comp regression ########"
sh /tmp/device_regress_all.sh 2>&1 | grep -E 'words=|color:|depth:|blend:|depth32:|vk_geom|layer0 rect|diff=|presented' | head -20

echo "######## 2. Wayland shm (3 toplevels) ########"
sh /tmp/device_wl_test.sh 2>&1 | grep -E 'mapped surface|verify: surf|verify: slot|presented|client: exiting'

echo "######## 3. Wayland dma-buf (3 toplevels) ########"
sh /tmp/device_wl_dmabuf.sh 2>&1 | grep -E 'dmabuf: imported|verify: surf|verify: slot|client: exiting'

echo "######## 4. idle + partial damage ########"
sh /tmp/device_wl_idle.sh 2>&1 | grep -E 'presented|cpu:|verify: slot|surface upload 200x150 rect|client: exiting'

echo "######## state ########"
systemctl is-active greetd
pgrep -c phoc
lsmod | grep -c pvrsrvkm
pgrep -c vk_wl
echo ALLDONE
