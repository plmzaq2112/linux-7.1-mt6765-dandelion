# 【求助】红米 9A（MT6762G）PowerVR GE8320 主线 7.1 移植：固件不回执 POW，渲染节点能开了但卡在最后一步

设备：**红米 9A（dandelion，MT6762G，PowerVR GE8320，BVNC 22.87.104.18）**
内核：主线 **7.1.0**（arm64）+ 厂商 PowerVR DDK **1.13（ED5776728）**，用户态 Alpine。

## 目前状态

✅ MIPS 固件能启动（空闲态 `EXC_STATUS=0x20`，与原厂一致）
✅ KCCB 正常（72 字节命令、128 槽），固件会消费命令
✅ POW 请求会改变 `ePowState`（ON → IDLE → FORCED_IDLE，POW_OFF → OFF）
✅ `/dev/dri/renderD129` 已能**成功 open**（靠一组诊断绕过）
❌ 固件**从不写** power-sync prim（`sPowerSync`），也从不写 KCCB 返回槽

## 已经排除的方向

- 命令 ABI（实测 72 B、`uCmdData` 偏移 8、POW 负载 8 B）
- GPU 页表 / 物理地址 / 缓存属性（PTE 审计）
- 主机 POW 流程（与 vendor 4.19 DDK 逐行一致，只多了诊断）
- MTCMOS（三个 MFG 域本来就已经上电，vendor 序列是空操作）
- 固件配置（与原厂正常 dump 完全一致：`cfg=0x00020030`、OS flags `0x7`、PM latency 3 ms、HWR OK）
- 固件/DDK 版本错配（原厂 `rgx.sh` md5 一致，DDK 1.13 对应 4.19.127 基线）
- FW trace（量产固件不输出，原厂 dump 也是 "log type: none"）

另一个怪现象：POW 处理是**间歇性**的——有时 30–90 秒后响应，有时完全不理直到超时。

## 目前能用的诊断配置

```
insmod pvrsrvkm.ko pvr_apm=2 pvr_os_active=1 pvr_no_sync=1 pvr_pow_off=1
```

`pvr_apm=2` 只写 APM dust 寄存器；`pvr_os_active=1` 强制 OS 状态 ACTIVE；
`pvr_pow_off=1` 用 POW_OFF 代替 FORCED_IDLE；`pvr_no_sync=1` 把永不写入的 prim 超时当作完成。

## 想请教的问题

1. Rogue 固件为什么会在执行 POW、更新 `ePowState` 之后，不写 `sPowerSync`（也不写返回槽）？
   固件电源状态机里是什么条件在控制这次写入？
2. 会不会是 MTK 的 RascalDust APM 路径（`INICFG_POW_RASCALDUST`）卡住了完成分支？
3. 原厂 4.19 驱动是否还有别的“主机可见完成信号”是我没发现的？

内核源码 + 说明 + 补丁（同一个仓库，分支 `dandelion-gpu-7.1`）：
**https://github.com/plmzaq2112/linux-7.1-mt6765-dandelion/tree/dandelion-gpu-7.1**
（说明文档在仓库内的 `gpu-bringup/README.md`）

全部是实验性内容，绕过逻辑会跳过驱动要求的固件握手，风险自负。
