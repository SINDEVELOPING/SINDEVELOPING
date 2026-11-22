"""Generates README design assets in the Burgundy #93032E / Night #151515 palette.
Text is converted to outlines so it renders identically everywhere on GitHub.

    pip install fonttools pillow
    python design/build.py          # SVG only
    python design/build.py --gifs   # SVG + recolor GIFs from design/gifs
"""
import os, re, sys
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from PIL import Image, ImageSequence

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets")

BURG, NIGHT = "#93032E", "#151515"
LINE, TEXT, MUTED, TINT = "#2A2A2A", "#ECE7E5", "#8E8988", "#D02A57"

def ntos(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s

class Font:
    def __init__(self, file, axes):
        f = instancer.instantiateVariableFont(TTFont(os.path.join(HERE, "fonts", file)), axes)
        self.gs, self.cmap = f.getGlyphSet(), f.getBestCmap()
        self.upm, self.hmtx = f["head"].unitsPerEm, f["hmtx"]
        self.cap = f["OS/2"].sCapHeight / self.upm
        self.xh = f["OS/2"].sxHeight / self.upm

    def glyph(self, ch):
        g = self.cmap.get(ord(ch))
        if g is None:
            print(f"  ! missing glyph {ch!r}", file=sys.stderr)
            g = self.cmap[ord("?")]
        return g

    def width(self, text, size, ls=0):
        if not text:
            return 0
        return sum(self.hmtx[self.glyph(c)][0] for c in text) * size / self.upm + ls * (len(text) - 1)

    def d(self, text, size, x, y, ls=0, anchor="start"):
        w = self.width(text, size, ls)
        x -= {"start": 0, "middle": w / 2, "end": w}[anchor]
        pen, k = SVGPathPen(self.gs, ntos=ntos), size / self.upm
        for c in text:
            g = self.glyph(c)
            self.gs[g].draw(TransformPen(pen, (k, 0, 0, -k, x, y)))
            x += self.hmtx[g][0] * k + ls
        return pen.getCommands()

    def wrap(self, text, size, maxw):
        lines, cur = [], ""
        for word in text.split():
            t = f"{cur} {word}".strip()
            if cur and self.width(t, size) > maxw:
                lines.append(cur)
                cur = word
            else:
                cur = t
        return lines + [cur] if cur else lines

DISPLAY = Font("Oswald.ttf", {"wght": 650})
BODY = Font("Inter.ttf", {"opsz": 14, "wght": 400})
BODY_MED = Font("Inter.ttf", {"opsz": 14, "wght": 500})
MONO = Font("JetBrainsMono.ttf", {"wght": 500})

def P(d, fill):
    return f'<path fill="{fill}" d="{d}"/>'

def svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">'
            f'<title>{title}</title>{body}</svg>')

def save(name, content):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  {name}: {len(content) // 1024} KB")

def clip(w, h, r, cid="c"):
    return f'<defs><clipPath id="{cid}"><rect width="{w}" height="{h}" rx="{r}"/></clipPath></defs>'

W = 840

# ---------- header ----------
def header():
    h, split = 420, 270
    b = clip(W, h, 20)
    b += f'<g clip-path="url(#c)"><rect width="{W}" height="{split}" fill="{BURG}"/>'
    b += f'<rect y="{split}" width="{W}" height="{h - split}" fill="{NIGHT}"/></g>'
    # corner labels, like a palette swatch
    b += P(MONO.d("SINDEVELOPING", 13, 32, 44, ls=1.5), NIGHT)
    b += P(MONO.d("#93032E", 13, W - 32, 44, ls=1.5, anchor="end"), NIGHT)
    size = 196
    base = split / 2 + DISPLAY.cap * size / 2
    b += P(DISPLAY.d("SIN", size, W / 2, base, ls=6, anchor="middle"), NIGHT)
    # bottom band
    b += P(DISPLAY.d("WEB DEVELOPER · DESIGNER", 40, W / 2, split + 72, ls=3, anchor="middle"), BURG)
    b += P(MONO.d("FIGMA  →  REACT  →  PRODUCTION", 13, W / 2, split + 112, ls=2, anchor="middle"), MUTED)
    b += P(MONO.d("#151515", 13, W - 32, h - 28, ls=1.5, anchor="end"), "#3A3A3A")
    save("header.svg", svg(W, h, b, "SIN — web developer · designer"))

# ---------- section title ----------
def section(slug, label, num):
    h = 72
    b = f'<rect width="{W}" height="{h}" rx="14" fill="{BURG}"/>'
    size = 34
    b += P(DISPLAY.d(label, size, 32, h / 2 + DISPLAY.cap * size / 2, ls=2), NIGHT)
    b += P(MONO.d(num, 14, W - 32, h / 2 + MONO.cap * 14 / 2, ls=1.5, anchor="end"), NIGHT)
    save(f"section-{slug}.svg", svg(W, h, b, label))

# ---------- about ----------
ABOUT = [
    "Веб-разработчик и дизайнер. Делаю сайты от макета до продакшена: сначала проектирую интерфейс в Figma, "
    "затем верстаю, пишу фронтенд на React и бэкенд под него. Люблю, когда страница не просто работает, "
    "а выглядит приятно и быстро загружается.",
    "Также умею делать Discord-ботов, работать в Linux и писать плагины для Minecraft — эти навыки "
    "пригодились в собственных проектах.",
]

def about():
    size, lh, pad, gap = 17, 29, 48, 18
    maxw = W - pad * 2 - 8
    paras = [BODY.wrap(p, size, maxw) for p in ABOUT]
    h = pad * 2 + sum(len(p) for p in paras) * lh + gap * (len(paras) - 1) - (lh - size)
    b = clip(W, h, 18) + f'<g clip-path="url(#c)"><rect width="{W}" height="{h}" fill="{NIGHT}"/>'
    b += f'<rect width="8" height="{h}" fill="{BURG}"/></g>'
    y = pad + size * 0.9
    for i, lines in enumerate(paras):
        for ln in lines:
            b += P(BODY.d(ln, size, pad + 8, y), TEXT if i == 0 else MUTED)
            y += lh
        y += gap
    save("about.svg", svg(W, round(h), b, " ".join(ABOUT)))

# ---------- stack ----------
STACK = [("html5", "HTML"), ("css", "CSS"), ("javascript", "JavaScript"), ("typescript", "TypeScript"),
         ("react", "React"), ("vite", "Vite"), ("figma", "Figma"), ("nodedotjs", "Node.js"),
         ("express", "Express"), ("python", "Python"), ("openjdk", "Java"), ("mysql", "MySQL"),
         ("postgresql", "PostgreSQL"), ("mongodb", "MongoDB"), ("linux", "Linux"), ("git", "Git")]

def icon_path(slug):
    raw = open(os.path.join(HERE, "icons", f"{slug}.svg"), encoding="utf-8").read()
    return re.search(r'<path d="([^"]+)"', raw).group(1)

def stack():
    cols, cw, ch = 4, W / 4, 128
    rows = len(STACK) // cols
    h = rows * ch
    b = clip(W, h, 18) + f'<g clip-path="url(#c)"><rect width="{W}" height="{h}" fill="{NIGHT}"/>'
    for i in range(1, cols):
        b += f'<rect x="{i * cw - 0.5}" width="1" height="{h}" fill="{LINE}"/>'
    for j in range(1, rows):
        b += f'<rect y="{j * ch - 0.5}" width="{W}" height="1" fill="{LINE}"/>'
    b += "</g>"
    isz = 34
    for n, (slug, label) in enumerate(STACK):
        cx, cy = (n % cols) * cw, (n // cols) * ch
        b += P(MONO.d(f"{n + 1:02}", 11, cx + 16, cy + 26, ls=1), TINT)
        k = isz / 24
        b += (f'<path fill="{TEXT}" transform="translate({cx + cw / 2 - isz / 2:.1f} {cy + 34}) scale({k:.4f})" '
              f'd="{icon_path(slug)}"/>')
        b += P(BODY_MED.d(label, 14, cx + cw / 2, cy + 102, anchor="middle"), MUTED)
    save("stack.svg", svg(W, h, b, "Стек: " + ", ".join(l for _, l in STACK)))

# ---------- project cards ----------
PROJECTS = [
    ("obhod", "ОБХОД", "Discord, YouTube и Telegram без блокировок одной кнопкой: подбор режима под провайдера, "
     "встроенный прокси для Telegram, работа в фоне.", ["Python", "CustomTkinter", "zapret", "WinDivert"]),
    ("masadora", "MASADORA", "Турнирная платформа: сайт с сеткой, матчами и командами, API и Discord-бот. "
     "VALORANT, CS2 и Dota 2.", ["React", "Vite", "Express", "PostgreSQL"]),
    ("mylinux", "MYLINUX", "Свой дистрибутив на базе Arch: live-образ, системные настройки, "
     "собственная тема Plasma.", ["archiso", "Bash", "PowerShell"]),
    ("mezu", "MEZU", "Модули Minecraft-сервера: локальный чат, спавн, банк на алмазах и клиентский мод.",
     ["Java", "Paper", "Fabric"]),
    ("mafia", "МАФИЯ", "Discord-бот для «Мафии» на двенадцать ролей с ночными действиями через кнопки.",
     ["JavaScript", "discord.js"]),
    ("server-copy", "SERVER COPY", "Переносит структуру Discord-сервера: роли, категории и каналы "
     "вместе с правами.", ["Python", "discord.py"]),
]

def card(n, slug, name, desc, tags):
    w, h, band, pad = 410, 250, 76, 26
    b = clip(w, h, 16) + f'<g clip-path="url(#c)"><rect width="{w}" height="{h}" fill="{NIGHT}"/>'
    b += f'<rect width="{w}" height="{band}" fill="{BURG}"/></g>'
    size = 30
    b += P(DISPLAY.d(name, size, pad, band / 2 + DISPLAY.cap * size / 2, ls=1.5), NIGHT)
    # arrow ↗
    ax, ay = w - pad - 16, band / 2 - 8
    b += (f'<path d="M{ax} {ay + 16}L{ax + 16} {ay}M{ax + 4} {ay}H{ax + 16}V{ay + 12}" stroke="{NIGHT}" '
          f'stroke-width="2.6" fill="none" stroke-linecap="square"/>')
    b += P(MONO.d(f"{n:02}", 11, w - pad - 28, band / 2 + MONO.cap * 11 / 2, ls=1, anchor="end"), NIGHT)
    fs, lh = 14.5, 22
    y = band + 34
    for ln in BODY.wrap(desc, fs, w - pad * 2)[:4]:
        b += P(BODY.d(ln, fs, pad, y), TEXT)
        y += lh
    x, ty, ts = pad, h - 26, 11.5
    for t in tags:
        tw = MONO.width(t, ts) + 20
        b += f'<rect x="{x + 0.5}" y="{ty - 20.5}" width="{tw:.1f}" height="27" rx="6" fill="none" stroke="{LINE}"/>'
        b += P(MONO.d(t, ts, x + 10, ty - 3), TINT)
        x += tw + 8
    save(f"project-{slug}.svg", svg(w, h, b, f"{name}: {desc}"))

# ---------- footer ----------
def footer():
    h = 64
    b = f'<rect width="{W}" height="{h}" rx="14" fill="{NIGHT}"/>'
    b += P(MONO.d("SINDEVELOPING", 13, 28, h / 2 + MONO.cap * 13 / 2, ls=2), TINT)
    x = W - 28
    for col, lab in ((NIGHT, "#151515"), (BURG, "#93032E")):
        tw = MONO.width(lab, 12, 1)
        b += P(MONO.d(lab, 12, x, h / 2 + MONO.cap * 12 / 2, ls=1, anchor="end"), MUTED)
        x -= tw + 12
        b += f'<rect x="{x - 18}" y="{h / 2 - 9}" width="18" height="18" rx="4" fill="{col}" stroke="#3A3A3A"/>'
        x -= 18 + 26
    save("footer.svg", svg(W, h, b, "SINDEVELOPING"))

# ---------- duotone gifs ----------
def hex2rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))

def lut():
    stops = [(0, hex2rgb(NIGHT)), (150, hex2rgb(BURG)), (255, hex2rgb("#F3E4E8"))]
    out = []
    for c in range(3):
        for v in range(256):
            for (a, ca), (bb, cb) in zip(stops, stops[1:]):
                if a <= v <= bb:
                    t = (v - a) / (bb - a)
                    out.append(round(ca[c] + (cb[c] - ca[c]) * t))
                    break
    return out

def duotone(src, dst, maxw):
    im = Image.open(src)
    grays, durs = [], []
    for fr in ImageSequence.Iterator(im):
        f = fr.convert("RGB")
        if f.width > maxw:
            f = f.resize((maxw, round(f.height * maxw / f.width)), Image.LANCZOS)
        grays.append(f.convert("L"))
        durs.append(fr.info.get("duration", 80))
    # one global levels stretch for the whole gif (per-frame would flicker)
    hist = [sum(g.histogram()[v] for g in grays) for v in range(256)]
    total, acc, lo, hi = sum(hist), 0, 0, 255
    for v in range(256):
        acc += hist[v]
        if acc <= total * 0.01: lo = v
        if acc <= total * 0.99: hi = v
    hi = max(hi, lo + 1)
    stretch = [min(255, max(0, round((v - lo) * 255 / (hi - lo)))) for v in range(256)]
    table, frames = lut(), []
    for g in grays:
        f = g.point(stretch).convert("RGB").point(table)
        frames.append(f.quantize(colors=64, method=Image.Quantize.MEDIANCUT))
    frames[0].save(dst, save_all=True, append_images=frames[1:], duration=durs, loop=0, optimize=True, disposal=1)
    print(f"  {os.path.basename(dst)}: {len(frames)} frames, {os.path.getsize(dst) // 1024} KB")

if __name__ == "__main__":
    header(); about(); stack(); footer()
    section("about", "ОБО МНЕ", "01 / 03")
    section("stack", "СТЕК", "02 / 03")
    section("projects", "ПРОЕКТЫ", "03 / 03")
    for i, p in enumerate(PROJECTS, 1):
        card(i, *p)
    if "--gifs" in sys.argv:
        src = os.path.join(HERE, "gifs")
        for name, mw in (("lily-field", 840), ("wistoria", 420), ("yuta", 420), ("absolute-cinema", 520)):
            duotone(os.path.join(src, f"{name}.gif"), os.path.join(OUT, f"{name}-burgundy.gif"), mw)
