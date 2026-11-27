#!/bin/sh
# 安装 TI/IMG Rogue DDK 1.13.5776728 Linux(glibc) 用户态到 /opt/pvr
# 用法: install-pvr-um.sh <.../targetfs/j721e_linux/wayland/release/usr> [目标目录]
# 不会覆盖 /usr/lib 下的系统 Mesa 库。

set -eu

SRC=${1:?用法: $0 <ti-umlibs .../wayland/release/usr> [dest]}
DEST=${2:-/opt/pvr}

[ -d "$SRC/lib" ] || { echo "找不到 $SRC/lib，检查路径是否指向 .../release/usr"; exit 1; }

echo "==> 安装到 $DEST"
mkdir -p "$DEST/lib/dri" "$DEST/bin"

# 库（保留符号链接）
cp -a "$SRC"/lib/*.so* "$DEST/lib/" 2>/dev/null || true
if [ -d "$SRC/lib/dri" ]; then
    cp -a "$SRC"/lib/dri/*.so "$DEST/lib/dri/"
fi

# 补齐 loader 需要的无版本名软链
cd "$DEST/lib"
[ -e libEGL.so ]        || ln -sf libEGL.so.1.0.0 libEGL.so
[ -e libEGL.so.1 ]      || ln -sf libEGL.so.1.0.0 libEGL.so.1
[ -e libGLESv2.so ]     || ln -sf libGLESv2.so.2.0.0 libGLESv2.so
[ -e libGLESv2.so.2 ]   || ln -sf libGLESv2.so.2.0.0 libGLESv2.so.2
[ -e libgbm.so ]        || ln -sf libgbm.so.1.0.0 libgbm.so
[ -e libgbm.so.1 ]      || ln -sf libgbm.so.1.0.0 libgbm.so.1
[ -e libglapi.so.0 ]    || ln -sf libglapi.so.0.0.0 libglapi.so.0
for n in libsrv_um libusc libglslcompiler libpvr_dri_support libGLESv2_PVR_MESA libGLESv1_CM_PVR_MESA; do
    v=$(ls -1 ${n}.so.[0-9]* 2>/dev/null | head -n1 || true)
    [ -n "$v" ] && { [ -e ${n}.so ] || ln -sf "$v" ${n}.so; }
done

# 工具
for b in eglinfo gles1test1 gles2test1 gles3test1 pvrsrvctl pvrdebug; do
    [ -f "$SRC/bin/$b" ] && cp -a "$SRC/bin/$b" "$DEST/bin/"
done

cat > "$DEST/env.sh" <<EOF
# source 这个文件后使用 /opt/pvr 的 EGL/GLES（PowerVR DDK 1.13）
export LD_LIBRARY_PATH=$DEST/lib\${LD_LIBRARY_PATH:+:\$LD_LIBRARY_PATH}
export LIBGL_DRIVERS_PATH=$DEST/lib/dri
export MESA_LOADER_DRIVER_OVERRIDE=pvr
export PATH=$DEST/bin\${PATH:+:\$PATH}
EOF

echo "==> 完成。验证："
echo "    . $DEST/env.sh"
echo "    eglinfo -B | head -30"
echo "    gles2test1"
