# linux-gpu —— Linux 侧图形栈资料索引

当前状态（2026-11-24）：**路线 A（TI glibc UM + BVNC 补丁）已实机证伪并关闭**；当前主线是**路线 C：继续优化现有 `src/pvr64` 方案**。

## 看哪份

| 文件 | 用途 |
| --- | --- |
| **`纯原生方案评估.md`** | **主文档**：四条路线的证据、结论与 C 的执行计划（先看这个） |
| `NATIVE-PLAN.md` | 路线 A 的方案草稿（已过时，仅留档） |
| `install-pvr-um.sh` | 把 TI glibc 包安装到 `/opt/pvr`（路线 A 用，现已不用） |
| `patch-ti-um-bvnc.py` | 路线 A 的 BVNC 补丁脚本（历史） |
| `native-check.sh` | 设备端自检：节点 / glibc / `eglinfo` / `gles2test1` / `dmesg`（任何 UM 栈都可复用） |

## 路线 A 为什么关闭（一句话）

三道门：BVNC 校验 → UM 编译期特性表 → **FW/UM 结构体对齐**（`RGXFWIF_CMD3D`：TI UM 352 B vs 本机固件 320 B）。
第三道是编译期 ABI，运行时无法修补。详见 `../notes/failures.md` F-001。

## 下一步

按 `纯原生方案评估.md` §4 执行：
1. 先做 5 分钟 A/B（`PVR_GL_FLUSH_IS_FLUSH=1`）定位瓶颈
2. C1：`glFinish` → native fence
3. C2：buffer 路径（dma-heap / tiling）
