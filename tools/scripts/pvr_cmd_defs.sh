#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline/drivers/misc/pvr"
echo "=== RGXFWIF_CMD3D definitions ==="
grep -rn "RGXFWIF_CMD3D" "$T" --include="*.h" | head -10
echo
echo "=== RGXFWIF_CMDTA ==="
grep -rn "RGXFWIF_CMDTA" "$T" --include="*.h" | head -10
echo
echo "=== RGXFWIF_CMDTRANSFER ==="
grep -rn "RGXFWIF_CMDTRANSFER" "$T" --include="*.h" | head -10
echo
echo "=== alignchecks ==="
grep -rn "RGXFW_ALIGN_CHECKS_INIT" "$T" --include="*.h" | head -5
