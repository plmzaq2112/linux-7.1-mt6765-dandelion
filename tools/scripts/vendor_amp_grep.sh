#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"

echo "=== 7.1 tree / out ==="
ls "$T" 2>/dev/null | head -8
if [ -d "$T/out" ]; then
    echo "out: yes"
    ls -l "$T/out/Module.symvers" 2>/dev/null
else
    echo "out: no"
fi

echo
echo "=== vendor machine driver files ==="
grep -rln "extamp\|rt5509\|speaker_amp\|Speaker_Amp\|spk_amp\|rcvspk" "$V/sound/soc/mediatek" 2>/dev/null | head -12

echo
echo "=== vendor GPIO/regulator for amp ==="
grep -rn "extamp\|spk_amp\|speaker_amp\|rcvspk" "$V/sound/soc/mediatek/mt6765" 2>/dev/null | head -20
grep -rn "extamp\|spk_amp\|speaker_amp" "$V/arch/arm64/boot/dts/mediatek" 2>/dev/null | head -20
