# Mesa PowerVR Stage 5 记录（2026-11-25 晚）

## 结论摘要

- **FACT**：`vk_clear_tq`（`vkCmdClearColorImage`）64×64 读回
  `words=4096 nonzero=4096 red=4096`，四角全 `ff0000ff`；1.13 TQ 152 B 已通。
- **FACT**：`vk_triangle` 能画出绿色三角形：
  `words=4096 nonzero=1024 green=507 blue=517`。
- **FACT**：三角形仍只覆盖左上 32×32；32×32 表面只清/画 16×16，
  即覆盖面积始终是 1/4。
- **FACT**：Mesa 的图形 control stream 只有 **60 B**；
  厂商 GLES 的 `vdm_ctrl_stream_base` 高字是 **0x80 = 128 B**。
- **HYPOTHESIS**：60 B 的 control stream 缺少 1.13 的 viewport/VPT 块，
  1.13 固件因此用默认 32×32 viewport；这是 1/4 覆盖的根因。

## 已验证的路径

| 路径 | 状态 |
|---|---|
| Mesa instance/device | 已通 |
| TQ 152 B 硬件 clear | 已通，整屏红 |
| render pass clear（load-op） | 只 1/4 |
| render pass triangle draw | 已出绿色像素，只 1/4 |
| 3D/TA 命令布局 | 80 B / 320 B，与厂商 golden 对齐 |

## 关键文件/函数

Mesa（WSL `~/AI_Project/Redmi_9A/mesa-pvr`，未提交）：

- `winsys/pvrsrvkm/pvr_arch_srv_job_render.c`
  - `pvr_pack_cmd_ta_113()` / `pvr_pack_cmd_3d_113()`；
  - HWRTData 参数覆盖（GE8320 用 `rgn=16`）。
- `winsys/pvrsrvkm/pvr_arch_srv_job_transfer.c`
  - `pvr_pack_cmd_transfer_113()`：192 B → 152 B TQ。
- `vulkan/pvr_arch_cmd_buffer.c`
  - `pvr_cmd_buffer_fill_default_scissor()`；
  - `PVR_DUMP_CS=1` control stream dump。
- `common/device_info/ge8300.h`
  - BVNC 22.87.104.18 专用 features：关闭 `simple_internal_parameter_format`。
- `include/hwdef/rogue_hw_utils.h`
  - `rogue_get_num_macrotiles_xy()` 对该 BVNC 返回 1×1（tpc=128）。
- `winsys/pvrsrvkm/pvr_srv_bridge.c`
  - `PVR_DUMP_CMD=1` 的 TA/3D/TQ 命名 dump。

内核（WSL `~/AI_Project/Redmi_9A/kernel_7.1_mainline`，未提交）：

- `drivers/misc/pvr/ddk/services/server/devices/rogue/rgxta3d.c`
  - `pvr_dump_kick`（TA/3D hexdump）；
  - `pvr-hwrt:` HWRTData 参数打印。
- `drivers/misc/pvr/ddk/services/server/devices/rogue/rgxtransfer.c`
  - `pvr_dump_tq`（TQ hexdump）。

注意：内核树里还有音频/panel 等未提交改动，本记录没有触碰它们。

Windows 工作区新增脚本：

- `src/wayland/vk_clear_tq.c` / `build_vk_clear_tq.sh`
- `src/wayland/vk_triangle.c` / `tri.vert` / `tri.frag` /
  `build_vk_triangle.sh` / `spv_to_header.py`
- `scripts/pvr_dump_shim.c` / `build_pvr_shim.sh`
- `scripts/scan_pvr_maps*.py`
- `scripts/mesa_*_patch.py`（各阶段补丁）

## 已验证的 1.13 TQ 布局

```text
0x00 isp_bgobjvals
0x04 usc_pixel_output_ctrl
0x08 usc_clear_register0..3
0x18 isp_mtile_size
0x1c isp_render_origin
0x20 isp_ctl
0x24 isp_xtp_pipe_enable      (1.13 无 isp_aa)
0x28 event_pixel_pds_info
0x2c event_pixel_pds_code
0x30 event_pixel_pds_data
0x34 isp_render
0x38 isp_rgn
0x40 pds_bgnd0_base
0x48 pds_bgnd1_base
0x50 pds_bgnd3_sizeinfo
0x58 isp_mtile_base
0x60 pbe_wordx_mrty[2][3]    (48 B)
0x90 flags
```

## 已排除的 1/4 候选

- scissor：已提供全屏 scissor 表，3D `0x48` 非 0，覆盖不变；
- region header：4 B / 5 B、`rgn=16`、`tpc=128` 均试过，覆盖不变；
- `isp_ctl=0x3600f`、硬件 clear 寄存器、`pds_info=0x204`：覆盖不变；
- `bgobjvals=0x100`：完全不 clear（已回退）；
- TA flags `0x00100000`：覆盖不变（已回退）。

## 厂商 control stream 已抓到（FACT，2026-11-25 深夜）

内核侧新增 `pvr_dump_stream`：

- `rgxta3d.c` 从 TA `0x10` 取完整 u64 VA（`0x800018b000`），
  经 `RGXTranslateDevVAddr` → `MMU_GetVDevAddrPhys` 翻译；
- `MMU_GetVDevAddrPhys` 在 `mmu_common.c`，按 PTE 的
  `uiAddrMask/uiAddrShift` 取物理地址；
- `phys_to_virt` 后用 `print_hex_dump` 输出 256 B。

实机（厂商 GLES clear）：

```text
pvr-stream: va=800018b000 phys=45a08000
00000000: 00000c80 00010000 4c000f84 00010040
00000010: 00010000 00000004 20000442 68000100
00000020: 00000002 00000380 00c2b000 c0000000
00000030: 00000000 ... 全 0
```

`pvr_gles2_test`（clear + triangle）抓到的是同一份 **clear/load-op**
stream（`va=80001c7000`），不是 draw 的 viewport stream。

## draw-only 结果（FACT）

`gles_triangle`（不 glClear）仍然抓到同一份 48 B stream：

```text
pvr-stream: va=800018b000 phys=454e2000
00000000: 00000c80 00010000 4c000f84 00010040
```

与厂商 clear 完全相同，说明 **viewport 不在主 control stream**。

- 关闭默认 scissor 表后，Mesa 三角形仍是 1024/4096
  （green 507 / blue 517），说明 scissor 块也不是 draw 的 1/4 根因；
  该探针已从 Mesa 源码回退。
- 目前差异更可能在 **TA 80 B 的 draw 状态** / VBO/TA 程序 / HWRTData，
  而不是 control stream。

## 下一步

1. 抓厂商 GLES draw 的 **TA 80 B** 与 **HWRTData**（`pvr-hwrt`），
   和 Mesa 的 64×64 draw 对比；
2. 特别看 `ppp_ctrl`、`te_psg`、TA flags、`isp_ctl` 的组合；
3. 若仍不明确，再回到 1.13 VDM/TA 状态块格式。

## 其他绘制尝试（FACT）

`vk_textured_quad`（2×2 纹理 + sampler + descriptor set + 6 顶点）：

```text
words=4096 nonzero=1024 red=0 green=0 blue=1024 yellow=0
(0,0)=ffff0000 (31,0)=ffff0000 (0,31)=ffff0000 (31,31)=ffff0000
```

只有 render pass 的蓝色，没有纹理颜色。说明 **descriptor/texture 路径**
在 1.13 上还没通（draw 没有写出，或采样路径失败），与 1/4 覆盖无关。

下一步先做 **无 descriptor 的彩色四边形**（vertex color + 2 三角形），
验证多属性/VBO，再单独修纹理/descriptor。

### 彩色四边形结果（FACT）

`vk_colored_quad`（vertex color + VBO + 6 顶点，无 descriptor）：

```text
words=4096 nonzero=1024 red=1024 green=0 blue=0
(0,0)=ff0000ff (31,0)=ff0000ff (0,31)=ff0000ff (31,31)=ff0000ff
```

整个 1/4 区域全红，第二三角形的绿色没有出现。说明：
- 无 varying 的三角形（`vk_triangle`）能正常画；
- 一旦使用 **vertex color varying**，结果退化成第一个顶点的红色；
- `vk_textured_quad` 也只有蓝底，纹理依赖 UV varying，和这里一致。

**HYPOTHESIS**：1.13 路径的 **PDS/USC varying/插值** 状态还没对齐，
不是 descriptor 或 viewport 单独的问题。下一步查 varying buffer /
插值寄存器的 1.15 vs 1.13 差异。

### varying 调查结果（FACT + HYPOTHESIS）

> 后续修正：本节的“PPP/control stream 格式不同”结论是错的，见下方
> “1/4 覆盖 + varying 丢失：根因已找到并修复”。

抓 colored quad 的 `PVR_DUMP_CS=1`：

```text
colored quad: 0000: 01 00 01 20 ...
triangle:     0000: 02 00 01 20 ...
vendor 1.13:  0000: 00000c80 00010000 4c000f84 00010040
```

- Mesa 两个 stream 都是 60 B，第一字是 **`0x20010001`**（colored）
  和 **`0x20010002`**（triangle）；
- vendor 1.13 draw stream 只有 48 B，第一字是 **`0x00000c80`**；
- 说明 **1.13 和 1.15 的 PPP/control stream 头格式不同**；
- 1.13 固件不认识 Mesa 的 `0x2001xxxx` PPP header，
  于是 varying 计数/varying base 没被应用，片段 shader 拿到默认值
  （第一个顶点的颜色）；viewport 也退回默认 32×32。

**结论**：1/4 viewport 和 varying 走丢是**同一个根因**——
1.15 PPP/control stream 格式没转成 1.13。下一步要做的是
**PPP/control stream 转换层**，而不是继续调 3D 命令字段。

补充实验：把 TA 的 `ppp_ctrl` 改成厂商 `0x303`，并给 TA flags 加
`0x00100000`，再跑 colored quad：

```text
words=4096 nonzero=1024 red=1024 green=0 blue=0
```

仍然全红，说明 **TA 80 B 的字段组合也不是 varying 的修法**；
该探针已回退。要解决 varying，必须拿到 1.13 的
PPP/control stream（或 `TA_STATE_VARYING`/`PDS_VARYINGBASE`）格式。

## 1/4 覆盖 + varying 丢失：根因已找到并修复（FACT）

根因不是 PPP/control stream 格式，而是 **TA terminate 的 clip 粒度**。

`pvr_arch_framebuffer.c: pvr_arch_ppp_state_create()` 里用
`DIV_ROUND_UP(width, ROGUE_TA_STATE_TERMINATE0_CLIP_*_BLOCK_SIZE_IN_PIXELS) - 1`
（XML 里该宏是 32）。GE8320 / 1.13 的 terminate clip 单位实际是 **16 px**。

证据：用 Mesa 自带解码器（`PVR_DEBUG=cs`）抓 `vk_colored_quad`（64×64）的
PPP state：

```text
[0030] 4: PPP_STATE_UPDATE -> STATE_TERMINATE
  clip_right  : 32 pixels (1 x 32 pixels)
  clip_bottom : 32 pixels (1 x 32 pixels)
```

→ TA 只终止了左上 32×32 区域，3D 阶段也只清/画这一块。

修复（`pvr_arch_framebuffer.c`）：

```c
term0.clip_right = DIV_ROUND_UP(width, 16) - 1;
term0.clip_bottom = DIV_ROUND_UP(height, 16) - 1;
```

修复前后实测（同一测试、同一 .so 版本）：

| 测试 | 修复前 | 修复后 |
| --- | --- | --- |
| `vk_geom64`（64×64 三角+clear） | nonzero=1024，bbox 0..31 | nonzero=4096，bbox 0..63 |
| `vk_clear2`（render-pass clear） | 1/4 | nonzero=4096 red=4096 |
| `vk_triangle` | green=507 | green=1352 blue=2744 |
| `vk_colored_quad`（顶点色 varying） | red=1024 green=0 | red=2016 green=2080 |
| `vk_textured_quad`（UV+纹理） | blue=1024 | red/green/blue/yellow 各 1024 |

**推翻早前的“PPP 格式 1.13/1.15 不同”结论**：`0x20010002` 不是错位的 PPP 头，
而是 VDMCTRL `PDS_STATE_UPDATE`（`block_type` = bits 29-31 = 1），
Mesa 的 `PVR_DEBUG=cs` 解码器可以把整条 stream 完整解开（PPP state、
`STATE_VARYING` f32_linear=3、viewport、region clip 全部正确）。
之前 varying“丢成第一个顶点颜色”，实际是区域被裁到 32×32 后的表现。

剩余问题：

- 32×32 目标仍然只有 32×16（`vk_geom32`、`vk_clear2_32`）；
- 大于 64×64 的目标只渲染**一个 macrotile**（见下）。

### 大尺寸只画一个 macrotile —— 已修复（FACT）

用厂商 720×1600 的 golden HWRTData 对照后解决。加载带打印的
`pvrsrvkm-hwrt.ko`，跑厂商 `gles_clear 720 1600`：

```text
pvr-hwrt: ppp=063f02cf te_screen=0006302c aa=00000000 mt1=00b40000 mt2=01900000
          stride=00001194 rgn=1194 isp_mtile=002d0064 maxrts=1 tpc=131072/0 merge=0,0,0,0,0,0
```

解读（720×1600 / 16 px tile = 45×100 tile）：

| 字段 | 厂商值 | 含义 |
| --- | --- | --- |
| `te_screen` | `0006302c` | xmax=44, ymax=99（45×100 tile） |
| `mt1` / `mt2` | `00b40000` / `01900000` | x1=45, y1=100，x2/x3 = y2/y3 = 0 |
| `stride`（`ui32MTileStride`） | `1194` | 4500 = 45×100 = 整个surface的 tile 数 |
| `rgn`（`uiRgnHeaderSize`） | `1194` | 4500，每 tile 一个 header |
| `isp_mtile` | `002d0064` | x=45, y=100 |
| `tpc` | `131072` | next_pow2(100)² × 8 B |

也就是说 **1.13 把整个 surface 当成一个 macrotile**：`MTILE1.x1` = 全部
tile 数，x2/x3 为 0，`MTileStride` / `uiRgnHeaderSize` = 全部 tile 数。

修复（都按 GE8320 识别码 gate，不影响其它设备）：

- `rogue_hw_utils.h`：`rogue_get_num_macrotiles_xy()` 对 GE8320 返回 1×1；
- `pvr_arch_job_render.c`：GE8320 的 `mtile_x1/y1 = num_tiles_x/y`、
  `x2/x3 = y2/y3 = 0`、`x/y_tile_max = num_tiles - 1`；
- `pvr_rt_get_isp_region_size()`：GE8320 返回 header 计数
  `num_tiles_x * num_tiles_y`，winsys 里原来的硬编码 16 已删除。

修复后 RT 参数与厂商 golden **逐字段一致**（720×1600）：

```text
Mesa:   rgn=4500 isp_mtile=002d0064 te_screen=0006302c mt1=00b40000 mt2=01900000 stride=4500 tpc=131072
Vendor: rgn=4500 isp_mtile=002d0064 te_screen=0006302c mt1=00b40000 mt2=01900000 stride=4500 tpc=131072
```

实测（`nonzero` / 目标面积）：

| 目标 | 结果 |
| --- | --- |
| 32×32 | 1024 / 1024 |
| 64×64 | 4096 / 4096 |
| 128×128 | 16384 / 16384 |
| 256×256 | 65536 / 65536 |
| 320×480 | 153600 / 153600 |
| **720×1600** | **1152000 / 1152000** |

`vk_colored_quad`（red=2016 green=2080）、`vk_textured_quad`
（四色各 1024）、`vk_clear2`（4096 全清）、`vk_clear2_32`（1024 全清）
全部正常。

剩余可继续项：depth/stencil、blend、以及把 Mesa Vulkan 接到合成器
（wlroots Vulkan renderer）做真实桌面验证。

- 调试探针：`PVR13_RGN_R/B`、`PVR13_TERM_R/B`、`PVR13_DUMP_RT`（`PVR13_MTILE_FULL` 已删除）。



## 设备状态

手机已恢复：原 `pvrsrvkm.ko.orig` 已加载，`greetd`/`phoc` 正常。
`vk_clear_tq` 可复现整屏红；`vk_triangle` 可复现 1/4 绿三角。
