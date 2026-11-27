# Mesa Vulkan 合成器（Compositor）阶段记录 — 2026-11-25

目标：让 Mesa PowerVR Vulkan 真正输出到 Redmi 9A 的 DSI 面板，向“合成器”方向验证。

## 结论摘要（FACT）

- **Vulkan 内容已经上屏**：`vk_kms2`（最小合成器内核）在 720×1600 面板上做
  DRM/KMS modeset + 双缓冲 page flip，画面由 Mesa Vulkan 渲染，**零拷贝**。
- 实测：`presented 118 frames in 6.08s (19.4 fps)`，`pageflip ≈ 6.5 ms`。
- 系统自带 `libwlroots 0.17.1` **没有 Vulkan renderer**（0.18 才有），
  所以先用自写最小合成器打通“渲染 + 上屏”。

## 关键发现（FACT）

### 1. Mesa pvr 的扩展能力足够

`vk_info`（设备 API 1.2.368）：

```text
VK_KHR_external_memory           yes
VK_KHR_external_memory_fd        yes
VK_EXT_external_memory_dma_buf   yes
VK_EXT_image_drm_format_modifier yes
VK_KHR_wayland_surface           no
VK_KHR_display                   no
```

即：**能导入/导出 dma-buf**，但没有 WSI surface（wlroots Vulkan renderer
也不需要 WSI，它用 dma-buf 直接合成）。

### 2. MTK 显示驱动只接受“物理连续”的 dma-buf

`drivers/gpu/drm/mediatek/mtk_drm_drv.c` 用 `DRM_GEM_DMA_DRIVER_OPS`，
对应 `drm_gem_dma_prime_import_sg_table()`：

```c
if (drm_prime_get_contiguous_size(sgt) < attach->dmabuf->size)
        return ERR_PTR(-EINVAL);
```

PVR 通用堆的 Vulkan 图像是离散页（实测 720×1600 = 1125 页 / 45–290 个 sg 段），
所以 `drmPrimeFDToHandle()` 返回 `EINVAL`。

为了让 PVR 侧能导出，另外给 DDK 补了 dma-buf export 的
`attach/map_dma_buf/vmap/vunmap`（`physmem_dmabuf.c`，原本全是 `-ENOSYS`），
导出后的 dmabuf 能被 attach/map，但**仍因不连续被 MTK 拒绝**。
结论：这个方向（PVR 出图 → DRM 导入）需要连续内存，暂不走。

### 3. 正确方向：连续扫描缓冲 → Vulkan 导入

`vk_kms2` 的做法：

1. 用 DRM dumb buffer 分配两块 720×1600 连续缓冲（CMA）+ `AddFB`；
2. `drmPrimeHandleToFD` 导出成 dma-buf；
3. `VK_KHR_external_memory_fd` + `VkImportMemoryFdInfoKHR` 把 dma-buf
   **导入成 Vulkan 线性图像**（pitch 2880 与 dumb buffer 一致）；
4. Vulkan 直接渲染进正在扫描的缓冲，`drmModePageFlip` 翻页。

实测 `import: 720x1600 pitch=2880 size=4608000`，随后
`zero-copy: Vulkan renders into the scanout dma-buf`。

## 性能（FACT）

| 场景 | 结果 |
| --- | --- |
| 零拷贝 + 上屏（串行） | 19.4 fps，pageflip 6.5 ms |
| 零拷贝 + 上屏（**流水线**） | 20.7–21.3 fps |
| 零拷贝 + 不上屏 | 18.1 fps |
| PVR 自有图像 + CPU 拷贝 | 12.3 fps |

### 流水线化（已做）

`vk_kms2` 现在是 3 个缓冲、1 帧在飞：渲染第 N 帧的同时翻第 N-1 帧
（`NSLOT=3`、`pending` / `onscreen` / `busy[]`）。效果：

```text
串行:   queue 0.5 ms,  fence-wait 43.0 ms,  pageflip 6.5 ms
流水线: queue 34.0 ms, fence-wait 0.07 ms,  pageflip 11.3 ms
```

**延迟被藏起来了，但成本转移到了 `vkQueueSubmit` 里**：fence 等待降到
0.07 ms，说明上一帧的渲染在翻页期间就完成了；但 `vkQueueSubmit` 本身
变成 34 ms。也就是说瓶颈是“每次提交一个 job 需要 ~35–43 ms 才能被
GPU/固件处理完”，与 draw 数、clear、是否上屏无关（clear-only 也是 53 ms）。

结论（HYPOTHESIS）：不是填充率、不是 dma-buf、不是 CPU 拷贝，而是
TA/3D job 的**往返延迟**（很可能内核 kick 路径要等上一个 job 完成，
或固件对每个 job 有固定开销）。厂商 GLES 用同一内核模块/固件跑桌面流畅，
所以差异在 Mesa 提交的 job 形态或 1.13 packer 的 kick flags。

下一步：在内核 `rgxta3d.c` 的 kick 路径加时间戳（需要换调试模块），
确认是 `RGXScheduleCommand` 重试、还是固件完成中断/ fence 更新慢。

### 定位 35 ms（FACT）

内核侧（`rgxta3d.c` 加 `pvr_kick_time` 时间戳，换模块实测）：

```text
pvr-kick: pre-sched  +960 us
pvr-kick: sched-done +1600 us
pvr-kick: tail       +2200 us
```

一个 kick 全程 **~2.2 ms**（含 TA/3D 合并 kick 的 `RGXScheduleCommand`）。

Mesa 侧（`PVR13_TIME=1`）：

```text
pvr-time: init=9 us  ws=204..386 us          # pvr_arch_render_job_submit
pvr-q:    clear=64728 us waits=0 cmds=325 us sig=56 us   # pvr_driver_queue_submit
```

- 提交主体（cmd 处理）只有 ~0.3 ms；
- 时间全在 `pvr_clear_last_submits_syncs()`：它里面调用
  `vk_sync_wait_many(..., VK_SYNC_WAIT_COMPLETE, UINT64_MAX)`，
  **阻塞等上一帧的 fence**。这就是“流水线也提不上去”的直接原因。

### 那为什么一帧要 44 ms？（FACT）

`vk_geom` 加循环基准（同一条 cmd buffer 重复提交）：

```text
bench 64x64:    20 frames, 0.51 ms/frame
bench 720x1600: 20 frames, 44.30 ms/frame
```

→ 成本与**像素数**成正比（≈38 ns/px，26 Mpx/s），不是固定的调度延迟。
同时确认：

- GPU 时钟不是问题：`mfg_sel = 390000000`（390 MHz，`13000000.mfg_doma`）；
- 与 draw 数无关（1 vs 16 draws 时长几乎一样）、与是否上屏无关、
  与扫描缓冲是 PVR 自有还是导入的 CMA 无关；
- 因此瓶颈是**逐像素/带宽**：720×1600 全屏 clear ≈ 4.6 MB，
  44 ms 相当于 ~105 MB/s，对这个 GPU 明显异常。

**HYPOTHESIS（下一步验证）**：
1. 线性（非 tiled）渲染目标导致写入不合并 —— 对比 tiled 目标；
2. 1.13 兼容路径的 clear/bgobj 实现效率低 —— 去掉 render pass 的
   loadOp=CLEAR，改成画一个全屏三角形对比；
3. MMU/缓存属性（导入的 CMA 是 uncached + 4 KB 页，TLB 抖动）。

### 三项排除实验（FACT）

| 实验 | 结果 | 结论 |
| --- | --- | --- |
| 线性 vs tiled（`VK_GEOM_TILED=1`） | 46.0 vs 47.3 ms | tiling 无关 |
| clear-only / draw-only / **什么都不画** | 46.6 / 47.1 / **46.2 ms** | 与内容无关，按面积计费 |
| 16 KB 页堆（`PVR13_NON4K=1`，内核已有 “General NON-4K”） | 46.0 ms | 页大小/TLB 无关 |
| **TQ clear（`vkCmdClearColorImage`）720×1600** | **1.03 ms** | 内存/TQ 路径正常 |
| 厂商 GLES `glClear` 720×1600（20 帧循环） | **1.94 ms** | 硬件完全能跑到这个量级 |

**结论（HYPOTHESIS）**：3D/ISP 阶段对**每个 tile**（4500 个 16 px tile）
都有 ~10 µs 的固定开销，与是否真的画/清无关；TQ 与厂商路径都正常。
即我们 1.13 3D 侧（ISP/TE 寄存器或 HWRTData）让硬件走了慢路径。

下一步：用 `pvr-hwrt` 打印 Mesa 720×1600 的 HWRTData，与厂商 golden
逐字段对比（`aa`、`merge`、`maxrts`、`tpc`），再对 3D 320 B 流里的
`isp_ctl` / `isp_zlsctl` / `pbe_word` / `te_psg` 做同样的对照。


### HWRTData / 3D 流逐字段对照（FACT）

用 `pvrsrvkm-hwrt.ko` 同时抓厂商 `gles_clear 720 1600` 与 Mesa `vk_geom720`：

```text
vendor: ppp=063f02cf te_screen=0006302c aa=00000000 mt1=00b40000 mt2=01900000
        stride=00001194 rgn=1194 isp_mtile=002d0064 maxrts=1 tpc=131072/0 merge=0,0,0,0,0,0
mesa:   ppp=063f02cf te_screen=0006302c aa=00000000 mt1=00b40000 mt2=01900000
        stride=00001194 rgn=1194 isp_mtile=002d0064 maxrts=1 tpc=131072/0 merge=0,0,0,0,0,0
```

**HWRTData 完全一致**（`aa=0`，没有误开 MSAA）。

3D 320 B 流（`pvr-dump-3D`）逐字对比后，只有少数几个字段不同：

| 偏移 | 字段 | 厂商 | Mesa |
| --- | --- | --- | --- |
| `0x28` | `isp_bgobjvals` | `00000100` | `000003ff` |
| `0x30` | `isp_ctl`（pipe_enable/upass_start） | `0003600f` | `00033000` |
| `0x14` | `usc_clear_register[0]`（clear 颜色） | `ff0000ff` | `00000000` |
| `0x130` | 我们猜的 submit flags | `0` | `00008000` |
| `0x50` | `isp_dbias_base` | 有地址 | `0` |

对应探针（`PVR13_3D_FLAGS0` / `PVR13_ISPCTL=0x3600f` /
`PVR13_BGobjVALS=0x100` / `PVR13_RGN_STRIDE=6|0|8`）逐个试过，**全部无变化**
（45→43 ms，属噪声）。

TA 80 B 流差异：`ppp_ctrl` 0x303 vs 0x202、`te_psg` 0x20000 vs 0x20005
（`region_stride` 0 vs 5）。`region_stride` 是“每个 RT 的 region header 页数”，
Mesa 用 `rgn_headers_stride / 4096` **整除截断**（22500 B 应为 6 页，写成了 5），
属于该修的真实小 bug，但实测改成 6/0/8 对本问题无影响。

### 决定性对照（FACT）

| 场景 | 720×1600 耗时 |
| --- | --- |
| 厂商 GLES **3D 绘制**（`glDrawArrays`+`glFinish`，无 clear） | **1.96 ms** |
| 厂商 GLES `glClear` | 1.94 ms |
| 我们的 3D pass（空 render pass） | 46 ms |
| scissor 缩到 32×32 | 44.6 ms |
| region clip 缩到 32×32（TA 只 tile 一小块） | 44.3 ms |

→ 3D 硬件本身没问题；我们的 3D pass 是**按整个 RT 面积无条件计费**
（4500 个 tile，~10 µs/tile），与 scissor/region/内容都无关；厂商路径
≈0.4 µs/tile。差异在“逐 tile 处理”这一层（region header / 参数流 / PDS 取数），
而不是像素着色器或寄存器开关。

### 下一步

抓 **TA 写出的 region header（每 tile 5 B）** 内容，厂商 vs Mesa 逐字节对比：
如果我们的 header 里“参数地址/load-store 位”写错，ISP 会在每个 tile 上
多做事，正好符合“按 tile 计费、与内容无关”的现象。

## 根因：region header 未按 512-bit 对齐（已修复，FACT）

抓 TA 写出的 region header（内核新增 `pvr_dump_rgn`，从 HWRTData 的
`sRgnHeaderDevVAddr` 翻译并按字节 dump）：

```text
vendor: pvr-rgn: rgn_va=80014d5800   (64 B 对齐)
        pvr-rgn: rgn_va=80014d0000   (64 B 对齐)
mesa:   pvr-rgn: rgn_va=dbf0001000   (对齐)
        pvr-rgn: rgn_va=dbf00067e4   (偏移 0x57e4 = 22500，36 字节 → 未对齐!)
```

`TE_PSGREGION_ADDR` 要求 **512-bit（64 B）对齐**。Mesa 的
`pvr_rt_get_region_headers_stride_size()` 只在
`simple_internal_parameter_format` 时才做这个对齐，本机（1.13，无该 feature）
就没对齐 → 第二份 RT data 的 region header 基址错位 36 字节，TE 每个 tile
的写入都跨 cache line，ISP 直接掉到 ~10 µs/tile 的慢路径。

修复（`pvr_arch_job_render.c`）：

```c
/* 永远按 512-bit 对齐，而不是只在 simple_internal_parameter_format 时 */
rgn_headers_size =
   ALIGN_POT(rgn_headers_size, ROGUE_CR_TE_PSGREGION_ADDR_BASE_ALIGNMENT);
```

顺带修掉 `te_psg.region_stride` 的整除截断（22500 B 应为 6 页而非 5）：

```c
value.region_stride = DIV_ROUND_UP(rt_dataset->rgn_headers_stride, 4096);
```

### 修复效果（FACT）

| 场景 | 修复前 | 修复后 |
| --- | --- | --- |
| `vk_geom720`（720×1600，3D pass） | 46 ms/帧 | **3.07 ms/帧** |
| `vk_geom64` | 0.53 ms | 0.36 ms |
| **`vk_kms2` 零拷贝合成器（720×1600）** | 20.7 fps | **57.9 fps** |
| 厂商 GLES 3D draw（参考） | 1.96 ms | 1.96 ms |

`vk_kms2` 现在：`queue 0.67 ms, fence-wait 0.07 ms, pageflip 14.99 ms`
→ 完全被 vsync 限速（60 Hz），已经进入“正常性能”区间。

正确性回归全部通过：

```text
vk_colored_quad : red=2016 green=2080
vk_textured_quad: red/green/blue/yellow 各 1024
vk_clear2       : nonzero=4096
vk_geom720      : nonzero=1152000 bbox 0..719 / 0..1599
```

## depth / blend 能力（FACT）

新增 `vk_ds`（64×64 颜色 + D16 深度，ds.vert/ds.frag）：

### blend —— 正常（FACT）

蓝色背景上画 (1,0,0,0.5) 的四边形，`srcAlpha/oneMinusSrcAlpha`：

```text
blend: center=ff800080 corner=ff800080   (期望 0.5*红 + 0.5*蓝 ≈ 0x800080)
```

字节序 RGBA → `ff800080` = A=ff, B=80, G=00, R=80 → **完全正确**。

### depth —— 未工作（FACT）

同一测试里：清深度到 1.0、先画近处绿色(z=0.1)、再画远处红色(z=0.9)，
期望中心绿、四周红。实际：

```text
color: red=0 green=0 blue=4096     ← 只有清屏的蓝，两个 quad 都没画出来
depth: center=0 corner=0           ← 深度清 1.0 也没生效
```

抓带深度附件的 3D 流（`pvr_dump_kick`）确认 Mesa 侧状态是齐的：

```text
0x24 isp_bgobjdepth = 0000ffff          (D16 清 1.0)
0x30 isp_ctl        = 00133000
0x60 isp_zlsctl     = 000000001d08001c
0x68 isp_zload_base = 80000ca000
0x70 stencil base   = 0
0x130 flags         = 00008080, 0x134 zls_stride = 00002000
```

**HYPOTHESIS**：1.15 里深度/模板缓冲描述符在 `pbe_word[1..7]` 中，
而我们的 1.13 packer 只拷贝了 `pbe_word[0]`（0x78 处 24 B），
所以 ZS 描述符根本没到硬件；另外 0x60/0x68/0x134 这几个偏移对 1.13
是否就是 zlsctl/zload/stride 也还没验证。

下一步：写一个**厂商 GLES 深度测试**，用 `pvr_dump_kick` 抓厂商的 3D 流，
定位 1.13 里 ZS 描述符和 zls 寄存器的真实偏移，再改 packer。

### depth —— D16 和 D32 都已修好（FACT）

厂商对照抓到关键差异：厂商 F32Z 的 `isp_bgobjdepth = 3f800000`（float 1.0），
而 Mesa 对 D16 写的是 UNORM16（`0xffff`）。

探针结果（`vk_ds`，64×64）：

| 配置 | 颜色 | 深度 |
| --- | --- | --- |
| D16 默认（`bgobjdepth=ffff`） | 全蓝（什么都没画） | 0 / 0 |
| D16 + `zls_stride=0` | 仍全蓝 | 0 / 0 |
| **D16 + `bgobjdepth=3f800000`** | **红 3072 / 绿 1024** | **6553 / 58982** |
| D16 + `bgobjdepth=float` + `zlsctl=F32` | 红/绿对，但深度值错 | 52429 / 26214 |

结论（FACT）：1.13 的 `ISP_BGOBJDEPTH` **即使深度缓冲是 16 位整数，也必须写
IEEE 单精度浮点**；写 UNORM16 会让 ISP 把所有片元都判为失败（连颜色都不出）。

修复（`pvr_arch_job_render.c`，按 GE8320 识别码 gate）：

```c
case ROGUE_CR_ZLS_FORMAT_TYPE_16BITINT:
   if (GE8320_113)
      value.value = fui(depth_clear);          /* float, 不是 UNORM16 */
   else
      value.value = _mesa_float_to_unorm(depth_clear, 16);
```

修复后：

```text
=== D16 (after quirk) ===
color: red=3072 green=1024
center=ff00ff00 corner=ff0000ff
depth: center=6553 corner=58982          ← 0.1 / 0.9
blend: center=ff800080 corner=ff800080   ← 混合仍正确

=== D32_SFLOAT ===
depth32: center=0.1000 corner=0.9000     ← 无回归
```

其它回归全过（`vk_colored_quad`、`vk_textured_quad`、`vk_clear2`、
`vk_geom720` 3.05 ms / 1152000 px）。

## 每 draw 成本与 region 面积（FACT，2026-11-26）

`VK_GEOM_DRAWS` / `GLES_DRAWS` 对照（720×1600，10 帧平均）：

| draws/帧 | Mesa（全屏 scissor） | 厂商 GLES |
| --- | --- | --- |
| 1 | 3.02 ms | 2.37 ms |
| 4 | 8.36 ms | 2.33 ms |
| 16 | 29.98 ms | 2.38 ms |
| 64 | 116.11 ms | 2.54 ms |
| 256 | 459.97 ms | 2.37 ms |

看起来“Mesa 每 draw 1.8 ms、厂商免费”，但把 **scissor 缩小**后（Mesa，64 draws）：

| scissor | 64 draws |
| --- | --- |
| 全屏 720×1600 | 116.13 ms |
| 256×256 | 6.73 ms |
| 64×64 | **1.51 ms** |

拟合：`t_per_draw ≈ 17 µs + 0.40 µs × tile 数`（tile = 16 px）。
厂商单次全屏 draw 2.37 ms ≈ 0.53 µs/tile，和我们 0.68 µs/tile 同一量级。

**结论（FACT）**：每 draw 成本与**该 draw 的 region（viewport∩scissor）面积**成正比，
不是固定的驱动开销；厂商的 256 draws 之所以“免费”，是因为每个 draw 的 region 只有
三角形包围盒那么小。

**对合成器的含义**：
- 必须按 damage/window 设置 scissor，不要每个 draw 都用全屏 scissor；
- 64×64 region 的 draw 约 0.024 ms，100 个这样的 draw ≈ 2.4 ms → 60 fps 有富余；
- 256×256 region 约 0.12 ms/draw，100 个 ≈ 12 ms → 60 fps 偏紧；
- 全屏 region 约 1.8 ms/draw，多个全屏 draw 会直接掉帧。



- `src/wayland/vk_kms.c`：第一版（PVR 出图 → DRM 导入；dmabuf 失败自动退到 CPU 拷贝）
- `src/wayland/vk_kms2.c`：**工作版本**（连续 dumb buffer → Vulkan 导入，零拷贝）
  - 环境变量：`VK_KMS_DRM`（默认 `/dev/dri/card0`，本机显示是 **card1**）、
    `VK_KMS_SECS`、`VK_KMS_NOPRESENT`、`VK_KMS_DUMB`、`VK_KMS_DRAWS`、
    `VK_KMS_CLEARONLY`
- `src/wayland/kms_prime_probe.c`：PRIME 自导入自检（证明显示驱动 PRIME 本身可用）
- `src/wayland/vk_info.c`：Vulkan 设备/扩展打印
- 内核侧（WSL 树，未装入日常模块）：`physmem_dmabuf.c` 增加
  dma-buf export 的 attach/map/vmap/vunmap

运行方式（手机）：

```sh
systemctl stop greetd
export VK_ICD_FILENAMES=/tmp/pvr-vk/powervr_icd.json
export PVR_I_WANT_A_BROKEN_VULKAN_DRIVER=1 LD_LIBRARY_PATH=/tmp/pvr-vk
VK_KMS_DRM=/dev/dri/card1 VK_KMS_SECS=15 /tmp/pvr-vk/vk_kms2
systemctl start greetd
```

## 多图层合成器（FACT，2026-11-26）

`vk_comp`（基于 `vk_kms2` 的零拷贝路径）：

- 每层是一个动画四边形，**每层用自己的 scissor**（像素矩形，clamp 到屏幕）；
- 层颜色带 alpha 0.7，`srcAlpha/oneMinusSrcAlpha` 混合，按数组顺序叠加；
- 3 个扫描缓冲 + 1 帧在飞，`VK_COMP_LAYERS` 控制层数（1..16）。

实测（720×1600，零拷贝上屏，8 s）：

| 层数 | 每层区域 | fps | queue | pageflip |
| --- | --- | --- | --- | --- |
| 8 | 180×200 | **58.4** | 0.57 ms | 14.83 ms |
| 16 | 180×200 | **58.4** | 0.53 ms | 14.95 ms |

16 层共约 576 个 16-px tile，远低于全屏 4500 tile 的预算，所以完全被 vsync 限速。
这直接验证了上一节“每 draw 成本 = region 面积”的结论：
**只要按窗口/damage 设 scissor，几十个图层也能跑满 60 Hz。**

## 多图层 + 纹理图层（FACT，2026-11-26）

### 纹理图层（已验证）

`vk_comp` 现在每层采样一张纹理（4 张程序生成的 128×128：棋盘、渐变、
同心环、斜条纹），`out = texture(u_tex, uv) * v_color`，alpha 0.7 混合。

用 `VK_COMP_VERIFY=1` 把最后一帧的扫描缓冲 mmap 回来做数值校验：

| 层数 | 非背景采样点 | 期望（每层 1440 点） | fps |
| --- | --- | --- | --- |
| 1 | 1440 | 1440 | 58.4 |
| 4 | 5760 | 5760 | 58.4 |
| 8 | 11335 | 11520（略有重叠） | 58.4 |

采样到的颜色 `ffb631a0` 是纹理像素值 × 层颜色，**证明纹理采样正确**。

### 动态 viewport / scissor：其实一直是对的（FACT，结论已修正）

最初以为「启用动态 scissor 后所有 draw 都不出像素」，并据此关掉 ISP scissor。
**这个结论是错的** —— 真正的起因是第 6.8 节（合成器自己的 Y 映射 bug）：

- 层几何被画到 y≈1352（镜像后），而 scissor 矩形在 y=48..248；
- ISP scissor 忠实地把它裁掉了 → 看起来“什么都没画”。

Y 修好之后复测：

```text
ISP scissor 启用（上游字格式）:  diff=1440/46080  bbox x=67..246 y=47..246   ✓
ISP scissor 启用 + 16 位对半交换: diff=0                                    ✗（格式确实是 xmin 高 / xmax 低）
```

精确裁剪验证（64×64，scissor 20×20）：

| 配置 | green |
| --- | --- |
| ISP scissor 启用 | **147**（三角形被裁到 20×20） |
| `PVR13_NOSCISSOR=1` 关闭 | 1352（**完全不裁**，连 region clip 也没有） |

所以：
- **ISP scissor 表（`isp_scissor_base` + `STATE_ISPDBSC.scindex`）工作正常**，
  字格式就是 `xmin` 高 16 位 / `xmax` 低 16 位（y 同理）；
- 之前“用 region clip 兜底”的绕行其实**完全不裁**（`scenable=0` 时
  `pvr_setup_isp_depth_bias_scissor_state()` 整段不执行），只是图层几何本身
  等于矩形，看起来“被裁好了”；
- 该 quirk 已回退，`PVR13_NOSCISSOR=1` 保留为 A/B 开关。

### 顺带发现：Y 翻转 —— 是合成器自己的 bug（FACT）

`VK_COMP_VERIFY` 求非背景 bbox 时发现层“跑到下半屏”：

```text
layer0 rect=(68,48 180x200)          ← 期望
verify bbox y=1353..1552             ← 实际（1600-48-200=1352）
```

第一版以为是驱动问题，实际是 **`layers_upload()` 里把 Vulkan clip space 的
Y 方向搞反了**（Vulkan 的 NDC **+Y 指向 framebuffer 底部**，我按“+Y 在上”写的）。
修正：

```c
/* Vulkan clip space: y = +1 is the *bottom* of the framebuffer. */
float y0 =  l->y        / h * 2.0f - 1.0f;
float y1 = (l->y + l->h) / h * 2.0f - 1.0f;
```

修正后 bbox = `x=67..246 y=47..246`，与层矩形 (68,48,180,200) 一致 ✓
（±1 px 来自像素中心取整）。驱动侧的 viewport 计算本来就是对的
（`a1 = y + h/2, m1 = +h/2`，符合 Vulkan 约定）。

## 触摸输入（FACT，2026-11-26）

`vk_comp` 现在直接读 evdev 拖拽图层：

- 自动探测触摸设备（遍历 `/dev/input/event*`，找带 `ABS_MT_POSITION_X` 的节点）：
  本机是 `/dev/input/event2`（`fts_ts`），**abs 范围 720×1600，与屏幕 1:1，无需缩放**；
- 协议 B：`ABS_MT_POSITION_X/Y` + `ABS_MT_TRACKING_ID` + `SYN_REPORT`；
- 按下时取最上层命中图层，记录抓取偏移；移动时更新图层位置并清零速度；
  抬起时释放（`VK_COMP_INPUT` 可强制指定设备节点）。

自检（`VK_COMP_AUTODRAG=1`，不需要真的摸屏）：

```text
touch: grab layer 0 at 18,18
touch: release layer 0
autodrag: layer0 (8,8) -> (48,38), expect +40,+30      ✓ 精确
input: /dev/input/event2 (abs 720x1600)
presented 118 frames in 2.02s (58.5 fps)
verify: slot=0 diff=5760/46080 bbox x=48..633 y=38..476  ✓ 拖拽后仍正确渲染
```

真机验证：`VK_COMP_LAYERS=8 VK_KMS_SECS=20 /tmp/pvr-vk/vk_comp`，然后用手指
拖动任意图层；日志会打印 `touch: grab layer N` / `touch: release layer N`。

## Wayland 协议子集（FACT，2026-11-26）

目标：让**真正的 Wayland 客户端**（标准 `libwayland-client` + xdg-shell）直接上屏，
而不是只在合成器内部画动画图层。

### 架构

| 文件 | 作用 |
| --- | --- |
| `src/wayland/wl/wl_backend.c` | `wl_display`、全局对象、表面/缓冲区/输入转发 |
| `src/wayland/wl/wl_test_client.c` | 标准 Wayland 客户端（xdg-shell + shm/dma-buf，动画） |
| `src/wayland/wl/xdg-shell.xml` | 协议 XML（wayland-protocols 1.34） |
| `src/wayland/wl/linux-dmabuf-unstable-v1.xml` | 协议 XML（dma-buf） |
| `src/wayland/make_vk_wl.py` | 从 `vk_comp.c` 生成 `vk_wl.c`，复用 Vulkan/KMS/零拷贝 |
| `src/wayland/build_vk_wl.sh` | 生成 xdg-shell 协议代码 + 交叉编译两个二进制 |

### 支持的协议

- `wl_compositor` 4：`create_surface`、`create_region`（region 忽略）
- `wl_shm`：直接用 `wl_display_init_shm()`，ARGB8888 / XRGB8888
- `zwp_linux_dmabuf_v1` 3：单平面 ARGB8888 / XRGB8888，LINEAR 或隐式 modifier，
  `create` 与 `create_immed` 都支持
- wl_seat 5：pointer + keyboard；触屏事件转发 pointer，evdev 键盘转发 wl_keyboard（含 xkb keymap、modifiers、focus）
- `wl_output` 2：geometry / mode / scale / done
- `xdg_wm_base` 1：`xdg_surface` + `xdg_toplevel`（configure/ack/title/app_id/
  move/maximize 等）；popup 可创建但不做约束求解

### 数据路径

两条路径，出图都走同一个管线：

**shm（软件客户端）**：客户端 shm（ARGB8888，内存里是 BGRA）→ commit 时同步
拷进该 surface 的 R8G8B8A8 线性 `VkImage`（host-visible；`vkDeviceWaitIdle`
后写，帧录制时插 `HOST → FRAGMENT_SHADER` 屏障）→ 采样 → 零拷贝扫描缓冲。
拷贝完立刻 `wl_buffer.release`。

**dma-buf（GPU 客户端）**：`zwp_linux_buffer_params_v1` 收到 fd 后立即
`VkImportMemoryFdInfoKHR` 导入成 `B8G8R8A8_UNORM` 线性图像（每次 wl_buffer
一张，`VK_IMAGE_USAGE_SAMPLED_BIT`），**不拷贝**；commit 时只做布局转换
（`UNDEFINED/HOST → SHADER_READ`）。`release` 延后一帧再发，避免客户端在 GPU
还在采样时重写。
注意：Mesa PVR 没有 `VK_EXT_image_drm_format_modifier`，所以线性 import 的
pitch 必须与客户端 stride 一致（实测 DRM dumb buffer 的 pitch 与
`vkGetImageSubresourceLayout().rowPitch` 完全相同）。

布局是 cascade：`x = 40 + 40*(i%4)`、`y = 200 + 40*(i%4)`；
按住窗口拖动时由合成器做服务端移动。

### 验证（FACT）

3 个真实客户端窗口：

```text
wl: mapped surface 0 at 40,200 size 200x150
wl: mapped surface 1 at 80,240 size 240x180
wl: mapped surface 2 at 120,280 size 280x210
verify: surf0 rect=(40,200 200x150) centre=(140,275) ff30a060
verify: surf1 rect=(80,240 240x180) centre=(200,330) ffc04040
verify: surf2 rect=(120,280 280x210) centre=(260,385) ffc04040
verify: slot=0 diff=3456/46080 bbox x=40..399 y=200..489
presented 1402 frames in 24.00s (58.4 fps), mode=zero-copy
```

- bbox 精确等于三个矩形的并集（x=40..399，y=200..489）；
- centre 颜色 = 覆盖该点的**最上层** surface 的颜色 → z-order 与 alpha 正确；
- 方向：客户端在 buffer 左上角画 20×20 黄块，读回 `marker top=ffffe000` → 无翻转；
- 8 个窗口同时动画：`presented 1051 frames in 18.00s (58.4 fps)`，
  bbox `x=40..639 y=200..679`（= 8 个矩形并集），`queue 0.53 ms / fence 0.08 ms`；
- 输入（合成器注入一次拖拽，`VK_WL_FAKE_TOUCH`）：客户端收到
  `pointer enter (20,10)` → `button down` → `motion (50,40)` ×2 →
  `motion (20,10)` → `button up`，窗口实际移动 +60,+60（`surf1 (80,240) → (140,300)`）；
- 期间 `vk_clear2 / vk_triangle / vk_colored_quad / vk_textured_quad / vk_ds /
  vk_geom 32..320x480 / vk_comp 8 层` 全部回归通过。

dma-buf 路径（`WL_CLIENT_DMABUF=1`，客户端用 DRM dumb buffer 导出 fd）：

```text
client: dmabuf 256x160 pitch=1024 (dumb handle 1)
dmabuf: imported 256x160 fmt=34325241 stride=1024 pitch=1024 size=163840
dmabuf: wl_buffer create_immed 256x160
wl: mapped surface 0 at 40,200 size 256x160
verify: surf0 rect=(40,200 256x160) centre=(168,280) ff000000 marker top=ffffe000
verify: slot=0 diff=4833/46080 bbox x=40..503 y=200..503
presented 936 frames in 16.02s (58.4 fps), mode=zero-copy
```

- `stride == pitch`（1024 / 1280 / 1536 三档全部一致）→ 无需显式 modifier 布局；
- bbox 精确等于三个矩形并集；`marker top=ffffe000` → 方向正确；
- 顺带修了一个真实 bug：libwayland 的 shm buffer 也带 user_data，最初被误判成
  dma-buf；现在先 `wl_shm_buffer_get()` 判定，dma-buf 再用 magic 校验；
- XRGB8888（`fmt=34325258`）同样导入成功，alpha 通过 view swizzle 强制为 1
  （`VK_COMPONENT_SWIZZLE_ONE`）。

### damage tracking 与空闲省电（FACT，2026-11-26）

`wl_surface.damage` / `damage_buffer` 现在真的被用起来了：

1. **上传裁剪**：shm 路径只把 damage 矩形（行区间 × 列区间）拷进纹理，
   其余内容沿用上一帧；首次上传或尺寸变化仍走全量。
2. **每 slot 独立累积**：三个扫描缓冲各自记录"自上次渲染以来发生过的 damage"，
   某个 slot 再次被选中时把累积的矩形一次补画完。
3. **局部重绘**：非首次的 slot 用 `loadOp=LOAD` 的 render pass
   （`initialLayout=GENERAL`），先用 `vkCmdClearAttachments` 只清 damage 矩形，
   再把每个表面的 scissor 与 damage 求交后绘制。
4. **空闲不提交**：连续 60 帧（约 1 秒）没有任何 damage 且没有挂起的
   frame callback 时，合成器不再渲染、不再 pageflip，只在 Wayland 事件循环里等待
   （`wl_event_loop_dispatch`，被客户端提交唤醒）。

实测（720×1600，零拷贝）：

| 场景 | 结果 |
| --- | --- |
| 静态客户端 | `presented 63 frames in 12.01s`、`cpu 0.44s (3.6%)`、`idle frames 682` |
| 动画客户端（全表面 damage） | `client: exiting after 8s (423 commits, 54.0 fps)`，合成器同窗口 421 帧 |
| 局部 damage（每帧 8×8 一块） | 上传 `rect=(104,48)-(112,56)` 这类小矩形；三个 slot 读回 `diff=1200` **完全一致** |

局部 damage 用例是刻意的正确性测试：客户端每帧只在条带上画一个新的 8×8 色块、
只 damage 这一块。如果任何 slot 丢掉一次 damage，三个 slot 的读回就会不一致；
实测三者 `diff` 与 bbox 完全相同。

**测量注意（踩过的坑）**：把"8 秒总时长"当分母会得到 43 fps 的假象 ——
客户端只运行了 6 秒，活跃期实际是 `353 damage / 6 s = 58.8 fps`。
现在统计口径统一用客户端提交数（每次提交对应一次呈现）。

### wl_keyboard + xkb（FACT，2026-11-26）

- `wl_seat` 同时 advertise `pointer + keyboard`。
- keymap：构建期用 `xkbcommon` 生成 `us`（evdev/pc105）keymap，内嵌为 `xkb_keymap.h`，通过 `wl_keyboard.keymap`（fd）发送；客户端用 libxkbcommon 解析。
- 输入：evdev 扫描带 `KEY_A..KEY_Z` 的 `/dev/input/event*`，`VK_WL_KBD` 可覆盖；keycode `+8` 转为 XKB keycode。
- 焦点：首个 mapped toplevel 自动 focus；点击设置 focus；focus surface 销毁时转移。
- 修饰键：Shift/Ctrl/Alt/Super/CapsLock 做基本 mask 跟踪（FACT：简化映射，按键语义由客户端 xkb 解释）。

端到端验证（uinput 虚拟键盘，`tests/device/device_wl_kbd.sh`）：

```text
kbd: using /dev/input/event3
kbd: client bound (keymap 34206 bytes)
kbd: focus on surface 0
client: keymap ok (34206 bytes, 1 layouts)
client: keyboard focus in (0 keys down)
client: key code=38 down sym=0x61 "a"
client: key code=56 down sym=0x62 "b"
client: key code=54 down sym=0x63 "c"
client: key code=36 down sym=0xff0d "\n"
```

限制：未在真实终端/GTK Wayland 客户端上验证（HYPOTHESIS：应可用，但可能暴露协议细节缺口）。

### 已知限制

1. dma-buf 只支持单平面、LINEAR/隐式 modifier（没有 `VK_EXT_image_drm_format_modifier`，
   tiled/压缩缓冲无法导入）；
2. shm 每次 commit 仍会 `vkDeviceWaitIdle`（实测 0.08 ms，不是瓶颈），但整表面重采样
   仍在活动期每帧进行 —— 局部重绘只按 damage 区域做，未做 occlusion/背景剔除；
3. 没有 popup 约束求解、没有 wl_data_device，只有单输出
4. damage 只用于上传裁剪 + 重绘范围 + 空闲判定，不做多矩形精确合并（单矩形并集）。

## 下一步

1. ~~真合成器~~ —— **已完成**：`vk_wl` 跑通标准 Wayland 客户端（xdg-shell + shm）；
2. ~~`zwp_linux_dmabuf_v1`~~ —— **已完成**：单平面 LINEAR dma-buf 直接导入采样；
3. ~~按需重绘~~ —— **已完成**：damage 上传裁剪 + per-slot 累积 + 局部重绘 + 1 秒空闲停刷；
4. ~~加 keyboard~~ —— **已完成**：evdev 扫描字母键盘（VK_WL_KBD 可覆盖），内嵌 us xkb keymap，wl_keyboard keymap/modifiers/enter/leave/key，点击或首个 toplevel 自动聚焦；uinput 端到端验证通过；
5. （可选）定位 3.05 ms vs 厂商 1.96 ms 的剩余 3D 差距。

