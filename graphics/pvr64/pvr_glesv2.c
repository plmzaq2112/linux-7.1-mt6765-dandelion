/*
 * pvr_glesv2.c - libGLESv2.so.2 shim for the PowerVR GE8320 bridge.
 *
 * All gl* entry points resolve through DT_NEEDED libGLESv2_mtk.so (global
 * symbol scope).  We only override glFlush: the DDK 1.13 dma-buf import path
 * does not attach GPU fences to the dma-buf reservation object, so the KMS
 * driver cannot implicitly wait for rendering.  wlroots 0.17 relies on
 * implicit sync after glFlush(), hence we turn glFlush into glFinish (can be
 * disabled with PVR_GL_FLUSH_IS_FLUSH=1).
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define EXPORT __attribute__((visibility("default")))

#define GL_FRAMEBUFFER        0x8D40
#define GL_READ_FRAMEBUFFER   0x8CA8
#define GL_DRAW_FRAMEBUFFER   0x8CA9
#define GL_RENDERBUFFER       0x8D41
#define GL_TEXTURE_2D         0x0DE1
#define GL_COLOR_ATTACHMENT0  0x8CE0

static void (*real_flush)(void);
static void (*real_finish)(void);
static void (*real_bind_framebuffer)(unsigned int, unsigned int);
static void (*real_bind_renderbuffer)(unsigned int, unsigned int);
static void (*real_bind_texture)(unsigned int, unsigned int);
static void (*real_framebuffer_renderbuffer)(unsigned int, unsigned int, unsigned int, unsigned int);
static void (*real_framebuffer_texture_2d)(unsigned int, unsigned int, unsigned int, unsigned int, int);
static void (*real_delete_framebuffers)(int, const unsigned int *);
static void (*real_delete_renderbuffers)(int, const unsigned int *);
static void (*real_delete_textures)(int, const unsigned int *);
static int (*egl_attach_fence)(void *);
static int flush_is_flush;
static int force_finish;

#define MAX_TRACK 256
struct obj_img { unsigned int id; void *img; };
struct fbo_att { unsigned int fbo; unsigned int obj; int is_tex; };

static struct obj_img rbo_imgs[MAX_TRACK];
static struct obj_img tex_imgs[MAX_TRACK];
static struct fbo_att fbo_atts[MAX_TRACK];
static pthread_mutex_t track_lock = PTHREAD_MUTEX_INITIALIZER;
static __thread unsigned int cur_draw_fbo;
static __thread unsigned int last_draw_fbo;
static __thread unsigned int cur_rbo;
static __thread unsigned int cur_tex_2d;
static __thread unsigned int g_window_fbo;

EXPORT void pvr_gles_set_window_fbo(unsigned int fbo)
{
	g_window_fbo = fbo;
	cur_draw_fbo = fbo;
	if (fbo)
		last_draw_fbo = fbo;
	if (real_bind_framebuffer)
		real_bind_framebuffer(GL_FRAMEBUFFER, fbo);
}

static void set_obj_img(struct obj_img *arr, unsigned int id, void *img)
{
	if (!id) return;
	for (int i = 0; i < MAX_TRACK; i++) {
		if (arr[i].id == id) { arr[i].img = img; if (!img) arr[i].id = 0; return; }
	}
	if (!img) return;
	for (int i = 0; i < MAX_TRACK; i++) {
		if (!arr[i].id) { arr[i].id = id; arr[i].img = img; return; }
	}
}

static void *get_obj_img(struct obj_img *arr, unsigned int id)
{
	if (!id) return NULL;
	for (int i = 0; i < MAX_TRACK; i++)
		if (arr[i].id == id) return arr[i].img;
	return NULL;
}

static void set_fbo_att(unsigned int fbo, unsigned int obj, int is_tex)
{
	if (!fbo) return;
	for (int i = 0; i < MAX_TRACK; i++) {
		if (fbo_atts[i].fbo == fbo) {
			if (!obj) fbo_atts[i].fbo = 0;
			else { fbo_atts[i].obj = obj; fbo_atts[i].is_tex = is_tex; }
			return;
		}
	}
	if (!obj) return;
	for (int i = 0; i < MAX_TRACK; i++) {
		if (!fbo_atts[i].fbo) {
			fbo_atts[i].fbo = fbo;
			fbo_atts[i].obj = obj;
			fbo_atts[i].is_tex = is_tex;
			return;
		}
	}
}

static void *lookup_fbo_image(unsigned int fbo)
{
	if (!fbo) return NULL;
	for (int i = 0; i < MAX_TRACK; i++) {
		if (fbo_atts[i].fbo == fbo)
			return get_obj_img(fbo_atts[i].is_tex ? tex_imgs : rbo_imgs, fbo_atts[i].obj);
	}
	return NULL;
}

EXPORT void pvr_gles_track_rbo_image(unsigned int target, void *img)
{
	if (target == GL_RENDERBUFFER && cur_rbo) {
		pthread_mutex_lock(&track_lock);
		set_obj_img(rbo_imgs, cur_rbo, img);
		pthread_mutex_unlock(&track_lock);
	}
}

EXPORT void pvr_gles_track_tex_image(unsigned int target, void *img)
{
	if (target == GL_TEXTURE_2D && cur_tex_2d) {
		pthread_mutex_lock(&track_lock);
		set_obj_img(tex_imgs, cur_tex_2d, img);
		pthread_mutex_unlock(&track_lock);
	}
}

__attribute__((constructor)) static void init(void)
{
	void *h = dlopen("libGLESv2_mtk.so", RTLD_NOW | RTLD_NOLOAD);
	if (!h)
		h = dlopen("/vendor/lib64/egl/libGLESv2_mtk.so", RTLD_NOW | RTLD_GLOBAL);
	if (h) {
		real_flush = (void (*)(void))dlsym(h, "glFlush");
		real_finish = (void (*)(void))dlsym(h, "glFinish");
		real_bind_framebuffer = (void (*)(unsigned int, unsigned int))dlsym(h, "glBindFramebuffer");
		real_bind_renderbuffer = (void (*)(unsigned int, unsigned int))dlsym(h, "glBindRenderbuffer");
		real_bind_texture = (void (*)(unsigned int, unsigned int))dlsym(h, "glBindTexture");
		real_framebuffer_renderbuffer = (void (*)(unsigned int, unsigned int, unsigned int, unsigned int))dlsym(h, "glFramebufferRenderbuffer");
		real_framebuffer_texture_2d = (void (*)(unsigned int, unsigned int, unsigned int, unsigned int, int))dlsym(h, "glFramebufferTexture2D");
		real_delete_framebuffers = (void (*)(int, const unsigned int *))dlsym(h, "glDeleteFramebuffers");
		real_delete_renderbuffers = (void (*)(int, const unsigned int *))dlsym(h, "glDeleteRenderbuffers");
		real_delete_textures = (void (*)(int, const unsigned int *))dlsym(h, "glDeleteTextures");
	}
	flush_is_flush = getenv("PVR_GL_FLUSH_IS_FLUSH") != NULL;
	force_finish = getenv("PVR_GL_FLUSH_FORCE_FINISH") != NULL;
}

EXPORT void glBindFramebuffer(unsigned int target, unsigned int fbo)
{
	if (fbo == 0 && g_window_fbo)
		fbo = g_window_fbo;
	if (target == GL_FRAMEBUFFER || target == GL_DRAW_FRAMEBUFFER) {
		cur_draw_fbo = fbo;
		if (fbo)
			last_draw_fbo = fbo;
	}
	if (real_bind_framebuffer)
		real_bind_framebuffer(target, fbo);
}

EXPORT void glBindRenderbuffer(unsigned int target, unsigned int rbo)
{
	if (target == GL_RENDERBUFFER)
		cur_rbo = rbo;
	if (real_bind_renderbuffer)
		real_bind_renderbuffer(target, rbo);
}

EXPORT void glBindTexture(unsigned int target, unsigned int tex)
{
	if (target == GL_TEXTURE_2D)
		cur_tex_2d = tex;
	if (real_bind_texture)
		real_bind_texture(target, tex);
}

EXPORT void glFramebufferRenderbuffer(unsigned int target, unsigned int attachment,
				      unsigned int rbtarget, unsigned int rbo)
{
	if ((target == GL_FRAMEBUFFER || target == GL_DRAW_FRAMEBUFFER) &&
	    attachment == GL_COLOR_ATTACHMENT0 && rbtarget == GL_RENDERBUFFER && cur_draw_fbo) {
		pthread_mutex_lock(&track_lock);
		set_fbo_att(cur_draw_fbo, rbo, 0);
		pthread_mutex_unlock(&track_lock);
	}
	if (real_framebuffer_renderbuffer)
		real_framebuffer_renderbuffer(target, attachment, rbtarget, rbo);
}

EXPORT void glFramebufferTexture2D(unsigned int target, unsigned int attachment,
				   unsigned int textarget, unsigned int tex, int level)
{
	if ((target == GL_FRAMEBUFFER || target == GL_DRAW_FRAMEBUFFER) &&
	    attachment == GL_COLOR_ATTACHMENT0 && textarget == GL_TEXTURE_2D && cur_draw_fbo) {
		pthread_mutex_lock(&track_lock);
		set_fbo_att(cur_draw_fbo, tex, 1);
		pthread_mutex_unlock(&track_lock);
	}
	if (real_framebuffer_texture_2d)
		real_framebuffer_texture_2d(target, attachment, textarget, tex, level);
}

EXPORT void glDeleteFramebuffers(int n, const unsigned int *fbos)
{
	if (fbos && n > 0) {
		pthread_mutex_lock(&track_lock);
		for (int i = 0; i < n; i++) {
			set_fbo_att(fbos[i], 0, 0);
			if (last_draw_fbo == fbos[i]) last_draw_fbo = 0;
			if (cur_draw_fbo == fbos[i]) cur_draw_fbo = 0;
		}
		pthread_mutex_unlock(&track_lock);
	}
	if (real_delete_framebuffers)
		real_delete_framebuffers(n, fbos);
}

EXPORT void glDeleteRenderbuffers(int n, const unsigned int *rbos)
{
	if (rbos && n > 0) {
		pthread_mutex_lock(&track_lock);
		for (int i = 0; i < n; i++)
			set_obj_img(rbo_imgs, rbos[i], NULL);
		pthread_mutex_unlock(&track_lock);
	}
	if (real_delete_renderbuffers)
		real_delete_renderbuffers(n, rbos);
}

EXPORT void glDeleteTextures(int n, const unsigned int *texs)
{
	if (texs && n > 0) {
		pthread_mutex_lock(&track_lock);
		for (int i = 0; i < n; i++)
			set_obj_img(tex_imgs, texs[i], NULL);
		pthread_mutex_unlock(&track_lock);
	}
	if (real_delete_textures)
		real_delete_textures(n, texs);
}

EXPORT void glFlush(void)
{
	if (force_finish && real_finish) {
		real_finish();
		return;
	}
	if (real_flush)
		real_flush();
	if (flush_is_flush)
		return;

	unsigned int fbo = cur_draw_fbo ? cur_draw_fbo : last_draw_fbo;
	void *img = NULL;
	if (fbo) {
		pthread_mutex_lock(&track_lock);
		img = lookup_fbo_image(fbo);
		pthread_mutex_unlock(&track_lock);
	}
	if (img) {
		if (!egl_attach_fence) {
			void *he = dlopen("libEGL.so.1", RTLD_NOLOAD);
			egl_attach_fence = (int (*)(void *))dlsym(he ? he : RTLD_DEFAULT, "pvr_egl_attach_fence_to_image");
		}
		if (egl_attach_fence && egl_attach_fence(img) == 0) {
			last_draw_fbo = 0;
			return;
		}
	}
	if (real_finish)
		real_finish();
}

/*
 * wlroots requires GL_EXT_unpack_subimage (GL_UNPACK_ROW_LENGTH & co).  The
 * DDK returns an ES 3.x context even when ES2 is requested, where these unpack
 * parameters are core, but it does not list the extension.  Advertise it when
 * the context is ES 3.x.
 */
#define GL_VERSION    0x1F02
#define GL_EXTENSIONS 0x1F03
static const unsigned char *(*real_get_string)(unsigned int);
static char *ext_cache;

EXPORT const unsigned char *glGetString(unsigned int name)
{
	if (!real_get_string) {
		void *h = dlopen("/vendor/lib64/egl/libGLESv2_mtk.so", RTLD_NOW | RTLD_GLOBAL);
		real_get_string = (const unsigned char *(*)(unsigned int))dlsym(h, "glGetString");
	}
	const unsigned char *s = real_get_string(name);
	if (name != GL_EXTENSIONS || !s)
		return s;
	const char *ver = (const char *)real_get_string(GL_VERSION);
	if (!ver || strncmp(ver, "OpenGL ES 3", 11) || strstr((const char *)s, "GL_EXT_unpack_subimage"))
		return s;
	if (!ext_cache) {
		size_t n = strlen((const char *)s);
		char *c = malloc(n + sizeof(" GL_EXT_unpack_subimage"));
		if (!c)
			return s;
		memcpy(c, s, n);
		strcpy(c + n, " GL_EXT_unpack_subimage");
		ext_cache = c;
	}
	return (const unsigned char *)ext_cache;
}
