import os, re

p = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(p).read()

# 1) drop the memremap(MEMREMAP_WC) physical view (it faults on this platform)
start = s.find("\tIMG_UINT32 ui32PaView = 0xDEADBEEF;")
if start < 0:
    raise SystemExit("paview block not found")
end = s.find("\tif (psDevInfo->psPowSyncPrim && psDevInfo->psPowSyncPrim->pui32LinAddr)", start)
if end < 0:
    raise SystemExit("paview block end not found")
s = s[:start] + "\tIMG_UINT32 ui32PaView = 0;\n" + s[end:]

# 2) guard the decode with a kernel-address sanity check + extra alloc debug
old_dump = "\t/* decode the most recent 400 dwords before the write pointer */\n"
new_dump = ("\tpr_info(\"pvr-mtk: FWT Probe rawptr=%016lx sizeof_ptr=%zu off=%zu\\n\",\n"
            "\t        (unsigned long)psTb->sTraceBuf[0].pui32TraceBuffer,\n"
            "\t        sizeof(psTb->sTraceBuf[0].pui32TraceBuffer),\n"
            "\t        (size_t)((char *)&psTb->sTraceBuf[0].pui32TraceBuffer - (char *)psTb));\n"
            "\tif (((unsigned long)psTb->sTraceBuf[0].pui32TraceBuffer >> 48) != 0xffffUL)\n"
            "\t{\n"
            "\t\tpr_info(\"pvr-mtk: FWT %s: cpu ptr not a kernel address, skip decode\\n\", pcTag);\n"
            "\t\treturn;\n"
            "\t}\n\n"
            "\t/* decode the most recent 400 dwords before the write pointer */\n")
if old_dump not in s:
    raise SystemExit("dump anchor not found")
s = s.replace(old_dump, new_dump, 1)

open(p, "w").write(s)
print("patched: paview removed, decode guarded")
