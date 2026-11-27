#!/usr/bin/env python3
"""Remove console=ttyGS0 from the r96 DTB /chosen/bootargs.

The bootargs string lives in /chosen/bootargs; replacing the token with spaces
keeps the blob length and NUL terminator intact, so nothing else shifts.
"""
import sys

src = sys.argv[1] if len(sys.argv) > 1 else \
    "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/r96-dandelion.dtb"
dst = sys.argv[2] if len(sys.argv) > 2 else \
    "/home/a12bbb/AI Project/Redmi 9A/kernel 7.1 mainline/r96-dandelion-noconsole.dtb"

d = open(src, "rb").read()
tok = b"console=ttyGS0"
n = d.count(tok)
print("occurrences of %r: %d" % (tok, n))
if n != 1:
    raise SystemExit("expected exactly one occurrence")

out = d.replace(tok, b" " * len(tok))
open(dst, "wb").write(out)

# sanity: bootargs still contains tty0, no ttyGS0, and dtb magic + symbols intact
i = out.find(b"bootargs")
print("bootargs region:", out[i:i + 240].split(b"\x00")[0].decode("latin1"))
print("still has __symbols__:", b"__symbols__" in out)
print("written:", dst, len(out), "bytes")
