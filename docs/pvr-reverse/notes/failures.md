# 失败记录

## F-001：TI glibc UM + BVNC 补丁（路线 A）—— 证伪，关闭

- 日期：2026-11-24
- 假设：TI 的 glibc 版 DDK 1.13 用户态与设备内核驱动同版本、同 bridge ABI，只要把 UM 里的 BVNC 期望值改成 GE8320，就能零垫片运行。
- 操作：`patch-ti-um-bvnc.py` 改 `CompatibilityCheck` 3 条指令 → 再补 UM 的 `gaFeatures`/`gaErnsBrns` 两张表（从 MTK 同版本 UM 抄两条 56 B 表项）。
- 结果（实机，三道门依次拦截）：

  | 关卡 | 现象 | 性质 |
  | --- | --- | --- |
  | 1. `CompatibilityCheck` | `PVRSRV_ERROR_BVNC_MISMATCH` → 改为 `PVRSRV_ERROR_BVNC_UNSUPPORTED` | 可绕（表项补齐后通过） |
  | 2. UM 侧特性/勘误表 | `libsrv_um.so` 内 `0x59a18`/`0x5a0b0` 两张编译期表只含 15/18 个目标核 | 可绕（补入 22.87.104.18 两条表项后通过） |
  | 3. FW/UM 结构体对齐 | `RGXAlignmentCheck: size/offset mismatch in RGXFW_ALIGN_CHECKS_INIT[21] between UM(352) and FW(320)` | **硬阻塞** |

- 根因：`rgx_fwif_alignchecks.h:90-92` 的索引 [21] 是 `sizeof(RGXFWIF_CMD3D)` / `offsetof(..., s3DRegs)`。
  TI UM 按 22.104.208.318 编译得到 352 B，本机 GE8320 固件期望 320 B —— `s3DRegs` 的寄存器数组长度由 BVNC 决定，属编译期 ABI。
  该校验由内核 `rgxinit.c:1865` 强制执行，运行时无法修补。
- 结论：**"UM 与 BVNC 无关"不成立**。BVNC 依赖不在字符串/常量里，而在**结构体尺寸与寄存器表长度**里。
  路线 A 关闭；设备端已清理 `/opt/pvr`。
- 方法论教训：用"扫描常量/字符串"证明"库与 BVNC 无关"是不可靠的；必须做结构体尺寸/ABI 级验证（本次由内核的 align check 直接给出答案）。
- 后续选择：路线 C（现有正确 BVNC 的 UM + 性能优化）；路线 B（libhybris）仅在需要去掉 ABI 垫片时考虑。
