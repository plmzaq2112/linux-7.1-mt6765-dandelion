#!/bin/bash
V=/home/a12bbb/dandelion-linux-kernel/01-pure-baseline/drivers/gpu/mediatek/gpu_rgx/m1.13ED5776728
O="/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline"/drivers/misc/pvr/ddk

for f in \
  services/server/devices/rogue/rgxstartstop.c \
  services/server/devices/rogue/rgxinit.c \
  services/server/devices/rogue/rgxpower.c \
  services/server/devices/rogue/rgxlayer_impl.c \
  services/server/env/linux/physmem_osmem_linux.c
do
  echo "=== $f"
  diff "$V/$f" "$O/$f" | head -14
done
