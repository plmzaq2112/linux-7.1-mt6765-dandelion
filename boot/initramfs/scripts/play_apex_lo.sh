#!/bin/sh
cd /root/audio || exit 1

python3 mixer3.py enum "Headphone Left Source" 0
python3 mixer3.py enum "Headphone Right Source" 0
python3 mixer3.py enum "Handset Source" 0
python3 mixer3.py enum "Line Out Source" 2
python3 mixer3.py volset Lineout 100
python3 wav_play.py /root/audio/apex.wav
