#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"

echo "=== mtk-soc-speaker-amp.c: gpio/regulator/power ==="
grep -nE "gpio|regulator|supply|enable|reset|pinctrl|power" \
    "$V/sound/soc/mediatek/common_int/mtk-soc-speaker-amp.c" 2>/dev/null | head -40

echo
echo "=== mtk-sp-spk-amp.c: rt5509 i2c probe / gpio ==="
grep -nE "gpio|regulator|supply|i2c|probe|0x34|reset" \
    "$V/sound/soc/mediatek/common/mtk-sp-spk-amp.c" 2>/dev/null | head -30

echo
echo "=== mtk-auddrv-gpio.c extamp ==="
grep -nE "extamp|EXTAMP|gpio_set|pinctrl" \
    "$V/sound/soc/mediatek/common_int/mtk-auddrv-gpio.c" 2>/dev/null | head -30

echo
echo "=== cust.dtsi speaker_amp node ==="
sed -n '118,140p' "$V/arch/arm64/boot/dts/mediatek/dandelion/cust.dtsi" 2>/dev/null
