#!/bin/sh
cd /tmp/pvr-vk || exit 1
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
export VK_KMS_DRM=/dev/dri/card1
systemctl stop greetd
sleep 3

echo "== regression: clear / tri / quads / ds"
timeout 60 ./vk_clear2 2>/dev/null | grep words=
timeout 60 ./vk_triangle 2>/dev/null | grep words=
timeout 60 ./vk_colored_quad 2>/dev/null | grep words=
timeout 60 ./vk_textured_quad 2>/dev/null | grep words=
timeout 60 ./vk_ds 2>/dev/null | grep -E 'color:|depth:|blend:'
VK_DS_D32=1 timeout 60 ./vk_ds 2>/dev/null | grep -E 'depth32:'

echo "== geom sizes"
for b in vk_geom32 vk_geom64 vk_geom128 vk_geom320x480; do
  printf "  %-16s " "$b"
  timeout 60 ./$b 2>/dev/null | grep -E 'bbox|words=' | tr '\n' ' '
  echo
done

echo "== compositor 8 layers (textured, dynamic scissor)"
VK_COMP_LAYERS=8 VK_KMS_SECS=4 VK_COMP_VERIFY=1 timeout 60 ./vk_comp > /tmp/comp_f.txt 2>&1
grep -E 'verify: slot=0|presented|rect=' /tmp/comp_f.txt

systemctl start greetd
echo DONE
