#!/bin/sh
# Set the AFE connection matrix and the speaker (line out) route.
# Stopgap until a proper ALSA UCM2 profile for the card exists.
T=/usr/local/lib/dandelion-audio

# DL1/DL2 -> INT ADDA
python3 "$T/mixer3.py" set "O03 I05" 1
python3 "$T/mixer3.py" set "INT ADDA O03_O04" 1

# speaker output: hardware LO at minimum, loudness comes from PipeWire
python3 "$T/mixer3.py" volset Lineout 0
python3 "$T/mixer3.py" enum "Line Out Source" 2
python3 "$T/mixer3.py" enum "Handset Source" 0
python3 "$T/mixer3.py" enum "Headphone Left Source" 0
python3 "$T/mixer3.py" enum "Headphone Right Source" 0
