"""Ludo Group – biblioteca de layouts editoriais para Instagram.

Formatos: feed/carrossel 1080x1350 (padrão) e story/reels 1080x1920.
    set_formato("story")  # antes de gerar artes 9:16 (Stories e Reels)
    set_formato("feed")   # volta ao 4:5
Carrossel: gere cada slide com page="01/05" e swipe=True na capa (editorial).
Reels: reel([img1, img2, ...], "posts/AAAA-MM-DD-slug.mp4") monta um vídeo 9:16 com transições suaves.

Uso:
    import sys; sys.path.insert(0, "marca")
    from ludo_templates import *
    img = editorial(label="Planejamento tributário", title=["O novo imposto", "sobre *dividendos*"],
                    body="Texto curto...", foot="Ludo Law · Ludo A&T")
    img.save("posts/AAAA-MM-DD-slug.jpg", "JPEG", quality=94)

Convenção de títulos: lista de linhas; trechos entre *asteriscos* saem em itálico
na cor de destaque. Rode sempre a partir da raiz do repositório.
"""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1080, 1350
M = 96   # margem lateral
TOP = 0  # deslocamento vertical do conteúdo (story: afasta da área da interface do Instagram)
BOT = 0  # margem inferior extra do rodapé (story)

def set_formato(fmt):
    """'feed' (1080x1350, feed e carrossel) ou 'story' (1080x1920, Stories e Reels)."""
    global H, TOP, BOT
    if fmt == "story":
        H, TOP, BOT = 1920, 260, 260
    else:
        H, TOP, BOT = 1350, 0, 0
BASE = os.path.dirname(os.path.abspath(__file__))
FD = os.path.join(BASE, "fontes")

def _h(x):
    x = x.lstrip("#"); return tuple(int(x[i:i + 2], 16) for i in (0, 2, 4))

NAVY, BLUE, GRAPH = _h("00214d"), _h("5271ff"), _h("4c4c4c")
G1, G2, OFF, CARAMEL = _h("bfbfbf"), _h("d9d9d9"), _h("fffff9"), _h("a2876c")
PAPER = _h("f6f4ee")  # off-white quente para fundos editoriais

def font(kind, size):
    files = {
        "serif": "playfair-display-400-normal.ttf",
        "serif-i": "playfair-display-400-italic.ttf",
        "display": "playfair-display-400-normal.ttf",
        "display-i": "playfair-display-400-italic.ttf",
        "sans-l": "manrope-300-normal.ttf",
        "sans": "manrope-400-normal.ttf",
        "sans-m": "manrope-500-normal.ttf",
        "sans-sb": "manrope-600-normal.ttf",
        "sans-b": "manrope-700-normal.ttf",
    }
    return ImageFont.truetype(os.path.join(FD, files[kind]), size)

def _logo(name, width):
    im = Image.open(os.path.join(BASE, name)).convert("RGBA")
    im = im.crop(im.split()[3].getbbox())
    return im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)

def _tint(im, color, alpha=1.0):
    a = im.split()[3].point(lambda v: int(v * alpha))
    out = Image.new("RGBA", im.size, color + (0,)); out.putalpha(a); return out

def spaced(d, x, y, text, f, fill, track=0.28):
    """Texto em caixa alta com espaçamento entre letras. Retorna largura."""
    x0 = x
    for ch in text.upper():
        d.text((x, y), ch, font=f, fill=fill)
        x += d.textlength(ch, font=f) + f.size * track
    return x - x0

def spaced_width(d, text, f, track=0.28):
    return sum(d.textlength(c, font=f) + f.size * track for c in text.upper())

def rich_line(d, x, y, line, size, color, accent, serif=True):
    """Desenha uma linha com trechos *itálicos* em cor de destaque."""
    parts = line.split("*")
    for i, p in enumerate(parts):
        if not p: continue
        it = i % 2 == 1
        f = font(("serif-i" if it else "serif") if serif else ("display-i" if it else "display"), size)
        d.text((x, y), p, font=f, fill=accent if it else color)
        x += d.textlength(p, font=f)
    return x

def wrap(d, text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def _footer(img, d, dark, foot, page=None, swipe=False):
    col = G2 if dark else GRAPH
    H = img.height - BOT
    rule = (255, 255, 255, 60) if dark else (0, 33, 77, 50)
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    od.line([M, H - 150, W - M, H - 150], fill=rule, width=1)
    img.alpha_composite(ov)
    logo = _logo("logo-branco-transparente.png" if dark else "logo-cinza-transparente.png", 150)
    if not dark: logo = _tint(logo, NAVY)
    img.alpha_composite(logo, (M, H - 112))
    f = font("sans-m", 17)
    txt = foot or "ludogroup.com.br"
    wdt = spaced_width(d, txt, f, 0.22)
    spaced(d, W - M - wdt, H - 96, txt, f, col, 0.22)
    if page:
        spaced(d, M, H - 190, page, f, col, 0.22)
    if swipe:
        fs = font("sans-m", 17); t = "DESLIZE"
        ax = W - M; ay = H - 186
        d.line([ax - 44, ay, ax, ay], fill=col, width=2)
        d.line([ax - 10, ay - 7, ax, ay], fill=col, width=2); d.line([ax - 10, ay + 7, ax, ay], fill=col, width=2)
        spaced(d, ax - 60 - spaced_width(d, t, fs, 0.22), ay - 12, t, fs, col, 0.22)

def _gradient(c1, c2, c3=None):
    g = Image.new("RGB", (W, H)); px = g.load()
    for y in range(H):
        for x in range(0, W, 2):
            t = x / W * 0.35 + y / H * 0.65
            if c3 and t > 0.55:
                u = (t - 0.55) / 0.45; a, b = c2, c3
            else:
                u = t / (0.55 if c3 else 1); a, b = c1, c2
            c = tuple(int(a[i] + (b[i] - a[i]) * min(u, 1)) for i in range(3))
            px[x, y] = c
            if x + 1 < W: px[x + 1, y] = c
    return g.convert("RGBA")

# ---------------------------------------------------------------- LAYOUTS

def editorial(label, title, body=None, foot=None, dark=False, page=None, title_size=84, swipe=False):
    """Capa editorial: selo em caixa alta, título serifado grande, corpo curto.
    dark=False -> papel off-white com texto marinho; dark=True -> marinho profundo."""
    bg = NAVY if dark else PAPER
    img = Image.new("RGBA", (W, H), bg + (255,)); d = ImageDraw.Draw(img)
    ink, soft, acc = (OFF, G2, _h("8fa5ff")) if dark else (NAVY, GRAPH, BLUE)
    sym = _tint(_logo("simbolo-branco.png", 520), OFF if dark else NAVY, 0.06 if dark else 0.05)
    img.alpha_composite(sym, (W - 380, 120 + TOP))
    d.line([M, 150 + TOP, M + 56, 150 + TOP], fill=CARAMEL, width=2)
    spaced(d, M, 170 + TOP, label, font("sans-sb", 20), soft)
    y = 300 + TOP
    for line in title:
        rich_line(d, M - 4, y, line, title_size, ink, acc); y += int(title_size * 1.18)
    if body:
        y += 40
        fb = font("sans-l", 32)
        for l in wrap(d, body, fb, W - 2 * M - 120):
            d.text((M, y), l, font=fb, fill=soft); y += 48
    _footer(img, d, dark, foot, page, swipe)
    return img.convert("RGB")

def manifesto(quote, author=None, label=None, foot=None, page=None):
    """Frase de impacto centralizada sobre degradê da marca, símbolo em marca d'água."""
    img = _gradient(BLUE, NAVY, (6, 12, 30)); d = ImageDraw.Draw(img)
    sym = _tint(_logo("simbolo-branco.png", 760), OFF, 0.07)
    img.alpha_composite(sym, ((W - sym.width) // 2, 230 + TOP))
    if label:
        f = font("sans-sb", 19); wdt = spaced_width(d, label, f)
        spaced(d, (W - wdt) / 2, 200 + TOP, label, f, G2)
    size = 70; y = 500 + TOP
    for line in quote:
        plain = line.replace("*", "")
        f = font("serif", size)
        x = (W - d.textlength(plain, font=f)) / 2
        rich_line(d, x, y, line, size, OFF, _h("aab8ff")); y += int(size * 1.25)
    if author:
        f = font("sans-m", 20); y += 30; wdt = spaced_width(d, author, f)
        spaced(d, (W - wdt) / 2, y, author, f, G2)
    _footer(img, d, True, foot, page)
    return img.convert("RGB")

def pontos(label, title, items, foot=None, dark=False, title_size=64, page=None):
    """Título + 2 a 4 pontos numerados em estilo editorial (01, 02, 03)."""
    bg = NAVY if dark else PAPER
    img = Image.new("RGBA", (W, H), bg + (255,)); d = ImageDraw.Draw(img)
    ink, soft, acc = (OFF, G2, _h("8fa5ff")) if dark else (NAVY, GRAPH, BLUE)
    rule = (255, 255, 255, 50) if dark else (0, 33, 77, 40)
    d.line([M, 150 + TOP, M + 56, 150 + TOP], fill=CARAMEL, width=2)
    spaced(d, M, 170 + TOP, label, font("sans-sb", 20), soft)
    y = 260 + TOP
    for line in title:
        rich_line(d, M - 3, y, line, title_size, ink, acc); y += int(title_size * 1.2)
    y += 50
    fn, ft, fb = font("serif-i", 44), font("sans-sb", 30), font("sans-l", 26)
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for i, (t, b) in enumerate(items, 1):
        od.line([M, y, W - M, y], fill=rule, width=1)
        y += 28
        d.text((M, y - 10), f"{i:02d}", font=fn, fill=CARAMEL)
        d.text((M + 120, y), t, font=ft, fill=ink)
        yy = y + 46
        for l in wrap(d, b, fb, W - 2 * M - 120):
            d.text((M + 120, yy), l, font=fb, fill=soft); yy += 38
        y = yy + 28
    img.alpha_composite(ov)
    _footer(img, d, dark, foot, page)
    return img.convert("RGB")

def numero(label, big, caption, body=None, foot=None, page=None):
    """Número/dado em destaque monumental (ex.: 'R$ 50 mil', '10%')."""
    img = Image.new("RGBA", (W, H), NAVY + (255,)); d = ImageDraw.Draw(img)
    d.line([M, 150 + TOP, M + 56, 150 + TOP], fill=CARAMEL, width=2)
    spaced(d, M, 170 + TOP, label, font("sans-sb", 20), G2)
    fbig = font("display", 250)
    d.text((M - 10, 300 + TOP), big, font=fbig, fill=OFF)
    y = 700 + TOP
    for l in caption:
        rich_line(d, M, y, l, 50, OFF, _h("8fa5ff")); y += 64
    if body:
        y += 30; fb = font("sans-l", 30)
        for l in wrap(d, body, fb, W - 2 * M - 80):
            d.text((M, y), l, font=fb, fill=G2); y += 44
    _footer(img, d, True, foot, page)
    return img.convert("RGB")


def reel(frames, out, secs=3.6, fade=0.7):
    """Monta um Reel/Story em vídeo (1080x1920, H.264 + AAC silencioso, 30 fps) a partir de
    uma lista de imagens PIL 1080x1920, com leve zoom e transições suaves. Duração: ~secs por quadro."""
    import subprocess, tempfile
    tmp = tempfile.mkdtemp()
    paths = []
    for i, im in enumerate(frames):
        p = os.path.join(tmp, f"f{i}.png"); im.save(p); paths.append(p)
    inputs, filters = [], []
    for i, p in enumerate(paths):
        inputs += ["-loop", "1", "-t", str(secs), "-i", p]
        filters.append(f"[{i}:v]scale=1188:2112,zoompan=z='min(zoom+0.0006,1.06)':d={int(secs*30)}:"
                       f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30,setsar=1,format=yuv420p[v{i}]")
    last = "v0"; off = secs - fade
    for i in range(1, len(paths)):
        filters.append(f"[{last}][v{i}]xfade=transition=fade:duration={fade}:offset={off:.2f}[x{i}]")
        last = f"x{i}"; off += secs - fade
    total = secs * len(paths) - fade * (len(paths) - 1)
    cmd = ["ffmpeg", "-y", *inputs, "-f", "lavfi", "-t", f"{total:.2f}", "-i", "anullsrc=r=44100:cl=stereo",
           "-filter_complex", ";".join(filters), "-map", f"[{last}]", "-map", f"{len(paths)}:a",
           "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", "30", "-b:v", "4M",
           "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out
