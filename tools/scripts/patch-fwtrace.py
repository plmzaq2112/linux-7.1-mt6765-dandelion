import os

DDK = os.path.expanduser("~/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk")
DBG = os.path.join(DDK, "services/server/devices/rogue/rgxdebug.c")
PWR = os.path.join(DDK, "services/server/devices/rogue/rgxpower.c")

# ---------------- rgxdebug.c : bounded FW trace decode ----------------
s = open(DBG).read()

if "g_pvrFwTraceLimit" not in s:
    anchor = "void RGXDumpFirmwareTrace(DUMPDEBUG_PRINTF_FUNC *pfnDumpDebugPrintf,"
    if anchor not in s:
        raise SystemExit("rgxdebug anchor1 missing")
    s = s.replace(anchor,
        "/* PVR-MTK diagnostic: limit FW trace decode to the last N DWords (0 = full) */\n"
        "IMG_UINT32 g_pvrFwTraceLimit = 0;\n\n" + anchor, 1)

    a2 = ("\t\tIMG_UINT32  ui32TraceBufSizeInDWords = psRGXFWIfTraceBufCtl->ui32TraceBufSizeInDWords;\n")
    if a2 not in s:
        raise SystemExit("rgxdebug anchor2 missing")
    s = s.replace(a2, a2 +
        "\t\tIMG_UINT32  ui32CountLimit = ui32TraceBufSizeInDWords;\n\n"
        "\t\tif (g_pvrFwTraceLimit != 0 && ui32CountLimit > g_pvrFwTraceLimit)\n"
        "\t\t{\n"
        "\t\t\tui32CountLimit = g_pvrFwTraceLimit;\n"
        "\t\t}\n", 1)

    a3 = "\t\t\twhile (ui32Count < ui32TraceBufSizeInDWords)\n"
    if a3 not in s:
        raise SystemExit("rgxdebug anchor3 missing")
    s = s.replace(a3, "\t\t\twhile (ui32Count < ui32CountLimit)\n", 1)

    a4 = "\t\t\t\t         ui32Count < ui32TraceBufSizeInDWords);\n"
    if a4 not in s:
        raise SystemExit("rgxdebug anchor4 missing")
    s = s.replace(a4, "\t\t\t\t         ui32Count < ui32CountLimit);\n", 1)

    open(DBG, "w").write(s)
    print("rgxdebug.c patched")
else:
    print("rgxdebug.c already patched")

# ---------------- rgxpower.c : param, ABI print, trace dump ----------------
s = open(PWR).read()

if "pvr_fwtrace" in s:
    print("rgxpower.c already patched")
    raise SystemExit(0)

anchor = 'MODULE_PARM_DESC(pvr_no_apm, "clear RGXFWIF_INICFG_POW_RASCALDUST before FW boots");\n'
if anchor not in s:
    raise SystemExit("rgxpower anchor1 missing")

helpers = anchor + '''
static int pvr_fwtrace = 0;
module_param(pvr_fwtrace, int, 0644);
MODULE_PARM_DESC(pvr_fwtrace, "enable FW trace logging and dump FW trace around POW");

static void pvr_fwtrace_printf(void *pvDumpDebugFile, const IMG_CHAR *pszFmt, ...)
{
	char acBuf[512];
	va_list ap;

	(void)pvDumpDebugFile;
	va_start(ap, pszFmt);
	vsnprintf(acBuf, sizeof(acBuf), pszFmt, ap);
	va_end(ap);
	pr_info("FWT> %s\\n", acBuf);
}

static void pvr_dump_fw_trace(PVRSRV_RGXDEV_INFO *psDevInfo, const char *pcTag)
{
	RGXFWIF_TRACEBUF *psTb = psDevInfo->psRGXFWIfTraceBufCtl;
	IMG_UINT32 ui32Size, ui32Ptr, ui32Save;

	if (psTb == IMG_NULL)
	{
		pr_info("pvr-mtk: FWT %s: no control buffer\\n", pcTag);
		return;
	}
	ui32Size = psTb->ui32TraceBufSizeInDWords;
	ui32Ptr  = psTb->sTraceBuf[0].ui32TracePointer;
	pr_info("pvr-mtk: FWT %s logtype=%08x size=%u ptr=%u buf=%p\\n",
	        pcTag, psTb->ui32LogType, ui32Size, ui32Ptr,
	        (void *)psTb->sTraceBuf[0].pui32TraceBuffer);

	if (psTb->sTraceBuf[0].pui32TraceBuffer == IMG_NULL || ui32Size == 0)
	{
		pr_info("pvr-mtk: FWT %s: buffer not allocated\\n", pcTag);
		return;
	}
	if ((psTb->ui32LogType & RGXFWIF_LOG_TYPE_GROUP_MASK) == 0)
	{
		pr_info("pvr-mtk: FWT %s: logging disabled\\n", pcTag);
		return;
	}

	/* decode the most recent 400 dwords before the write pointer */
	ui32Save = psTb->sTraceBuf[0].ui32TracePointer;
	pr_info("pvr-mtk: FWT %s: --- begin decode ---\\n", pcTag);
	g_pvrFwTraceLimit = 400;
	psTb->sTraceBuf[0].ui32TracePointer = (ui32Ptr + ui32Size - 400) % ui32Size;
	RGXDumpFirmwareTrace(pvr_fwtrace_printf, IMG_NULL, psDevInfo);
	psTb->sTraceBuf[0].ui32TracePointer = ui32Save;
	g_pvrFwTraceLimit = 0;
	pr_info("pvr-mtk: FWT %s: --- end decode ---\\n", pcTag);
}

extern IMG_UINT32 g_pvrFwTraceLimit;
'''
s = s.replace(anchor, helpers, 1)

# early hook: ABI print + enable FW trace groups before FW boots
a_early = "\tif (pvr_no_apm && psDevInfo->psRGXFWIfFwSysData)\n"
if a_early not in s:
    raise SystemExit("rgxpower anchor2 missing")
early_ins = '''	if (pvr_fwtrace)
	{
		pr_info("pvr-mtk: ABI cmd=%u data=%u powreq=%u powoff=%u ccbctl=%u tb=%u\\n",
		        (unsigned)sizeof(RGXFWIF_KCCB_CMD),
		        (unsigned)offsetof(RGXFWIF_KCCB_CMD, uCmdData),
		        (unsigned)sizeof(RGXFWIF_POWER_REQUEST),
		        (unsigned)offsetof(RGXFWIF_POWER_REQUEST, uPowerReqData),
		        (unsigned)sizeof(RGXFWIF_CCB_CTL),
		        (unsigned)sizeof(RGXFWIF_TRACEBUF));
		if (psDevInfo->psRGXFWIfTraceBufCtl != IMG_NULL)
		{
			RGXFWIF_TRACEBUF *psTb = psDevInfo->psRGXFWIfTraceBufCtl;
			pr_info("pvr-mtk: FWT boot logtype=%08x\\n", psTb->ui32LogType);
			psTb->ui32LogType |= (RGXFWIF_LOG_TYPE_TRACE |
			                      RGXFWIF_LOG_TYPE_GROUP_MAIN |
			                      RGXFWIF_LOG_TYPE_GROUP_POW);
			pr_info("pvr-mtk: FWT boot logtype now=%08x\\n", psTb->ui32LogType);
		}
	}

'''
s = s.replace(a_early, early_ins + a_early, 1)

# raw command words right after filling the POW command
a_cmd = "\tsPowCmd.uCmdData.sPowData.uPowerReqData.ePowRequestType = RGXFWIF_POWER_FORCE_IDLE;\n"
if a_cmd not in s:
    raise SystemExit("rgxpower anchor3 missing")
s = s.replace(a_cmd, a_cmd +
    '\tif (pvr_fwtrace)\n'
    '\t{\n'
    '\t\tIMG_UINT32 *pui32Raw = (IMG_UINT32 *)&sPowCmd;\n'
    '\t\tpr_info("pvr-mtk: POW raw %08x %08x %08x %08x (w=%u)\\n",\n'
    '\t\t        pui32Raw[0], pui32Raw[1], pui32Raw[2], pui32Raw[3],\n'
    '\t\t        psDevInfo->psKernelCCBCtl->ui32WriteOffset);\n'
    '\t}\n', 1)

# dump FW trace right after the POW poll loop
a_poll = "\tif (eError != PVRSRV_OK)\n\t{\n\t\tpr_info(\"pvr-mtk: forced-idle timeout: kccb w=%u r=%u\\n\","
if a_poll not in s:
    raise SystemExit("rgxpower anchor4 missing")
s = s.replace(a_poll, '\tif (pvr_fwtrace)\n\t{\n\t\tpvr_dump_fw_trace(psDevInfo, "after-pow");\n\t}\n\n' + a_poll, 1)

open(PWR, "w").write(s)
print("rgxpower.c patched")
