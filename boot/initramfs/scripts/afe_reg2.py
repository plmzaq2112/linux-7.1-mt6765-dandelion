#!/usr/bin/env python3
"""Small /dev/mem helper for the mt6765 AFE register block (base 0x11220000).

usage:
  afe_reg2.py dac on|off     AFE_DAC_CON0 bit0
  afe_reg2.py irq            dump IRQ MCU registers
  afe_reg2.py irqclear       clear AFE_IRQ_MCU_STATUS bits
"""
import mmap
import os
import sys

BASE = 0x11220000
AFE_DAC_CON0 = 0x0010
IRQ_CON, IRQ_STATUS, IRQ_CLR, IRQ_EN = 0x03a0, 0x03a4, 0x03a8, 0x03b4

fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
page = mmap.mmap(fd, 0x4000, mmap.MAP_SHARED,
                 mmap.PROT_READ | mmap.PROT_WRITE, offset=BASE)


def rd(off):
    return int.from_bytes(page[off:off + 4], "little")


def wr(off, v):
    page[off:off + 4] = v.to_bytes(4, "little")


cmd = sys.argv[1]
if cmd == "dac":
    before = rd(AFE_DAC_CON0)
    if sys.argv[2] == "on":
        wr(AFE_DAC_CON0, before | 1)
    else:
        wr(AFE_DAC_CON0, before & ~1)
    print("DAC_CON0 0x%08x -> 0x%08x" % (before, rd(AFE_DAC_CON0)))
elif cmd == "irq":
    print("CON=0x%08x STATUS=0x%08x CLR=0x%08x EN=0x%08x" %
          (rd(IRQ_CON), rd(IRQ_STATUS), rd(IRQ_CLR), rd(IRQ_EN)))
elif cmd == "irqclear":
    wr(IRQ_CLR, 0x3ff)
    print("STATUS after clear=0x%08x" % rd(IRQ_STATUS))
page.close()
os.close(fd)
