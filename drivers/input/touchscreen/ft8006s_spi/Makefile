# Makefile for the focaltech touchscreen drivers.

ccflags-y += -I$(srctree)/drivers/input/touchscreen/
ccflags-y += -I$(srctree)/drivers/input/touchscreen/mediatek/
ccflags-y += -I$(srctree)/drivers/input/touchscreen/mediatek/ft8006s_spi/
ccflags-y += -I$(srctree)/drivers/spi/mediatek/$(MTK_PLATFORM)
ccflags-y += -I$(srctree)/drivers/misc/mediatek/include/mt-plat/
ccflags-y += -I$(srctree)/drivers/misc/mediatek/include/mt-plat/$(MTK_PLATFORM)/include/
ccflags-y += -I$(srctree)/drivers/base
ccflags-y += -I$(srctree)/drivers/misc/mediatek/hwmon/include
ccflags-y += -I$(srctree)/drivers/misc/mediatek/alsps/inc/

#obj-$(CONFIG_TOUCHSCREEN_FTS)   +=  focaltech_flash/





# single combined module (multiple .o must be linked together)
focaltech_ts-y := focaltech_core.o focaltech_spi.o focaltech_ex_fun.o \
                  focaltech_ex_mode.o focaltech_gesture.o focaltech_esdcheck.o \
                  focaltech_point_report_check.o focaltech_flash.o fts_stub.o
obj-$(CONFIG_TOUCHSCREEN_FTS) += focaltech_ts.o
