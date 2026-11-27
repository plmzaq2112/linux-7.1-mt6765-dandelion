#!/bin/sh
echo "=== devfreq ==="
ls /sys/class/devfreq 2>/dev/null
for d in /sys/class/devfreq/*; do
  [ -e "$d/cur_freq" ] || continue
  echo "$d: cur=$(cat $d/cur_freq 2>/dev/null) min=$(cat $d/min_freq 2>/dev/null) max=$(cat $d/max_freq 2>/dev/null) gov=$(cat $d/governor 2>/dev/null)"
done
echo "=== gpufreq proc ==="
ls /proc/gpufreq 2>/dev/null
head -5 /proc/gpufreq/gpufreq_var_dump 2>/dev/null
echo "=== clk summary (mfg/gpu) ==="
mount -t debugfs none /sys/kernel/debug 2>/dev/null
grep -iE 'mfg|gpu' /sys/kernel/debug/clk/clk_summary 2>/dev/null | head -10
echo "=== kernel cmdline ==="
cat /proc/cmdline
echo "=== pvrsrvkm params ==="
ls /sys/module/pvrsrvkm/parameters/ 2>/dev/null
for p in /sys/module/pvrsrvkm/parameters/*; do echo "$(basename $p)=$(cat $p 2>/dev/null)"; done
