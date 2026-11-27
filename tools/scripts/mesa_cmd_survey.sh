#!/bin/bash
M="$HOME/AI_Project/Redmi_9A/mesa-pvr/src/imagination/vulkan"
echo "=== cmd struct definitions ==="
grep -rn "typedef struct.*cmd_3d\|} pvr_cmd_3d\|struct pvr_rogue_fwif_cmd_3d\|cmd_3d;" "$M" --include="*.h" | head -10
grep -rn "cmd_ta\|cmd_transfer" "$M/winsys/pvrsrvkm/fw-api/pvr_rogue_fwif_shared.h" 2>/dev/null | head -10
echo
echo "=== fw-api file ==="
ls "$M/winsys/pvrsrvkm/fw-api/" 2>/dev/null
echo
echo "=== job render packing ==="
grep -n "cmd_3d\|cmd_ta\|sizeof" "$M/winsys/pvrsrvkm/pvr_srv_job_render.c" | head -20
echo
echo "=== job transfer packing ==="
grep -n "cmd_transfer\|sizeof" "$M/winsys/pvrsrvkm/pvr_srv_job_transfer.c" | head -20
