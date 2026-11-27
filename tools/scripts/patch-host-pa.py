import os
P = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(P).read()

if "HOST prim pa" in s:
    print("already patched")
    raise SystemExit(0)

anchor = '\t\t\t\t\tmemunmap(pvPt);\n'
i = s.find(anchor)
if i < 0:
    raise SystemExit("memunmap anchor not found")

ins = (r'''				{
					unsigned long long ullPrimPa = 0ULL, ullCtlPa = 0ULL;
					struct page *psPg;

					if (psDevInfo->psPowSyncPrim && psDevInfo->psPowSyncPrim->pui32LinAddr)
					{
						psPg = vmalloc_to_page((void *)psDevInfo->psPowSyncPrim->pui32LinAddr);
						if (psPg)
							ullPrimPa = page_to_phys(psPg) +
							            offset_in_page((void *)psDevInfo->psPowSyncPrim->pui32LinAddr);
					}
					if (psDevInfo->psKernelCCBCtl)
					{
						psPg = vmalloc_to_page(psDevInfo->psKernelCCBCtl);
						if (psPg)
							ullCtlPa = page_to_phys(psPg) +
							           offset_in_page(psDevInfo->psKernelCCBCtl);
					}
					pr_info("pvr-mtk: HOST prim pa=0x%llx ctl pa=0x%llx (PTE says prim=0x42c7c000 ctl=0x42c7d880)\n",
					        ullPrimPa, ullCtlPa);
				}
''')
s = s[:i] + ins + s[i:]
open(P, "w").write(s)
print("host PA compare added")
