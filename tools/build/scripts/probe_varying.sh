#!/bin/bash
# 1.13 DDK: which files mention varying / PPP
D=/home/a12bbb/AI_Project/Redmi_9A/kernel_4.19.325_kernelsu/kernel/drivers/gpu/mediatek/gpu_rgx/m1.13ED5776728
echo "=== 1.13 DDK grep VARYING ==="
grep -rln 'VARYING' "$D" --include=*.h --include=*.c 2>/dev/null | head -20
echo "=== 1.13 DDK grep PPPE / PPP ==="
grep -rln 'PPPE\|PPP_CTRL\|RGX_CR_PPP' "$D" --include=*.h --include=*.c 2>/dev/null | head -20

M=/home/a12bbb/AI_Project/Redmi_9A/mesa-pvr
echo "=== ppp.xml VARYING ==="
grep -n 'VARYING' "$M/src/imagination/csbgen/rogue/ppp.xml" | head -40
echo "=== ppp.xml TA_STATE_PDS_VARYINGBASE context ==="
grep -n 'VARYINGBASE' -A 12 "$M/src/imagination/csbgen/rogue/ppp.xml" | head -40
