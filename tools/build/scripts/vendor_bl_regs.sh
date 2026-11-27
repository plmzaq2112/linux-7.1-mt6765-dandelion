#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity/drivers/misc/mediatek/lcm/ft8006s_vdo_hdp_boe_helitai/ft8006s_vdo_hdp_boe_helitai.c"
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline/drivers/gpu/drm/panel/panel-fitipower-ft8006s.c"
echo "=== vendor: 0x51/0x53/0x55/0x5e/0x5f ==="
grep -nE "\{0x5[135ef],|\{0x51," "$V" | head -20
echo
echo "=== mainline: 0x51/0x53/0x55 ==="
grep -nE "0x5[135ef]" "$T" | head -20
echo
echo "=== vendor CABC / HBM knobs ==="
grep -niE "cabc|hbm|high brightness|elvss|vsp|vsn" "$V" | head -20
