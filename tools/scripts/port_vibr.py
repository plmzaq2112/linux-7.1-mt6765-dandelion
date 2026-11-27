#!/usr/bin/env python3
"""Port the vendor MTK regulator-vibrator driver to the 7.1 tree."""
from pathlib import Path

P = Path("/mnt/c/Users/31806/Documents/AI_Project/Redmi_9A/silex-linux-dandelion/kernel/modules/regulator-vibrator/regulator-vibrator.c")
s = P.read_text(encoding="utf-8")

old = "#include <linux/module.h>\n"
new = "#include <linux/module.h>\n#include <linux/of.h>\n"
assert s.count(old) == 1
s = s.replace(old, new, 1)

old = """\thrtimer_init(&(m_vibr->vibr_timer), CLOCK_MONOTONIC, HRTIMER_MODE_REL);
\tm_vibr->vibr_timer.function = mtk_vibrator_timer_func;
"""
new = """\thrtimer_setup(&m_vibr->vibr_timer, mtk_vibrator_timer_func,
\t\t      CLOCK_MONOTONIC, HRTIMER_MODE_REL);
"""
assert s.count(old) == 1
s = s.replace(old, new, 1)

old = """static int vib_remove(struct platform_device *pdev)
{
\tstruct reg_vibr *vibr = platform_get_drvdata(pdev);

\tcancel_work_sync(&vibr->vibr_work);
\thrtimer_cancel(&vibr->vibr_timer);
\tdevm_led_classdev_unregister(&pdev->dev, &led_vibr);

\treturn 0;
}
"""
new = """static void vib_remove(struct platform_device *pdev)
{
\tstruct reg_vibr *vibr = platform_get_drvdata(pdev);

\tcancel_work_sync(&vibr->vibr_work);
\thrtimer_cancel(&vibr->vibr_timer);
}
"""
assert s.count(old) == 1
s = s.replace(old, new, 1)

P.write_text(s, encoding="utf-8")
print("ported: of.h, hrtimer_setup, void remove")
