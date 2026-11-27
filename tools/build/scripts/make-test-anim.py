from PIL import Image, ImageDraw
import math, subprocess, os

A = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/artifacts"
frames = []
N = 40
for i in range(N):
    img = Image.new("RGB", (480, 480), (8, 8, 24))
    d = ImageDraw.Draw(img)
    ang = 2 * math.pi * i / N
    cx = 240 + int(120 * math.cos(ang))
    cy = 240 + int(120 * math.sin(ang))
    r, g, b = (128 + 127 * math.sin(ang), 128 + 127 * math.sin(ang + 2.1), 128 + 127 * math.sin(ang + 4.2))
    d.ellipse([cx - 90, cy - 90, cx + 90, cy + 90], fill=(int(r), int(g), int(b)))
    d.ellipse([220, 220, 260, 260], fill=(255, 255, 255))
    frames.append(img)

gif = os.path.join(A, "test-anim.gif")
frames[0].save(gif, save_all=True, append_images=frames[1:], duration=60, loop=0)
print("gif:", gif, os.path.getsize(gif))

subprocess.run(["python3", os.path.join(A, "convert-gif.py"), gif,
                os.path.join(A, "test-anim.kmsa")], check=True)
