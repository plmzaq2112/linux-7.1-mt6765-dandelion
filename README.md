# Redmi 9A — kernel 7.1 mainline

主线 7.1 内核移植 + Ubuntu (Phosh) 根文件系统 + Mesa PowerVR Vulkan / Wayland 合成器的项目工作区。
内核源码本体在 WSL：`~/AI_Project/Redmi_9A/kernel_7.1_mainline`（独立 git 树）。

## 目录结构

| 目录 | 内容 |
|---|---|
| `kernel/` | `configs/` 内核配置、`patches/` 补丁快照、`modules/` 树外模块源码 |
| `device/dandelion/` | 设备声明：dts/audio/firmware.manifest/deviceinfo（骨架） |
| `rootfs/` | `ubuntu/`（packages/overlay/build 脚本骨架）、`rescue/` |
| `src/` | 自研源码：`pvr64/`、`wayland/`（vk_wl/vk_kms2 等） |
| `installer/` | `linux/` 构建/刷写脚本、`windows/` 串口/Windows 工具 |
| `tests/` | `device/` 真机 smoke/回归，另有诊断探针在 `scripts/probes/` |
| `releases/` | 版本清单、校验和、变更日志（骨架） |
| `docs/` | `STATUS.md`、`FLASHING.md`、`porting/`、`audits/`、`项目构思.txt` |
| `scripts/` | 通用辅助脚本、`probes/` 诊断探针 |
| `data/` | 静态数据：`dts/`、`fw/`、`keys/`、`assets/`、`backups/`（私钥不入库） |
| `dist/` | 构建产物（gitignored） |
| `logs/` | 运行/诊断日志（gitignored） |
| `archive/` | 历史归档 |
| `artifacts/` | 设备端二进制/运行时归档 |
| `ubuntu/` | Ubuntu rootfs 历史资料/notes 迁移后的剩余内容（逐步收敛到 `rootfs/ubuntu/`） |

## 常用

```bash
make help     # 查看命令
make check    # bash -n 检查所有 shell 脚本
```

## 当前状态（FACT，2026-11-26）

> 详细状态见 **`docs/STATUS.md`**；全项目技术存档见 **`docs/porting/PROJECT-ARCHIVE.md`**；
> 合成器/Wayland 见 **`docs/porting/COMPOSITOR-PORT.md`**。

- 设备：Redmi 9A dandelion / MT6762G / PowerVR GE8320（BVNC 22.87.104.18）/ DDK 1.13@5776728
- 内核：主线 7.1（WSL `~/AI_Project/Redmi_9A/kernel_7.1_mainline`），配置 `kernel/kernel/configs/dandelion-7.1.config`
- 显示/触摸/音频/充电基础：已工作（见 `docs/STATUS.md`）
- GPU：`pvrsrvkm.ko` + Mesa Vulkan（PowerVR）可运行；绘制、depth/blend、纹理、几何尺寸通过回归
- 零拷贝合成：`vk_kms2` 连续 DRM dumb buffer → Vulkan 渲染 → KMS 扫描，720×1600 @ 58.4 fps（vsync）
- 多层合成器：`vk_comp`，8/16 层 alpha/scissor，58.4 fps
- Wayland 合成器：`vk_wl`（`wl_compositor`/`wl_shm`/`xdg_wm_base`/`wl_seat` pointer+keyboard/`wl_output`/`zwp_linux_dmabuf_v1`）
  - shm BGRA→RGBA 上传、单平面 LINEAR dma-buf 导入、damage 裁剪上传 + per-slot 累积 + 局部重绘、空闲停刷
  - keyboard：evdev + 内嵌 us xkb keymap，uinput 端到端验证通过（FACT）
- 已知差距：3D 全屏 720×1600 约 3.05 ms vs 厂商 1.96 ms（HYPOTHESIS：仍有 GPU 侧开销）；Wayland 无 popup/drag-data/tiled modifier；未跑真实终端/GTK 客户端

## 下一步建议

1. 用真实 Wayland 客户端（foot/GTK 等）验证 keyboard、dma-buf、damage 行为；缺客户端时先交叉编译最小客户端。
2. 补 Wayland 缺口：按需 `wl_data_device`/剪贴板、popup 约束、更多 buffer 格式（在 Mesa PVR 能力范围内）。
3. 继续 GPU 性能：定位 3.05 ms vs 1.96 ms 的剩余差距（保持 FACT/HYPOTHESIS 分级）。
4. 系统侧：USB Host VBUS、热管理、挂起/唤醒 PM 审计、音频收尾（见 `docs/STATUS.md`）。

## 归档

- `docs/porting/PROJECT-ARCHIVE.md`：全项目技术存档（权威）
- `docs/porting/COMPOSITOR-PORT.md`：合成器/Wayland 细节与验证记录
- `kernel/patches/`：Mesa/内核补丁快照
- `archive/REORG-20261123.tsv`：标准化旧→新路径映射
