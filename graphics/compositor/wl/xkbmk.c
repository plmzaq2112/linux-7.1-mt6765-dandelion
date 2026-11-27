/* Build-time helper: dump the default "us" XKB keymap as a string.
 * Runs on the build host only; the compositor embeds the result. */
#include <stdio.h>
#include <stdlib.h>
#include <xkbcommon/xkbcommon.h>

int main(void)
{
    struct xkb_context *ctx = xkb_context_new(XKB_CONTEXT_NO_FLAGS);
    struct xkb_rule_names names = {
        .rules = "evdev",
        .model = "pc105",
        .layout = "us",
        .variant = NULL,
        .options = NULL,
    };
    struct xkb_keymap *km;
    char *str;

    if (!ctx)
        return 1;
    km = xkb_keymap_new_from_names(ctx, &names, XKB_KEYMAP_COMPILE_NO_FLAGS);
    if (!km)
        return 1;
    str = xkb_keymap_get_as_string(km, XKB_KEYMAP_FORMAT_TEXT_V1);
    if (!str)
        return 1;
    fputs(str, stdout);
    free(str);
    xkb_keymap_unref(km);
    xkb_context_unref(ctx);
    return 0;
}
