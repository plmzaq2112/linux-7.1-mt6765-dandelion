#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
echo "=== sTransRegs / s3DRegs / sGeomRegs anywhere ==="
grep -rn "sTransRegs\|s3DRegs\|sGeomRegs" "$T/drivers/misc/pvr" | head -20
echo
echo "=== any 'rgx_fwif.h' with cmd structs ==="
find "$T/drivers/misc/pvr" -name "*.h" | xargs grep -ln "RGXFWIF_CMDTRANSFER\|RGXFWIF_CMDTA\b" 2>/dev/null | head
echo
echo "=== module sig/modversions in out/.config ==="
grep -E "CONFIG_MODULE_SIG|CONFIG_MODVERSIONS|CONFIG_MODULE_FORCE" "$T/out/.config"
