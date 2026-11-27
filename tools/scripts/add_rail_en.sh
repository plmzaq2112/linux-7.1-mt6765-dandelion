#!/bin/bash
set -e
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
cp /mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/kernel/modules/rail-en/rail_en.c "$T/drivers/misc/rail_en.c"

grep -q "rail_en" "$T/drivers/misc/Makefile" || \
    echo 'obj-$(CONFIG_RAIL_EN)	+= rail_en.o' >> "$T/drivers/misc/Makefile"

if ! grep -q "config RAIL_EN" "$T/drivers/misc/Kconfig"; then
    cat >> "$T/drivers/misc/Kconfig" <<'EOF'

config RAIL_EN
	tristate "Regulator debug helper"
	help
	  Enable a named regulator from userspace via module parameter.
	  Used for bring-up probing of peripherals on unpowered rails.
EOF
fi

grep -n "rail_en" "$T/drivers/misc/Makefile" "$T/drivers/misc/Kconfig"
