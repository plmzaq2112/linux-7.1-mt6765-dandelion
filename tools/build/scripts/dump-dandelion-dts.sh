V="$HOME/dandelion-linux-kernel/01-pure-baseline/arch/arm64/boot/dts/mediatek"
echo "== dandelion dir =="
ls "$V/dandelion" | head -30
echo "== backlight refs =="
grep -rn -i -e backlight -e bled "$V/dandelion" "$V/dandelion.dts" 2>/dev/null | head -20
echo "== mt6370 refs =="
grep -rn -i mt6370 "$V/dandelion" "$V/dandelion.dts" 2>/dev/null | head -20
