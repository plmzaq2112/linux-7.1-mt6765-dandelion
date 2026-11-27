import os
P = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(P).read()

if "PHY kccbctl" in s:
    print("already patched")
    raise SystemExit(0)

# include vmalloc/mm
a = "#if defined(LINUX)\n#include <linux/stddef.h>\n#else\n#include <stddef.h>\n#endif\n"
i = s.find(a)
if i < 0:
    raise SystemExit("include anchor not found")
s = s[:i] + a + "\n#if defined(LINUX)\n#include <linux/vmalloc.h>\n#include <linux/mm.h>\n#endif\n" + s[i + len(a):]

# PHY print inside skip-fidle block (after the OSINIT print)
anchor = '\t\tpr_info("pvr-mtk: OSINIT kccbctl=%08x kccb=%08x cmdsize=%u wrapmask=%u\\n",\n'
j = s.find(anchor)
if j < 0:
    raise SystemExit("OSINIT print anchor not found")

ins = ('''
\t\t{
\t\t\tunsigned long long pa1 = 0, pa2 = 0, pa3 = 0;
\t\t\tconst char *k1 = "vm", *k2 = "vm", *k3 = "vm";
\t\t\tif (psDevInfo->psKernelCCBCtl &&
\t\t\t    !is_vmalloc_addr(psDevInfo->psKernelCCBCtl)) {
\t\t\t\tpa1 = virt_to_phys((void *)psDevInfo->psKernelCCBCtl); k1 = "lin";
\t\t\t}
\t\t\tif (psDevInfo->psPowSyncPrim && psDevInfo->psPowSyncPrim->pui32LinAddr &&
\t\t\t    !is_vmalloc_addr((void *)psDevInfo->psPowSyncPrim->pui32LinAddr)) {
\t\t\t\tpa2 = virt_to_phys((void *)psDevInfo->psPowSyncPrim->pui32LinAddr); k2 = "lin";
\t\t\t}
\t\t\tif (psDevInfo->psRGXFWIfFwSysData &&
\t\t\t    !is_vmalloc_addr(psDevInfo->psRGXFWIfFwSysData)) {
\t\t\t\tpa3 = virt_to_phys((void *)psDevInfo->psRGXFWIfFwSysData); k3 = "lin";
\t\t\t}
\t\t\tpr_info("pvr-mtk: PHY kccbctl(%s)=0x%llx prim(%s)=0x%llx sysdata(%s)=0x%llx\\n",
\t\t\t        k1, pa1, k2, pa2, k3, pa3);
\t\t}
''')
s = s[:j] + ins + s[j:]
open(P, "w").write(s)
print("PHY diagnostic added")
