# Experiment timeline (facts only)

Chronological log of what was tried on the device. "Excluded" means the hypothesis was disproved by
measurement, not by reasoning alone.

## 2026-11-19 — DDK port basics

- DDK 1.13 builds as an out-of-tree module against mainline 7.1 (`CONFIG_DRM_PVR_LEGACY=m`).
- DRM device registers (`[drm] Initialized pvr 1.13.5776728 for 13000000.mfg_doma`).
- `PVRSRVDeviceOpen` fails: firmware does not start.

## 2026-11-20 — firmware boot

- Found the GPU is **MIPS**, not META (feature word bit 17).
- `SUPPORT_MIPS_CONTIGUOUS_FW_MEMORY` (64K pages) makes the MIPS core take an exception; **4K pages required**.
- Platform layer must **not** program the MTK APM `0x24` sequence (`pvr_apm=0`), otherwise MFG_CORE0 is gated.
- Firmware now boots: `bFirmwareStarted`, `EXC_STATUS=0x20`, connection `FW_ACTIVE`/`OS_ACTIVE`,
  clock 390 MHz, syscfg `0x00020030` identical to the stock ROM.
- Firmware boot remains intermittent (`boot stage=0`).

## 2026-11-20 — POW investigation

- Command ABI verified: 72 B, `uCmdData` offset 8, POW payload 8 B, `eCmdType=0x2abc006b`
  (107 | magic), `powtype=2`, `req=1`.
- GPU page table audited (PT base `0x42c10000`, FW VA base `0xC0000000`):
  KCCB ctl, pow prim, KCCB buffer PTEs all valid; PTEs match host physical addresses.
- Return slot never written; prim never written.
- FW trace buffer allocated and enabled before FW start — firmware writes nothing;
  the stock ROM dump also reports `Debug log type: none`.

## 2026-11-21 — MTCMOS / APM / clock experiments

- Ported the vendor `clk-mt6765-pg.c` MFG MTCMOS sequence (async → mfg → bus-protect → core0).
  It executes, but every register reads back identical to the idle state → domains were already on. **Excluded.**
- APM dust-only (`0x504..0x528`, no `0x24`): firmware can reach `pow=2` (FORCED_IDLE),
  but still no prim. Partially effective.
- `POW_OFF_REQ` instead of `FORCED_IDLE_REQ`: firmware reaches `pow=0` (OFF) in some runs, still no prim.
- Clearing `INICFG_POW_RASCALDUST` (`pvr_no_apm=1`): firmware boots already OFF, finalise fails earlier.
  Combination unusable.
- Core clock alignment (400 MHz instead of 390 MHz): no change. **Excluded.**

## 2026-11-21 — IRQ path

- LISR instrumented: exactly one interrupt, `mips_st=1` at entry, `sample_processed=0`.
- Root cause: the firmware raises the level IRQ before updating its interrupt counter;
  the LISR samples too early, and no second IRQ is raised.
- Fixes: return `IMG_TRUE` when the event was acked, clear `aui32SampleIRQCount` at FW start,
  and re-check host/FW counts after the DDK's timeout handler.

## 2026-11-21 — open milestone

```
pvr_apm=2 pvr_os_active=1 pvr_no_sync=1 pvr_pow_off=1
→ open("/dev/dri/renderD129") = 0
```

The process then blocks in `drm_read` (expected for a render node with no events), confirming that
open returned successfully.

## Not yet done

- Any real GPU work submission (no usable userspace for this kernel driver).
- Understanding the firmware's power-state machine completion path.
