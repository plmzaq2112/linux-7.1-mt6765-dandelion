# Patches

These diffs are against the vendor PowerVR DDK **1.13 (ED5776728)** sources, specifically:

- `services/server/devices/rogue/rgxinit.c`
- `services/server/devices/rogue/rgxpower.c`

They were produced with `diff -u <original>.bak_s3irq <modified>` and include:

- LISR instrumentation (`RGX_LISR[S3DBG]`) and the "return handled when the event was acked" fix
- `SampleIRQCount` timing/alignment handling in `RGXPrePowerState`
- `RGXDoStart` clearing `aui32SampleIRQCount`
- POW workarounds: `pvr_no_sync`, `pvr_pow_off`, `pvr_state_wait`, `pvr_fwstate`, diagnostics
- The state-based teardown used when the firmware does not write the prim

Apply from the `services/server/devices/rogue/` directory:

```sh
cp rgxinit.c rgxinit.c.bak
cp rgxpower.c rgxpower.c.bak
patch -p0 < rgxinit-s3irq.diff
patch -p0 < rgxpower-s3irq.diff
```

`ddk-diffstat.txt` lists the full change set against the DDK subtree (including the platform layer
and the new MTCMOS module, which are not part of these two diffs).

These patches are **not** upstream-quality: they include diagnostic parameters and deliberate
bypasses. License follows the DDK (dual MIT/GPLv2); the added code is GPL-2.0.
