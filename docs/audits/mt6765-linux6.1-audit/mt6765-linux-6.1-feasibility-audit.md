# MT6765 / Blossom-family Linux 6.1 Migration — Feasibility Audit

**Scope:** Read-only feasibility audit for migrating the existing, device-working
Linux **4.19.325** kernel for the Xiaomi **Redmi 9A (dandelion, MT6762G)** — and,
per user clarification, **any device in the "blossom" family** (Redmi 9C /
9C NFC, POCO C3; MT6762/MT6765 Helio G25/G35) — to **Linux 6.1**, while keeping
Android compatibility and KernelSU.

**Nature of this document (read first):**
- **VERIFIED** = I observed it directly (API response, raw file content, `git`/`Makefile`
  read, command output) in this audit.
- **AUTHOR-CLAIMED** = a repo owner / wiki editor / doc asserts it; I did not
  reproduce the build or boot.
- **UNKNOWN** = not determinable from available evidence; explicitly *not* guessed.

Nothing in this audit was compiled, flashed, checked out, reset, merged, or written
into any existing kernel tree. All repository access was via read-only HTTP APIs and
raw-file fetches. Baseline trees were only inspected with read-only `git` commands.

---

## 1. Executive summary

**Bottom line:** A direct "vendor 4.19 → 6.1" port of the current working tree is
**not the best path**, and Linux **6.1 is not a natural target** for this SoC family.
The realistic, stepwise-verifiable base is the **out-of-tree mainline MT6765/6762
enablement stack** maintained in the blossom community (currently at the **7.1–7.2
mainline era**), onto which the Android/KernelSU requirements must be re-added. 6.1
sits *before* that enablement series matured and *after* the point where the vendor
drivers you already rely on stop applying.

Key findings:

1. **Mainline (incl. 6.1) does not boot MT6765 out of the box.** **VERIFIED:**
   upstream `v6.1`, `v6.6`, and `master` contain only
   `drivers/pinctrl/mediatek/pinctrl-mt6765.c` and
   `drivers/clk/mediatek/clk-mt6765.c` for this SoC. There is **no `mt6765.dtsi`**
   and **no "6765" entry** in mtk-mmsys, mtk-mutex, mtk-smi, mtk-iommu,
   mtk-cmdq-mailbox, mtk-drm, mtk-wdt, or mtk-sd. Booting requires the
   **out-of-tree MT6765 enablement series** (SOC pinctrl/clk/DTS + display/sd/mmc
   glue) that lives in the blossom forks, not in mainline.

2. **The community enablement series targets 6.10+/7.x, not 6.1.** **VERIFIED**
   by Makefile reads: `adomerle/linux-mt6765@mt6765-next` = **6.10.0-rc3**, and
   `evilMyQueen/linux-mt6765@mt6765-devel` = **7.1.0** (fork `master` =
   **7.2.0-rc7**). No 6.1-targeted MT6765 tree was found.

3. **Real-device boot evidence exists — on the 7.x era, not 6.1.** **AUTHOR-CLAIMED**
   (Nura/postmarketOS wiki + project docs): dandelion boots a **7.1.0** mainline
   kernel with **ssh + sdcard working** (peripheral support still largely `N`);
   alpican docs claim boots on **5.15, 6.10.0-rc3 (no U-Boot), 7.2.0-rc4 (with
   U-Boot)**.

4. **Android + KernelSU does not come for free on any of these mainline trees.**
   The existing Android compatibility rests on **vendor `drivers/misc/mediatek/*`**
   and legacy subsystems (binder, ION/ASHMEM, fake-version EROFS/F2FS) that are
   **4.19-specific**; mainline enablement trees ship **none** of the Android/GKI
   plumbing. KernelSU is integrated via a **manual-hook** scheme (6 hook sites +
   SELinux symbol exports) that is portable in principle but must be re-applied
   and re-verified per kernel.

5. **The "highest version that actually boots a blossom-family device" is ~7.1–7.2,
   and it is not Android-complete.** So chasing 6.1 buys no version advantage and
   inherits the same missing-Android problem, while sitting on a *less complete*
   SoC-enablement baseline than 6.10/7.x.

**Recommendation (detail in §8):** Do **not** make 6.1 the target by default.
Build on the **blossom-family mainline enablement base (6.10 → 7.1/7.2)** as the
*forward* device/SoC port, and treat **Android-stack re-integration** (binder/ION
or its replacements, storage, and KernelSU) as the real workstream. If a 6.1
target is a hard external requirement, it is **feasible but strictly worse**: you
would backport the same out-of-tree MT6765 series to 6.1 *and* still port the
Android/KernelSU layer, with **no** existing device-verified 6.1 reference for this
family. Prefer **Route B/C (mainline-enablement base) over Route A (4.19 vendor →
6.1)**.

Confidence: repo/version/mainline facts are **high (VERIFIED)**; boot/peripheral
status is **author-claimed only**; Android/KSU portability is **partly unknown** and
flagged below.

---

## 2. Repository & kernel version table (from `Makefile` VERSION/PATCHLEVEL/SUBLEVEL)

All versions below were read from each tree's top-level `Makefile` (not README/name).
**VERIFIED.**

| Repository (owner/name) | Branch | Kernel (Makefile) | MT6765/blossom enablement? | dandelion DT? | Status/notes |
|---|---|---|---|---|---|
| *(baseline)* `pure-kernel/main` (local WSL) | `main` | **4.19.325** | vendor MTK tree | `dandelion.dts` | **Device-working** baseline, HEAD `67867e9c4`, 221 commits |
| `adomerle/linux-mt6765` | `master` | **6.10.0-rc3** | vanilla only | no | Fork of torvalds/linux; **ARCHIVED** |
| `adomerle/linux-mt6765` | `mt6765-next` | **6.10.0-rc3** | **yes** (~30-patch series) | no | HEAD `5be6e64`; patches by Arseniy Velikanov |
| `evilMyQueen/linux-mt6765` | `master` | **7.2.0-rc7** | vanilla only | no | Fork of torvalds/linux directly |
| `evilMyQueen/linux-mt6765` | `mt6765-devel` | **7.1.0** | **yes** (30 commits) | **yes** | HEAD `22b4320`; contains dandelion DT + WIP defconfig |
| `99-blossom/linux-mt6765` | `master` | **6.10.0-rc3** | no | no | Bare fork of adomerle; only `master`=`44ef20b` |
| `mtk-mainline/linux-mt6762` | `mt6765` | **6.5.0-rc3** | partial | no | — |
| `Helio-P22/linux-mainline` | `mt6765` | **6.5.0-rc3** | partial | no | — |
| `mt6735-mainline/linux` | `mt6735-stable-6.1.y` | **6.1** | **no (MT6735/37)** | no | Nearest *6.1* tree, wrong SoC family |
| `99-blossom/kernel_xiaomi_blossom_gnulinux` (alpican distro kernel) | — | **4.19.325** | vendor | blossom family | Alpine/Nura distro kernel for blossom |
| `KrutosVIP/...4.19.191_mt6765` | — | **4.19.191** | vendor | — | `CORN-R1/...` is a fork of this (same version) |
| `MiCode/...dandelion-q-oss` | — | **4.9.190** | vendor | dandelion | Official Q OSS drop |
| *(local)* `kernel-ksu/integration/ksu-base` | `ksu-integration` | 4.19.325 base | + KernelSU | — | HEAD `fdcdca7e7`, clean |

**Takeaway:** The only trees that carry *real* MT6765/blossom enablement are the
**6.10-rc3** and **7.1.0** series (`adomerle@mt6765-next`, `evilMyQueen@mt6765-devel`).
**No 6.1 tree with MT6765 enablement was found.**

---

## 3. Fork relations & commit diffs

**VERIFIED** via GitHub API (parent/fork fields) and commit listings.

- **`adomerle/linux-mt6765`** → fork of **`torvalds/linux`**. `master` = vanilla
  `6.10-rc3`. `mt6765-next` (`5be6e64`) = `6.10-rc3` + **~30-patch MT6765 series**
  (SoC bring-up: pinctrl/clk/DTS/display/mmc glue). **No dandelion/blossom DT.**
  Repo is **archived**.
- **`evilMyQueen/linux-mt6765`** → fork of **`torvalds/linux`** *directly* (not via
  adomerle). `master` = vanilla `7.2.0-rc7`. `mt6765-devel` (`22b4320`) = **7.1.0 +
  30 MT6765 commits**, including:
  - `3a7a5f476` — "arm64: mediatek: add support for Xiaomi Redmi 9A" (dandelion DT)
  - `5d41651ed` — "WIP: working defconfig"
  - mutex fixes attributed to **FuzzyPixelzz**
- **`TheKnightSky/linux-mt6765`** → **resolves to `evilMyQueen/linux-mt6765`**
  (same repo); the Nura wiki's "How to boot" instructs cloning this at
  `mt6765-devel`.
- **`99-blossom/linux-mt6765`** → bare fork of `adomerle/linux-mt6765`; carries
  **no MT6765 code** (only `master`=`44ef20b`, vanilla `6.10-rc3`).
- **`Helio-P22/linux-mainline`** & **`mtk-mainline/linux-mt6762`** → `mt6765`
  branches at `6.5.0-rc3` (partial enablement; not a blossom device tree).

**Implication:** The de-facto "forward" MT6765 base has *moved* from 6.10
(adomerle, archived) to **7.1/7.2 (evilMyQueen)**. A 6.1 target would be a **new
backport branch**, not a fork of any existing enablement tree.

### Device-tree specifics (VERIFIED, `evilMyQueen@mt6765-devel`)

- DTS: `arch/arm64/boot/dts/mediatek/mt6762g-xiaomi-dandelion.dts`
  - `compatible = "xiaomi,dandelion", "mediatek,mt6762", "mediatek,mt6765";`
  - Uses bootloader-provided **`simple-framebuffer`**; **no panel node** (no display
    driver) — consistent with wiki "screen = P (partial)".
- Config: `arch/arm64/configs/dandelion_defconfig`
  - Built with **Alpine/musl GCC 15.2.0**; header comment says **6.10.0-rc3**
    (i.e., the defconfig lineage predates the 7.1 rebase).

---

## 4. High-version porting results & on-device evidence

**All boot/peripheral results in this section are AUTHOR-CLAIMED** (project docs,
wiki). No build or boot was performed in this audit.

| Source | Claim | Device | Kernel | Evidence quality |
|---|---|---|---|---|
| Nura wiki — *Xiaomi Redmi 9A (xiaomi-dandelion)* | "**7.1 kernel, ssh & sdcard works**"; screen=P, emmc=N, battery=N, touch/wifi/bt/audio/camera/calls = N; **boots only on 2 GB model**; via **uniLoader** | dandelion | **7.1.0** | Author/wiki claim; `booting = yes` |
| alpican `Docs/mainline.md` | Booted **5.15**, **6.10.0-rc3 (without U-Boot)**, **7.2.0-rc4 (with U-Boot)** | blossom family | 5.15 / 6.10 / 7.2 | Author claim |
| `SheatNoisette/postmarket_redmi_9a` | **Failed** — "Unable to boot" | dandelion | (mainline) | Author claim (negative result) |
| Nura wiki — *Xiaomi Redmi 9C (xiaomi-angelica)* | `category = testing`, **`booting = no`**, screen=P, flashing=Y | 9C | (mainline) | Author/wiki claim (negative) |

**Interpretation:**
- The **highest version with a *positive* real-device boot claim in the blossom
  family is ~7.1–7.2** — *above* 6.1, on a *more complete* SoC enablement base.
- Even at that peak, the device is **far from feature-complete** (only ssh + sdcard;
  no touch/WiFi/baseband/display driver). *This is the non-Android "mainline" state.*
- **6.1 has no device-verified reference at all** for this family — you would be
  the first, on a base with *less* enablement than 6.10/7.x.

---

## 5. Driver & Android compatibility diff table

### 5a. SoC driver presence (mainline vs. needed for boot)

| Subsystem | `pinctrl-mt6765` | `clk-mt6765` | `mt6765.dtsi` | mmsys | mutex | smi | iommu | cmdq-mbox | drm | wdt | sd/mmc |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **mainline v6.1** | ✅ exists | ✅ exists | ❌ **no** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **mainline v6.6** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **mainline master** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **6.10-rc3 enablement** (adomerle/evilMyQueen) | ✅ | ✅ | ✅ (out-of-tree) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Needed to boot dandelion** | ✔ | ✔ | ✔ | ✔(disp) | ✔ | ✔ | ? | ? | ✔ | ✔ | ✔ |

Legend: ✅ = code present for MT6765 (VERIFIED in that tree); ❌ = **not** present
(VERIFIED absent); ✔ = required; ? = required-ness unknown for a minimal boot.

**VERIFIED absence** in `v6.1`/`v6.6`/`master`: no `"6765"` string in
`drivers/soc/mediatek/mtk-mmsys.c`, `mtk-mutex.c`, `mtk-smi.c`,
`drivers/iommu/mtk_iommu*`, `mtk-cmdq-mailbox.c`, `mediatek/mtk_drm_drv.c`,
`mediatek/mtk_wdt.c`, or `mediatek/mtk_sd*`/`mtk-sd.c`.

### 5b. Android userspace compatibility (4.19 baseline → mainline)

| Requirement | In 4.19 baseline (VERIFIED) | In mainline 6.1 / 6.10 / 7.x | Migration risk |
|---|---|---|---|
| **Binder** | `CONFIG_ANDROID_BINDER_IPC` (+ legacy) | **Not** in mainline; needs backport | **High** — Android userspace needs it |
| **ION / ASHMEM** | `CONFIG_ION`, ASHMEM enabled | **Removed/absent** in mainline; use **DMA-BUF heaps** instead | **High** — needs rewrite or dma-heap port |
| **EROFS / F2FS** | present, with **fake version 4.19.127** trick | mainline has both, but **no fake-version hack** | Medium — the fake-version trick is 4.19-specific |
| **MTK vendor drivers** | `drivers/misc/mediatek/*` (large vendor tree) | **None** in mainline enablement | **High** — touch/WiFi/baseband/charger/thermal all live here |
| **Android GKI / ABI** | downstream Android kernel | mainline ≠ GKI; ABI not preserved | **High** if any Android/GKI ABI must be kept |
| **Defconfig** | `blossom_defconfig`/`defconfig`/`gki_defconfig`/`stock_defconfig` | `dandelion_defconfig` (Alpine/musl, 6.10-rc3 era) | Medium — different toolchain (GCC 15.2.0 musl) |

**Note the symmetry:** mainline 6.1 *and* mainline 6.10/7.x **both lack** the
Android stack. Choosing 6.1 therefore **does not reduce** the Android work — it only
reduces the SoC-enablement baseline you start from. **VERIFIED for absence; risk
ratings are my assessment.**

---

## 6. KernelSU risk

**Baseline KSU state (VERIFIED, `kernel-ksu@ksu-integration`, `fdcdca7e7`, clean):**

- Integration = **manual hook** scheme (BakaSU-style), **UAPI v5**, version **35002**.
- Hook sites (6 files): `kernel/reboot.c`, `fs/read_write.c`, `fs/exec.c`,
  `fs/open.c`, `fs/stat.c`, `drivers/input/input.c`.
- **SELinux symbol export** added via `selinuxfs.c` / `services.c`.
- Config: `CONFIG_KSU_MANUAL_HOOK=y`; `porting/cfgs/ksu43.config`; patches
  `../patches/0001–0012`.
- Device is **running and verified**, SELinux **enforcing**.

**Portability to mainline 6.1 / 6.10 / 7.x:**

| Aspect | Assessment | Basis |
|---|---|---|
| Hook-set concept | Ports in principle | Hooks are generic (syscall/input/exec); VERIFIED shape |
| **File/line drift** | **High churn** | 4.19→7.x rewrote `fs/*`, `kernel/*` heavily; each patch needs rebasing |
| **SELinux exports** | Fragile | Symbol names/`EXPORT_SYMBOL` sites differ across versions; must re-audit |
| **Manual-hook `UAPI v5`** | Likely forward-compatible | Depends on kernel side only; UNKNOWN without build |
| **Upstream KSU (non-manual)** | None in mainline | KSU is out-of-tree; must vendor it |
| **Android dependency** | KSU needs a booting Android-capable kernel first | Same blocker as §5b |

**UNKNOWN / must be tested:** whether the 12 KSU patches apply cleanly to 6.1,
6.10, or 7.1, and whether manual hooks resolve the same symbols. **Do not assume
"KSU is easy" on 6.1** — the hooks are the *last* mile; the Android stack is the
blocker. (Risk: **Medium-High**, dominated by Android-stack, not by KSU itself.)

---

## 7. Three-route feasibility comparison

Scoring on **stepwise-verifiability** and **risk control** (not version number).

### Route A — Vendor 4.19 tree → Linux 6.1 (direct)
- **What:** Port the existing device-working 4.19.325 tree (with its MTK vendor
  drivers, Android plumbing, KSU) forward to 6.1.
- **Pros:** Starts from the only **device-verified** tree; preserves the known-good
  Android/KSU behavior at the 4.19 reference.
- **Cons / blockers:** The 4.19 **MTK vendor driver tree** (`drivers/misc/mediatek/*`)
  does **not** forward-port as a unit; rebasing onto 6.1 means either (a) dragging
  vendor drivers across 5 major versions (very high churn, ION/ASHMEM/binder all
  changed), or (b) discarding them and adopting mainline drivers — at which point
  you are really doing Route B, but **worse**, because you skipped the community
  MT6765 enablement series. **6.1 has no MT6765 enablement in mainline** (VERIFIED),
  so you would re-implement the SoC bring-up yourself.
- **Verdict:** **Not preferred.** Highest effort, no existing 6.1 reference, and it
  combines the *worst* of both worlds (vendor churn **and** missing mainline SoC code).

### Route B — Mainline MT6765/6762 base + add Android (front-to-back)
- **What:** Use the community MT6765 enablement base (`adomerle@mt6765-next`
  6.10-rc3 → `evilMyQueen@mt6765-devel` 7.1) and layer the Android requirements
  (binder/dma-heap/storage/vendor drivers) + KSU on top. Choose the kernel version
  *within that base's working range* rather than forcing 6.1.
- **Pros:** Starts from the **only base where blossom-family devices actually boot
  mainline** (7.1/7.2, author-claimed); the MT6765 SoC bring-up already exists
  (VERIFIED code presence); forward-maintained; matches where the community is.
- **Cons / blockers:** Mainline enablement currently boots with **minimal
  peripherals** (ssh + sdcard; no touch/WiFi/etc.), so **Android is not usable yet**
  regardless of version; the Android stack (binder/ION→dma-heap, vendor drivers) is
  **entirely missing** and is the real cost. **This cost is identical at 6.1.**
- **Verdict:** **Preferred base** — assuming "mainline Linux + kernel.org + KernelSU"
  is the goal, not "keep the existing Android userspace exactly."

### Route C — Other high-version real-device projects + Android evaluation
- **What:** Adopt the most mature **real-device** blossom-family projects and
  evaluate Android readiness.
  - `99-blossom/alpican` (Alpine/Nura for blossom; Redmi 9C NFC primary) — kernel
    `4.19.325` (verified), distro docs claim 5.15/6.10/7.2 boots.
  - `evilMyQueen/pmaports-blossom` + `linux-mt6765@mt6765-devel` (7.1) — the wiki's
    recommended dandelion path.
  - `MeexReay/pmos-xiaomi-angelican` (Redmi 9C NFC) — referenced from the 9C page.
- **Pros:** These are the **only** projects with actual device boots and packaged
  userspaces; they give the fastest path to a *running* (non-Android) system, which
  is the necessary prerequisite for Android work.
- **Cons / blockers:** Alpine/Nura/musl userspaces are **not Android**; reusing their
  kernel still leaves the **entire Android stack** to add. Peripheral support is
  partial, and the dandelion path reportedly **boots only on the 2 GB model**
  (author-claimed).
- **Verdict:** **Strong complement to Route B**; the pragmatic entry point to a
  booting base. Not a standalone Android solution.

### Comparison summary

| Criterion | A (4.19→6.1) | B (mainline MT6765 base) | C (other real-device proj.) |
|---|---|---|---|
| Existing device boot? | ✅ (at 4.19) | ✅ (at 6.10/7.x, author-claimed) | ✅ (6.10/7.x, author-claimed) |
| MT6765 SoC enablement present? | ❌ at 6.1 | ✅ in base | ✅ in base |
| Android stack present? | ✅ at 4.19 only | ❌ | ❌ |
| KSU present? | ✅ at 4.19 only | ❌ (must add) | ❌ |
| **6.1-specific reference exists?** | ❌ | ❌ (base is 6.10/7.x) | ❌ |
| Stepwise verify-ability | Low | **High** | **High** |
| Risk control | Poor | **Good** | **Good** |

---

## 8. Recommended route

**Recommendation:** **Route B, seeded by Route C** — adopt the **blossom-family
mainline MT6765 enablement base** (community 6.10 → 7.1/7.2 line), use an
**already-booting blossom-family tree** as the verified milestone, and treat
**Android-stack + KernelSU re-integration** as the primary, staged workstream.
**Do not make Linux 6.1 the default target.**

### Why this route, and why not the others

1. **"Code exists ≠ device works" cuts both ways and favors B/C.** **VERIFIED:**
   mainline 6.1 has *only* pinctrl+clk for MT6765 — that is *code exists*, not
   *device works*. The **only** trees with *device-works* claims are the 6.10/7.x
   community series. Starting from a base that **already boots** maximizes
   stepwise verifiability: each subsequent step (touch → WiFi → display → Android)
   can be tested against a known-booting baseline.

2. **6.1 adds no advantage and costs enablement.** Because **no MT6765 enablement
   exists in 6.1** (VERIFIED) and **no 6.1 MT6765 tree exists** (VERIFIED), a 6.1
   target means **backporting the same ~30-patch SoC series** *plus* the Android
   stack — strictly more work than Route B/C, with **no** device-verified 6.1
   reference. The version number is not the goal; the best *stepwise-verifiable,
   risk-controllable* base is.

3. **Android/KSU cost is version-invariant across 6.1→7.x.** Binder, ION/ASHMEM
   (→ dma-heap), vendor `mediatek/*` drivers, and GKI ABI concerns are **equally
   missing** on 6.1, 6.10, and 7.x (VERIFIED absence in mainline; the Android stack
   in the baseline is 4.19-specific). Therefore 6.1 buys **nothing** on the Android
   axis while losing SoC readiness.

4. **Route A is dominated.** It forces a 4.19-vendor-driver forward-port across 5
   majors (ION/ASHMEM/binder all changed) *and* lacks the community SoC enablement
   — i.e., maximum churn with minimum reuse. Route A only makes sense if the hard
   requirement is "preserve the exact current Android userspace + vendor feature
   set," which contradicts "move to 6.1 mainline."

### Suggested staging (verifiable milestones)

1. **Reproduce a booting blossom-family mainline base** (6.10-rc3 or 7.1) on a
   supported device/model; confirm ssh + sdcard. *(Prereq: unlocks all else.)*
2. **Add storage + display + input** needed for a usable console (close `screen=P`,
   `emmc=N`, `touch=N`).
3. **Add Android-prerequisite kernel interfaces**: binder, a memory-sharing path
   (dma-buf heaps or ION shim), and storage fs options — decide GKI/ABI posture.
4. **Vendor the required MTK peripherals** (touch/WiFi/baseband) — the largest and
   least-verified dependency; assess per-subtree.
5. **Re-apply KernelSU** (12-patch manual-hook set) and re-verify SELinux
   (enforcing), hook resolution, and version/UAPI compatibility.
6. **Refine the defconfig** (current `dandelion_defconfig` is a 6.10-era,
   musl-GCC WIP) toward a reproducible, upstreamable config.

**If 6.1 is a hard external requirement** (not merely "newer is better"): treat it
as Route B **+ a backport of the enablement series to 6.1**, and accept that
**steps 1–2 have no prior reference** — expect extra bring-up risk and no
device-verified 6.1 baseline to compare against. This is **feasible but inferior**.

---

## 9. Open questions (UNKNOWN — must be resolved by testing)

1. **Does the 12-patch KSU manual-hook set apply to 6.1 / 6.10 / 7.1?** UNKNOWN —
   requires patch-apply and build. Symbol resolution for SELinux exports likely
   differs.
2. **Exact peripheral bring-up status** behind the wiki's `N`/`P` flags on the 7.1
   dandelion claim (touch, WiFi, baseband, display) — the wiki is coarse; no
   per-feature logs were available.
3. **2 GB vs 3/4 GB boot limitation**: the wiki says dandelion "boots only on 2 GB."
   Root cause (DRAM config / DTS memory node?) is UNKNOWN.
4. **uniLoader dependency**: baseline device boot uses `uniLoader` as secondary
   bootloader; eMMC boot reportedly doesn't work (boots from SD). Impact on an
   Android/OEM boot flow is UNKNOWN.
5. **Android/GKI target**: is the goal a full Android userspace, or any
   Android-capable kernel? This materially changes binder/dma-heap/ABI work.
   **UNKNOWN / needs product decision.**
6. **Vendor driver re-licensing/feasibility** for touch/WiFi/baseband on mainline —
   UNKNOWN; may require reverse-engineering (cf. `DavidBuchanan314/lk-mt6765`).
7. **Blossom-family model choice**: user allows *any* blossom device. Best-supported
   target (9C NFC via alpican, vs. dandelion via evilMyQueen) and its peripheral
   maturity are UNKNOWN and should be picked per available test hardware.
8. **`alpican` distro kernel = 4.19.325** (VERIFIED) vs. its docs' 6.10/7.2 boot
   claims — reconcile which tree actually ships/boots.

---

## 10. Evidence index

### 10.1 Baseline local trees (read-only inspection)

- **`/home/a12bbb/android-kernel/pure-kernel/main`** (WSL, `Ubuntu-26.04`)
  - HEAD `67867e9c43781d57c515be813d3a6a4088972d1c`; `git describe` =
    `v2.1-22-g67867e9c4`; 221 commits; Makefile **4.19.325**.
  - Remotes: `github=plmzaq2112/android_kernel_mt6765`,
    `origin=Iam-nishan/Jujutsu-kernel`; branches `V6`, `archive/local-main`, `main`.
  - DT/defconfigs: `dandelion.dts`, `cust_mt6765_*.dtsi`,
    `blossom_defconfig` / `defconfig` / `gki_defconfig` / `stock_defconfig`.
  - **Dirty (DO NOT MODIFY):** `build-tools/check_config.sh`,
    `include/linux/debugfs.h`, `mm/page_owner.c`, `mm/slub.c`; untracked
    `build-tools/` debug files.
  - Device-verified 2026-10-15 (touch/WiFi/baseband OK).
- **`/home/a12bbb/android-kernel/kernel-ksu/integration/ksu-base`** — branch
  `ksu-integration` @ `fdcdca7e7`, clean; `drivers/kernelsu/`,
  `porting/cfgs/ksu43.config`, `../patches/0001–0012`; BakaSU manual hook, UAPI v5,
  version 35002; hooks in `kernel/reboot.c`, `fs/read_write.c`, `fs/exec.c`,
  `fs/open.c`, `fs/stat.c`, `drivers/input/input.c`; SELinux exports in
  `selinuxfs.c`/`services.c`; device running, SELinux enforcing.
- **`/home/a12bbb/android-kernel/upstream/linux-4.19.325`** + `filediff.txt` +
  `sha256sums.asc` — vanilla upstream reference.
- **`C:\Users\31806\Documents\AI_Project\Redmi_9A\silex-linux-dandelion\WORKFLOW.md`** — workspace conventions.
- **`C:\Users\31806\Documents\AI_Project\Redmi_9A\silex-linux-dandelion\windows-side\01-pure-baseline\dandelion-pure-kernel\`** — `README.md`,
  `commits.md`, `upstream-diff-report.md`, `phase2-batch-report.md`.
- **`C:\Users\31806\Documents\AI_Project\Redmi_9A\silex-linux-dandelion\windows-side\02-kernelsu\dandelion-ksu\`** — `README.md`,
  `commits.md`, `PHASE-A-REPORT.md`.
- **`C:\Users\31806\Documents\AI_Project\Redmi_9A\silex-linux-dandelion\bootimg.cfg`** — baseline boot cmdline
  (`bootopt=64S3,32N2,64N2 ...`).
- **`C:\Users\31806\AppData\Local\Temp\opencode\{baseline.sh,baseline2.sh,ksu.sh,ksu2.sh}`**
  — read-only WSL inspection scripts.

### 10.2 Remote repositories (GitHub/GitLab API + raw Makefile reads)

| Repo | Branch | HEAD | Makefile version |
|---|---|---|---|
| `adomerle/linux-mt6765` | `master` | `44ef20b`* | 6.10.0-rc3 |
| `adomerle/linux-mt6765` | `mt6765-next` | `5be6e64` | 6.10.0-rc3 |
| `evilMyQueen/linux-mt6765` | `master` | — | 7.2.0-rc7 |
| `evilMyQueen/linux-mt6765` | `mt6765-devel` | `22b4320` | 7.1.0 |
| `99-blossom/linux-mt6765` | `master` | `44ef20b` | 6.10.0-rc3 |
| `mtk-mainline/linux-mt6762` | `mt6765` | — | 6.5.0-rc3 |
| `Helio-P22/linux-mainline` | `mt6765` | — | 6.5.0-rc3 |
| `mt6735-mainline/linux` | `mt6735-stable-6.1.y` | — | 6.1 |
| `99-blossom/kernel_xiaomi_blossom_gnulinux` | — | — | 4.19.325 |
| `KrutosVIP/...4.19.191_mt6765` | — | — | 4.19.191 |
| `MiCode/...dandelion-q-oss` | — | — | 4.9.190 |

\* `adomerle@master` and `99-blossom@master` both point at the same vanilla
`44ef20b` content (99-blossom is a bare fork).

Notable commits (`evilMyQueen@mt6765-devel`):
- `3a7a5f476` — "arm64: mediatek: add support for Xiaomi Redmi 9A"
- `5d41651ed` — "WIP: working defconfig"
- mutex fixes by **FuzzyPixelzz**

Notable paths (`evilMyQueen@mt6765-devel`):
- `arch/arm64/boot/dts/mediatek/mt6762g-xiaomi-dandelion.dts`
- `arch/arm64/configs/dandelion_defconfig`

### 10.3 Upstream mainline (kernel.org / GitHub raw, VERIFIED)

- `drivers/pinctrl/mediatek/pinctrl-mt6765.c` — **present** in `v6.1`, `v6.6`,
  `master`.
- `drivers/clk/mediatek/clk-mt6765.c` — **present** in `v6.1`, `v6.6`, `master`.
- `mt6765.dtsi` — **absent** in `v6.1`, `v6.6`, `master`.
- No `"6765"` in: `mtk-mmsys.c`, `mtk-mutex.c`, `mtk-smi.c`, `mtk_iommu*`,
  `mtk-cmdq-mailbox.c`, `mtk_drm_drv.c`, `mtk_wdt.c`, `mtk-sd*` (v6.1/v6.6/master).
- Upstream status: MT6765 SoC enablement is **out-of-tree**; Yassine Oudjana is
  upstreaming MT6735/MT6765-family pinctrl (`mt6779-pinctrl` binding, v10, 2026-09);
  postmarketOS wiki user **FuzzyPixelzz** is mainlining Redmi 9A.

### 10.4 On-device / project evidence (AUTHOR-CLAIMED)

- **Nura wiki — `Xiaomi_Redmi_9A_(xiaomi-dandelion)`:** `status = "7.1 kernel, ssh &
  sdcard works"`, `pmoskernel = 7.1.0`, `booting = yes`, `status_screen = P`,
  `status_emmc = N`, `status_battery = N`, `status_touch = N`, `status_wifi = N`,
  `status_bluetooth = N`, `status_audio = N`, `status_camera = N`, `status_calls =
  N`; note: "alternative codename for the product lineup ... is 'blossom'"; boot via
  `evilMyQueen/pmaports-blossom` + `linux-mt6765@mt6765-devel` + **uniLoader**;
  warning: "this will boot only on 2GB ram model."
- **Nura wiki — `Xiaomi_Redmi_9C_(xiaomi-angelica)`:** `category = testing`,
  `booting = no`, `status_screen = P`, `status_flashing = Y`; chipset Helio G35
  (MT6765G); links `MeexReay/pmos-xiaomi-angelican`.
- **`99-blossom/alpican` `Docs/mainline.md`:** booted **5.15**, **6.10.0-rc3**
  (without U-Boot), **7.2.0-rc4** (with U-Boot).
- **`SheatNoisette/postmarket_redmi_9a`:** failed — "Unable to boot."
- **`xiaomi-blossom-dev/edk2-mt6765`:** UEFI shell boots, no license file.
- **`DavidBuchanan314/lk-mt6765`:** bootloader RE.
- **`kitty4O4/Generic_Kernel_Mediatek_MT6765`:** 404 (does not exist).

### 10.5 Method note

- No writes to any existing kernel repo; no checkout/reset/clean/rebase/merge/
  cherry-pick; no build; no flash; no partition ops.
- Remote facts gathered via GitHub/GitLab REST + raw file fetch and kernel.org cgit
  (read-only), occasionally retried due to transient timeouts and the 60/hr
  unauthenticated API limit.
- Environment: 2026; WSL distro `Ubuntu-26.04`; scripts run read-only via
  `wsl -d Ubuntu-26.04 bash -c 'sed "s/\r$//" <path> | bash'`.
- Scope note: per user, **any blossom-family device** is in scope, not only
  MT6765/dandelion; the audit therefore includes 9C/9C-NFC (alpican) evidence.

---

*End of audit.*
