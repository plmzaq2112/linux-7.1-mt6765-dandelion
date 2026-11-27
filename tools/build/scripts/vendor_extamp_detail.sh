#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"

echo "=== extamp pinctrl definitions ==="
sed -n '558,585p' "$V/arch/arm64/boot/dts/mediatek/custom_common.dtsi"

echo
echo "=== dandelion dts extamp/spk/amp ==="
grep -rn "extamp\|speaker_amp\|spk_amp\|SPEAKER" "$V/arch/arm64/boot/dts/mediatek/dandelion/" 2>/dev/null | head -20

echo
echo "=== AudDrv_GPIO_EXTAMP_Select body ==="
sed -n '450,500p' "$V/sound/soc/mediatek/common_int/mtk-auddrv-gpio.c"

echo
echo "=== who calls EXTAMP select ==="
grep -rn "EXTAMP_Select\|EXTAMP_HIGH\|EXTAMP_LOW" "$V/sound/soc/mediatek" 2>/dev/null | head -20

echo
echo "=== mtk-soc-speaker-amp.c head ==="
sed -n '1,60p' "$V/sound/soc/mediatek/common_int/mtk-soc-speaker-amp.c"
