#!/bin/sh
R=/mnt/p41/etc/init.d/rcS

if [ ! -f "$R" ]; then
  echo "no rcS"
  exit 1
fi

if grep -q "dandelion-rcs-debug" "$R"; then
  echo "already"
else
  # insert debug redirect right after the shebang
  sed -i '2i\
# dandelion-rcs-debug: log everything to p41\
exec > /dandelion-rcs.log 2>\&1\
set -x' "$R"
  echo "patched"
fi

head -8 "$R"
