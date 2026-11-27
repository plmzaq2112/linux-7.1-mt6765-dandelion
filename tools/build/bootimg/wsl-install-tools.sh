#!/bin/bash
export http_proxy=http://172.29.192.1:3128
export https_proxy=http://172.29.192.1:3128
sudo -E apt-get install -y android-sdk-libsparse-utils >/tmp/apt2.log 2>&1
tail -3 /tmp/apt2.log
which simg2img
pip3 install --break-system-packages --quiet lpunpack 2>&1 | tail -2
python3 -c 'import lpunpack; print("lpunpack ok")' 2>&1 | tail -1
