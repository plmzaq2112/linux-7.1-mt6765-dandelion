import os
P = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxpower.c")
s = open(P).read()

if "POW[%s]" in s:
    print("already patched")
    raise SystemExit(0)

HELPER = r'''static void pvr_pow_snap(PVRSRV_RGXDEV_INFO *psDevInfo, const char *tag,
                         const RGXFWIF_KCCB_CMD *psCmd, IMG_UINT32 ui32Slot)
{
	RGXFWIF_SYSDATA *psSys = psDevInfo->psRGXFWIfFwSysData;
	IMG_UINT32 ui32Sync = 0xDEADBEEF;

	if (psDevInfo->psPowSyncPrim && psDevInfo->psPowSyncPrim->pui32LinAddr)
		ui32Sync = *(volatile IMG_UINT32 *)psDevInfo->psPowSyncPrim->pui32LinAddr;

	pr_info("pvr-mtk: POW[%s] sync=%u fwaddr=%08x cpuva=%px kccb=%u/%u slot=%u pow=%u hwr=%08x fwirq=%u faults=%u\n",
		tag, ui32Sync,
		psDevInfo->psRGXFWIfFwOsData->sPowerSync.ui32Addr,
		psDevInfo->psPowSyncPrim ? psDevInfo->psPowSyncPrim->pui32LinAddr : NULL,
		psDevInfo->psKernelCCBCtl->ui32WriteOffset,
		psDevInfo->psKernelCCBCtl->ui32ReadOffset,
		ui32Slot,
		psSys ? (unsigned)psSys->ePowState : 999U,
		psSys ? psSys->ui32HWRStateFlags : 0U,
		psSys ? psSys->aui32InterruptCount[0] : 0U,
		psSys ? psSys->ui32FWFaults : 0U);

	if (psCmd)
		pr_info("pvr-mtk: POW[%s] cmd=%08x powtype=%u req=%u raw=%08x\n",
			tag, psCmd->eCmdType,
			(unsigned)psCmd->uCmdData.sPowData.ePowType,
			(unsigned)psCmd->uCmdData.sPowData.uPowerReqData.ePowRequestType,
			psCmd->uCmdData.sPowData.uPowerReqData.ui32ActivePMLatencyms);
}

'''

anchor_fn = "PVRSRV_ERROR RGXForcedIdleRequest(IMG_HANDLE hDevHandle, IMG_BOOL bDeviceOffPermitted)\n{\n"
i = s.find(anchor_fn)
if i < 0:
    raise SystemExit("function anchor not found")
s = s[:i] + HELPER + s[i:]

# 1) snapshot before zeroing the sync prim
a1 = "\teError = SyncPrimSet(psDevInfo->psPowSyncPrim, 0);\n"
i1 = s.find(a1)
if i1 < 0:
    raise SystemExit("SyncPrimSet anchor not found")
s = s[:i1] + '\tpvr_pow_snap(psDevInfo, "before", &sPowCmd, 0);\n' + s[i1:]

# 2) replace the ad-hoc conn/after-send/kick block with one snapshot
start = s.find('\tpr_info("pvr-mtk: conn fw=')
end = s.find("\t/* Wait for GPU to finish current workload */", start)
if start < 0 or end < 0:
    raise SystemExit("ad-hoc block anchors not found")
s = s[:start] + '\tpvr_pow_snap(psDevInfo, "sent", &sPowCmd, ui32CmdKCCBSlot);\n\n' + s[end:]

# 3) snapshot after the forced-idle poll (locate via the pow sync prim argument)
p = s.find("psDevInfo->psPowSyncPrim->pui32LinAddr,")
if p < 0:
    raise SystemExit("pow sync prim arg not found")
q = s.find("0x1, 0xFFFFFFFF);", p)
if q < 0:
    raise SystemExit("poll end not found")
q = s.find("\n", q) + 1
s = s[:q] + '\t\tpvr_pow_snap(psDevInfo, "poll", &sPowCmd, ui32CmdKCCBSlot);\n' + s[q:]

# 4) timeout snapshot
t = s.find('pr_info("pvr-mtk: forced-idle timeout:')
if t < 0:
    raise SystemExit("timeout print not found")
t2 = s.find("\n", s.find("\n", t) + 1)  # skip the 3-line pr_info (2 more lines)
# safer: find the closing ");" of that pr_info
t3 = s.find(");", t) + 2
t3 = s.find("\n", t3) + 1
s = s[:t3] + '\t\tpvr_pow_snap(psDevInfo, "timeout", &sPowCmd, ui32CmdKCCBSlot);\n' + s[t3:]

open(P, "w").write(s)
print("POW snapshot instrumentation applied")
