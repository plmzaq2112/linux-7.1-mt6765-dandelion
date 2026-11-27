#!/usr/bin/env python3
"""Turn a text keymap into a C string header."""
import json
import sys
from pathlib import Path

src = Path(sys.argv[1]).read_text()
out = Path(sys.argv[2])

lines = src.splitlines()
body = "\n".join("    %s" % json.dumps(line + "\n") for line in lines)
out.write_text(
    "/* Generated from %s -- do not edit. */\n"
    "static const char xkb_keymap_string[] =\n%s;\n"
    "static const unsigned int xkb_keymap_size = sizeof(xkb_keymap_string);\n"
    % (Path(sys.argv[1]).name, body)
)
print("wrote %s (%d bytes)" % (out, len(src)))
