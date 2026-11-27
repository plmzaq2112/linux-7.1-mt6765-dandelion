# Redmi 9A 主线 Linux 7.1 + Mesa PowerVR Vulkan 移植 — 完整存档

> 日期：2026-11-25；最后更新：2026-11-26（Wayland 合成器 vk_wl/damage/idle/keyboard）
> 范围：内核侧移植（显示/触控/音频/振动）+ GPU（1.13 固件 + 7.1 DDK）+ Mesa Vulkan
> 驱动 + 零拷贝合成器原型。
> 阅读顺序建议：第 0 章看现状 → 第 6 章看关键 bug → 第 11 章看文件清单。

---

## 0. 现状一览（FACT）

| 子系统 | 状态 | 备注 |
| --- | --- | --- |
| 内核启动 | ✅ | 7.1.0-mt6765+（自维护树），Ubuntu 24.04 arm64 rootfs |
| 显示 | ✅ | DRM/KMS + DSI + FT8006S 面板 720×1600 + PWM 背光 + 自动亮度 |
| 触摸 | ✅ | FocalTech FT8006S（SPI），116.8 Hz |
| 音频 | ✅ | mt6765 AFE + mt6357 codec（新增 9 个源文件） |
| 振动 | ✅ | regulator-vibrator |
| 日常桌面 | ✅ | greetd → phosh-session → phoc（厂商 GLES，`pvr-bridge`） |
| GPU 内核 | ✅ | 7.1 DDK 模块 + 1.13@5776728 固件 |
| **Mesa Vulkan** | ✅ | 清屏/三角形/varying/纹理/blend/depth(D16/D32) 全部可用 |
| **零拷贝上屏** | ✅ | 720×1600，58.4 fps（vsync 限速） |
| **Wayland 合成器** | ✅ | `vk_wl`：xdg-shell/shm/dmabuf v3/pointer+keyboard，damage 裁剪+局部重绘+空闲停刷（见 COMPOSITOR-PORT） |
| Stencil | ⚠️ | 通路已就绪，未做测试 |

---

## 1. 硬件与系统基础（FACT）

| 项 | 值 |
| --- | --- |
| 机型 | Redmi 9A（`dandelion`），SoC MT6762G（MT6765 系列） |
| GPU | PowerVR **GE8320**，BVNC **22.87.104.18**，固件 **1.13@5776728** |
| 面板 | Fitipower **FT8006S**，720×1600，4 lane MIPI-DSI，RGB888 |
| 触摸 | FocalTech **FT8006S**（SPI，chip id `0x8642`，固件 `0x04`） |
| 音频 | MT6357 codec + mt6765 AFE |
| 内核 | `7.1.0-mt6765+`，`CONFIG_DRM=y`、`CONFIG_DRM_MEDIATEK=y` |
| rootfs | Ubuntu 24.04.3 LTS（arm64），glibc |
| 分区 | boot `mmcblk0p33`；rootfs/data `p41`；Alpine 救援 `p40` |
| DRM 节点 | 显示 = `/dev/dri/card1`（mediatek-drm）；`card2` = pvrsrvkm；`card0` = faux |
| SSH | `root@169.254.195.201`，私钥 `data/keys/ubuntu-ssh-key` |
| 桌面栈 | greetd → `/usr/local/bin/start-phosh` → `phosh-session` → `phoc`（厂商 GLES 经 `phoc-pvr`），20 s 内失败则回退 pixman |

`start-phosh` 的两个开关（不要动）：
- `/etc/phosh/pvr-disable` 存在 → 强制软件渲染；
- `$XDG_RUNTIME_DIR/pvr-phoc-failed` → 本次启动已回退。

---

## 2. 构建、部署与测试环境

### 2.1 目录分工

- **Windows 工作区**（当前目录）：文档、脚本、测试源码、日志产物
  `C:\Users\31806\Documents\AI_Project\Redmi_9A\silex-linux-dandelion`
- **WSL**：
  - `~/AI_Project/Redmi_9A/kernel_7.1_mainline`：内核树（`O=out` 编译）
  - `~/AI_Project/Redmi_9A/mesa-pvr`：Mesa 树（meson）

### 2.2 构建脚本（`scripts/`）

| 脚本 | 作用 |
| --- | --- |
| `mesa_build.sh` | `ninja -C build-arm64` + `aarch64-linux-gnu-strip -s` → `logs/libvulkan_powervr_mesa.so` |
| `mesa_ninja.sh` | 只跑 ninja（看编译错误） |
| `pvr_build.sh` | 内核模块 `pvrsrvkm.ko` → `logs/pvrsrvkm-dump.ko`（**必须 `strip --strip-debug`**，`-s` 会导致 Invalid module format） |
| `pvr_build_err.sh` | 只打印内核模块编译错误 |
| `build_vk_*.sh` | 各 Vulkan 测试程序（`aarch64-linux-gnu-gcc` + `logs/libvulkan.so.1`） |
| `build_gles_*.sh` | 厂商 GLES oracle（`dlopen` 方式，`-ldl`） |
| `build_vk_kms*.sh` | 合成器原型（额外 `-ldrm -lm`） |

### 2.3 设备端运行环境

```sh
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1
export LD_LIBRARY_PATH=/tmp/pvr-vk
```

厂商 GLES oracle：

```sh
export EGL_LIB=libEGL.so.1 GLES_LIB=libGLESv2.so.2
export LD_LIBRARY_PATH=/root/pvrb:/root/pvr64:/root/pvr64/egl:/root/pvr64/hw
```

合成器原型：

```sh
export VK_KMS_DRM=/dev/dri/card1     # 必须 card1，不是 card0
VK_KMS_SECS=15 /tmp/pvr-vk/vk_kms2
```

测试前 `systemctl stop greetd`，测试后 `systemctl start greetd`（脚本里都带）。

### 2.4 内核模块替换（调试用）

`/root/pvrsrvkm.ko.orig` 是日常模块。调试模块各自独立，例如
`/root/pvrsrvkm-hwrt.ko`、`/root/pvrsrvkm-rgn.ko`、`/root/pvrsrvkm-kicktime.ko`。

所有替换脚本统一用 `trap restore EXIT` 保证自动还原：

```sh
systemctl stop greetd; sleep 3
rmmod pvrsrvkm && insmod /root/pvrsrvkm-xxx.ko pvr_apm=0
... 测试 ...
# trap: rmmod; insmod /root/pvrsrvkm.ko.orig pvr_apm=0; systemctl start greetd
```

**注意**：`pvr_apm=0` 必须带上，否则日常会话行为变化。

---

## 3. 内核侧移植（FACT）

### 3.1 显示

- 根因：`mmsys` 被时钟驱动抢走（详见 `DISPLAY-PORT.md`）。
- 新面板驱动：`drivers/gpu/drm/panel/panel-fitipower-ft8006s.c`
  （720×1600、4 lane、RGB888、video + sync pulse，init 序列来自厂商 4.19 LCM）。
- DSI PHY 用 `mediatek,mt8183-mipi-tx` 兼容串绑定（mt6765 数据缺失，历史遗留）。
- 背光：MTK PWM + I2C 背光 IC；自动亮度（ALS）已能用。

### 3.2 触摸

- `drivers/input/touchscreen/ft8006s_spi/`（厂商驱动移植，模块 `focaltech_ts.ko`）。
- DT：`compatible = "focaltech,fts"`，reset GPIO 174、IRQ GPIO 0。
- 固件：从原厂 `super.img → vendor.img` 提取 `focaltech_ab_ts_fw_helitai.bin`（131072 B）。

### 3.3 音频（新增代码最多的部分）

`sound/soc/mediatek/mt6765/` 新增 9 个文件（afe-clk、afe-pcm、dai-adda/dmic/i2s/pcm、
mt6765-mt6357、reg.h），并改动：

- `sound/soc/codecs/mt6357.c`
- `sound/soc/mediatek/Kconfig` / `Makefile`
- `sound/soc/mediatek/common/mtk-afe-platform-driver.c` / `mtk-soundcard-driver.c`
- `sound/soc/soc-core.c`

### 3.4 其它

- 振动：`regulator-vibrator`
- 电量计：`bq256xx_charger.c`、`generic-adc-battery.c`
- 按键：`mtk-pmic-keys.c`
- 时钟：`clk-mt6765-audio.c`
- ADC：`mt6359-auxadc.c`

### 3.5 内核改动统计（FACT）

```text
34 files changed, 7045 insertions(+), 22 deletions(-)
```

其中音频约 5800 行；GPU 相关改动见第 4 章。

---

## 4. GPU：1.13 固件 + 7.1 DDK 内核 + Mesa UM

### 4.1 三层结构

```
Mesa Vulkan (UM, 我们的移植)
   ↓ ioctl（7.1 DDK 内核模块 ABI）
pvrsrvkm.ko（7.1 DDK 内核，drivers/misc/pvr/ddk）
   ↓ CCB / KCCB 命令（1.13 固件 ABI，由 Mesa winsys 里的 packer 生成）
PowerVR 固件 1.13@5776728（MIPS）
```

**关键设计**：1.13 固件的命令 ABI 差异（TA 80 B / 3D 320 B / TQ 152 B 的字段布局）
全部在 **Mesa 的 winsys** 里转换，不改内核、不 patch 二进制：

- `winsys/pvrsrvkm/pvr_arch_srv_job_render.c`：`pvr_pack_cmd_ta_113()`（80 B）、
  `pvr_pack_cmd_3d_113()`（320 B）
- `winsys/pvrsrvkm/pvr_arch_srv_job_transfer.c`：`pvr_pack_cmd_transfer_113()`（152 B）

### 4.2 内核侧调试设施（都在 7.1 内核树里，默认关闭）

| 机制 | 用法 | 输出前缀 |
| --- | --- | --- |
| `pvr_dump_kick` | `echo N > /sys/module/pvrsrvkm/parameters/pvr_dump_kick` | `pvr-dump:` / `pvr-dump-TA:` / `pvr-dump-3D:` |
| `pvr_dump_stream` | 同上，按 MMU 翻译 VDM control stream | `pvr-stream:` |
| `pvr_dump_rgn` | 同上，dump TA 写出的 region header | `pvr-rgn:` |
| `pvr_kick_time` | 时间戳（entry/pre-sched/sched-done/tail） | `pvr-kick:` |
| `pvr-hwrt`（编译期） | 每次建 HWRTData 打印 | `pvr-hwrt:` |
| MMU 翻译 | `RGXTranslateDevVAddr` + `phys_to_virt`（`mmu_common.c` / `rgxmem.c`） | — |

### 4.3 dma-buf export（实验性，未进日常模块）

`services/server/env/linux/physmem_dmabuf.c`：DDK 原本把 `attach/map_dma_buf/vmap`
全部返回 `-ENOSYS`（“防止外部驱动导入我们的 dmabuf”）。为了让 DRM/KMS 能导入
Vulkan 图像，补了 `attach`（返回 0）、`map_dma_buf`（从 PMR 物理页建 sg_table）、
`vmap/vunmap`（`vm_map_ram`）。

实测导入仍被 **MTK 显示驱动**拒绝（要求物理连续，见 8.2），所以日常不使用；
相关代码只编译成 `/root/pvrsrvkm-dmabuf.ko` 做过实验。

---

## 5. Mesa Vulkan 移植

### 5.1 设备描述

- 新增 `src/imagination/common/device_info/ge8300.h`（BVNC 22.87.104.18 的参数），
  在 `pvr_device_info.c` 注册。
- 关键参数：`tile_size_x/y = 16`、无 `simple_internal_parameter_format`、
  region header 5 B、`tpc` 由内核计算。

### 5.2 扩展能力（`vk_info`，FACT）

```text
device: PowerVR Rogue GE8320   api=1.2.368
VK_KHR_external_memory / _fd        yes
VK_EXT_external_memory_dma_buf      yes
VK_EXT_image_drm_format_modifier    yes
VK_KHR_wayland_surface              no
VK_KHR_display                      no
```

### 5.3 Mesa 改动统计（FACT）

```text
18 files changed, 804 insertions(+), 267 deletions(-)
```

主要文件：`pvr_srv_bridge.c/.h`（1.13 bridge）、`pvr_arch_srv_job_render.c`（packer）、
`pvr_arch_job_render.c`（rt dataset / ZLS / 提交）、`pvr_arch_framebuffer.c`（terminate）、
`pvr_arch_cmd_buffer.c`、`rogue_hw_utils.h`、`ge8300.h`、`pvr_srv.c`。

---

## 6. 关键 bug 档案（按发现顺序）

### 6.1 1.13 TQ 152 B 布局（第 1 阶段）

- 现象：`vkCmdClearColorImage` 无输出。
- 根因：`CR_...` 字段在 1.13 的位置与 1.15 不同。
- 修复：`pvr_arch_srv_job_transfer.c` 里手工 pack 152 B。
- 验证：64×64 清屏 `words=4096 nonzero=4096 red=4096`。

### 6.2 3D 地址块偏移（第 2 阶段）

- 现象：3D 在 `EventStatus=0x10 (ISP_END_MACROTILE)` 锁死。
- 根因：0x40/0x48/0x50/0x100/0x118 的含义与 1.15 不同。
- 修复：`0x40=event_pixel_pds_data`、`0x48=isp_scissor_base`、
  `0x50=isp_dbias_base`、`0x100/0x118=pds_bgnd/pds_pr_bgnd`。
- 验证：三角形能出图（1/4 覆盖）。

### 6.3 TA terminate clip 粒度是 16 px，不是 32 px（1/4 覆盖 + varying 丢失）

- 现象：64×64 只画左上 32×32；顶点色四边形全红；纹理四边形只有底色。
- 证据：`PVR_DEBUG=cs` 解码 PPP state：

```text
[0030] 4: PPP_STATE_UPDATE -> STATE_TERMINATE
  clip_right  : 32 pixels (1 x 32 pixels)
  clip_bottom : 32 pixels (1 x 32 pixels)
```

- 根因：`pvr_arch_framebuffer.c` 用 `DIV_ROUND_UP(w, 32) - 1`，而 1.13 的
  terminate clip 单位是 **16 px**。
- 修复：

```c
term0.clip_right  = DIV_ROUND_UP(width, 16) - 1;
term0.clip_bottom = DIV_ROUND_UP(height, 16) - 1;
```

- 效果：清屏/varying/纹理全部恢复正常。
- **教训**：当时一度误判为“1.15 PPP 格式与 1.13 不同”，实际用 Mesa 自带
  `PVR_DEBUG=cs` 解码器几秒就能证伪。

### 6.4 大尺寸只画一个 macrotile（128×128 以上）

- 现象：128×128 → 只画 64×64；720×1600 → 192×448。
- 证据：厂商 720×1600 的 HWRTData（`pvr-hwrt`）：

```text
vendor: te_screen=0006302c mt1=00b40000 mt2=01900000 stride=00001194
        rgn=1194 isp_mtile=002d0064 tpc=131072/0
```

- 根因：1.13 把**整个 surface 当成一个 macrotile**；Mesa 用的是 4×4 macrotile 分组，
  且 `uiRgnHeaderSize` 被硬编码成 16。
- 修复（按 GE8320 gate）：`mtiles = 1×1`、`mtile_x1/y1 = num_tiles_x/y`、
  x2/x3=y2/y3=0、`rgn header 计数 = num_tiles_x*num_tiles_y`。
- 效果：32×32/64×64/128×128/256×256/320×480/**720×1600** 全部满屏。

### 6.5 region header 未按 512-bit 对齐（24 倍性能损失）★

- 现象：720×1600 的 3D pass 恒定 46 ms，与内容/scissor/region 无关；厂商 1.96 ms。
- 证据（`pvr_dump_rgn`）：

```text
vendor: rgn_va=80014d5800 / 80014d0000   ← 64 B 对齐
mesa:   rgn_va=dbf0001000 / dbf00067e4   ← 第二份偏移 0x57e4 = 22500，36 B 未对齐
```

- 根因：`pvr_rt_get_region_headers_stride_size()` 只在
  `simple_internal_parameter_format` 时才 `ALIGN_POT(..., 512-bit)`；
  1.13 没有该 feature，第二份 RT data 的 region header 基址错位 36 字节，
  TE 每 tile 写入都跨 cache line → ISP 走慢路径（~10 µs/tile）。
- 修复：

```c
rgn_headers_size =
   ALIGN_POT(rgn_headers_size, ROGUE_CR_TE_PSGREGION_ADDR_BASE_ALIGNMENT);
```

- 效果：46 ms → **3.07 ms**；合成器 20.7 → **57.9 fps**。

### 6.6 `te_psg.region_stride` 整除截断（次要）

- 根因：`rgn_headers_stride / 4096` 向下取整（22500 B 应为 6 页，写成 5 页）。
- 修复：`DIV_ROUND_UP`。对性能无影响，但避免 TE 写 region header 越界。

### 6.7 D16 深度：`isp_bgobjdepth` 必须写 float

- 现象：D16 深度测试完全不出图（连颜色都没有），深度清 1.0 也没生效。
- 证据：厂商 F32Z 的 `isp_bgobjdepth = 3f800000`；我们 D16 写 UNORM16 `0xffff`。
- 探针结果（`vk_ds`，64×64）：

| 配置 | 颜色 | 深度 |
| --- | --- | --- |
| D16 默认（`0xffff`） | 全蓝 | 0/0 |
| D16 + `zls_stride=0` | 全蓝 | 0/0 |
| **D16 + `bgobjdepth=3f800000`** | **红 3072 / 绿 1024** | **6553 / 58982** |
| D16 + float + `zlsctl=F32` | 红/绿对但深度值错 | 52429 / 26214 |

- 修复（GE8320 gate）：

```c
case ROGUE_CR_ZLS_FORMAT_TYPE_16BITINT:
   if (GE8320_113) value.value = fui(depth_clear);      /* float! */
   else            value.value = _mesa_float_to_unorm(depth_clear, 16);
```

---

## 7. 绘制能力现状（FACT）

| 能力 | 状态 | 验证 |
| --- | --- | --- |
| TQ clear（`vkCmdClearColorImage`） | ✅ | `words=4096 nonzero=4096 red=4096` |
| render-pass clear | ✅ | `nonzero=4096 red=4096` |
| 三角形（无 varying） | ✅ | 全屏 1352 绿 / 2744 蓝 |
| 顶点色 varying | ✅ | `red=2016 green=2080` |
| 纹理 + UV | ✅ | 四色各 1024 |
| Alpha blend | ✅ | `ff800080`（0.5 红 + 0.5 蓝） |
| Depth D32_SFLOAT | ✅ | 深度值 0.1 / 0.9 精确，遮挡正确 |
| Depth D16_UNORM | ✅ | 6553 / 58982（本次修复） |
| Stencil | ⚠️ | 通路存在，未测 |
| 720×1600 全屏 3D | ✅ | 3.05 ms（厂商 1.96 ms） |

---

## 8. 合成器原型（零拷贝上屏）

### 8.1 结论

`vk_kms2`：**Mesa Vulkan 直接渲染进扫描缓冲并上屏，720×1600，57.9 fps（vsync 限速）**。

```text
import: 720x1600 pitch=2880 size=4608000
zero-copy: Vulkan renders into the scanout dma-buf
presented 464 frames in 8.01s (57.9 fps)
avg: queue 0.67 ms, fence-wait 0.07 ms, pageflip 14.99 ms
```

### 8.2 为什么是“反向导入”

`mtk-drm` 用 `DRM_GEM_DMA_DRIVER_OPS`，其导入函数要求 **dma-buf 物理连续**：

```c
if (drm_prime_get_contiguous_size(sgt) < attach->dmabuf->size)
        return ERR_PTR(-EINVAL);
```

PVR 通用堆的 Vulkan 图像是离散页（1125 页 / 45–290 段），所以“PVR 出图 → DRM 导入”
必然失败。正确做法：

1. DRM dumb buffer 分配连续缓冲（CMA）+ `AddFB`；
2. `drmPrimeHandleToFD` 导出；
3. Vulkan `VK_KHR_external_memory_fd` 导入成线性图像（pitch 2880 与 dumb 一致）；
4. Vulkan 直接画进正在扫描的缓冲，`drmModePageFlip` 翻页。

### 8.3 流水线与性能定位

- `NSLOT=3` + 1 帧在飞：渲染第 N 帧的同时翻第 N-1 帧。
- 定位过程：内核 kick 2.2 ms、Mesa 提交主体 0.3 ms，时间全在
  `pvr_clear_last_submits_syncs()` 的 `vk_sync_wait_many(...)`（等上一帧 fence）。
- 最终瓶颈是 6.5 的 region header 对齐问题（46 ms）；修好后自然回到 vsync 限速。

---

## 9. 调试方法论（可复用）

1. **先拿厂商 golden，再改代码**：同样的内核模块/固件跑厂商 GLES（`gles_clear`、
   `gles_triangle`、`gles_depth`），把“硬件能做到什么”钉死。
2. **Mesa 自带解码器**：`PVR_DEBUG=cs` 能把 TA control stream、PPP state
   （`STATE_HEADER`/`STATE_VARYING`/`VIEWPORT`/`TERMINATE`）完整解出来，
   比手工猜字段快得多。
3. **内核侧时间戳**：`pvr_kick_time` 把 kick 拆成 pre-sched/sched/tail；
   `PVR13_TIME=1`（Mesa）把提交拆成 clear/waits/cmds/sig。
4. **环境变量探针**：Mesa 里 17 个 `PVR13_*`（见第 11 章）可以在一次构建里
   反复试字段组合，避免频繁重编译。
5. **对照顺序**：HWRTData → 寄存器流 → 地址/对齐 → 时间戳，逐层排除。
6. **基准测试要闭环**：同一 cmd buffer 循环提交 + `vkQueueWaitIdle`，
   才能把“帧成本”和“启动开销”分开。

---

## 10. 已知问题与后续路线

### 10.1 已知问题（FACT）

| 问题 | 说明 |
| --- | --- |
| 系统 wlroots 是 0.17.1 | 没有 Vulkan renderer（0.18+ 才有），无法直接接 phoc；当前用自研 `vk_wl` 协议子集绕开 |
| MTK 显示要求连续 dma-buf | 只能“连续缓冲 → Vulkan 导入”，不能反向导出 |
| dma-buf 导入限制 | 仅单平面 LINEAR/implicit modifier；Mesa PVR 无 `VK_EXT_image_drm_format_modifier`（FACT） |
| Wayland 协议缺口 | 无 popup 约束、无 `wl_data_device`、单输出；keyboard 已有但未跑真实终端/GTK 客户端（FACT） |
| Mesa 每帧在 `pvr_clear_last_submits_syncs` 等上一帧 | 单帧延迟因此偏高（吞吐已够） |
| 3D 3.05 ms vs 厂商 1.96 ms | 还差 ~1.5 倍，来源未查清 |
| Stencil / D24 | 未验证 |

### 10.2 路线建议

1. **真实 Wayland 客户端验证**：在 `vk_wl` 上跑 foot/GTK 等真实客户端，验证 keyboard、dma-buf、damage/focus；缺客户端时先交叉编译最小客户端。
2. **Wayland 协议补齐**：按需补 `wl_data_device`、popup 约束、更多 buffer 格式/ modifier（受 Mesa PVR 能力限制）。
3. **性能**：对比厂商 1.96 ms，继续定位 3D 3.05 ms 的剩余开销。
4. **功能**：stencil、D24、mipmap、多重采样。

---

## 11. 文件与改动清单

### 11.1 文档

| 文件 | 内容 |
| --- | --- |
| `docs/porting/PROJECT-ARCHIVE.md` | **本文件**，全项目存档 |
| `docs/porting/GPU-PORT.md` | GPU 移植历史（1.13 固件、连接、固件启动等） |
| `docs/porting/DISPLAY-PORT.md` | 显示/DSI/背光 |
| `docs/porting/TOUCH-PORT.md` | 触摸 |
| `docs/porting/PROJECT-HANDOVER.md` | 早期交接文档（顶部已标注指向本文件） |
| `docs/porting/mesa-pvr-stage5-session.md` | Mesa 阶段 5 详细记录（含推翻的错误结论） |
| `docs/porting/COMPOSITOR-PORT.md` | 合成器、零拷贝、性能定位、Wayland 协议子集 (`vk_wl`) |

### 11.1.1 状态快照

未提交改动的补丁快照（可 `git apply` 回放）：

| 文件 | 内容 |
| --- | --- |
| `kernel/patches/mesa-pvr-2026-11-26.patch` | Mesa 全部改动（18 文件，824+ / 270-，1961 行 diff） |
| `kernel/patches/mesa-pvr-2026-11-25.patch` | Mesa 早期快照（2026-11-25） |
| `kernel/patches/kernel-7.1-2026-11-25.patch` | 内核树全部改动（34 文件，7639 行；WSL diff stat 2026-11-26 未变） |
| `kernel/patches/kernel-untracked-files/` | 内核未跟踪的新文件（`regulator-vibrator.c`、`rail_en.c`） |
| `kernel/patches/*-untracked-2026-11-25.txt` | 未跟踪文件清单（`vendor-unpack/` 体积大，未纳入） |

回放方式（在各自 git 树根目录）：

```sh
git apply kernel/patches/mesa-pvr-2026-11-26.patch
git apply kernel/patches/kernel-7.1-2026-11-25.patch
```


### 11.2 Mesa（WSL `~/AI_Project/Redmi_9A/mesa-pvr`，未提交，2026-11-26）

```text
18 files changed, 824 insertions(+), 270 deletions(-)
（详见 kernel/patches/mesa-pvr-2026-11-26.patch）
```

主要文件：`ge8300.h`、`pvr_device_info.c`、`rogue_hw_utils.h`、
`pvr_arch_cmd_buffer.c`、`pvr_arch_framebuffer.c`、`pvr_arch_job_render.c`、
`pvr_arch_queue.c`、`pvr_rogue_fwif_shared.h`、`pvr_arch_srv_job_render.c`、
`pvr_arch_srv_job_transfer.c`、`pvr_srv*.c/h`、bridge/job_common/compute/render/transfer。

**GE8320 专属分支**（BVNC 22.87.104.18 gate）共 5 处：
`pvr_arch_job_render.c`（mtile、region header 计数、D16 bgobjdepth）、
`pvr_arch_srv_job_render.c`（`PVR_DEVICE_IS_GE8320_113`）、`rogue_hw_utils.h`（1×1 macrotile）。

**调试探针（环境变量）**：

```text
PVR13_3D_FLAGS0  PVR13_BGOBJDEPTH  PVR13_BGobjVALS  PVR13_DUMP_RT  PVR13_HEAPS
PVR13_ISPCTL     PVR13_NON4K       PVR13_PAGE_LOG2  PVR13_RGN_B     PVR13_RGN_R
PVR13_RGN_STRIDE PVR13_SLSSTRIDE   PVR13_TERM_B     PVR13_TERM_R    PVR13_TIME
PVR13_ZLSCTL     PVR13_ZLSSTRIDE
```

### 11.3 内核（WSL `~/AI_Project/Redmi_9A/kernel_7.1_mainline`）

```text
34 files changed, 7045 insertions(+), 22 deletions(-)
```

- 音频（新增 9 文件 ≈5800 行）、显示（面板驱动）、触摸、振动、电源、ADC、时钟；
- GPU 调试：`rgxta3d.c`（dump_kick/stream/rgn/kick_time/hwrt）、`mmu_common.c`、
  `rgxmem.c/h`、`rgxtransfer.c`、`physmem_dmabuf.c`（实验性 export ops）；
- **注意**：内核树里同时有音频/面板等未提交改动，改动前先 `git status`。

### 11.4 测试程序 / 合成器（`scripts/`）

| 程序 | 用途 |
| --- | --- |
| `vk_info.c` | 设备/扩展/内存属性 |
| `vk_clear_tq.c` | TQ clear（`VK_TQ_LOOP`） |
| `vk_clear2.c` | render-pass clear |
| `vk_triangle.c` | 无 varying 三角形 |
| `vk_colored_quad.c` | 顶点色 varying |
| `vk_textured_quad.c` | 纹理 + UV |
| `vk_geom.c` | 视口/scissor/像素图/bbox + 循环基准（`VK_GEOM_LOOP`、`VK_GEOM_TILED`、`VK_GEOM_NOCLEAR`、`VK_GEOM_NODRAW`） |
| `vk_ds.c` | depth + blend（`VK_DS_D32`） |
| `vk_kms.c` | 合成器 v1（PVR 出图 → DRM 导入，失败退 CPU 拷贝） |
| `vk_kms2.c` | 合成器 v2（连续 dumb buffer → Vulkan 导入，零拷贝） |
| `vk_comp.c` | 多层 KMS 合成器（alpha/scissor/touch 输入） |
| `vk_wl.c`（生成） | Wayland 合成器：由 `make_vk_wl.py` 从 `vk_comp.c` 生成 |
| `wl/wl_backend.c` | Wayland 协议后端：shm/dmabuf/damage/idle/seat pointer+keyboard |
| `wl/wl_test_client.c` | Wayland 测试客户端：shm/dmabuf/static/partial/freerun |
| `wl/uinput_kbd.c` | uinput 虚拟键盘注入器（端到端 keyboard 验证） |
| `build_vk_wl.sh` / `make_vk_wl.py` | 构建 vk_wl / 生成 C 源 |
| `kms_prime_probe.c` | PRIME 自导入自检 |
| `gles_clear.c` / `gles_triangle.c` / `gles_depth.c` | 厂商 oracle（带 `GLES_LOOP`） |
| `ds.vert` / `ds.frag` / `tri.vert` / `tri.frag` / `color.*` / `quad.*` | shader 源 |

### 11.5 设备端产物

```text
/root/pvrsrvkm.ko.orig         日常模块（pvr_apm=0）
/root/pvrsrvkm-hwrt.ko         HWRTData 打印
/root/pvrsrvkm-rgn.ko          region header / kick dump
/root/pvrsrvkm-dmabuf.ko       dma-buf export 实验
/tmp/pvr-vk/                   Mesa .so、ICD json、Vulkan 测试、vk_comp/vk_wl/wl_test_client
/root/gles_clear|gles_triangle|gles_depth   厂商 oracle
artifacts/                     本仓库归档：vk_*, vk_wl, wl_test_client, uinput_kbd, pvr64 libs 等
```

---

## 12. 回滚与注意事项

1. **不要动日常可用链路**：`greetd`、`start-phosh`、`phoc-pvr`、`pvrsrvkm.ko.orig`。
2. 任何模块替换都必须用 `trap` 自动还原（仓库里的 `device_*.sh` 都是这个模式）。
3. 刷机 / 分区写入需要人工显式批准，并先备份。
4. Mesa 的 `PVR13_*` 探针都是 `getenv` 门控，默认行为不变；但**正式合并前应清理**。`VK_WL_*` / `WL_CLIENT_*` 为 compositor 测试开关，默认关闭。
5. `mesa_build.sh` 用 `strip -s`；内核模块必须 `strip --strip-debug`。
6. 内核树与 Mesa 树都有大量未提交改动，操作前先看清 `git status`。
