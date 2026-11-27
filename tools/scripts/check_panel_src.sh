#!/bin/bash
T="$HOME/AI_Project/Redmi_9A/kernel_7.1_mainline"
grep -nE '0x51|max_brightness|brightness = 0x78|msecs_to_jiffies' "$T/drivers/gpu/drm/panel/panel-fitipower-ft8006s.c"
