# WSL home 主线相关整理记录（2026-11-23）

处理结果：

- 散落小件已归档到 Windows：`C:\Users\31806\Documents\AI_Project\Redmi_9A\silex-linux-dandelion\archive\wsl-archive\`（13 MB）
- 主线源码已移动到：`~/AI Project/Redmi 9A/kernel 7.1 mainline`（目录本身就是内核树根）
- 旧路径 `~/dandelion-linux-kernel/03-mainline-7.1` 已不存在

## 归档内容（wsl-archive）

| 目录 | 内容 | 体积 |
|---|---|---:|
| `dts/` | r96 系列 dts/dtb、bl2chk.dts、vendor.dts、vendor-dtb、r96-gpu.dts.bak-cma | 1.1 MB |
| `initramfs/` | `initramfs-busybox/`、`initramfs-busybox.cpio.gz` | 2.7 MB |
| `gpu-bringup/` | 树内 GPU 文档（已归档） | 88 KB |
| `rootfs-alpine/` | GPU userspace chroot | 8.3 MB |
| `backups/` | `build-boot-r26.sh`、`GPU_BRINGUP.md`、3 个 `.before/.bak` 备份 | 0.2 MB |

## 源码树状态

| 项 | 值 |
|---|---|
| 路径 | `~/AI Project/Redmi 9A/kernel 7.1 mainline` |
| 体积 | 2.4 GB（`.git` 591 MB） |
| HEAD | `09afeff6c gpu-bringup:` |
| 未提交 | 36 项（原 21 项工作改动 + 归档导致的 15 项删除） |

未提交的 15 项删除是 `gpu-bringup/` 和 `GPU_BRINGUP.md`（已归档），需要时可在新树里 `git checkout -- gpu-bringup GPU_BRINGUP.md` 恢复。

## 保留在 `~/dandelion-linux-kernel/`

- `01-pure-baseline` 1.2 GB
- `02-kernelsu` 1.3 GB
- `03-pure-variant` 3.8 GB
- `04-debug` 1.8 GB
- `dandelion-7.1.config` 205 KB（与 Windows `configs/` md5 一致）

## 其他未动

- `~/j`、`~/j2`、`~/dandelion-ubuntu`、`~/dandelion-linux-kernel/` 已于 2026-11-23 删除（均与项目内副本逐字节校验一致，见下）
- 删除前校验：`~/j`/`~/j2` 与 `ubuntu/journal/*.tgz` 内容一致；`dandelion-7.1.config` 与 `configs/` 一致；`dandelion-ubuntu` 的 tarball、`enter.sh`/`install-p41.sh`/`pack_rootfs.sh`、`sources.list` 与项目内副本一致
- `~/dandelion-ubuntu/install.log` 已保存为 `ubuntu/dist/install-rootfs-20261121.log`
- `~/pixelos-build` 已不在 home（用户已整理）
- 非主线项目：`kernel-oc` 3.3 GB、`alpican-gpu` 1.1 GB + tar 191 MB、`alpican-kernel-gpu` 34 MB、`alpican-gist`、`gist.json`、`ali-cloud` 1.1 GB、`ck`、`io_uring_*`、`io_backup_4.19`、`projects/minishell`
- `~/kport` 1.8 GB：与 `~/AI Project/Redmi 9A/kernel 4.19.325 purity` 同一 HEAD / remote 的 4.19 重复克隆（干净，可删）
