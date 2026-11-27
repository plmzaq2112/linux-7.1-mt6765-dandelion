#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdarg.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <fcntl.h>
#include <dlfcn.h>
#include <poll.h>
#include <pthread.h>
#include <signal.h>
#include <ucontext.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <linux/sync_file.h>
#include <drm/drm.h>
#include <drm/drm_mode.h>

/* Ensure at least 128 bytes of static TLS so [tpidr_el0, #40] is always valid */
__thread uint64_t __bionic_tls_pad[16] __attribute__((used)) = {
    0x1122334455667788ULL, 0x1122334455667788ULL,
    0x1122334455667788ULL, 0x1122334455667788ULL,
    0x1122334455667788ULL, 0x1122334455667788ULL,
    0x1122334455667788ULL, 0x1122334455667788ULL
};

static int g_debug_log = -1;
static inline int shim_log_enabled(void) {
    if (g_debug_log < 0) {
        const char *env = getenv("PVR_SHIM_LOG");
        g_debug_log = (env && atoi(env) > 0) ? 1 : 0;
    }
    return g_debug_log;
}

static void crash_handler(int sig, siginfo_t *si, void *uctx) {
    ucontext_t *uc = (ucontext_t *)uctx;
    void *pc = (void *)uc->uc_mcontext.pc;
    void *lr = (void *)uc->uc_mcontext.regs[30];
    Dl_info dli_pc = {0}, dli_lr = {0};
    dladdr(pc, &dli_pc);
    dladdr(lr, &dli_lr);
    fprintf(stderr, "\n[CRASH] sig=%d (%s) si_code=%d fault_addr=%p\n",
            sig, strsignal(sig), si->si_code, si->si_addr);
    fprintf(stderr, "  PC = %p (%s + 0x%lx [%s])\n",
            pc, dli_pc.dli_fname ? dli_pc.dli_fname : "?",
            dli_pc.dli_fbase ? (unsigned long)((uintptr_t)pc - (uintptr_t)dli_pc.dli_fbase) : 0UL,
            dli_pc.dli_sname ? dli_pc.dli_sname : "?");
    fprintf(stderr, "  LR = %p (%s + 0x%lx [%s])\n",
            lr, dli_lr.dli_fname ? dli_lr.dli_fname : "?",
            dli_lr.dli_fbase ? (unsigned long)((uintptr_t)lr - (uintptr_t)dli_lr.dli_fbase) : 0UL,
            dli_lr.dli_sname ? dli_lr.dli_sname : "?");
    fflush(stderr);
    _exit(128 + sig);
}

__attribute__((constructor))
static void init_shim_signals(void) {
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_sigaction = crash_handler;
    sa.sa_flags = SA_SIGINFO;
    sigaction(SIGBUS, &sa, NULL);
    sigaction(SIGSEGV, &sa, NULL);
}

/* Safe memset / memcpy without DC ZVA (safe on MT_NORMAL_NC / Write-Combine memory) */
__attribute__((optimize("no-tree-loop-distribute-patterns")))
void *bmemst(void *s, int c, size_t n) {
    volatile uint8_t *p = (volatile uint8_t *)s;
    uint8_t v = (uint8_t)c;
    uint64_t v64 = (uint64_t)v * 0x0101010101010101ULL;
    while (n > 0 && ((uintptr_t)p & 7)) {
        *p++ = v;
        n--;
    }
    volatile uint64_t *p64 = (volatile uint64_t *)p;
    while (n >= 32) {
        p64[0] = v64;
        p64[1] = v64;
        p64[2] = v64;
        p64[3] = v64;
        p64 += 4;
        n -= 32;
    }
    while (n >= 8) {
        *p64++ = v64;
        n -= 8;
    }
    p = (volatile uint8_t *)p64;
    while (n > 0) {
        *p++ = v;
        n--;
    }
    return s;
}

void *b_memset_chk(void *s, int c, size_t n, size_t dest_len) {
    (void)dest_len;
    return bmemst(s, c, n);
}

__attribute__((optimize("no-tree-loop-distribute-patterns")))
void *bmemcp(void *dest, const void *src, size_t n) {
    uint8_t *d = (uint8_t *)dest;
    const uint8_t *s = (const uint8_t *)src;
    if ((((uintptr_t)d | (uintptr_t)s) & 7) == 0) {
        uint64_t *d64 = (uint64_t *)d;
        const uint64_t *s64 = (const uint64_t *)s;
        while (n >= 32) {
            d64[0] = s64[0];
            d64[1] = s64[1];
            d64[2] = s64[2];
            d64[3] = s64[3];
            d64 += 4;
            s64 += 4;
            n -= 32;
        }
        while (n >= 8) {
            *d64++ = *s64++;
            n -= 8;
        }
        d = (uint8_t *)d64;
        s = (const uint8_t *)s64;
    }
    while (n > 0) {
        *d++ = *s++;
        n--;
    }
    return dest;
}

void *b_memcpy_chk(void *dest, const void *src, size_t n, size_t dest_len) {
    (void)dest_len;
    return bmemcp(dest, src, n);
}

/* =========================================================================
 * 1. Bionic setjmp / longjmp (176 bytes, fits inside 256-byte Bionic jmp_buf)
 * ========================================================================= */
__asm__(
".global bsetjm\n"
".type bsetjm, %function\n"
"bsetjm:\n"
"    stp x19, x20, [x0, #0]\n"
"    stp x21, x22, [x0, #16]\n"
"    stp x23, x24, [x0, #32]\n"
"    stp x25, x26, [x0, #48]\n"
"    stp x27, x28, [x0, #64]\n"
"    stp x29, x30, [x0, #80]\n"
"    mov x2, sp\n"
"    str x2,       [x0, #96]\n"
"    stp d8,  d9,  [x0, #112]\n"
"    stp d10, d11, [x0, #128]\n"
"    stp d12, d13, [x0, #144]\n"
"    stp d14, d15, [x0, #160]\n"
"    mov w0, #0\n"
"    ret\n"
"\n"
".global blongjm\n"
".type blongjm, %function\n"
"blongjm:\n"
"    ldp x19, x20, [x0, #0]\n"
"    ldp x21, x22, [x0, #16]\n"
"    ldp x23, x24, [x0, #32]\n"
"    ldp x25, x26, [x0, #48]\n"
"    ldp x27, x28, [x0, #64]\n"
"    ldp x29, x30, [x0, #80]\n"
"    ldr x2,       [x0, #96]\n"
"    mov sp, x2\n"
"    ldp d8,  d9,  [x0, #112]\n"
"    ldp d10, d11, [x0, #128]\n"
"    ldp d12, d13, [x0, #144]\n"
"    ldp d14, d15, [x0, #160]\n"
"    cmp w1, #0\n"
"    csinc w0, w1, wzr, ne\n"
"    ret\n"
);

/* =========================================================================
 * 2. Bionic pthread_mutex_t (40B, 4B-aligned) & pthread_cond_t (48B, 4B-aligned)
 * ========================================================================= */
#define BIONIC_MUTEX_MAGIC32 0x4D545831U
#define BIONIC_COND_MAGIC32  0x434E4431U

typedef struct {
    uint32_t state;
    uint32_t magic;
    uint32_t ptr_lo;
    uint32_t ptr_hi;
} bionic_mutex_slot_t;

typedef struct {
    uint32_t state;
    uint32_t magic;
    uint32_t ptr_lo;
    uint32_t ptr_hi;
} bionic_cond_slot_t;

static inline void slot_set_ptr(uint32_t *lo, uint32_t *hi, void *p) {
    uintptr_t v = (uintptr_t)p;
    *lo = (uint32_t)(v & 0xFFFFFFFFUL);
    *hi = (uint32_t)(v >> 32);
}

static inline void *slot_get_ptr(uint32_t lo, uint32_t hi) {
    return (void *)(((uintptr_t)hi << 32) | (uintptr_t)lo);
}

static pthread_mutex_t g_init_lock = PTHREAD_MUTEX_INITIALIZER;

static pthread_mutex_t *get_or_init_mutex(void *bmutex) {
    bionic_mutex_slot_t *slot = (bionic_mutex_slot_t *)bmutex;
    if (__atomic_load_n(&slot->magic, __ATOMIC_ACQUIRE) == BIONIC_MUTEX_MAGIC32) {
        return (pthread_mutex_t *)slot_get_ptr(slot->ptr_lo, slot->ptr_hi);
    }
    pthread_mutex_lock(&g_init_lock);
    if (slot->magic != BIONIC_MUTEX_MAGIC32) {
        uint16_t state = (uint16_t)(slot->state & 0xFFFFU);
        int mtype = (state >> 14) & 3;
        pthread_mutex_t *m = (pthread_mutex_t *)calloc(1, sizeof(pthread_mutex_t));
        pthread_mutexattr_t attr;
        pthread_mutexattr_init(&attr);
        if (mtype == 1)
            pthread_mutexattr_settype(&attr, PTHREAD_MUTEX_RECURSIVE);
        else if (mtype == 2)
            pthread_mutexattr_settype(&attr, PTHREAD_MUTEX_ERRORCHECK);
        pthread_mutex_init(m, &attr);
        pthread_mutexattr_destroy(&attr);
        slot_set_ptr(&slot->ptr_lo, &slot->ptr_hi, m);
        __atomic_store_n(&slot->magic, BIONIC_MUTEX_MAGIC32, __ATOMIC_RELEASE);
    }
    pthread_mutex_unlock(&g_init_lock);
    return (pthread_mutex_t *)slot_get_ptr(slot->ptr_lo, slot->ptr_hi);
}

int b_mutexattr_init(long *attr) {
    if (!attr) return EINVAL;
    *attr = 0;
    return 0;
}

int b_mutexattr_settype(long *attr, int type) {
    if (!attr) return EINVAL;
    *attr = (type & 3);
    return 0;
}

int b_mutexattr_destroy(long *attr) {
    (void)attr;
    return 0;
}

int b_mutex_init(void *bmutex, const long *battr) {
    if (!bmutex) return EINVAL;
    bionic_mutex_slot_t *slot = (bionic_mutex_slot_t *)bmutex;
    pthread_mutex_t *m = (pthread_mutex_t *)calloc(1, sizeof(pthread_mutex_t));
    if (!m) return ENOMEM;
    pthread_mutexattr_t attr;
    pthread_mutexattr_init(&attr);
    if (battr) {
        int mtype = (*battr) & 3;
        if (mtype == 1)
            pthread_mutexattr_settype(&attr, PTHREAD_MUTEX_RECURSIVE);
        else if (mtype == 2)
            pthread_mutexattr_settype(&attr, PTHREAD_MUTEX_ERRORCHECK);
    }
    int rc = pthread_mutex_init(m, &attr);
    pthread_mutexattr_destroy(&attr);
    slot_set_ptr(&slot->ptr_lo, &slot->ptr_hi, m);
    __atomic_store_n(&slot->magic, BIONIC_MUTEX_MAGIC32, __ATOMIC_RELEASE);
    return rc;
}

int b_mutex_lock(void *bmutex) {
    if (!bmutex) return EINVAL;
    return pthread_mutex_lock(get_or_init_mutex(bmutex));
}

int b_mutex_trylock(void *bmutex) {
    if (!bmutex) return EINVAL;
    return pthread_mutex_trylock(get_or_init_mutex(bmutex));
}

int b_mutex_unlock(void *bmutex) {
    if (!bmutex) return EINVAL;
    return pthread_mutex_unlock(get_or_init_mutex(bmutex));
}

int b_mutex_destroy(void *bmutex) {
    if (!bmutex) return EINVAL;
    bionic_mutex_slot_t *slot = (bionic_mutex_slot_t *)bmutex;
    if (__atomic_load_n(&slot->magic, __ATOMIC_ACQUIRE) == BIONIC_MUTEX_MAGIC32) {
        pthread_mutex_t *m = (pthread_mutex_t *)slot_get_ptr(slot->ptr_lo, slot->ptr_hi);
        int rc = 0;
        if (m) {
            rc = pthread_mutex_destroy(m);
            free(m);
        }
        slot->ptr_lo = 0;
        slot->ptr_hi = 0;
        __atomic_store_n(&slot->magic, 0, __ATOMIC_RELEASE);
        return rc;
    }
    return 0;
}

static pthread_cond_t *get_or_init_cond(void *bcond) {
    bionic_cond_slot_t *slot = (bionic_cond_slot_t *)bcond;
    if (__atomic_load_n(&slot->magic, __ATOMIC_ACQUIRE) == BIONIC_COND_MAGIC32) {
        return (pthread_cond_t *)slot_get_ptr(slot->ptr_lo, slot->ptr_hi);
    }
    pthread_mutex_lock(&g_init_lock);
    if (slot->magic != BIONIC_COND_MAGIC32) {
        pthread_cond_t *c = (pthread_cond_t *)calloc(1, sizeof(pthread_cond_t));
        pthread_cond_init(c, NULL);
        slot_set_ptr(&slot->ptr_lo, &slot->ptr_hi, c);
        __atomic_store_n(&slot->magic, BIONIC_COND_MAGIC32, __ATOMIC_RELEASE);
    }
    pthread_mutex_unlock(&g_init_lock);
    return (pthread_cond_t *)slot_get_ptr(slot->ptr_lo, slot->ptr_hi);
}

int b_cond_init(void *bcond, const void *cattr) {
    (void)cattr;
    if (!bcond) return EINVAL;
    bionic_cond_slot_t *slot = (bionic_cond_slot_t *)bcond;
    pthread_cond_t *c = (pthread_cond_t *)calloc(1, sizeof(pthread_cond_t));
    if (!c) return ENOMEM;
    int rc = pthread_cond_init(c, NULL);
    slot_set_ptr(&slot->ptr_lo, &slot->ptr_hi, c);
    __atomic_store_n(&slot->magic, BIONIC_COND_MAGIC32, __ATOMIC_RELEASE);
    return rc;
}

int b_cond_wait(void *bcond, void *bmutex) {
    if (!bcond || !bmutex) return EINVAL;
    return pthread_cond_wait(get_or_init_cond(bcond), get_or_init_mutex(bmutex));
}

int b_cond_timedwait(void *bcond, void *bmutex, const struct timespec *abstime) {
    if (!bcond || !bmutex) return EINVAL;
    return pthread_cond_timedwait(get_or_init_cond(bcond), get_or_init_mutex(bmutex), abstime);
}

int b_cond_signal(void *bcond) {
    if (!bcond) return EINVAL;
    return pthread_cond_signal(get_or_init_cond(bcond));
}

int b_cond_broadcast(void *bcond) {
    if (!bcond) return EINVAL;
    return pthread_cond_broadcast(get_or_init_cond(bcond));
}

int b_cond_destroy(void *bcond) {
    if (!bcond) return EINVAL;
    bionic_cond_slot_t *slot = (bionic_cond_slot_t *)bcond;
    if (__atomic_load_n(&slot->magic, __ATOMIC_ACQUIRE) == BIONIC_COND_MAGIC32) {
        pthread_cond_t *c = (pthread_cond_t *)slot_get_ptr(slot->ptr_lo, slot->ptr_hi);
        int rc = 0;
        if (c) {
            rc = pthread_cond_destroy(c);
            free(c);
        }
        slot->ptr_lo = 0;
        slot->ptr_hi = 0;
        __atomic_store_n(&slot->magic, 0, __ATOMIC_RELEASE);
        return rc;
    }
    return 0;
}

/* =========================================================================
 * 3. Bionic / FORTIFY / Android system functions
 * ========================================================================= */
int *__errno(void) {
    return __errno_location();
}

long bsyscon(int name) {
    if (name == 0x27 || name == 0x28) /* Bionic _SC_PAGESIZE / _SC_PAGE_SIZE */
        return 4096;
    if (name == 0x60) /* Bionic _SC_NPROCESSORS_CONF */
        return sysconf(_SC_NPROCESSORS_CONF);
    if (name == 0x61) /* Bionic _SC_NPROCESSORS_ONLN */
        return sysconf(_SC_NPROCESSORS_ONLN);
    return sysconf(name);
}

int __android_log_print(int prio, const char *tag, const char *fmt, ...) {
    if (shim_log_enabled() || prio >= 6) {
        va_list ap;
        va_start(ap, fmt);
        fprintf(stderr, "[PVR-%d/%s] ", prio, tag ? tag : "");
        vfprintf(stderr, fmt, ap);
        fprintf(stderr, "\n");
        va_end(ap);
    }
    return 0;
}

int __system_property_get(const char *name, char *value) {
    if (!value) return 0;
    value[0] = '\0';
    if (name && shim_log_enabled()) {
        fprintf(stderr, "[shim] __system_property_get(%s)\n", name);
    }
    return 0;
}

int property_get(const char *key, char *value, const char *default_value) {
    if (!value) return 0;
    if (default_value) {
        strncpy(value, default_value, 91);
        value[91] = '\0';
        return (int)strlen(value);
    }
    value[0] = '\0';
    return 0;
}

void *bdlopn(const char *filename, int flags) {
    char rewritten[512];
    const char *target = filename;
    if (filename && strncmp(filename, "/system/vendor/", 15) == 0) {
        snprintf(rewritten, sizeof(rewritten), "/vendor/%s", filename + 15);
        target = rewritten;
    }
    void *h = dlopen(target, flags);
    if (!h && target && strchr(target, '/')) {
        const char *base = strrchr(target, '/') + 1;
        snprintf(rewritten, sizeof(rewritten), "/vendor/lib64/%s", base);
        h = dlopen(rewritten, flags);
        if (!h) {
            snprintf(rewritten, sizeof(rewritten), "/vendor/lib64/egl/%s", base);
            h = dlopen(rewritten, flags);
        }
        if (!h) {
            snprintf(rewritten, sizeof(rewritten), "/vendor/lib64/hw/%s", base);
            h = dlopen(rewritten, flags);
        }
    }
    if (shim_log_enabled() || !h) {
        fprintf(stderr, "[shim] dlopen(%s -> %s, 0x%x) = %p %s\n",
                filename ? filename : "NULL",
                target ? target : "NULL",
                flags, h, h ? "" : dlerror());
    }
    return h;
}

void *android_load_sphal_library(const char *name, int flags) {
    return bdlopn(name, flags);
}

size_t __fwrite_chk(const void *buf, size_t size, size_t count, FILE *stream, size_t buf_size) {
    (void)buf_size;
    return fwrite(buf, size, count, stream);
}

char *__strchr_chk(const char *p, int ch, size_t s_len) {
    (void)s_len;
    return (char *)strchr(p, ch);
}

size_t __strlen_chk(const char *s, size_t s_len) {
    (void)s_len;
    return strlen(s);
}

char *__strncpy_chk2(char *dst, const char *src, size_t n, size_t dst_len, size_t src_len) {
    (void)dst_len;
    (void)src_len;
    return strncpy(dst, src, n);
}

char *__strrchr_chk(const char *p, int ch, size_t s_len) {
    (void)s_len;
    return (char *)strrchr(p, ch);
}

ssize_t __write_chk(int fd, const void *buf, size_t count, size_t buf_size) {
    (void)buf_size;
    return write(fd, buf, count);
}

/* zlib wrappers via runtime libz.so.1 */
static void *get_libz(void) {
    static void *h = NULL;
    if (!h) h = dlopen("libz.so.1", RTLD_LAZY | RTLD_LOCAL);
    return h;
}

unsigned long compressBound(unsigned long sourceLen) {
    static unsigned long (*fn)(unsigned long) = NULL;
    if (!fn && get_libz()) fn = dlsym(get_libz(), "compressBound");
    if (fn) return fn(sourceLen);
    return sourceLen + (sourceLen >> 12) + (sourceLen >> 14) + (sourceLen >> 25) + 13;
}

int compress2(uint8_t *dest, unsigned long *destLen, const uint8_t *source, unsigned long sourceLen, int level) {
    static int (*fn)(uint8_t *, unsigned long *, const uint8_t *, unsigned long, int) = NULL;
    if (!fn && get_libz()) fn = dlsym(get_libz(), "compress2");
    if (fn) return fn(dest, destLen, source, sourceLen, level);
    return -1;
}

int uncompress(uint8_t *dest, unsigned long *destLen, const uint8_t *source, unsigned long sourceLen) {
    static int (*fn)(uint8_t *, unsigned long *, const uint8_t *, unsigned long) = NULL;
    if (!fn && get_libz()) fn = dlsym(get_libz(), "uncompress");
    if (fn) return fn(dest, destLen, source, sourceLen);
    return -1;
}

/* android::CallStack stubs */
void _ZN7android9CallStackC1EPKci(void *this_ptr, const char *logtag, int ignoreDepth) {
    (void)this_ptr; (void)logtag; (void)ignoreDepth;
}
void _ZN7android9CallStackC1Ev(void *this_ptr) { (void)this_ptr; }
void _ZN7android9CallStack6updateEii(void *this_ptr, int ignoreDepth, int maxDepth) {
    (void)this_ptr; (void)ignoreDepth; (void)maxDepth;
}
void _ZNK7android9CallStack3logEPKc19android_LogPriorityS2_(const void *this_ptr, const char *logtag, int priority, const char *prefix) {
    (void)this_ptr; (void)logtag; (void)priority; (void)prefix;
}
void _ZN7android9CallStackD1Ev(void *this_ptr) { (void)this_ptr; }

/* =========================================================================
 * 4. Linux sync_file (libsync.so) implementation
 * ========================================================================= */
int sync_wait(int fd, int timeout) {
    struct pollfd fds;
    int ret;
    if (fd < 0) {
        errno = EINVAL;
        return -1;
    }
    fds.fd = fd;
    fds.events = POLLIN;
    do {
        ret = poll(&fds, 1, timeout);
        if (ret > 0) {
            if (fds.revents & (POLLERR | POLLNVAL)) {
                errno = EINVAL;
                return -1;
            }
            return 0;
        } else if (ret == 0) {
            errno = ETIME;
            return -1;
        }
    } while (ret == -1 && (errno == EINTR || errno == EAGAIN));
    return ret;
}

int sync_merge(const char *name, int fd1, int fd2) {
    struct sync_merge_data data;
    memset(&data, 0, sizeof(data));
    data.fd2 = fd2;
    if (name) {
        strncpy(data.name, name, sizeof(data.name) - 1);
    }
    if (ioctl(fd1, SYNC_IOC_MERGE, &data) < 0)
        return -1;
    return data.fence;
}

struct sync_file_info *sync_file_info(int32_t fd) {
    struct sync_file_info local_info;
    memset(&local_info, 0, sizeof(local_info));
    if (ioctl(fd, SYNC_IOC_FILE_INFO, &local_info) < 0)
        return NULL;
    uint32_t num_fences = local_info.num_fences;
    size_t total_size = sizeof(struct sync_file_info) + num_fences * sizeof(struct sync_fence_info);
    struct sync_file_info *info = (struct sync_file_info *)calloc(1, total_size);
    if (!info) return NULL;
    info->num_fences = num_fences;
    if (num_fences > 0) {
        info->sync_fence_info = (uintptr_t)(info + 1);
    }
    if (ioctl(fd, SYNC_IOC_FILE_INFO, info) < 0) {
        free(info);
        return NULL;
    }
    return info;
}

void sync_file_info_free(struct sync_file_info *info) {
    free(info);
}

/* =========================================================================
 * 5. MTK GED / GPUD / GpuAux / ION stubs & DRM dumb-buffer DMA-BUF allocator
 * ========================================================================= */
uint8_t g_gpud_context[4096] = {0};

void *ged_create(void) { return calloc(1, 16); }
void ged_destroy(void *h) { free(h); }
int ged_event_notify(void *h, int ev) { (void)h; (void)ev; return 0; }
int ged_gpu_hint_cpu(void *h, int hint) { (void)h; (void)hint; return 0; }
void *ged_swd_create(int a, const char *b) { (void)a; (void)b; return calloc(1, 24); }
void ged_swd_destroy(void *h) { free(h); }
int ged_swd_push_fence(void *h, int fd) { (void)h; (void)fd; return 0; }
int ged_ge_alloc(int a, void *b) { (void)a; (void)b; return 0; }
int ged_ge_get(int a, int b, int c, int d, void *e) { (void)a; (void)b; (void)c; (void)d; (void)e; return 0; }
int ged_ge_set(int a, int b, int c, int d, void *e) { (void)a; (void)b; (void)c; (void)d; (void)e; return 0; }
int ged_ge_query(int a, int b, void *c) { (void)a; (void)b; (void)c; return 0; }

int gpudInitialize(int a) { (void)a; return 0; }
int gpudIsEnabled(int a) { (void)a; return 0; }
int gpudIsGlBindFramebufferDumpEnabled(void) { return 0; }
int gpudAuxShowConversionStatus(void) { return 0; }
int gpudGrallocDumpAllocInfo(void) { return 0; }
int gpudGlDumpPresentFrame(void) { return 0; }
int gpudGlDumpBindFramebuffer(void) { return 0; }
int gpudGlDumpCompressedTexImage2D(void) { return 0; }
int gpudGlDumpCompressedTexImage3D(void) { return 0; }
int gpudGlDumpCompressedTexSubImage2D(void) { return 0; }
int gpudGlDumpCompressedTexSubImage3D(void) { return 0; }
int gpudGlDumpCopyTexImage2D(void) { return 0; }
int gpudGlDumpCopyTexSubImage2D(void) { return 0; }
int gpudGlDumpCopyTexSubImage3D(void) { return 0; }
int gpudGlDumpEGLImageTargetTexture2DOES(void) { return 0; }
int gpudGlDumpReadPixels(void) { return 0; }
int gpudGlDumpStateError(void) { return 0; }
int gpudGlDumpTexImage2D(void) { return 0; }
int gpudGlDumpTexImage3D(void) { return 0; }
int gpudGlDumpTexSubImage2D(void) { return 0; }
int gpudGlDumpTexSubImage3D(void) { return 0; }
int gpudGlHackClear(void) { return 0; }
int gpudGlHackClearColor(void) { return 0; }
int gpudGlHackClearDepthf(void) { return 0; }
int gpudGlHackClearStencil(void) { return 0; }
int gpudGlHackGetString(void) { return 0; }
int gpudGlHackOrDumpShaderSource(void) { return 0; }
int gpudGlHackPolygonOffset(void) { return 0; }
int gpudGlHackScissor(void) { return 0; }
int gpudGlHackUseProgram(void) { return 0; }
int gpudGlHackViewport(void) { return 0; }

int GpuAuxCheckAuxPath(void) { return 0; }
void *GpuAuxCreateContext(int a, int b) { (void)a; (void)b; return calloc(1, 48); }
void GpuAuxDestoryContext(void *ctx) { free(ctx); }
int GpuAuxDoConversionIfNeedV2(void *ctx, int a) { (void)ctx; (void)a; return 0; }
int GpuAuxGetAuxOutFormat(int a) { return a; }
void *GpuAuxGetCurrentAuxBuffer(void *ctx) { (void)ctx; return NULL; }
int GpuAuxGetCurrentIdx(void *ctx) { (void)ctx; return 0; }
int GpuAuxPrepareBuffer(void *ctx, void *buf) { (void)ctx; (void)buf; return 0; }

/* ION -> DRM Dumb Buffer DMA-BUF shim */
int ion_open(void) {
    int fd = open("/dev/dri/card1", O_RDWR | O_CLOEXEC);
    if (fd < 0) fd = open("/dev/dri/card0", O_RDWR | O_CLOEXEC);
    if (fd < 0) fd = open("/dev/null", O_RDWR | O_CLOEXEC);
    return fd;
}

int mt_ion_open(const char *name) {
    (void)name;
    return ion_open();
}

int ion_close(int fd) {
    if (fd >= 0) return close(fd);
    return 0;
}

int ion_alloc_fd(int fd, size_t len, size_t align, unsigned int heap_mask, unsigned int flags, int *handle_fd) {
    (void)align; (void)heap_mask; (void)flags;
    if (!handle_fd) return -EINVAL;
    size_t pages = (len + 4095) / 4096;
    if (pages == 0) pages = 1;

    struct drm_mode_create_dumb creq;
    memset(&creq, 0, sizeof(creq));
    creq.width = 1024;
    creq.height = (uint32_t)pages;
    creq.bpp = 32;
    if (ioctl(fd, DRM_IOCTL_MODE_CREATE_DUMB, &creq) == 0) {
        struct drm_prime_handle preq;
        memset(&preq, 0, sizeof(preq));
        preq.handle = creq.handle;
        preq.flags = DRM_CLOEXEC | DRM_RDWR;
        int rc = ioctl(fd, DRM_IOCTL_PRIME_HANDLE_TO_FD, &preq);
        struct drm_mode_destroy_dumb dreq = { .handle = creq.handle };
        ioctl(fd, DRM_IOCTL_MODE_DESTROY_DUMB, &dreq);
        if (rc == 0 && preq.fd >= 0) {
            *handle_fd = preq.fd;
            return 0;
        }
    }
    int mfd = memfd_create("ion_fallback", MFD_CLOEXEC);
    if (mfd >= 0) {
        if (ftruncate(mfd, (off_t)(pages * 4096)) == 0) {
            *handle_fd = mfd;
            return 0;
        }
        close(mfd);
    }
    return -ENOMEM;
}

int ion_alloc(int fd, size_t len, size_t align, unsigned int heap_mask, unsigned int flags, int *handle) {
    return ion_alloc_fd(fd, len, align, heap_mask, flags, handle);
}

int ion_import(int fd, int share_fd, int *handle) {
    (void)fd;
    if (handle) *handle = share_fd;
    return 0;
}

int ion_free(int fd, int handle) {
    (void)fd; (void)handle;
    return 0;
}

int ion_custom_ioctl(int fd, unsigned int cmd, void *arg) {
    (void)fd; (void)cmd; (void)arg;
    return 0;
}
