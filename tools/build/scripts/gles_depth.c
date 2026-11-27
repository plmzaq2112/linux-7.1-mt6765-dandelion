/* Vendor GLES2 depth test oracle: pbuffer with D16 depth, two overlapping
 * quads (near green, far red). Used to capture the 1.13 3D stream with a
 * depth buffer attached so the ZS descriptor offsets can be located. */
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef void *EGLDisplay, *EGLConfig, *EGLSurface, *EGLContext;
typedef int32_t EGLint;
typedef uint32_t EGLBoolean, GLenum, GLuint, GLint, GLbitfield;
typedef intptr_t GLsizeiptr, GLsizei, GLintptr;
typedef unsigned char GLboolean;
typedef float GLfloat;
typedef char GLchar;

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
#define EGL_DEPTH_SIZE 0x3025
#define EGL_WIDTH 0x3057
#define EGL_HEIGHT 0x3056
#define EGL_CONTEXT_CLIENT_VERSION 0x3098

#define GL_COLOR_BUFFER_BIT 0x4000
#define GL_DEPTH_BUFFER_BIT 0x0100
#define GL_RGBA 0x1908
#define GL_UNSIGNED_BYTE 0x1401
#define GL_DEPTH_TEST 0x0B71
#define GL_LESS 0x0201
#define GL_RENDERER 0x1F01
#define GL_VERTEX_SHADER 0x8B31
#define GL_FRAGMENT_SHADER 0x8B30
#define GL_COMPILE_STATUS 0x8B81
#define GL_LINK_STATUS 0x8B82
#define GL_ARRAY_BUFFER 0x8892
#define GL_STATIC_DRAW 0x88E4
#define GL_FLOAT 0x1406
#define GL_FALSE 0
#define GL_TRIANGLES 0x0004

static void *sym(void *h, const char *n)
{
    void *p = dlsym(h, n);
    if (!p) {
        fprintf(stderr, "missing %s\n", n);
        exit(1);
    }
    return p;
}

static void *gpa(void *(*getProc)(const char *), void *h, const char *n)
{
    void *p = getProc ? getProc(n) : NULL;
    if (!p)
        p = dlsym(h, n);
    if (!p) {
        fprintf(stderr, "missing GL %s\n", n);
        exit(1);
    }
    return p;
}

int main(int argc, char **argv)
{
    int w = argc > 1 ? atoi(argv[1]) : 64;
    int hgt = argc > 2 ? atoi(argv[2]) : 64;

    const char *egln = getenv("EGL_LIB");
    const char *gln = getenv("GLES_LIB");
    if (!egln)
        egln = "libEGL_mtk.so";
    if (!gln)
        gln = "libGLESv2_mtk.so";
    void *he = dlopen(egln, RTLD_NOW);
    if (!he) {
        fprintf(stderr, "dlopen EGL: %s\n", dlerror());
        return 1;
    }
    void *hg = dlopen(gln, RTLD_NOW);
    if (!hg) {
        fprintf(stderr, "dlopen GLES: %s\n", dlerror());
        return 1;
    }

    void *(*eglGetProcAddress)(const char *) = dlsym(he, "eglGetProcAddress");
    EGLDisplay (*eglGetDisplay)(void *) = sym(he, "eglGetDisplay");
    EGLBoolean (*eglInitialize)(EGLDisplay, EGLint *, EGLint *) =
        sym(he, "eglInitialize");
    EGLBoolean (*eglChooseConfig)(EGLDisplay, const EGLint *, EGLConfig *,
                                  EGLint, EGLint *) = sym(he, "eglChooseConfig");
    EGLSurface (*eglCreatePbufferSurface)(EGLDisplay, EGLConfig, const EGLint *) =
        sym(he, "eglCreatePbufferSurface");
    EGLContext (*eglCreateContext)(EGLDisplay, EGLConfig, EGLContext,
                                   const EGLint *) = sym(he, "eglCreateContext");
    EGLBoolean (*eglMakeCurrent)(EGLDisplay, EGLSurface, EGLSurface, EGLContext) =
        sym(he, "eglMakeCurrent");
    EGLint (*eglGetError)(void) = sym(he, "eglGetError");

    GLuint (*glCreateShader)(GLenum) = gpa(eglGetProcAddress, hg, "glCreateShader");
    void (*glShaderSource)(GLuint, GLsizei, const GLchar *const *, const GLint *) =
        gpa(eglGetProcAddress, hg, "glShaderSource");
    void (*glCompileShader)(GLuint) = gpa(eglGetProcAddress, hg, "glCompileShader");
    void (*glGetShaderiv)(GLuint, GLenum, GLint *) =
        gpa(eglGetProcAddress, hg, "glGetShaderiv");
    GLuint (*glCreateProgram)(void) = gpa(eglGetProcAddress, hg, "glCreateProgram");
    void (*glAttachShader)(GLuint, GLuint) = gpa(eglGetProcAddress, hg, "glAttachShader");
    void (*glBindAttribLocation)(GLuint, GLuint, const GLchar *) =
        gpa(eglGetProcAddress, hg, "glBindAttribLocation");
    void (*glLinkProgram)(GLuint) = gpa(eglGetProcAddress, hg, "glLinkProgram");
    void (*glGetProgramiv)(GLuint, GLenum, GLint *) =
        gpa(eglGetProcAddress, hg, "glGetProgramiv");
    void (*glUseProgram)(GLuint) = gpa(eglGetProcAddress, hg, "glUseProgram");
    void (*glGenBuffers)(GLint, GLuint *) = gpa(eglGetProcAddress, hg, "glGenBuffers");
    void (*glBindBuffer)(GLenum, GLuint) = gpa(eglGetProcAddress, hg, "glBindBuffer");
    void (*glBufferData)(GLenum, GLsizeiptr, const void *, GLenum) =
        gpa(eglGetProcAddress, hg, "glBufferData");
    void (*glVertexAttribPointer)(GLuint, GLint, GLenum, GLboolean, GLsizei,
                                  const void *) =
        gpa(eglGetProcAddress, hg, "glVertexAttribPointer");
    void (*glEnableVertexAttribArray)(GLuint) =
        gpa(eglGetProcAddress, hg, "glEnableVertexAttribArray");
    void (*glViewport)(GLint, GLint, GLsizei, GLsizei) =
        gpa(eglGetProcAddress, hg, "glViewport");
    void (*glDrawArrays)(GLenum, GLint, GLsizei) =
        gpa(eglGetProcAddress, hg, "glDrawArrays");
    void (*glReadPixels)(GLint, GLint, GLsizei, GLsizei, GLenum, GLenum, void *) =
        gpa(eglGetProcAddress, hg, "glReadPixels");
    void (*glFinish)(void) = gpa(eglGetProcAddress, hg, "glFinish");
    void (*glClear)(GLbitfield) = gpa(eglGetProcAddress, hg, "glClear");
    void (*glClearColor)(GLfloat, GLfloat, GLfloat, GLfloat) =
        gpa(eglGetProcAddress, hg, "glClearColor");
    void (*glClearDepthf)(GLfloat) = gpa(eglGetProcAddress, hg, "glClearDepthf");
    void (*glEnable)(GLenum) = gpa(eglGetProcAddress, hg, "glEnable");
    void (*glDepthFunc)(GLenum) = gpa(eglGetProcAddress, hg, "glDepthFunc");
    GLenum (*glGetError)(void) = gpa(eglGetProcAddress, hg, "glGetError");
    const unsigned char *(*glGetString)(GLenum) =
        gpa(eglGetProcAddress, hg, "glGetString");

    EGLDisplay d = eglGetDisplay((void *)(uintptr_t)EGL_DEFAULT_DISPLAY);
    EGLint maj, min;
    if (!eglInitialize(d, &maj, &min)) {
        fprintf(stderr, "eglInitialize err %x\n", eglGetError());
        return 1;
    }

    EGLint cfgAttrs[] = {
        EGL_SURFACE_TYPE, EGL_PBUFFER_BIT,
        EGL_RENDERABLE_TYPE, EGL_OPENGL_ES2_BIT,
        EGL_RED_SIZE, 8, EGL_GREEN_SIZE, 8, EGL_BLUE_SIZE, 8, EGL_ALPHA_SIZE, 8,
        EGL_DEPTH_SIZE, 16,
        EGL_NONE,
    };
    EGLConfig cfg;
    EGLint n = 0;
    if (!eglChooseConfig(d, cfgAttrs, &cfg, 1, &n) || n < 1) {
        fprintf(stderr, "chooseConfig err %x\n", eglGetError());
        return 1;
    }

    EGLint pbAttrs[] = { EGL_WIDTH, w, EGL_HEIGHT, hgt, EGL_NONE };
    EGLSurface s = eglCreatePbufferSurface(d, cfg, pbAttrs);
    if (!s) {
        fprintf(stderr, "pbuffer err %x\n", eglGetError());
        return 1;
    }
    EGLint ctxAttrs[] = { EGL_CONTEXT_CLIENT_VERSION, 2, EGL_NONE };
    EGLContext c = eglCreateContext(d, cfg, NULL, ctxAttrs);
    if (!c) {
        fprintf(stderr, "context err %x\n", eglGetError());
        return 1;
    }
    if (!eglMakeCurrent(d, s, s, c)) {
        fprintf(stderr, "makeCurrent err %x\n", eglGetError());
        return 1;
    }
    fprintf(stderr, "GL_RENDERER=%s\n", (const char *)glGetString(GL_RENDERER));

    const char *vs_src =
        "attribute vec3 a_pos;\n"
        "attribute vec4 a_col;\n"
        "varying vec4 v_col;\n"
        "void main() { v_col = a_col; gl_Position = vec4(a_pos, 1.0); }\n";
    const char *fs_src =
        "precision mediump float;\n"
        "varying vec4 v_col;\n"
        "void main() { gl_FragColor = v_col; }\n";

    GLuint vs = glCreateShader(GL_VERTEX_SHADER);
    glShaderSource(vs, 1, &vs_src, NULL);
    glCompileShader(vs);
    GLint ok = 0;
    glGetShaderiv(vs, GL_COMPILE_STATUS, &ok);
    if (!ok) {
        fprintf(stderr, "vertex compile failed\n");
        return 1;
    }
    GLuint fs = glCreateShader(GL_FRAGMENT_SHADER);
    glShaderSource(fs, 1, &fs_src, NULL);
    glCompileShader(fs);
    glGetShaderiv(fs, GL_COMPILE_STATUS, &ok);
    if (!ok) {
        fprintf(stderr, "fragment compile failed\n");
        return 1;
    }
    GLuint prog = glCreateProgram();
    glAttachShader(prog, vs);
    glAttachShader(prog, fs);
    glBindAttribLocation(prog, 0, "a_pos");
    glBindAttribLocation(prog, 1, "a_col");
    glLinkProgram(prog);
    glGetProgramiv(prog, GL_LINK_STATUS, &ok);
    if (!ok) {
        fprintf(stderr, "link failed\n");
        return 1;
    }
    glUseProgram(prog);

    /* near green quad (centre half) then far red quad (full screen) */
    float verts[] = {
        -0.5f, -0.5f, 0.1f, 0, 1, 0, 1,
         0.5f, -0.5f, 0.1f, 0, 1, 0, 1,
        -0.5f,  0.5f, 0.1f, 0, 1, 0, 1,
         0.5f, -0.5f, 0.1f, 0, 1, 0, 1,
         0.5f,  0.5f, 0.1f, 0, 1, 0, 1,
        -0.5f,  0.5f, 0.1f, 0, 1, 0, 1,
        -1.0f, -1.0f, 0.9f, 1, 0, 0, 1,
         1.0f, -1.0f, 0.9f, 1, 0, 0, 1,
        -1.0f,  1.0f, 0.9f, 1, 0, 0, 1,
         1.0f, -1.0f, 0.9f, 1, 0, 0, 1,
         1.0f,  1.0f, 0.9f, 1, 0, 0, 1,
        -1.0f,  1.0f, 0.9f, 1, 0, 0, 1,
    };
    GLuint vbo;
    glGenBuffers(1, &vbo);
    glBindBuffer(GL_ARRAY_BUFFER, vbo);
    glBufferData(GL_ARRAY_BUFFER, sizeof(verts), verts, GL_STATIC_DRAW);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 7 * sizeof(float), 0);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 7 * sizeof(float),
                          (const void *)(3 * sizeof(float)));
    glEnableVertexAttribArray(1);

    glViewport(0, 0, w, hgt);
    glEnable(GL_DEPTH_TEST);
    glDepthFunc(GL_LESS);
    glClearColor(0.0f, 0.0f, 1.0f, 1.0f);
    glClearDepthf(1.0f);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

    glDrawArrays(GL_TRIANGLES, 0, 6);   /* near green */
    glDrawArrays(GL_TRIANGLES, 6, 6);   /* far red, must be rejected */
    glFinish();

    unsigned char px[4] = { 0, 0, 0, 0 };
    glReadPixels(w / 2, hgt / 2, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE, px);
    unsigned char c0[4] = { 0, 0, 0, 0 };
    glReadPixels(0, 0, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE, c0);
    glFinish();
    printf("gles depth %dx%d center=%u,%u,%u,%u corner=%u,%u,%u,%u glerr=0x%x\n",
           w, hgt, px[0], px[1], px[2], px[3], c0[0], c0[1], c0[2], c0[3],
           glGetError());
    return 0;
}
