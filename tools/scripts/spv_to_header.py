#!/usr/bin/env python3
"""Convert a SPIR-V binary to a C header with a byte array."""
import sys

name, inp, out = sys.argv[1], sys.argv[2], sys.argv[3]
data = open(inp, "rb").read()

with open(out, "w", encoding="utf-8") as f:
    f.write("static const unsigned char %s[] = {\n" % name)
    for i in range(0, len(data), 12):
        f.write("   " + ",".join("0x%02x" % b for b in data[i:i + 12]) + ",\n")
    f.write("};\n")
    f.write("static const unsigned int %s_len = %u;\n" % (name, len(data)))
