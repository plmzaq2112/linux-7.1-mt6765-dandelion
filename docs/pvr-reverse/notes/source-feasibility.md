# 图形驱动源码可行性（以 TI Rogue DDK 仓库为参照）

结论先说：**UM（用户态）驱动源码拿不到；但同版本 DDK 的内核态源码是公开的，而且我们的二进制与它版本完全一致。**
"从二进制反推全部源码"不可行；"拿到同版本内核源码 + 用同版本 UM 预编译二进制做对照"可行，且已在本目录完成。

## 1. 参照仓库里有什么（FACT）

`https://git.ti.com/git/graphics/ti-img-rogue-umlibs.git`
分支 `linuxws/dunfell/k5.10/1.13.5776728`（与设备 DDK 版本号一致）已克隆到 `_src/ti-umlibs-1.13`：

- 161 个文件 / 19.3 MB，`targetfs/` 下**全是预编译产物**，没有任何 `.c/.cpp`：
  - `libsrv_um.so.1.13.5776728`、`libusc.so.1.13.5776728`、`libglslcompiler.so.1.13.5776728`
  - `libGLESv2_PVR_MESA.so.1.13.5776728`、`libGLESv1_CM_PVR_MESA.so.1.13.5776728`
  - `libpvr_dri_support.so`、`libPVRScopeServices.so`、`libsutu_display.so`
  - `lib/firmware/rgx.fw.22.104.208.318`、`rgx.sh.22.104.208.318`
  - 只有 Khronos 公共头文件（`EGL/`、`GLES*/`、`KHR/`）
- README 原文：*"This package contains the user mode libraries and binaries for Rogue. These user mode libraries are developed by Imagination Technologies (IMG)."*

→ TI 这个仓库是"UM 二进制分发"，不是源码仓库。IMG 的 UM 驱动从不公开源码。

## 2. 二进制与 TI 同版本对照（FACT，脚本 `_src/cmp.sh`）

用 `readelf --dyn-syms` 取导出符号（去掉 UND），比较 MTK vendor 64 位库与 TI 1.13.5776728：

| 我们的库 | MTK 导出符号 | TI 同版本 | 共同 | MTK 独有 |
| --- | --- | --- | --- | --- |
| `lib64/libsrv_um.so` | 295 | 301 | **295** | **0** |
| `lib64/libusc.so` | 30 | 32 | 30 | 0 |
| `lib64/libglslcompiler.so` | 12 | 14 | 12 | 0 |
| `lib64/egl/libGLESv2_mtk.so` | 359 | 361 | 359 | 0 |
| `lib64/egl/libGLESv1_CM_mtk.so` | 146 | 148 | 146 | 0 |
| `lib64/libPVRScopeServices.so` | 2 | 4 | 2 | 0 |

TI 多出来的 2~6 个符号都是 Linux 侧专用（`PVRSRVNativePrintStackTrace`、`PVRDRM*`、wayland 支持等）。

版本字符串也一致：
- 我们：`libGLESv2_mtk.so` → `OpenGL ES 3.2 build 1.13@5776728`；`libsrv_um.so` → `1.13@5776728`
- TI：同名库 → 同样的 `1.13@5776728`

**含义**：MTK 没有改 DDK 主体 ABI，只是换编译目标（Android/bionic）+ 加了自己的外围库。所以 TI 同版本二进制可以作为"stock 参考件"，用于函数级 diff 和符号对齐。

## 3. 真正的源码：内核态 pvrsrvkm（FACT）

`https://git.ti.com/git/graphics/ti-img-rogue-driver.git` 分支 `1.13-5776728/linux-k5.10`，
已克隆到 `_src/ti-rogue-driver-1.13`：**806 个文件 / 13.9 MB 真源码**。

- `include/pvrversion.h`: `PVRVERSION_STRING "Rogue_DDK_Linux_WS rogueddk 1.13@5776728"` → 与设备 UM 二进制同 DDK 版本
- 目录结构：
  - `services/server/` —— 内核态服务（MMU、内存、同步、电源、RGX 硬件初始化）
  - `services/shared/common/` —— UM/KM 共享代码与结构体（`devicemem.c` 等）
  - `generated/rogue/*_bridge/` —— **bridge 层**：`client_*_bridge.h`（UM 侧）与 `server_*_bridge.c`（KM 侧），即 `/dev/pvrsrvkm` 的 ioctl 协议定义
  - `hwdefs/` —— RGX 寄存器/硬件定义（GE8320 属于 8XE 系列，同族）
  - `kernel/drivers/staging/imgtec/` —— DRM 接口、`pvr_drm.h`
- 1118 个 `PVRSRV_BRIDGE_*` 操作标识符、2213 个 `PVRSRV_*` 类型/宏

这是唯一能拿到"源码级"细节的部分，覆盖：驱动加载、设备节点、内存/MMU、同步原语、bridge 调用协议、RGX 固件交互。

## 4. 拿不到的部分及原因

| 组件 | 源码可得性 | 说明 |
| --- | --- | --- |
| `libsrv_um.so` / `libusc.so` / `libglslcompiler.so` / GLES 前端 | ✗ 无源码 | IMG 只发预编译 UM；任何"同版本"公开仓库都只有二进制 |
| `libIMGegl.so`（PVR EGL 实现） | ✗ | 同上；TI wayland 版用 `libpvr_dri_support.so` 代替，不构成同组件对照（UNKNOWN） |
| `gralloc.rogue.so` / `hwcomposer.mt6765.so` | ✗ | IMG+MTK 集成层，非公开 |
| `libged.so` / `libgpu_aux.so` / `libPVRMtkutils.so` / `libgpud.so` / MEOW | ✗ | MTK 自研（GED = GPU Extension Driver），只能反汇编 |
| 内核态 `pvrsrvkm` | ✓ 有源码 | 但 TI 版面向 J721E/AM62；MT6765 的内核驱动要用 MTK 内核源码（未在本目录） |

## 5. 已产出的可用工件

```
_src/
├─ ti-umlibs-1.13/        # TI 1.13.5776728 UM 预编译库（对照用，非源码）
├─ ti-rogue-driver-1.13/  # 同版本 KM 源码（可读、可编译研究）
├─ cmp.sh                 # 符号对照脚本
├─ cmp/*.a.txt  *.b.txt   # 逐库导出符号表
├─ cmp/*.mtk_only.txt     # MTK 独有符号（上述主体库均为空）
└─ cmp/libsrv_um.srcmap.txt
```

## 6. 下一步可做的（按性价比）

1. **内核 ABI 文档化**：从 `generated/rogue/*/common_*_bridge.h` + `server_*_bridge.c` 提取全部 bridge 号/参数结构，与 `libsrv_um.so` 的导出函数对应，形成 ioctl 参考手册 —— 这一步能接近"源码级"理解 UM↔KM 交互。
2. **MTK 层反汇编**：`libged.so`、`libgpu_aux.so`、`libPVRMtkutils.so` 体量小（50~107 KB），适合 IDA/Ghidra 出调用图。
3. **同版本二进制 diff**：用 TI 库与 MTK 库逐函数比对（字符串引用、常量表），定位 MTK 为 Android/bionic 做的改动。
4. 若必须内核源码贴合本机：需要 MT6765 的 MTK 内核源码包（含 `drivers/gpu/.../pvrsrvkm`），而不是 TI 的 J721E 版。
