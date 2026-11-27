#!/bin/bash
for d in ~/dandelion-linux-kernel/*/; do
  [ -d "$d/.git" ] || continue
  echo "===== $d"
  git -C "$d" log -1 --format='HEAD %h %ad %s' --date=short 2>/dev/null
  git -C "$d" remote -v 2>/dev/null | head -1
  git -C "$d" branch --show-current 2>/dev/null
  if [ -f "$d/arch/arm64/boot/dts/mediatek/mt6765.dtsi" ]; then
    printf '  mt6765.dtsi top-reg(11cd0000): %s\n' "$(grep -c '11cd0000' "$d/arch/arm64/boot/dts/mediatek/mt6765.dtsi")"
    printf '  msdc50 clock provider: %s\n' "$(grep -o '<&[a-z]* CLK_TOP_MSDC50_0>' "$d/arch/arm64/boot/dts/mediatek/mt6765.dtsi" | head -1)"
  fi
  ls "$d/arch/arm64/boot/dts/mediatek/" 2>/dev/null | grep -i dandelion
done
