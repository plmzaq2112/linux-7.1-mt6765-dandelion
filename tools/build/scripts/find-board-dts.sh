for t in "$HOME/dandelion-linux-kernel/01-pure-baseline" "$HOME/pixelos-build/kernel-src" "$HOME/kernel-oc/android_kernel_xiaomi_blossom"; do
	echo "== $t"
	ls "$t/arch/arm64/boot/dts/mediatek/" 2>/dev/null | grep -i -e dandelion -e 6762 -e 6765 | head -10
done
