#!/bin/bash
M="$HOME/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan"
echo "=== pvr_rogue_fwif.h: cmd structs ==="
grep -n "cmd_3d\|cmd_ta\b\|cmd_transfer\|ROGUE_CMD" "$M/winsys/pvrsrvkm/fw-api/pvr_rogue_fwif.h" | head -30
echo
echo "=== where cmd_3d is written ==="
grep -rn "cmd_3d" "$M" --include="*.c" | head -20
echo
echo "=== where cmd_transfer is written ==="
grep -rn "cmd_transfer" "$M" --include="*.c" | head -20
