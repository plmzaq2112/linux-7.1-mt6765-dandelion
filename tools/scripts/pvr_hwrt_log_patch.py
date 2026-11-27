#!/usr/bin/env python3
"""Log the UM-provided HWRTData parameters so the vendor GLES values can be
compared with Mesa's."""
from pathlib import Path

P = Path("/home/a12bbb/AI_Project/Redmi_9A/kernel_7.1_mainline/drivers/misc/pvr/ddk/services/server/devices/rogue/rgxta3d.c")
s = P.read_text(encoding="utf-8")

if "pvr-hwrt:" in s:
    print("already patched")
    raise SystemExit(0)

anchor = """	PVRSRV_ERROR eError;
	PVRSRV_RGXDEV_INFO		*psDevInfo = psDeviceNode->pvDevice;

	RGX_HWRTDATA_COMMON_COOKIE	*psHWRTDataCommonCookie;
"""
insert = """	PVRSRV_ERROR eError;
	PVRSRV_RGXDEV_INFO		*psDevInfo = psDeviceNode->pvDevice;

	pr_info("pvr-hwrt: ppp=%08x te_screen=%08x aa=%08x mt1=%08x mt2=%08x "
	        "stride=%08x rgn=%llx isp_mtile=%08x maxrts=%u tpc=%u/%u "
	        "merge=%u,%u,%u,%u,%u,%u\\n",
	        ui32ScreenPixelMax, ui32TEScreen, ui32TEAA, ui32TEMTILE1,
	        ui32TEMTILE2, ui32MTileStride,
	        (unsigned long long)uiRgnHeaderSize, ui32ISPMtileSize,
	        ui16MaxRTs, ui32TPCSize, ui32TPCStride,
	        ui32ISPMergeLowerX, ui32ISPMergeLowerY,
	        ui32ISPMergeUpperX, ui32ISPMergeUpperY,
	        ui32ISPMergeScaleX, ui32ISPMergeScaleY);

	RGX_HWRTDATA_COMMON_COOKIE	*psHWRTDataCommonCookie;
"""
assert s.count(anchor) == 1
s = s.replace(anchor, insert, 1)

P.write_text(s, encoding="utf-8")
print("patched hwrt log")
