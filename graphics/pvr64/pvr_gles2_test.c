#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <dlfcn.h>

typedef int32_t EGLint;
typedef unsigned int EGLBoolean;
typedef unsigned int EGLenum;
typedef void *EGLDisplay;
typedef void *EGLConfig;
typedef void *EGLSurface;
typedef void *EGLContext;
typedef void *EGLNativeDisplayType;

#define EGL_DEFAULT_DISPLAY ((EGLNativeDisplayType)0)
#define EGL_NO_DISPLAY ((EGLDisplay)0)
#define EGL_NO_CONTEXT ((EGLContext)0)
#define EGL_NO_SURFACE ((EGLSurface)0)
#define EGL_FALSE 0
#define EGL_TRUE 1

#define EGL_SURFACE_TYPE 0x3033
#define EGL_PBUFFER_BIT 0x0001
#define EGL_RENDERABLE_TYPE 0x3040
#define EGL_OPENGL_ES2_BIT 0x0004
#define EGL_RED_SIZE 0x3024
#define EGL_GREEN_SIZE 0x3023
#define EGL_BLUE_SIZE 0x3022
#define EGL_ALPHA_SIZE 0x3021
#define EGL_WIDTH 0x3057
#define EGL_HEIGHT 0x3056
#define EGL_CONTEXT_CLIENT_VERSION 0x3098
#define EGL_NONE 0x3038
#define EGL_VENDOR 0x3053
#define EGL_VERSION 0x3054
#define EGL_EXTENSIONS 0x3055

typedef unsigned int GLenum;
typedef unsigned char GLboolean;
typedef unsigned int GLbitfield;
typedef int GLint;
typedef int GLsizei;
typedef unsigned int GLuint;
typedef float GLfloat;
typedef char GLchar;
typedef unsigned char GLubyte;

#define GL_COLOR_BUFFER_BIT 0x00004000
#define GL_TRIANGLES 0x0004
#define GL_UNSIGNED_BYTE 0x1401
#define GL_FLOAT 0x1406
#define GL_RGBA 0x1908
#define GL_VENDOR 0x1F00
#define GL_RENDERER 0x1F01
#define GL_VERSION 0x1F02
#define GL_SHADING_LANGUAGE_VERSION 0x8B8C
#define GL_FRAGMENT_SHADER 0x8B30
#define GL_VERTEX_SHADER 0x8B31
#define GL_COMPILE_STATUS 0x8B81
#define GL_LINK_STATUS 0x8B82

#define LOAD_SYM(handle, var, name) do { \
    var = dlsym(handle, name); \
    if (!var) { fprintf(stderr, "Missing symbol: %s\n", name); return 1; } \
} while (0)

int main(void) {
    printf("=== PowerVR GE8320 64-bit EGL/GLESv2 Offscreen Render Test ===\n");
    void *libegl = dlopen("/vendor/lib64/egl/libEGL_mtk.so", RTLD_NOW | RTLD_GLOBAL);
    if (!libegl) {
        fprintf(stderr, "dlopen libEGL_mtk.so failed: %s\n", dlerror());
        return 1;
    }
    void *libgles = dlopen("/vendor/lib64/egl/libGLESv2_mtk.so", RTLD_NOW | RTLD_GLOBAL);
    if (!libgles) {
        fprintf(stderr, "dlopen libGLESv2_mtk.so failed: %s\n", dlerror());
        return 1;
    }
    printf("[1] Loaded 64-bit libEGL_mtk.so and libGLESv2_mtk.so successfully!\n");

    EGLDisplay (*p_eglGetDisplay)(EGLNativeDisplayType);
    EGLBoolean (*p_eglInitialize)(EGLDisplay, EGLint *, EGLint *);
    const char *(*p_eglQueryString)(EGLDisplay, EGLint);
    EGLBoolean (*p_eglChooseConfig)(EGLDisplay, const EGLint *, EGLConfig *, EGLint, EGLint *);
    EGLSurface (*p_eglCreatePbufferSurface)(EGLDisplay, EGLConfig, const EGLint *);
    EGLContext (*p_eglCreateContext)(EGLDisplay, EGLConfig, EGLContext, const EGLint *);
    EGLBoolean (*p_eglMakeCurrent)(EGLDisplay, EGLSurface, EGLSurface, EGLContext);
    EGLBoolean (*p_eglDestroyContext)(EGLDisplay, EGLContext);
    EGLBoolean (*p_eglDestroySurface)(EGLDisplay, EGLSurface);
    EGLBoolean (*p_eglTerminate)(EGLDisplay);
    EGLint (*p_eglGetError)(void);

    LOAD_SYM(libegl, p_eglGetDisplay, "eglGetDisplay");
    LOAD_SYM(libegl, p_eglInitialize, "eglInitialize");
    LOAD_SYM(libegl, p_eglQueryString, "eglQueryString");
    LOAD_SYM(libegl, p_eglChooseConfig, "eglChooseConfig");
    LOAD_SYM(libegl, p_eglCreatePbufferSurface, "eglCreatePbufferSurface");
    LOAD_SYM(libegl, p_eglCreateContext, "eglCreateContext");
    LOAD_SYM(libegl, p_eglMakeCurrent, "eglMakeCurrent");
    LOAD_SYM(libegl, p_eglDestroyContext, "eglDestroyContext");
    LOAD_SYM(libegl, p_eglDestroySurface, "eglDestroySurface");
    LOAD_SYM(libegl, p_eglTerminate, "eglTerminate");
    LOAD_SYM(libegl, p_eglGetError, "eglGetError");

    const GLubyte *(*p_glGetString)(GLenum);
    void (*p_glViewport)(GLint, GLint, GLsizei, GLsizei);
    void (*p_glClearColor)(GLfloat, GLfloat, GLfloat, GLfloat);
    void (*p_glClear)(GLbitfield);
    GLuint (*p_glCreateShader)(GLenum);
    void (*p_glShaderSource)(GLuint, GLsizei, const GLchar *const*, const GLint *);
    void (*p_glCompileShader)(GLuint);
    void (*p_glGetShaderiv)(GLuint, GLenum, GLint *);
    GLuint (*p_glCreateProgram)(void);
    void (*p_glAttachShader)(GLuint, GLuint);
    void (*p_glBindAttribLocation)(GLuint, GLuint, const GLchar *);
    void (*p_glLinkProgram)(GLuint);
    void (*p_glGetProgramiv)(GLuint, GLenum, GLint *);
    void (*p_glUseProgram)(GLuint);
    void (*p_glVertexAttribPointer)(GLuint, GLint, GLenum, GLboolean, GLsizei, const void *);
    void (*p_glEnableVertexAttribArray)(GLuint);
    void (*p_glDrawArrays)(GLenum, GLint, GLsizei);
    void (*p_glFinish)(void);
    void (*p_glReadPixels)(GLint, GLint, GLsizei, GLsizei, GLenum, GLenum, void *);

    LOAD_SYM(libgles, p_glGetString, "glGetString");
    LOAD_SYM(libgles, p_glViewport, "glViewport");
    LOAD_SYM(libgles, p_glClearColor, "glClearColor");
    LOAD_SYM(libgles, p_glClear, "glClear");
    LOAD_SYM(libgles, p_glCreateShader, "glCreateShader");
    LOAD_SYM(libgles, p_glShaderSource, "glShaderSource");
    LOAD_SYM(libgles, p_glCompileShader, "glCompileShader");
    LOAD_SYM(libgles, p_glGetShaderiv, "glGetShaderiv");
    LOAD_SYM(libgles, p_glCreateProgram, "glCreateProgram");
    LOAD_SYM(libgles, p_glAttachShader, "glAttachShader");
    LOAD_SYM(libgles, p_glBindAttribLocation, "glBindAttribLocation");
    LOAD_SYM(libgles, p_glLinkProgram, "glLinkProgram");
    LOAD_SYM(libgles, p_glGetProgramiv, "glGetProgramiv");
    LOAD_SYM(libgles, p_glUseProgram, "glUseProgram");
    LOAD_SYM(libgles, p_glVertexAttribPointer, "glVertexAttribPointer");
    LOAD_SYM(libgles, p_glEnableVertexAttribArray, "glEnableVertexAttribArray");
    LOAD_SYM(libgles, p_glDrawArrays, "glDrawArrays");
    LOAD_SYM(libgles, p_glFinish, "glFinish");
    LOAD_SYM(libgles, p_glReadPixels, "glReadPixels");

    EGLDisplay dpy = p_eglGetDisplay(EGL_DEFAULT_DISPLAY);
    printf("[2] eglGetDisplay = %p\n", dpy);
    EGLint major = 0, minor = 0;
    if (!p_eglInitialize(dpy, &major, &minor)) {
        fprintf(stderr, "eglInitialize failed: 0x%x\n", p_eglGetError());
        return 1;
    }
    printf("[3] eglInitialize OK: EGL %d.%d (%s)\n", major, minor, p_eglQueryString(dpy, EGL_VENDOR));

    const EGLint cfg_attribs[] = {
        EGL_SURFACE_TYPE, EGL_PBUFFER_BIT,
        EGL_RENDERABLE_TYPE, EGL_OPENGL_ES2_BIT,
        EGL_RED_SIZE, 8,
        EGL_GREEN_SIZE, 8,
        EGL_BLUE_SIZE, 8,
        EGL_ALPHA_SIZE, 8,
        EGL_NONE
    };
    EGLConfig cfg = NULL;
    EGLint num_cfg = 0;
    if (!p_eglChooseConfig(dpy, cfg_attribs, &cfg, 1, &num_cfg) || num_cfg < 1) {
        fprintf(stderr, "eglChooseConfig failed: 0x%x (num=%d)\n", p_eglGetError(), num_cfg);
        return 1;
    }

    const int W = 256, H = 256;
    const EGLint pbuf_attribs[] = { EGL_WIDTH, W, EGL_HEIGHT, H, EGL_NONE };
    EGLSurface surf = p_eglCreatePbufferSurface(dpy, cfg, pbuf_attribs);
    if (surf == EGL_NO_SURFACE) {
        fprintf(stderr, "eglCreatePbufferSurface failed: 0x%x\n", p_eglGetError());
        return 1;
    }

    const EGLint ctx_attribs[] = { EGL_CONTEXT_CLIENT_VERSION, 2, EGL_NONE };
    EGLContext ctx = p_eglCreateContext(dpy, cfg, EGL_NO_CONTEXT, ctx_attribs);
    if (ctx == EGL_NO_CONTEXT) {
        fprintf(stderr, "eglCreateContext failed: 0x%x\n", p_eglGetError());
        return 1;
    }

    if (!p_eglMakeCurrent(dpy, surf, surf, ctx)) {
        fprintf(stderr, "eglMakeCurrent failed: 0x%x\n", p_eglGetError());
        return 1;
    }

    printf("[4] GL_VENDOR   = %s\n", (const char *)p_glGetString(GL_VENDOR));
    printf("    GL_RENDERER = %s\n", (const char *)p_glGetString(GL_RENDERER));
    printf("    GL_VERSION  = %s\n", (const char *)p_glGetString(GL_VERSION));
    printf("    GL_SL_VER   = %s\n", (const char *)p_glGetString(GL_SHADING_LANGUAGE_VERSION));

    const char *vs_src =
        "attribute vec4 aPos;\n"
        "attribute vec4 aCol;\n"
        "varying vec4 vCol;\n"
        "void main() {\n"
        "    gl_Position = aPos;\n"
        "    vCol = aCol;\n"
        "}\n";
    const char *fs_src =
        "precision mediump float;\n"
        "varying vec4 vCol;\n"
        "void main() {\n"
        "    gl_FragColor = vCol;\n"
        "}\n";

    GLuint vs = p_glCreateShader(GL_VERTEX_SHADER);
    p_glShaderSource(vs, 1, &vs_src, NULL);
    p_glCompileShader(vs);
    GLint ok = 0;
    p_glGetShaderiv(vs, GL_COMPILE_STATUS, &ok);
    printf("[5] Vertex shader compile: %s\n", ok ? "OK" : "FAIL");

    GLuint fs = p_glCreateShader(GL_FRAGMENT_SHADER);
    p_glShaderSource(fs, 1, &fs_src, NULL);
    p_glCompileShader(fs);
    p_glGetShaderiv(fs, GL_COMPILE_STATUS, &ok);
    printf("    Fragment shader compile: %s\n", ok ? "OK" : "FAIL");

    GLuint prog = p_glCreateProgram();
    p_glAttachShader(prog, vs);
    p_glAttachShader(prog, fs);
    p_glBindAttribLocation(prog, 0, "aPos");
    p_glBindAttribLocation(prog, 1, "aCol");
    p_glLinkProgram(prog);
    p_glGetProgramiv(prog, GL_LINK_STATUS, &ok);
    printf("    Shader program link: %s\n", ok ? "OK" : "FAIL");
    p_glUseProgram(prog);

    p_glViewport(0, 0, W, H);
    p_glClearColor(0.08f, 0.12f, 0.24f, 1.0f);
    p_glClear(GL_COLOR_BUFFER_BIT);

    const float verts[] = {
         0.0f,  0.75f, 0.0f,
        -0.75f, -0.75f, 0.0f,
         0.75f, -0.75f, 0.0f,
    };
    const float cols[] = {
        1.0f, 0.1f, 0.1f, 1.0f,
        0.1f, 1.0f, 0.1f, 1.0f,
        0.1f, 0.3f, 1.0f, 1.0f,
    };
    p_glVertexAttribPointer(0, 3, GL_FLOAT, 0, 0, verts);
    p_glEnableVertexAttribArray(0);
    p_glVertexAttribPointer(1, 4, GL_FLOAT, 0, 0, cols);
    p_glEnableVertexAttribArray(1);
    p_glDrawArrays(GL_TRIANGLES, 0, 3);
    p_glFinish();

    uint8_t *pixels = (uint8_t *)calloc(W * H * 4, 1);
    p_glReadPixels(0, 0, W, H, GL_RGBA, GL_UNSIGNED_BYTE, pixels);

    uint8_t *bg = &pixels[(10 * W + 10) * 4];
    uint8_t *center = &pixels[((H / 2) * W + (W / 2)) * 4];
    printf("[6] Readback pixel (10,10) background RGBA = (%u, %u, %u, %u)\n",
           bg[0], bg[1], bg[2], bg[3]);
    printf("    Readback pixel (128,128) triangle RGBA = (%u, %u, %u, %u)\n",
           center[0], center[1], center[2], center[3]);

    FILE *fp = fopen("/tmp/pvr_render.ppm", "wb");
    if (fp) {
        fprintf(fp, "P6\n%d %d\n255\n", W, H);
        for (int y = H - 1; y >= 0; y--) {
            for (int x = 0; x < W; x++) {
                fwrite(&pixels[(y * W + x) * 4], 1, 3, fp);
            }
        }
        fclose(fp);
        printf("[7] Saved hardware-rendered frame to /tmp/pvr_render.ppm\n");
    }
    free(pixels);

    p_eglMakeCurrent(dpy, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
    p_eglDestroyContext(dpy, ctx);
    p_eglDestroySurface(dpy, surf);
    p_eglTerminate(dpy);
    printf("[8] Cleanly destroyed EGL context/surface and terminated EGL display.\n");
    return 0;
}
