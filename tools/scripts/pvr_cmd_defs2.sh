#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline/drivers/misc/pvr"
echo "=== where are the structs defined? ==="
grep -rn "RGXFWIF_CMD3D_STRUCT\|RGXFWIF_CMDTA_STRUCT\|RGXFWIF_CMDTRANSFER_STRUCT" "$T" --include="*.h" | head -10
echo
echo "=== fwif headers ==="
ls "$T"/ddk/include/rogue/ | head -20
echo
echo "=== grep cmd3d in rgx_fwif* ==="
grep -rn "CMD3D" "$T"/ddk/include/rogue/rgx_fwif*.h | head -10
