#!/bin/bash
F="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity/drivers/misc/mediatek/lcm/ft8006s_vdo_hdp_boe_helitai/ft8006s_vdo_hdp_boe_helitai.c"
echo "=== bl_level table ==="
sed -n '185,205p' "$F"
echo
echo "=== setbacklight ==="
sed -n '520,565p' "$F"
