#!/bin/bash
for T in "$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity" "$HOME/AI_Project/Redmi_9A/kernel_4.19.325_blossom" "$HOME/AI_Project/Redmi_9A/kernel_4.19.325_variant" "$HOME/AI_Project/Redmi_9A/kernel_4.19.325_kernelsu"; do
    [ -d "$T" ] || continue
    echo "== $T"
    grep -rln "RGXFWIF_CMD3D" "$T" 2>/dev/null | head -5
done
