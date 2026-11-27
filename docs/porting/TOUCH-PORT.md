# TOUCH-PORT.md — FT8006S 触摸移植（03-mainline-7.1）

> 目标：在主线 7.1 上跑通 Redmi 9A（dandelion）的 SPI 触摸。

## 结论（已完成）

| 项 | 结果 |
|---|---|
| 触摸 IC | **FocalTech FT8006S**（helitai 面板），SPI，chip id `0x8642` |
| 控制器 | `spi3` @ 0x11013000（GPIO21-24），IRQ=GPIO0，RESET=GPIO174 |
| 驱动 | `drivers/input/touchscreen/ft8006s_spi/`（vendor 驱动移植，单模块 `focaltech_ts.ko`）|
| 固件 | 从原厂 `super.img → vendor.img` 提取 `focaltech_ab_ts_fw_helitai.bin`（131072 B），升级到 FW `0x04` |
| 输入 | udev 识别 `ID_INPUT_TOUCHSCREEN=1`，Weston 自动关联 `DSI-1` |
| 采样率 | **116.8 Hz**（连续滑动，median 8.6ms，峰值 185Hz）|

## 关键改动

### DT（r96-gpu.dts）
```dts
&spi3（spi@11013000）:
  status = "okay";
  mediatek,pad-select = <0>;      /* 7.1 的 mt65xx SPI 必需 */
  pinctrl-0 = <&spi3_pins>;
  touch@0 {
      compatible = "focaltech,fts";
      spi-max-frequency = <0x7a1200>;   /* 8 MHz */
      interrupts = <0 2>;                /* GPIO0, falling */
      focaltech,reset-gpios = <&pio 174 0>;
      focaltech,irq-gpios   = <&pio 0 0>;
  };
pinctrl: spi3-pins { pinmux = <0x1501 0x1601 0x1701 0x1801>; };  /* 无 drive-strength */
```
- **`drive-strength` 不能写**（MTK pinctrl 报 `pin_config_group_set op failed`）
- **`mediatek,pad-select` 必须写**（否则 probe 报 `-EINVAL`）

### 驱动适配（7.1 API）
1. `of_get_named_gpio_flags` → `fwnode_gpiod_get_index`（gpiod）
2. `gpio_direction_* / gpio_to_irq` → `gpiod_*`
3. `proc_create(file_operations)` → `proc_ops`
4. `earlysuspend` / `FB_EVENT_BLANK` → 宏兜底
5. `get_fs/set_fs/mm_segment_t` → 删除
6. `vfs_read` → `kernel_read`
7. `irq_to_desc` → 去掉（7.1 不导出）
8. `.remove` 返回 void
9. `FTS_INFO/FTS_ERROR` 改为 printk（`FTS_DEBUG_EN=0` 时原本是空宏）
10. lct_* / flash 的缺失符号用 `fts_stub.c` 补齐

### 固件
- vendor 源码里的 `fw_helitai_v0e.h` 是 **0 字节空文件**
- 从原厂包 `dandelion_images_V12.5.4.0.../images/super.img`（7-Zip 解 LP）→ `vendor.img`（609MB）→ `firmware/focaltech_ab_ts_fw_helitai.bin`
- 放到设备 `/lib/firmware/`，驱动 `FTS_FW_REQUEST_SUPPORT=1`，insmod 后自动升级
- 升级日志：`pram app write successfully` / `fw download successfully` / `tp is in fw mode`

### 自启（rcS）
```
udevd --daemon; udevadm trigger; udevadm settle
insmod /root/focaltech_ts.ko
seatd -g root &
weston --backend=drm-backend.so --continue-without-input &
mpv --vo=wlshm --fullscreen --loop /root/wallpaper_opt.mp4 &
```
- **udev 是必须的**（libinput 靠它枚举 `/dev/input`，否则 Weston 报 no input devices）
- 时间：`TZ=CST-8`

## 已知问题
- `rmmod focaltech_ts` 后 GPIO 未释放（`gpiod` 非 devm），再次 insmod 报 `-EBUSY`；需重启或改用 `devm_fwnode_gpiod_get_index`
- 触摸坐标映射（XY 轴方向）尚未校准（需要在 Weston 里验证）
- 多点触控未测（只测了单点）
