# Technical status (detailed)

All statements below are either measured on the device (FACT) or explicitly marked as hypothesis.

## 1. Platform

- SoC: MT6762G (MT6765 family), GPU PowerVR GE8320, BVNC 22.87.104.18
- GPU register window `0x13000000..0x137fffff`
- MFG clock controller `0x13ffe000` (CG: SET `0x04` = gate off, CLR `0x08` = enable)
- SPM `0x10006000`: PWR_STATUS `0x180`, PWR_STATUS_2ND `0x184`,
  MFG_ASYNC_PWR_CON `0x334`, MFG_PWR_CON `0x338`, MFG_CORE0_PWR_CON `0x34c`
- INFRA `0x10001000`: TOPAXI protect `0x220`, SET `0x2a0`, CLR `0x2a4`, STA1 `0x228`
- GPU IRQ: GIC SPI 259, level low (`/proc/interrupts` shows `MT_SYSIRQ 259 pvrsrvkm`)

Measured idle state: `PWR_STATUS=0x068fdffd` (MFG=1, CORE0=1, ASYNC=1),
`TOPAXI=0x98`, `MFG_CON=0x0e0d`, `CORE0_CON=0x0e0d`, `ASYNC_CON=0x0f0d`.

## 2. Firmware

- File: `rgx.sh`, 309200 bytes, md5 `6456299eddd62b1834f71e81b4d6bb67` (identical to the stock vendor image)
- MIPS core (not META): `META_sup=0`, `MIPS_sup=1`
- After boot: `EXC_STATUS=0x20` (SI_SLEEP) — same idle value as the stock ROM
- FW shared structures: KCCB ctl `0xc0018880`, KCCB `0xc001a000`, pow prim `0xc0019000`,
  OSData `0xc0018b00`, command size 72 B, 128 slots

## 3. Verified equal to a working stock ROM

| Field | Stock ROM dump | This port |
|---|---|---|
| `ui32ConfigFlags` | `0x00020030` | `0x00020030` |
| `ui32FwOsConfigFlags` | `0x7` | `0x7` |
| HWR state | `0x1` (OK) | `0x1` |
| PM latency | 3 ms | 3 ms |
| connection | FW active / OS active | FW active / OS active |

The stock dump also reports `RGX FW Power State: RGXFWIF_POW_IDLE` and
`APM disabled ... Latency: 3 ms`.

## 4. POW path — what the firmware actually does

Observed sequences (all with the vendor DDK 1.13 command layout):

```
FORCED_IDLE_REQ:
  entry pow=1
  send  -> kccb w=1
  (+10s)  pow=3 (IDLE)      sometimes
  (+30s)  kcmds=1, r=1      sometimes
  (+…)    pow=2 (FORCED_IDLE) sometimes
  sync prim = 0 always, rtn slot = 0 always

POW_OFF_REQ:
  send -> kccb w=1
  pow=0 (OFF) in some runs, pow=3 in others
  sync prim = 0 always, rtn slot = 0 always
```

The firmware **never** writes the completion primitive and never writes the return slot,
even when it changes `ePowState`.

## 5. IRQ path

- `/proc/interrupts` shows a single interrupt for the whole session
- LISR instrumented: entry `EVENT_STATUS=0`, `MIPS_WRAPPER_IRQ_ENABLE=1`, `MIPS_WRAPPER_IRQ_STATUS=1`
- `SampleIRQCount()` returned “no change” because the FW had not yet updated its counter
- The DDK's timeout handler later re-samples and catches up, but the caller kept the old error
- Fix: re-check host/FW counts after the timeout handler and clear the stale error

## 6. What the workarounds do

| Param | Effect |
|---|---|
| `pvr_apm=2` | write APM dust registers `0x504..0x528` only (the `0x24` sequence can power-gate MFG_CORE0) |
| `pvr_os_active=1` | force OS connection state ACTIVE right before POW |
| `pvr_pow_off=1` | send `POW_OFF_REQ` (type 1, forced) instead of `FORCED_IDLE_REQ` |
| `pvr_no_sync=1` | accept the prim timeout as completion; on POW the code then performs the normal teardown |
| `pvr_state_wait=1` | accept `ePowState` transitions (IDLE/FORCED_IDLE/OFF) as completion (experimental) |
| `skip_mtcmos=1` | skip the explicit vendor MTCMOS bring-up sequence |

## 7. Open milestone

```
insmod pvrsrvkm.ko pvr_apm=2 pvr_os_active=1 pvr_no_sync=1 pvr_pow_off=1
open("/dev/dri/renderD129") -> success
```

The open path runs: `RGXPostPowerState(ON)` → `RGXDoStart` (ret 0) → FW started poll →
POW_OFF → IRQ count alignment → `RGXDoStop` (ret 0) → success.

## 8. Open questions

1. Why does the firmware not write `sPowerSync` / the rtn slot?
2. Why is POW processing intermittent (30–90 s vs never)?
3. Is the fail path gated behind `INICFG_POW_RASCALDUST` / MTK APM?
4. Is there any hosts-visible completion other than the prim that the stock 4.19 driver relies on?

## 9. Environment notes

- Two `insmod` runs without a reboot fail: IRQ 205 is not freed on `rmmod`
  (`genirq: Flags mismatch ... (GX_Main)`, `UNABLE_TO_REGISTER_ISR_HANDLER`)
- Firmware boot itself is intermittent (`boot stage=0`, FW started timeout)
- Console is USB ACM; after a kernel oops the ACM endpoint can die while NCM still works
