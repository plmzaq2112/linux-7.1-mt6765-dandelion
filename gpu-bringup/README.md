# PowerVR GE8320 (Redmi 9A / MT6762G) on mainline Linux 7.1 — bring-up notes, help wanted

**TL;DR** — I ported the vendor PowerVR DDK 1.13 (Rogue, BVNC 22.87.104.18) to a mainline 7.1 kernel on the
Xiaomi Redmi 9A (dandelion, MT6762G). The MIPS firmware boots, KCCB works, power-state requests are executed,
and `/dev/dri/renderD129` now **opens successfully** using a small set of controlled workarounds.
**What is still missing:** the firmware never writes the power-sync primitive (or the KCCB return slot),
and it only processes POW commands intermittently. I'm looking for someone with PowerVR Rogue
firmware/MTS knowledge to help close this.

---

## 1. Hardware / software

| Item | Value |
|---|---|
| Device | Xiaomi Redmi 9A (dandelion), MT6762G |
| GPU | PowerVR GE8320 (Rogue), BVNC **22.87.104.18** |
| GPU regs | `0x13000000` + `0x80000` |
| MFG clock ctrl | `0x13ffe000` |
| SPM | `0x10006000` |
| IRQ | GIC SPI 259 (LEVEL_LOW) |
| Kernel | mainline **7.1.0** (arm64), Alpine userland |
| DDK | Imagination **1.13 (ED5776728)**, out-of-tree under `drivers/misc/pvr/ddk` |
| Firmware | stock `rgx.sh`, 309200 bytes, md5 `6456299eddd62b1834f71e81b4d6bb67` |
| Stock base | vendor 4.19.127 + DDK 1.13 (verified via vendor module vermagic) |

The firmware and DDK generation match the stock ROM, so this is **not** a firmware/DDK version mismatch.

## 2. What works (verified on device)

- GPU register block, CORE_ID `0x08470000`, REVISION `0x00680012`
- MFG clocks (mfg / mfgpll), clock gating, MFG MTCMOS domains (MFG / MFG_CORE0 / MFG_ASYNC all on)
- MIPS firmware boot: `bFirmwareStarted`, `EXC_STATUS=0x20` (same idle state as the stock ROM)
- FW connection: `FW_ACTIVE` / `OS_ACTIVE`, KCCB 72-byte commands, 128 slots
- KCCB command submission: the FW consumes commands (`r` advances, `kcmds` increments)
- POW requests: the FW changes `ePowState` (ON → IDLE → FORCED_IDLE, and POW_OFF → OFF)
- **`/dev/dri/renderD129` opens successfully** with the workaround config below

## 3. What is broken (the actual blocker)

The firmware **never writes the power-sync primitive** (`RGXFWIF_OSDATA::sPowerSync`, FW VA `0xc0019000`),
and it never writes the KCCB return slot either. I verified:

- command ABI is correct (72 B, uCmdData offset 8, POW payload 8 B, values match the mainline layout)
- GPU page table entries / host physical addresses / cache attributes all match
- `MTS_SCHEDULE` doorbell value and write sequence match the vendor DDK
- the host-side `RGXForcedIdleRequest` is byte-identical to the vendor 4.19 DDK except diagnostics
- MTCMOS is already powered by genpd/bootloader (my explicit vendor sequence is a no-op)
- all FW configuration fields match a working stock ROM dump
  (`ui32ConfigFlags=0x00020030`, OS flags `0x7`, PM latency 3 ms, HWR OK)

Additionally, POW command processing is **intermittent**: sometimes the FW consumes the command after
30–90 s and transitions the power state, sometimes it ignores it entirely until timeout.

The IRQ path had a separate bug (one IRQ ever; host counter never caught up because the FW updates its
counter after raising the, level-triggered, interrupt). That is now worked around (see patches).

## 4. Known-good workaround configuration (open works)

```
insmod pvrsrvkm.ko pvr_apm=2 pvr_os_active=1 pvr_no_sync=1 pvr_pow_off=1
```

- `pvr_apm=2`: program MTK APM dust registers `0x504–0x528` only (skip the `0x24` sequence that can
  power-gate MFG_CORE0)
- `pvr_os_active=1`: force the OS connection state to ACTIVE before POW
- `pvr_pow_off=1`: send `POW_OFF_REQ` instead of `FORCED_IDLE_REQ`
- `pvr_no_sync=1`: treat the (never-written) prim timeout as completion

With this, `open("/dev/dri/renderD129")` succeeds and the driver stays stable.
This is a **diagnostic workaround**, not an upstream-quality fix.

## 5. Things that were tried and ruled out

| Hypothesis | Result |
|---|---|
| Wrong command ABI | ruled out (measured) |
| Invalid/mismatched GPU page tables | ruled out (PTE audit) |
| Wrong cache attributes (host or FW side) | ruled out (PTE + PA + write-combine semantics) |
| MTCMOS not powered / wrong order | ruled out (vendor sequence executes, registers identical) |
| Only POW_OFF gets an ack | ruled out (neither FORCED_IDLE nor POW_OFF writes the prim) |
| Return-slot completion | ruled out (rtn slot stays 0) |
| Level IRQ not cleared | fixed (LISR returns handled; clear path verified) |
| FW/DDK version mismatch | ruled out (stock FW md5 identical, DDK 1.13 matches 4.19.127 base) |
| FW trace can tell us where it stops | impossible: production firmware emits no trace (stock ROM dump also says "log type: none") |

## 6. Help wanted

1. **PowerVR Rogue firmware internals**: why would the FW process a POW command, change `ePowState`,
   but not update `sPowerSync` / the KCCB rtn slot? Any pointers to the FW power-state machine,
   MTS scheduling, or `RGXFWIF_OSDATA` usage would help.
2. **MTK MTS / APM interaction**: the MTK "RascalDust" APM path (`INICFG_POW_RASCALDUST`) may gate the
   firmware's completion path; experience with vendor `ged`/`gpufreq` would help.
3. **Userspace**: with the vendor kernel driver there is no usable userland on Alpine
   (vendor UM libs are bionic-only; Mesa's `powervr` driver targets the upstream `drm/imagination`, not this
   driver). Ideas for a minimal test path are welcome.

## 7. This repository

This repository **is** the kernel source: mainline **7.1** for MT6765 / Redmi 9A,
branch **`dandelion-7.1`**. It is based on `evilMyQueen/linux-mt6765`.

GPU bring-up material lives in **`gpu-bringup/`**; the actual driver changes are in
`drivers/misc/pvr/ddk/` (plus one panel driver fix).

## 8. Layout

```
gpu-bringup/README.md        this document
gpu-bringup/README.zh-CN.md  Chinese version
gpu-bringup/docs/STATUS.md   detailed technical status
gpu-bringup/docs/TIMELINE.md chronological experiment log (facts only)
gpu-bringup/ddk-patches/         diffs against the vendor DDK 1.13 sources
gpu-bringup/logs/open-ok.txt sanitized kernel log of a successful open
```

## 9. Disclaimer

Everything here is experimental. The workarounds deliberately bypass firmware handshakes that the driver
expects to be honoured; use at your own risk. No warranty, no support for other devices.

## 10. License

The patches follow the licensing of the vendor DDK sources (dual MIT / GPLv2); the added code is GPL-2.0.
Logs and documentation are provided under CC BY-SA 4.0.
