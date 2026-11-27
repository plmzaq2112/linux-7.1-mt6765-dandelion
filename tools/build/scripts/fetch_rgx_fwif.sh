#!/bin/bash
W=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion
URL="https://chromium.googlesource.com/chromiumos/third_party/kernel/+/chromeos-4.4/drivers/gpu/drm/img-rogue/1.10/rgx_fwif.h?format=TEXT"
curl -sL --max-time 90 "$URL" | base64 -d > "$W/logs/rgx_fwif_110.h" 2>/dev/null
ls -l "$W/logs/rgx_fwif_110.h"
grep -n "RGXFWIF_CMD3D\|typedef struct _RGXFWIF_3D_REGS\|s3DRegs" "$W/logs/rgx_fwif_110.h" | head
