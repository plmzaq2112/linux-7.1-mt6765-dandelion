#!/bin/sh
cat > /root/vk-vendor/icd.json <<'EOF'
{"file_format_version":"1.0.0","ICD":{"library_path":"/root/vk-vendor/hw/vulkan.mt6765.so","api_version":"1.0.0"}}
EOF

systemctl stop greetd
sleep 2
rmmod pvrsrvkm
sleep 1
insmod /root/pvrsrvkm-dump2.ko pvr_apm=0
sleep 1
echo 4 > /sys/module/pvrsrvkm/parameters/pvr_dump_kick
echo 4 > /sys/module/pvrsrvkm/parameters/pvr_dump_tq
dmesg -C

export VK_ICD_FILENAMES=/root/vk-vendor/icd.json
export LD_LIBRARY_PATH=/root/vk-vendor:/root/vk-vendor/hw
cd /tmp/pvr-vk
./vk_clear2 > /tmp/vk-vendor-run.log 2>&1
echo "rc=$?"
sleep 1
echo "--- test output ---"
grep -E "words=|first32|failed|image mem" /tmp/vk-vendor-run.log | head -5
echo "--- dmesg ---"
dmesg | grep -E "pvr-dump-3D|pvr-dump-TA|pvr-dump:" | head -20

systemctl start greetd
