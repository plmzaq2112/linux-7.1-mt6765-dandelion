# GPU-PORT.md — 主线 7.1 移植 PowerVR DDK 1.13（本项目进度）

## 收尾状态（2026-11-20 20:0x，本轮暂停点）

### 一句话
**MIPS 固件已经能在主线 7.1 上真正启动**（重大突破），但固件启动后**从未轮询 KCCB**（`r` 指针 110 秒不动、`fwirq=0`），
所以 `POW/forced-idle` 命令发不进去，`/dev/dri/renderD129` 仍无法打开。GPU 尚不可用。

### 已验证可用（FACT）
| 环节 | 状态 | 证据 |
|---|---|---|
| GPU 块/寄存器 | ✅ | `CORE_ID=0x08470000`、`REVISION=0x00680012` |
| MFG 电源域 | ✅ | `pvr_apm=0` 时 `PWR_STATUS` bit7=1 |
| MIPS 固件启动 | ✅ | `bFirmwareStarted` 置位；无 “FW started” 超时 |
| MIPS 运行状态 | ✅ | `EXC_STATUS=0x20`（与 MIUI 正常值一致） |
| FW 连接 | ✅ | `conn fw=2 (FW_ACTIVE)`、`pow=1` |
| GPU 时钟 | ✅ | `mfgpll/mfg_sel/mfg_ck = 390 MHz` |
| KCCB 命令消费 | ❌ | 快照显示 110s 内 `r` 始终为 0（固件不读） |
| FW 中断 | ❌ | `fwirq=0`（MIUI 正常时 2 万+） |
| POW/forced-idle 完成 | ❌ | `pow sync prim (fwaddr=0xC0019000)` 始终为 0 |

### 关键结论（务必先看）
1. **64K FW 页是错误方向**：`SUPPORT_MIPS_CONTIGUOUS_FW_MEMORY` 会让 MIPS 进异常（`EXC 0x22`），
   必须保持**关闭**（4K 页，和 vendor 一致）。
2. **`pvr_apm=0`** 必须传，否则平台层写入 MTK HW APM 寄存器会把 `MFG_CORE0` 自动掉电。
3. **bus=32 不是解法**：已恢复原表 36 位；32/36 都能启动固件，但都卡在 POW。
4. 普通 KCCB 通道可用，问题集中在 **FW 的电源状态机**（或回执写回不可见）。

### 当前源码开关
```c
// drivers/misc/pvr/ddk/include/config_kernel_user_mt6765.h
#define PVR_LINUX_PHYSMEM_SUPPRESS_DMA_AC      // vendor 风格（alloc_pages）
// #define PVR_LINUX_PHYSMEM_USE_HIGHMEM_ONLY  // 关闭
// #define SUPPORT_MIPS_CONTIGUOUS_FW_MEMORY   // 必须关闭（4K 页）
```

### POW 五环节快照（FACT，2026-11-20 20:1x，一次完整观测）
在 `RGXForcedIdleRequest` 加纯快照后，一次 POW 请求的完整记录：
```
POW[before]  sync=0 fwaddr=c0019000 cpuva=ffff80008486c000 kccb=0/0 pow=1 hwr=00000001 fwirq=0 faults=0
POW[sent]    ... kccb=1/0 slot=0 ...
POW[poll]    sync=0 kccb=1/0 pow=1 hwr=00000001 fwirq=0 faults=0      ×11（每 10s）
POW[timeout] sync=0 kccb=1/0 pow=1 hwr=00000001 fwirq=0 faults=0
POW[*] cmd=2abc006b powtype=2 req=1 raw=00000001
```
| 环节 | 观测 | 结论 |
|---|---|---|
| ① SyncPrim 清零 | `sync=0` | 主机已做 |
| ② 写 KCCB | `w=1`，命令 `0x2abc006b`/powtype=2/req=1 | 入队正确 |
| ③ FW 消费 | `r=0` 110 秒不动 | **FW 没读** |
| ④ FW 状态/回执 | `pow=1` 不变、`sync=0` | 未发生 |
| ⑤ 关硬件 | — | 未到达 |

补充：`hwr=1`（HWR OK）、`faults=0` → 不是硬件错误/固件崩溃；`fwirq=0` → 固件主循环没跑。
下一步只查：**FW 看到的 KCCB 控制结构地址/参数是否正确**（OSINIT 的 `psKernelCCBCtl` / `psKernelCCB` / `ui32CmdSize` / `ui32WrapMask`）。

### OSINIT / 连接状态（FACT，2026-11-20 20:3x）```
skip-fidle conn fw=2(FW_ACTIVE) os=1(READY) fwtok=0 ostok=0 mts=0 kccb=0/0 pow=1
OSINIT kccbctl=c0018880  kccb=c001a000  cmdsize=72  wrapmask=127
prim   fwaddr=c0019000
```
- KCCB 控制结构/缓冲/prim 都在 FW heap 同一区间，**地址与参数形态正常**（72 B/命令、128 槽）。
- **OS 侧连接状态停在 `READY(1)`，不是 `ACTIVE(2)`**。

### 当前主假设：连接握手死锁（HYPOTHESIS）
> 固件可能要求 OS 置 `ACTIVE` 才进入主循环轮询 KCCB；
> 而主机在 `pvrsrv.c:3056`（`PVRSRVDeviceFinalise` 之后）才置 `ACTIVE`；
> 但 `Finalise` 内部先做 POW forced-idle 并等待固件回执 → 双方互等。

可同时解释：`r=0`（固件没读）、`fwirq=0`（不产生中断）、`sync=0`、`pow=1`。
验证方式（已加参数）：`insmod pvrsrvkm.ko pvr_apm=0 pvr_os_active=1`，在发 POW 前把 OS 状态置 ACTIVE。
- 若固件立刻开始消费/回执 → 假设成立，正式修法是调整初始化顺序（先置 ACTIVE 或让 Finalise 跳过 POW）。
- 若仍 `r=0` → 排除该假设，回到“FW 取指/映射”方向。

### 决定性观测：固件完成了，但主机看不见（FACT，2026-11-20 20:5x）「coherent 内存 + `pvr_os_active=1`」下：
```
kccb=1/0  pow=2(FORCED_IDLE)  fwirq=1  sync=0
```
- `pow=2`：固件**完成了**电源状态切换（从 SYSDATA 读到）；
- `fwirq=1`：固件发了中断；
- 但 **KCCB 读指针与 pow sync prim 主机仍看不到**。

对比结论：**固件侧没问题，丢在共享内存可见性**；且这两块缓冲区与 SYSDATA 的分配/cache 属性不同
（KCCB 分配带 `PVRSRV_MEMALLOCFLAG_DEVICE_FLAG(FIRMWARE_CACHED)`，见 `rgxfwutils.c` 的 `RGXSetupCCB`）。

下一步实验（未做）：
1. 去掉 KCCB 分配的 `FIRMWARE_CACHED` 标志，让固件以 uncached 访问；
2. 或在主机读之前对 sync prim 页做 cache invalidate，验证“值已写、主机读到旧 cache”。

### OSINIT 完整地址（FACT，2026-11-20 21:2x）+ 上游对照

```
conn    fw=2(FW_ACTIVE) os=1(READY) fwirq=0
OSINIT  osdata=c0018b00 rtn=c00188c0 fwccbctl=c0018ac0 fwccb=c001d000
        kccbctl=c0018880 kccb=c001a000 cmdsize=72 wrapmask=127
prim    fwaddr=c0019000
```
- 所有共享结构都在 `0xC0018xxx–0xC001Dxxx`，指针非 0、布局正常；
- OSDATA 指针正确 → 固件能读到 `sPowerSync=0xC0019000`；
- **主机侧的地址/参数/指针全部正确**。

**与上游 Linux 驱动对照（web）**：
- `pvr_ccb.c`：CCB ctl / CCB / power_sync 全部 `PVR_BO_FW_FLAGS_DEVICE_UNCACHED`；
- 发送顺序：`memcpy` → `mb()` → 更新 write_offset → `pvr_fw_mts_schedule()`；
- `pvr_fw_mts_schedule()`：`wmb()` → 写 `ROGUE_CR_MTS_SCHEDULE(DM_GP)` → `mb()`。
- 我们的 DDK `__MTSScheduleWrite()` 有同样的两道屏障，**软件写法一致**。
- DeepWiki：固件主循环用 `_mips_wait()`，**靠中断唤醒**。

**因此剩下两个 GPU 侧可能**：
1. GPU MMU 页表把 `0xC0019000` 映射到与主机 vmap 不同的物理页；
2. 该页在 GPU 侧是 cached（固件写入未落到内存）。

验证方法（未做）：读 GPU MMU PTE（DDK MMU 代码），把 `0xC0019000` 翻译出的 PA 与主机页对比。

### 绕过 prim 的尝试（FACT，2026-11-20 21:4x）
加入 `pvr_no_sync=1`（GP 轮询超时当成功、跳过 forced-idle 的 `ePowState` 检查）后：

```
OS state forced to ACTIVE
forced-idle enter: pow=1 kccb w=0 r=0
no-sync: GP poll timeout treated as complete
no-sync: GP poll timeout treated as complete
RGXPrePowerState: Failure to power off during a forced power off. FW: 2
PVRSRVDeviceFinalise: ... default power state (PVRSRV_ERROR_DEVICE_POWER_CHANGE_DENIED)
```
- 设备默认电源状态是 **OFF**，finalise 要把设备关掉；
- 但固件停在 **FORCED_IDLE(2)**，不肯进 OFF(0) → 被拒绝。
- 说明 **prim 那一步握手是 FW 状态机的一部分**，单纯跳过会让 FW 卡在 FORCED_IDLE。

**结论：绕过不可行，必须修 prim 页的可见性。**

另外观察到：**固件启动是间歇性的**（同样的镜像/参数，有时 `bFirmwareStarted` 超时），这本身也指向内存/缓存可见性问题。

### GPU MMU 审计 + 返回槽 + 关 APM（FACT，2026-11-20 22:3x-22:5x）

**页表（PT base pa=0x42c10000，VA 基址 0xC0000000）**：
```
PTE[018] c0018000 → pa=0x42c7d000  v=1  cache=2 UNCACHED      (KCCB ctl)
PTE[019] c0019000 → pa=0x42c7c000  v=1  cache=2 UNCACHED      (pow prim)
PTE[01a] c001a000 → pa=0x42c7b000  v=1  cache=1 WRITETHROUGH  (KCCB buf)
HOST prim pa=0x42c7c000  ctl pa=0x42c7d880   ← 与 PTE 完全一致
```
→ **PTE 有效、属性与 ctl 相同、主机与固件物理页一致**，映射假设全部排除。

**返回槽**：
```
POW[poll] sync=0 rtn=00000000 kccb=1/0 pow=3 fwirq=1
```
→ 固件连 KCCB 返回槽都不写；该轮 `r=0`，命令**根本没被消费**（`pow=3` = FW 自己进了 IDLE）。

**关 APM（`pvr_no_apm=1`，清 `RGXFWIF_INICFG_POW_RASCALDUST`）**：
`syscfg=0x00020030 → 0x00020020` 生效；但固件随后直接处于 FORCED_IDLE，
forced-idle 步骤被跳过，下一步 POW_OFF 仍然卡在 prim 超时。

**结论**：主机侧（地址、映射、缓存属性、屏障、协议）已全部证明正确；
固件对 POW 命令要么不处理，要么处理但**不给任何主机可见的回执**（`r`/`rtn`/`prim` 全为 0）。
问题已确定在 **固件/硬件交互层**，不再是移植层。

### 复现（设备侧，无需刷机）
```sh
# 模块/固件已放在 p40 的 /root 与 /lib/firmware
insmod /root/pvr-4k.ko pvr_apm=0          # 正常路径（会卡 110s 后超时）
# 或只取诊断（快速失败）：
insmod /root/pvr-prim.ko pvr_apm=0 pvr_skip_fidle=1
dd if=/dev/dri/renderD129 of=/dev/null bs=1 count=1
dmesg | grep pvr-mtk
```
模块参数：
- `pvr_apm=0|1`：是否写 MTK HW APM 寄存器（默认 0）
- `pvr_skip_fidle=1`：跳过 forced-idle，只打印连接/prim 状态（诊断用）

### 本轮改动（未提交，可 `git checkout` 回滚）
| 文件 | 改动 |
|---|---|
| `drivers/misc/pvr/ddk/include/config_kernel_user_mt6765.h` | 关闭 `SUPPORT_MIPS_CONTIGUOUS_FW_MEMORY`；打开 `PVR_LINUX_PHYSMEM_SUPPRESS_DMA_AC` |
| `.../rgx_mtk/pvr_platform_mt6765.c` | 新增 `pvr_apm` 参数；`pvr_mtk_init_apm()` 受其控制；新增 `mtk_pvr_dump_spm()` |
| `.../rogue/rgxpower.c` | FW 启动前后 SPM 采样；forced-idle 的 KCCB/连接/prim 打印；`pvr_skip_fidle` 参数 |
| `.../hwdefs/rogue/km/rgx_bvnc_table_km.h` | 恢复 36 位并修正注释 |
| `GPU-PORT.md` | 本轮全部结论 |

### 下一步（恢复时从这里继续）
1. 查 FW 侧 HWR/错误状态（`RGXFWIF_OS_STATE` / HWR info buffer），确认 POW 命令是被拒绝还是写入不可见；
2. 尝试绕过 POW 的初始化路径（让设备在无电源管理状态下 open），验证渲染链路是否可用；
3. 若都不行，需要 vendor 4.19 运行时对照（仅取证，不长期使用）。



> 目标：把厂商 DDK `m1.13ED5776728`（rgx, GE8320 22.87.104.18）移植进
> `03-mainline-7.1`，先求编译通过（S1），再求 `/proc/pvr/status` 变 OK（S2）。

## 参考材料（只读）

| 材料 | 位置 |
|---|---|
| 厂商 DDK 源码 | `~/dandelion-linux-kernel/01-pure-baseline/drivers/gpu/mediatek/gpu_rgx/m1.13ED5776728` |
| m3 的移植记录 | `mt6765-mainline-m3/docs/porting/GPU-PORT.md`（S0–S2、r97–r104、CG 极性、FOP_UNSIGNED_OFFSET） |
| alpican（同平台 4.19 + Alpine） | `~/alpican-gpu/`（tarball 解包），GPU 在厂商 4.19 上可用 |
| 固件 | `~/alpican-gpu/ramdisk/lib/firmware/rgx.fw`（114688 B）、`rgx.sh` |
| 用户态配方 | gist `bd991ef60538bf37115d0f6befb615ae`（`~/alpican-gist/`），32 位 Bionic chroot |

## 已完成（S1 进行中）
1. DDK 复制到 `drivers/misc/pvr/ddk/`
2. `drivers/misc/pvr/{Kconfig,Makefile}`，`drivers/misc/{Kconfig,Makefile}` 已挂接
3. `CONFIG_DRM_PVR_LEGACY=m`
4. `ddk/Makefile`：`MTK_PLATFORM := mt6765`、去掉 4.19 mt-plat 的 -I 块、obj 改为 `CONFIG_DRM_PVR_LEGACY`
5. 垫片头 `ddk/include/kernel_libc_compat/`（stdarg/stddef/stdbool/stdint/string/stdio/stdlib）

## 当前错误（下一步）
- `services/system/rogue/rgx_mtk/mt6765/mtk_mfgsys.h: ged_dvfs.h` 缺失
  → 建 `mtk_plat_stub/`（ged_dvfs/ged_log/ged_base/mtk_gpufreq/mtk_gpu_utility/mtk_boot + mach/mt_irq/irqs/mtk_hibernate_dpm）
  → 最终用新写的 `pvr_platform_mt6765.c` 替换 `mtk_mfgsys.o`
- `dma_support.c: vm_map_ram` 3 vs 4 参数
- 预期还有（m3 清单）：`access_ok` 签名、`init_timer/setup_timer`、`proc_ops`、`class_create`、`timespec`、`mmap_sem`、`set_memory_*`、shrinker、`dma_buf_vmap`（iosys_map）、tracepoint `__assign_str`、`platform_driver.remove` 返回 void

## S2 关键点（m3 已踩过）
- DT：`mfgcfg: syscon@13ffe000`、`gpu@13000000`（`mediatek,doma`，reg 0x80000，SPI 259，clocks mfg/mfgpll，power-domains MFG_ASYNC/MFG/MFG_CORE0，status okay）
- CG 极性：`0x13FFE004 = SET(关)`、`0x13FFE008 = CLR(开)`，写 0xF 到 **0x008** 才是开时钟
- 读 `CORE_ID(0x18)` 验证：`0x08470000`，BVNC 22.87.104.18
- DRM fops 需要 `FOP_UNSIGNED_OFFSET`
- 固件加载：`rgx.fw` 在 `/lib/firmware`（首次 open renderD128 时、按进程根目录找）；`FW_LOADER_USER_HELPER_FALLBACK` 已关（我们已满足）
- m3 r104 卡点：`PVRSRVDeviceOpen` 失败、IRQ 计数 0 → 固件未启动；r104 加了 PVR_DPF 真打印，未刷

## 构建命令
```bash
cd "$HOME/AI Project/Redmi 9A/kernel 7.1 mainline"
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- O=out -j8 drivers/misc/pvr/ddk/pvrsrvkm.ko
```

## S1 完成（2026-11-19 22:06）

```
out/drivers/misc/pvr/ddk/pvrsrvkm.ko   20 714 952 B   0 error
```

### 实际改动清单
| # | 文件/位置 | 改动 |
|---|---|---|
| 1 | `drivers/misc/pvr/{Kconfig,Makefile}` | 新建，`config DRM_PVR_LEGACY` |
| 2 | `drivers/misc/{Kconfig,Makefile}` | 挂接 `pvr/` |
| 3 | `ddk/Makefile` | `MTK_PLATFORM := mt6765`、去掉 4.19 mt-plat -I 块、obj 改 `CONFIG_DRM_PVR_LEGACY` |
| 4 | `ddk/include/kernel_libc_compat/` | 7 个 libc 垫片（stdarg/stddef/stdbool/stdint/string/stdio/stdlib） |
| 5 | `ddk/include/mtk_plat_stub/` | ged_dvfs(含 GED_DVFS_COMMIT_TYPE)/ged_log/ged_base/mtk_gpufreq/mtk_boot/mtk_gpu_utility/mach/* |
| 6 | `ddk/include/mtk_plat_stub/linux/pfn_t.h` | pfn_t 已从内核移除，用 `unsigned long` + pfn_to_pfn_t 等宏补 |
| 7 | `ddk/include/pvr_compat_prologue.h` | 强制包含：`strlcpy→strscpy`、`dma_buf_vmap/vunmap`(iosys_map)、`register_shrinker` 空实现 |
| 8 | `config_kernel_user_mt6765.h` | 关闭 `SUPPORT_ION` |
| 9 | `dma_support.c`、`physmem_osmem_linux.c` | `vm_map_ram` 去掉 prot 参数（4 处） |
| 10 | 5 个 .c | `vm_flags |=` → `vm_flags_set()`、`mmap_sem` → `mmap_read/write_lock`、`from_timer`→`timer_container_of`、`del_timer_sync`→`timer_delete_sync` |
| 11 | trace 头（2 个） | `__assign_str(a,b)` → `__assign_str(a)` |
| 12 | `pvr_fence.c`/`pvr_sw_fence.c` | 去掉 6.11 删除的 `.fence_value_str/.timeline_value_str` |
| 13 | `pvr_sync_file.c`、`pvr_counting_timeline.c` | 去掉对上述回调的**调用** |
| 14 | `osfunc_arm64.c` | `uaccess_enable/disable` → `uaccess_{enable,disable}_privileged` |
| 15 | `pvr_platform_drv.c` | `remove` 返回 void（6.11） |
| 16 | `pvr_drm.c` | 删 `.dev_priv_size`/`.date`、去 `DRM_UNLOCKED`、加 `MODULE_IMPORT_NS("DMA_BUF")` |
| 17 | `pvr_platform_mt6765.c`（新） | 平台层：`MTKRGXDeviceInit/DeInit`、`MTKDevPre/PostPowerState`、`MTKMFGSystemInit/DeInit`、`mtk_mfg_async/2d_init`、`MTKGetIonClient`、GPU mem 回调 |
| 18 | `ddk/Makefile` | 用 `pvr_platform_mt6765.o` 替换 `mtk_mfgsys.o`，删 `ion_support.o`、`pvr_ion_stats.o` |

### 下一步 S2
1. DT：`mfgcfg` syscon + `gpu@13000000`（`mediatek,doma`，reg 0x80000，SPI 259，clocks mfg/mfgpll，power-domains MFG_ASYNC/MFG/MFG_CORE0）
2. 平台层填实：clk 开/关 + CG 极性（**0x13FFE008 写 0xF = 开**）+ CORE_ID 自检
3. `CONFIG_DRM_PVR_LEGACY=y` 内置、固件 `rgx.fw` 打包进 initramfs
4. 上机看 `/proc/pvr/status` 与 dmesg

## S2 上机（2026-11-19 22:5x）

### 结果（FACT）
```
pvr-mtk: irq (platform_get_irq) = 204
pvr-mtk: reg_res = 0x13000000, 0x80000
pvr-mtk: mfg clk rate=390000000
pvr-mtk: MFG_CFG 0x0=00000070 0x4=00000000 0x8=00000000
pvr-mtk: RGX CORE_ID=08470000 CORE_REVISION=00680012     ← GPU 块活着
[drm] Initialized pvr 1.13.5776728 for 13000000.mfg_doma on minor 2
```
- `/dev/dri/card2` + `renderD129` 出现
- `head -c 0 renderD129` 进入 `pvr_drm_open`（FOP_UNSIGNED_OFFSET 已补）→ `-ENODEV`

### 固件阶段（FACT，已打开 DDK 真日志）
```
Direct firmware load for rgx.fw.22.87.104.18 failed (-2)   ← 版本名回落，正常
...
PVR_K:(2) PollForValueKM: Timeout. Expected 0x1 but found 0x0
PVR_K:(2) RGXPostPowerState: Polling for 'FW started' flag failed
PVR_K:(2) PVRSRVDeviceOpen: Failed to initialise device (PVRSRV_ERROR_TIMEOUT)
```
→ **固件已加载，但 GPU 未置起 FW started 标志**

### 关键改动（本轮）
1. `sysconfig.c`：IRQ 用 `platform_get_irq()` 兜底 + pr_info（资源都拿到了）
2. `pvr_drm.c`：`.fop_flags = FOP_UNSIGNED_OFFSET`（7.1 drm_open_helper 硬检查）
3. `pvr_debug.c`：把空桩换成真 printk（`PVR_K:(level) file:line msg`）
4. `pvr_platform_mt6765.c`：真实平台层（pm_runtime + clk + mfgcfg CG + CORE_ID 校验）

### 已知副作用
- **不要 `rmmod pvrsrvkm`**：IRQ action 未清理，之后读 `/proc/interrupts` 会 oops 并打死 dropbear

### 下一步（FW started 超时排查）
1. 确认固件真的加载成功（在 DDK 的 request_firmware 路径加打印，或看 `firmware_class` 的 debug）
2. 对照厂商 4.19 的 `RGXPostPowerState`：初始化序列里除 CG 外还需要哪些（MFG 电源域、SLC/内存时钟、SMMU/IOMMU 映射）
3. 检查 DDK 的物理堆（`physmem_osmem`）在我们改过的 dma-buf/iosys_map 垫片下是否给出正确的 GPU 可见地址
4. 与 alpican（4.19 可用）对比：他们的 `CONFIG_MTK_GPU_COMMON_DVFS_SUPPORT` 与 gpufreq 可能影响上电时序

## S2 关键转折（2026-11-20 00:2x）：GE8320 是 MIPS，不是 META

### 铁证（FACT，驱动内打印）
```
pvr-mtk: BVNC=22.87.104.18  META_val=-1  META_sup=0  MIPS_sup=1  RISCV_sup=0
```
DDK 的 feature 表 `rgx_bvnc_table_km.h:296`（vendor 同版本一字不差）：
```
/* 22.0.104.18 */
{ 0x0016000000680012, 0x00000045844e600b, 0x0008d28253100100 }
```
`0x45844e600b` 的 bit17 = `RGX_FEATURE_MIPS` = **1**。
`_RGXBvncParseFeatureValues()` 见 MIPS 就强制把 META 置 DISABLED。

### 结论：之前所有 META 方向的调试都是错的
| 现象 | META 假设下的解释 | 真实原因 |
|---|---|---|
| `MSLVCTRL1 = 0` | META 没唤醒 | **MIPS 核根本没有这个 SP** |
| `META_BOOT` 写 1 无效 | META 没电/没时钟 | 对 MIPS 无意义 |
| `boot stage = 0` | 固件没跑 | META 专用寄存器，MIPS 不用 |
| `RGXSetPowerParams` 走 else 分支 | feature 解析错 | **正确行为，MIPS 分支** |

### 当前真实卡点
- 固件加载正常：`FwExCodeRegion 98304B` + `FwExDataRegion 16384B`
- MIPS master boot 后 `bFirmwareStarted` 仍为 0 → `PVRSRV_ERROR_TIMEOUT`
- 与 vendor 4.19 的差异：vendor `SUPPORT_ION`（ION 分配物理连续内存），
  我们禁用后 FW 走 `osmem`（`alloc_pages` 4K 分散页）
- `physmem_osmem_linux.c: bIsCMA = uiLog2AllocPageSize > PAGE_SHIFT`
  → 定义 `SUPPORT_MIPS_CONTIGUOUS_FW_MEMORY` 可让 MIPS FW 走 64K 对齐→CMA
  （已加，**尚未验证是否真的变成 64K/CMA**，因为打印插在调整之前）

### 无重启调试工具（新增）
- `tests/tools/gpurw.c`：/dev/mem 读 GPU 寄存器（0x13000000 页可用，0xE000 页被 iomem 独占）
- `tests/tools/gpu_diag.c`：独立 .ko，ioremap 0x13000000/0x80000，可读 BIF/MMU/Garten

### 寄存器实测（FACT）
```
0x13000018 CORE_ID        = 0x08470000
0x13000020 CORE_REVISION  = 0x00680012   (N=104, C=18)
0x13000024                = 0x00160057   (B=22, V=87)  ← 64 位读 0x20 会丢这半！
0x13ffe000 MFG_CFG        = 0x70
0x1000634c MFG_CORE0_PWR  = 0x1e0d  (PWR_ON=1, RST_B=1, CLK_DIS=0)
0x10000050 CLK_CFG_1      = 0x01010201 (mfg_sel=mfgpll_ck)
```
注意：GPU 寄存器**不支持 64 位单指令访问**，gpurw 用 `ldr x` 读 0x20 会得到高半 0；
DDK 的 `OSReadHWReg64` 是两次 readl，所以 DDK 读 BVNC 是**正确**的。

### 下一步（MIPS 方向）
1. 确认 FW 分配真的变成 64K/CMA（把打印移到 `#if` 之后，或读 /proc/meminfo CmaFree 变化）
2. 读 `RGX_CR_MIPS_WRAPPER_CONFIG` 与 MIPS 状态，确认 MIPS 的 PC/启动地址
3. 对照 vendor 4.19 的 `RGXInitMipsProcWrapper` 所需页表（`RGXPDumpBootldrData`）
4. 若 CMA 不生效，直接在 `PhysmemNewOSRamBackedPMR` 对 FW heap 强制 `dma_alloc_coherent`

## MIPS 固件启动：最后一步（2026-11-20 15:3x）

### 已全部解决（FACT）
| 项 | 证据 |
|---|---|
| 固件在低 4GB | `cma alloc ... dma=0x7cd10000` |
| FW code 映射 | `MIPS boot_remap_pa=0x7cd27000` |
| 固件内容正确 | memremap 读出 MIPS 指令 `02fc039f 18000000` |
| ELF 匹配 | `rgx.fw` = ELF, e_machine=8(MIPS), e_entry=0xBFC00100 |
| wrapper | `0x810 = 0x0001cf80` (0xCF800000>>16 + microMIPS) |
| boot remap | `0x818=0x1fc00001`, `0x820=0x7cd2700c` |
| data/code remap | `0x828=0x1fc01001`, `0x838=0x1fc02001` |
| DDK 与 vendor | 完全一致（只差调试打印和 vm_map_ram 适配）|

### 关键修复（本轮）
1. DT 加 `linux,cma`：32MB @ 0x40000000-0x80000000（原先 size 少一个 cell → 失效）
2. 删除宏 `PVR_LINUX_PHYSMEM_SUPPRESS_DMA_AC`（它让 osmem 跳过 dma_alloc_coherent）
3. 删除宏 `PVR_LINUX_PHYSMEM_USE_HIGHMEM_ONLY`（强制 HIGHMEM）
4. `DevmemFwAllocateExportable`：页大小一律用 `ExactLog2(uiAlign)`（64K→CMA）

### 仍未解决
- MIPS 核不执行：`bFirmwareStarted` 始终 0
- 不是地址/内容/映射问题

### 下一步候选
1. **VCORE 电压**：vendor `mt_gpufreq_voltage_enable_set(BUCK_ON)` 会把 VCORE 抬到 OPP 电压；我们只有 800mV（CPU 的 OPP）
2. **MTCMOS 序列**：vendor 用 clk-mt6765-pg 的完整上电序列（PWR_ON→2ND→等 ACK→CLK_DIS→ISO→RST_B→SRAM_PDN），主线 scpsys 可能精简
3. **对比 4.19 运行时**：刷 vendor 4.19 内核，读同一组寄存器（wrapper/remap/SOFT_RESET/MIPS 状态）
4. **MIPS 调试接口**：读 MIPS PC（若有 debug 寄存器）

## 突破：固件真的起来了（2026-11-20 18:5x）

### 两个根因（FACT，实机 A/B）
1. **HW APM 把 MFG_CORE0 自动掉电**
   - 平台层抄 vendor 的 `MTKInitHWAPM()` 写 `0x13FFE024` 序列 → SPM `PWR_STATUS` 的 CORE0(bit7)=0，
     而 genpd 认为 on；手动置 `PWR_ON|PWR_ON_2ND` 200ms 也不 ACK。
   - 加模块参数 `pvr_apm=0`（不写 APM 寄存器）后：`st=068fdffd`，CORE0=1。
2. **64K FW 页导致 MIPS 异常**
   - `SUPPORT_MIPS_CONTIGUOUS_FW_MEMORY` 把 MIPS FW 区域的 `uiLog2Align` 设成 64K → CMA；
     实测 MIPS 进异常：`EXC_STATUS=0x22 (SLEEP|EXL)`，`bFirmwareStarted=0`。
   - 关掉该宏（回到 `OSGetPageShift()`=4K，vendor 行为）：**FW 启动成功**。

### 成功证据（FACT，4K + bus36 + pvr_apm=0）
```
boot_remap_pa=0x42c65000   (4K 页，非 64K 对齐)
[无 'FW started' 超时] → 直接进入 PVRSRVDeviceFinalise
/proc/interrupts: 205 ... pvrsrvkm  计数=1
gpu_diag4: EXC_STATUS=0x20    ← 与 MIUI 正常时一致（仅 SLEEP，无 EXL）
gpu_diag4: IRQ_EN=0x1 REMAP1=0x1FC00001/0x42c6500c WRAPPER=0x1cf80
```
→ **MIPS 固件活着且 idle**，不是崩溃。

### 当前卡点（FACT）
`PVRSRVDeviceFinalise` → `RGXForcedIdleRequest` → `RGXPollForGPCommandCompletion` 每次 10s 超时：
```
PVR_K:(2) :4493 RGXPollForGPCommandCompletion: Failed! Error(PVRSRV_ERROR_TIMEOUT)
PVR_K:(2) :1160 RGXForcedIdleRequest: Idle request failed
```
即 host→FW 的 GP 命令没有被消费/回执。下一步查 FW 连接状态与 kernel CCB 读写指针。

### 复现命令（设备已具备）
```
insmod /root/pvr-4k.ko pvr_apm=0
dd if=/dev/dri/renderD129 of=/dev/null bs=1 count=1
```

### 进一步定位（FACT，2026-11-20 19:0x）
在 `RGXForcedIdleRequest` 里加了 KCCB 读写指针打印：
```
pvr-mtk: forced-idle enter: pow=1 kccb w=0 r=0
pvr-mtk: forced-idle sent : kccb w=1 r=0 slot=0      ← 主机写入 1 条命令
pvr-mtk: forced-idle timeout: kccb w=1 r=0           ← 110s 后 FW 从未消费
```
即 **FW 活着、pow=1，但从不读 KCCB**。两种可能：
1. kick（`RGX_CR_MTS_SCHEDULE` 写）没真正唤醒 GP 数据主控；
2. KCCB 控制结构对 FW 不可见（GPU MMU 映射问题），FW 看到的是“没有命令”。

下一步：读 MTS 状态/中断寄存器确认 kick 是否生效；对比 vendor 的 `PVR_LINUX_PHYSMEM_*` 配置（vendor 用 alloc_pages + ION，我们用 dma_alloc_coherent）。

### KCCB / 连接状态实测（FACT，2026-11-20 19:2x-19:4x）
```
skip-fidle conn fw=2 os=1 fwtok=00000000 ostok=00000000 mts=00000000 kccb w=0 r=0 pow=1
```
- `fw=2` = `RGXFW_CONNECTION_FW_ACTIVE`（连接已建立），`pow=1` = ON。
- 队列命令后（pvr-kick 版）：
```
after-send kccb w=1 r=0
after-kick kccb w=1 r=0      ← 手动补写 RGX_CR_MTS_SCHEDULE(0xB00)=DM_GP，20ms 内无变化
forced-idle timeout kccb w=1 r=0   （APM=1 时 110s 都不消费）
```
- 另一轮（APM=0）同一位置在 timeout 时 `r=1`，即**偶尔/很晚才消费**，但完成信号（pow sync prim）始终不见。
- 时钟正常：`clk_summary` 显示 `mfgpll/mfgpll_ck/mfg_sel/mfg_ck = 390 MHz`。
- **A/B 结论**：APM 开关不影响 FW 启动（真正决定启动的是 FW 页大小：4K 可以，64K 不行）。

剩余怀疑：
1. FW 侧看到的 KCCB 控制结构与主机不一致（`RGXFWIF_RUNTIME_CFG` 里的 FW 地址 vs 主机地址）；
2. 共享内存一致性（FW 写、主机看不到 → 完成信号丢失）；
3. DDK 的 KCCB 处理路径与 MTK 的 IRQ/门铃机制不匹配。

下一步优先做 (1)：打印 `psRGXFWIfRuntimeCfg->sKCCB.psKernelCCBCtl` 与主机 `psKernelCCBCtlMemDesc` 的 FW 地址对比。

### 一致性 A/B（FACT，2026-11-20 20:3x-20:4x）
- 改回 vendor 风格内存（`#define PVR_LINUX_PHYSMEM_SUPPRESS_DMA_AC`，alloc_pages + DDK cache 维护）后重测：
```
forced-idle timeout: kccb w=1 r=1   ← 命令被消费
PVR_K: RGXPollForGPCommandCompletion: TIMEOUT (×11)
PVR_K: RGXForcedIdleRequest: Idle request failed
```
- 结论：**KCCB 本身能被 FW 消费（r 前进），但 POW(forced-idle) 的完成信号（pow sync prim→1）永远不出现**。
- 说明不是“FW 完全看不到命令”，而是 **FW 无法完成 forced-idle 这次状态切换**（或回执写入不可见）。

剩余方向：
1. 先确认 health-check 那条 GP 命令是否成功（若成功则通道 OK，问题只在 POW）；
2. 读 FW 侧错误/HWR 状态（`RGXFWIF_OS_STATE`、HWR info buffer）；
3. 对照 vendor 4.19 运行时（需要刷 MIUI boot 取证）。

### sync prim 地址核查（FACT，2026-11-20 19:4x）```
skip-fidle conn fw=2 os=1 fwtok=00000000 ostok=00000000 mts=00000000 kccb w=0 r=0 pow=1
prim fwaddr=c0019000 cpuva=ffff80008486c000
```
- POW 完成用的 sync prim：FW 地址 `0xC0019000`（在 FW heap 的 kseg0 区间，形态正常），主机 VA 有效。
- 所以 **不是地址明显错误**；更像是 FW 收到 POW 命令后无法完成这次状态切换（或写回不可见）。
- 结论：GPU 驱动已推进到 **电源状态机（POW）** 这一层，普通 KCCB 通道可用。

## MIUI 对照记录复查 + 活体调试（2026-11-20 18:0x）

### 记录位置（FACT）
- rtifacts/miui-gpu/debug_dump.txt / debug_dump_utf8.txt：MIUI（4.19 + vendor DDK 1.13@5776728、FW 正常）完整 PVR debug dump。
- PROJECT-HANDOVER.md §3.4/§8 有对照摘要：MIUI PHYS_BUS_WIDTH=32，我们是 36；已改 
gx_bvnc_table_km.h 的 22.0.104.18 条目（0x…82… → 0x…83…），但当时设备 bootloop，**从未在设备上验证**。

### MIUI 基准寄存器（FACT，debug_dump_utf8.txt:122-158）
`
MIPS_WRAPPER_CONFIG      = 0x000000000001cf80
REMAP1 1FC00001 / 0x1220d100c
REMAP2 1FC01001 / 0x12221730c
REMAP3 1FC02001 / 0x1220d000c
REMAP4 1FC00000 / 0xc
REMAP5 00000001 / 0x1220d100c
MIPS_EXCEPTION_STATUS = 0x20 (仅 SI_SLEEP)
MIPS PC=0xC00153EC STATUS=0x00481C05 SP=0xCF600FE0
TLB: 0xCF800000(64k)->0x13000000 ; 0xCF000000(16k)->0x1243d0000 ; 0xCF600000(4k)->0x122174000
`

### 活体调试通道打通（FACT）
- r23 + Alpine 上可直接 insmod（CONFIG_MODULES=y、无 MODULE_SIG、vermagic 匹配）：pvrsrvkm.ko（strip 后 1.69 MB，gzip 423 KB）经 USB-NCM 
c 传入（把 usb0 改成 169.254.195.201/16 与 PC 的 NCM 网卡同网段），无需刷机。
- 首次加载（缺 
gx.sh）失败在 TQ shader 阶段；补 /lib/firmware/rgx.sh 后重启重载，流程推进到 RGXPostPowerState → **FW started 超时**。

### 实机结果（FACT）
`
pvr-mtk: BVNC=22.87.104.18 META_sup=0 MIPS_sup=1
pvr-mtk: FW code DevVAddr=e1c0000000, cma dma=0x7cd10000
pvr-mtk: boot stage=0 meta_boot=0 soft_reset=0
pvr-mtk: FW[0] cpu=ed7fae02 gpu=deadbeef rc=9
PVR_K: PollForValueKM: Timeout. Expected 0x5000000 but found 0x0
PVR_K: RGXPostPowerState: Polling for 'FW started' flag failed
pvr-mtk: mslvctrl1=0 mslvirqstatus=0 bif_cat0=0 mmu_fault=0
`
自写 gpu_diag2.ko 读到的状态：
`
PWR_STATUS=0x068fdf7d  MFG=1  CORE0=0  ASYNC=1
MFG_ASYNC_PWR_CON=0x0f0d MFG_PWR_CON=0x0e0d MFG_CORE0_PWR_CON=0x1e0d
TOPAXI_PROTECTEN=0x98 (MFG bit25/21 = 0，总线保护已释放)
REMAP1..5 与 MIUI 一致（地址换成我们的 0x7cd27xxx）
MIPS_EXCEPTION_STATUS=0x2a (SI_SLEEP|SI_EXL|SI_NEST_EXL)  ← MIUI 只有 0x20
`
gpu_diag3.ko 手动再置 PWR_ON|PWR_ON_2ND：**200 ms 内 MFG_CORE0 仍不 ACK**（状态位 bit7 始终 0）。

### 结论（当前）
- bus=32 **不是**唯一原因：补上 
gx.sh 后仍 FW 超时。
- 地址/remap/wrapper 与 MIUI 完全一致，问题不在映射。
- MIPS 侧 EXC_STATUS 带 EXL/NEST_EXL，说明核心执行过并进入异常；而 MFG_CORE0 的 SPM 状态在失败后为 0（可能为失败后掉电状态，需在 FW 启动瞬间采样确认）。
- 剩下两个高优先级假设：①MFG_CORE0 MTCMOS 实际未上电（需在 open 过程中采样/补 vendor MTCMOS 细节）；②MIPS 异常（需读 CP0/异常地址）。

### 下一步
1. 在 MTKDevPrePowerState 与 RGXPostPowerState 轮询前后打印 PWR_STATUS/MFG_CORE0_PWR_CON（采样窗口对齐 FW 启动瞬间）。
2. 若确认 CORE0 掉电：对照 vendor clk-mt6765-pg.c 的 MTCMOS 细节（SRAM PDN 顺序/额外时钟），或在平台层直接走 vendor 序列。
3. 若 CORE0 正常：读 MIPS CP0（PC/EPC/Cause）定位异常类型。

---

## 2026-11-20 深夜：ABI 校验 + 固件实际执行证据（本轮新增）

### 1) ABI 校验通过（FACT）

`pvr_fwtrace=1` 时打印（实机，r23 内核 + Alpine）：

```
pvr-mtk: ABI cmd=72 data=8 powreq=8 powoff=4 ccbctl=16 tb=440
```

- `sizeof(RGXFWIF_KCCB_CMD)=72`，`uCmdData` 偏移 **8**（＝主线 `cmd_type` + `kccb_flags` 后接 union）
- `sizeof(RGXFWIF_POWER_REQUEST)=8`，`uPowerReqData` 偏移 **4**
- POW 命令前 16 字节的布局与主线 `struct rogue_fwif_kccb_cmd` 完全一致

→ **ABI 不一致的假设排除**。

### 2) 固件确实执行了 POW 命令（FACT，决定性）

新增 `kcmds` 字段（= `RGXFWIfFwOsData->ui32KCCBCmdsExecuted`）：

```
POW[sent]  sync=0 rtn=00000000 kccb=1/0 kcmds=0 pow=1
POW[poll]  sync=0 rtn=00000000 kccb=1/0 kcmds=0 pow=3        (t+10s)
POW[poll]  sync=0 rtn=00000000 kccb=1/0 kcmds=1 pow=2        (t+30s)
POW[poll]  sync=0 rtn=00000000 kccb=1/1 kcmds=1 pow=2        (t+40s)
```

- `kcmds` 0→1：固件**执行了一条 KCCB 命令**（命令已被取走并处理）
- `ePowState`: 1(ON) → 3(IDLE) → 2(FORCED_IDLE)：固件**接受了 forced-idle 请求**
- `sync` 始终 0：固件**没有写回执 prim**

→ 结论从“固件不处理命令”修正为：**命令被处理、状态也切换了，但完成信号没发出来**。

### 3) 为什么之前看不到 FW trace（FACT）

```
pvr-mtk: FWT after-pow logtype=00000203 size=0 ptr=0 buf=0000000000000000
pvr-mtk: FWT after-pow: buffer not allocated
```

- 启动时 `ui32LogType=0x00000001`（只有 TRACE 位，无 group）
- `RGXTraceBufferIsInitRequired()` 要求 `TRACE|GROUP_MASK`，因此 **trace 缓冲从未分配**
- 已在驱动里补：`pvr_fwtrace=1` 时在 FW 启动前调用
  `RGXTraceBufferInitOnDemandResources()` 并设置 `TRACE|MAIN|POW`，
  下一轮即可 dump 固件侧 POW 日志（`FWT>` 前缀）

### 4) 物理页直读未完成

`paview=deadbeef`：`memremap(pa, 0x1000, MEMREMAP_WC)` 返回 NULL（或 `vmalloc_to_page` 失败），
未能用来排除“CPU 缓存读不到固件写入”。下一轮需打印 pa 后再判。
参考：prim 块的分配标志是 `GPU_UNCACHED | CPU_WRITE_COMBINE`（`rgxinit.c: RGXAllocUFOBlock`），
理论上 CPU 应当能看到固件写入。

### 5) 当前主假设（HYPOTHESIS）

固件执行 forced-idle 后卡在 **dust/APM 掉电完成** 之前，故不写 prim：

- 我们以 `pvr_apm=0` 跳过 MTK APM 寄存器（0x504–0x528 与 0x24）编程；
- sysdata 仍带 `RGXFWIF_INICFG_POW_RASCALDUST`（`syscfg=0x00020030` bit4）；
- 固件按 APM 流程关闭 dust → 硬件不 ACK → prim 永不写。

验证方法：
1. 只写 dust 配置寄存器（0x504–0x528），**不写**会导致 `MFG_CORE0` 掉电的 0x24 序列，看 prim 是否出现；
2. 或先看 FW trace（已挂钩）中 POW group 的日志，确认卡在哪一步。

### 设备状态

2026-11-20 23:5x：`dd if=/dev/dri/renderD129` 之后内核再次卡死（串口无响应），需长按电源重启后继续。

---

## 2026-11-21：FW trace 路线关闭 + 两次 oops 根因 + MTS kick A/B（阶段收口）

### 1) FW trace：确认走不通（FACT，定论）

`pvr_fwtrace=1` + `EnableLogGroup=main,pow`，在 `RGXPostPowerState` 里于 **`RGXDoStart` 之前**设置：

```
FWT logtype=00000203 size=12000 flags=00000000 threads=1 ctl_fw=c001f000
FWT tid=0 ptr=0 buf_fw=c0036000 field=ffff8000858d3000
FWTRAW t0 11840..11992: 全 00000000
```

- 缓冲区**已正确分配**（12000 DWords = 48 KB，FW VA `0xc0036000`，主机 CPU VA 有效）
- logtype `0x203`（TRACE|MAIN|POW）在固件启动前写入
- 固件**一个 DWord 都没写**（`ui32TracePointer = 0`，整个窗口全 0）
- 对照：MIUI 正常机的 debug dump 里同样是 `Debug log type: none`
  （`logs/diag/miui-gpu/debug_dump_utf8.txt:160-161`）

→ **量产 `rgx.sh` 不输出 FW trace**，这条诊断路线永久关闭，不要再投入。

### 2) 两次内核 oops 的根因（FACT，已修复）

| # | 现场 | 根因 | 修复 |
|---|---|---|---|
| 1 | `memremap+0x208`，`x19=0x42c7c000` | 用 `MEMREMAP_WC` 映射普通 RAM 直读 prim 物理页，本平台直接 fault | 删除该诊断代码 |
| 2 | `RGXDumpFirmwareTrace+0x1f8`，FAR `ffff80077ba4caf8`，`pud=0` | 直接信任共享结构（write-combine）里的 `pui32TraceBuffer`，读到坏指针后解引用 | 改为 dump 时用 `DevmemAcquireCpuVirtAddr(memdesc)` 重新取，并校验 `>>48 == 0xffff`；解码改用原始 DWord 打印 |

### 3) 本轮新增观测（FACT）

- 同参数不同轮次，固件对 POW 命令的响应**不稳定**：
  - 有时 `kcmds 0→1`、`pow 1→3→2`（命令被执行、进入 FORCED_IDLE），但 `sync` 仍为 0
  - 有时 `kcmds=0`、`r=0`（命令根本没被取走），`pow=3`
- 固件**启动本身**也偶发失败（`boot stage=0`，`FW started` 超时），本轮最后一次即撞上，
  该轮 POW 数据无效。

→ 两个不稳定现象同源的可能性高：**GP 的 MTS 调度/唤醒不可靠**。

### 4) 已就绪但未取得有效数据的 A/B（UNVERIFIED）

**先看旧结论**（FACT，2026-11-20 19:4x）：早前已做过一次“手动补写 `RGX_CR_MTS_SCHEDULE(0xB00)=DM_GP`”，
20 ms 内 `kccb w=1 r=0` **毫无变化**（本文件 439-443 行）。
所以单次 kick 无效已证；本轮 `pvr_kick=1` 是**加强版**（2 秒内 40 次），用于排除“单次写入丢失”。

`pvr_kick=1`：发完 POW 后每 50 ms 重写 `RGX_CR_MTS_SCHEDULE (0xB00)` 并回读，
同时打印 `kccb w/r`、`kcmds`、`pow`：

```
pvr-mtk: KICK %u rb=%08x kccb=%u/%u kcmds=%u pow=%u
```

判读标准：
- `kcmds` 在 kick 期间立刻增长 → **MTS 调度是主因**，下一步查 `RGX_CR_MTS_SCHEDULE` 初始化/OSID，而不是 POW
- `rb` 恒非 0 或 `kcmds` 始终 0 → MTS 也死，停止该方向

本轮因固件启动失败未拿到数据，模块 `pvr-t6.ko` 已留在设备 `/root/`。

### 5) 复现命令（设备侧，已可用）

```sh
insmod /root/pvr-t6.ko pvr_apm=0 pvr_os_active=1 pvr_kick=1
timeout 110 dd if=/dev/dri/renderD129 of=/dev/null bs=1 count=1
dmesg | grep -e KICK -e POW
```

注意：
- `reboot -f` 才可靠；`reboot` 有时不执行
- 固件启动失败时本轮作废，直接重启重试
- 串口 ACM 在 oops 后会死（NCM 仍活），需拔插 USB 或重启

### 6) 阶段结论

| 项 | 结论 |
|---|---|
| 命令 ABI（72B / 偏移 8 / POW 8B） | ✅ 已证一致 |
| 页表 / 物理页 / 属性 | ✅ 已证一致 |
| 固件执行 POW（`kcmds` 增长） | ⚠️ 偶发成功，但不稳定 |
| forced-idle 回执 prim | ❌ 从未写入 |
| FW trace | ❌ 固件不输出，路线关闭 |
| 根因定位 | 未完成；最强假设是 **GP MTS 调度/唤醒不可靠**（HYPOTHESIS） |

### 7) 收口后的建议（下次开工从这里继续）
按性价比排序，只做这三件之一：

1. **对比 vendor 的 MTS 初始化**：`rgxinit.c:1436` 那处 `RGX_CR_MTS_SCHEDULE` 写入、
   `RGX_CR_MTS_*` 相关寄存器、以及 vendor 4.19 在 `RGXPostPowerState` 里是否额外写了
   `MTS_SUSPEND`/`MTS_INT` 之类寄存器。这是目前唯一没有对照过的寄存器组。
2. **查 KCCB 的 readback 可见性**：`kcmds`、`r` 都来自 FW 写的共享内存；如果 FW 的写没落盘
   （例如 FW 侧对这块内存的映射是 write-back 而主机是 write-combine），主机就永远看不到。
   可用“FW 写入后触发一个 IRQ，主机在 ISR 里读”的方式交叉验证（`fwirq` 已经能看到）。
3. 若还要碰 POW 完成路径，只剩 `RGXFWIfFwOsData->sPowerSync` 的**写入是否真的发生**这一条，
   但已证明 ABI/PTE/物理页全部正确，继续投入性价比很低。

不建议再做的事：
- 再开 FW trace（固件不输出）
- 再改时钟 / 复位 / APM 寄存器（已多次证明不是启动失败主因）
- 再改 prim 地址（PTE 审计已排除）

---

## 2026-11-21：查小米开源仓库（Poco C3 / C31）与固件版本核对

### 1) 官方分支（FACT）
- `MiCode/Xiaomi_Kernel_OpenSource` 里**没有** Poco 专用分支；
  README 明确：`dandelion-q-oss` = **Redmi 9C / Redmi POCO C3 / Redmi 9A**
- Poco C31 的内部代号是 `angelicain`（LineageOS blossom 设备树），但小米未单独发分支 → 同样走 dandelion
- 该分支内核 **4.9.190**，GPU DDK 是 **m1.11ED5425693**
  （`drivers/misc/mediatek/gpu/gpu_rgx/Makefile`：`doma/lorne/clark` → `m1.11ED5425693/`）

### 2) 但本机实际基线是 4.19 + DDK 1.13（FACT，决定性）

| 证据 | 值 |
|---|---|
| 原厂 vendor 分区模块 vermagic | `4.19.127-perf-g7288046673d5 SMP preempt mod_unload modversions aarch64` |
| 本机 `rgx.sh` md5 | `6456299eddd62b1834f71e81b4d6bb67` |
| `vendor_backup.img` 内 rgx.sh | **同一 md5**（字节完全一致） |
| FrankenROM / crDroid vendor.img 内 rgx.sh | **同一 md5** |
| 我们移植的 DDK | `m1.13ED5776728`（4.19 代） |

→ **固件与 DDK 是同一代（1.13），"FW/DDK 版本错配" 假设排除。**
  `dandelion-q-oss`（4.9/1.11）是 Android 10 时代的旧分支，不是本机实际跑的那一代。

### 3) 对后续路线的意义

- 继续主线：DDK 源码与固件版本都已确认正确，剩下的差异仍然是 **vendor 4.19.127 的 GPU 电源框架（GED / gpufreq / MTCMOS / APM）**
- 若走 "vendor 内核 + Alpine"：应当基于 **4.19（blossom 系，LineageOS/crDroid 公开源码）**，而不是小米的 4.9 分支
  该内核 + 同一份 `rgx.sh` 在定制 ROM 上是能点亮 GPU 的（`logs/device/blossom-20261017` 里有 `Initialized pvr 1.13.5776728`）

### 4) 结论
Poco C3/C31 的开源发布**没有新增可用信息**；但它反证了一件事：
**我们的 DDK/FW 组合是对的**，问题只在移植层，不在版本代差。

---

## 2026-11-21 下午：A6/A6b 实验（MTCMOS / dust-only APM / POW_OFF）

完整记录见 `../dandelion-gpu-refactor/notes/a6-results.md`，要点：

| 实验 | 结果 |
|---|---|
| MTCMOS 显式序列（`skip_mtcmos=0`） | 执行成功，但寄存器读数与空闲态**完全相同** → 该假设排除 |
| `pvr_apm=2`（dust-only） | 固件能到 `pow=2 FORCED_IDLE`，但 `sync` 仍 0 |
| `pvr_pow_off=1`（POW_OFF_REQ） | 固件到 `pow=0 OFF`，`sync` 和 `rtn` 仍 0 |
| `pvr_no_apm=1`（清 RASCALDUST） | 固件启动即 OFF，finalize 提前超时，组合不可用 |

唯一未解释现象：**固件执行 POW、改 `ePowState`，但不写任何主机可见完成标志**（prim/rtn 都不写）。
下一步：A7 —— dump `SYSINIT/OSINIT/SYSDATA/OSDATA/RUNTIMECFG` 全量 hex，与 MIUI dump 逐项对照。

---

## 2026-11-21 晚：里程碑 —— `/dev/dri/renderD129` 首次 open 成功

完整存档见 `../dandelion-gpu-refactor/notes/MILESTONE-open-ok.md`。

```
insmod /root/pvr-t20.ko pvr_apm=2 pvr_os_active=1 pvr_no_sync=1 pvr_pow_off=1
→ OPEN_OK
```

关键修复（FACT）：

1. `RGXPrePowerState` 在 "pending interrupts" 超时后重采样并对齐 host/FW 计数，
   相等则清掉旧的 `eError`（IRQ 计数竞态：固件先发中断、后写计数，且不再发第二次）。
2. `pvr_no_sync` 的 pow-state 绕过分支补上正常 teardown（`RGXDoStop` 等）。
3. LISR 在 `RGXFwIrqEventRx` 已清中断但计数未变时返回 `IMG_TRUE`，避免被当 spurious。

结论：**prim 只是完成通知**，固件不写它并不妨碍电源状态机推进；
open 成功依赖 `pvr_no_sync=1` + `pvr_pow_off=1`，仍属受控绕过，尚未验证渲染。


---

## 2026-11-24：根本原因彻底查明并修复 —— 零绕过 18ms 原生完成 FW 启动/握手/上下电 + 64 位用户态库提取

### 1) 终极根因：`vm_map_ram()` 去掉 `prot` 导致 Uncached/Write-Combine 共享内存被映射为 `PAGE_KERNEL` (Write-Back Cached)（FACT，定论）

在 `scripts/pvr-api-fix1.py` 为适配主线 Linux 7.1 的 3 参数 `vm_map_ram(pages, count, node)` 时，直接删除了第 4 个 `prot` 参数：
- `drivers/misc/pvr/ddk/services/server/env/linux/physmem_osmem_linux.c`（`PMRAcquireKernelMappingDataOSMem`、`_ZeroPageArray`）
- `drivers/misc/pvr/ddk/services/server/env/linux/dma_support.c`（`SysDmaAcquireKernelAddress`）

这导致在 ARM64 64 位内核上，原本走 `vm_map_ram(pagearray, ui32PageCount, -1, prot)` 分支的所有 `PVRSRV_MEMALLOCFLAG_CPU_UNCACHED` 与 `PVRSRV_MEMALLOCFLAG_CPU_WRITE_COMBINE` 共享内存（包括 MIPS 页表、Boot/NMI 共享数据区、KCCB 控制结构与队列、`sPowerSync` 完成原语、返回槽 `rtn`）：
- **在 GPU/MIPS 固件侧**通过 GPU MMU 被映射为 **Uncached / Write-Through**（直写物理 DRAM）；
- **在 ARM64 CPU 主机侧**却被 `vm_map_ram()` 固定映射为 **`PAGE_KERNEL`（Normal Write-Back Cached）**！

这一处缓存属性失配同时解释了此前所有的异常现象：
1. **CPU 写入留在 CPU D-Cache 未及时落盘**：`_ZeroPageArray` 清零、MIPS 页表更新、KCCB 命令写入、NMI 唤醒请求留在 CPU 缓存中，MIPS 从物理内存读到旧数据（导致间歇性 `FW started` 超时、KCCB 延迟 10~90 秒才被消费、NMI 状态全 0 或 `0xFFFFFFFF`）。
2. **MIPS 写入物理 DRAM 被 CPU 旧缓存遮蔽**：CPU 初始化时读过一次 `sPowerSync=0`、`rtn=0` 后该缓存行常驻 CPU D-Cache，MIPS 固件向物理 DRAM 写入 `sPowerSync=1` 和 `rtn=1` 后，CPU 轮询读到的永远是自己缓存里的 `0`！

### 2) 修复方案（仅 1 行核心宏定义 + 2 处配套加固）

1. **开启 `vmap(..., prot)` 路径**：
   在 `drivers/misc/pvr/ddk/include/pvr_compat_prologue.h` 中定义：
   ```c
   #define PVRSRV_FORCE_SLOWER_VMAP_ON_64BIT_BUILDS 1
   ```
   使 `physmem_osmem_linux.c` 与 `dma_support.c` 切换至 `vmap(pagearray, count, VM_READ | VM_WRITE, prot)` / `vunmap()`，完整保留 `pgprot_noncached` / `pgprot_writecombine` 页保护属性。
2. **修复并发 `open("/dev/dri/renderD129")` 初始化竞态**：
   在 `drivers/misc/pvr/ddk/services/server/env/linux/module_common.c` 的 `PVRSRVDeviceOpen()` 中增加 `static DEFINE_MUTEX(g_pvr_open_lock);`，保护 `eDevState == PVRSRV_DEVICE_STATE_INIT` 的首次固件加载与 IRQ 注册，消除 Ubuntu 下 `udev` 与用户进程并发打开设备节点导致的 `genirq: Flags mismatch irq` 竞态。
3. **清理全部临时绕过并加固平台层时钟对称性**：
   - 将 `rgxpower.c`、`rgxinit.c`、`rgxfwutils.c`、`rgxfwutils.h`、`rgxstartstop.c`、`rgxdebug.c`、`fwload.c`、`rgx_bvnc_table_km.h` 全部还原至无 hack 的干净基线。
   - 在 `drivers/misc/pvr/ddk/services/system/rogue/rgx_mtk/pvr_platform_mt6765.c` 中加入 `mfg_clk_enabled` 状态位，保证 `Init`/`PostPowerState`/`PrePowerState`/`DeInit` 中 `clk_prepare_enable` 与 `clk_disable_unprepare` 严格 1:1 对称，支持反复 `insmod`/`rmmod`。

### 3) 实机验证结果（FACT，Linux 7.1.0-mt6765+ #34 + Ubuntu 24.04）

在**零绕过参数**下直接加载干净驱动并打开 `/dev/dri/renderD129`：
- `sPowerSync`（`0xc0019000`）在 **0.89 ms** 内由固件写回 `1`；
- KCCB 指针瞬间完成 `1/1 -> 2/2`，电源状态无超时完成 `ON(1) -> FORCED_IDLE(2) -> OFF(0)`，全程仅耗时 **18 ms**；
- MIPS NMI 调试转储（`_RGXMipsExtraDebug`）正常返回 `PC=0xC00153DC`、`STATUS=0x00481C05`、`CAUSE=0x00800000`、`SP=0xCF600FE0` 及全部 16 条有效 TLB 项，与 MIUI 4.19 原厂快照完全一致；
- 已部署至手机 `/lib/modules/7.1.0-mt6765+/extra/pvrsrvkm.ko` 及 `/lib/firmware/rgx.{fw,sh}.22.87.104.18`，开机自动加载成功（`/dev/dri/card2`、`/dev/dri/renderD129`、`/dev/pvr_sync` 全部就绪）。

### 4) 64 位 PowerVR DDK `1.13@5776728` 用户态库提取与符号审计（FACT）

从类原生 Android 16 ROM（`blossom`）的 `vendor.new.dat.br` + `vendor.transfer.list` 解包出 `vendor.img`，确认包含与当前内核驱动 **100% 同源同版本**（`1.13@5776728`、BVNC `22.87.104.18`、`rgx.sh` MD5 `6456299eddd62b1834f71e81b4d6bb67` 完全一致）的 **64 位 (`aarch64`) 用户态驱动栈**，已归档至 `dist/vendor-pvr64/`：
- 核心 EGL/GLES/USC/Srv 库：`lib64/libsrv_um.so`、`lib64/libIMGegl.so`、`lib64/libusc.so`、`lib64/libglslcompiler.so`、`lib64/libPVRMtkutils.so`、`lib64/egl/libEGL_mtk.so`、`lib64/egl/libGLESv2_mtk.so`、`lib64/egl/libGLESv1_CM_mtk.so`
- Gralloc / Vulkan / OpenCL：`lib64/hw/gralloc.rogue.so`、`lib64/hw/vulkan.mt6765.so`、`lib64/libufwriter.so`、`lib64/libPVROCL.so`
- 辅助库：`lib64/libgralloc_extra.so`、`lib64/libged.so`、`lib64/libgpu_aux.so`、`lib64/libgpud.so`、`lib64/libmpvr.so`

**64 位用户态 glibc 兼容层审计结论**：
- 全部 11 个核心 64 位 PowerVR `.so` 均为标准 `ELF64 aarch64`（无 `PT_TLS` 段，`tpidr_el0` 仅读取 `[tpidr_el0, #40]` 栈金丝雀，`stdout`/`stderr`/`stat`/`fstat`/`__vsnprintf_chk` 与 glibc `2.39` 同签名）；
- 除 glibc (`libc.so.6`/`libm.so.6`/`libz.so.1`) 已提供的符号外，仅需在轻量级兼容垫片 `libbionic_compat.so` 中提供：
  1. 15 个 Bionic/Android 基础函数（`__errno`、`__android_log_print`、`__system_property_get`、`sync_wait`/`sync_merge`/`sync_file_info`、`android_load_sphal_library` 及 6 个 `__*_chk` 包装）；
  2. 16 个结构体尺寸敏感函数的安全转发（40B Bionic `pthread_mutex_t` / 48B `pthread_cond_t` 指针封装、176B ARM64 `setjmp`/`longjmp`）；
  3. MTK 辅助桩函数（`ged_*` 空桩、`g_gpud_context` 全零关闭调试转储、`GpuAux*` 空桩、以及用 DRM dumb buffer / DMA-BUF 实现 `mt_ion_open` / `ion_alloc_fd`）。


### 5) 64 位 Ubuntu 24.04 原生进程 PowerVR GE8320 硬件 3D 渲染打通 + `bEnableRDPowIsland` 修复（FACT，2026-11-24 11:38）

#### (1) 用户态兼容层 `libb.so` (`src/pvr64/bionic_compat.c`) 与 ELF 补丁器 (`src/pvr64/patch_pvr_elf.py`)
在 64 位 Ubuntu 24.04 (`aarch64-linux-gnu`) 原生环境中直接加载 64 位 Android Bionic PowerVR 驱动库，排查并解决了以下 4 个核心 ABI 差异：
1. **`DT_ANDROID_RELR` 重定位标签转换**：`libgralloc_extra.so` 使用了 Android 私有动态标签 `0x6fffe000`/`0x6fffe001`/`0x6fffe003`，通过 `patch_pvr_elf.py` 转换为标准 ELF `DT_RELR (36)` / `DT_RELRSZ (35)` / `DT_RELRENT (37)`，由 glibc 2.39 动态链接器原生完成相对重定位。
2. **Bionic `sysconf(_SC_PAGESIZE)` 常量差异**：Bionic 中 `_SC_PAGESIZE = 0x27 (39)`，而在 glibc 中 `39` 是 `_SC_AIO_PRIO_DELTA_MAX`（返回 `20`），导致 `libsrv_um.so` 的 `OSGetPageShift()` 算出 `7` 而非 `12`，使 `mmap` 的 PMR 句柄偏移错位并报 `PVRSRV_ERROR_HANDLE_INDEX_OUT_OF_RANGE`。在 `libb.so` 中拦截 `bsyscon(0x27)` 返回 `4096` 后，`AcquireInfoPage()` / `DevmemAcquireCpuVirtAddr()` 一次性映射成功。
3. **ARM64 `MT_NORMAL_NC` (Write-Combine) 内存上的 `DC ZVA` 对齐故障**：glibc `memset` 在长度 $\ge 64$ 字节时使用 `dc zva` 指令，在 `pgprot_writecombine` 映射的 GPU 缓冲区上会触发 ARM64 Alignment Fault (`SIGBUS`)。在 `libb.so` 中提供无 `dc zva` 的 `bmemst` / `bmemcp` 并替换符号引用。
4. **Bionic 64 位 `pthread_mutex_t` (40B) / `pthread_cond_t` (48B) 的 4 字节对齐**：Bionic 64 位下 `pthread_mutex_t` 定义为 `int32_t __private[10]`（仅保证 **4 字节对齐**而非 8 字节对齐），ARM64 的 64 位原子指令 `ldar xN` / `stlr xN` 在 4 字节对齐地址（如 `0x...c`）上直接触发 `SIGBUS` (`BUS_ADRALN`)。改为 32 位原子标志 (`uint32_t magic`) + 拆分高低 32 位指针槽位后彻底解决。

#### (2) 连续 3D 渲染死锁根因：`MTK_USE_HW_APM` 导致 `bEnableRDPowIsland = true` 等待未启用的硬件 APM（FACT，定论）
- 首次 3D 渲染成功后，第二次运行出现 `HW operation timeout`，内核 `PVR DBG` 转储明确显示：
  - `T0 polling set (reg:0x00000130 mask:0x00000C00)`（即 `RGX_CR_EVENT_STATUS` 的 `POWER_ABORT_EN | POWER_COMPLETE_EN` 位）；
  - `FW System config flags = 0x00020030 (...; Power Rascal/Dust; ...)`。
- **原因**：`drivers/misc/pvr/ddk/services/system/rogue/rgx_mtk/sysconfig.c` 因定义了 `MTK_USE_HW_APM` 而将 `gsRGXTimingInfo.bEnableRDPowIsland` 设为 `true`，告知固件在 3D 渲染结束后请求外部 MTK HW APM 控制器关闭 Rascal/Dust 电源岛并轮询 `0x0130` 的 `POWER_COMPLETE (0x400)` 信号；但平台层 `pvr_apm=0` 并未启用 MTK HW APM 硬件状态机，导致第一次 3D kick 完成后固件永久死等 `0x0130 & 0xC00`。
- **修复**：在 `sysconfig.c` 中将 `gsRGXTimingInfo.bEnableRDPowIsland` 设为 `false`。

#### (3) 连续 3 次 64 位 EGL + OpenGL ES 3.2 硬件渲染实机验证（FACT）
重启加载更新后的 `pvrsrvkm.ko`，连续 3 次运行 `/root/pvr_gles2_test` 均在瞬间完成，零超时、零警告：
```text
=== PowerVR GE8320 64-bit EGL/GLESv2 Offscreen Render Test ===
[1] Loaded 64-bit libEGL_mtk.so and libGLESv2_mtk.so successfully!
[2] eglGetDisplay = 0x1
[3] eglInitialize OK: EGL 1.4 (Imagination Technologies)
[4] GL_VENDOR   = Imagination Technologies
    GL_RENDERER = PowerVR Rogue GE8320
    GL_VERSION  = OpenGL ES 3.2 build 1.13@5776728
    GL_SL_VER   = OpenGL ES GLSL ES 3.20 build 1.13@5776728
[5] Vertex shader compile: OK
    Fragment shader compile: OK
    Shader program link: OK
[6] Readback pixel (10,10) background RGBA = (20, 31, 61, 255)
    Readback pixel (128,128) triangle RGBA = (141, 95, 83, 255)
[7] Saved hardware-rendered frame to /tmp/pvr_render.ppm
[8] Cleanly destroyed EGL context/surface and terminated EGL display.
```
渲染出的帧已保存为 `dist/vendor-pvr64/pvr_render.ppm`。

---

### 6) `mediatek-drm` 零拷贝 DMA-BUF 与 `phoc` (`wlroots 0.17`) 桌面合成器接入（FACT）

1. **零拷贝 DMA-BUF 验证（`src/pvr64/pvr_dmabuf_test.c`）**：
   - 在 `/dev/dri/card1` (`mediatek-drm`) 分配 DRM dumb buffer 并通过 `DRM_IOCTL_PRIME_HANDLE_TO_FD` 导出 `dmabuf_fd`，经 `eglCreateImageKHR(EGL_LINUX_DMA_BUF_EXT)` 导入 PowerVR 并绑定 FBO 渲染，无需 `glReadPixels` 即可从 dumb buffer `mmap` 直接读出渲染结果。
2. **glibc 端 PowerVR 桥接库（`src/pvr64/build_bridge.sh` → `dist/vendor-pvr64/bridge/`）**：
   - `src/pvr64/pvr_gbm.c` → `libgbm.so.1`：以 `mediatek-drm` DRM dumb buffer + `PRIME_HANDLE_TO_FD` 实现 `wlroots 0.17` 所需的 `gbm_device` / `gbm_bo` 分配与导出接口（32 像素宽度对齐，仅线性 modifier）。
   - `src/pvr64/pvr_egl.c` → `libEGL.so.1`：转发 `/vendor/lib64/egl/libEGL_mtk.so`（`libIMGegl.so`），补充 `EGL_EXT_platform_base` / `EGL_KHR_platform_gbm` 客户端扩展、`eglGetPlatformDisplay(EXT)`、`eglQueryDmaBufFormatsEXT` / `eglQueryDmaBufModifiersEXT`、DMA-BUF modifier 过滤以及无配置/无表面回退。
   - `src/pvr64/pvr_glesv2.c` → `libGLESv2.so.2`：转发 `/vendor/lib64/egl/libGLESv2_mtk.so`，将 `glFlush` 转为 `glFinish` 以保证隐式同步，并在 ES 3.x 上下文下补充广告 `GL_EXT_unpack_subimage`。
3. **Phosh 会话接入与自动回退（`src/pvr64/session/`）**：
   - `phoc-pvr`：仅对 `phoc` 进程设置 `LD_LIBRARY_PATH=/vendor/lib64/pvr-bridge:/vendor/lib64:/vendor/lib64/egl` 与 `WLR_RENDERER=gles2`，并通过 `-E env -u ...` 为子会话清除环境变量，避免影响常规 Mesa 应用。
   - `start-phosh`：优先尝试 `phoc-pvr`；若 20 秒内退出则记录 `~/phosh-pvr-failed.log` 并回退到软件渲染会话。
   - 实机已验证 `phoc` 成功初始化 `EGL_PLATFORM_GBM_KHR`，日志显示 `GL vendor: Imagination Technologies` / `GL renderer: PowerVR Rogue GE8320`，`/proc/<pid>/maps` 确认加载了 `pvr-bridge` 与 `/vendor/lib64` PowerVR 驱动库。
   - 诊断脚本：`src/pvr64/tools/check_phoc_gpu.sh`。


---

### 7) 日用收尾与异步同步 / Wayland 客户端接入（FACT，2026-11-24 晚）

1. **`/dev/pvr_sync` udev 权限与调试日志清理**：
   - 修复手机 `/etc/udev/rules.d/99-pvr.rules` 为 `KERNEL=="pvr_sync", MODE="0666"`，解决非 root 用户 `PVRFDSyncOpen` 报 `Permission denied` 导致回退软件渲染的问题。
   - 移除 `/usr/local/bin/phoc-pvr` 中的临时 `PVR_EGL_DEBUG=1 G_MESSAGES_DEBUG=all` 调试参数，保持日志干净。
2. **C1 异步 Native Fence 同步（`pvr_egl.c` + `pvr_glesv2.c`）**：
   - 替代每帧 `glFinish()` 阻塞：`glFlush()` 后通过 `EGL_ANDROID_native_fence_sync` + `eglDupNativeFenceFDANDROID()` 导出 `sync_file` fd，经 Linux 7.1 `DMA_BUF_IOCTL_IMPORT_SYNC_FILE` 注入对应 `dma-buf`，由 `mediatek-drm` 内核态等待 GPU 完成（720×1600 120 帧基准测试从 `626.4 FPS` 提升至 `982.7 FPS`，`120/120` 导入成功）。
3. **Wayland 客户端硬件加速（`EGL_PLATFORM_WAYLAND_KHR`）**：
   - 新增 `src/pvr64/pvr_wl.h` 并在 `pvr_egl.c` / `pvr_glesv2.c` 实现 `EGL_PLATFORM_WAYLAND_KHR`、`eglCreatePlatformWindowSurface(EXT)`、`zwp_linux_dmabuf_v1` 3 缓冲交换链及默认 FBO（`0`）重定向；
   - 更新 `src/pvr64/session/phoc-pvr` 向会话保留 `LD_LIBRARY_PATH` 并设置 `GSK_RENDERER=gl`，实测 `wl_egl_test` 与 GTK4 应用（`phosh-mobile-settings`）及 `phoc`/`phosh`/`phosh-osk-stub` 会话均稳定运行。
4. **TI glibc 原生用户态路线（路线 A）证伪结论**：
   - 实测打穿 `CompatibilityCheck` 与 `gaFeatures`/`gaErnsBrns` 表后，在内核 `RGXAlignmentCheck` 撞上编译期结构体 ABI 硬阻塞：`RGXFWIF_CMD3D`（`RGXFW_ALIGN_CHECKS_INIT[21]`）在 TI `22.104.208.318` 库中为 `352 B`，本机 `22.87.104.18` 固件为 `320 B`，确认闭源 UM 与具体 BVNC 强绑定，已关闭路线 A 并清理 `/opt/pvr`。
5. **内核仓库收口（WSL `dandelion-7.1`）**：
   - `50f7a102d` `pvr: finalize PowerVR GE8320 DDK 1.13 bringup on mainline 7.1`
   - `5bbf455dc` `pvr: clean up PVR_DUMPDEBUG_LOG, double-check open lock, and clk_enable`（修复 `pvr_notifier.h` 空宏、`module_common.c` 双检锁、`pvr_platform_mt6765.c` 时钟幂等检查）


## 8. Mesa PowerVR (Stage 2/3) 进展 (2026-11-25)

状态: vk_probe 枚举 GE8320 成功; vk_clear_test 的 vkCreateDevice/Submit/WaitIdle 成功, 但读回全 0。

已对齐 DDK 1.13: SRVKM_INIT 不存在; sync ioctl 走 /dev/pvr_sync('W'); HEAP 名 VisTest;
PMR/MAPPMR/MAPPAGES/DMABUF 的 flags 为 u32; TQ/CMP/TA3D bridge 结构重排; reset-framework cmd size=4;
ROGUE_NUM_GEOM_CORES_SIZE=1; simple_parameter_format_version 断言放宽到 >=1 (v1 macrotile 布局未核对)。

根因(读回为 0): Mesa 固件命令布局与 DDK 1.13 固件不一致。
Mesa: sizeof(cmd_3d)=488, cmd_ta=112, cmd_transfer=192; 1.13 (snapshot): CMD3D=320, CMDTA=80。
Mesa TQ 提交(192B)字段整体偏移, 例如 BGOBJVALS 在 0x0c, 而 1.13 CMD3D 在 0x10。
内核 bridge 对命令体不透明, 所以提交成功但固件读到错误布局。
下一步: 以 mesa-pvr-stage1-snapshot.txt 为依据写 1.13 布局的 fw-api 转换层(CMDTA 80B / CMD3D 320B), 并给 RGXSubmitTransferKM 加 dump 抓 TQ 命令。

### 8.1 TQ/TA/3D 真值捕获与测试改造（2026-11-25 续，接手后）

1. **Mesa 侧命令 dump**：`winsys/pvrsrvkm/pvr_srv_bridge.c` 增加 `PVR_DUMP_CMD=1` 门控的 hexdump（TQ/TA/3D）。
   - 旧 `vk_clear_test`（vkCmdClearColorImage）只发 TQ：2×192 B，前 8 字节是用户态指针，与 DDK 命令体无关。
   - 新增 `src/wayland/vk_clear2.c`：render pass `loadOp=CLEAR` 清到 **host-visible linear image**，直接 mmap 读回，
     完全**不走 TQ**；实测发出 `TA 112 B + 3D 488 B`，读回全 0（预期，布局未转换）。
2. **KMD 侧 TQ dump**：`rgxtransfer.c:PVRSRVRGXSubmitTransferKM` 增加 `pvr_dump_tq` 模块参数，
   用厂商 UM（greetd→phoc 合成）抓到 DDK 1.13 的 TQ 命令真值：
   - **size = 152 B**（Mesa 是 192 B），
   - 记录在 `mesa-pvr-stage1-snapshot.txt` 末尾。
   - 注意：模块必须保留符号表（`strip --strip-debug`），`strip -s` 会导致
     `module has no symbols (stripped?)` → Invalid module format。
3. **vendor DDK 源码确认**：4.19 的 `gpu_rgx/m1.13ED5776728` 只有 KM + `rgx_fwif_shared.h`，
   **没有** `RGXFWIF_CMD3D/CMDTA/CMDTRANSFER` 的完整定义（只有 alignchecks 引用），
   所以 1.13 布局仍需靠 golden snapshot + Mesa 结构对照来写转换层。
4. **下一步**：以 `vk_clear2` 为唯一验证用例，写 `pvr_srv_fwif_113` 转换层（CMDTA 80 B / CMD3D 320 B），
   用 snapshot 里的常量逐项对齐；TQ 152 B 布局留到需要 copy/readback 时再做。

### 8.2 1.13 CMDTA/CMD3D 转换层跑通，`vk_clear2` 首次读回红色（2026-11-25 晚）

**结论（FACT）**：`vk_clear2` 现在返回 `rc=0`，读回 `first32=ff0000ff`，即 `(255,0,0,255)`；
64×64 表面目前覆盖 **1024/4096** 像素（左上 32×32），其余仍为 0。

关键步骤：

1. **厂商 GLES UM 作 oracle（FACT）**
   - 直接用 `libEGL_mtk.so`/`libGLESv2_mtk.so` 时 GL 入口点不稳定；
     改用项目自己的 glibc 桥接库：
     `EGL_LIB=libEGL.so.1 GLES_LIB=libGLESv2.so.2`，
     `LD_LIBRARY_PATH=/root/pvrb:/root/pvr64:/root/pvr64/egl:/root/pvr64/hw`。
   - `scripts/gles_clear.c` 用 `eglGetProcAddress` 取 GL 入口点，64×64 红/绿/蓝
     读回分别为 `(255,0,0,255)` / `(0,255,0,255)` / `(0,0,255,255)`。
   - 抓到 1.13 `CMDTA=80 B`、`CMD3D=320 B`；offsets 见
     `mesa-pvr-stage1-snapshot.txt`。

2. **Mesa render-pass clear 不是硬件 clear（FACT，重要）**
   - `vk_clear2` 的 `loadOp=CLEAR` 在 Mesa 里走 **load-op PDS shader**
     (`pvr_arch_mrt.c` / `pvr_usc.c`)，`usc_clear_register` **全 0**，
     clear colour 在 shader 的 shared registers / PDS 数据里。
   - 因此不能只照抄 GLES `glClear` 的 `0x14=clear colour`；必须把
     Mesa 的 `pds_bgnd` / `pds_pr_bgnd` / `event_pixel_pds_data` 映射进去。

3. **转换层（FACT）**
   - `pvr_arch_srv_job_render.c` 新增 `pvr_pack_cmd_ta_113()` /
     `pvr_pack_cmd_3d_113()`，提交 80 B TA + 320 B 3D。
   - 1.13 3D 地址块修正：`0x40 = event_pixel_pds_data`，
     `0x48/0x50 = isp_scissor_base/isp_dbias_base`，
     `0x100/0x118 = pds_bgnd/pds_pr_bgnd`。
     修正前固件在 `EventStatus=0x10 (ISP_END_MACROTILE)` 锁死；修正后 clear 成功。
   - 通过内核 `PVRSRVRGXKickTA3DKM` 的 `pvr_dump_kick` 确认提交
     `ta_sz=80 pr_sz=0 3d_sz=320`（PR 与 3D 合并，与厂商一致）。

4. **HWRTData 与厂商 1.13 UM 对齐（FACT + 现场对比）**
   - 在 `rgxta3d.c` 临时加 `pvr-hwrt:` 打印，对比厂商 GLES 与 Mesa
     对 64×64 的 `RGXCreateHWRTDataSet` 入参：
     - 厂商：`ppp=003f003f te_screen=00003003 mt1=00100000 mt2=00100000
       stride=10 rgn=10 isp_mtile=00040004 tpc=128/0`
     - Mesa（修正前）：`te_screen=00001001 rgn=4 isp_mtile=00020002 tpc=32/0`
   - 三处设备参数修正（`ge8300.h` / `rogue_hw_utils.h` /
     `pvr_arch_srv_job_render.c`）：
     1) BVNC 22.87.104.18 关闭 `simple_internal_parameter_format`；
     2) 该 BVNC 的 region header 按 **4 B** 计算（`uiRgnHeaderSize=16`）；
     3) `TE_MTILE1/2` 只写 x1/y1，x2/x3 置 0（厂商值 `0x00100000`）。
   - 修正后 Mesa 的 `te_screen/mt1/mt2/stride/rgn/isp_mtile` 与厂商一致；
     覆盖从 512 像素提升到 1024 像素。

5. **剩余问题（HYPOTHESIS，未验证）**
   - 64×64 仍只清左上 32×32。四次修正后 HWRTData 已基本一致。
   - 关键新证据：用 `-DW=32 -DH=32` 编的 `vk_clear2_32` 只清 **16×16**
     （256/1024），即覆盖面积始终是 **1/4**，不是固定 32×32。
     这说明 x/y 各被裁掉一半。
   - 已排除的候选：
     a) **scissor**：已实现默认全屏 scissor 表
        (`pvr_cmd_buffer_fill_default_scissor`)，3D 的 `0x48` 从 0
        变成有效地址 `0x5a0c0`，但覆盖仍是 1024/4096 → 不是 scissor；
     b) **region header 单位**：试过 4 B / `rgn=16` 与 5 B / `rgn=16`
        （厂商值），覆盖不变；
     c) `isp_ctl`（厂商 0x3600f）、硬件 clear 寄存器、`pds_info=0x204`
        均试过，覆盖不变；`bgobjvals=0x100` 反而完全不 clear；
     d) `mtiles 1×1`（tpc 128，与厂商一致），覆盖不变。
   - 剩余差异集中在 **load-op PDS/EOT 程序本身**：
     厂商 GLES clear 用硬件背景对象 + 自己的 PDS clear 程序，
     Mesa 的 load-op shader 在 1.13 上只覆盖 1/4。
     这不是 3D 命令字段能修的，需要改 clear 实现路径。
   - 建议下一步（按优先级）：
     1. `vkCmdClearColorImage` + **TQ 152 B** 硬件 clear（不依赖 load-op/TA）；
     2. 或在 Mesa 里把 `loadOp=CLEAR` 改成硬件 clear（`usc_clear_register`
        + PBE clear enable），绕过 load-op shader；
     3. 保留已实现的全屏 scissor 表（对正常 draw 是正确的）。
   - 下一步候选：
     a) 对比厂商 GLES clear 的 **scissor/region 表**内容，给 Mesa 分配全屏
        scissor table 并填 `isp_scissor_base`；
     b) 或改用 `vkCmdClearColorImage` + TQ 152 B 的硬件 clear 路径；
     c) 或在 1.13 侧把 EOT flush 的数据量改为整屏（需确认固件触发粒度）。

**验证状态**：`vk_clear2` 读回红 = 已实测；整屏覆盖 = 未完成（UNVERIFIED 修复方案）。
手机已恢复日用：原 `pvrsrvkm.ko.orig` + `greetd`/`phoc` 正常。

### 8.3 1.13 TQ 152 B 转换层跑通，`vkCmdClearColorImage` 整屏红（2026-11-25 晚）

**结论（FACT）**：`vk_clear_tq`（`vkCmdClearColorImage`）64×64 读回
`words=4096 nonzero=4096 red=4096`，四角全 `ff0000ff`。内核 `pvr_dump_tq`
确认提交 `size=152`，不再是 Mesa 的 192 B。

TQ 布局（由厂商 TQ golden + 本次 clear dump 确认）：

```text
0x00 isp_bgobjvals
0x04 usc_pixel_output_ctrl
0x08 usc_clear_register0..3
0x18 isp_mtile_size
0x1c isp_render_origin
0x20 isp_ctl
0x24 isp_xtp_pipe_enable      (1.13 没有 isp_aa)
0x28 event_pixel_pds_info
0x2c event_pixel_pds_code
0x30 event_pixel_pds_data
0x34 isp_render
0x38 isp_rgn
0x40 pds_bgnd0_base
0x48 pds_bgnd1_base
0x50 pds_bgnd3_sizeinfo
0x58 isp_mtile_base
0x60 pbe_wordx_mrty[2][3]    (48 B)
0x90 flags
```

Mesa 改动：

- 新增 `src/wayland/vk_clear_tq.c` + `scripts/build_vk_clear_tq.sh`；
- `winsys/pvrsrvkm/pvr_arch_srv_job_transfer.c` 新增
  `pvr_pack_cmd_transfer_113()`，把 192 B 的
  `struct rogue_fwif_cmd_transfer` 重排成 152 B；
- `cmd_sizes[i]=152`，其余仍走 Mesa 的 transfer 提交。

关键点：

- TQ clear 用 **`usc_clear_register0 = clear colour`**（0x08 = `ff0000ff`），
  `pds_bgnd0/1/3` 全 0；不经过 load-op PDS/EOT，所以不受 1/4 限制。
- 这仍然是 Mesa：`libvulkan_powervr_mesa.so` + `vkCmdClearColorImage`，
  不是厂商 Android Vulkan，也不是外部包装层。

**遗留**：render pass `loadOp=CLEAR` 仍只清 1/4（load-op PDS 在 1.13 的
限制）。日常合成器的背景 clear 若走 render pass load-op，仍会受影响；
Stage 5 的 draw 路径可以继续用 render pass，但 clear 需要另走 TQ 或
硬件 clear。当前手机已恢复日用，`vk_clear_tq` 可复现整屏红。

### 8.4 Stage 5 三角形：draw 已通，但视口仍只有 1/4（2026-11-25 晚）

新增：

- `src/wayland/vk_triangle.c`：64×64 线性 host-visible 颜色附件，render pass +
  `vkCmdDraw(3)`，顶点用 `gl_VertexIndex` 生成，无 vertex buffer；
- `scripts/tri.vert` / `scripts/tri.frag`；
- `scripts/build_vk_triangle.sh` + `scripts/spv_to_header.py`
  （host `glslangValidator` 编 SPIR-V，嵌入 C 头）。

**实测（FACT）**：

```text
words=4096 nonzero=1024 green=507 blue=517
center=00000000 (0,0)=ffff0000 (63,0)=00000000 ...
```

- **绿色像素出现**，说明 vertex/fragment shader、TA 控制流、3D 提交都跑通了；
- 背景蓝 517、三角绿 507，合计仍只有 1024/4096（左上 32×32）；
- 内核 dump：`ta_sz=80 pr_sz=0 3d_sz=320`，与 clear 相同；
- 三角颜色在 32×32 内按整屏视口缩放（不是只缺了三个象限），
  说明 **viewport 是 32×32**，不是 EOT/region 只 flush 了一部分。

**判断（HYPOTHESIS）**：

- 1/4 的根因在 **TA 控制流里的 viewport/VPT 块**；
- Mesa 的 control stream 是 1.15 格式，1.13 固件可能没解析，
  于是用默认 32×32 视口；
- 3D 命令字段、scissor、region header、TA flags（试过 0x00100000）
  都不是限制点。

**下一步**：

1. 抓厂商 GLES draw 的 **VDM control stream**（`vdm_ctrl_stream_base` 指向的 BO），
   对比 1.13 的 `TA_STATE_VIEWPORT`/VPT 块格式；
2. 在 Mesa 的 `pvr_csb` 里按 1.13 格式重发 viewport 块；
3. 或先绕过：用 `vkCmdClearColorImage`（TQ）做 clear，draw 仍走 render pass。

**验证状态**：draw 链路 = 已实测出像素；整屏 viewport = 未完成（UNVERIFIED）。
手机已恢复原 `pvrsrvkm.ko.orig` + `greetd`/`phoc`。

**8.4.1 控制流长度对比（FACT，2026-11-25 晚）**

在 `pvr_arch_cmd_buffer.c` 加了 `PVR_DUMP_CS=1` 的 control stream dump：

```text
pvr-cs len=60
0000: 02 00 01 20 80 1a 01 00 c0 19 01 00 80 19 00 00
0010: 00 a2 06 00 80 1f 00 4c 00 1a 01 00 00 19 01 00
0020: 05 00 00 00 41 04 00 00 00 06 00 68 03 00 00 00
0030: 80 03 00 00 80 a0 05 00 00 00 00 c0
```

- Mesa 的三角形 control stream 只有 **60 B**；
- 厂商 GLES clear/draw 的 `vdm_ctrl_stream_base` 高字是 **0x80 = 128 B**；
- 60 B 里主要是 PDS/USC 程序地址，**没有 1.13 的 viewport/VPT 状态块**；
- 因此 1.13 固件用默认 32×32 viewport，和观察到的 1/4 覆盖一致。

尝试用 `LD_PRELOAD` shim（`scripts/pvr_dump_shim.c`）记录厂商 UM 的
`PVRSRVMapToDeviceAddress`/`mmap`，抓到 51 个 CPU mapping，但 control stream
BO 不在这些映射里（很可能是 GPU-only 或未被拦截的映射），所以还没拿到
厂商 128 B 的原始内容。

**下一步（按可行性）**：

1. 内核侧用 `MMU_IsVDevAddrValid` / `MMU_GetVDevAddrPTE` 把
   `vdm_ctrl_stream_base`（本次 0x18b000）翻译成物理页，dump 128 B；
2. 或在 `libsrv_um.so` 里定位 TA/control stream 的提交函数，读它写入的块；
3. 拿到 1.13 的 VPT 块后，在 Mesa 的 `pvr_csb` 里补发。

已保留的调试工具：`PVR_DUMP_CS=1`、`scripts/pvr_dump_shim.c`、
`scripts/scan_pvr_maps*.py`。这些都不影响日常启动。

**8.4.2 厂商 128 B control stream 已抓到（FACT，2026-11-25 深夜）**

内核新增 `pvr_dump_stream`：

- `rgxta3d.c` 从 TA `0x10` 取完整 u64 VA（不是低 32 位）；
- `RGXTranslateDevVAddr`（`rgxmem.c`）按 PID 找 `SERVER_MMU_CONTEXT`；
- `MMU_GetVDevAddrPhys`（`mmu_common.c`）按 PTE 的
  `uiAddrMask/uiAddrShift` 取物理地址；
- `phys_to_virt` 后 `print_hex_dump` 输出 256 B。

实机（厂商 GLES clear）：

```text
pvr-stream: va=800018b000 phys=45a08000
00000000: 00000c80 00010000 4c000f84 00010040
00000010: 00010000 00000004 20000442 68000100
00000020: 00000002 00000380 00c2b000 c0000000
00000030: 00000000 ... 全 0
```

注意：`pvr_gles2_test`（clear + triangle）抓到的仍是同一份
**clear/load-op** stream（`va=80001c7000`），不是 draw 的 viewport stream。
下一步需要一个 **只 draw、不 glClear** 的厂商 GLES 三角形测试。
