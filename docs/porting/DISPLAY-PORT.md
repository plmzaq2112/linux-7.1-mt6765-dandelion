# DISPLAY-PORT.md — MT6765（dandelion）主線显示移植

> 状态真相源。最后更新：2026-11-19（r11 之后）。
> 相关：`logs/device/recovery-pstore-2026-11-19/FINDINGS.md` §11，内核提交 `b547a60ff`。

## 0. 目标

在主线 7.1 上做出 `/dev/dri/card0`（mediatek）+ 面板点亮 + 触摸，
之后才能上任意合成器（X11 / wlroots+pixman / Phosh / Plasma Mobile）。

## 1. 现状（FACT）

| 项 | 状态 |
|---|---|
| `mtk-mmsys` 绑定 14000000 | ✅（r10 起） |
| `mediatek-drm` 设备创建、组件绑定、`/dev/dri/card0` | ✅ |
| DRM fbdev 注册（`mediatekdrmfb`） | ✅ |
| DSI 时钟：pixelclock 87.9 MHz / 4 lane / 527.4 Mbps | ✅ 设置成功（`hs_clk actual=527400000`） |
| PHY `power_on` | ✅ 无报错 |
| **DSI CMD_DONE** | ❌ 超时（`Wait DSI IRQ(0x00000002)`，面板 init `-62`） |
| 系统稳定性 | ❌ r10：init 卡 SD；r11：fb0 后整机挂死，看门狗重启 |

## 2. 已做的关键修复

### 2.1 mmsys 被时钟驱动抢走（根因）
- `clk-mt6765-mm.c` 老式 `of_match = "mediatek,mt6765-mmsys"`，链接顺序在 `drivers/soc` 之前
- 结果 `mtk-mmsys` 不绑定 → 不创建 `mediatek-drm` 子设备 → DRM 从未 probe
- 修法：改成 mt8183 同款 `mtk_clk_pdev_probe` + `platform_device_id`（`clk-mt6765-mm`）
- 验证：`mediatek-drm mediatek-drm.3.auto: bound ...` 全部组件 + `[drm] Initialized mediatek`

### 2.2 面板驱动（新）
`drivers/gpu/drm/panel/panel-fitipower-ft8006s.c`
- 720×1600、4 lane、RGB888、video + sync pulse
- hsync 16 / hbp 45 / hfp 48；vsync 8 / vbp 45 / vfp 115 → 87.9 MHz
- init 序列/复位时序来自厂商 4.19：`drivers/misc/mediatek/lcm/ft8006s_vdo_hdp_boe_helitai/`
- GPIO：reset / enable / biasp / biasn / backlight（DT 属性名已对上）

## 3. 未解问题与假设

### 3.1 DSI CMD_DONE 超时（HYPOTHESIS：mt6765 MIPI-TX ≠ mt8183）
- 主线 `drivers/phy/mediatek/phy-mtk-mipi-dsi.c` 只有 mt8183 数据；DTS 靠 `mediatek,mt8183-mipi-tx` 兼容串绑定
- 频率名义上设置成功（`actual=527400000`），但 mt6765 的 PLL 分频/寄存器布局可能不同 → PLL 实际没锁/输出异常
- 待办：从厂商 4.19（`video/mt6765/dispsys/ddp_dsi.c`、`ddp_reg_mipi.h`、`disp_helper.c`）提取 mt6765 的 MIPI-TX 配置，逐项对比

### 3.2 系统挂死
- r10：显示起来后 SD 控制器超时（`msdc_request_timeout cmd=17/13`），init 卡在 SD mount
- r11：fb0 注册后内核直接挂死（无 `Run /init`）
- 可能原因：SMI/IOMMU 显示通路未就绪导致总线卡死；或 DSI PHY 扰动共享 PLL
- 待办：把 bring-up 改成安全模式（不自动 commit / 不接管 console），系统始终能起来

## 4. 下一步计划

1. **安全模式**：关闭 DRM fbdev 自动接管（或面板 prepare 可控），保证 SSH/串口始终可用
2. **mt6765 MIPI-TX 数据**：从 4.19 源码提取 → 补/改 phy 驱动或加 mt6765 data
3. DSI 能发命令后：RDMA/OVL 扫描输出验证 → 面板 init → 背光（PWM/DCS）
4. 触摸：`drivers/input/touchscreen/ft8006s_spi`（Focaltech TDDI，SPI）
5. 偏压：TPS65132（I2C，厂商写 0x00/0x01=0x13）

## 5. 镜像记录

| 镜像 | 说明 | 结果 |
|---|---|---|
| r9 | 可用的 Alpine（p41 根） | ✅ 基线，回滚用 |
| r10 | +mmsys 修复 +面板驱动 | DRM 起来；DSI 超时；init 卡 SD；看门狗重启 |
| r11 | r10 + init 去掉 SD 检查 + DSI 仪表 | DSI 参数确认；fb0 后整机挂死 |

回滚：`adb push boot-7.1-dandelion-busybox-r9.img` → `dd ... of=/dev/block/by-name/boot`

## 6. r12/r13 进展（2026-11-19 20:0x–20:2x）

### 6.1 DSI 通路验证通过（FACT）
- r12 关掉 `DRM_FBDEV_EMULATION`（安全模式），系统稳定；`/dev/dri/card1` = mediatek
- 自写静态 `kms-test`（裸 DRM ioctl）手动 `SETCRTC` 成功：
  `mtk-dsi poweron pixelclock=87900000 data_rate=527400000`，无超时、无挂死
  `card1-DSI-1: connected / enabled`
- 结论：**主线 DSI + 面板初始化链路可用**；之前失败是开机早期（~1.3 s）做 modeset 的时序问题

### 6.2 面板复位极性（FACT，已修）
- `/sys/kernel/debug/gpio`: `gpio-45 (reset) out lo ACTIVE LOW` → 面板被一直按在复位
- 修法：assert（写逻辑 1，物理低）→ 上 biasp/biasn → release（写 0）→ 延时 35 ms → init 序列

### 6.3 背光与 MT6370（FACT，当前阻塞）
- 背光是 MT6370 PMIC 的 WLED 驱动；已在内核 DTB 增加子节点：
  `backlight { compatible = "mediatek,mt6370-backlight"; max-brightness = <0x7ff>; default-brightness = <0x400>; }`
- 但 **MT6370 的 I2C 完全不通**：
  - `mt6370 5-0034: error -ENXIO: Failed to check vendor info`
  - `i2cdetect -y 5` 全空；`i2ctransfer w1@0x34` NACK
  - 5-001a / 5-0034 / 5-006b 三个设备全部无驱动
  - 引脚 48/49 已 mux func1 并被 `11016000.i2c` 占用（pinctrl 正常）
- 连带影响：DSV 偏压（面板 AVDD/AVEE）、充电、ADC、`usb:connector` deferred 全部卡住

### 6.4 下一步
1. **修 I2C5**：对照厂商 4.19（`i2c5: scl-gpio-id=48`、`clock-div=5`、`CLK_IFR_I2C_AP`）核对时钟/时序/引脚功能
2. 背光：`/sys/class/backlight/mt6370-backlight` 出现后写亮度
3. 触摸：`ft8006s_spi`（Focaltech TDDI，SPI）
4. 合成器：wlroots + pixman 软渲染

## 7. I2C5 / MT6370 深挖（2026-11-19 20:3x）

### 7.1 已排除（FACT）
- 引脚 48/49 的 func1 就是 **SCL5/SDA5**（`pinctrl-mtk-mt6765.h`: `MTK_FUNCTION(1, "SCL5"/"SDA5")`）
- 时钟 ID 正确：`CLK_IFR_I2C_AP=4`、`CLK_IFR_AP_DMA=28`，与厂商 `i2c5` 节点一致
- 控制器 probe 正常，pinctrl debugfs 显示 48/49 被 `11016000.i2c` 占用
- 驱动返回 `-ENXIO` 对应 **ACK error**（不是超时）→ 总线在动，是**从设备不应答**
- 全地址扫描 0x08–0x77（`i2ctransfer w1`）**无一 ACK**
- 厂商 DTB 确认 `i2c5@11016000`、`scl-gpio-id=0x30`、`sda-gpio-id=0x31`，总线和地址没错

### 7.2 两种可能
1. MT6370 的 I2C 接口未就绪（供电/复位/使能未配置；厂商 DTS 的 `core { mrstb_en; }` 未移植）
2. 板上 PMIC 实际挂在别的 I2C 控制器（m3 DTS 是从其它参考板改的，未验证）

### 7.3 下一步实验
- 把 i2c0..i2c6 全部 `status = "okay"` 编进 DTB，开机逐个总线扫描 0x34；有 ACK 就说明总线猜错了
- 若都不通：查 MT6370 的供电/使能（厂商 DTS `mt6370_pmu_dts` 的 `mrstb_en`、`int_wdt` 等），或补厂商的 pad 电气配置（`eh_cfg/pu_cfg/rsel_cfg`）

## 8. 点亮里程碑（2026-11-19 21:3x）

### 8.1 结果（FACT）
- 背光：**不是 MT6370**，是 MTK disp PWM（厂商 `custom_common.dtsi` 的 `mediatek,lcd-backlight`，`led_mode=4` PWM 模式）
  - `pwm@1100e000` 加 `mediatek,mt8183-disp-pwm` 回退并 enable，加标准 `pwm-backlight` 节点（`pwms = <&disp_pwm 0 100000>`，10 kHz，不闪）
  - `/sys/class/backlight/backlight` 出现，max=11
- 面板驱动 probe 成功（背光 GPIO 被 pwm-backlight 占用，改为忽略 -EBUSY）
- 手动 `kms-test` → `SETCRTC ok`，DSI poweron 正常，无超时/无挂死，**屏幕出现红色画面**
- 关闭 kms-test 后画面消失：最后一个 DRM master fd 关闭 → 内核禁用 CRTC（预期行为）

### 8.2 结论
主线 7.1 在这台机器上已经可以完整驱动屏幕：
`mmsys/clk → mediatek-drm → RDMA/OVL → DSI(4 lane, 527.4 Mbps) → FT8006S + PWM 背光`

### 8.3 下一步
1. 常驻显示：起一个合成器（先 wlroots+pixman 软渲染）或最小 KMS 守护进程占住 master
2. 触摸：厂商 `drivers/input/touchscreen/ft8006s_spi`（Focaltech TDDI，SPI）+ `touchscreen.dtsi` 的 SPI/中断/复位配置
3. 之后才是 GUI 选型（phosh/plasma-mobile/sway 等）

## 9. 开机集成（2026-11-19 21:4x）

- `/usr/local/bin/kms-loop`（静态 ARM64）：KMS 常驻播放器，支持 `KMSA` 动画格式（720x1600 RGB565 + RLE，PC 端 `convert-gif.py` 转换，保留每帧延时）
- `/usr/local/bin/display-start.sh`：**延时 15 s** 再启动（早期 modeset 会挂 DSI），失败自动重试
- `/etc/init.d/rcS`：启动时拉起 display-start（后台）、SD 卡自动挂载到 `/mnt/sd`
- 验证：重启后 16.9 s DSI poweron 成功，屏幕自动播放测试动画

## 10. 系统体检（FACT）

| 项 | 状态 |
|---|---|
| CPU 频率调节 | ❌ 无 `/sys/devices/system/cpu/cpu0/cpufreq`（DTS 缺 OPP 表/cpu-supply） |
| 电池 / 充电 | ❌ 无 `/sys/class/power_supply`（mt6357 gauge/charger 未接；MT6370 无响应） |
| 温度 | ❌ 无 `/sys/class/thermal` |
| 内存 | ✅ 3.6 GiB |
| 显示 | ✅ DRM/DSI/面板/PWM 背光 |
| 触摸 | ❌ Focaltech SPI TDDI 未移植 |
