# pvr64 桥接层的"损耗"定位（读源码 + 查二进制）

对象：`src/pvr64/*`（桥接层）+ vendor 64 位 DDK 1.13 库
目的：找出性能/正确性损耗的真实来源，按收益排序，并给出可落地的改法。

## 结论：损耗不在 bionic 垫片，在**缓冲区与同步路径**

| 排名 | 损耗来源 | 性质 | 证据 |
| --- | --- | --- | --- |
| **1** | `glFlush()` 被替换成 `glFinish()` | 每帧强制 GPU 管线排空，CPU 阻塞 | `src/pvr64/pvr_glesv2.c:34-40` |
| **2** | 扫描输出缓冲全是 **linear DRM dumb buffer** | GPU 无法用 tiling/AFBC，带宽与填充率损失；且合成器无法直接扫描输出 | `src/pvr64/pvr_gbm.c:161-180`（`DRM_IOCTL_MODE_CREATE_DUMB`）、`pvr_gbm.c:286`（只报 `DRM_FORMAT_MOD_LINEAR`）、`pvr_egl.c:310-324`（非 0 modifier 直接拒绝） |
| **3** | 没有 `gbm_surface`（一律 `ENOSYS`） | wlroots 拿不到 EGL 交换链路径，只能 FBO→dma-buf→KMS，多一次 resolve/额外 FBO | `src/pvr64/pvr_gbm.c:382-392` |
| 4 | `bmemcp`/`bmemst` 是 32 B/轮的朴素实现 | 大块拷贝比 glibc 慢 2~4 倍（但 DDK 热路径很少走 CPU 拷贝） | `src/pvr64/bionic_compat.c:106-133` |
| 5 | mutex/cond 每次加锁多一层间接（原子读 + 一次 glibc 调用） | 数量级 ~5–10 ns/次，合成器每帧千级锁 → 微秒级，**可忽略** | `src/pvr64/bionic_compat.c:277-290` |
| 6 | EGL 转发每调用一次间接跳转 + `pthread_once` | 每帧数百次 → 微秒级，**可忽略** | `src/pvr64/pvr_egl.c:168-203` |

第 5、6 条特意列出来，是为了说明"垫片本身不背这个锅"，别把优化方向放错。

## 1) 最大的问题：`glFlush` → `glFinish`

```c
/* pvr_glesv2.c:34 */
EXPORT void glFlush(void)
{
    if (!flush_is_flush && real_finish)
        real_finish();          /* 每帧一次全管线排空 */
```

注释里写的原因是：DDK 1.13 的 dma-buf 导入路径不给 reservation object 挂 fence，KMS 不会隐式等待，所以用 `glFinish` 当"同步屏障"。

**但 DDK 本身是有 fence 能力的**（FACT）：
- `libIMGegl.so` 的扩展串包含 `EGL_ANDROID_native_fence_sync`、`EGL_KHR_fence_sync`、`EGL_KHR_wait_sync`
- `libIMGegl.so` 导出 `eglCreateSyncKHR`、`eglDupNativeFenceFDANDROID`
- `libsrv_um.so` 导出 `PVRSRVFenceExportI` / `PVRSRVFenceDupExt` / `PVRSRVFenceWaitExt`

也就是说：**能拿到 sync_file fd**，只是桥接层没用。正确做法有两条：

- **A（彻底）**：`glFlush` 恢复成真 flush；随后 `eglCreateSyncKHR(dpy, EGL_SYNC_NATIVE_FENCE_ANDROID, NULL)` + `eglDupNativeFenceFDANDROID()` 拿 fd，交给 wlroots 在 atomic commit 时用 `IN_FENCE_FD` 属性。KMS 等 GPU，CPU 不阻塞。需要给 wlroots 打一个小补丁（把 fence fd 挂到 `drmModeAtomicAddProperty(..., "IN_FENCE_FD", ...)`）。
- **B（不改 wlroots）**：**延迟一帧等待**。桥接层保存上一帧的 fence，只在"同一 buffer 被复用"或下一帧开始时 `eglClientWaitSyncKHR(prev_fence, 0, 0)`。代价从"每帧排空"降到"等上一帧已经做完的事"，多数情况下不阻塞。

预期收益：合成器帧率与输入延迟改善，CPU 不再被 5–10 ms 级别的 GPU 排空卡住。

## 2) 第二大的问题：全 linear + dumb buffer

`gbm_bo_create()` 走 `DRM_IOCTL_MODE_CREATE_DUMB`：
- MTK DRM 的 dumb buffer 是**线性**的，没有 PowerVR 的 twiddled 布局，也没有 AFBC；
- `eglQueryDmaBufModifiersEXT` 只报 `DRM_FORMAT_MOD_LINEAR`，`eglCreateImageKHR` 遇到非 0 modifier 直接 `EGL_BAD_MATCH`；
- 结果：GPU 全程渲染到线性内存（PBE 写线性、采样线性纹理），**带宽/填充率天然吃亏**；合成器也无法走 direct scanout 优化。

而 vendor 侧其实有带 tiling/压缩的分配器（FACT）：
- `hw/gralloc.rogue.so` 导出 `MTKGenericAlloc`，且内部字符串含 `FBCSurface num tiles`（帧缓冲压缩）
- 说明 MTK 的分配路径是支持压缩/分块的，只是当前的 `libgbm` 没用它

可行路线（按风险从低到高）：
1. **先用 dma-heap 替换 dumb buffer**（`/dev/dma_heap/system`），拿真正的 dma-buf，至少去掉 dumb 的额外限制；tiling 仍然没有。
2. **反汇编 `MTKGenericAlloc`**，还原它的参数/返回结构，直接在 `libgbm` 里调用，让 `gralloc.rogue.so` 负责分配（它知道 tiling/压缩格式），再把 dmabuf fd 交给 KMS/EGL。这是收益最大、也最"钻研源码"的一步。
3. 把 `eglQueryDmaBufModifiersEXT`/`eglCreateImageKHR` 的"只接受 LINEAR"放开到 gralloc 实际返回的 modifier。

## 3) `gbm_surface` 直接 `ENOSYS`

wlroots 0.17 的 DRM 后端在 gles2 渲染器下优先要 `gbm_surface_create()` 拿 EGL 交换链；现在返回 `ENOSYS`，只能退回"FBO + dma-buf 导入导出"的路径，每帧多一次 EGLImage 创建/销毁与可能的 resolve。

如果第 2 步的分配器做出来了，`gbm_surface` 可以基于同一个分配器实现（Android 的 `gralloc.gbm` 就是这么干的），从而恢复零拷贝交换链。

## 4) 垫片的 CPU 微优化（可选，收益小）

- `bmemcp`/`bmemst` 改成 128 B/轮的 `ldp/stp`（或 NEON `ld1/st1`），保持"不用 `dc zva`"的约束即可，能从 ~32 B/轮提升到接近 glibc；
- mutex 不建议重写成 futex（收益 <1%，但正确性风险高，你现在这套已经验证过）。

## 测量建议（先量再改）

- 用 `perf stat -e cycles,instructions` 与 `perf record` 看 phoc 的 CPU 时间分布；
- 用 `ftrace` 的 `drm:` 事件看每帧 commit 的时序（`/sys/kernel/debug/tracing/events/drm`）；
- 跑 `glmark2-es2-wayland` 或 `es2gears_wayland` 拿 fps 基线，再对比改完后的数字；
- 用 `PVR_GL_FLUSH_IS_FLUSH=1` 跑一次对比：如果帧率明显变化，说明第 1 条就是主因。
