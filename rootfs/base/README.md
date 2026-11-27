# Ubuntu 24.04 / Phosh on Redmi 9A

## 目录

| 目录 | 内容 |
|---|---|
| `boot/images/` | 42 个 boot 镜像（当前基线 `boot-stable8.img`） |
| `boot/scripts/` | 打包、重签、部署脚本 |
| `boot/modules/` | AFE/audio 测试模块源码（ampen、regen、i2cgpio_dev 等） |
| `boot/assets/` | wav、dts/dtb、.ko、service/lua/conf 等部署资源 |
| `notes/` | 音频、失败记录、UI 修复笔记 |
| `audio-handover/` | 音频交接资料（寄存器对照、vendor 证据） |
| `pstore/` | 设备崩溃日志 |
| `journal/` | systemd journal 打包 |
| `units/systemd/` | 部署用 systemd unit 与配置 |
| `units/archive/` | 历史调查脚本（一次性，归档） |
| `scripts/` | 早期 rootfs 构建脚本 |
| `dist/` | 根文件系统 tarball 与依赖包 |
| `ssh-key` | 设备连接密钥（勿外传） |

> WSL 构建区 `~/dandelion-ubuntu` 已于 2026-11-23 删除（与 `dist/` 内副本逐字节一致）；需要重新打包时按 `scripts/` 里的 `get_tools.py`、`get_e2fsprogs.py`、`prepare_rootfs.py` 等重建。

## 常用

- 当前基线：`boot/images/boot-stable8.img`
- 重新打包：`boot/scripts/repack_stable8.py`（改路径后可用）
- 部署音频等：`boot/scripts/deploy_*.sh`
- 设备侧脚本与 mixer：`boot/scripts/mixer3.py`、`boot/scripts/wav_play.py`
