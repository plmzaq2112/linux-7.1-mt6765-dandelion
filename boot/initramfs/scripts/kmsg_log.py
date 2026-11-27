#!/usr/bin/env python3
"""Dump /dev/kmsg to a file, fsync() after every record so the log survives
a power cycle / hang."""
import os
import sys

LOG = sys.argv[1] if len(sys.argv) > 1 else "/var/log/kmsg-live.log"
f = open(LOG, "w", buffering=1)
fd = os.open("/dev/kmsg", os.O_RDONLY | os.O_NONBLOCK)
f.write("# kmsg capture started\n")
f.flush()
os.fsync(f.fileno())
while True:
    try:
        data = os.read(fd, 8192)
    except BlockingIOError:
        import time
        time.sleep(0.05)
        continue
    if not data:
        continue
    f.write(data.decode("utf-8", "replace"))
    f.flush()
    os.fsync(f.fileno())
