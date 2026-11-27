#!/bin/bash
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity/drivers/gpu/mediatek/gpu_rgx/m1.13ED5776728"
echo "=== include dirs ==="
ls "$V/include" && echo "--- rogue:" && ls "$V/include/rogue" | head -20
echo
echo "=== CMD3D definition site ==="
grep -rn "RGXFWIF_CMD3D_STRUCT\|} RGXFWIF_CMD3D\|RGXFWIF_CMD3D;" "$V/include" | head -10
echo
echo "=== CMDTRANSFER definition site ==="
grep -rn "} RGXFWIF_CMDTRANSFER\|RGXFWIF_CMDTRANSFER;" "$V/include" | head -10
