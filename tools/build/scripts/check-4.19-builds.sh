#!/bin/bash
for d in 02-kernelsu 03-pure-variant 04-debug; do
  echo "=== $d"
  ls ~/dandelion-linux-kernel/$d/arch/arm64/boot/Image* 2>/dev/null | head -3
  find ~/dandelion-linux-kernel/$d -name 'pvrsrvkm.ko' 2>/dev/null | head -2
done
echo "=== 01 readme ==="
head -30 ~/dandelion-linux-kernel/01-pure-baseline/README.md
echo "=== build-tools ==="
ls ~/dandelion-linux-kernel/01-pure-baseline/build-tools/
