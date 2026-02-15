from PIL import Image, ImageDraw

sizes = [16, 32, 48, 64, 128, 256]
imgs = []

for s in sizes:
    img = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Background rounded rect with gentle gradient (matches site palette)
    r = int(s * 0.22)
    top = (16, 27, 68, 255)     # deep blue
    bot = (52, 211, 153, 255)   # mint

    for y in range(s):
        t = y / (s - 1)
        col = (
            int(top[0] * (1 - t) + bot[0] * t),
            int(top[1] * (1 - t) + bot[1] * t),
            int(top[2] * (1 - t) + bot[2] * t),
            255,
        )
        d.line([(0, y), (s, y)], fill=col)

    # Rounded-corner alpha mask
    mask = Image.new('L', (s, s), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([0, 0, s - 1, s - 1], radius=r, fill=255)
    img.putalpha(mask)

    # Stylized "E"
    pad = int(s * 0.22)
    stroke = max(2, int(s * 0.10))
    x0 = pad
    x1 = s - pad
    y0 = pad
    y1 = s - pad

    white = (255, 255, 255, 235)
    glow = (255, 255, 255, 55)

    # subtle glow behind backbone
    d.rounded_rectangle([x0 - stroke, y0 - stroke, x0 + stroke, y1 + stroke], radius=stroke, fill=glow)

    # backbone
    d.rounded_rectangle([x0, y0, x0 + stroke, y1], radius=max(1, stroke // 2), fill=white)

    # bars
    bar_len = int((x1 - x0) * 0.85)

    def bar(y):
        d.rounded_rectangle([x0, y, x0 + bar_len, y + stroke], radius=max(1, stroke // 2), fill=white)

    bar(y0)
    bar(int((y0 + y1) / 2 - stroke / 2))
    bar(y1 - stroke)

    # tiny highlight
    d.ellipse([int(s * 0.72), int(s * 0.20), int(s * 0.80), int(s * 0.28)], fill=(255, 255, 255, 120))

    imgs.append(img)

# Write multi-size .ico
imgs[0].save('favicon.ico', format='ICO', sizes=[(s, s) for s in sizes])

# Optional preview for quick review
imgs[-1].save('favicon-preview.png')

print('wrote favicon.ico + favicon-preview.png')
