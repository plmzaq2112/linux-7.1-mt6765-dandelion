#!/bin/sh
# Load the dandelion audio modules and set the digital routing.
# The analog output is intentionally NOT enabled here: enabling the handset
# at boot produces a power-up pop in the earpiece. DAPM powers it when a
# stream starts.

M=/lib/modules/$(uname -r)/extra/dandelion-audio
T=/usr/local/lib/dandelion-audio

insmod "$M/snd-soc-mtk-common.ko" 2>/dev/null
insmod "$M/snd-soc-mt6765-pcm.ko" 2>/dev/null
insmod "$M/mt6765-mt6357.ko" 2>/dev/null

sleep 1

# DL1/DL2 -> INT ADDA connection matrix (digital only)
python3 "$T/mixer3.py" set "O03 I05" 1
python3 "$T/mixer3.py" set "INT ADDA O03_O04" 1
