#!/bin/bash
K=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion
KEY=$K/data/keys/ubuntu-ssh-key
O="-i $KEY -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=8 -o LogLevel=ERROR"
ssh $O root@169.254.195.201 'systemctl stop greetd; sleep 2; cd /tmp/pvr-vk; export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1 LD_LIBRARY_PATH=/tmp/pvr-vk PVR_DUMP_CS=1; timeout 60 ./vk_colored_quad >/tmp/cs_out.txt 2>/tmp/cs_colored.txt; echo "rc=$?"; systemctl start greetd' 2>&1 | tail -3
scp $O root@169.254.195.201:/tmp/cs_colored.txt $K/logs/cs_colored.txt 2>&1 | tail -2
scp $O root@169.254.195.201:/tmp/cs_out.txt $K/logs/cs_out.txt 2>&1 | tail -2
wc -l $K/logs/cs_colored.txt
