#!/bin/bash
for T in "$HOME/AI_Project/Redmi_9A"/kernel_4.19.325_*; do
    [ -d "$T" ] || continue
    echo "== $(basename $T)"
    grep -rn "sGeomRegs;\|sTransRegs;\|s3DRegs;" "$T" 2>/dev/null | head -5
done
