# -*- coding: utf-8 -*-
"""Generate ShaoNian brand icons and logos."""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = r"C:\Users\Administrator\Desktop\rustdesk"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
BLUE_TOP = (61, 155, 255)
BLUE_BOTTOM = (18, 84, 186)
WHITE = (255, 255, 255, 255)


def vertical_gradient(size, top, bottom):
    img = Image.new("RGB", (1, size))
    px = img.load()
    for y in range(size):
        t = y / max(1, size - 1)
        px[0, y] = tuple(round(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
    return img.resize((size, size), Image.NEAREST)


def rounded_mask(size, radius):
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return mask


def draw_mark(size):
    """Blue rounded square with white stacked 少 / 年."""
    ss = 4  # supersample
    s = size * ss
    base = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    grad = vertical_gradient(s, BLUE_TOP, BLUE_BOTTOM).convert("RGBA")
    mask = rounded_mask(s, radius=int(s * 0.235))
    base.paste(grad, (0, 0), mask)

    d = ImageDraw.Draw(base)
    # Fit two glyphs stacked inside the safe area.
    safe = int(s * 0.82)
    target = safe // 2
    font_size = target
    while font_size > 4:
        f = ImageFont.truetype(FONT_BOLD, font_size)
        b1 = d.textbbox((0, 0), "少", font=f)
        b2 = d.textbbox((0, 0), "年", font=f)
        h1, h2 = b1[3] - b1[1], b2[3] - b2[1]
        widest = max(b1[2] - b1[0], b2[2] - b2[0])
        if h1 + h2 <= safe and widest <= int(s * 0.80):
            break
        font_size -= 2
    f = ImageFont.truetype(FONT_BOLD, font_size)
    stroke = max(1, int(font_size * 0.035))

    b1 = d.textbbox((0, 0), "少", font=f)
    b2 = d.textbbox((0, 0), "年", font=f)
    h1, h2 = b1[3] - b1[1], b2[3] - b2[1]
    gap = int(s * 0.02)
    total = h1 + gap + h2
    top = (s - total) // 2
    cx = s // 2
    d.text((cx, top - b1[1]), "少", font=f, fill=WHITE, anchor="ma",
           stroke_width=stroke, stroke_fill=WHITE)
    d.text((cx, top + h1 + gap - b2[1]), "年", font=f, fill=WHITE, anchor="ma",
           stroke_width=stroke, stroke_fill=WHITE)

    return base.resize((size, size), Image.LANCZOS)


def save_ico(path, sizes):
    master = draw_mark(256)
    imgs = []
    for s in sizes:
        im = master.resize((s, s), Image.LANCZOS) if s != 256 else master
        imgs.append(im)
    imgs[-1].save(path, format="ICO",
                  sizes=[(i.size[0], i.size[1]) for i in imgs])


def wordmark(height, text_color, with_mark=True):
    ss = 2
    h = height * ss
    mark = draw_mark(h) if with_mark else None
    text = "少年远程"
    gap = int(h * 0.28)
    font_size = int(h * 0.56)
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    while font_size > 8:
        f = ImageFont.truetype(FONT_BOLD, font_size)
        b = d.textbbox((0, 0), text, font=f)
        if b[2] - b[0] <= h * 4 and b[3] - b[1] <= h * 0.66:
            break
        font_size -= 2
    f = ImageFont.truetype(FONT_BOLD, font_size)
    b = d.textbbox((0, 0), text, font=f)
    tw, th = b[2] - b[0], b[3] - b[1]
    total_w = (h + gap if with_mark else 0) + tw
    canvas = Image.new("RGBA", (total_w, h), (0, 0, 0, 0))
    x = 0
    if with_mark:
        canvas.paste(mark, (0, 0), mark)
        x = h + gap
    dc = ImageDraw.Draw(canvas)
    dc.text((x - b[0], (h - th) // 2 - b[1]), text, font=f, fill=text_color)
    return canvas.resize((total_w // ss, h // ss), Image.LANCZOS)


def main():
    # Application icon (exe / dll / MSI / installer).
    save_ico(os.path.join(ROOT, r"res\icon.ico"), [16, 32, 48, 64, 128, 256])
    # Tray icon keeps a single 32x32 entry, matching the previous file.
    draw_mark(32).save(os.path.join(ROOT, r"res\tray-icon.ico"), format="ICO",
                       sizes=[(32, 32)])
    # Flutter Windows runner icon (window + explorer + taskbar).
    save_ico(os.path.join(ROOT, r"flutter\windows\runner\resources\app_icon.ico"),
             [16, 32, 48, 256])

    for name, size in [("icon.png", 1024), ("mac-icon.png", 1024),
                       ("128x128@2x.png", 256), ("128x128.png", 128),
                       ("64x64.png", 64), ("32x32.png", 32)]:
        draw_mark(size).save(os.path.join(ROOT, "res", name))

    # In-app header logo: logo_light for light theme (blue text),
    # logo_dark for dark theme (near-white text), logo.png as fallback.
    assets = os.path.join(ROOT, r"flutter\assets")
    wordmark(64, (44, 140, 255, 255)).save(os.path.join(assets, "logo_light.png"))
    wordmark(64, (236, 243, 255, 255)).save(os.path.join(assets, "logo_dark.png"))
    wordmark(64, (44, 140, 255, 255)).save(os.path.join(assets, "logo.png"))
    print("done")


if __name__ == "__main__":
    main()
