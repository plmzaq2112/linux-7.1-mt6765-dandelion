/* Minimal EGL/GLES2 offscreen clear test (eglGetProcAddress for GL entry points). */
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>

typedef void *EGLDisplay, *EGLConfig, *EGLSurface, *EGLContext;
typedef int32_t EGLint;
typedef uint32_t EGLBoolean, GLenum;

#define EGL_DEFAULT_DISPLAY 0
#define EGL_NONE 0x3038
#define EGL_RENDERABLE_TYPE 0x3040
#define EGL_OPENGL_ES2_BIT 0x0004
#define EGL_SURFACE_TYPE 0x3033
#define EGL_PBUFFER_BIT 0x0001
#define EGL_RED_SIZE 0x3024
#define EGL_GREEN_SIZE 0x3023
#define EGL_BLUE_SIZE 0x3022
#define EGL_ALPHA_SIZE 0x3021
#define EGL_WIDTH 0x3057
#define EGL_HEIGHT 0x3056
#define EGL_CONTEXT_CLIENT_VERSION 0x3098
#define GL_COLOR_BUFFER_BIT 0x4000
#define GL_RGBA 0x1908
#define GL_UNSIGNED_BYTE 0x1401
#define GL_RENDERER 0x1F01
#define GL_VERSION 0x1F02

/* Optional LD_PRELOAD helper from pvr_dump_shim.c. */
extern void pvr_dump_maps(void) __attribute__((weak));

static void *gpa(void *(*getProc)(const char *), void *h, const char *n)
{
    void *p = getProc ? getProc(n) : NULL;
    if (!p) p = dlsym(h, n);
    if (!p) { fprintf(stderr, "missing %s\n", n); exit(1); }
    return p;
}

int main(int argc, char **argv)
{
    int w = argc > 1 ? atoi(argv[1]) : 64;
    int hgt = argc > 2 ? atoi(argv[2]) : 64;
    float r = argc > 3 ? atof(argv[3]) : 1.0f;
    float g = argc > 4 ? atof(argv[4]) : 0.0f;
    float b = argc > 5 ? atof(argv[5]) : 0.0f;

    const char *egln = getenv("EGL_LIB"); if (!egln) egln = "libEGL_mtk.so";
    const char *gln = getenv("GLES_LIB"); if (!gln) gln = "libGLESv2_mtk.so";
    void *he = dlopen(egln, RTLD_NOW);
    if (!he) { fprintf(stderr, "dlopen EGL: %s\n", dlerror()); return 1; }
    void *hg = dlopen(gln, RTLD_NOW);
    if (!hg) { fprintf(stderr, "dlopen GLES: %s\n", dlerror()); return 1; }

    void *(*eglGetProcAddress)(const char *) = dlsym(he, "eglGetProcAddress");
    if (!eglGetProcAddress) eglGetProcAddress = dlsym(hg, "eglGetProcAddress");

    EGLDisplay (*eglGetDisplay)(void *) = dlsym(he, "eglGetDisplay");
    EGLBoolean (*eglInitialize)(EGLDisplay, EGLint *, EGLint *) = dlsym(he, "eglInitialize");
    EGLBoolean (*eglChooseConfig)(EGLDisplay, const EGLint *, EGLConfig *, EGLint, EGLint *) = dlsym(he, "eglChooseConfig");
    EGLSurface (*eglCreatePbufferSurface)(EGLDisplay, EGLConfig, const EGLint *) = dlsym(he, "eglCreatePbufferSurface");
    EGLContext (*eglCreateContext)(EGLDisplay, EGLConfig, EGLContext, const EGLint *) = dlsym(he, "eglCreateContext");
    EGLBoolean (*eglMakeCurrent)(EGLDisplay, EGLSurface, EGLSurface, EGLContext) = dlsym(he, "eglMakeCurrent");
    EGLBoolean (*eglSwapBuffers)(EGLDisplay, EGLSurface) = dlsym(he, "eglSwapBuffers");
    EGLint (*eglGetError)(void) = dlsym(he, "eglGetError");

    void (*glClearColor)(float, float, float, float) = gpa(eglGetProcAddress, hg, "glClearColor");
    void (*glClear)(GLenum) = gpa(eglGetProcAddress, hg, "glClear");
    void (*glReadPixels)(int, int, int, int, GLenum, GLenum, void *) = gpa(eglGetProcAddress, hg, "glReadPixels");
    void (*glFinish)(void) = gpa(eglGetProcAddress, hg, "glFinish");
    GLenum (*glGetError)(void) = gpa(eglGetProcAddress, hg, "glGetError");
    const unsigned char *(*glGetString)(GLenum) = gpa(eglGetProcAddress, hg, "glGetString");

    EGLDisplay d = eglGetDisplay((void *)(uintptr_t)EGL_DEFAULT_DISPLAY);
    EGLint maj, min;
    if (!eglInitialize(d, &maj, &min)) { fprintf(stderr, "eglInitialize err %x\n", eglGetError()); return 1; }

    EGLint cfgAttrs[] = {
        EGL_SURFACE_TYPE, EGL_PBUFFER_BIT,
        EGL_RENDERABLE_TYPE, EGL_OPENGL_ES2_BIT,
        EGL_RED_SIZE, 8, EGL_GREEN_SIZE, 8, EGL_BLUE_SIZE, 8, EGL_ALPHA_SIZE, 8,
        EGL_NONE
    };
    EGLConfig cfg;
    EGLint n = 0;
    if (!eglChooseConfig(d, cfgAttrs, &cfg, 1, &n) || n < 1) {
        fprintf(stderr, "chooseConfig err %x n=%d\n", eglGetError(), n); return 1;
    }

    EGLint pbAttrs[] = { EGL_WIDTH, w, EGL_HEIGHT, hgt, EGL_NONE };
    EGLSurface s = eglCreatePbufferSurface(d, cfg, pbAttrs);
    if (!s) { fprintf(stderr, "pbuffer err %x\n", eglGetError()); return 1; }

    EGLint ctxAttrs[] = { EGL_CONTEXT_CLIENT_VERSION, 2, EGL_NONE };
    EGLContext c = eglCreateContext(d, cfg, NULL, ctxAttrs);
    if (!c) { fprintf(stderr, "context err %x\n", eglGetError()); return 1; }
    if (!eglMakeCurrent(d, s, s, c)) { fprintf(stderr, "makeCurrent err %x\n", eglGetError()); return 1; }

    fprintf(stderr, "GL_RENDERER=%s\n", (const char *)glGetString(GL_RENDERER));

    glClearColor(r, g, b, 1.0f);

    if (getenv("GLES_LOOP")) {
        int loop = atoi(getenv("GLES_LOOP"));
        struct timespec a, bb;
        double tot = 0.0;
        for (int i = 0; i < loop; i++) {
            clock_gettime(CLOCK_MONOTONIC, &a);
            glClear(GL_COLOR_BUFFER_BIT);
            glFinish();
            eglSwapBuffers(d, s);
            clock_gettime(CLOCK_MONOTONIC, &bb);
            tot += (bb.tv_sec - a.tv_sec) + (bb.tv_nsec - a.tv_nsec) / 1e9;
        }
        printf("gles bench %dx%d: %d frames, %.2f ms/frame\n", w, hgt, loop,
               1000.0 * tot / loop);
    }

    glClear(GL_COLOR_BUFFER_BIT);
    glFinish();
    eglSwapBuffers(d, s);
    if (pvr_dump_maps)
        pvr_dump_maps();

    unsigned char *buf = malloc((size_t)w * hgt * 4);
    for (int i = 0; i < w * hgt * 4; i++) buf[i] = 0x5a;
    glReadPixels(0, 0, w, hgt, GL_RGBA, GL_UNSIGNED_BYTE, buf);
    glFinish();
    printf("clear %dx%d rgba=(%.2f,%.2f,%.2f,1) px0=(%u,%u,%u,%u) pxlast=(%u,%u,%u,%u) glerr=0x%x egl=0x%x\n",
           w, hgt, r, g, b,
           buf[0], buf[1], buf[2], buf[3],
           buf[(w * hgt - 1) * 4], buf[(w * hgt - 1) * 4 + 1],
           buf[(w * hgt - 1) * 4 + 2], buf[(w * hgt - 1) * 4 + 3],
           glGetError(), eglGetError());
    return 0;
}
