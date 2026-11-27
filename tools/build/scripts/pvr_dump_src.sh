#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline/drivers/misc/pvr/ddk/services/server/devices/rogue"
echo "=== rgxta3d dump helper ==="
sed -n '3290,3400p' "$T/rgxta3d.c"
echo
echo "=== rgxtransfer submit head ==="
grep -n "PVRSRVRGXSubmitTransferKM" "$T/rgxtransfer.c" | head
grep -n "pui32CommandSize\|pui32FWCommand\|pvFWCommand" "$T/rgxtransfer.c" | head -20
