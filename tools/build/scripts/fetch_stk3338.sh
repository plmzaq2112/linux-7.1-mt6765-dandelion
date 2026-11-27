#!/bin/bash
cd /tmp || exit 1
URL="https://uploadcdn.oneyac.com/attachments/files/brand_pdf/sensortek/STK3338-V.pdf"
curl -sL --max-time 60 -o stk3338.pdf "$URL" || { echo "curl failed"; exit 1; }
ls -l stk3338.pdf
if command -v pdftotext >/dev/null 2>&1; then
    pdftotext -layout stk3338.pdf /mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/logs/stk3338.txt
    echo "extracted: $(wc -l < /mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/logs/stk3338.txt) lines"
else
    echo "no pdftotext"
fi
