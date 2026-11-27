# MT6357 card-bind pop mitigation

## Files

- `mt6357-pop-fix.patch` targets the upstream-style
  `sound/soc/codecs/mt6357.c` driver, matching `CONFIG_SND_SOC_MT6357=y`.
- It adds a 500-1000 us settling interval immediately after the platform
  driver enables the `vaud28` regulator and before it registers the codec
  component. This puts the wait before ASoC can bind the card.

## Why this change

The dandelion device tree in this handover tree connects `vaud28-supply` to
the MT6357 `ldo-vaud28` regulator and specifies
`regulator-enable-ramp-delay = <0x108>` (264 us). The mainline MT6357 driver
already enables VAUD28 before registering the codec component, but has no
additional settle interval there. The MT6768 vendor codec's analog power-up
sequence includes 250 us waits around enabling the analog/audio path. The
patch adds a bounded, sleepable wait at the earliest codec bind point, based
on those two pieces of evidence.

## Scope and limits

- Mainline MT6357 has no `set_bias_level` callback and no explicit VMID
  control. Do not copy a VMID sequence from a different codec or vendor tree
  without confirming the matching MT6357 register semantics.
- The mainline DAPM path already uses -40 dB startup gain and staged
  headphone output ramping. This patch leaves that runtime sequence intact.
- The vendor MT6768 source is a legacy analog codec implementation, not a
  drop-in replacement for this ASoC driver. Its two 250 us waits are useful
  timing evidence, not proof that this probe delay alone fixes every pop.
- This only targets card-bind / initial VAUD28 settling. If the pop happens
  on each playback start or route change, capture logs around DAPM events and
  adjust the runtime path based on that evidence.
- `AW87519` speaker-amplifier support is independent and is not included.

## Integration

From the kernel source root, apply with:

```sh
git apply /path/to/mt6357-pop-fix.patch
```

Because `CONFIG_SND_SOC_MT6357=y`, rebuild the kernel `Image.gz` and flash
the resulting boot image. This patch has not been built or device-tested.

## Source comparison

- Upstream codec: <https://github.com/torvalds/linux/blob/master/sound/soc/codecs/mt6357.c>
- MT6768 vendor codec: <https://github.com/LineageOS/android_kernel_xiaomi_mt6768/blob/6fbdf4e6800ab732f8f132cd3eca05b26e357255/sound/soc/mediatek/codec/mt6357/mtk-soc-codec-6357.c>
- Local board DT: `dandelion-audio.dts`, `audio-codec` and `ldo-vaud28` nodes.
