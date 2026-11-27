# 项目状态（2026-11-26）

基线：内核 `7.1.0-mt6765+ #34`；Ubuntu 24.04 + Phosh（p41）；PowerVR DDK `1.13@5776728`。
当前 boot：`boot-stable17-panelbl2047.img`（#34 + USB connector 修复 + 面板 DSI 0x51 亮度，11 位 / 2047 级）。
数据来源：设备 `/sys`、`/proc`、`dmesg`、`journalctl`，以及 `docs/porting/`、`docs/porting/notes/`。
补充：Mesa Vulkan / Wayland 合成器状态见 `docs/porting/COMPOSITOR-PORT.md`、`docs/porting/PROJECT-ARCHIVE.md`。

## 已工作（FACT）

| 功能 | 驱动 / 设备 | 证据 |
|---|---|---|
| 显示 720x1600 | `mediatek-drm` + `mtk-dsi` | `card1-DSI-1: connected` |
| 屏幕亮度 / 背光 | panel DSI `0x51`（`panel-backlight`） | `/sys/class/backlight/panel-backlight`，11 位，`max_brightness=2047`，GPIO154 仅作使能；PWM/MT6370 实测无效，详见 `docs/porting/notes/BACKLIGHT.md` |
| 触摸 | `focaltech_ts` | `fts_ts`，`event2` |
| 音量键 / 电源键 | `mt6779-keypad` / `mtk-pmic-keys` | `event0` / `event1` |
| eMMC + microSD | `mtk-msdc` | `mmc0`、`mmc1`、`mmcblk0/1` |
| USB gadget（NCM/串口） | `musb-hdrc` + configfs | `usb0`、`ttyGS0` |
| RTC / 看门狗 | `mt6397-rtc` / `mtk-wdt` | `rtc0`、`watchdog0/1` |
| PMIC / 稳压器 / I2C / SPI | `mt6357`、`i2c-mt65xx`、`spi-mt65xx` | 各 regulator、`i2c-0..6` |
| 充电 / 电池（基础） | `bq256xx-charger`、`adc-battery` | `bq256xx-charger: online=1 status=Full`；`adc-battery: Charging 100%` |
| GPU 3D（vendor bridge） | `pvrsrvkm`（DDK 1.13） + vendor GLES bridge | `card2`、`renderD129`；64 位 EGL/GLES 3.2 渲染通过 |
| Mesa Vulkan（PowerVR） | Mesa `libvulkan_powervr_mesa.so`（GE8320/1.13） | clear/triangle/quad/texture/depth/blend/geom 回归通过；`vk_info` 识别 GE8320（FACT，见 PROJECT-ARCHIVE） |
| 零拷贝合成 | `vk_kms2`（DRM dumb + Vulkan + KMS） | 720×1600 @ 58.4 fps，vsync，零 CPU 拷贝（FACT） |
| Wayland 合成器 | `vk_wl` + `wl_test_client` | xdg-shell/shm/dmabuf v3/pointer+keyboard；damage/idle；uinput 键盘端到端验证（FACT，见 COMPOSITOR-PORT） |
| Phosh GPU 合成 | `phoc` + `libGLESv2_mtk` | `WLR_RENDERER=gles2`，phoc 映射 `libGLESv2_mtk.so`、pvr-bridge |
| 音频（听筒） | `mt6765-mt6357` + `mt6357` | 干净播放，pop 已修 |
| 音频（外放） | machine driver DAPM + extamp GPIO153 | 播放前 GPIO 低、播放中高、停止后低；25% 软件音量合适 |
| 振动马达 | `regulator-vibrator`（移植 vendor 驱动）+ MT6357 `vibr` LDO | `/sys/class/leds/vibrator/{duration,activate}`，400ms×3 用户确认有振感；开机自动加载，`input` 组可写 |

## 部分可用 / 待验证

| 功能 | 状态 | 证据 / 阻塞点 |
|---|---|---|
| USB Host / OTG | connector 已正常 probe；Host VBUS 待补 | 已从 DTB 移除失效的 `vbus-supply`（`boot-stable9-usbotg.img`）；role=device；Host 需要 bq256xx OTG regulator |
| 充电细节 | 基础状态有，限流/温控未验证 | `bq256xx-battery` 状态为空；充电电流/电压未核对 |
| 热管理 | 无 thermal zone | `/sys/class/thermal` 下只有 cooling_device |
| GPU 稳定性 | 有日志告警 | `RGXAlignmentCheck: size/offset mismatch [21] UM(352) vs FW(320)`；暂未观察到崩溃 |
| 音频收尾 | 结束 pop 未最终确认；UCM2 未做；mic 未测 | `docs/porting/notes/AUDIO.md` |
| 挂起/唤醒 | `mem_sleep=deep` 可用，未验证 | `/sys/power/mem_sleep`；GPU 刚稳定，适合做 PM 审计 |
| Mesa 3D 性能 | 可用但未追平厂商 | 720×1600 全屏 3.05 ms vs 厂商 1.96 ms（FACT）；差距来源未定位（HYPOTHESIS） |
| Wayland 客户端兼容性 | 协议子集可用 | shm/dmabuf/keyboard 已验证；未跑真实 foot/GTK 客户端；无 popup/data_device/tiled modifier（FACT） |

## 不可用（需要驱动）

| 功能 | 原因 |
|---|---|
| WiFi | **SoC 内集成 CONNAC（AXI HIF）**，不是 SDIO；vendor `gen4m` 约 149 个 C 文件 / 29.6 万行，主线无对应驱动 | `CONFIG_MTK_COMBO_CHIP_CONSYS_6765=y`、`mediatek,wifi` @0x18000000、`os/linux/hif/axi` |
| 蓝牙 | 同一 combo，vendor BT 栈；被 WiFi 移植阻塞 | — |
| 摄像头 | vendor 驱动，i2c 注册失败 |
| 调制解调器 | 无驱动 |
| 传感器（加速度/光感/距离） | 硬件存在，主线下未接管 | 原厂走 SCP hub；AP 侧 i2c 0/1 全 NAK、2/3/4/6 超时、5 只有充电器；详见 `docs/porting/notes/SENSORS.md` |
| 环境光 / 自动亮度 | `alsd` + 0x47 ALS（位操作 i2c1） | 光感位于 i2c1 引脚（SDA 81/SCL 84），400kHz 控制器不 ACK，50kHz i2c-gpio 可读；`alsd.service` 读 0x14 通道走 gsd D-Bus 调亮度；详见 `docs/porting/notes/SENSORS.md` |
| 指纹 / NFC | 硬件无或未使用 |

## 下一步建议（按性价比）

1. **Wayland 真实客户端验证**：跑 foot/GTK 等真实客户端，验证 keyboard、dma-buf、damage、focus；缺客户端时先交叉编译最小客户端。
2. **USB Host VBUS（快赢，进行中）**：connector deferred 已修（`boot-stable9-usbotg.img`）；下一步在 bq256xx 里加 OTG regulator 并让 connector 引用，才能给 U 盘/键鼠供电。
3. **热管理 / 挂起唤醒**：加 MT6765 thermal zone；在 GPU/显示/音频已工作的基础上做 PM 审计。
4. **音频收尾**：结束 pop 顺序、UCM2 profile、麦克风验证。
5. **GPU 性能**：定位 Mesa 3.05 ms vs 厂商 1.96 ms 的剩余差距。
6. **WiFi/BT（长期）**：需移植 vendor gen4m/HIF（约 29.6 万行）与 conninfra，单独立长期分支评估，不建议短期投入。

## 已知问题

- `RGXAlignmentCheck` 的 UM/FW 结构体尺寸告警（`[21]`，352 vs 320）：目前只出现在日志，可能与 64 位用户态兼容层有关，需观察。
- 外放结束噪声：已改为 PCM shutdown 先关功放，待最终听感确认。
