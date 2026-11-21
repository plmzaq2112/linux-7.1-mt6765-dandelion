/*************************************************************************/ /*!
@File
@Title          Device specific power routines
@Copyright      Copyright (c) Imagination Technologies Ltd. All Rights Reserved
@Description    Device specific functions
@License        Dual MIT/GPLv2

The contents of this file are subject to the MIT license as set out below.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

Alternatively, the contents of this file may be used under the terms of
the GNU General Public License Version 2 ("GPL") in which case the provisions
of GPL are applicable instead of those above.

If you wish to allow use of your version of this file only under the terms of
GPL, and not to allow others to use your version of this file under the terms
of the MIT license, indicate your decision by deleting the provisions above
and replace them with the notice and other provisions required by GPL as set
out in the file called "GPL-COPYING" included in this distribution. If you do
not delete the provisions above, a recipient may use your version of this file
under the terms of either the MIT license or GPL.

This License is also included in this distribution in the file called
"MIT-COPYING".

EXCEPT AS OTHERWISE STATED IN A NEGOTIATED AGREEMENT: (A) THE SOFTWARE IS
PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE AND NONINFRINGEMENT; AND (B) IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*/ /**************************************************************************/

#if defined(LINUX)
#include <linux/stddef.h>
#else
#include <stddef.h>
#endif

#if defined(LINUX)
#include <linux/vmalloc.h>
#include <linux/mm.h>
#endif


#include "rgxpower.h"
#include "rgxmem.h"
#include "rgxinit.h"
#include "rgx_fwif_km.h"
#include "rgxfwutils.h"
#include "pdump_km.h"
#include "pvr_debug.h"
#include "osfunc.h"
#include "rgxdebug.h"
#include "devicemem.h"
#include "devicemem_pdump.h"
#include "rgxtimecorr.h"
#include "devicemem_utils.h"
#include "htbserver.h"
#include "rgxstartstop.h"
#include "rgxfwimageutils.h"
#include "sync.h"
#include "rgxdefs_km.h"
#include <linux/io.h>
#include <linux/delay.h>
#include "mmu_common.h"

extern int g_pvrNoSync;

static int pvr_no_apm = 0;
module_param(pvr_no_apm, int, 0644);
MODULE_PARM_DESC(pvr_no_apm, "clear RGXFWIF_INICFG_POW_RASCALDUST before FW boots");

static int pvr_state_wait = 1;
module_param(pvr_state_wait, int, 0644);
MODULE_PARM_DESC(pvr_state_wait, "accept ePowState transitions as completion (FW does not ack the prim)");

static int pvr_kick = 0;
module_param(pvr_kick, int, 0644);
MODULE_PARM_DESC(pvr_kick, "repeatedly kick MTS_SCHEDULE after POW and log readback");

static int pvr_fwstate = 0;
module_param(pvr_fwstate, int, 0644);
MODULE_PARM_DESC(pvr_fwstate, "dump FWIF init/data structs as hex at POW entry (A7)");

static void pvr_hexdump(const char *name, const void *ptr, unsigned int size,
			unsigned int max_bytes)
{
	const u8 *p = (const u8 *)ptr;
	unsigned int n, i, j;

	if (p == NULL) {
		pr_info("FWSTATE %s: <null>\n", name);
		return;
	}
	n = size < max_bytes ? size : max_bytes;
	pr_info("FWSTATE %s ptr=%px size=%u dump=%u\n", name, ptr, size, n);
	for (i = 0; i < n; i += 16) {
		char line[16 * 3 + 1];
		char *h = line;

		for (j = 0; j < 16 && i + j < n; j++)
			h += scnprintf(h, sizeof(line) - (size_t)(h - line), "%02x ",
				       p[i + j]);
		*h = '\0';
		pr_info("FWSTATE %s +%03x: %s\n", name, i, line);
	}
}

static void pvr_dump_fwstate(PVRSRV_RGXDEV_INFO *psDevInfo)
{
	pr_info("FWSTATE key: cfg=%08x ext=%08x osflg=%08x pow=%u kcmds=%u lat=%u clk=%u dusts=%u\n",
		psDevInfo->psRGXFWIfFwSysData ? psDevInfo->psRGXFWIfFwSysData->ui32ConfigFlags : 0,
		psDevInfo->psRGXFWIfFwSysData ? psDevInfo->psRGXFWIfFwSysData->ui32ConfigFlagsExt : 0,
		psDevInfo->psRGXFWIfFwOsData ? psDevInfo->psRGXFWIfFwOsData->ui32FwOsConfigFlags : 0,
		psDevInfo->psRGXFWIfFwSysData ? (unsigned)psDevInfo->psRGXFWIfFwSysData->ePowState : 999,
		psDevInfo->psRGXFWIfFwOsData ? psDevInfo->psRGXFWIfFwOsData->ui32KCCBCmdsExecuted : 0,
		psDevInfo->psRGXFWIfRuntimeCfg ? psDevInfo->psRGXFWIfRuntimeCfg->ui32ActivePMLatencyms : 0,
		psDevInfo->psRGXFWIfRuntimeCfg ? psDevInfo->psRGXFWIfRuntimeCfg->ui32CoreClockSpeed : 0,
		psDevInfo->psRGXFWIfRuntimeCfg ? psDevInfo->psRGXFWIfRuntimeCfg->ui32DefaultDustsNumInit : 0);

	pvr_hexdump("SYSDATA", psDevInfo->psRGXFWIfFwSysData,
		    psDevInfo->psRGXFWIfFwSysData ? sizeof(RGXFWIF_SYSDATA) : 0, 512);
	pvr_hexdump("OSDATA", psDevInfo->psRGXFWIfFwOsData,
		    psDevInfo->psRGXFWIfFwOsData ? sizeof(RGXFWIF_OSDATA) : 0, 512);
	pvr_hexdump("SYSINIT", psDevInfo->psRGXFWIfSysInit,
		    psDevInfo->psRGXFWIfSysInit ? sizeof(RGXFWIF_SYSINIT) : 0, 512);
	pvr_hexdump("OSINIT", psDevInfo->psRGXFWIfOsInit,
		    psDevInfo->psRGXFWIfOsInit ? sizeof(RGXFWIF_OSINIT) : 0, 512);
	pvr_hexdump("RTCFG", psDevInfo->psRGXFWIfRuntimeCfg,
		    psDevInfo->psRGXFWIfRuntimeCfg ? sizeof(RGXFWIF_RUNTIME_CFG) : 0, 256);
}

static int pvr_fwtrace = 0;
module_param(pvr_fwtrace, int, 0644);
MODULE_PARM_DESC(pvr_fwtrace, "enable FW trace logging and dump FW trace around POW");


static void pvr_dump_fw_trace(PVRSRV_RGXDEV_INFO *psDevInfo, const char *pcTag)
{
	RGXFWIF_TRACEBUF *psTb = psDevInfo->psRGXFWIfTraceBufCtl;
	IMG_UINT32 ui32Size;
	IMG_UINT32 tid;

	if (psTb == NULL)
	{
		pr_info("pvr-mtk: FWT %s: no control buffer\n", pcTag);
		return;
	}

	ui32Size = psTb->ui32TraceBufSizeInDWords;
	pr_info("pvr-mtk: FWT %s logtype=%08x size=%u flags=%08x threads=%u ctl_fw=%08x\n",
	        pcTag, psTb->ui32LogType, ui32Size, psTb->ui32TracebufFlags,
	        (unsigned)RGXFW_THREAD_NUM,
	        (psDevInfo->psRGXFWIfSysInit != NULL) ?
	            psDevInfo->psRGXFWIfSysInit->sTraceBufCtl.ui32Addr : 0U);

	if ((psTb->ui32LogType & RGXFWIF_LOG_TYPE_GROUP_MASK) == 0)
	{
		pr_info("pvr-mtk: FWT %s: logging disabled\n", pcTag);
		return;
	}
	if (ui32Size == 0)
	{
		pr_info("pvr-mtk: FWT %s: size 0\n", pcTag);
		return;
	}

	for (tid = 0; tid < RGXFW_THREAD_NUM; tid++)
	{
		void *pvCpu = NULL;
		IMG_UINT32 i, ui32Start, ui32Count;
		IMG_UINT32 ui32Ptr = psTb->sTraceBuf[tid].ui32TracePointer;

		pr_info("pvr-mtk: FWT %s tid=%u ptr=%u buf_fw=%08x field=%016lx\n",
		        pcTag, tid, ui32Ptr,
		        psTb->sTraceBuf[tid].pui32RGXFWIfTraceBuffer.ui32Addr,
		        (unsigned long)psTb->sTraceBuf[tid].pui32TraceBuffer);

		if (psDevInfo->psRGXFWIfTraceBufferMemDesc[tid] == NULL)
		{
			pr_info("pvr-mtk: FWT %s tid=%u: no memdesc\n", pcTag, tid);
			continue;
		}
		if (DevmemAcquireCpuVirtAddr(psDevInfo->psRGXFWIfTraceBufferMemDesc[tid], &pvCpu) != PVRSRV_OK ||
		    pvCpu == NULL)
		{
			pr_info("pvr-mtk: FWT %s tid=%u: acquire cpu va failed\n", pcTag, tid);
			continue;
		}
		pr_info("pvr-mtk: FWT %s tid=%u fresh cpu=%px\n", pcTag, tid, pvCpu);

		if (((unsigned long)pvCpu >> 48) == 0xffffUL)
		{
			IMG_UINT32 *pui32 = (IMG_UINT32 *)pvCpu;

			ui32Count = 160;
			if (ui32Count > ui32Size)
			{
				ui32Count = ui32Size;
			}
			ui32Start = (ui32Ptr + ui32Size - ui32Count) % ui32Size;

			for (i = 0; i < ui32Count; i += 8)
			{
				pr_info("FWTRAW t%u %u: %08x %08x %08x %08x %08x %08x %08x %08x\n",
				        tid, ui32Start + i,
				        pui32[(ui32Start + i + 0) % ui32Size],
				        pui32[(ui32Start + i + 1) % ui32Size],
				        pui32[(ui32Start + i + 2) % ui32Size],
				        pui32[(ui32Start + i + 3) % ui32Size],
				        pui32[(ui32Start + i + 4) % ui32Size],
				        pui32[(ui32Start + i + 5) % ui32Size],
				        pui32[(ui32Start + i + 6) % ui32Size],
				        pui32[(ui32Start + i + 7) % ui32Size]);
			}
		}
		DevmemReleaseCpuVirtAddr(psDevInfo->psRGXFWIfTraceBufferMemDesc[tid]);
	}
}

static void pvr_maybe_move_prim(PVRSRV_RGXDEV_INFO *psDevInfo);

#if defined(PVRSRV_ENABLE_PROCESS_STATS)
#include "process_stats.h"
#endif
#if defined(SUPPORT_LINUX_DVFS)
#include "pvr_dvfs_device.h"
#endif

static PVRSRV_ERROR RGXFWNotifyHostTimeout(PVRSRV_RGXDEV_INFO *psDevInfo)
{
	RGXFWIF_KCCB_CMD sCmd;
	PVRSRV_ERROR eError;
	IMG_UINT32 ui32CmdKCCBSlot;

	/* Send the Timeout notification to the FW */
	sCmd.eCmdType = RGXFWIF_KCCB_CMD_POW;
	sCmd.uCmdData.sPowData.ePowType = RGXFWIF_POW_FORCED_IDLE_REQ;
	sCmd.uCmdData.sPowData.uPowerReqData.ePowRequestType = RGXFWIF_POWER_HOST_TIMEOUT;

	eError = RGXSendCommandAndGetKCCBSlot(psDevInfo,
	                                      &sCmd,
	                                      PDUMP_FLAGS_NONE,
	                                      &ui32CmdKCCBSlot);

	return eError;
}

static void _RGXUpdateGPUUtilStats(PVRSRV_RGXDEV_INFO *psDevInfo)
{
	RGXFWIF_GPU_UTIL_FWCB *psUtilFWCb;
	IMG_UINT64 *paui64StatsCounters;
	IMG_UINT64 ui64LastPeriod;
	IMG_UINT64 ui64LastState;
	IMG_UINT64 ui64LastTime;
	IMG_UINT64 ui64TimeNow;

#ifdef ENABLE_COMMON_DVFS
	unsigned long uLockFlags;
#endif

	psUtilFWCb = psDevInfo->psRGXFWIfGpuUtilFWCb;
	paui64StatsCounters = &psUtilFWCb->aui64StatsCounters[0];

#ifndef ENABLE_COMMON_DVFS
	OSLockAcquire(psDevInfo->hGPUUtilLock);
#else
	spin_lock_irqsave(&psDevInfo->sGPUUtilLock, uLockFlags);
#endif

	ui64TimeNow = RGXFWIF_GPU_UTIL_GET_TIME(RGXTimeCorrGetClockns64());

	/* Update counters to account for the time since the last update */
	ui64LastState  = RGXFWIF_GPU_UTIL_GET_STATE(psUtilFWCb->ui64LastWord);
	ui64LastTime   = RGXFWIF_GPU_UTIL_GET_TIME(psUtilFWCb->ui64LastWord);
	ui64LastPeriod = RGXFWIF_GPU_UTIL_GET_PERIOD(ui64TimeNow, ui64LastTime);
	paui64StatsCounters[ui64LastState] += ui64LastPeriod;

	/* Update state and time of the latest update */
	psUtilFWCb->ui64LastWord = RGXFWIF_GPU_UTIL_MAKE_WORD(ui64TimeNow, ui64LastState);

#ifndef ENABLE_COMMON_DVFS
	OSLockRelease(psDevInfo->hGPUUtilLock);
#else
	spin_unlock_irqrestore(&psDevInfo->sGPUUtilLock, uLockFlags);
#endif
}

static INLINE PVRSRV_ERROR RGXDoStop(PVRSRV_DEVICE_NODE *psDeviceNode)
{
	PVRSRV_ERROR eError;

	pr_info("pvr-mtk[S3FLOW]: RGXDoStop enter\n");

#if defined(SUPPORT_TRUSTED_DEVICE) && !defined(NO_HARDWARE) && !defined(SUPPORT_SECURITY_VALIDATION)
	PVRSRV_DEVICE_CONFIG *psDevConfig = psDeviceNode->psDevConfig;
	PVRSRV_VZ_RET_IF_MODE(GUEST, PVRSRV_OK);

	if (psDevConfig->pfnTDRGXStop == NULL)
	{
		PVR_DPF((PVR_DBG_ERROR, "RGXPrePowerState: TDRGXStop not implemented!"));
		return PVRSRV_ERROR_NOT_IMPLEMENTED;
	}

	eError = psDevConfig->pfnTDRGXStop(psDevConfig->hSysData);
#else
	PVRSRV_RGXDEV_INFO *psDevInfo = psDeviceNode->pvDevice;
	PVRSRV_VZ_RET_IF_MODE(GUEST, PVRSRV_OK);

	eError = RGXStop(&psDevInfo->sLayerParams);
	pr_info("pvr-mtk[S3FLOW]: RGXStop ret=%d\n", eError);
#endif

	return eError;
}

/*
	RGXPrePowerState
*/
PVRSRV_ERROR RGXPrePowerState(IMG_HANDLE				hDevHandle,
                              PVRSRV_DEV_POWER_STATE	eNewPowerState,
                              PVRSRV_DEV_POWER_STATE	eCurrentPowerState,
                              IMG_BOOL					bForced)
{
	PVRSRV_ERROR eError = PVRSRV_OK;
	PVRSRV_DEVICE_NODE    *psDeviceNode = hDevHandle;

	if (PVRSRV_VZ_MODE_IS(GUEST) || (psDeviceNode->bAutoVzFwIsUp))
	{
		return PVRSRV_OK;
	}

	if ((eNewPowerState != eCurrentPowerState) &&
	    (eNewPowerState != PVRSRV_DEV_POWER_STATE_ON))
	{
		PVRSRV_RGXDEV_INFO    *psDevInfo = psDeviceNode->pvDevice;
		RGXFWIF_KCCB_CMD      sPowCmd;
		IMG_UINT32            ui32CmdKCCBSlot;

		RGXFWIF_SYSDATA *psFwSysData = psDevInfo->psRGXFWIfFwSysData;

		/* Send the Power off request to the FW */
		sPowCmd.eCmdType = RGXFWIF_KCCB_CMD_POW;
		sPowCmd.uCmdData.sPowData.ePowType = RGXFWIF_POW_OFF_REQ;
		sPowCmd.uCmdData.sPowData.uPowerReqData.bForced = bForced;

	eError = SyncPrimSet(psDevInfo->psPowSyncPrim, 0);
		if (eError != PVRSRV_OK)
		{
			PVR_DPF((PVR_DBG_ERROR, "%s: Failed to set Power sync prim",
					__func__));
			return eError;
		}

		eError = RGXSendCommandAndGetKCCBSlot(psDevInfo,
		                                      &sPowCmd,
		                                      PDUMP_FLAGS_NONE,
		                                      &ui32CmdKCCBSlot);
		if (eError != PVRSRV_OK)
		{
			PVR_DPF((PVR_DBG_ERROR, "%s: Failed to send Power off request",
					__func__));
			return eError;
		}

		/* Wait for the firmware to complete processing. It cannot use PVRSRVWaitForValueKM as it relies
		   on the EventObject which is signalled in this MISR */
		eError = RGXPollForGPCommandCompletion(psDeviceNode,
								  psDevInfo->psPowSyncPrim->pui32LinAddr,
								  0x1, 0xFFFFFFFF);

		if (eError != PVRSRV_OK && pvr_state_wait)
		{
			unsigned int st = (unsigned int)psFwSysData->ePowState;
			if (st == RGXFWIF_POW_OFF || st == RGXFWIF_POW_IDLE ||
			    st == RGXFWIF_POW_FORCED_IDLE)
			{
				pr_info("pvr-mtk: state-wait: powoff accepted with pow=%u\n", st);
				eError = PVRSRV_OK;
			}
		}

		/* Check the Power state after the answer */
		if (eError == PVRSRV_OK)
		{
			/* Finally, de-initialise some registers. */
			if (psFwSysData->ePowState == RGXFWIF_POW_OFF)
			{
#if !defined(NO_HARDWARE)
#if defined(RGX_FW_IRQ_OS_COUNTERS)
				IMG_UINT32 ui32idx = RGXFW_HOST_OS;
#else
				IMG_UINT32 ui32idx;
				for_each_irq_cnt(ui32idx)
#endif /* RGX_FW_IRQ_OS_COUNTERS */
				{
					IMG_UINT32 ui32IrqCnt;

					get_irq_cnt_val(ui32IrqCnt, ui32idx, psDevInfo);
					pr_info("pvr-mtk: IRQCNT idx=%u expect=%u host=%u\n",
					        ui32idx, ui32IrqCnt,
					        psDevInfo->aui32SampleIRQCount[ui32idx]);

					/* Wait for the pending FW processor to host interrupts to come back. */
					eError = PVRSRVPollForValueKM(psDeviceNode,
					                              (IMG_UINT32 __iomem *)&psDevInfo->aui32SampleIRQCount[ui32idx],
					                              ui32IrqCnt,
					                              0xffffffff,
					                              POLL_FLAG_LOG_ERROR);

					if (eError != PVRSRV_OK)
					{
						PVR_DPF((PVR_DBG_ERROR,
								"%s: Wait for pending interrupts failed." MSG_IRQ_CNT_TYPE " %u Host: %u, FW: %u",
								__func__,
								ui32idx,
								psDevInfo->aui32SampleIRQCount[ui32idx],
								ui32IrqCnt));

						RGX_WaitForInterruptsTimeout(psDevInfo);
						/* S3: the FW may update its IRQ counter after we acked the
						 * level IRQ (no second IRQ is raised). Re-sample once and,
						 * if it moved, align the host counter so the power
						 * transition can complete. */
						{
							IMG_UINT32 ui32Now;

							get_irq_cnt_val(ui32Now, ui32idx, psDevInfo);
							pr_info("pvr-mtk: IRQCNT after-timeout idx=%u now=%u host=%u ev=%08x wst=%08x\n",
							        ui32idx, ui32Now,
							        psDevInfo->aui32SampleIRQCount[ui32idx],
							        OSReadHWReg32(psDevInfo->pvRegsBaseKM, 0x130),
							        OSReadHWReg32(psDevInfo->pvRegsBaseKM, RGX_CR_MIPS_WRAPPER_IRQ_STATUS));
							if (psDevInfo->aui32SampleIRQCount[ui32idx] != ui32Now)
							{
								psDevInfo->aui32SampleIRQCount[ui32idx] = ui32Now;
							}
							/* The timeout handler above already resamples the
							 * counter; if the counts now agree the pending IRQ
							 * has been accounted for, so clear the stale error. */
							if (psDevInfo->aui32SampleIRQCount[ui32idx] == ui32Now)
							{
								pr_info("pvr-mtk: IRQ counts aligned (host=%u), continue\n",
								        ui32Now);
								eError = PVRSRV_OK;
							}
						}
					}
				}
#endif /* NO_HARDWARE */

				/* Update GPU frequency and timer correlation related data */
				RGXTimeCorrEnd(psDeviceNode, RGXTIMECORR_EVENT_POWER);

				/* Update GPU state counters */
				_RGXUpdateGPUUtilStats(psDevInfo);

#if defined(SUPPORT_LINUX_DVFS)
				eError = SuspendDVFS();
				if (eError != PVRSRV_OK)
				{
					PVR_DPF((PVR_DBG_ERROR, "%s: Failed to suspend DVFS", __func__));
					return eError;
				}
#endif

				psDevInfo->bRGXPowered = IMG_FALSE;

				eError = RGXDoStop(psDeviceNode);
				if (eError != PVRSRV_OK)
				{
					/* Power down failures are treated as successful since the power was removed but logged. */
					PVR_DPF((PVR_DBG_WARNING, "%s: RGXDoStop failed (%s)",
							__func__, PVRSRVGetErrorString(eError)));
					psDevInfo->ui32ActivePMReqNonIdle++;
					eError = PVRSRV_OK;
				}
			}
			else if (g_pvrNoSync ||
			         (pvr_state_wait &&
			          (psFwSysData->ePowState == RGXFWIF_POW_IDLE ||
			           psFwSysData->ePowState == RGXFWIF_POW_FORCED_IDLE)))
			{
				pr_info("pvr-mtk: no-sync: pow state %u treated as OFF (bypass)\n",
				        (unsigned)psFwSysData->ePowState);
				/* S3 bypass teardown: mirror the normal POW_OFF path. */
				RGXTimeCorrEnd(psDeviceNode, RGXTIMECORR_EVENT_POWER);
				_RGXUpdateGPUUtilStats(psDevInfo);
				psDevInfo->bRGXPowered = IMG_FALSE;
				eError = RGXDoStop(psDeviceNode);
				if (eError != PVRSRV_OK)
				{
					pr_info("pvr-mtk: no-sync: RGXDoStop failed (%s), ignored\n",
					        PVRSRVGetErrorString(eError));
					psDevInfo->ui32ActivePMReqNonIdle++;
					eError = PVRSRV_OK;
				}
			}
			else
			{
				/* the sync was updated but the pow state isn't off -> the FW denied the transition */
				eError = PVRSRV_ERROR_DEVICE_POWER_CHANGE_DENIED;

				if (bForced)
				{	/* It is an error for a forced request to be denied */
					PVR_DPF((PVR_DBG_ERROR,
							 "%s: Failure to power off during a forced power off. FW: %d",
							 __func__, psFwSysData->ePowState));
				}
			}
		}
		else if (eError == PVRSRV_ERROR_TIMEOUT)
		{
			/* timeout waiting for the FW to ack the request: return timeout */
			PVR_DPF((PVR_DBG_WARNING,
					 "%s: Timeout waiting for powoff ack from the FW",
					 __func__));
		}
		else
		{
			PVR_DPF((PVR_DBG_ERROR,
					 "%s: Error waiting for powoff ack from the FW (%s)",
					 __func__, PVRSRVGetErrorString(eError)));
			eError = PVRSRV_ERROR_DEVICE_POWER_CHANGE_FAILURE;
		}
	}

	return eError;
}

#if defined(TRACK_FW_BOOT)
static INLINE void RGXCheckFWBootStage(PVRSRV_RGXDEV_INFO *psDevInfo)
{
	FW_BOOT_STAGE eStage;

	if (RGX_IS_FEATURE_VALUE_SUPPORTED(psDevInfo, META))
	{
		/* Boot stage temporarily stored to the register below */
		eStage = OSReadHWReg32(psDevInfo->pvRegsBaseKM,
		                       RGX_FW_BOOT_STAGE_REGISTER);
	}
	else if (RGX_IS_FEATURE_SUPPORTED(psDevInfo, RISCV_FW_PROCESSOR))
	{
		eStage = OSReadHWReg32(psDevInfo->pvRegsBaseKM, RGX_CR_SCRATCH14);
	}
	else
	{
		IMG_BYTE *pbBootData;

		if (PVRSRV_OK != DevmemAcquireCpuVirtAddr(psDevInfo->psRGXFWDataMemDesc,
		                                          (void**)&pbBootData))
		{
			PVR_DPF((PVR_DBG_ERROR, "%s: Could not acquire pointer to FW boot stage", __func__));
			eStage = FW_BOOT_STAGE_NOT_AVAILABLE;
		}
		else
		{
			pbBootData += RGXGetFWImageSectionOffset(NULL, MIPS_BOOT_DATA);

			eStage = *(FW_BOOT_STAGE*)&pbBootData[RGXMIPSFW_BOOT_STAGE_OFFSET];

			if (eStage == FW_BOOT_STAGE_TLB_INIT_FAILURE)
			{
				RGXMIPSFW_BOOT_DATA *psBootData =
					(RGXMIPSFW_BOOT_DATA*) (pbBootData + RGXMIPSFW_BOOTLDR_CONF_OFFSET);

				PVR_LOG(("MIPS TLB could not be initialised. Boot data info:"
						 " num PT pages %u, log2 PT page size %u, PT page addresses"
						 " %"IMG_UINT64_FMTSPECx " %"IMG_UINT64_FMTSPECx
						 " %"IMG_UINT64_FMTSPECx " %"IMG_UINT64_FMTSPECx,
						 psBootData->ui32PTNumPages,
						 psBootData->ui32PTLog2PageSize,
						 psBootData->aui64PTPhyAddr[0U],
						 psBootData->aui64PTPhyAddr[1U],
						 psBootData->aui64PTPhyAddr[2U],
						 psBootData->aui64PTPhyAddr[3U]));
			}

			DevmemReleaseCpuVirtAddr(psDevInfo->psRGXFWDataMemDesc);
		}
	}

	PVR_LOG(("%s: FW reached boot stage %i/%i.",
	         __func__, eStage, FW_BOOT_INIT_DONE));
}
#endif

static INLINE PVRSRV_ERROR RGXDoStart(PVRSRV_DEVICE_NODE *psDeviceNode)
{
	PVRSRV_ERROR eError;
	PVRSRV_RGXDEV_INFO *psDevInfo = psDeviceNode->pvDevice;
	IMG_UINT32 ui32Idx;

	/* S3: clear sampled IRQ counts before FW start to avoid stale
	 * PrePowerState/health-check waits misjudging pending IRQs. */
	for (ui32Idx = 0; ui32Idx < RGXFW_THREAD_NUM; ui32Idx++)
	{
		psDevInfo->aui32SampleIRQCount[ui32Idx] = 0;
	}

#if defined(SUPPORT_TRUSTED_DEVICE) && !defined(NO_HARDWARE) && !defined(SUPPORT_SECURITY_VALIDATION)
	{
		PVRSRV_DEVICE_CONFIG *psDevConfig = psDeviceNode->psDevConfig;

		if (psDevConfig->pfnTDRGXStart == NULL)
		{
			PVR_DPF((PVR_DBG_ERROR, "RGXPostPowerState: TDRGXStart not implemented!"));
			return PVRSRV_ERROR_NOT_IMPLEMENTED;
		}

		eError = psDevConfig->pfnTDRGXStart(psDevConfig->hSysData);
	}
#else
	eError = RGXStart(&psDevInfo->sLayerParams);
#endif

	return eError;
}


#if defined(NO_HARDWARE) && defined(PDUMP)

#if 0
#include "rgxtbdefs.h"

#else

/*
    Register RGX_TB_SYSTEM_STATUS
*/
#define RGX_TB_SYSTEM_STATUS                              (0x00E0U)
#define RGX_TB_SYSTEM_STATUS_MASKFULL                     (IMG_UINT64_C(0x00000000030100FF))
/*
directly indicates the status of power_abort flag from the power management controller (RGX_PRCM)
*/
#define RGX_TB_SYSTEM_STATUS_HOST_POWER_EVENT_ABORT_SHIFT (25U)
#define RGX_TB_SYSTEM_STATUS_HOST_POWER_EVENT_ABORT_CLRMSK (IMG_UINT64_C(0XFFFFFFFFFDFFFFFF))
#define RGX_TB_SYSTEM_STATUS_HOST_POWER_EVENT_ABORT_EN    (IMG_UINT64_C(0X0000000002000000))
/*
directly indicates the status of power_complete flag from the power management controller (RGX_PRCM)
*/
#define RGX_TB_SYSTEM_STATUS_HOST_POWER_EVENT_COMPLETE_SHIFT (24U)
#define RGX_TB_SYSTEM_STATUS_HOST_POWER_EVENT_COMPLETE_CLRMSK (IMG_UINT64_C(0XFFFFFFFFFEFFFFFF))
#define RGX_TB_SYSTEM_STATUS_HOST_POWER_EVENT_COMPLETE_EN (IMG_UINT64_C(0X0000000001000000))
/*
directly indicates the status of GPU's hmmu_irq
*/
#define RGX_TB_SYSTEM_STATUS_HMMU_IRQ_SHIFT               (16U)
#define RGX_TB_SYSTEM_STATUS_HMMU_IRQ_CLRMSK              (IMG_UINT64_C(0XFFFFFFFFFFFEFFFF))
#define RGX_TB_SYSTEM_STATUS_HMMU_IRQ_EN                  (IMG_UINT64_C(0X0000000000010000))
/*
directly indicates the status of GPU's irq per OS_ID
*/
#define RGX_TB_SYSTEM_STATUS_IRQ_SHIFT                    (1U)
#define RGX_TB_SYSTEM_STATUS_IRQ_CLRMSK                   (IMG_UINT64_C(0XFFFFFFFFFFFFFE01))
/*
old deprecated single irq
*/
#define RGX_TB_SYSTEM_STATUS_OLD_IRQ_SHIFT                    (0U)
#define RGX_TB_SYSTEM_STATUS_OLD_IRQ_CLRMSK                   (IMG_UINT64_C(0XFFFFFFFFFFFFFFFE))
#endif

static PVRSRV_ERROR
_ValidateIrqs(PVRSRV_RGXDEV_INFO *psDevInfo)
{
	IMG_UINT32 ui32OSid;
	IMG_UINT32 ui32ConfigFlags;
	PDUMP_FLAGS_T ui32PDumpFlags = PDUMP_FLAGS_CONTINUOUS;

	{
		PVRSRV_ERROR eError;
		RGXFWIF_SYSDATA *psFwSysData;

		eError = DevmemAcquireCpuVirtAddr(psDevInfo->psRGXFWIfFwSysDataMemDesc, (void **)&psFwSysData);
		if (eError != PVRSRV_OK)
		{
			PVR_DPF((PVR_DBG_ERROR,
					"%s: Failed to acquire OS Config (%u)",
					__func__,
					eError));
			return eError;
		}

		ui32ConfigFlags = psFwSysData->ui32ConfigFlags;

		DevmemReleaseCpuVirtAddr(psDevInfo->psRGXFWIfFwSysDataMemDesc);
	}

	/* Check if the Validation IRQ flag is set */
	if ((ui32ConfigFlags & RGXFWIF_INICFG_VALIDATE_IRQ) == 0)
	{
		return PVRSRV_OK;
	}

	PDUMPIF("IMG_PVR_TESTBENCH", ui32PDumpFlags);
	PDUMPCOMMENTWITHFLAGS(ui32PDumpFlags, "Poll for TB irq status to be set (irqs signalled)...");
	PDUMPREGPOL(RGX_TB_PDUMPREG_NAME,
	            RGX_TB_SYSTEM_STATUS,
				~RGX_TB_SYSTEM_STATUS_IRQ_CLRMSK,
				~RGX_TB_SYSTEM_STATUS_IRQ_CLRMSK,
				ui32PDumpFlags,
				PDUMP_POLL_OPERATOR_EQUAL);

	PDUMPCOMMENTWITHFLAGS(ui32PDumpFlags, "... and then clear them");
	for (ui32OSid = 0; ui32OSid < RGXFW_MAX_NUM_OS; ui32OSid++)
	{
		PDUMPREG32(RGX_PDUMPREG_NAME,
		           RGX_CR_IRQ_OS0_EVENT_CLEAR + ui32OSid * 0x10000,
		           RGX_CR_IRQ_OS0_EVENT_CLEAR_MASKFULL,
		           ui32PDumpFlags);
	}

	PDUMPFI("IMG_PVR_TESTBENCH", ui32PDumpFlags);

	/* Poll on all the interrupt status registers for all OSes */
	PDUMPCOMMENTWITHFLAGS(ui32PDumpFlags, "Validate Interrupt lines.");

	for (ui32OSid = 0; ui32OSid < RGXFW_MAX_NUM_OS; ui32OSid++)
	{
		PDUMPREGPOL(RGX_PDUMPREG_NAME,
		            RGX_CR_IRQ_OS0_EVENT_STATUS + ui32OSid * 0x10000,
		            0x0,
		            0xFFFFFFFF,
		            ui32PDumpFlags,
		            PDUMP_POLL_OPERATOR_EQUAL);
	}

	return PVRSRV_OK;
}
#endif /* defined(NO_HARDWARE) && defined(PDUMP) */

#if defined(SUPPORT_GPUVIRT_VALIDATION) && !defined(NO_HARDWARE)
/*
 * To validate the MTS unit we do the following:
 *  - Immediately after firmware loading for each OSID
 *    - Write the OSid to a memory location shared with FW
 *    - Kick the register of that OSid
 *         (Uncounted, DM 0)
 *    - FW clears the memory location if OSid matches
 *    - Host checks that memory location is cleared
 *
 *  See firmware/devices/rgx/rgxfw_bg.c
 */
static PVRSRV_ERROR RGXVirtualisationPowerupSidebandTest(PVRSRV_DEVICE_NODE	 *psDeviceNode,
														 RGXFWIF_SYSINIT *psFwSysInit,
														 PVRSRV_RGXDEV_INFO	 *psDevInfo)
{
	IMG_UINT32 ui32ScheduleRegister;
	IMG_UINT32 ui32OSid;
	IMG_UINT32 ui32KickType;
	IMG_UINT32 ui32OsRegBanksMapped = (psDeviceNode->psDevConfig->ui32RegsSize / RGX_VIRTUALISATION_REG_SIZE_PER_OS);

	/* Nothing to do if the device does not support GPU_VIRTUALISATION */
	if (!PVRSRV_IS_FEATURE_SUPPORTED(psDeviceNode, GPU_VIRTUALISATION))
	{
		return PVRSRV_OK;
	}

	PVR_DPF((PVR_DBG_MESSAGE, "Testing per-os kick registers:"));

	/* Need to get the maximum supported OSid value from the per-device info.
	 * This can change according to how much memory is physically present and
	 * what the carve-out mapping looks like (provided by the module load-time
	 * parameters).
	 */
	ui32OsRegBanksMapped = MIN(ui32OsRegBanksMapped, psDeviceNode->ui32NumOSId);

	if (ui32OsRegBanksMapped != RGXFW_MAX_NUM_OS)
	{
		PVR_DPF((PVR_DBG_WARNING, "The register bank mapped into kernel VA does not cover all OS' registers:"));
		PVR_DPF((PVR_DBG_WARNING, "Maximum OS count = %d / Per-os register banks mapped = %d", RGXFW_MAX_NUM_OS, ui32OsRegBanksMapped));
		PVR_DPF((PVR_DBG_WARNING, "Only first %d MTS registers will be tested", ui32OsRegBanksMapped));
	}

	ui32KickType = RGX_CR_MTS_SCHEDULE_DM_DM0 | RGX_CR_MTS_SCHEDULE_TASK_NON_COUNTED;

	for (ui32OSid = 0; ui32OSid < ui32OsRegBanksMapped; ui32OSid++)
	{
		/* set Test field */
		psFwSysInit->ui32OSKickTest = (ui32OSid << RGXFWIF_KICK_TEST_OSID_SHIFT) | RGXFWIF_KICK_TEST_ENABLED_BIT;
		/* Force a read-back to memory to avoid posted writes on certain buses */
		(void) psFwSysInit->ui32OSKickTest;
		OSWriteMemoryBarrier();

		/* kick register */
		ui32ScheduleRegister = RGX_CR_MTS_SCHEDULE + (ui32OSid * RGX_VIRTUALISATION_REG_SIZE_PER_OS);
		PVR_DPF((PVR_DBG_MESSAGE, "  Testing OS: %u, Kick Reg: %X",
				 ui32OSid,
				 ui32ScheduleRegister));
		OSWriteHWReg32(psDevInfo->pvRegsBaseKM, ui32ScheduleRegister, ui32KickType);
		OSMemoryBarrier();

		/* Wait test enable bit to be unset */
		if (PVRSRVPollForValueKM(psDeviceNode,
								 (IMG_UINT32 *)&psFwSysInit->ui32OSKickTest,
								 0,
								 RGXFWIF_KICK_TEST_ENABLED_BIT,
								 POLL_FLAG_LOG_ERROR | POLL_FLAG_DEBUG_DUMP) != PVRSRV_OK)
		{
			PVR_DPF((PVR_DBG_ERROR, "Testing OS %u kick register failed: firmware did not clear test location (contents: 0x%X)",
					 ui32OSid,
					 psFwSysInit->ui32OSKickTest));

			return PVRSRV_ERROR_TIMEOUT;
		}

		/* sanity check that the value is what we expect */
		if (psFwSysInit->ui32OSKickTest != 0)
		{
			PVR_DPF((PVR_DBG_ERROR, "Testing OS %u kick register failed: firmware wrote 0x%X to test location",
					 ui32OSid,
					 psFwSysInit->ui32OSKickTest));
			return PVRSRV_ERROR_INIT_FAILURE;
		}

		PVR_DPF((PVR_DBG_MESSAGE, "    PASS"));
	}

	PVR_LOG(("MTS passed sideband tests"));
	return PVRSRV_OK;
}
#endif /* defined(SUPPORT_GPUVIRT_VALIDATION) && !defined(NO_HARDWARE) */

/*
	RGXPostPowerState
*/
extern void mtk_pvr_dump_spm(const char *tag);

PVRSRV_ERROR RGXPostPowerState(IMG_HANDLE				hDevHandle,
                               PVRSRV_DEV_POWER_STATE	eNewPowerState,
                               PVRSRV_DEV_POWER_STATE	eCurrentPowerState,
                               IMG_BOOL					bForced)
{
	if ((eNewPowerState != eCurrentPowerState) &&
	    (eCurrentPowerState != PVRSRV_DEV_POWER_STATE_ON))
	{
		PVRSRV_ERROR		 eError;
		PVRSRV_DEVICE_NODE	 *psDeviceNode = hDevHandle;
		PVRSRV_RGXDEV_INFO	 *psDevInfo = psDeviceNode->pvDevice;

		if (PVRSRV_VZ_MODE_IS(GUEST) || (psDeviceNode->bAutoVzFwIsUp))
		{
			psDevInfo->bRGXPowered = IMG_TRUE;
			return PVRSRV_OK;
		}

		if (eCurrentPowerState == PVRSRV_DEV_POWER_STATE_OFF)
		{
			pr_info("pvr-mtk[S3FLOW]: PostPowerState ON enter\n");
			/* Update timer correlation related data */
			RGXTimeCorrBegin(psDeviceNode, RGXTIMECORR_EVENT_POWER);

			/* Update GPU state counters */
			_RGXUpdateGPUUtilStats(psDevInfo);

			mtk_pvr_dump_spm("pre-start");
			pvr_maybe_move_prim(psDevInfo);
			pr_info("pvr-mtk[S3FLOW]: RGXDoStart begin\n");
			eError = RGXDoStart(psDeviceNode);
			pr_info("pvr-mtk[S3FLOW]: RGXDoStart ret=%d\n", eError);
			if (eError != PVRSRV_OK)
			{
				PVR_DPF((PVR_DBG_ERROR, "RGXPostPowerState: RGXDoStart failed"));
				return eError;
			}

			mtk_pvr_dump_spm("post-start");
			OSMemoryBarrier();

			/*
			 * Check whether the FW has started by polling on bFirmwareStarted flag
			 */
			pr_info("pvr-mtk[S3FLOW]: poll FW started begin\n");
			if (PVRSRVPollForValueKM(psDeviceNode,
			                         (IMG_UINT32 __iomem *)&psDevInfo->psRGXFWIfSysInit->bFirmwareStarted,
			                         IMG_TRUE,
			                         0xFFFFFFFF,
			                         POLL_FLAG_LOG_ERROR | POLL_FLAG_DEBUG_DUMP) != PVRSRV_OK)
			{
				PVR_DPF((PVR_DBG_ERROR, "RGXPostPowerState: Polling for 'FW started' flag failed."));
				pr_info("pvr-mtk: boot stage=%u meta_boot=%08x soft_reset=%08x sys_bus_secure=%08x slc_idle=%08x sidekick_idle=%08x",
				         OSReadHWReg32(psDevInfo->pvRegsBaseKM, RGX_FW_BOOT_STAGE_REGISTER),
				         OSReadHWReg32(psDevInfo->pvRegsBaseKM, RGX_CR_META_BOOT),
				         OSReadHWReg32(psDevInfo->pvRegsBaseKM, RGX_CR_SOFT_RESET),
				         OSReadHWReg32(psDevInfo->pvRegsBaseKM, RGX_CR_SYS_BUS_SECURE),
				         OSReadHWReg32(psDevInfo->pvRegsBaseKM, RGX_CR_SLC_IDLE),
				         OSReadHWReg32(psDevInfo->pvRegsBaseKM, RGX_CR_SIDEKICK_IDLE));
				{
					void *pvCPUVA = NULL;
					IMG_UINT32 ui32GPUVal = 0xDEADBEEF;
					PVRSRV_ERROR eRd;

					eRd = DevmemAcquireCpuVirtAddr(psDevInfo->psRGXFWCodeMemDesc, &pvCPUVA);
					if (eRd == PVRSRV_OK)
					{
						eRd = RGXReadMETAAddr(psDevInfo,
						                      (IMG_UINT32)psDevInfo->sFWCodeDevVAddrBase.uiAddr,
						                      &ui32GPUVal);
						pr_info("pvr-mtk: FW[0] cpu=%08x gpu=%08x rc=%d\n",
						        *(IMG_UINT32 *)pvCPUVA, ui32GPUVal, eRd);
						DevmemReleaseCpuVirtAddr(psDevInfo->psRGXFWCodeMemDesc);
					}
					else
					{
						pr_info("pvr-mtk: FW code CPU VA unavailable (%d)\n", eRd);
					}

					pr_info("pvr-mtk: mslvctrl1=%08x mslvirqstatus=%08x\n",
					        OSReadHWReg32(psDevInfo->pvRegsBaseKM, RGX_CR_META_SP_MSLVCTRL1),
					        OSReadHWReg32(psDevInfo->pvRegsBaseKM, RGX_CR_META_SP_MSLVIRQSTATUS));
					pr_info("pvr-mtk: bif_cat0=%llx mmu_fault=%llx mmu_cbase=%llx garten=%llx\n",
					        (unsigned long long)OSReadHWReg64(psDevInfo->pvRegsBaseKM, RGX_CR_BIF_CAT_BASE0),
					        (unsigned long long)OSReadHWReg64(psDevInfo->pvRegsBaseKM, RGX_CR_MMU_FAULT_STATUS),
					        (unsigned long long)OSReadHWReg64(psDevInfo->pvRegsBaseKM, RGX_CR_MMU_CBASE_MAPPING),
					        (unsigned long long)OSReadHWReg64(psDevInfo->pvRegsBaseKM, RGX_CR_MTS_GARTEN_WRAPPER_CONFIG));
				}
				eError = PVRSRV_ERROR_TIMEOUT;

#if defined(TRACK_FW_BOOT)
				RGXCheckFWBootStage(psDevInfo);
#endif

				/*
				 * When bFirmwareStarted fails some info may be gained by doing the following
				 * debug dump but unfortunately it could be potentially dangerous if the reason
				 * for not booting is the GPU power is not ON. However, if we have reached this
				 * point the System Layer has returned without errors, we assume the GPU power
				 * is indeed ON.
				 */
				RGXDumpRGXDebugSummary(NULL, NULL, psDeviceNode->pvDevice, IMG_TRUE);
				RGXDumpRGXRegisters(NULL, NULL, psDeviceNode->pvDevice);

				return eError;
			}

#if defined(PDUMP)
			PDUMPCOMMENTWITHFLAGS(PDUMP_FLAGS_CONTINUOUS, "Wait for the Firmware to start.");
			eError = DevmemPDumpDevmemPol32(psDevInfo->psRGXFWIfSysInitMemDesc,
			                                offsetof(RGXFWIF_SYSINIT, bFirmwareStarted),
			                                IMG_TRUE,
			                                0xFFFFFFFFU,
			                                PDUMP_POLL_OPERATOR_EQUAL,
			                                PDUMP_FLAGS_CONTINUOUS);

			if (eError != PVRSRV_OK)
			{
				PVR_DPF((PVR_DBG_ERROR,
				         "RGXPostPowerState: problem pdumping POL for psRGXFWIfSysInitMemDesc (%d)",
				         eError));
				return eError;
			}

#if defined(NO_HARDWARE) && defined(PDUMP)
			eError = _ValidateIrqs(psDevInfo);
			if (eError != PVRSRV_OK)
			{
				return eError;
			}
#endif
#endif

#if defined(SUPPORT_GPUVIRT_VALIDATION) && !defined(NO_HARDWARE)
			eError = RGXVirtualisationPowerupSidebandTest(psDeviceNode, psDevInfo->psRGXFWIfSysInit, psDevInfo);
			if (eError != PVRSRV_OK)
			{
				return eError;
			}
#endif

#if defined(PVRSRV_ENABLE_PROCESS_STATS)
			SetFirmwareStartTime(psDevInfo->psRGXFWIfSysInit->ui32FirmwareStartedTimeStamp);
#endif

			HTBSyncPartitionMarker(psDevInfo->psRGXFWIfSysInit->ui32MarkerVal);

			psDevInfo->bRGXPowered = IMG_TRUE;

#if defined(SUPPORT_LINUX_DVFS)
			eError = ResumeDVFS();
			if (eError != PVRSRV_OK)
			{
				PVR_DPF((PVR_DBG_ERROR, "RGXPostPowerState: Failed to resume DVFS"));
				return eError;
			}
#endif
		}
	}

	PDUMPCOMMENT("RGXPostPowerState: Current state: %d, New state: %d", eCurrentPowerState, eNewPowerState);

	return PVRSRV_OK;
}

/*
	RGXPreClockSpeedChange
*/
PVRSRV_ERROR RGXPreClockSpeedChange(IMG_HANDLE				hDevHandle,
                                    PVRSRV_DEV_POWER_STATE	eCurrentPowerState)
{
	PVRSRV_ERROR		eError = PVRSRV_OK;
	PVRSRV_DEVICE_NODE	*psDeviceNode = hDevHandle;
	PVRSRV_RGXDEV_INFO	*psDevInfo = psDeviceNode->pvDevice;
	RGX_DATA			*psRGXData = (RGX_DATA*)psDeviceNode->psDevConfig->hDevData;
	RGXFWIF_SYSDATA		*psFwSysData = psDevInfo->psRGXFWIfFwSysData;
	PVRSRV_VZ_RET_IF_MODE(GUEST, PVRSRV_OK);
	PVR_UNREFERENCED_PARAMETER(psRGXData);

	PVR_DPF((PVR_DBG_MESSAGE, "RGXPreClockSpeedChange: RGX clock speed was %uHz",
			psRGXData->psRGXTimingInfo->ui32CoreClockSpeed));

	if ((eCurrentPowerState != PVRSRV_DEV_POWER_STATE_OFF) &&
	    (psFwSysData->ePowState != RGXFWIF_POW_OFF))
	{
		/* Update GPU frequency and timer correlation related data */
		RGXTimeCorrEnd(psDeviceNode, RGXTIMECORR_EVENT_DVFS);
	}

	return eError;
}

/*
	RGXPostClockSpeedChange
*/
PVRSRV_ERROR RGXPostClockSpeedChange(IMG_HANDLE				hDevHandle,
                                     PVRSRV_DEV_POWER_STATE	eCurrentPowerState)
{
	PVRSRV_DEVICE_NODE	*psDeviceNode = hDevHandle;
	PVRSRV_RGXDEV_INFO	*psDevInfo = psDeviceNode->pvDevice;
	RGX_DATA			*psRGXData = (RGX_DATA*)psDeviceNode->psDevConfig->hDevData;
	PVRSRV_ERROR		eError = PVRSRV_OK;
	RGXFWIF_SYSDATA		*psFwSysData = psDevInfo->psRGXFWIfFwSysData;
	IMG_UINT32			ui32NewClockSpeed = psRGXData->psRGXTimingInfo->ui32CoreClockSpeed;
	PVRSRV_VZ_RET_IF_MODE(GUEST, PVRSRV_OK);

	/* Update runtime configuration with the new value */
	psDevInfo->psRGXFWIfRuntimeCfg->ui32CoreClockSpeed = ui32NewClockSpeed;

	if ((eCurrentPowerState != PVRSRV_DEV_POWER_STATE_OFF) &&
	    (psFwSysData->ePowState != RGXFWIF_POW_OFF))
	{
		RGXFWIF_KCCB_CMD sCOREClkSpeedChangeCmd;
		IMG_UINT32 ui32CmdKCCBSlot;

		RGXTimeCorrBegin(psDeviceNode, RGXTIMECORR_EVENT_DVFS);

		sCOREClkSpeedChangeCmd.eCmdType = RGXFWIF_KCCB_CMD_CORECLKSPEEDCHANGE;
		sCOREClkSpeedChangeCmd.uCmdData.sCoreClkSpeedChangeData.ui32NewClockSpeed = ui32NewClockSpeed;

		/* Ensure the new clock speed is written to memory before requesting the FW to read it */
		OSMemoryBarrier();

		PDUMPCOMMENT("Scheduling CORE clock speed change command");

		PDUMPPOWCMDSTART();
		eError = RGXSendCommandAndGetKCCBSlot(psDeviceNode->pvDevice,
		                                      &sCOREClkSpeedChangeCmd,
		                                      PDUMP_FLAGS_NONE,
		                                      &ui32CmdKCCBSlot);
		PDUMPPOWCMDEND();

		if (eError != PVRSRV_OK)
		{
			PDUMPCOMMENT("Scheduling CORE clock speed change command failed");
			PVR_DPF((PVR_DBG_ERROR, "RGXPostClockSpeedChange: Scheduling KCCB command failed. Error:%u", eError));
			return eError;
		}

		PVR_DPF((PVR_DBG_MESSAGE, "RGXPostClockSpeedChange: RGX clock speed changed to %uHz",
				psRGXData->psRGXTimingInfo->ui32CoreClockSpeed));
	}

	return eError;
}

/*!
 ******************************************************************************

 @Function	RGXDustCountChange

 @Description

	Does change of number of DUSTs

 @Input	   hDevHandle : RGX Device Node
 @Input	   ui32NumberOfDusts : Number of DUSTs to make transition to

 @Return   PVRSRV_ERROR :

 ******************************************************************************/
PVRSRV_ERROR RGXDustCountChange(IMG_HANDLE		hDevHandle,
                                IMG_UINT32		ui32NumberOfDusts)
{

	PVRSRV_DEVICE_NODE	*psDeviceNode = hDevHandle;
	PVRSRV_RGXDEV_INFO	*psDevInfo = psDeviceNode->pvDevice;
	PVRSRV_ERROR		eError;
	RGXFWIF_KCCB_CMD	sDustCountChange;
	IMG_UINT32			ui32MaxAvailableDusts = psDevInfo->sDevFeatureCfg.ui32MAXDustCount;
	IMG_UINT32			ui32CmdKCCBSlot;
	RGXFWIF_RUNTIME_CFG *psRuntimeCfg = psDevInfo->psRGXFWIfRuntimeCfg;
	PVRSRV_VZ_RET_IF_MODE(GUEST, PVRSRV_OK);

	if (ui32NumberOfDusts > ui32MaxAvailableDusts)
	{
		eError = PVRSRV_ERROR_INVALID_PARAMS;
		PVR_DPF((PVR_DBG_ERROR,
				"%s: Invalid number of DUSTs (%u) while expecting value within <0,%u>. Error:%u",
				__func__,
				ui32NumberOfDusts,
				ui32MaxAvailableDusts,
				eError));
		return eError;
	}

	psRuntimeCfg->ui32DefaultDustsNumInit = ui32NumberOfDusts;

#if !defined(NO_HARDWARE)
	{
		RGXFWIF_SYSDATA *psFwSysData = psDevInfo->psRGXFWIfFwSysData;

		if (psFwSysData->ePowState == RGXFWIF_POW_OFF)
		{
			return PVRSRV_OK;
		}

		if (psFwSysData->ePowState != RGXFWIF_POW_FORCED_IDLE)
		{
			eError = PVRSRV_ERROR_DEVICE_POWER_CHANGE_DENIED;
			PVR_DPF((PVR_DBG_ERROR,
					 "%s: Attempt to change dust count when not IDLE",
					 __func__));
			return eError;
		}
	}
#endif

	eError = SyncPrimSet(psDevInfo->psPowSyncPrim, 0);
	if (eError != PVRSRV_OK)
	{
		PVR_DPF((PVR_DBG_ERROR, "%s: Failed to set Power sync prim",
				__func__));
		return eError;
	}

	sDustCountChange.eCmdType = RGXFWIF_KCCB_CMD_POW;
	sDustCountChange.uCmdData.sPowData.ePowType = RGXFWIF_POW_NUM_UNITS_CHANGE;
	sDustCountChange.uCmdData.sPowData.uPowerReqData.ui32NumOfDusts = ui32NumberOfDusts;

	PDUMPCOMMENT("Scheduling command to change Dust Count to %u", ui32NumberOfDusts);
	eError = RGXSendCommandAndGetKCCBSlot(psDeviceNode->pvDevice,
	                                      &sDustCountChange,
	                                      PDUMP_FLAGS_NONE,
	                                      &ui32CmdKCCBSlot);

	if (eError != PVRSRV_OK)
	{
		PDUMPCOMMENT("Scheduling command to change Dust Count failed. Error:%u", eError);
		PVR_DPF((PVR_DBG_ERROR,
				 "%s: Scheduling KCCB to change Dust Count failed. Error:%u",
				 __func__, eError));
		return eError;
	}

	/* Wait for the firmware to answer. */
	eError = RGXPollForGPCommandCompletion(psDeviceNode,
	                              psDevInfo->psPowSyncPrim->pui32LinAddr,
								  0x1, 0xFFFFFFFF);

	if (eError != PVRSRV_OK)
	{
		PVR_DPF((PVR_DBG_ERROR, "%s: Timeout waiting for idle request", __func__));
		return eError;
	}

#if defined(PDUMP)
	PDUMPCOMMENT("RGXDustCountChange: Poll for Kernel SyncPrim [0x%p] on DM %d", psDevInfo->psPowSyncPrim->pui32LinAddr, RGXFWIF_DM_GP);

	SyncPrimPDumpPol(psDevInfo->psPowSyncPrim,
	                 1,
	                 0xffffffff,
	                 PDUMP_POLL_OPERATOR_EQUAL,
	                 0);
#endif

	return PVRSRV_OK;
}

/*
 @Function	RGXAPMLatencyChange
*/
PVRSRV_ERROR RGXAPMLatencyChange(IMG_HANDLE		hDevHandle,
                                 IMG_UINT32		ui32ActivePMLatencyms,
                                 IMG_BOOL		bActivePMLatencyPersistant)
{

	PVRSRV_DEVICE_NODE	*psDeviceNode = hDevHandle;
	PVRSRV_RGXDEV_INFO	*psDevInfo = psDeviceNode->pvDevice;
	PVRSRV_ERROR		eError;
	RGXFWIF_RUNTIME_CFG	*psRuntimeCfg = psDevInfo->psRGXFWIfRuntimeCfg;
	IMG_UINT32			ui32CmdKCCBSlot;
	PVRSRV_DEV_POWER_STATE	ePowerState;
	PVRSRV_VZ_RET_IF_MODE(GUEST, PVRSRV_OK);

	eError = PVRSRVPowerLock(psDeviceNode);
	if (eError != PVRSRV_OK)
	{
		PVR_DPF((PVR_DBG_ERROR, "RGXAPMLatencyChange: Failed to acquire power lock"));
		return eError;
	}

	/* Update runtime configuration with the new values and ensure the
	 * new APM latency is written to memory before requesting the FW to
	 * read it
	 */
	psRuntimeCfg->ui32ActivePMLatencyms = ui32ActivePMLatencyms;
	psRuntimeCfg->bActivePMLatencyPersistant = bActivePMLatencyPersistant;
	OSMemoryBarrier();

	eError = PVRSRVGetDevicePowerState(psDeviceNode, &ePowerState);

	if ((eError == PVRSRV_OK) && (ePowerState != PVRSRV_DEV_POWER_STATE_OFF))
	{
		RGXFWIF_KCCB_CMD	sActivePMLatencyChange;
		sActivePMLatencyChange.eCmdType = RGXFWIF_KCCB_CMD_POW;
		sActivePMLatencyChange.uCmdData.sPowData.ePowType = RGXFWIF_POW_APM_LATENCY_CHANGE;
		sActivePMLatencyChange.uCmdData.sPowData.uPowerReqData.ui32ActivePMLatencyms = ui32ActivePMLatencyms;

		PDUMPCOMMENT("Scheduling command to change APM latency to %u", ui32ActivePMLatencyms);
		eError = RGXSendCommandAndGetKCCBSlot(psDeviceNode->pvDevice,
		                                      &sActivePMLatencyChange,
		                                      PDUMP_FLAGS_NONE,
		                                      &ui32CmdKCCBSlot);

		if (eError != PVRSRV_OK)
		{
			PDUMPCOMMENT("Scheduling command to change APM latency failed. Error:%u", eError);
			PVR_DPF((PVR_DBG_ERROR, "RGXAPMLatencyChange: Scheduling KCCB to change APM latency failed. Error:%u", eError));
			goto ErrorExit;
		}
	}

ErrorExit:
	PVRSRVPowerUnlock(psDeviceNode);

	return eError;
}

/*
	RGXActivePowerRequest
*/
PVRSRV_ERROR RGXActivePowerRequest(IMG_HANDLE hDevHandle)
{
	PVRSRV_ERROR eError = PVRSRV_OK;
	PVRSRV_DEVICE_NODE	*psDeviceNode = hDevHandle;
	PVRSRV_RGXDEV_INFO *psDevInfo = psDeviceNode->pvDevice;
	RGXFWIF_SYSDATA *psFwSysData = psDevInfo->psRGXFWIfFwSysData;
	PVRSRV_VZ_RET_IF_MODE(GUEST, PVRSRV_OK);


	psDevInfo->ui32ActivePMReqTotal++;

	/* Powerlock to avoid further requests from racing with the FW hand-shake
	 * from now on (previous kicks to this point are detected by the FW)
	 * PVRSRVPowerLock is replaced with PVRSRVPowerTryLock to avoid
	 * potential dead lock between PDumpWriteLock and PowerLock
	 * during 'DriverLive + PDUMP=1 + EnableAPM=1'.
	 */
	eError = PVRSRVPowerTryLock(psDeviceNode);
	if (eError != PVRSRV_OK)
	{
		if (eError != PVRSRV_ERROR_RETRY)
		{
			PVR_LOG_ERROR(eError, "PVRSRVPowerTryLock");
		}
		else
		{
			psDevInfo->ui32ActivePMReqRetry++;
		}
		goto _RGXActivePowerRequest_PowerLock_failed;
	}

	/* Check again for IDLE once we have the power lock */
	if (psFwSysData->ePowState == RGXFWIF_POW_IDLE)
	{
#if defined(PVRSRV_ENABLE_PROCESS_STATS)
		SetFirmwareHandshakeIdleTime(RGXReadHWTimerReg(psDevInfo)-psFwSysData->ui64StartIdleTime);
#endif

		PDUMPPOWCMDSTART();
		eError = PVRSRVSetDevicePowerStateKM(psDeviceNode,
		                                     PVRSRV_DEV_POWER_STATE_OFF,
		                                     IMG_FALSE); /* forced */
		PDUMPPOWCMDEND();

		if (eError == PVRSRV_OK)
		{
			psDevInfo->ui32ActivePMReqOk++;
		}
		else if (eError == PVRSRV_ERROR_DEVICE_POWER_CHANGE_DENIED)
		{
			psDevInfo->ui32ActivePMReqDenied++;
		}
	}
	else
	{
		psDevInfo->ui32ActivePMReqNonIdle++;
	}

	PVRSRVPowerUnlock(psDeviceNode);

_RGXActivePowerRequest_PowerLock_failed:

	return eError;
}
/*
	RGXForcedIdleRequest
*/

#define RGX_FORCED_IDLE_RETRY_COUNT 10

static int pvr_skip_fidle = 0;
module_param(pvr_skip_fidle, int, 0644);
MODULE_PARM_DESC(pvr_skip_fidle, "skip the forced-idle KCCB request (diagnostic)");

static void pvr_pow_snap(PVRSRV_RGXDEV_INFO *psDevInfo, const char *tag,
                         const RGXFWIF_KCCB_CMD *psCmd, IMG_UINT32 ui32Slot)
{
	RGXFWIF_SYSDATA *psSys = psDevInfo->psRGXFWIfFwSysData;
	IMG_UINT32 ui32Sync = 0xDEADBEEF;

	IMG_UINT32 ui32PaView = 0;

	if (psDevInfo->psPowSyncPrim && psDevInfo->psPowSyncPrim->pui32LinAddr)
		ui32Sync = *(volatile IMG_UINT32 *)psDevInfo->psPowSyncPrim->pui32LinAddr;

	pr_info("pvr-mtk: POW[%s] sync=%u paview=%08x rtn=%08x fwaddr=%08x cpuva=%px kccb=%u/%u kcmds=%u slot=%u pow=%u hwr=%08x fwirq=%u faults=%u\n",
		tag, ui32Sync, ui32PaView,
		(psDevInfo->pui32KernelCCBRtnSlots != NULL) ? psDevInfo->pui32KernelCCBRtnSlots[ui32Slot] : 0xDEADBEEFu,
		psDevInfo->psRGXFWIfFwOsData->sPowerSync.ui32Addr,
		psDevInfo->psPowSyncPrim ? psDevInfo->psPowSyncPrim->pui32LinAddr : NULL,
		psDevInfo->psKernelCCBCtl->ui32WriteOffset,
		psDevInfo->psKernelCCBCtl->ui32ReadOffset,
		psDevInfo->psRGXFWIfFwOsData->ui32KCCBCmdsExecuted,
		ui32Slot,
		psSys ? (unsigned)psSys->ePowState : 999U,
		psSys ? psSys->ui32HWRStateFlags : 0U,
		psSys ? psSys->aui32InterruptCount[0] : 0U,
		psSys ? psSys->ui32FWFaults : 0U);

	if (psCmd)
		pr_info("pvr-mtk: POW[%s] ev=%08x irqen=%08x irqst=%08x mts=%08x\n",
	        tag,
	        OSReadHWReg32(psDevInfo->pvRegsBaseKM, 0x130),
	        OSReadHWReg32(psDevInfo->pvRegsBaseKM, 0x8A0),
	        OSReadHWReg32(psDevInfo->pvRegsBaseKM, 0x8A8),
	        OSReadHWReg32(psDevInfo->pvRegsBaseKM, 0xB00));

	pr_info("pvr-mtk: POW[%s] cmd=%08x powtype=%u req=%u raw=%08x\n",
			tag, psCmd->eCmdType,
			(unsigned)psCmd->uCmdData.sPowData.ePowType,
			(unsigned)psCmd->uCmdData.sPowData.uPowerReqData.ePowRequestType,
			psCmd->uCmdData.sPowData.uPowerReqData.ui32ActivePMLatencyms);
}

static int pvr_os_active = 0;
module_param(pvr_os_active, int, 0644);
MODULE_PARM_DESC(pvr_os_active, "set OS connection state ACTIVE before POW (diagnostic)");

static int pvr_pow_off = 0;
module_param(pvr_pow_off, int, 0644);
MODULE_PARM_DESC(pvr_pow_off, "send POW_OFF_REQ instead of FORCED_IDLE_REQ (A/B)");


static int pvr_prim_in_ccb = 0;
module_param(pvr_prim_in_ccb, int, 0644);
MODULE_PARM_DESC(pvr_prim_in_ccb, "place the POW sync prim inside the KCCB ctl page (diagnostic)");

static void pvr_maybe_move_prim(PVRSRV_RGXDEV_INFO *psDevInfo)
{
	IMG_UINT32 ui32Fw;
	if (pvr_fwtrace)
	{
		pr_info("pvr-mtk: ABI cmd=%u data=%u powreq=%u powoff=%u ccbctl=%u tb=%u\n",
		        (unsigned)sizeof(RGXFWIF_KCCB_CMD),
		        (unsigned)offsetof(RGXFWIF_KCCB_CMD, uCmdData),
		        (unsigned)sizeof(RGXFWIF_POWER_REQUEST),
		        (unsigned)offsetof(RGXFWIF_POWER_REQUEST, uPowerReqData),
		        (unsigned)sizeof(RGXFWIF_CCB_CTL),
		        (unsigned)sizeof(RGXFWIF_TRACEBUF));
		if (psDevInfo->psRGXFWIfTraceBufCtl != NULL)
		{
			RGXFWIF_TRACEBUF *psTb = psDevInfo->psRGXFWIfTraceBufCtl;

			pr_info("pvr-mtk: FWT boot logtype=%08x size=%u\n",
			        psTb->ui32LogType, psTb->ui32TraceBufSizeInDWords);
			if (psTb->ui32TraceBufSizeInDWords == 0)
			{
				PVRSRV_ERROR eTb = RGXTraceBufferInitOnDemandResources(psDevInfo,
				                                                       RGX_FWSHAREDMEM_CPU_RO_ALLOCFLAGS);
				pr_info("pvr-mtk: FWT alloc=%d size=%u fwaddr=%08x buf=%p\n",
				        eTb, psTb->ui32TraceBufSizeInDWords,
				        psTb->sTraceBuf[0].pui32RGXFWIfTraceBuffer.ui32Addr,
				        (void *)psTb->sTraceBuf[0].pui32TraceBuffer);
			}
			psTb->ui32LogType = (RGXFWIF_LOG_TYPE_TRACE |
			                     RGXFWIF_LOG_TYPE_GROUP_MAIN |
			                     RGXFWIF_LOG_TYPE_GROUP_POW);
			pr_info("pvr-mtk: FWT logtype now=%08x\n", psTb->ui32LogType);
		}
	}

	if (pvr_no_apm && psDevInfo->psRGXFWIfFwSysData)
	{
		psDevInfo->psRGXFWIfFwSysData->ui32ConfigFlags &=
			~(IMG_UINT32)RGXFWIF_INICFG_POW_RASCALDUST;
		pr_info("pvr-mtk: APM off, syscfg=%08x\n",
		        psDevInfo->psRGXFWIfFwSysData->ui32ConfigFlags);
	}

	if (!pvr_prim_in_ccb)
		return;
	if (!psDevInfo->psRGXFWIfOsInit || !psDevInfo->psKernelCCBCtl)
		return;
	ui32Fw = psDevInfo->psRGXFWIfOsInit->psKernelCCBCtl.ui32Addr + 0x100;
	psDevInfo->psRGXFWIfFwOsData->sPowerSync.ui32Addr = ui32Fw;
	psDevInfo->psPowSyncPrim->pui32LinAddr =
		(volatile IMG_UINT32 __iomem *)((IMG_UINT8 *)psDevInfo->psKernelCCBCtl + 0x100);
	pr_info("pvr-mtk: prim->ccb page (early) fw=%08x va=%px\n",
	        ui32Fw, psDevInfo->psPowSyncPrim->pui32LinAddr);
}

extern int g_pvrNoSync;

PVRSRV_ERROR RGXForcedIdleRequest(IMG_HANDLE hDevHandle, IMG_BOOL bDeviceOffPermitted)
{
	PVRSRV_DEVICE_NODE    *psDeviceNode = hDevHandle;
	PVRSRV_RGXDEV_INFO    *psDevInfo = psDeviceNode->pvDevice;
	RGXFWIF_KCCB_CMD      sPowCmd;
	PVRSRV_ERROR          eError;
	IMG_UINT32            ui32RetryCount = 0;
	IMG_UINT32            ui32CmdKCCBSlot;
#if !defined(NO_HARDWARE)
	RGXFWIF_SYSDATA *psFwSysData;
#endif
	PVRSRV_VZ_RET_IF_MODE(GUEST, PVRSRV_OK);

	if (pvr_os_active) {
		psDevInfo->psRGXFWIfConnectionCtl->eConnectionOsState = RGXFW_CONNECTION_OS_ACTIVE;
		pr_info("pvr-mtk: OS state forced to ACTIVE\n");
	}

	if (pvr_skip_fidle) {
		pr_info("pvr-mtk: skip-fidle conn fw=%u os=%u fwtok=%08x ostok=%08x mts=%08x kccb w=%u r=%u pow=%u\n",
		        (unsigned)psDevInfo->psRGXFWIfConnectionCtl->eConnectionFwState,
		        (unsigned)psDevInfo->psRGXFWIfConnectionCtl->eConnectionOsState,
		        psDevInfo->psRGXFWIfConnectionCtl->ui32AliveFwToken,
		        psDevInfo->psRGXFWIfConnectionCtl->ui32AliveOsToken,
		        OSReadHWReg32(psDevInfo->pvRegsBaseKM, 0xB00),
		        psDevInfo->psKernelCCBCtl->ui32WriteOffset,
		        psDevInfo->psKernelCCBCtl->ui32ReadOffset,
		        psDevInfo->psRGXFWIfFwSysData ? (unsigned)psDevInfo->psRGXFWIfFwSysData->ePowState : 999U);

		{
			unsigned long long pa1 = 0, pa2 = 0, pa3 = 0;
			const char *k1 = "vm", *k2 = "vm", *k3 = "vm";
			if (psDevInfo->psKernelCCBCtl &&
			    !is_vmalloc_addr(psDevInfo->psKernelCCBCtl)) {
				pa1 = virt_to_phys((void *)psDevInfo->psKernelCCBCtl); k1 = "lin";
			}
			if (psDevInfo->psPowSyncPrim && psDevInfo->psPowSyncPrim->pui32LinAddr &&
			    !is_vmalloc_addr((void *)psDevInfo->psPowSyncPrim->pui32LinAddr)) {
				pa2 = virt_to_phys((void *)psDevInfo->psPowSyncPrim->pui32LinAddr); k2 = "lin";
			}
			if (psDevInfo->psRGXFWIfFwSysData &&
			    !is_vmalloc_addr(psDevInfo->psRGXFWIfFwSysData)) {
				pa3 = virt_to_phys((void *)psDevInfo->psRGXFWIfFwSysData); k3 = "lin";
			}
			pr_info("pvr-mtk: PHY kccbctl(%s)=0x%llx prim(%s)=0x%llx sysdata(%s)=0x%llx\n",
			        k1, pa1, k2, pa2, k3, pa3);
		}
		{
			IMG_DEV_PHYADDR sPtAddr;
			if (MMU_AcquireBaseAddr(psDevInfo->psKernelMMUCtx, &sPtAddr) == PVRSRV_OK)
			{
				void *pvPt = memremap(sPtAddr.uiAddr, 0x10000, MEMREMAP_WB);
				pr_info("pvr-mtk: PT base pa=0x%llx map=%p\n",
				        (unsigned long long)sPtAddr.uiAddr, pvPt);
				if (pvPt)
				{
					unsigned int k;
					unsigned int *pui32 = (unsigned int *)pvPt;
					for (k = 0x10; k < 0x30; k++)
					{
						unsigned int e = pui32[k];
						pr_info("pvr-mtk: PTE[%03x] va=%08x raw=%08x v=%u pa=0x%llx cache=%u\n",
						        k, 0xC0000000u + (k << 12), e, (e >> 1) & 1u,
						        (unsigned long long)(((unsigned long long)(e & 0x03FFFFC0u)) << 6),
						        (e >> 3) & 7u);
					}
				{
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
					memunmap(pvPt);
				}
			}
			else
			{
				pr_info("pvr-mtk: MMU_AcquireBaseAddr failed\n");
			}
		}
		pr_info("pvr-mtk: RT cfg=%08x pm=%u clk=%u dusts=%u syscfg=%08x syscfgx=%08x\n",
		        psDevInfo->psRGXFWIfRuntimeCfg->ui32RuntimeCfgFlags,
		        psDevInfo->psRGXFWIfRuntimeCfg->ui32ActivePMLatencyms,
		        psDevInfo->psRGXFWIfRuntimeCfg->ui32CoreClockSpeed,
		        psDevInfo->psRGXFWIfRuntimeCfg->ui32DefaultDustsNumInit,
		        psDevInfo->psRGXFWIfFwSysData ? psDevInfo->psRGXFWIfFwSysData->ui32ConfigFlags : 0U,
		        psDevInfo->psRGXFWIfFwSysData ? psDevInfo->psRGXFWIfFwSysData->ui32ConfigFlagsExt : 0U);
		pr_info("pvr-mtk: OSINIT osdata=%08x rtn=%08x fwccbctl=%08x fwccb=%08x\n",
		        psDevInfo->psRGXFWIfOsInit->sFwOsData.ui32Addr,
		        psDevInfo->psRGXFWIfOsInit->psKernelCCBRtnSlots.ui32Addr,
		        psDevInfo->psRGXFWIfOsInit->psFirmwareCCBCtl.ui32Addr,
		        psDevInfo->psRGXFWIfOsInit->psFirmwareCCB.ui32Addr);
		pr_info("pvr-mtk: OSINIT kccbctl=%08x kccb=%08x cmdsize=%u wrapmask=%u\n",
		        psDevInfo->psRGXFWIfOsInit->psKernelCCBCtl.ui32Addr,
		        psDevInfo->psRGXFWIfOsInit->psKernelCCB.ui32Addr,
		        psDevInfo->psKernelCCBCtl->ui32CmdSize,
		        psDevInfo->psKernelCCBCtl->ui32WrapMask);
		pr_info("pvr-mtk: prim fwaddr=%08x cpuva=%px\n",
		        psDevInfo->psRGXFWIfFwOsData->sPowerSync.ui32Addr,
		        psDevInfo->psPowSyncPrim->pui32LinAddr);
		return PVRSRV_OK;
	}

#if !defined(NO_HARDWARE)
	psFwSysData = psDevInfo->psRGXFWIfFwSysData;
	pr_info("pvr-mtk: forced-idle enter: pow=%u kccb w=%u r=%u\n",
	        (unsigned)psFwSysData->ePowState,
	        psDevInfo->psKernelCCBCtl->ui32WriteOffset,
	        psDevInfo->psKernelCCBCtl->ui32ReadOffset);

	/* Firmware already forced idle */
	if (!pvr_pow_off && psFwSysData->ePowState == RGXFWIF_POW_FORCED_IDLE)
	{
		return PVRSRV_OK;
	}

	/* Firmware is not powered. Sometimes this is permitted, for instance we were forcing idle to power down. */
	if (psFwSysData->ePowState == RGXFWIF_POW_OFF)
	{
		return (bDeviceOffPermitted) ? PVRSRV_OK : PVRSRV_ERROR_DEVICE_IDLE_REQUEST_DENIED;
	}
#endif

	pvr_pow_snap(psDevInfo, "before", &sPowCmd, 0);
	if (pvr_fwstate)
		pvr_dump_fwstate(psDevInfo);
	if (pvr_prim_in_ccb)
	{
		IMG_UINT32 ui32Fw = psDevInfo->psRGXFWIfOsInit->psKernelCCBCtl.ui32Addr + 0x100;
		psDevInfo->psRGXFWIfFwOsData->sPowerSync.ui32Addr = ui32Fw;
		psDevInfo->psPowSyncPrim->pui32LinAddr =
			(volatile IMG_UINT32 __iomem *)((IMG_UINT8 *)psDevInfo->psKernelCCBCtl + 0x100);
		pr_info("pvr-mtk: prim->ccb page fw=%08x va=%px\n",
		        ui32Fw, psDevInfo->psPowSyncPrim->pui32LinAddr);
	}

	eError = SyncPrimSet(psDevInfo->psPowSyncPrim, 0);
	if (eError != PVRSRV_OK)
	{
		PVR_DPF((PVR_DBG_ERROR, "%s: Failed to set Power sync prim",
				__func__));
		return eError;
	}
	sPowCmd.eCmdType = RGXFWIF_KCCB_CMD_POW;
	sPowCmd.uCmdData.sPowData.ePowType = RGXFWIF_POW_FORCED_IDLE_REQ;
	sPowCmd.uCmdData.sPowData.uPowerReqData.ePowRequestType = RGXFWIF_POWER_FORCE_IDLE;
	if (pvr_pow_off)
	{
		sPowCmd.uCmdData.sPowData.ePowType = RGXFWIF_POW_OFF_REQ;
		sPowCmd.uCmdData.sPowData.uPowerReqData.bForced = IMG_TRUE;
		pr_info("pvr-mtk: POW_OFF_REQ instead of FORCED_IDLE (A/B)\n");
	}
	if (pvr_fwtrace)
	{
		IMG_UINT32 *pui32Raw = (IMG_UINT32 *)&sPowCmd;
		pr_info("pvr-mtk: POW raw %08x %08x %08x %08x (w=%u)\n",
		        pui32Raw[0], pui32Raw[1], pui32Raw[2], pui32Raw[3],
		        psDevInfo->psKernelCCBCtl->ui32WriteOffset);
	}

	PDUMPCOMMENT("RGXForcedIdleRequest: Sending forced idle command");

	/* Send one forced IDLE command to GP */
	eError = RGXSendCommandAndGetKCCBSlot(psDevInfo,
	                                      &sPowCmd,
	                                      PDUMP_FLAGS_NONE,
	                                      &ui32CmdKCCBSlot);

	if (eError != PVRSRV_OK)
	{
		PVR_DPF((PVR_DBG_ERROR, "%s: Failed to send idle request", __func__));
		return eError;
	}

	pvr_pow_snap(psDevInfo, "sent", &sPowCmd, ui32CmdKCCBSlot);

	if (pvr_kick)
	{
		IMG_UINT32 i;

		for (i = 0; i < 40; i++)
		{
			IMG_UINT32 ui32Rb;

			OSWriteMemoryBarrier();
			OSWriteHWReg32(psDevInfo->pvRegsBaseKM, RGX_CR_MTS_SCHEDULE,
			               (RGXFWIF_DM_GP & ~RGX_CR_MTS_SCHEDULE_DM_CLRMSK) |
			               RGX_CR_MTS_SCHEDULE_TASK_NON_COUNTED);
			OSMemoryBarrier();
			ui32Rb = OSReadHWReg32(psDevInfo->pvRegsBaseKM, RGX_CR_MTS_SCHEDULE);

			if ((i % 5) == 0)
			{
				pr_info("pvr-mtk: KICK %u rb=%08x kccb=%u/%u kcmds=%u pow=%u\n",
				        i, ui32Rb,
				        psDevInfo->psKernelCCBCtl->ui32WriteOffset,
				        psDevInfo->psKernelCCBCtl->ui32ReadOffset,
				        psDevInfo->psRGXFWIfFwOsData->ui32KCCBCmdsExecuted,
				        (unsigned)psDevInfo->psRGXFWIfFwSysData->ePowState);
			}
			msleep(50);
		}
	}

	/* Wait for GPU to finish current workload */
	do {
		eError = RGXPollForGPCommandCompletion(psDeviceNode,
		                              psDevInfo->psPowSyncPrim->pui32LinAddr,
									  0x1, 0xFFFFFFFF);
		pvr_pow_snap(psDevInfo, "poll", &sPowCmd, ui32CmdKCCBSlot);
		if (eError != PVRSRV_OK && pvr_state_wait)
		{
			unsigned int st = (unsigned int)psFwSysData->ePowState;
			if (st == RGXFWIF_POW_IDLE || st == RGXFWIF_POW_FORCED_IDLE)
			{
				pr_info("pvr-mtk: state-wait: forced idle reached pow=%u (early)\n", st);
				eError = PVRSRV_OK;
			}
		}
		if ((eError == PVRSRV_OK) || (ui32RetryCount == RGX_FORCED_IDLE_RETRY_COUNT))
		{
			break;
		}
		ui32RetryCount++;
		PVR_DPF((PVR_DBG_WARNING,
				"%s: Request timeout. Retry %d of %d",
				 __func__, ui32RetryCount, RGX_FORCED_IDLE_RETRY_COUNT));
	} while (IMG_TRUE);

	if (pvr_fwtrace)
	{
		pvr_dump_fw_trace(psDevInfo, "after-pow");
	}

	if (eError != PVRSRV_OK && pvr_state_wait && psFwSysData != NULL)
	{
		unsigned int st = (unsigned int)psFwSysData->ePowState;
		if (st == RGXFWIF_POW_IDLE || st == RGXFWIF_POW_FORCED_IDLE)
		{
			pr_info("pvr-mtk: state-wait: forced idle reached pow=%u\n", st);
			eError = PVRSRV_OK;
		}
	}

	if (eError != PVRSRV_OK)
	{
		pr_info("pvr-mtk: forced-idle timeout: kccb w=%u r=%u\n",
		        psDevInfo->psKernelCCBCtl->ui32WriteOffset,
		        psDevInfo->psKernelCCBCtl->ui32ReadOffset);
		pvr_pow_snap(psDevInfo, "timeout", &sPowCmd, ui32CmdKCCBSlot);
		RGXFWNotifyHostTimeout(psDevInfo);
		PVR_DPF((PVR_DBG_ERROR,
				 "%s: Idle request failed. Firmware potentially left in forced idle state",
				 __func__));
		return eError;
	}

#if defined(PDUMP)
	PDUMPCOMMENT("RGXForcedIdleRequest: Poll for Kernel SyncPrim [0x%p] on DM %d", psDevInfo->psPowSyncPrim->pui32LinAddr, RGXFWIF_DM_GP);

	SyncPrimPDumpPol(psDevInfo->psPowSyncPrim,
	                 1,
	                 0xffffffff,
	                 PDUMP_POLL_OPERATOR_EQUAL,
	                 0);
#endif

#if !defined(NO_HARDWARE)
	/* Check the firmware state for idleness */
	if (!g_pvrNoSync && !pvr_pow_off &&
	    !(pvr_state_wait && (psFwSysData->ePowState == RGXFWIF_POW_IDLE ||
	                          psFwSysData->ePowState == RGXFWIF_POW_FORCED_IDLE)) &&
	    psFwSysData->ePowState != RGXFWIF_POW_FORCED_IDLE)
	{
		return PVRSRV_ERROR_DEVICE_IDLE_REQUEST_DENIED;
	}
#endif

	return PVRSRV_OK;
}

/*
	RGXCancelForcedIdleRequest
*/
PVRSRV_ERROR RGXCancelForcedIdleRequest(IMG_HANDLE hDevHandle)
{
	PVRSRV_DEVICE_NODE	*psDeviceNode = hDevHandle;
	PVRSRV_RGXDEV_INFO	*psDevInfo = psDeviceNode->pvDevice;
	RGXFWIF_KCCB_CMD	sPowCmd;
	PVRSRV_ERROR		eError = PVRSRV_OK;
	IMG_UINT32			ui32CmdKCCBSlot;
	PVRSRV_VZ_RET_IF_MODE(GUEST, PVRSRV_OK);

	eError = SyncPrimSet(psDevInfo->psPowSyncPrim, 0);
	if (eError != PVRSRV_OK)
	{
		PVR_DPF((PVR_DBG_ERROR, "%s: Failed to set Power sync prim",
				__func__));
		goto ErrorExit;
	}

	/* Send the IDLE request to the FW */
	sPowCmd.eCmdType = RGXFWIF_KCCB_CMD_POW;
	sPowCmd.uCmdData.sPowData.ePowType = RGXFWIF_POW_FORCED_IDLE_REQ;
	sPowCmd.uCmdData.sPowData.uPowerReqData.ePowRequestType = RGXFWIF_POWER_CANCEL_FORCED_IDLE;

	PDUMPCOMMENT("RGXForcedIdleRequest: Sending cancel forced idle command");

	/* Send cancel forced IDLE command to GP */
	eError = RGXSendCommandAndGetKCCBSlot(psDevInfo,
	                                      &sPowCmd,
	                                      PDUMP_FLAGS_NONE,
	                                      &ui32CmdKCCBSlot);

	if (eError != PVRSRV_OK)
	{
		PDUMPCOMMENT("RGXCancelForcedIdleRequest: Failed to send cancel IDLE request for DM%d", RGXFWIF_DM_GP);
		goto ErrorExit;
	}

	/* Wait for the firmware to answer. */
	eError = RGXPollForGPCommandCompletion(psDeviceNode,
	                              psDevInfo->psPowSyncPrim->pui32LinAddr,
								  1, 0xFFFFFFFF);

	if (eError != PVRSRV_OK)
	{
		PVR_DPF((PVR_DBG_ERROR, "%s: Timeout waiting for cancel idle request", __func__));
		goto ErrorExit;
	}

#if defined(PDUMP)
	PDUMPCOMMENT("RGXCancelForcedIdleRequest: Poll for Kernel SyncPrim [0x%p] on DM %d", psDevInfo->psPowSyncPrim->pui32LinAddr, RGXFWIF_DM_GP);

	SyncPrimPDumpPol(psDevInfo->psPowSyncPrim,
	                 1,
	                 0xffffffff,
	                 PDUMP_POLL_OPERATOR_EQUAL,
	                 0);
#endif

	return eError;

ErrorExit:
	PVR_DPF((PVR_DBG_ERROR, "%s: Firmware potentially left in forced idle state", __func__));
	return eError;
}

/*!
 ******************************************************************************

 @Function	PVRSRVGetNextDustCount

 @Description

	Calculate a sequence of dust counts to achieve full transition coverage.
	We increment two counts of dusts and switch up and down between them.
	It does	contain a few redundant transitions. If two dust exist, the
	output transitions should be as follows.

	0->1, 0<-1, 0->2, 0<-2, (0->1)
	1->1, 1->2, 1<-2, (1->2)
	2->2, (2->0),
	0->0. Repeat.

	Redundant transitions in brackets.

 @Input		psDustReqState : Counter state used to calculate next dust count
 @Input		ui32DustCount : Number of dusts in the core

 @Return	PVRSRV_ERROR

 ******************************************************************************/
IMG_UINT32 RGXGetNextDustCount(RGX_DUST_STATE *psDustReqState, IMG_UINT32 ui32DustCount)
{
	if (psDustReqState->bToggle)
	{
		psDustReqState->ui32DustCount2++;
	}

	if (psDustReqState->ui32DustCount2 > ui32DustCount)
	{
		psDustReqState->ui32DustCount1++;
		psDustReqState->ui32DustCount2 = psDustReqState->ui32DustCount1;
	}

	if (psDustReqState->ui32DustCount1 > ui32DustCount)
	{
		psDustReqState->ui32DustCount1 = 0;
		psDustReqState->ui32DustCount2 = 0;
	}

	psDustReqState->bToggle = !psDustReqState->bToggle;

	return (psDustReqState->bToggle) ? psDustReqState->ui32DustCount1 : psDustReqState->ui32DustCount2;
}

/******************************************************************************
 End of file (rgxpower.c)
******************************************************************************/
