/* LD_PRELOAD shim: record device mappings made by the vendor PowerVR UM.
 * pvr_dump_maps() (called by gles_clear) dumps the containing /proc/self/maps
 * region for each recorded CPU pointer.
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/types.h>

#define MAX_MAPS 512
#define MAX_DUMP (4 * 1024 * 1024)

struct rec {
    void *cpu;
    uint64_t dev;
};

static struct rec g_maps[MAX_MAPS];
static int g_n;

static void add_map(void *cpu, uint64_t dev)
{
    if (!cpu || cpu == MAP_FAILED || g_n >= MAX_MAPS)
        return;
    g_maps[g_n].cpu = cpu;
    g_maps[g_n].dev = dev;
    g_n++;
}

static int region_for(void *p, uint64_t *start, uint64_t *end)
{
    FILE *f = fopen("/proc/self/maps", "r");
    char line[512];
    int found = 0;

    if (!f)
        return 0;

    while (fgets(line, sizeof(line), f)) {
        unsigned long s, e;
        char perms[16];
        if (sscanf(line, "%lx-%lx %15s", &s, &e, perms) == 3) {
            if ((uint64_t)(uintptr_t)p >= s && (uint64_t)(uintptr_t)p < e) {
                *start = s;
                *end = e;
                found = 1;
                break;
            }
        }
    }
    fclose(f);
    return found;
}

void pvr_dump_maps(void)
{
    FILE *log = fopen("/tmp/pvr-maps.txt", "w");

    if (log)
        fprintf(log, "maps=%d\n", g_n);

    for (int i = 0; i < g_n; i++) {
        uint64_t s = 0, e = 0;
        size_t len;

        if (!region_for(g_maps[i].cpu, &s, &e)) {
            if (log)
                fprintf(log, "%03d cpu=%p dev=%llx region=none\n",
                        i, g_maps[i].cpu,
                        (unsigned long long)g_maps[i].dev);
            continue;
        }

        len = e - s;
        if (len > 8 * 1024 * 1024) {
            if (log)
                fprintf(log,
                        "%03d cpu=%p dev=%llx region=%llx-%llx (skip huge)\n",
                        i, g_maps[i].cpu, (unsigned long long)g_maps[i].dev,
                        (unsigned long long)s, (unsigned long long)e);
            continue;
        }
        if (len > MAX_DUMP)
            len = MAX_DUMP;

        char path[128];
        snprintf(path, sizeof(path), "/tmp/pvr-map-%03d.bin", i);
        FILE *f = fopen(path, "wb");
        if (f) {
            fwrite((void *)(uintptr_t)s, 1, len, f);
            fclose(f);
        }
        if (log)
            fprintf(log, "%03d cpu=%p dev=%llx region=%llx-%llx\n",
                    i, g_maps[i].cpu, (unsigned long long)g_maps[i].dev,
                    (unsigned long long)s, (unsigned long long)e);
    }

    if (log)
        fclose(log);
}

int PVRSRVMapToDeviceAddress(void *a, void *b, void *c)
{
    static int (*real)(void *, void *, void *);
    if (!real)
        real = dlsym(RTLD_NEXT, "PVRSRVMapToDeviceAddress");
    int r = real(a, b, c);
    if (r == 0 && c)
        add_map(*(void **)c, b ? *(uint64_t *)b : 0);
    return r;
}

int PVRSRVMapToDevice(void *a, void *b, void *c)
{
    static int (*real)(void *, void *, void *);
    if (!real)
        real = dlsym(RTLD_NEXT, "PVRSRVMapToDevice");
    int r = real(a, b, c);
    if (r == 0 && c)
        add_map(*(void **)c, 0);
    return r;
}

void *mmap(void *addr, size_t len, int prot, int flags, int fd, off_t off)
{
    static void *(*real)(void *, size_t, int, int, int, off_t);
    if (!real)
        real = dlsym(RTLD_NEXT, "mmap");
    void *p = real(addr, len, prot, flags, fd, off);
    if (p != MAP_FAILED && (prot & PROT_WRITE) && len >= 128)
        add_map(p, 0);
    return p;
}

void *mmap64(void *addr, size_t len, int prot, int flags, int fd, off_t off)
{
    static void *(*real)(void *, size_t, int, int, int, off_t);
    if (!real)
        real = dlsym(RTLD_NEXT, "mmap64");
    void *p = real(addr, len, prot, flags, fd, off);
    if (p != MAP_FAILED && (prot & PROT_WRITE) && len >= 128)
        add_map(p, 0);
    return p;
}
