# dandelion 驱动状态（2026-11-22）

> 2026-11-24 更新：GPU（含 Phosh 合成）、听筒/外放音频已工作；最新状态与下一步见 `docs/STATUS.md`。
> 本页保留为 11-22 的历史快照。

内核：`7.1.0-mt6765+ #13`（Ubuntu 24.04 + Phosh，p41）
数据来源：`/sys/class/*`、`/proc/interrupts`、`dmesg`、`/proc/config.gz`

## 可用（已验证）

| 功能 | 驱动 / 设备 | 证据 |
|---|---|---|
| 显示面板 720x1600 | `mediatek-drm`（card1）+ `mtk-dsi` | `card1-DSI-1: connected`，modes `720x1600`，ovl IRQ 183/184 活跃 |
| 背光 | `pwm-backlight` | `/sys/class/backlight/backlight` |
| 触摸 | `focaltech_ts`（模块） | IRQ 16 `fts_ts`，`/dev/input/event2` |
| 音量键 | `mt6779-keypad` | IRQ 193，KEY_VOLUMEUP/DOWN 正常 |
| 电源键 | `mtk-pmic-keys` | IRQ 187/189（press/release），KEY_POWER 正常 |
| eMMC 58.2G | `mtk-msdc`（mmc0） | `mmcblk0` HS400，根文件系统 |
| microSD 7.44G | `mtk-msdc`（mmc1） | `mmcblk1` SDHC |
| USB gadget（串口/网络） | `musb-hdrc` + configfs | `ttyGS0`、`usb0`（169.254.195.201） |
| RTC | `mt6397-rtc` | `rtc0` |
| 看门狗 | `mtk-wdt` | `watchdog0/1` |
| PMIC / 稳压器 | `mt6357`（pwrap） | 各 regulator 正常注册 |
| I2C / SPI | `i2c-mt65xx` / `spi-mt65xx` | `i2c-0..6`、`spi3.0`（触摸） |
| 定时器 / 中断 / CMDQ | `arch_timer`、GICv3、`mtk-cmdq` | IRQ 11 / 176 活跃 |
| 软件渲染 | `vgem` + Mesa llvmpipe | `renderD128` 属于 vgem；phoc 使用 `WLR_RENDERER_ALLOW_SOFTWARE=1` |

## 部分可用 / 未验证

| 功能 | 状态 | 证据 |
|---|---|---|
| USB Host / OTG | 延迟探测 | `11200000.usb:connector` deferred：缺 `usb-otg-vbus-regulator` |
| 充电状态 / 电量 | 硬件在充电，系统无 `power_supply` | `mt6370 ... Failed to check vendor info`；`switching_charger@6b` 注册失败 |
| 蓝牙 | 协议栈在，无 HCI 设备 | `/sys/class/bluetooth` 为空；无芯片驱动绑定 |
| 温度传感器 | thermal 核心在，无 zone | `/sys/class/thermal` 为空 |
| 显示稳定性 | 出现过一次 CMDQ 超时 | `mtk_crtc 0 CMDQ execute command timeout!`（未复现） |

## 不可用

| 功能 | 原因 | 证据 |
|---|---|---|
| GPU 加速 | `CONFIG_DRM_PVR_LEGACY=m`，但 `/lib/modules` 只有 `focaltech_ts.ko`；当前用 llvmpipe | `renderD128` 是 vgem（faux_driver） |
| 音频 | `mt6357-sound: Failed to locate of_node [id: -1]` | 无 `/sys/class/sound`，`/proc/asound/cards` 为空 |
| WiFi | 无 `wlan` 接口、无 SDIO 设备、无 MT76 绑定 | `ip link` 只有 lo/sit0/usb0；`/sys/bus/sdio/devices` 空 |
| 摄像头 | i2c 客户端注册失败（地址冲突/硬件缺失） | `camera_main_backup@20`、`camera_sub_backup@3f` 注册失败 |
| 传感器（加速度/光线/距离） | 无驱动、无 input 设备 | `input0/1/2` 仅为 keypad/pmic-keys/fts_ts |
| 振动马达 | 无驱动 | 无相关 sysfs/input |
| 调制解调器（通话/移动数据） | 无驱动 | 无相关设备 |
| 指纹 | 无驱动 | 无相关设备 |

## 备注

- 闪烁/黑屏类问题多半与 **GPU/软件渲染** 或 **挂起** 有关，挂起已禁用。
- WiFi/蓝牙/音频/摄像头属于需要在主线内核补驱动或移植厂商驱动的部分，不是配置问题。
