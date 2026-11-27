for t in "$HOME/dandelion-linux-kernel/01-pure-baseline" "$HOME/pixelos-build/kernel-src" "$HOME/kernel-oc/android_kernel_xiaomi_blossom"; do
	echo "== $t"
	ls "$t/drivers/gpu/mediatek/" 2>/dev/null | head -12
	ls -d "$t"/drivers/gpu/mediatek/gpu_rgx 2>/dev/null
done
