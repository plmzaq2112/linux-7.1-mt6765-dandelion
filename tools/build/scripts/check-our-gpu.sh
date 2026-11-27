R="$HOME/AI Project/Redmi 9A/kernel 7.1 mainline"
echo "== gpu dirs =="
ls "$R/drivers/gpu/" 2>/dev/null
echo "== mtk gpu in tree =="
ls "$R/drivers/gpu/mediatek" 2>/dev/null | head
echo "== defconfig gpu =="
grep -i -e MTK_GPU -e MALI -e PVR "$R/arch/arm64/configs/dandelion_defconfig" 2>/dev/null | head
echo "== .config gpu =="
grep -i -e MTK_GPU -e PVR -e DRM_POWERVR "$R/out/.config" 2>/dev/null | head
echo "== firmware =="
ls "$R/firmware" 2>/dev/null | head
