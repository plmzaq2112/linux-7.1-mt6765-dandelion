#!/bin/bash
A=/home/a12bbb/AI_Project/Redmi_9A/kernel_4.19.325_kernelsu/kernel/drivers/gpu/mediatek/gpu_rgx/m1.13ED5776728/services/include/rogue/rgx_fwif_km.h
B=/home/a12bbb/AI_Project/Redmi_9A/kernel_7.1_mainline/drivers/misc/pvr/ddk/services/include/rogue/rgx_fwif_km.h

echo "=== 1.13 HWRTDATA ==="
awk '/^typedef struct RGXFWIF_HWRTDATA_TAG/,/RGXFWIF_HWRTDATA;/' "$A" | head -120

echo "=== 7.1 HWRTDATA ==="
awk '/^typedef struct RGXFWIF_HWRTDATA_TAG/,/RGXFWIF_HWRTDATA;/' "$B" | head -120
