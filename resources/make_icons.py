"""Generates the launcher icon, adaptive-icon layers, splash and Play Store icon.

Run from the repo root:  python3 resources/make_icons.py
Needs Pillow. Output goes straight into android/app/src/main/res and store/.
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, 'android', 'app', 'src', 'main', 'res')
STORE = os.path.join(ROOT, 'store')
FONT = os.path.join(ROOT, 'resources', 'unbounded-cyrillic-900-normal.ttf')

BLUE = (28, 93, 171)        # --accent of the app
BLUE_DARK = (20, 72, 138)
WHITE = (255, 255, 255)
YELLOW = (255, 200, 40)     # road-marking yellow

U = 32                      # supersampling: pixels per dp of the 108-dp adaptive canvas
S = 108 * U


def foreground(color=WHITE, mark=YELLOW):
    """Adaptive-icon foreground: 108x108 dp canvas, artwork inside the 66-dp safe circle."""
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype(FONT, 17 * U)
    text = 'ПДР'
    l, t, r, b = d.textbbox((0, 0), text, font=font)
    w, h = r - l, b - t
    x = (S - w) / 2 - l
    y = 54 * U - h / 2 - 4 * U - t
    d.text((x, y), text, font=font, fill=color)
    # dashed road marking under the letters
    dash, gap, th = 8 * U, 4.5 * U, 3.2 * U
    total = 3 * dash + 2 * gap
    x0, y0 = (S - total) / 2, 54 * U + h / 2 + 1 * U
    for i in range(3):
        xs = x0 + i * (dash + gap)
        d.rounded_rectangle((xs, y0, xs + dash, y0 + th), radius=th / 2, fill=mark)
    return im


def background():
    im = Image.new('RGBA', (S, S), BLUE + (255,))
    # soft diagonal light: lighter top-left, darker bottom-right
    g = Image.new('L', (64, 64))
    g.putdata([int(255 * (x + y) / 126) for y in range(64) for x in range(64)])
    grad = g.resize((S, S), Image.BILINEAR)
    dark = Image.new('RGBA', (S, S), BLUE_DARK + (255,))
    return Image.composite(dark, im, grad)


def full(shape):
    """Legacy (pre-Android 8) icon: background + foreground clipped to a rounded square or a circle."""
    art = background()
    art.alpha_composite(foreground())
    # legacy icons show the central 72 dp of the 108-dp canvas (scaled 48 dp + padding)
    c = 18 * U
    art = art.crop((c, c, S - c, S - c))
    n = art.size[0]
    mask = Image.new('L', (n, n), 0)
    md = ImageDraw.Draw(mask)
    pad = int(n * 0.04)
    if shape == 'round':
        md.ellipse((pad, pad, n - pad, n - pad), fill=255)
    else:
        md.rounded_rectangle((pad, pad, n - pad, n - pad), radius=int(n * 0.18), fill=255)
    out = Image.new('RGBA', (n, n), (0, 0, 0, 0))
    out.paste(art, (0, 0), mask)
    return out


DENS = {'mdpi': 1, 'hdpi': 1.5, 'xhdpi': 2, 'xxhdpi': 3, 'xxxhdpi': 4}


def save(im, path, px):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.resize((px, px), Image.LANCZOS).save(path, optimize=True)


def main():
    fg, sq, rd = foreground(), full('square'), full('round')
    for name, k in DENS.items():
        folder = os.path.join(RES, f'mipmap-{name}')
        save(fg, os.path.join(folder, 'ic_launcher_foreground.png'), round(108 * k))
        save(sq, os.path.join(folder, 'ic_launcher.png'), round(48 * k))
        save(rd, os.path.join(folder, 'ic_launcher_round.png'), round(48 * k))
    # monochrome layer for themed icons (Android 13+): one solid colour, the system tints it
    mono = foreground(WHITE, WHITE)
    for name, k in DENS.items():
        save(mono, os.path.join(RES, f'mipmap-{name}', 'ic_launcher_monochrome.png'), round(108 * k))
    # splash for Android < 12 (Android 12+ uses the adaptive icon on @color/splash_background)
    splash = foreground()
    save(splash, os.path.join(RES, 'drawable-nodpi', 'splash_icon.png'), 432)
    # Play Store: 512x512, full square (Google Play rounds the corners itself)
    os.makedirs(STORE, exist_ok=True)
    art = background(); art.alpha_composite(foreground())
    c = 18 * U
    art.crop((c, c, S - c, S - c)).resize((512, 512), Image.LANCZOS).convert('RGB').save(os.path.join(STORE, 'icon-512.png'), optimize=True)
    print('icons written')


if __name__ == '__main__':
    main()
