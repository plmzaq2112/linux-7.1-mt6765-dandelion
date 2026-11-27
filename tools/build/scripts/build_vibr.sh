#!/bin/bash
set -e
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
W=/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion
V="$HOME/AI_Project/Redmi_9A/kernel_4.19.325_purity"

cp "$V/drivers/leds/regulator-vibrator.c" "$T/drivers/leds/regulator-vibrator.c"
cp "$T/drivers/leds/regulator-vibrator.c" "$W/kernel/modules/regulator-vibrator/regulator-vibrator.c"

grep -q "CONFIG_REGULATOR_VIBRATOR" "$T/drivers/leds/Makefile" || \
    echo 'obj-$(CONFIG_REGULATOR_VIBRATOR)	+= regulator-vibrator.o' >> "$T/drivers/leds/Makefile"

if ! grep -q "config REGULATOR_VIBRATOR" "$T/drivers/leds/Kconfig"; then
    cat >> "$T/drivers/leds/Kconfig" <<'EOF'

config REGULATOR_VIBRATOR
	tristate "Regulator based vibrator"
	depends on REGULATOR
	help
	  Say Y here if you want to support a vibrator driven by a regulator
	  (MediaTek MT635x style). The regulator voltage selects the
	  vibration strength.
EOF
fi

cd "$T"
scripts/config --file out/.config -m REGULATOR_VIBRATOR
make O=out ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- olddefconfig >/dev/null
grep -n "REGULATOR_VIBRATOR" out/.config
make O=out ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- M=drivers/leds modules 2>&1 | grep -E "regulator-vibrator|error|warning: implicit" | head -30
ls -l out/drivers/leds/regulator-vibrator.ko 2>/dev/null || true
