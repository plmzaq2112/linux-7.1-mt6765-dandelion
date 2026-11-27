# k71-build 内核驱动对比复核（对照 TI DDK 1.13 + 编译产物）

对象：`\\wsl.localhost\Ubuntu-26.04\home\a12bbb\k71-build`（Linux 7.1 + MT6765 + vendor DDK 1.13@5776728）
基线：`_src/ti-rogue-driver-1.13`（TI 同版本 KM 源码）/ `graphics-driver/`（本机 vendor UM 二进制）

## 1. 三条修复的核对结果

| 声明 | 结论 | 证据 |
| --- | --- | --- |
| 定义 `PVRSRV_FORCE_SLOWER_VMAP_ON_64BIT_BUILDS` 走 `vmap(..., prot)` | 成立，且用的是 DDK 自带开关 | `include/pvr_compat_prologue.h:10`；`Makefile:13` 用 `-include` 全局强包含；4 处 `#if !defined(CONFIG_64BIT) || defined(...)` 分支本来就在 stock 里（`physmem_osmem_linux.c:954/979/3253/3297`、`dma_support.c:140/157`） |
| prot 真正生效 | 成立 | `physmem_osmem_linux.c:3192` 按 `ui32CPUCacheFlags` 选 `pgprot_noncached()` / `pgprot_writecombine()`，再由 `vmap` 应用 |
| .ko 里确实是新路径 | 成立 | `nm -u out/.../dma_support.o` 只有 `vmap`（无 `vm_map_ram`）；`pvrsrvkm.ko` 内 `g_pvr_open_lock.0` 存在 |
| 并发首次 open 加锁 | 成立 | `module_common.c:473` 起 `static DEFINE_MUTEX(g_pvr_open_lock)`，改后包含 `INIT` 双检 + `BAD` 直接返回 `-ENODEV` |
| 回退临时绕过 | 基本成立 | staged diff 删掉了 `pvr_no_apm/pvr_state_wait/pvr_kick/pvr_fwstate/pvr_fwtrace/pvr_skip_fidle/pvr_os_active/pvr_pow_off` 等 8 个诊断 module_param，以及 S3 IRQ 快照、`mtk_pvr_dump_spm`、CMA 分配 pr_info |
| clk 对称 | 成立（见下方 P3 的细节） | probe 里 `pm_runtime_get_sync` + `pvr_mtk_clk_enable`；`PrePowerState ON→OFF` 关时钟；`PostPowerState OFF→ON` 重开；`DeInit` 关时钟 + `pm_runtime_put_sync/disable` |

## 2. 需要收尾的问题

### P1 `pvr_notifier.h` 的 `PVR_DUMPDEBUG_LOG` 改动是死代码且签名不匹配（未提交）
```
-#define PVR_DUMPDEBUG_LOG(...)          // stock: 空实现
+#define PVR_DUMPDEBUG_LOG(...) \
+	do { if (pfnDumpDebugPrintf) pfnDumpDebugPrintf(pvDumpDebugFile, __VA_ARGS__); \
+	     else PVR_DPF((PVR_DBG_ERROR, __VA_ARGS__)); } while (0)
```
- 宏是纯 `(...)` 可变参，宏体却引用自由标识符 `pfnDumpDebugPrintf` / `pvDumpDebugFile`；一旦 services 侧出现调用点就编译失败（目前 `grep` 显示 services 下无调用者，所以没暴露）。
- 另外 `#if defined(MTK_DEBUG_PROC_PRINT)` 两个分支被改成完全相同，条件编译失去意义。
- 影响：`PVR_DBG_ERROR` 级输出，若被调用会在 dump 路径刷日志。
- 建议：回退为 stock 的空宏；需要打印就在调用点显式传参。

### P2 open 锁粒度：`if (STATE_INIT)` 被改成无条件加锁
- 现在**每次**打开 render 节点都会走 `mutex_lock`，即使设备早已初始化。
- 建议改成双检锁，保持热路径无锁：
```c
if (psDeviceNode->eDevState == PVRSRV_DEVICE_STATE_INIT) {
    mutex_lock(&g_pvr_open_lock);
    if (psDeviceNode->eDevState == PVRSRV_DEVICE_STATE_INIT)
        eError = PVRSRVCommonDeviceInitialise(psDeviceNode);
    mutex_unlock(&g_pvr_open_lock);
}
```
- 另外 `static DEFINE_MUTEX` 放在函数体内建议提到文件作用域（与其它 static 放一起），便于阅读和后续复用。

### P3 两个"看起来像漏改"的点，其实不是
1. `nm -u pvrsrvkm.ko` 里仍有 `vm_map_ram`：来源是 `physmem_osmem_linux.c:1560` 的 `_ApplyCacheMaintenance()`，**stock DDK 1.13 同样是裸 `vm_map_ram`**（TI 源码 1504 行）。它只用于对 cached 页做 flush，且 flush 需要走缓存，行为正确。不要把它当未修复点。
2. `dma_support.c` 的 prot 在 ARM64 上固定 `pgprot_writecombine(PAGE_KERNEL)`（stock 如此），所以此类 DMA 映射是 WC 而不是 NC；对 MIPS 固件足够了，但别在文档里写成 "uncached"。

### P4 平台层小细节
- `pvr_mtk_clk_enable()` 在时钟已开启时仍会重写 `MFG_CFG 0x8 = 0xf` 并重跑 APM 序列；由 `PostPowerState` 每次 ON 触发。重复写 CLR 幂等，但若 `pvr_apm==1`，每次上电都会再打一次 `0x24` 脉冲，属于会扰动硬件的操作，建议只在 `!mfg_clk_enabled` 时执行。
- `pvr_rate_mhz` 默认 390 MHz，注释里"FW runtime cfg 说 400"已被删掉；如果后续排查频率相关问题，这个默认值是个隐藏变量。
- `MTKRGXDeviceDeInit()` 里 `pm_runtime_put_sync()` 与 probe 的 `get_sync()` 成对，但没有 `pm_runtime_disable()` 之后的 `devm` 资源清理问题（devm 处理），可以接受。

## 3. 未能验证的部分（UNVERIFIED）

- "MIPS 0.89 ms 回写 sPowerSync=1、18 ms 走完 KCCB 握手"：需要设备侧 dmesg/寄存器快照，本次只在源码与 .ko 层面核对。
- "零超时零报错"：同上。

## 4. 与 TI stock 的文本 diff 不可用的原因（FACT）

两边是不同 DDK 变体：本机 `PVRVERSION_STRING = "Rogue_DDK_Android rogueddk 1.13@5776728"`，TI 为 `"Rogue_DDK_Linux_WS ..."`；`generated/` 与大部分源文件排版/配置不同（逐文件 diff 动辄 2000+ 行，纯噪声）。因此本次对比用"语义 + 符号 + 编译产物"三种手段，而不是文本 diff。
