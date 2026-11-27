# 传感器（光感 / 距离 / 加速度）

最后更新：2026-11-24

## 结论摘要

- 硬件存在且原厂可用：用户确认原厂 MIUI 自动亮度有效（FACT，用户实测）
- 原厂实现走 **SCP 传感器 hub**，AP 侧设备树里**没有任何传感器节点**（FACT）
- 主线下目前**无法接管**：AP 侧 7 条 i2c 里没有任何一条能应答传感器地址（FACT，见下）

## 证据

### 1. 芯片型号来自 SCP 固件字符串（FACT）

`/dev/disk/by-partlabel/scp2`（1 MiB）里可见：

```
stk3x3x / stk3x3xInit              -> 光感+距离（Sensortek STK3x3x 系列）
alsps_separate / als: enable done
sc7a20 / sc7a20InitReg             -> 加速度（Silan SC7A20）
bma2x2Init                         -> 备选加速度（Bosch BMA2x2）
Accelerometer / ALS / Proximity
alsPs: i2c error / spi error
```

vendor 内核里只有 `sensors-1.0/alsps/alspshub`、`accelerometer/accelhub`——即 **hub 模式**，
具体芯片和 i2c 参数在 SCP 固件里，不在 AP 设备树（FACT：`grep i2c_addr arch/arm64/boot/dts` 无结果）。

### 2. AP 侧 i2c 实测（FACT，内核态 `i2c_transfer` 全地址 0x08-0x77 扫描）

| 总线 | 结果 | 说明 |
|---|---|---|
| i2c-0 (11007000) | 112 个地址全部 NAK | 总线正常，无器件 |
| i2c-1 (11008000) | 112 个地址全部 NAK | 总线正常，无器件 |
| i2c-3 (1100f000) | 112 个地址全部 `-110`（超时） | 线路被拉死/无上拉 |
| i2c-5 (11016000) | 只有 0x6b ACK（bq256xx 充电器） | 正常 |
| i2c-2 / i2c-4 / i2c-6 | 112 个地址全部 `-110` | 线路被拉死/无上拉 |

全部 PMIC LDO 上电后（`rail_en2.ko names=vcn18,vcn28,vldo28,vcamio,vcama,vcamd,vfe28,vcn33-bt,vcn33-wifi,vefuse,vrf18,vsim1,vsim2,vmc,vmch`，15/15 ret=0）结果不变。

### 3. 已排除的软件原因（FACT）

- i2c 时钟引用正确：DTB `clocks = <0x16 0x04 0x16 0x1c>`，`0x16` 是 infracfg，ID 4/28 分别是
  `CLK_IFR_I2C_AP` / `CLK_IFR_AP_DMA`
- 引脚复用正确：`pin 50/51 -> 1100f000.i2c func1` 等，pinfunc 里 func1 就是 `SCL3/SDA3`
- 不是驱动没绑定：i2c 控制器都在（`/sys/class/i2c-dev/i2c-0..6`）

### 4. 与 SCP 共享总线的线索（HYPOTHESIS）

时钟树里有 `CLK_IFR_I2C1_ARBITER`、`CLK_IFR_I2C2_ARBITER`、`CLK_IFR_I2C5_ARBITER`、
`CLK_IFR_I2C2_IMM`、`CLK_IFR_I2C_SSPM`；主线 `i2c-mt65xx` 支持可选的 `"arb"` 时钟，
但我们的 DTB 里 7 条 i2c 全部只有 `main`/`dma`，没有 `arb`。

推测：传感器挂在 SCP 与 AP 共享的 i2c（i2c-1/2/5 之一）上；没有 arbiter 时钟、
或者 SCP 侧还没把总线交出来时，AP 传输就会一直超时（对应 i2c-2 的 112 次 -110）。

验证方法：给 i2c-2 节点补 `clocks = <&infracfg CLK_IFR_I2C_AP>, <&infracfg CLK_IFR_AP_DMA>,
<&infracfg CLK_IFR_I2C2_ARBITER>`、`clock-names = "main","dma","arb"`，刷机后重扫 0x48/0x19。

## 驱动选择（待总线打通后）

- 光感/距离：`CONFIG_STK3310`（`drivers/iio/light/stk3310.c`，支持 stk3013/3310/3311/3335，
  i2c 地址通常 0x48）
- 加速度：`CONFIG_IIO_ST_ACCEL_3AXIS`（`silan,sc7a20` 已支持）或
  `CONFIG_BMC150_ACCEL`（`bosch,bma253`）

注意：`stk3310.c` 主线版本**不处理电源 regulator**，只做 i2c + 可选 irq；
若传感器所在的 LDO 默认关闭，需要给驱动补 `vdd`/`vddio` 或在 DTB 里给该 LDO 加 `regulator-always-on`。

## 用户态方案

设备无外网（只有 usb0 link-local，apt 依赖还是坏的），所以不装 `iio-sensor-proxy`；
计划用一个 systemd 小脚本读 `/sys/bus/iio/devices/iio:deviceX/in_illuminance_input`，
按对数曲线 + 迟滞写入 `/sys/class/backlight/panel-backlight/brightness`。

## 尚未验证（UNVERIFIED）

- 传感器具体挂在 i2c-1/2/5 哪一条、地址是多少
- 传感器供电由哪一路 LDO 提供
- SCP 固件是否在 AP 启动时把 i2c 总线"锁住"

## 关键突破：位操作（i2c-gpio）能正常访问同样两条线（FACT）

在 DTB 里把 i2c2/3/4/6 的硬件控制器 `status = "disabled"`，用同一对引脚建了 4 条
`i2c-gpio` 总线（`boot-stable20-i2cgpio.img`）后扫描结果：

| 位操作总线 | 原硬件控制器 | 扫描结果 |
|---|---|---|
| i2c-7 | i2c2 (11009000, pin 103/104) | 空；`vcamio` 上电后出现 0x54 / 0x5c（相机 eeprom） |
| i2c-8 | i2c3 (1100f000, pin 50/51) | **0x50 + 0x57 = ext buck LP4X / LP4** |
| i2c-9 | i2c4 (11011000, pin 105/106) | 空；`vcamio` 上电后出现 0x51 / 0x59（相机 eeprom） |
| i2c-10 | i2c6 (1100d000, pin 161/162) | **0x3e = LCD bias tps65132** |

结论：引脚、上拉、供电、器件全部正常，**问题出在 i2c 控制器本身**；位操作可以完全绕开。

逐路 LDO 上电（vcn18/vcn28/vldo28/vcamio/vcama/vcamd/vfe28/vcn33-bt/wifi/vefuse/vrf18/vsim1/2）
都没有出现 0x48（STK3x3x 常见地址），也没有其它疑似光感地址。

## 控制器为什么“锁死”：现有证据与假设

证据（FACT）：

- 硬件控制器对**任何**地址都超时（`-110`），但同样两条线位操作正常 → 不是线的问题
- 传输卡住期间 `DEBUGSTAT(0x11009000+0xe4) = 0x00000300` 稳定不变；空闲时所有控制器寄存器读回 0
  （外设时钟被门控）
- 主线驱动只取 `main`(CLK_IFR_I2C_AP) 和 `dma`(CLK_IFR_AP_DMA) 两个时钟，7 条总线共用；
  时钟树里另有每实例门 `ifr_i2c4`、`ifr_i2c6`、`ifr_i2c2a`、`ifr_i2c2_imm`、`ifr_i2c5a`、
  `ifr_i2c5_imm`，consumer 全是 `deviceless`（没被任何驱动持有）
- SCP 固件里有 `[I2C-SCP]` 日志和 `drivers/CM4_A/mt6765/i2c/src/i2cchre-plat.c`
  → **SCP 确实通过 AP 的 i2c 控制器访问传感器**（不是 GPIO 位操作）

假设（按可能性排序）：

1. **每实例功能时钟门未开**：`I2C_AP` 可能只是总线/PCLK 门，2/4/6 还需要各自的
   `ifr_i2c2_imm`/`ifr_i2c4`/`ifr_i2c6` 才能让传输状态机动起来。已试过 `I2C2_ARBITER`
   （无效），还没试 `I2C2_IMM` / `I2C4` / `I2C6`。
2. **SCP 仲裁未释放**：SCP 与 AP 共享总线时由 arbiter 决定谁持有。若开机时 SCP 没运行、
   总线停在“SCP 持有”，AP 可能一直等不到总线。arbiter 时钟已开过，但“所有权/释放”是
   寄存器状态，AP 侧看不到语义。
3. bus3 没有独立时钟门却也超时，说明上面的解释并不完整，可能还有寄存器配置差异。

### 2026-11-25：给 i2c2/4/6 补每实例时钟（无效）

- 假设：`CLK_IFR_I2C_AP` 只是总线门，2/4/6 还缺各自的 `ifr_i2c2_imm` / `ifr_i2c4` / `ifr_i2c6`
- 操作：i2c2 的 `arb` 槽填 `CLK_IFR_I2C2_IMM`(47)，i2c4 填 `CLK_IFR_I2C4`(38)，
  i2c6 填 `CLK_IFR_I2C6`(54)（`boot-stable21-i2cclk.img`）
- 结果：i2c-2 仍 `ack=0 nack=0 err=112`（全部超时）
- 结论：不是每实例时钟门的问题。结合 arbiter 时钟也无效，控制器"卡死"更像是
  **SCP 侧的总线/焊盘归属状态**（SCP 固件 `i2cchre-plat.c` 直接操作这些控制器），
  而不是 AP 侧的时钟或配置。要彻底确认需要 MTK i2c 寄存器手册或示波器看 SCL 波形

## 失败记录

### 2026-11-24：给 i2c1/2/5 补 arbiter 时钟（无效）

- 假设：缺 `CLK_IFR_I2Cx_ARBITER` 导致传输超时
- 操作：DTB 给 i2c@11008000/11009000/11016000 增加 `arb` 时钟（`boot-stable19-i2carb.img`）
- 结果：i2c-2 仍 112 个地址全部 `-110`
- 结论：arbiter 时钟不是原因

### 2026-11-24：按“器件未上电”排查（被推翻）

- 曾根据 DEBUGSTAT 低两位为 0 推测两条线被未上电器件钳低
- i2c-gpio 位操作在同一对线上正常通信 → 该推测推翻

## 2026-11-25：找到光感（FACT）

- 芯片在 **i2c1 引脚（GPIO81=SDA1 / GPIO84=SCL1）**、地址 **0x47**
- 硬件 i2c1 在 400 kHz 下对它 **NAK**；把同两条线切成 i2c-gpio（50 kHz）后一切正常
- 芯片 ID（0x3E）= **0x5F**，状态寄存器 0x00（写 0x02 = ALS on）、控制 0x02（0x23）、
  环境光数据在 **0x14（0..255）**，另有 0x16/0x18/0x1A 三个通道随光照变化
- 验证：纸片遮挡 / 手电筒照射都会让 0x14 明显变化（40↔180），确认是光感不是纯接近
- 注意：这颗芯片向 0x00 连续写 "standby/enable" 会把它带进“数据恒 0”的状态，
  只有彻底断电（长按电源关机）才能恢复；运行时只初始化一次

实现：

- DTB：`boot-stable22-i2c01gpio.img` 把 i2c0/i2c1 硬件控制器禁用，用 i2c-gpio 在
  同一组引脚上重建 50 kHz 总线（`i2c-7` = i2c0，`i2c-8` = i2c1）
- 模块：`i2c-algo-bit.ko` + `i2c-gpio.ko`，已装入 `/lib/modules/.../extra`，
  `/etc/modules-load.d/i2c-gpio-sensors.conf` 开机自动加载
- 权限：`/etc/udev/rules.d/99-als-i2c.rules`（i2c-8 → group i2c）,
  `/etc/udev/rules.d/99-backlight.rules`（backlight → group video）
- 用户态：`/usr/local/bin/alsd.py`（`alsd.service`，以 dandelion 用户运行，
  通过会话总线写 gsd-power 的 Brightness），源码 `tests/tools/alsd.py`
- 引导保护：`/etc/tmpfiles.d/dandelion-rootfs.conf` 每次启动重建
  `/etc/dandelion-rootfs-ok`，避免 initramfs 掉进 Alpine 救援系统导致黑屏

## 尚未解决

- **加速度计**：7 条 i2c 全扫（含位操作）都没找到 sc7a20/bma2x2 的可疑地址，
  可能在未上电的相机电源域或另有使能信号
- **接近感应**：同一颗芯片大概率有 PS 通道（reg 0x11/0x12），还没做通话贴脸灭屏
- 自动亮度策略仍在调：面板每个 0x51 写入都可能闪一下，低亮度更明显；
  目前回到用户认可的 v3（分段曲线 + 20% 迟滞 + 1%/tick 渐变），常量在
  `tests/tools/alsd.py` 顶部可调

## 失败记录（补充）

- 2026-11-25：给 i2c2/4/6 补 `I2C4`/`I2C6`/`I2C2_IMM` 时钟无效
- 2026-11-25：`base DTB` 改 i2c1 的 `clock-frequency` 无效 —— **bootloader 会把 dtbo
  合并进来并覆盖该属性**（dtbo fragment@36 固定 400 kHz），这也是必须用位操作的原因
- 2026-11-25：自动亮度初版直接写 sysfs 与 gsd 冲突（触摸后被顶回）；改为 gsd D-Bus
- 2026-11-25：20 Hz 高频写亮度会让滑块抖动/低亮度闪烁；改为慢采样+迟滞+限速
