# 项目交接文档 — Redmi 9A 主线 Linux 7.1

> 目标：在 Redmi 9A（dandelion / MT6762G）上运行主线 Linux 7.1，最终得到可用的 GUI 桌面。
> 本文件面向接手的新同学，包含：现状、环境、文件位置、操作手册、已知坑、下一步。
>
> **⚠️ 最新状态请看 [`PROJECT-ARCHIVE.md`](PROJECT-ARCHIVE.md)**（2026-11-25）。
> 本文件写于更早阶段（rootfs 还是 Alpine、GPU 卡在固件启动），
> 与当前 Ubuntu + phoc + Mesa Vulkan 的状态有出入；保留它作为历史记录。

---

## 1. 项目目标与现实状态

| 子系统 | 状态 | 说明 |
|---|---|---|
| 内核启动 | ✅ | 主线 7.1（自定义树）可启动到 Alpine |
| 显示 | ✅ | DRM/KMS + DSI + FT8006S 面板 + MTK PWM 背光 |
| 触摸 | ✅ | FocalTech FT8006S（SPI），采样率 116.8 Hz |
| 网络/SSH | ✅ | USB NCM（usb0），dropbear |
| GUI | ✅ | Weston（Wayland）+ 软件渲染（llvmpipe）+ mpv 视频壁纸 |
| **GPU** | ⚠️ 90% | 驱动加载、DRM 注册、固件加载、MIPS remap 全部正确；**MIPS 核不执行**（`bFirmwareStarted=0`）|
| 相机/音频/传感器/电池 | ❌ | 未开始 |

**当前阻塞**：设备在刷入原厂 super 后出现 bootloop（r5/r22/r23/r24 全试过），怀疑 **AVB/vbmeta 或 super 分区** 冲突（详见第 7 节）。

---

## 2. 环境与目录

### Windows 侧（编辑、刷机、adb、串口）
```
C:\Users\31806\Documents\AI_Project\Redmi_9A\silex-linux-dandelion\dandelion-kernel\
├── 03-mainline-7.1\          ← 主工作树（文档、脚本、镜像都在这里）
│   ├── GPU-PORT.md           ← GPU 移植进度（必读）
│   ├── DISPLAY-PORT.md       ← 显示/背光进度
│   ├── TOUCH-PORT.md         ← 触摸移植记录
│   └── artifacts\            ← 镜像、驱动、脚本、备份
├── mt6765-mainline-m2\       ← pack_boot_mainline.py（打包工具）
└── mt6765-mainline-m3\       ← 原厂 boot 备份等
```

### WSL 侧（内核编译）
```
~/dandelion-linux-kernel/
├── 01-pure-baseline\         ← 厂商 4.19 内核树（GPU DDK / 触摸驱动 / DTS 参考）
├── 03-mainline-7.1\          ← 主线 7.1（编译在这里，O=out）
└── 02/03/04-*                ← 其他实验树（一般不用）
```

### 设备
- 型号：Redmi 9A（dandelion），SoC MT6762G（MT6765 系列），GPU PowerVR GE8320。
- 关键分区：
  - `p33` boot
  - `p38` super（system/vendor/product）
  - `p40` cache（旧 Alpine 回退）
  - `p41` data（**当前 Alpine 根文件系统**，约 50 GB）
- 串口：USB ACM（initramfs/Alpine 里的 ttyGS0），PC 侧 COM5，115200。
- 网络：USB NCM。手机 `usb0` = 192.168.42.1 + 169.254.42.45/16；PC 侧网卡 APIPA 169.254.42.44。SSH：`root@169.254.42.45`，私钥 `data/keys/dandelion_key`。

---

## 3. 已完成的关键工作

### 3.1 显示（DISPLAY-PORT.md 有细节）
- 修复 `clk-mt6765-mm`（pdev 风格）→ `mediatek-drm` 绑定成功。
- DSI + FT8006S 面板 + 复位极性修正。
- PWM 背光（`pwm@1100e000` 走 MT8183 回退，10 kHz）。
- `kms-loop`：16 bpp RGB565 双缓冲 page flip 播放器（CPU ~2%）。
- 安全模式：`CONFIG_DRM_FBDEV_EMULATION=n`，开机延迟 15 s 再 modeset（早期 modeset 会挂 DSI）。

### 3.2 触摸（TOUCH-PORT.md）
- IC：**FocalTech FT8006S**（helitai 面板），SPI，chip id 0x8642。
- 驱动：`drivers/input/touchscreen/ft8006s_spi/`（从 vendor 4.19 移植，见文档里的 10 项 API 适配）。
- 固件：vendor 源码里的 `fw_helitai_v0e.h` 是 **空文件**；真正固件从 **原厂 super.img → vendor.img → firmware/focaltech_ab_ts_fw_helitai.bin** 提取，放到 `/lib/firmware/`，驱动自动升级（FW 0x04）。
- **udev 必须启动**（libinput 靠它枚举输入设备）。
- 采样率 116.8 Hz（连续滑动）。

### 3.3 网络/GUI
- rcS 自启：udev → insmod 触摸 → seatd → weston → mpv 壁纸。
- Weston 配置：`/etc/xdg/weston/weston.ini`（`panel-height`、`scale=2` 让状态栏字体变大；字体由 Pango 固定，改 panel-height 只改高度）。
- 壁纸：`/root/wallpaper_opt.mp4`（H.264 720x1600，24 fps，7.6 MB，由 1080x1920 源转码）。
- 时区：`TZ=CST-8`（`/etc/profile` + rcS export）。

### 3.4 GPU（GPU-PORT.md）
已确认的事实：
1. **GE8320 是 MIPS 固件核，不是 META**（DDK feature 表 `22.0.104.18` → `MIPS=1`，`META` 被禁用）。早期所有 META 方向的调试都是错的。
2. MIPS 是 32 位处理器：固件必须位于 **物理地址 < 4 GB**。
3. 已修复：
   - DT 加 `linux,cma`（32 MB @ 0x40000000-0x80000000），并修 `size` 的 2-cell 格式。
   - 删除 DDK 宏 `PVR_LINUX_PHYSMEM_SUPPRESS_DMA_AC` 和 `PVR_LINUX_PHYSMEM_USE_HIGHMEM_ONLY`。
   - `DevmemFwAllocateExportable` 强制 `ExactLog2(uiAlign)`（64K 页 → CMA）。
   - 结果：固件在 `0x7cd27000`（低 4 GB），内容正确（MIPS 指令）。
4. 已对比 MIUI（4.19 + vendor 驱动，GPU 正常）：
   - DDK 版本相同（1.13@5776728），固件相同（sha256 `BD4D4155…5575`）。
   - **关键差异**：MIUI 的 `PHYS_BUS_WIDTH = 32`（有 trampoline/REMAP4/REMAP5-BRN63553），我们的表是 **36**。
   - 已把 `rgx_bvnc_table_km.h` 的 `22.0.104.18` 条目改成 32（`0x0008d282…` → `0x0008d283…`），**但还没在设备上验证**（设备 bootloop）。

未解决：MIPS 核不执行（`MSLVCTRL1=0`、`bFirmwareStarted=0`、`boot stage=0`）。电源/时钟/复位/remap 均已核对正确。

---

## 4. 关键文件清单（dist/ 与 scripts/）

| 文件 | 用途 |
|---|---|
| `boot-7.1-dandelion-busybox-r24.img` | 最新启动镜像（含日志的 initramfs；dtb 47672）|
| `build-boot-r24.sh` | 打包脚本（改 r 号即可出新版）|
| `init-busybox-r11.sh` | initramfs 的 init（**r24 版本已加 switch_root 日志**）|
| `alpine-minirootfs-3.24.4-aarch64.tar.gz` | Alpine 根文件系统 |
| `p41-backup/p41-bk.tgz` | p41 关键文件备份（触摸驱动、壁纸、rcS、dropbear key、固件、profile、X11）|
| `focaltech_ts.ko` | 触摸驱动模块 |
| `rcS-final.sh` / `rcS-autostart.sh` | 开机脚本（当前 p41 上的是 rcS-final + 调试包装）|
| `pvrsrvkm.ko` | GPU 驱动模块（**含 PHYS_BUS_WIDTH=32 修改**）|
| `gpurw.c` / `gpurw` | /dev/mem 寄存器读写工具（7.1 上可用；MIUI 的 /dev/mem 被禁）|
| `gpu_diag.c` / `gpu_diag.ko` | ioremap GPU 寄存器的一次性诊断模块 |
| `proxy.py` | PC 代理（0.0.0.0:3128 → 127.0.0.1:10808），apk 依赖它 |
| `serial-capture.ps1` / `serial-cmd.ps1` | 串口抓取/发命令 |
| `dandelion_key` | SSH 私钥（root@169.254.42.45）|
| `miui-gpu/debug_dump_utf8.txt` | MIUI 的 GPU 寄存器快照（UTF-8，对比用）|
| `ICNT86xx_Application.pdf` | 触摸手册（结论：ICNT86 是 I2C，不是我们的芯片）|

---

## 5. 操作手册

### 5.1 编译内核/模块（WSL）
```bash
cd "$HOME/AI Project/Redmi 9A/kernel 7.1 mainline"
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- O=out -j8 Image
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- O=out -j8 modules
# GPU 模块
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- O=out -j8 drivers/misc/pvr/ddk/pvrsrvkm.ko
# 触摸模块
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- O=out -j8 modules
```

### 5.2 打包 boot.img
```bash
bash scripts/build-boot-rXX.sh   # 复制并改 r 号
# 需要：out/arch/arm64/boot/Image.gz、initramfs-busybox.cpio.gz、archive/wsl-archive/dts/r96-gpu.dtb
# DT 源：archive/wsl-archive/dts/r96-gpu.dts（反编译的原厂 dtb），dtc -I dts -O dtb -o archive/wsl-archive/dts/r96-gpu.dtb archive/wsl-archive/dts/r96-gpu.dts
```

### 5.3 刷机（用户手动）
```
fastboot flash boot <img>
fastboot flash super <super.img>   # 3.18GB，恢复 vendor
```

### 5.4 调试
- **SSH**：`ssh -i data/keys/dandelion_key root@169.254.42.45`（PC 的 NCM 网卡需有 169.254.42.44/16）。
- **串口**：PC 的 COM5（需要手机侧 ttyGS0 起来，即 initramfs 的 gadget 或 Alpine 的 usb0）。
- **pstore**：7.1 有 PSTORE_RAM，但当前 pstore 里只有旧数据（ramoops 区域在 DT 里是 `nomap`，可能影响；待查）。
- **屏幕日志**：早期内核（r5）开了 `CONFIG_DRM_FBDEV_EMULATION`，能看到 initramfs 的 tty0 输出；r18+ 为了安全关掉了。

---

## 6. 已知坑（务必先看）

1. **不要 `rmmod pvrsrvkm`**：IRQ action 未清理，之后读 `/proc/interrupts` 会 oops 并打死 dropbear。
2. **GPU 固件**：vendor 源码的 `fw_helitai_v0e.h` 是空的；必须从原厂 `vendor.img` 提取 `.bin`。
3. **触摸 DT**：`mediatek,pad-select` 必须写；`drive-strength` 不能写（MTK pinctrl 报错）。
4. **udev 必须启动**，否则 Weston 报 "no input devices"。
5. **WDT 150 秒**：MTK 看门狗，如果用户态卡住，150 秒后强制重启（看起来像 bootloop）。
6. **AVB/super**：刷了原厂 super 后，boot 分区的 AVB（vbmeta）可能不匹配 → bootloop（**当前怀疑点**）。
7. **TWRP 的 chroot 不可靠**：符号链接在 chroot 里会 "not found"（TWRP 的 chroot 不 chdir），不代表真实启动有问题。
8. **p41 的 ext4 特性**：用 `mke2fs -O ^metadata_csum,^64bit`（TWRP 的 mke2fs 默认特性 TWRP 内核不认）。
9. **串口握手**：initramfs 的 ttyGS0 需要主机先发 1 字节才出提示符。
10. **`/etc/TZ` 对 busybox 不生效**：用 `TZ=CST-8` 环境变量 + `/etc/profile`。

---

## 7. 当前阻塞：bootloop（刷了原厂 super 之后）

时间线：
1. 为做 GPU 对照，刷了原厂 `super.img`（3.18 GB）+ 原厂 `boot.img`（MIUI 4.19）。
2. 之后刷回 r23/r24（我们的 boot）：**bootloop**（150 秒 WDT 或更早）。
3. 试过 r5（有屏幕日志）也 bootloop。
4. p41（Alpine）已恢复（ext4 + minirootfs + 备份），文件完整，chroot 里 busybox 可用。
5. pstore 里只有旧数据（7.1 的 ramoops 可能因 DT `no-map` 无法写）。

**怀疑**：原厂 super 带来 **vbmeta/AVB** 状态，bootloader 对 boot 分区验证失败 → bootloop（即使 unlocked）。

**验证/修复建议**：
- 在 fastboot 里执行：
  ```
  fastboot --disable-verity --disable-verification flash vbmeta <原厂 vbmeta.img>
  ```
  或刷原厂 `vbmeta.img`（disarm AVB）。
- 或者先刷回原厂 boot.img（MIUI）确认能启动，再排查 boot 镜像。
- 如果能进 TWRP，检查 `boot`/`vbmeta` 分区的 AVB 状态。

---

## 8. 下一步建议（优先级）

1. **先解决 bootloop**（AVB/vbmeta 或 boot 镜像问题），让设备能启动。
2. **验证 GPU 的 bus=32 修改**：刷 r24 + `insmod /root/pvrsrvkm.ko`（p41 上已是 bus=32 版本），看 `/proc/pvr/status` 是否 `Firmware Status: OK`。
3. 如果 bus=32 不行，继续对比 MIUI 的 `debug_dump_utf8.txt`（REMAP4/5、MIPS 内部状态）。
4. 触摸的 X/Y 方向/多点触控校准（Weston 里验证）。
5. 相机/音频/电池等驱动（从 vendor 4.19 移植，方法同触摸）。

---

## 9. 参考文档

- `GPU-PORT.md`：GPU 全部细节（S1/S2、MIPS 发现、寄存器值、遇到的问题）。
- `DISPLAY-PORT.md`：显示/背光/开机集成。
- `TOUCH-PORT.md`：触摸移植（芯片、驱动适配、固件提取、采样率）。
- `miui-gpu/debug_dump_utf8.txt`：MIUI 的 GPU 完整状态（对比基准）。
- `logs/device/recovery-pstore-2026-11-19/FINDINGS.md`：早期 r1-r11 的取证记录。
