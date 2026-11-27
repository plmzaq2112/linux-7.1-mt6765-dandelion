# 2026-11-24 复核：kernel 7.1 mainline（原 k71-build，已改名）

路径：`\\wsl.localhost\Ubuntu-26.04\home\a12bbb\AI Project\Redmi 9A\kernel 7.1 mainline`
分支：`dandelion-7.1`（HEAD `09afeff6c "gpu-bringup:"`），远端 `evilMyQueen/linux-mt6765.git`

## 与 11-23 那次复核相比，真正新增的（FACT）

| 项 | 内容 | 证据 |
| --- | --- | --- |
| 源码改动 | **仅 1 行**：`sysconfig.c` 里 `bEnableRDPowIsland` 由 `true` 改为 `false`（`MTK_USE_HW_APM` 分支） | `git diff -- sysconfig.c`；现在 `#if/#else` 两支都是 false，条件编译成了死代码 |
| 重新编译 | `out/out/drivers/misc/pvr/ddk/pvrsrvkm.ko`，2026-11-24 11:35，vermagic `7.1.0-mt6765+` | `ls`/`modinfo` |
| 修复仍在 | ko 里有 `g_pvr_open_lock.0`，`nm -u` 有 `vmap` | `nm` |
| 自解 vendor | `vendor-unpack/`（untracked）：`vendor.img`、`extracted/`（Android 64 位图形库）、`firmware/rgx.fw` 114,688 B、`firmware/rgx.sh` 309,200 B | 目录列表 |
| 原厂 FW 校验 | `rgx.sh` md5 `6456299eddd62b1834f71e81b4d6bb67`，与 `gpu-bringup/docs/STATUS.md` 里记录的"stock vendor image"一致 | `md5sum` |
| TI FW 对照 | TI 1.13 的 `rgx.fw.22.104.208.318` md5 `a0faf4f7...`、`rgx.sh` md5 `7a88c37e...`，与 MTK 的**不同** | `md5sum` |
| 文档清理 | `gpu-bringup/*`、`GPU_BRINGUP.md` 在工作区被删除（HEAD 里还是"卡在 POW"的求助帖） | `git status` |
| 杂项 | `rgx_bvnc_table_km.h` 仅改了注释（去掉 "bus=32 was tried and did NOT fix FW boot"） | `git diff` |
| 其他 | `drivers/mmc/host/mtk-sd.c.r3-before` 备份文件未清理 | `git status` |

**没有新提交**：HEAD 仍是 11-21~23 的 `gpu-bringup:` 系列，工作区改动全部未提交；公开仓库里目前还是"未解决"状态。

## 仍未处理（沿用 11-23 复核结论）

1. `pvr_notifier.h` 的 `PVR_DUMPDEBUG_LOG` 宏改写仍在（宏体引用自由标识符，一旦被调用就编译失败；且两个 `#if` 分支内容相同）。
2. `module_common.c` 的 open 锁仍在，且是"每次 open 都加锁"（原 `INIT` 判断被删）。
3. `sysconfig.c` 的 `#if defined(MTK_USE_HW_APM)` 现在两支相同 → 建议直接删条件。

## 对"Linux 上跑图形"的关键影响（FACT/推断）

- 设备 userland 是 **Alpine（musl）**（`gpu-bringup/POST.en.md` 原文："Alpine userland"）。
- TI/IMG 的 1.13 Linux UM 是 **glibc**（`NEEDED libc.so.6 / libm.so.6 / libpthread.so.0`）→ **不能直接在 musl 上跑**。
  gcompat 理论上能兜一部分，但 Mesa 加载器 + `dlopen(pvr_dri.so)` + 大量 libc 细节，成功率低。
  → 现实做法：换/加一个 glibc rootfs（Debian/Ubuntu chroot 或直接换发行版）。
- 1.13 的 Linux 包只带 GLES/EGL/GBM，**没有 Vulkan**；主线 Mesa 的 PowerVR Vulkan 不支持 22.87.104.18（8XE）。
- `RDPowIsland=false` 与"固件不回写 sPowerSync"的因果关系是 **HYPOTHESIS**：它关掉的是 RD 电源岛下电路径，症状吻合，但没有 FW 侧证据。

## 建议的下一步

1. 先把当前工作区提交/推到 `dandelion-7.1`（现在公开仓库落后于实际状态）。
2. 设备上准备 glibc 环境（chroot 最省事），装 TI 1.13 UM，跑 `eglinfo -B` / `gles2test1`。
3. 清理 P1/P2/P3 三处收尾，避免下游复现者踩坑。
