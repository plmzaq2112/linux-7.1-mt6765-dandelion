#!/bin/sh
# native-check.sh - 在设备上验证 TI/IMG glibc 版 DDK 1.13 UM（零垫片）
# 用法: sh native-check.sh <ti-umlibs 的 usr 目录> [安装目录=/opt/pvr]
set -u

SRC=${1:?用法: $0 <.../wayland/release/usr> [dest]}
DEST=${2:-/opt/pvr}
LOG=/tmp/pvr-native-check.log
: > "$LOG"

say() { echo "$@" | tee -a "$LOG"; }
has() { command -v "$1" >/dev/null 2>&1; }

say "== 1. 内核侧节点"
for n in /dev/dri/card* /dev/dri/renderD* /dev/pvr_sync; do
    [ -e "$n" ] && say "  OK  $n" || say "  MISS $n"
done
say "  dmesg: $(dmesg | grep -i 'pvr\|rgx' | tail -3 | tr '\n' ';')"

say ""
say "== 2. 确认是 glibc（不是 musl）"
if ldd --version 2>&1 | grep -qi 'GNU libc\|GLIBC'; then
    say "  OK  $(ldd --version | head -1)"
else
    say "  !!  当前不是 glibc，原生包无法直接加载"
    exit 2
fi

say ""
say "== 3. 安装到 $DEST"
sh "$(dirname "$0")/install-pvr-um.sh" "$SRC" "$DEST" >>"$LOG" 2>&1 || { say "  安装失败，见 $LOG"; exit 3; }
mkdir -p /usr/lib/dri
install -m 0644 "$DEST"/lib/dri/pvr_dri.so /usr/lib/dri/pvr_dri.so 2>/dev/null \
    && say "  OK  /usr/lib/dri/pvr_dri.so" || say "  !!  无法写入 /usr/lib/dri"

say ""
say "== 4. EGL/GLES"
. "$DEST/env.sh"
if has eglinfo; then
    say "-- eglinfo -B"
    eglinfo -B 2>&1 | head -25 | tee -a "$LOG"
else
    say "  (包内没有 eglinfo，跳过)"
fi
if has gles2test1; then
    say "-- gles2test1（5 秒超时）"
    timeout 5 gles2test1 2>&1 | tail -10 | tee -a "$LOG"
    say "  exit=$?"
else
    say "  (包内没有 gles2test1，跳过)"
fi

say ""
say "== 5. 内核日志（失败时看这里）"
dmesg | grep -iE 'pvr|rgx|pvrsrv' | tail -20 | tee -a "$LOG"

say ""
say "结果汇总: $LOG"
