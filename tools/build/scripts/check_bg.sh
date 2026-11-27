#!/bin/bash
D=/mnt/c/Users/31806/.local/share/opencode/shell/a1725204a68ff843cc80c95e35d9436996bfd697
ls -l "$D"/*.out | tail -6
for f in "$D"/sh_212c*.out "$D"/sh_212d*.out; do
  echo "== $f"
  tr -d '\000' < "$f" | tail -8
done
echo "== ssh procs"
ps -ef | grep -c "[s]sh "
