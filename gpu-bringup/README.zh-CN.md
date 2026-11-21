# 红米 9A（MT6762G）PowerVR GE8320 主线 7.1 移植：求助帖

**一句话**：我把厂商 PowerVR DDK 1.13（Rogue，BVNC 22.87.104.18）移植到了主线 7.1，
MIPS 固件能启动、KCCB 能用、电源请求会被执行，`/dev/dri/renderD129` 现在**能成功 open**（靠一组受控绕过）。
**还差最后一环**：固件从不写 power-sync prim（也不写 KCCB 返回槽），而且 POW 命令是**间歇性**处理的。
想找懂 PowerVR Rogue 固件 / MTK MTS 的朋友一起看看。

---

## 一、硬件与软件

| 项 | 值 |
|---|---|
| 设备 | 红米 9A（dandelion），MT6762G |
| GPU | PowerVR GE8320（Rogue），BVNC **22.87.104.18** |
| GPU 寄存器 | `0x13000000` + `0x80000` |
| MFG 时钟控制 | `0x13ffe000` |
| SPM | `0x10006000` |
| 中断 | GIC SPI 259（LEVEL_LOW） |
| 内核 | 主线 **7.1.0**（arm64），Alpine 用户态 |
| DDK | Imagination **1.13（ED5776728）**，out-of-tree 放在 `drivers/misc/pvr/ddk` |
| 固件 | 原厂 `rgx.sh`，309200 字节，md5 `6456299eddd62b1834f71e81b4d6bb67` |
| 原厂基线 | vendor 4.19.127 + DDK 1.13（用 vendor 模块 vermagic 核实） |

固件与 DDK 是同一代（都来自原厂 4.19.127），**不存在版本错配**。

## 二、已经可用的部分（实机验证）

- GPU 寄存器、`CORE_ID=0x08470000`、`REVISION=0x00680012`
- MFG 时钟（mfg / mfgpll）、时钟门控、MFG / MFG_CORE0 / MFG_ASYNC 三个电源域
- MIPS 固件启动：`bFirmwareStarted`、`EXC_STATUS=0x20`（与原厂空闲态一致）
- FW 连接：`FW_ACTIVE` / `OS_ACTIVE`，KCCB 72 字节命令、128 槽
- 命令提交：固件会消费（`r` 前进、`kcmds` 递增）
- POW 请求：固件会改 `ePowState`（ON → IDLE → FORCED_IDLE，POW_OFF → OFF）
- **`/dev/dri/renderD129` 能成功 open**（下面这组参数）

## 三、卡住的地方

固件**从不写 power-sync prim**（`RGXFWIF_OSDATA::sPowerSync`，FW VA `0xc0019000`），
也**从不写 KCCB 返回槽**。已经排除：

- 命令 ABI（72 B、`uCmdData` 偏移 8、POW 负载 8 B，全部实测一致）
- GPU 页表 / 物理页 / 缓存属性（PTE 审计 + 主机 PA 一致）
- `MTS_SCHEDULE` 门铃的值与写序列（与 vendor 一致）
- 主机侧 `RGXForcedIdleRequest`（与 vendor 4.19 DDK 逐行一致，只多了诊断）
- MTCMOS（三个域本来就已上电，显式 vendor 序列是空操作）
- 固件配置字段（与正常开机的原厂 dump 完全一致：`cfg=0x00020030`、OS flags `0x7`、PM latency 3 ms、HWR OK）
- FW trace（量产固件不输出，原厂 dump 也是 “log type: none”）

另外：POW 命令处理是**间歇性**的——有时 30–90 秒后处理并切状态，有时完全不理直到超时。

中断路径另有一个独立 bug（全程只来 1 次中断；固件是“先发中断、后写计数”，电平中断又不会重来），
已经用补丁绕过。

## 四、目前可用的组合（open 成功）

```
insmod pvrsrvkm.ko pvr_apm=2 pvr_os_active=1 pvr_no_sync=1 pvr_pow_off=1
```

- `pvr_apm=2`：只写 MTK APM dust 寄存器 `0x504–0x528`，跳过会掉 MFG_CORE0 的 `0x24` 序列
- `pvr_os_active=1`：POW 前把 OS 连接状态强制为 ACTIVE
- `pvr_pow_off=1`：用 `POW_OFF_REQ` 代替 `FORCED_IDLE_REQ`
- `pvr_no_sync=1`：prim 永远不写，把超时当作完成

这套能让 `open` 成功、驱动稳定运行，但它只是**诊断用绕过**，不是合格的上游实现。

## 五、希望得到帮助的点

1. **Rogue 固件的电源状态机**：为什么固件执行了 POW、改了 `ePowState`，却不更新 `sPowerSync` / 返回槽？
2. **MTK MTS / APM 的交互**：`INICFG_POW_RASCALDUST` 这条 APM 路径是否会卡住固件的完成分支？
   有 vendor `ged` / `gpufreq` 经验的朋友欢迎指点。
3. **用户态**：vendor 内核驱动没有可用的 Linux 用户态（原厂 UM 库是 bionic；
   Mesa 的 `powervr` 驱动配的是上游 `drm/imagination`，不是这套驱动）。求最小验证思路。

## 六、仓库内容

```
docs/STATUS.md        详细技术状态
docs/TIMELINE.md      按时间线的实验记录（只写事实）
patches/              相对 vendor DDK 1.13 的补丁
logs/open-ok.txt      一次成功 open 的内核日志
artifacts/            里程碑用的 pvrsrvkm.ko
```

## 七、免责声明

全部是实验性内容。绕过逻辑会跳过驱动本来要求的固件握手，**风险自负**，不保证适用于其它机型。

## 八、许可

补丁沿用厂商 DDK 源码的许可（MIT / GPLv2 双许可），新增代码为 GPL-2.0；
日志与文档采用 CC BY-SA 4.0。
