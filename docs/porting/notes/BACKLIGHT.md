# 屏幕亮度 / 背光（Redmi 9A，FT8006S 面板）

最后更新：2026-11-24

## 结论（FACT）

屏幕亮度由 **MIPI DSI 命令 `0x51`** 控制，GPIO154 只是背光**使能开关**（高=开）。
PWM（DISP_PWM / GPIO43）和 MT6370 BLED 都不参与这块板子的实际调光。

证据：

- vendor LCM 驱动 `kernel_4.19.325_purity/drivers/misc/mediatek/lcm/ft8006s_vdo_hdp_boe_helitai/ft8006s_vdo_hdp_boe_helitai.c`
  - `lcm_setbacklight_cmdq()`（约 540 行）：`bl_level[0].para_list[0] = level; push_table(...)`，而 `bl_level[]` 的首项是 `{0x51, ...}`
  - 同一函数：`level > 0` 时 `disp_dts_gpio_select_state(DTS_GPIO_STATE_LCD_BL_OUT1)`、`level == 0` 时 `..._OUT0` → 该 GPIO 只做开关
- 运行设备 `journalctl -b`：`panel-fitipower-ft8006s ...: backlight gpio unavailable (-16)`（早期版本），说明 GPIO154 是 `backlight-gpios`
- 主线 `pwm-mtk-disp.c` 实测：`1100e000.pwm` 时钟 `disp_pwm_sel`/`ifr_disp_pwm` 已使能（26 MHz），周期 39385 ns（1024 个 26 MHz 周期），占空比随 sysfs 变化，但**屏幕亮度不动** → 这路 PWM 在本机没有接到 LED
- i2c5（`i2c@11016000`）0x34 MT6370：`NAK`，各 LDO 打开后仍 NAK → 芯片不存在/未上电；vendor DTB 里的 `mt6370-backlight` 节点对本机无效

## 11 位亮度编码（FACT，来自 vendor）

`CONFIG_BACKLIGHT_SUPPORT_2047_FEATURE=y`（`arch/arm64/configs/blossom_defconfig:132`、`stock_defconfig:1589`）。

vendor 运行时：

```c
level = level * 72 / 100;   /* UI 0..2047 -> 0..1473 */
level <<= 1;
para[0] = level >> 4;       /* bit10..3 */
para[1] = level & 0x0E;     /* bit2..0，左移 1 */
```

等价于 11 位值 `v = (b0 << 3) | (b1 >> 1)`，满幅约 1472。

主线驱动 `drivers/gpu/drm/panel/panel-fitipower-ft8006s.c` 已改成同样的 2 字节写法：

```c
ft8006s_write(ctx, 0x51, (const u8[]){val >> 3, (val & 0x07) << 1}, 2);
```

- `max_brightness`：**`0x7ff`（2047）**。实测 2047 比 1472（vendor `*72/100` 的上限）明显更亮 → 这块面板满幅是 2047，vendor 的 72% 是自我限制
- 最低限制 `0x40`（64），避免 `0x00` 全黑
- 默认 `0x400`（1024）
- 不做防抖：每次改亮度立即写一次 `0x51`（用户要求优先跟手，接受可能出现的一帧闪烁）

## 相关配置

- DTB：root `backlight`（pwm-backlight）必须 `status = "disabled"`，否则它会占用 GPIO154，panel 驱动拿不到 `backlight-gpios`（`-16`）
- 面板驱动是 built-in（`CONFIG_DRM_PANEL_FITIPOWER_FT8006S=y`），改它必须重编内核并刷 boot
- 生成的镜像：`boot-stable14-panelbl2.img`（8 位）、`boot-stable16-panelbl11-nodb.img`（11 位，1472 上限）、`boot-stable17-panelbl2047.img`（11 位，2047 上限，当前使用）

## 触控（相邻问题记录）

- 触控是 `focaltech_ts`（SPI3，reset=GPIO174，irq=GPIO180），不是本页的亮度改动引起的
- 现象：个别开机时 `fts_read_bootid` 读到全 `0x0000`，probe 失败，日志 `not focal IC, unregister driver`；**重启后正常**
- 驱动 probe 失败时不释放 reset/irq GPIO，手动 `unbind/bind` 会因 `-16` 再失败；只能重启
- 若反复出现，需要在 `focaltech_ts` 里补 `-EPROBE_DEFER` 或释放 GPIO 的失败路径
