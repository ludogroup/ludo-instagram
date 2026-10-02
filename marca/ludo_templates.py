"""Ludo Group – biblioteca de layouts editoriais para Instagram.

Formatos: feed/carrossel 1080x1350 (padrão) e story/reels 1080x1920.
    set_formato("story")  # antes de gerar artes 9:16 (Stories e Reels)
    set_formato("feed")   # volta ao 4:5
Carrossel: gere cada slide com page="01/05" e swipe=True na capa (editorial).
Reels: reel([img1, img2, ...], "posts/AAAA-MM-DD-slug.mp4") monta um vídeo 9:16 com transições suaves.

Layouts: editorial, pontos, numero, manifesto, grafico (dados oficiais em barras/linha),
foto (foto real de pessoas/eventos da pasta fotos/, com véu marinho e título).
Vídeo real: reel_de_video("fotos/<video>.mp4", "posts/AAAA-MM-DD-slug.mp4", title=[...]).

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


def fmt_valor(v, unidade="", casas=None):
    """Número no padrão brasileiro com unidade: fmt_valor(13.75, '%') -> '13,75%'; 'R$' vai antes."""
    s = f"{v:,.{2 if casas is None else casas}f}"
    if casas is None and "." in s:
        s = s.rstrip("0").rstrip(".")          # 13.75 -> 13,75 · 14.50 -> 14,5 · 15.00 -> 15
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    if unidade.startswith("R$"):
        return f"{unidade} {s}"
    return s + unidade


def _veu(alpha_topo=0.0, inicio=0.38, alpha_base=0.93, cor=None):
    """Véu marinho vertical (transparente em cima, denso na base) para textos sobre fotos."""
    cor = cor or NAVY
    col = Image.new("L", (1, H))
    for y in range(H):
        t = y / H
        if t < inicio:
            a = alpha_topo * (1 - t / inicio)
        else:
            u = (t - inicio) / (1 - inicio)
            a = alpha_base * (u ** 1.35)
        col.putpixel((0, y), int(255 * max(0.0, min(1.0, a))))
    mask = col.resize((W, H))
    veu = Image.new("RGBA", (W, H), cor + (0,))
    veu.putalpha(mask)
    return veu


def _bloco_inferior(img, d, label, title, body, title_size=72):
    """Selo + título + corpo, alinhados à esquerda e apoiados acima do rodapé."""
    fb = font("sans-l", 30)
    corpo = wrap(d, body, fb, W - 2 * M - 60) if body else []
    altura = (60 if label else 0) + len(title) * int(title_size * 1.18) + (30 + 44 * len(corpo) if corpo else 0)
    y = img.height - BOT - 220 - altura
    if label:
        d.line([M, y, M + 56, y], fill=CARAMEL, width=2)
        spaced(d, M, y + 18, label, font("sans-sb", 20), G2)
        y += 60
    for line in title:
        rich_line(d, M - 4, y, line, title_size, OFF, _h("aab8ff"))
        y += int(title_size * 1.18)
    if corpo:
        y += 30
        for l in corpo:
            d.text((M, y), l, font=fb, fill=G2)
            y += 44


def foto(path, title, label=None, body=None, foot=None, page=None, focus=(0.5, 0.4), swipe=False,
         title_size=72):
    """Foto real em tela cheia (pessoas, eventos, bastidores) com véu marinho, título e logo.
    path: arquivo em fotos/. focus=(x, y), de 0 a 1: ponto da foto que fica no centro do recorte
    (use a posição dos rostos). Funciona em feed (1080x1350) e story/reels (1080x1920)."""
    from PIL import ImageOps
    src = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    esc = max(W / src.width, H / src.height)
    nw, nh = int(src.width * esc + 0.5), int(src.height * esc + 0.5)
    src = src.resize((nw, nh), Image.LANCZOS)
    left = int(min(max(focus[0] * nw - W / 2, 0), nw - W))
    top = int(min(max(focus[1] * nh - H / 2, 0), nh - H))
    img = src.crop((left, top, left + W, top + H)).convert("RGBA")
    img.alpha_composite(_veu(alpha_topo=0.35, inicio=0.30 if H > 1400 else 0.36))
    d = ImageDraw.Draw(img)
    _bloco_inferior(img, d, label, title, body, title_size)
    _footer(img, d, True, foot, page, swipe)
    return img.convert("RGB")


def grafico(label, title, dados, unidade="", fonte=None, foot=None, dark=False, page=None,
            tipo="barras", destaque=None, title_size=60, casas=None):
    """Gráfico editorial com dados oficiais (sempre cite a fonte).
    dados: [(rótulo, valor), ...] com até 12 pontos. tipo='barras' (comparação) ou 'linha' (evolução).
    destaque: índice ou lista de índices realçados em azul (padrão: o último)."""
    bg = NAVY if dark else PAPER
    img = Image.new("RGBA", (W, H), bg + (255,)); d = ImageDraw.Draw(img)
    ink, soft, acc = (OFF, G2, _h("8fa5ff")) if dark else (NAVY, GRAPH, BLUE)
    d.line([M, 150 + TOP, M + 56, 150 + TOP], fill=CARAMEL, width=2)
    spaced(d, M, 170 + TOP, label, font("sans-sb", 20), soft)
    y = 260 + TOP
    for line in title:
        rich_line(d, M - 3, y, line, title_size, ink, acc); y += int(title_size * 1.2)
    n = len(dados)
    if destaque is None:
        destaque = [n - 1]
    elif isinstance(destaque, int):
        destaque = [destaque]
    destaque = {i % n for i in destaque}
    vals = [v for _, v in dados]
    y0, y1 = y + 110, H - BOT - 330          # área do gráfico (deixa espaço para fonte e paginação)
    x0, x1 = M, W - M
    fv, fr = font("sans-sb", 28), font("sans-m", 21)
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    regua = (255, 255, 255, 70) if dark else (0, 33, 77, 60)
    neutro = (255, 255, 255, 70) if dark else G1 + (255,)
    realce = _h("8fa5ff") if dark else BLUE
    if tipo == "barras":
        lo, hi = min(0.0, min(vals)), max(0.0, max(vals))
        span = (hi - lo) or 1.0
        passo = (x1 - x0) / n
        larg = passo * 0.62
        zero = y1 - (0 - lo) / span * (y1 - y0) * 0.86
        for i, (rot, v) in enumerate(dados):
            cx = x0 + passo * (i + 0.5)
            topo = zero - v / span * (y1 - y0) * 0.86
            cor = realce + (255,) if i in destaque else neutro
            od.rectangle([cx - larg / 2, min(topo, zero), cx + larg / 2, max(topo, zero)], fill=cor)
            txt = fmt_valor(v, unidade, casas)
            ty = (topo - 44) if v >= 0 else (topo + 12)
            d.text((cx - d.textlength(txt, font=fv) / 2, ty), txt, font=fv,
                   fill=(realce if i in destaque else ink))
            d.text((cx - d.textlength(rot, font=fr) / 2, y1 + 22), rot, font=fr, fill=soft)
        od.line([x0, zero, x1, zero], fill=regua, width=2)
    else:
        lo, hi = min(vals), max(vals)
        pad = (hi - lo) * 0.18 or abs(hi) * 0.1 or 1.0
        lo, hi = lo - pad, hi + pad
        passo = (x1 - x0 - 60) / max(n - 1, 1)
        pts = [(x0 + 30 + passo * i, y1 - (v - lo) / (hi - lo) * (y1 - y0)) for i, v in enumerate(vals)]
        for k in range(4):                    # grade discreta
            gy = y0 + (y1 - y0) * k / 3
            od.line([x0, gy, x1, gy], fill=regua[:3] + (30,), width=1)
        od.line(pts, fill=(ink + (255,)), width=5, joint="curve")
        cada = max(1, round(n / 6))
        for i, ((px, py), (rot, v)) in enumerate(zip(pts, dados)):
            r = 11 if i in destaque else 6
            od.ellipse([px - r, py - r, px + r, py + r], fill=(realce if i in destaque else ink) + (255,))
            if i in destaque or i == 0:
                txt = fmt_valor(v, unidade, casas)
                tw = d.textlength(txt, font=fv)
                viz = pts[i - 1] if i > 0 else (pts[i + 1] if n > 1 else (px, py))
                abaixo = viz[1] < py - 4            # linha chega de cima: rótulo vai abaixo do ponto
                if i == n - 1 and n > 1:            # último ponto: rótulo à esquerda, longe da borda
                    tx = px - tw - 22
                else:
                    tx = min(max(px - tw / 2, x0), x1 - tw)
                ty = py + 20 if abaixo else py - 58
                d.text((tx, ty), txt, font=fv, fill=(realce if i in destaque else ink))
            if i % cada == 0 or i == n - 1:
                d.text((px - d.textlength(rot, font=fr) / 2, y1 + 22), rot, font=fr, fill=soft)
    img.alpha_composite(ov)
    d = ImageDraw.Draw(img)
    if fonte:
        d.text((M, y1 + 76), f"Fonte: {fonte}", font=font("sans", 20), fill=soft)
    _footer(img, d, dark, foot, page)
    return img.convert("RGB")


def reel_de_video(entrada, saida, title=None, label=None, foot=None, inicio=0.0, duracao=None,
                  focus_x=0.5, title_size=68):
    """Reel a partir de vídeo real (pessoas, eventos, bastidores) da pasta fotos/: recorta para
    1080x1920, mantém o áudio original (ou silêncio) e sobrepõe véu marinho, título e logo.
    duracao em segundos (recomendado 8 a 60). Requer ffmpeg/ffprobe."""
    import subprocess, tempfile, json as _json
    global H, TOP, BOT
    antigo = (H, TOP, BOT)
    set_formato("story")
    try:
        cam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cam.alpha_composite(_veu(alpha_topo=0.30, inicio=0.30))
        d = ImageDraw.Draw(cam)
        if title:
            _bloco_inferior(cam, d, label, title, None, title_size)
        _footer(cam, d, True, foot)
        tmp = tempfile.mkdtemp()
        png = os.path.join(tmp, "overlay.png"); cam.save(png)
    finally:
        H, TOP, BOT = antigo
    info = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-of", "json", entrada],
                          capture_output=True, text=True, check=True)
    tem_audio = any(s.get("codec_type") == "audio" for s in _json.loads(info.stdout).get("streams", []))
    corte = ["-ss", str(inicio)] + (["-t", str(duracao)] if duracao else [])
    cmd = ["ffmpeg", "-y", *corte, "-i", entrada, "-loop", "1", "-i", png]
    if not tem_audio:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
    filtro = (f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
              f"crop=1080:1920:(in_w-1080)*{focus_x}:(in_h-1920)/2,fps=30,setsar=1[v];"
              f"[v][1:v]overlay=0:0:shortest=1,format=yuv420p[out]")
    cmd += ["-filter_complex", filtro, "-map", "[out]", "-map", "0:a" if tem_audio else "2:a",
            "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", "30", "-b:v", "5M",
            "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-shortest", "-movflags", "+faststart", saida]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return saida


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
