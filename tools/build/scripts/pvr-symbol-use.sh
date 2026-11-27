cd "$HOME/AI Project/Redmi 9A/kernel 7.1 mainline/drivers/misc/pvr/ddk" || exit 1
for s in MTKMFGSystemInit MTKMFGSystemDeInit MTKSystemPrePowerState MTKSystemPostPowerState \
         mtk_fdvfs_update_cur_freq MTKFWDump mtk_mfg_async_init mtk_mfg_2d_init \
         spm_mtcmos_ctrl_mfg0 ged_dvfs_gpu_freq_commit_fp ged_log_trace_counter \
         mt_gpufreq_get_cur_freq_index mtk_get_gpu_loading_fp; do
	echo "== $s"
	grep -rln "$s" --include='*.c' . 2>/dev/null | grep -v mtk_mfgsys | head -3
done
