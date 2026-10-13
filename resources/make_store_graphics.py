"""Google Play graphics: captioned phone screenshots (1080x1920) and the feature graphic (1024x500).

Run from the repo root after taking raw screenshots into store/screenshots/raw/:
    python3 resources/make_store_graphics.py
"""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, 'resources')
STORE = os.path.join(ROOT, 'store')
RAW = os.path.join(STORE, 'screenshots', 'raw')

BLUE, BLUE_DARK, WHITE, YELLOW = (28, 93, 171), (18, 64, 124), (255, 255, 255), (255, 200, 40)
SOFT = (214, 228, 245)

SHOTS = [
    ('1_home.png', 'Видно, скільки пройдено\nі скільки залишилось'),
    ('2_question_ok.png', '1762 питання\nдля категорій B1, B'),
    ('3_question_wrong.png', 'Помилки повертаються,\nдоки їх не вивчите'),
    ('4_result.png', 'Білет на 20 питань,\nяк у сервісному центрі'),
    ('5_real_exam.png', 'Режим «Реальний іспит»:\n20 питань, 20 хвилин'),
]


def font(name, size):
    return ImageFont.truetype(os.path.join(RES, name), size)


def gradient(w, h):
    g = Image.new('L', (64, 64))
    g.putdata([int(255 * (0.35 * x / 63 + 0.65 * y / 63)) for y in range(64) for x in range(64)])
    mask = g.resize((w, h), Image.BILINEAR)
    return Image.composite(Image.new('RGB', (w, h), BLUE_DARK), Image.new('RGB', (w, h), BLUE), mask)


def dashes(d, x, y, n=3, dash=54, gap=30, th=16):
    for i in range(n):
        xs = x + i * (dash + gap)
        d.rounded_rectangle((xs, y, xs + dash, y + th), radius=th // 2, fill=YELLOW)


def phone(shot, width, radius):
    """Screenshot scaled to width with rounded corners, a thin bezel and a soft shadow; returns (image, pad)."""
    im = shot.resize((width, round(shot.height * width / shot.width)), Image.LANCZOS)
    bez = max(8, width // 60)
    w, h = im.width + 2 * bez, im.height + 2 * bez
    pad = 40
    out = Image.new('RGBA', (w + 2 * pad, h + 2 * pad), (0, 0, 0, 255))
    sh = Image.new('L', out.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 14, pad + w, pad + h + 14), radius=radius + bez, fill=110)
    out.putalpha(sh.filter(ImageFilter.GaussianBlur(22)))   # soft shadow under the phone
    body = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(body).rounded_rectangle((0, 0, w - 1, h - 1), radius=radius + bez, fill=(16, 22, 30, 255))
    m = Image.new('L', im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=radius, fill=255)
    body.paste(im, (bez, bez), m)
    out.alpha_composite(body, (pad, pad))
    return out, pad


def captioned(raw_name, caption, out_name):
    W, H = 1080, 1920
    bg = gradient(W, H).convert('RGBA')
    d = ImageDraw.Draw(bg)
    f = font('unbounded-700.ttf', 60)
    y = 110
    for line in caption.split('\n'):
        l, t, r, b = d.textbbox((0, 0), line, font=f)
        d.text(((W - (r - l)) / 2 - l, y - t), line, font=f, fill=WHITE)
        y += 84
    dashes(d, (W - (3 * 54 + 2 * 30)) // 2, y + 18)
    shot = Image.open(os.path.join(RAW, raw_name)).convert('RGB')
    ph, pad = phone(shot, 820, 44)
    top = y + 90
    bg.alpha_composite(ph, ((W - ph.width) // 2, top - pad))   # bottom of the phone runs off the canvas
    bg.convert('RGB').save(os.path.join(STORE, 'screenshots', out_name), optimize=True)


def feature_graphic():
    W, H = 1024, 500
    bg = gradient(W, H).convert('RGBA')
    d = ImageDraw.Draw(bg)
    x = 64
    d.text((x, 120), 'Теорія ПДР:', font=font('unbounded-700.ttf', 56), fill=WHITE)
    d.text((x, 190), 'тести', font=font('unbounded-700.ttf', 56), fill=WHITE)
    dashes(d, x + 2, 286, dash=46, gap=24, th=14)
    f = font('onest-500.ttf', 27)
    d.text((x, 330), 'Тренажер теоретичного іспиту', font=f, fill=SOFT)
    d.text((x, 366), 'Категорії B1, B · працює без інтернету', font=f, fill=SOFT)
    shot = Image.open(os.path.join(RAW, '2_question_ok.png')).convert('RGB')
    ph, pad = phone(shot, 300, 26)
    bg.alpha_composite(ph, (W - 300 - 70 - pad, 52 - pad))
    bg.convert('RGB').save(os.path.join(STORE, 'feature-graphic-1024x500.png'), optimize=True)


def main():
    for i, (raw, cap) in enumerate(SHOTS, 1):
        captioned(raw, cap, f'{i}.png')
    feature_graphic()
    print('store graphics written')


if __name__ == '__main__':
    main()
