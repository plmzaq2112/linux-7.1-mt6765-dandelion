D="/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline"/data/dts/dts-r96.dts
awk '/i2c@11016000 \{/,/^\t\t\};/' "$D" | grep -E '^\t\t\t[a-z0-9_@-]+ \{' | head -20
