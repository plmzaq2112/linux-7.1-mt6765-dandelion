# 全量 dump UM/FW 对齐表（研究用）

目的：内核目前只打印**失配**项（如 `[21]`）。要判断"两套 UM 的 ABI 到底差多少"，需要一次拿到 44 项完整对照。

索引含义见 `aligncheck-index.txt`（由 `aligncheck-index.py` 解析 `rgx_fwif_alignchecks.h` 生成，共 44 项）。

## 改法（`rgxinit.c`，`RGXAlignmentCheck`）

找到这段（约 1860 行，特征是 `RGXFW_ALIGN_CHECKS_INIT[%d]`）：

```c
	for (i = 0; i < ui32AlignChecksSizeUM; i++)
	{
		if (aui32AlignChecksUM[i] != paui32FWAlignChecks[i])
		{
			PVR_DPF((PVR_DBG_ERROR, "%s: size/offset mismatch in RGXFW_ALIGN_CHECKS_INIT[%d]"
					" between UM(%d) and FW(%d)",
					__func__, i, aui32AlignChecksUM[i], paui32FWAlignChecks[i]));
			eError = PVRSRV_ERROR_INVALID_ALIGNMENT;
		}
	}
```

在它**之后**插入（原有的 mismatch 打印保留）：

```c
	if (eError == PVRSRV_ERROR_INVALID_ALIGNMENT)
	{
		PVR_DPF((PVR_DBG_ERROR, "=== RGXFW_ALIGN_CHECKS full dump (UM vs FW) ==="));
		for (i = 0; i < ui32AlignChecksSizeUM; i++)
		{
			PVR_DPF((PVR_DBG_ERROR, "ALIGN[%02d] UM=%-6u FW=%-6u %s",
					i,
					(IMG_UINT32)aui32AlignChecksUM[i],
					(IMG_UINT32)paui32FWAlignChecks[i],
					(aui32AlignChecksUM[i] != paui32FWAlignChecks[i]) ? "<-- DIFF" : ""));
		}
	}
```

## 使用

1. 重新编译 `pvrsrvkm.ko`，按路线 A 的方式装上 TI 的 UM（补丁版）触发失配；
2. `dmesg | grep -E 'ALIGN\[' > align.txt`；
3. 对照 `aligncheck-index.txt` 看差异集中在哪几个结构体。

## 判读

| 现象 | 含义 | 下一步 |
| --- | --- | --- |
| 只有 `[19]`~`[26]`（CMDTA/CMD3D/CMDTRANSFER/CMD_COMPUTE 等）不同 | 差异局限在 3D/几何命令包，且很可能是编译期数组上限 | 值得做"计数式解析"实验（见下） |
| 散布在 TRACEBUF/SYSDATA/OSDATA/HWRINFOBUF 等多处 | 配置差异面很大 | 止损，回到路线 C |
| 覆盖几乎全部 44 项 | 两套 UM 构建配置差异过大 | 放弃移植思路 |

## 后续实验（若差异只在命令包）

关键问题：`RGXFWIF_CMD3D` 是 `{header, count, regs[]}` 还是定长块？

- 若是**计数驱动**：352 与 320 只是编译期上限不同，实际包同构 → 骗过校验后可能直接能跑（实验：把 UM 的 `aui32AlignChecksUM[21]` 值改成 320，或 KM 里跳过该检查）。
- 若是**定长块**：多出的 32 B 会被固件当成后续数据，必然错位 → 放弃。

验证方法（纯静态，不上机）：反汇编 MTK UM（320）与 TI UM（352）中构造 CM3D 的函数，比较写入长度是常量还是从计数字段取值。
