#!/bin/bash
for d in "$HOME/pixelos-build/kernel-src" "$HOME/kernel-oc/android_kernel_xiaomi_blossom" "$HOME/kernel-oc/sashimi_kernel_xiaomi_blossom"; do
	echo "== $d"
	if [ -d "$d" ]; then
		head -4 "$d/Makefile" 2>/dev/null | tr '\n' ' '
		echo
		find "$d" -maxdepth 5 -iname '*mipi_tx*' 2>/dev/null | head -5
		find "$d" -maxdepth 6 -iname '*mipi*' -path '*video*' 2>/dev/null | head -5
	fi
done
