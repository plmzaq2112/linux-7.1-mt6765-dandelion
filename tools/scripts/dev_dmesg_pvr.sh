#!/bin/sh
dmesg > /tmp/pvr-dmesg.log
grep -n "PVRSRVDevicePrimaryInit\|pvr-dump\|WARNING\|HWR\|CCB\|RGX\|Firmware" /tmp/pvr-dmesg.log | tail -60
