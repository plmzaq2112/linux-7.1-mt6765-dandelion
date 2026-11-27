#!/bin/bash
set -u
cd "$HOME"
rm -f alpican-gpu.tar.gz
for u in \
  "https://ghfast.top/https://github.com/99-blossom/kernel_xiaomi_blossom_linux/archive/refs/heads/gpu.tar.gz" \
  "https://gh-proxy.com/https://github.com/99-blossom/kernel_xiaomi_blossom_linux/archive/refs/heads/gpu.tar.gz" \
  "https://ghproxy.net/https://github.com/99-blossom/kernel_xiaomi_blossom_linux/archive/refs/heads/gpu.tar.gz" \
  "https://github.moeyy.xyz/https://github.com/99-blossom/kernel_xiaomi_blossom_linux/archive/refs/heads/gpu.tar.gz"; do
	echo "== trying $u"
	code=$(curl -sIL -o /dev/null -w '%{http_code}' --max-time 20 "$u" 2>/dev/null)
	echo "   HTTP $code"
	if [ "$code" = "200" ] || [ "$code" = "302" ]; then
		if curl -L --max-time 900 -o alpican-gpu.tar.gz "$u"; then
			ls -l alpican-gpu.tar.gz
			break
		fi
	fi
done
if [ -f alpican-gpu.tar.gz ]; then
	tar -tzf alpican-gpu.tar.gz >/dev/null 2>&1 && echo "tarball OK"
fi
