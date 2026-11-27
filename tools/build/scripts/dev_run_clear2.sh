#!/bin/sh
cp -f /mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/logs/vk_clear2 /tmp/pvr-vk/vk_clear2 2>/dev/null || true
chmod +x /tmp/pvr-vk/vk_clear2
systemctl stop greetd
sleep 2
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export PVR_DUMP_CMD=1
cd /tmp/pvr-vk
./vk_clear2 > /tmp/pvr-vk/clear2.log 2>&1
echo "rc=$?"
systemctl start greetd
grep -E "words=|first32|image mem|failed" /tmp/pvr-vk/clear2.log | head -6
grep "pvr-cmd-.*size=" /tmp/pvr-vk/clear2.log | head -6
