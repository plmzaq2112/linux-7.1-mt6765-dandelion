#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <dlfcn.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <drm/drm.h>
#include <drm/drm_mode.h>
#include <drm/drm_fourcc.h>

typedef int32_t EGLint;
typedef unsigned int EGLBoolean;
typedef unsigned int EGLenum;
typedef void *EGLDisplay;
typedef void *EGLConfig;
typedef void *EGLSurface;
typedef void *EGLContext;
typedef void *EGLClientBuffer;
typedef void *EGLImageKHR;
typedef void *EGLNativeDisplayType;

#define EGL_DEFAULT_DISPLAY ((EGLNativeDisplayType)0)
#define EGL_NO_DISPLAY ((EGLDisplay)0)
#define EGL_NO_CONTEXT ((EGLContext)0)
#define EGL_NO_SURFACE ((EGLSurface)0)
#define EGL_NO_IMAGE_KHR ((EGLImageKHR)0)

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
#define EGL_EXTENSIONS 0x3055

#define EGL_LINUX_DMA_BUF_EXT 0x3270
#define EGL_LINUX_DRM_FOURCC_EXT 0x3271
#define EGL_DMA_BUF_PLANE0_FD_EXT 0x3272
#define EGL_DMA_BUF_PLANE0_OFFSET_EXT 0x3273
#define EGL_DMA_BUF_PLANE0_PITCH_EXT 0x3274

typedef unsigned int GLenum;
typedef unsigned char GLboolean;
typedef unsigned int GLbitfield;
typedef int GLint;
typedef int GLsizei;
typedef unsigned int GLuint;
typedef float GLfloat;
typedef char GLchar;

#define GL_COLOR_BUFFER_BIT 0x00004000
#define GL_TRIANGLES 0x0004
#define GL_FLOAT 0x1406
#define GL_FRAMEBUFFER 0x8D40
#define GL_RENDERBUFFER 0x8D41
#define GL_COLOR_ATTACHMENT0 0x8CE0
#define GL_FRAMEBUFFER_COMPLETE 0x8CD5
#define GL_FRAGMENT_SHADER 0x8B30
#define GL_VERTEX_SHADER 0x8B31

#define LOAD_SYM(handle, var, name) do { \
    var = dlsym(handle, name); \
    if (!var) { fprintf(stderr, "Missing symbol: %s\n", name); return 1; } \
} while (0)

int main(void) {
    printf("=== PowerVR GE8320 <-> mediatek-drm (card1) Zero-Copy DMA-BUF Render Test ===\n");

    /* 1. Open mediatek-drm (/dev/dri/card1) and allocate a 256x256 XRGB8888 dumb buffer */
    int drm_fd = open("/dev/dri/card1", O_RDWR | O_CLOEXEC);
    if (drm_fd < 0) {
        perror("open /dev/dri/card1");
        return 1;
    }

    const uint32_t W = 256, H = 256;
    struct drm_mode_create_dumb creq = {
        .width = W,
        .height = H,
        .bpp = 32,
    };
    if (ioctl(drm_fd, DRM_IOCTL_MODE_CREATE_DUMB, &creq) < 0) {
        perror("DRM_IOCTL_MODE_CREATE_DUMB");
        return 1;
    }
    struct drm_prime_handle preq = {
        .handle = creq.handle,
        .flags = DRM_CLOEXEC | DRM_RDWR,
    };
    if (ioctl(drm_fd, DRM_IOCTL_PRIME_HANDLE_TO_FD, &preq) < 0) {
        perror("DRM_IOCTL_PRIME_HANDLE_TO_FD");
        return 1;
    }
    struct drm_mode_map_dumb mreq = { .handle = creq.handle };
    if (ioctl(drm_fd, DRM_IOCTL_MODE_MAP_DUMB, &mreq) < 0) {
        perror("DRM_IOCTL_MODE_MAP_DUMB");
        return 1;
    }
    uint8_t *drm_map = mmap(NULL, creq.size, PROT_READ | PROT_WRITE, MAP_SHARED, drm_fd, mreq.offset);
    if (drm_map == MAP_FAILED) {
        perror("mmap dumb buffer");
        return 1;
    }
    memset(drm_map, 0, creq.size);
    printf("[1] Allocated mediatek-drm dumb buffer: handle=%u pitch=%u size=%llu dmabuf_fd=%d\n",
           creq.handle, creq.pitch, (unsigned long long)creq.size, preq.fd);

    /* 2. Initialize PowerVR EGL + GLESv2 */
    void *libegl = dlopen("/vendor/lib64/egl/libEGL_mtk.so", RTLD_NOW | RTLD_GLOBAL);
    void *libgles = dlopen("/vendor/lib64/egl/libGLESv2_mtk.so", RTLD_NOW | RTLD_GLOBAL);
    if (!libegl || !libgles) {
        fprintf(stderr, "dlopen failed: %s\n", dlerror());
        return 1;
    }

    EGLDisplay (*p_eglGetDisplay)(EGLNativeDisplayType);
    EGLBoolean (*p_eglInitialize)(EGLDisplay, EGLint *, EGLint *);
    const char *(*p_eglQueryString)(EGLDisplay, EGLint);
    EGLBoolean (*p_eglChooseConfig)(EGLDisplay, const EGLint *, EGLConfig *, EGLint, EGLint *);
    EGLSurface (*p_eglCreatePbufferSurface)(EGLDisplay, EGLConfig, const EGLint *);
    EGLContext (*p_eglCreateContext)(EGLDisplay, EGLConfig, EGLContext, const EGLint *);
    EGLBoolean (*p_eglMakeCurrent)(EGLDisplay, EGLSurface, EGLSurface, EGLContext);
    void *(*p_eglGetProcAddress)(const char *);
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
    LOAD_SYM(libegl, p_eglGetProcAddress, "eglGetProcAddress");
    LOAD_SYM(libegl, p_eglDestroyContext, "eglDestroyContext");
    LOAD_SYM(libegl, p_eglDestroySurface, "eglDestroySurface");
    LOAD_SYM(libegl, p_eglTerminate, "eglTerminate");
    LOAD_SYM(libegl, p_eglGetError, "eglGetError");

    EGLImageKHR (*p_eglCreateImageKHR)(EGLDisplay, EGLContext, EGLenum, EGLClientBuffer, const EGLint *) =
        p_eglGetProcAddress("eglCreateImageKHR");
    EGLBoolean (*p_eglDestroyImageKHR)(EGLDisplay, EGLImageKHR) =
        p_eglGetProcAddress("eglDestroyImageKHR");
    void (*p_glEGLImageTargetRenderbufferStorageOES)(GLenum, EGLImageKHR) =
        p_eglGetProcAddress("glEGLImageTargetRenderbufferStorageOES");

    void (*p_glGenFramebuffers)(GLsizei, GLuint *);
    void (*p_glBindFramebuffer)(GLenum, GLuint);
    void (*p_glGenRenderbuffers)(GLsizei, GLuint *);
    void (*p_glBindRenderbuffer)(GLenum, GLuint);
    void (*p_glFramebufferRenderbuffer)(GLenum, GLenum, GLenum, GLuint);
    GLenum (*p_glCheckFramebufferStatus)(GLenum);
    void (*p_glViewport)(GLint, GLint, GLsizei, GLsizei);
    void (*p_glClearColor)(GLfloat, GLfloat, GLfloat, GLfloat);
    void (*p_glClear)(GLbitfield);
    GLuint (*p_glCreateShader)(GLenum);
    void (*p_glShaderSource)(GLuint, GLsizei, const GLchar *const*, const GLint *);
    void (*p_glCompileShader)(GLuint);
    GLuint (*p_glCreateProgram)(void);
    void (*p_glAttachShader)(GLuint, GLuint);
    void (*p_glBindAttribLocation)(GLuint, GLuint, const GLchar *);
    void (*p_glLinkProgram)(GLuint);
    void (*p_glUseProgram)(GLuint);
    void (*p_glVertexAttribPointer)(GLuint, GLint, GLenum, GLboolean, GLsizei, const void *);
    void (*p_glEnableVertexAttribArray)(GLuint);
    void (*p_glDrawArrays)(GLenum, GLint, GLsizei);
    void (*p_glFinish)(void);

    LOAD_SYM(libgles, p_glGenFramebuffers, "glGenFramebuffers");
    LOAD_SYM(libgles, p_glBindFramebuffer, "glBindFramebuffer");
    LOAD_SYM(libgles, p_glGenRenderbuffers, "glGenRenderbuffers");
    LOAD_SYM(libgles, p_glBindRenderbuffer, "glBindRenderbuffer");
    LOAD_SYM(libgles, p_glFramebufferRenderbuffer, "glFramebufferRenderbuffer");
    LOAD_SYM(libgles, p_glCheckFramebufferStatus, "glCheckFramebufferStatus");
    LOAD_SYM(libgles, p_glViewport, "glViewport");
    LOAD_SYM(libgles, p_glClearColor, "glClearColor");
    LOAD_SYM(libgles, p_glClear, "glClear");
    LOAD_SYM(libgles, p_glCreateShader, "glCreateShader");
    LOAD_SYM(libgles, p_glShaderSource, "glShaderSource");
    LOAD_SYM(libgles, p_glCompileShader, "glCompileShader");
    LOAD_SYM(libgles, p_glCreateProgram, "glCreateProgram");
    LOAD_SYM(libgles, p_glAttachShader, "glAttachShader");
    LOAD_SYM(libgles, p_glBindAttribLocation, "glBindAttribLocation");
    LOAD_SYM(libgles, p_glLinkProgram, "glLinkProgram");
    LOAD_SYM(libgles, p_glUseProgram, "glUseProgram");
    LOAD_SYM(libgles, p_glVertexAttribPointer, "glVertexAttribPointer");
    LOAD_SYM(libgles, p_glEnableVertexAttribArray, "glEnableVertexAttribArray");
    LOAD_SYM(libgles, p_glDrawArrays, "glDrawArrays");
    LOAD_SYM(libgles, p_glFinish, "glFinish");

    EGLDisplay dpy = p_eglGetDisplay(EGL_DEFAULT_DISPLAY);
    p_eglInitialize(dpy, NULL, NULL);
    printf("[2] EGL_EXTENSIONS = %s\n", p_eglQueryString(dpy, EGL_EXTENSIONS));

    const EGLint cfg_attribs[] = {
        EGL_SURFACE_TYPE, EGL_PBUFFER_BIT,
        EGL_RENDERABLE_TYPE, EGL_OPENGL_ES2_BIT,
        EGL_RED_SIZE, 8, EGL_GREEN_SIZE, 8, EGL_BLUE_SIZE, 8, EGL_ALPHA_SIZE, 8,
        EGL_NONE
    };
    EGLConfig cfg = NULL;
    EGLint num_cfg = 0;
    p_eglChooseConfig(dpy, cfg_attribs, &cfg, 1, &num_cfg);

    /* 1x1 dummy PBuffer for surfaceless context binding */
    const EGLint pbuf_attribs[] = { EGL_WIDTH, 1, EGL_HEIGHT, 1, EGL_NONE };
    EGLSurface dummy_surf = p_eglCreatePbufferSurface(dpy, cfg, pbuf_attribs);
    const EGLint ctx_attribs[] = { EGL_CONTEXT_CLIENT_VERSION, 2, EGL_NONE };
    EGLContext ctx = p_eglCreateContext(dpy, cfg, EGL_NO_CONTEXT, ctx_attribs);
    p_eglMakeCurrent(dpy, dummy_surf, dummy_surf, ctx);

    /* 3. Import mediatek-drm DMA-BUF fd into PowerVR via EGL_LINUX_DMA_BUF_EXT */
    const EGLint img_attrs[] = {
        EGL_WIDTH, W,
        EGL_HEIGHT, H,
        EGL_LINUX_DRM_FOURCC_EXT, DRM_FORMAT_ARGB8888,
        EGL_DMA_BUF_PLANE0_FD_EXT, preq.fd,
        EGL_DMA_BUF_PLANE0_OFFSET_EXT, 0,
        EGL_DMA_BUF_PLANE0_PITCH_EXT, (EGLint)creq.pitch,
        EGL_NONE
    };
    EGLImageKHR img = p_eglCreateImageKHR(dpy, EGL_NO_CONTEXT, EGL_LINUX_DMA_BUF_EXT, NULL, img_attrs);
    if (img == EGL_NO_IMAGE_KHR) {
        fprintf(stderr, "eglCreateImageKHR(EGL_LINUX_DMA_BUF_EXT) failed: 0x%x\n", p_eglGetError());
        return 1;
    }
    printf("[3] Imported mediatek-drm DMA-BUF fd=%d into PowerVR EGLImageKHR=%p!\n", preq.fd, img);

    /* 4. Bind EGLImageKHR to FBO and render 3D triangle directly into mediatek-drm buffer */
    GLuint rbo = 0, fbo = 0;
    p_glGenRenderbuffers(1, &rbo);
    p_glBindRenderbuffer(GL_RENDERBUFFER, rbo);
    p_glEGLImageTargetRenderbufferStorageOES(GL_RENDERBUFFER, img);

    p_glGenFramebuffers(1, &fbo);
    p_glBindFramebuffer(GL_FRAMEBUFFER, fbo);
    p_glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_RENDERBUFFER, rbo);
    GLenum fb_status = p_glCheckFramebufferStatus(GL_FRAMEBUFFER);
    printf("[4] FBO status = 0x%x (expected 0x%x GL_FRAMEBUFFER_COMPLETE)\n", fb_status, GL_FRAMEBUFFER_COMPLETE);

    const char *vs_src =
        "attribute vec4 aPos;\n"
        "attribute vec4 aCol;\n"
        "varying vec4 vCol;\n"
        "void main() { gl_Position = aPos; vCol = aCol; }\n";
    const char *fs_src =
        "precision mediump float;\n"
        "varying vec4 vCol;\n"
        "void main() { gl_FragColor = vCol; }\n";

    GLuint vs = p_glCreateShader(GL_VERTEX_SHADER);
    p_glShaderSource(vs, 1, &vs_src, NULL);
    p_glCompileShader(vs);
    GLuint fs = p_glCreateShader(GL_FRAGMENT_SHADER);
    p_glShaderSource(fs, 1, &fs_src, NULL);
    p_glCompileShader(fs);
    GLuint prog = p_glCreateProgram();
    p_glAttachShader(prog, vs);
    p_glAttachShader(prog, fs);
    p_glBindAttribLocation(prog, 0, "aPos");
    p_glBindAttribLocation(prog, 1, "aCol");
    p_glLinkProgram(prog);
    p_glUseProgram(prog);

    p_glViewport(0, 0, W, H);
    p_glClearColor(0.08f, 0.12f, 0.24f, 1.0f);
    p_glClear(GL_COLOR_BUFFER_BIT);

    const float verts[] = { 0.0f, 0.75f, 0.0f, -0.75f, -0.75f, 0.0f, 0.75f, -0.75f, 0.0f };
    const float cols[]  = { 1.0f, 0.1f, 0.1f, 1.0f, 0.1f, 1.0f, 0.1f, 1.0f, 0.1f, 0.3f, 1.0f, 1.0f };
    p_glVertexAttribPointer(0, 3, GL_FLOAT, 0, 0, verts);
    p_glEnableVertexAttribArray(0);
    p_glVertexAttribPointer(1, 4, GL_FLOAT, 0, 0, cols);
    p_glEnableVertexAttribArray(1);
    p_glDrawArrays(GL_TRIANGLES, 0, 3);
    p_glFinish();

    /* 5. Read directly from mediatek-drm dumb buffer mmap (ZERO glReadPixels!) */
    uint8_t *bg = &drm_map[(10 * W + 10) * 4];
    uint8_t *center = &drm_map[((H / 2) * W + (W / 2)) * 4];
    printf("[5] Direct mediatek-drm mmap read (NO glReadPixels!): bg BGRA=(%u,%u,%u,%u), center BGRA=(%u,%u,%u,%u)\n",
           bg[0], bg[1], bg[2], bg[3], center[0], center[1], center[2], center[3]);

    p_eglDestroyImageKHR(dpy, img);
    p_eglMakeCurrent(dpy, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
    p_eglDestroyContext(dpy, ctx);
    p_eglDestroySurface(dpy, dummy_surf);
    p_eglTerminate(dpy);
    munmap(drm_map, creq.size);
    close(preq.fd);
    close(drm_fd);
    printf("[6] Zero-copy DMA-BUF test completed cleanly!\n");
    return 0;
}
