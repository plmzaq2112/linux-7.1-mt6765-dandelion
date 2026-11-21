# Artifacts

`pvr-t20-open-ok.ko` — the `pvrsrvkm.ko` build used for the "render node opens" milestone.

- Kernel: mainline 7.1.0-mt6765+ (arm64), SMA mismatch will make it **unusable on other builds**
- DDK: 1.13 (ED5776728), out-of-tree
- Loaded with: `insmod pvr-t20-open-ok.ko pvr_apm=2 pvr_os_active=1 pvr_no_sync=1 pvr_pow_off=1`

This file is included as evidence/reference only. Do not expect it to load on a different kernel
(`vermagic` and symbol CRC must match).
