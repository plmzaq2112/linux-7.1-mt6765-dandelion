/* Vendor GLES2 triangle, no glClear: used to capture the 1.13 draw control
 * stream with the kernel pvr_dump_stream parameter. */
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

typedef void *EGLDisplay, *EGLConfig, *EGLSurface, *EGLContext;
typedef int32_t EGLint;
typedef uint32_t EGLBoolean, GLenum, GLuint, GLint, GLbitfield, GLboolean;
typedef char GLchar;
typedef intptr_t GLsizeiptr, GLintptr;

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

#define GL_FRAGMENT_SHADER 0x8B30
#define GL_VERTEX_SHADER 0x8B31
#define GL_COMPILE_STATUS 0x8B81
#define GL_LINK_STATUS 0x8B82
#define GL_ARRAY_BUFFER 0x8892
#define GL_STATIC_DRAW 0x88E4
#define GL_FLOAT 0x1406
#define GL_FALSE 0
#define GL_TRIANGLES 0x0004
#define GL_RGBA 0x1908
#define GL_UNSIGNED_BYTE 0x1401
#define GL_RENDERER 0x1F01

static void *sym(void *h, const char *n)
{
    void *p = dlsym(h, n);
    if (!p) { fprintf(stderr, "missing %s\n", n); exit(1); }
    return p;
}

static void *gpa(void *(*getProc)(const char *), void *h, const char *n)
{
    void *p = getProc ? getProc(n) : NULL;
    if (!p) p = dlsym(h, n);
    if (!p) { fprintf(stderr, "missing GL %s\n", n); exit(1); }
    return p;
}

int main(int argc, char **argv)
{
    int w = argc > 1 ? atoi(argv[1]) : 64;
    int hgt = argc > 2 ? atoi(argv[2]) : 64;

    const char *egln = getenv("EGL_LIB"); if (!egln) egln = "libEGL_mtk.so";
    const char *gln = getenv("GLES_LIB"); if (!gln) gln = "libGLESv2_mtk.so";
    void *he = dlopen(egln, RTLD_NOW);
    if (!he) { fprintf(stderr, "dlopen EGL: %s\n", dlerror()); return 1; }
    void *hg = dlopen(gln, RTLD_NOW);
    if (!hg) { fprintf(stderr, "dlopen GLES: %s\n", dlerror()); return 1; }

    void *(*eglGetProcAddress)(const char *) = dlsym(he, "eglGetProcAddress");
    EGLDisplay (*eglGetDisplay)(void *) = sym(he, "eglGetDisplay");
    EGLBoolean (*eglInitialize)(EGLDisplay, EGLint *, EGLint *) = sym(he, "eglInitialize");
    EGLBoolean (*eglChooseConfig)(EGLDisplay, const EGLint *, EGLConfig *, EGLint, EGLint *) = sym(he, "eglChooseConfig");
    EGLSurface (*eglCreatePbufferSurface)(EGLDisplay, EGLConfig, const EGLint *) = sym(he, "eglCreatePbufferSurface");
    EGLContext (*eglCreateContext)(EGLDisplay, EGLConfig, EGLContext, const EGLint *) = sym(he, "eglCreateContext");
    EGLBoolean (*eglMakeCurrent)(EGLDisplay, EGLSurface, EGLSurface, EGLContext) = sym(he, "eglMakeCurrent");
    EGLint (*eglGetError)(void) = sym(he, "eglGetError");

    GLuint (*glCreateShader)(GLenum) = gpa(eglGetProcAddress, hg, "glCreateShader");
    void (*glShaderSource)(GLuint, GLsizeiptr, const GLchar *const *, const GLint *) = gpa(eglGetProcAddress, hg, "glShaderSource");
    void (*glCompileShader)(GLuint) = gpa(eglGetProcAddress, hg, "glCompileShader");
    void (*glGetShaderiv)(GLuint, GLenum, GLint *) = gpa(eglGetProcAddress, hg, "glGetShaderiv");
    GLuint (*glCreateProgram)(void) = gpa(eglGetProcAddress, hg, "glCreateProgram");
    void (*glAttachShader)(GLuint, GLuint) = gpa(eglGetProcAddress, hg, "glAttachShader");
    void (*glBindAttribLocation)(GLuint, GLuint, const GLchar *) = gpa(eglGetProcAddress, hg, "glBindAttribLocation");
    void (*glLinkProgram)(GLuint) = gpa(eglGetProcAddress, hg, "glLinkProgram");
    void (*glGetProgramiv)(GLuint, GLenum, GLint *) = gpa(eglGetProcAddress, hg, "glGetProgramiv");
    void (*glUseProgram)(GLuint) = gpa(eglGetProcAddress, hg, "glUseProgram");
    void (*glGenBuffers)(GLint, GLuint *) = gpa(eglGetProcAddress, hg, "glGenBuffers");
    void (*glBindBuffer)(GLenum, GLuint) = gpa(eglGetProcAddress, hg, "glBindBuffer");
    void (*glBufferData)(GLenum, GLsizeiptr, const void *, GLenum) = gpa(eglGetProcAddress, hg, "glBufferData");
    void (*glVertexAttribPointer)(GLuint, GLint, GLenum, GLboolean, GLint, const void *) = gpa(eglGetProcAddress, hg, "glVertexAttribPointer");
    void (*glEnableVertexAttribArray)(GLuint) = gpa(eglGetProcAddress, hg, "glEnableVertexAttribArray");
    void (*glViewport)(GLint, GLint, GLint, GLint) = gpa(eglGetProcAddress, hg, "glViewport");
    void (*glDrawArrays)(GLenum, GLint, GLint) = gpa(eglGetProcAddress, hg, "glDrawArrays");
    void (*glReadPixels)(GLint, GLint, GLint, GLint, GLenum, GLenum, void *) = gpa(eglGetProcAddress, hg, "glReadPixels");
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
        fprintf(stderr, "chooseConfig err %x\n", eglGetError()); return 1;
    }

    EGLint pbAttrs[] = { EGL_WIDTH, w, EGL_HEIGHT, hgt, EGL_NONE };
    EGLSurface s = eglCreatePbufferSurface(d, cfg, pbAttrs);
    if (!s) { fprintf(stderr, "pbuffer err %x\n", eglGetError()); return 1; }

    EGLint ctxAttrs[] = { EGL_CONTEXT_CLIENT_VERSION, 2, EGL_NONE };
    EGLContext c = eglCreateContext(d, cfg, NULL, ctxAttrs);
    if (!c) { fprintf(stderr, "context err %x\n", eglGetError()); return 1; }
    if (!eglMakeCurrent(d, s, s, c)) { fprintf(stderr, "makeCurrent err %x\n", eglGetError()); return 1; }

    fprintf(stderr, "GL_RENDERER=%s\n", (const char *)glGetString(GL_RENDERER));

    const char *vs_src =
        "attribute vec2 a_pos;\n"
        "void main() { gl_Position = vec4(a_pos, 0.0, 1.0); }\n";
    const char *fs_src =
        "precision mediump float;\n"
        "void main() { gl_FragColor = vec4(0.0, 1.0, 0.0, 1.0); }\n";

    GLuint vs = glCreateShader(GL_VERTEX_SHADER);
    glShaderSource(vs, 1, &vs_src, NULL);
    glCompileShader(vs);
    GLint ok = 0;
    glGetShaderiv(vs, GL_COMPILE_STATUS, &ok);
    if (!ok) { fprintf(stderr, "vertex compile failed\n"); return 1; }

    GLuint fs = glCreateShader(GL_FRAGMENT_SHADER);
    glShaderSource(fs, 1, &fs_src, NULL);
    glCompileShader(fs);
    glGetShaderiv(fs, GL_COMPILE_STATUS, &ok);
    if (!ok) { fprintf(stderr, "fragment compile failed\n"); return 1; }

    GLuint prog = glCreateProgram();
    glAttachShader(prog, vs);
    glAttachShader(prog, fs);
    glBindAttribLocation(prog, 0, "a_pos");
    glLinkProgram(prog);
    glGetProgramiv(prog, GL_LINK_STATUS, &ok);
    if (!ok) { fprintf(stderr, "link failed\n"); return 1; }
    glUseProgram(prog);

    float verts[] = {
        -0.8f, -0.8f,
         0.8f, -0.8f,
         0.0f,  0.8f,
    };
    GLuint vbo;
    glGenBuffers(1, &vbo);
    glBindBuffer(GL_ARRAY_BUFFER, vbo);
    glBufferData(GL_ARRAY_BUFFER, sizeof(verts), verts, GL_STATIC_DRAW);
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, 0);
    glEnableVertexAttribArray(0);
    glViewport(0, 0, w, hgt);

    if (getenv("GLES_LOOP")) {
        int loop = atoi(getenv("GLES_LOOP"));
        struct timespec a, b;
        double tot = 0.0;

        for (int i = 0; i < loop; i++) {
            clock_gettime(CLOCK_MONOTONIC, &a);
            glDrawArrays(GL_TRIANGLES, 0, 3);
            glFinish();
            clock_gettime(CLOCK_MONOTONIC, &b);
            tot += (b.tv_sec - a.tv_sec) + (b.tv_nsec - a.tv_nsec) / 1e9;
        }
        printf("gles tri bench %dx%d: %d frames, %.2f ms/frame\n", w, hgt, loop,
               1000.0 * tot / loop);
    }

    {
        int ndraws = getenv("GLES_DRAWS") ? atoi(getenv("GLES_DRAWS")) : 1;

        if (ndraws < 1)
            ndraws = 1;
        for (int d = 0; d < ndraws; d++)
            glDrawArrays(GL_TRIANGLES, 0, 3);
    }
    glFinish();

    unsigned char px[4] = {0, 0, 0, 0};
    glReadPixels(0, 0, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE, px);
    glFinish();
    printf("triangle %dx%d center=%u,%u,%u,%u glerr=0x%x\n",
           w, hgt, px[0], px[1], px[2], px[3], glGetError());
    return 0;
}
