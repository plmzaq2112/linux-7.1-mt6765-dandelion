# 纯原生（零垫片）运行方案

> **状态（2026-11-24）：已实机证伪，仅留档。**
> 三道门中第三道（`RGXFWIF_CMD3D` 结构体 352 vs 320）属编译期 ABI，无法绕过。
> 现状与结论请见 `纯原生方案评估.md`，失败记录见 `../notes/failures.md` F-001。

## 一句话

有。用 **TI/IMG 官方的 glibc 版 DDK 1.13 UM 包**（`ti-img-rogue-umlibs` 分支 `1.13.5776728`）替换现在这套
"Android bionic 库 + libb.so 垫片 + ELF 补丁 + libEGL/libgbm 桥"。
它是同一份 DDK、同版本号、同 bridge ABI，但**本身就是 glibc + Mesa 前端**，不需要任何 shim。

## 为什么能直接用（FACT）

| 检查项 | 结果 | 证据 |
| --- | --- | --- |
| DDK 版本 | 与内核 `1.13@5776728` 一致 | TI 包内 `libsrv_um.so.1.13.5776728`、`1.13@5776728` 字符串 |
| bridge ABI | 25 个 `generated/rogue/*/common_*_bridge.h` 与本地内核树逐字节相同（忽略 CR） | 上次对照脚本，25/25 identical |
| 动态依赖 | `libsrv_um.so` 只依赖 **libm/libdl/librt/libpthread/libc**，无任何 Android/vendor 库 | `readelf -d` |
| 设备节点 | 搜索 `/dev/dri/card%d`、`/dev/dri/renderD%d`、`/dev/pvr_sync`，与你内核暴露的完全一致 | `strings libsrv_um.so` |
| 前端 | Mesa 20.0.1 的 `libEGL`/`libgbm`/`libglapi` + `dri/pvr_dri.so`（`__driDriverGetExtensions_pvr`） | `dri.pc: Version 20.0.1`、符号表 |
| 内核页大小 | 你的配置是 `CONFIG_ARM64_4K_PAGES=y`、`PAGE_SHIFT=12`；TI 有专门的 `arm64_page_size_4k/1.13.5776728` 分支（内容与默认分支同尺寸） | `kernel/configs/dandelion-7.1.config`、git 分支列表 |
| 版本校验 | KM 只比 MAJ/MIN（`pvrversion.h:65-66` 打包，`srvcore.c:557` 比较） | 源码 |

顺带能解决 `proposals/pvr64-perf/ANALYSIS.md` 里排名 1、3 的两个损耗：
Mesa 的 GBM/DRI 交换链是 DRI 驱动自己实现的，不需要 `glFinish` 兜底，也不需要自己写 `gbm_surface`。

## 安装与验证（设备上）

```sh
# 1) 把 TI 包里的 usr/ 拷到设备，例如 /root/pvr-native
#    （_src/ti-umlibs-1.13-4k/targetfs/j721e_linux/wayland/release/usr）

# 2) 安装到 /opt/pvr（不覆盖系统 Mesa）
/root/linux-gpu/install-pvr-um.sh /root/pvr-native

# 3) 把 DRI 后端放到 loader 的默认搜索路径（pvr_dri.so 不与其他驱动重名）
install -D /opt/pvr/lib/dri/pvr_dri.so /usr/lib/dri/pvr_dri.so

# 4) 验证
. /opt/pvr/env.sh
eglinfo -B 2>&1 | head -30        # 期望 PowerVR / Imagination
gles2test1                        # DDK 自带三角形，跑通即原生 UM↔KM 全链路 OK
```

桌面（phoc/wlroots）直接用这套原生库，不再经过 `pvr-bridge`：

```sh
export LD_LIBRARY_PATH=/opt/pvr/lib
export MESA_LOADER_DRIVER_OVERRIDE=pvr
export WLR_RENDERER=gles2
phoc
```

## 已知风险（必须在设备上实测）

1. **FW 版本串**：TI 的 `libsrv_um.so` 里有 `22.104.208.318`（TI 的 FW 构建号），你用的是 MTK 的 `rgx.fw`（114,688 B）。若 UM 在连接时校验 FW 版本，可能报 `BVNC/FW mismatch`。
   处理：先跑 `eglinfo`；失败就 `dmesg | grep -i pvr` 看具体错误码；必要时把 `dist/vendor-pvr64/firmware/` 换成 TI 的 `rgx.fw.22.104.208.318` 再试（两者都是 1.13 协议）。
2. **平台假设**：TI 这份是 J721E/AM62 的构建，UM 里可能带 TI 平台的显示/电源假设（`libsutu_display.so` 之类）。桌面路径若崩，先只用离屏 `gles2test1` 验证 UM↔KM，再上合成器。
3. **Mesa 20.0.1 较老**：wlroots 0.17 需要 EGL 1.5 + `EGL_EXT_image_dma_buf_import`，20.0.1 都有；但 `gbm_surface` 的 modifier 协商可能与 MTK DRM 不匹配（还是会退回 linear，但至少是原生 Mesa 路径）。
4. **BVNC**：UM 里有 `PVRSRV_ERROR_BVNC_UNSUPPORTED`；BVNC 由 KM 上报，KM 表里已有 `22.87.104.18`，大概率不受影响。

## 如果这条不通

那就只剩"把 bionic 垫片做薄"这一条：
- 垫片里目前只有 4 处是**必须**的（RELR 标签、`sysconf(0x27)`、`pthread_*` 结构、ZVA 规避），其余（`__android_log_print`、property、CallStack、zlib 包装）都是空实现；
- 这 4 处都可以按之前分析的方向做小：ZVA 规避换成 128B 向量拷贝、mutex 保持 glibc 后端（已够快），重点仍是 `glFinish` 与 linear buffer（`ANALYSIS.md`）。
