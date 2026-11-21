# [Help] PowerVR GE8320 on mainline Linux 7.1 — firmware never acks POW, render node opens but I'm stuck

Device: **Xiaomi Redmi 9A (dandelion, MT6762G, PowerVR GE8320, BVNC 22.87.104.18)**
Kernel: mainline **7.1.0** (arm64) + vendor PowerVR DDK **1.13 (ED5776728)**, Alpine userland.

## Status

✅ MIPS firmware boots (same `EXC_STATUS=0x20` idle state as the stock ROM)
✅ KCCB works (72-byte commands, 128 slots), firmware consumes commands
✅ POW requests change `ePowState` (ON → IDLE → FORCED_IDLE, POW_OFF → OFF)
✅ `/dev/dri/renderD129` **opens successfully** with a workaround config
❌ firmware **never writes** the power-sync primitive (`sPowerSync`) nor the KCCB return slot

## What I already ruled out

- Command ABI (measured: 72 B, `uCmdData` offset 8, POW payload 8 B)
- GPU page tables / physical addresses / cache attributes (PTE audit)
- Host POW code (identical to the vendor 4.19 DDK, diagnostics aside)
- MTCMOS (the three MFG domains are already powered; vendor sequence is a no-op)
- Firmware configuration (matches a working stock ROM dump: `cfg=0x00020030`, OS flags `0x7`,
  PM latency 3 ms, HWR OK)
- Firmware/DDK version mismatch (stock `rgx.sh` md5 identical, DDK 1.13 matches the 4.19.127 base)
- Firmware trace (production FW emits none; stock dump says "log type: none")

Extra oddity: POW handling is **intermittent** — sometimes the firmware reacts after 30–90 s,
sometimes it ignores the command until timeout.

## Working (diagnostic) configuration

```
insmod pvrsrvkm.ko pvr_apm=2 pvr_os_active=1 pvr_no_sync=1 pvr_pow_off=1
```

`pvr_apm=2` = APM dust regs only, `pvr_os_active=1` = force OS state ACTIVE,
`pvr_pow_off=1` = send POW_OFF instead of FORCED_IDLE, `pvr_no_sync=1` = accept the never-written prim timeout.

## Questions for the PowerVR/MTK folks

1. Why would Rogue firmware execute a POW command, update `ePowState`, but not write `sPowerSync`
   (or the rtn slot)? What gates that write in the FW power-state machine?
2. Could the MTK "RascalDust" APM path (`INICFG_POW_RASCALDUST`) stall the completion branch?
3. Is there any other host-visible completion the stock 4.19 driver could be relying on?

Kernel source + docs + patches (single repository, branch `dandelion-7.1`):
**https://github.com/plmzaq2112/linux-7.1-mt6765-dandelion/tree/dandelion-7.1**
(the write-up is in `gpu-bringup/README.md` inside the tree)

Everything is experimental; the workarounds bypass firmware handshakes the driver expects.
