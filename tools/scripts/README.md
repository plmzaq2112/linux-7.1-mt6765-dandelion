# scripts/

通用辅助脚本与诊断探针。

## 布局

| 路径 | 说明 |
| --- | --- |
| `scripts/probes/` | 设备端诊断/一次性探针（`device_*.sh` 等），保留用于复现 |
| `scripts/win/` | **已迁移**到 `installer/windows/` |
| `src/wayland/` | Wayland/合成器源码与构建脚本（`vk_wl`、`vk_comp`、`wl/`） |
| `tests/device/` | smoke/回归验证脚本 |
| `installer/linux/` | build-boot/打包/刷写相关脚本 |

## 常用入口

- Wayland 构建：`src/wayland/build_vk_wl.sh`
- 设备综合验证：`tests/device/device_verify_all.sh`
- Wayland 测试：`tests/device/device_wl_test.sh`、`device_wl_dmabuf.sh`、`device_wl_idle.sh`、`device_wl_kbd.sh`

> 说明：重构后部分脚本内的硬编码路径可能仍指向旧位置；运行前检查脚本头部变量与路径。