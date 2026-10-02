#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LIAM – fotos e vídeos da equipe (pasta do Google Drive "Fotos e Vídeos Luis - LIAM").

Fluxo (rotina "LIAM – Mídias da equipe"):
  Fotos  : originais vão para a nuvem (staging) -> `foto` (JPEG limpo, rostos, nitidez, duplicadas) -> revisão
           visual (`folha`) -> fotos/ no GitHub + 🎞️ Banco de mídia.
  Vídeos : o original fica no Mac. No Mac: `audio` (Opus leve) -> nuvem: `transcrever` (Whisper) -> escolha dos
           melhores trechos -> no Mac: `trecho` (+ `juntar`) e `corte` (Reels pronto, legendado) -> o corte vai
           para a nuvem -> fotos/cortes/ no GitHub + Banco de mídia.

Comandos que rodam no Mac (shell do Cowork: python3 + ffmpeg; cada chamada tem no máximo ~180 s):
  listar <pasta>                       inventário + textos de contexto (.txt/.md) da equipe por pasta
                                       (ignora pastas "_LIAM..." e arquivos ocultos)
  audio <video> <saida.opus> [--de S --ate S]
                                       áudio para transcrever (Opus 24 kbps mono: ~11 MB por hora)
  trecho <video> <ini_s> <fim_s> <saida.mp4> [--altura-max 1440] [--preset veryfast]
                                       recorte em alta qualidade, HDR do iPhone convertido para SDR.
                                       Até ~40 s por chamada; partes maiores: vários trechos + `juntar`.
  juntar <partes...> <saida.mp4>       une partes sem recodificar
  corte <trecho.mp4> <saida.mp4> --legendas segs.json --titulo "Linha|com *destaque*" [--rotulo X]
        [--rodape X] [--modo auto|recorte|moldura] [--preset fast] [--mosaico]
                                       Reels 1080x1920 pronto: recorte vertical que acompanha o rosto (ou
                                       moldura com fundo desfocado), legendas Ludo, título nos primeiros 4 s,
                                       rodapé com logo, áudio a -14 LUFS, arquivo <= 18 MB e capa JPEG.
Comandos que rodam na nuvem (pip install pillow pillow-heif sherpa-onnx numpy opencv-python-headless):
  foto <arquivos...> --saida DIR [--prefixo AAAA-MM-DD-slug]
                                       JPEG limpo (sem EXIF/GPS, lado maior 2160), foco sugerido, nitidez,
                                       data da foto e aviso de fotos quase iguais
  folha <imagens...> --saida folha.jpg  folhas de contato numeradas (20 por folha) para revisar rápido
  transcrever <audio> <saida.json> [--modelo base|small] [--frases] [--de S --ate S] [--desloca S]
                                       Whisper (sherpa-onnx) + detector de voz -> JSON e .txt com tempos.
                                       Vídeo inteiro: --modelo base. Legenda de um corte: --modelo small --frases.
`corte`, `trecho` e `juntar` também rodam na nuvem. Preparar o Mac: liam/preparar_mac.sh.
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
import urllib.request
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FONTES = RAIZ / "marca" / "fontes"
MODELOS = Path(os.environ.get("LIAM_MODELOS", Path.home() / ".cache" / "liam-modelos"))
URL_MODELOS = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models"
YUNET = ("https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/"
         "face_detection_yunet_2023mar.onnx")
EXT_FOTO = {".heic", ".heif", ".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}
EXT_VIDEO = {".mp4", ".mov", ".m4v", ".mkv", ".avi", ".mts", ".m2ts", ".webm", ".3gp"}
SR = 16000


# =========================================================================== utilidades
def rodar(cmd, **kw):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise SystemExit(f"Falhou: {' '.join(map(str, cmd))[:400]}\n{r.stderr[-2000:]}")
    return r.stdout


def par(x):
    return max(2, int(round(x / 2)) * 2)


def achar(caminho):
    """Pastas vindas do Mac usam acentos decompostos (NFD), e 'Vídeos' digitado (NFC) não é encontrado.
    Resolve parte a parte, comparando nomes normalizados; erro claro se nada existir."""
    if not str(caminho).strip():
        raise SystemExit("Caminho vazio")
    c = Path(caminho)
    if c.exists():
        return str(c)
    atual = Path(c.anchor or ".")
    for parte in (c.parts[1:] if c.anchor else c.parts):
        candidato = atual / parte
        if not candidato.exists() and atual.is_dir():
            alvo = unicodedata.normalize("NFC", parte)
            candidato = next((atual / n for n in os.listdir(atual) if unicodedata.normalize("NFC", n) == alvo),
                             candidato)
        atual = candidato
    if atual.exists():
        return str(atual)
    raise SystemExit(f"Não encontrado: {caminho}")


def sondar(video):
    info = json.loads(rodar(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", video]))
    v = next((s for s in info["streams"] if s.get("codec_type") == "video"), {})
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(float(sd["rotation"]))
    rot = int(float(v.get("tags", {}).get("rotate", rot) or 0))
    w, h = int(v.get("width", 0)), int(v.get("height", 0))
    if abs(rot) % 180 == 90:
        w, h = h, w
    try:
        num, den = (v.get("avg_frame_rate") or "0/1").split("/")
        fps = float(num) / float(den) if float(den) else 0.0
    except ValueError:
        fps = 0.0
    trc = v.get("color_transfer") or ""
    return {"largura": w, "altura": h, "duracao": float(info["format"].get("duration", 0) or 0), "fps": round(fps, 2),
            "codec": v.get("codec_name"), "tem_audio": any(s.get("codec_type") == "audio" for s in info["streams"]),
            "hdr": trc in ("arib-std-b67", "smpte2084"), "transfer": trc,
            "primarias": v.get("color_primaries") or "", "matriz": v.get("color_space") or ""}


def _dims_trabalho(W, H, altura_max=1440):
    """Horizontal: altura até altura_max. Vertical: largura até 1080 (o Reels final é 1080x1920)."""
    if W >= H:
        h2 = min(H, altura_max)
        return par(W * h2 / H), par(h2)
    w2 = min(W, 1080)
    return par(w2), par(H * w2 / W)


def _pre_video(info, w2, h2):
    """Filtro inicial: redimensiona e, se o vídeo for HDR (HLG/PQ do iPhone), converte para SDR Rec.709."""
    if info["hdr"]:
        return (f"zscale=w={w2}:h={h2}:tin={info['transfer']}:min={info['matriz'] or 'bt2020nc'}:"
                f"pin={info['primarias'] or 'bt2020'}:rin=tv:t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,"
                f"tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
    if (w2, h2) == (info["largura"], info["altura"]):
        return "format=yuv420p"
    return f"scale={w2}:{h2}:flags=lanczos,format=yuv420p"


def _data_do_nome(nome):
    """'260926_Palestra...' / '2026-09-26 Evento' / '20260926-x' -> '2026-09-26' (ou None)."""
    m = re.match(r"\s*(20\d{2})[-_.]?(\d{2})[-_.]?(\d{2})(?!\d)", nome) or re.match(r"\s*(\d{2})(\d{2})(\d{2})(?!\d)", nome)
    if not m:
        return None
    a, mes, d = m.groups()
    a = int(a) + (2000 if len(a) == 2 else 0)
    try:
        return datetime(a, int(mes), int(d)).strftime("%Y-%m-%d")
    except ValueError:
        return None


def _baixar(url, destino):
    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_name(destino.name + ".parcial")
    with urllib.request.urlopen(url, timeout=60) as r, open(tmp, "wb") as f:
        while True:
            bloco = r.read(1 << 20)
            if not bloco:
                break
            f.write(bloco)
    tmp.rename(destino)


# =========================================================================== inventário (Mac)
def cmd_listar(a):
    raiz = Path(achar(a.pasta))
    itens, contextos = [], {}
    for p in sorted(raiz.rglob("*")):
        rel = p.relative_to(raiz)
        if not p.is_file() or any(x.startswith((".", "_LIAM")) for x in rel.parts):
            continue
        ext = p.suffix.lower()
        if ext in (".txt", ".md"):                 # contexto escrito pela equipe (quem aparece, o que foi o evento)
            try:
                texto = p.read_text(encoding="utf-8", errors="replace").strip()
            except OSError:
                texto = ""
            if texto:
                contextos[unicodedata.normalize("NFC", str(rel))] = texto[:3000]
            continue
        tipo = "foto" if ext in EXT_FOTO else "video" if ext in EXT_VIDEO else None
        if not tipo:
            continue
        st = p.stat()
        pasta = unicodedata.normalize("NFC", rel.parts[0]) if len(rel.parts) > 1 else ""
        item = {"arquivo": unicodedata.normalize("NFC", str(rel)), "caminho": str(p), "tipo": tipo,
                "mb": round(st.st_size / 1e6, 1), "pasta": pasta, "data_pasta": _data_do_nome(pasta) if pasta else None,
                "modificado": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="minutes")}
        if tipo == "video" and not a.sem_sondar:
            try:
                i = sondar(p)
                item.update(duracao_s=round(i["duracao"], 1), resolucao=f"{i['largura']}x{i['altura']}", hdr=i["hdr"],
                            audio=i["tem_audio"])
            except SystemExit:
                item["erro"] = "não abriu (arquivo só na nuvem ou corrompido?)"
        itens.append(item)
    print(json.dumps({"arquivos": itens, "contextos": contextos}, ensure_ascii=False, indent=1))


# =========================================================================== áudio, trechos (Mac)
def cmd_audio(a):
    a.video = achar(a.video)
    entrada = ["ffmpeg", "-y", "-v", "error"] + (["-ss", f"{float(a.de):.3f}"] if a.de else []) + ["-i", a.video]
    if a.ate:
        entrada += ["-t", f"{float(a.ate) - float(a.de or 0):.3f}"]
    saida = Path(a.saida)
    ext = saida.suffix.lower()
    if ext == ".flac":
        codec = ["-c:a", "flac"]
    elif ext in (".opus", ".ogg"):
        codec = ["-c:a", "libopus", "-b:a", "24k", "-application", "voip"]
    else:
        codec = ["-c:a", "aac", "-b:a", "48k"]
    r = subprocess.run([str(c) for c in entrada + ["-vn", "-ac", "1", "-ar", str(SR), *codec, saida]],
                       capture_output=True, text=True)
    if r.returncode != 0 and ext in (".opus", ".ogg"):            # ffmpeg sem libopus: usa AAC
        saida = saida.with_suffix(".m4a")
        rodar(entrada + ["-vn", "-ac", "1", "-ar", str(SR), "-c:a", "aac", "-b:a", "48k", saida])
    elif r.returncode != 0:
        raise SystemExit(r.stderr[-2000:])
    print(json.dumps({"audio": str(saida), "mb": round(saida.stat().st_size / 1e6, 1),
                      "de": float(a.de or 0), "ate": float(a.ate) if a.ate else None}))


def cmd_trecho(a):
    a.video = achar(a.video)
    ini, fim = float(a.inicio), float(a.fim)
    info = sondar(a.video)
    w2, h2 = _dims_trabalho(info["largura"], info["altura"], a.altura_max)
    rodar(["ffmpeg", "-y", "-v", "error", "-ss", f"{ini:.3f}", "-i", a.video, "-t", f"{fim - ini:.3f}",
           "-map", "0:v:0", "-map", "0:a:0?", "-vf", _pre_video(info, w2, h2), "-c:v", "libx264",
           "-preset", a.preset, "-crf", "19", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", a.saida])
    print(json.dumps({"trecho": a.saida, "de": ini, "ate": fim, "resolucao": f"{w2}x{h2}", "hdr_convertido": info["hdr"],
                      "mb": round(Path(a.saida).stat().st_size / 1e6, 1)}))


def cmd_juntar(a):
    partes = [achar(p) for p in a.partes]
    lista = Path(tempfile.mkdtemp()) / "lista.txt"
    lista.write_text("".join("file '" + str(Path(p).resolve()).replace("'", "'\\''") + "'\n" for p in partes),
                     encoding="utf-8")
    rodar(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lista, "-c", "copy",
           "-movflags", "+faststart", a.saida])
    print(json.dumps({"saida": a.saida, "duracao_s": round(sondar(a.saida)["duracao"], 1)}))


# =========================================================================== rostos
def _detector():
    """Detector de rostos: YuNet (preciso, pega perfil; 230 KB) ou Haar como reserva.
    Devolve função bgr -> [(x, y, w, h, confiança)]."""
    import cv2
    m = MODELOS / "face_detection_yunet_2023mar.onnx"
    if not m.exists():
        try:
            _baixar(YUNET, m)
        except Exception as e:                                   # sem rede: segue com Haar
            print(f"[aviso] YuNet indisponível ({e}); usando Haar", file=sys.stderr)
    if m.exists() and m.stat().st_size > 100_000 and hasattr(cv2, "FaceDetectorYN"):
        det = cv2.FaceDetectorYN.create(str(m), "", (320, 320), score_threshold=0.6)

        def detectar(bgr):
            det.setInputSize((bgr.shape[1], bgr.shape[0]))
            _, f = det.detect(bgr)
            return [] if f is None else [tuple(float(v) for v in (*r[:4], r[-1])) for r in f]
        return detectar
    haar = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    def detectar(bgr):
        g = cv2.equalizeHist(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY))
        return [(float(x), float(y), float(w), float(h), 0.5)
                for x, y, w, h in haar.detectMultiScale(g, 1.1, 6, minSize=(24, 24))]
    return detectar


def _principal(rostos):
    return max(rostos, key=lambda r: r[2] * r[3] * r[4])


# =========================================================================== fotos (nuvem)
def _heif():
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError:
        pass


def _dhash(im):
    g = list(im.convert("L").resize((9, 8)).tobytes())
    v = 0
    for r in range(8):
        for c in range(8):
            v = (v << 1) | (g[r * 9 + c] > g[r * 9 + c + 1])
    return v


def _data_exif(im):
    try:
        ex = im.getexif()
        bruto = ex.get_ifd(0x8769).get(36867) or ex.get(306)
        return datetime.strptime(str(bruto).strip(), "%Y:%m:%d %H:%M:%S").isoformat(timespec="minutes")
    except Exception:
        return None


def cmd_foto(a):
    from PIL import Image, ImageOps
    import numpy as np
    _heif()
    saida = Path(a.saida)
    saida.mkdir(parents=True, exist_ok=True)
    res, hashes, detectar = [], [], None
    for i, arq in enumerate(a.arquivos, 1):
        arq = achar(arq)
        bruta = Image.open(arq)
        data = _data_exif(bruta)
        im = ImageOps.exif_transpose(bruta).convert("RGB")
        w, h = im.size
        esc = min(1.0, 2160 / max(w, h))
        if esc < 1:
            im = im.resize((round(w * esc), round(h * esc)), Image.LANCZOS)
        if a.prefixo:
            nome = f"{a.prefixo}-{i}" if len(a.arquivos) > 1 else a.prefixo
        else:
            nome = re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFKD", Path(arq).stem)
                          .encode("ascii", "ignore").decode().lower()).strip("-")
        destino = saida / f"{nome}.jpg"
        im.save(destino, "JPEG", quality=90, optimize=True)        # sem EXIF: remove GPS e dados do aparelho
        ow, oh = im.size
        item = {"n": i, "origem": str(arq), "arquivo": str(destino), "largura": ow, "altura": oh,
                "orientacao": "Vertical" if oh > ow * 1.05 else "Horizontal" if ow > oh * 1.05 else "Quadrada",
                "kb": destino.stat().st_size // 1024, "data_foto": data}
        hs = _dhash(im)
        parecida = next((n for n, x in hashes if bin(hs ^ x).count("1") <= 6), None)
        if parecida:
            item["parecida_com"] = parecida                       # rajada/foto quase igual: escolha a melhor
        hashes.append((i, hs))
        try:
            import cv2
            if detectar is None:
                detectar = _detector()
            peq = im.resize((1080, round(oh * 1080 / ow))) if ow > 1080 else im
            rgb = np.asarray(peq)
            item["nitidez"] = round(float(cv2.Laplacian(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY), cv2.CV_64F).var()), 1)
            r = detectar(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
            item["rostos"] = len(r)
            if r:
                x, y, fw, fh, _ = _principal(r)
                cx, cy = (x + fw / 2) / rgb.shape[1], (y + fh / 2) / rgb.shape[0]
                item["rosto"] = [round(cx, 2), round(cy, 2)]
                item["foco"] = [round(cx, 2), round(min(0.7, cy + 0.12), 2)]     # rosto no terço superior
            else:
                item["foco"] = [0.5, 0.4]
            if item["nitidez"] < 40:
                item["alerta"] = "possivelmente desfocada"
        except ImportError:
            pass
        res.append(item)
    print(json.dumps(res, ensure_ascii=False, indent=1))


def cmd_folha(a):
    """Folhas de contato numeradas (5x4) para revisar muitas imagens de uma vez."""
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    _heif()
    arquivos = [achar(x) for x in a.arquivos]
    try:
        fonte = ImageFont.truetype(str(FONTES / "manrope-700-normal.ttf"), 30)
    except OSError:
        fonte = ImageFont.load_default()
    cel, cols, linhas = 360, 5, 4
    saidas = []
    for pag in range(0, len(arquivos), cols * linhas):
        folha = Image.new("RGB", (cols * cel, linhas * cel), (24, 24, 24))
        d = ImageDraw.Draw(folha)
        for k, arq in enumerate(arquivos[pag:pag + cols * linhas]):
            im = ImageOps.exif_transpose(Image.open(arq)).convert("RGB")
            im.thumbnail((cel - 12, cel - 12))
            x0, y0 = (k % cols) * cel, (k // cols) * cel
            folha.paste(im, (x0 + (cel - im.width) // 2, y0 + (cel - im.height) // 2))
            n = str(pag + k + 1)
            d.rectangle([x0 + 6, y0 + 6, x0 + 18 + 20 * len(n), y0 + 46], fill=(0, 33, 77))
            d.text((x0 + 12, y0 + 8), n, font=fonte, fill=(255, 255, 255))
        destino = Path(a.saida) if len(arquivos) <= cols * linhas else \
            Path(a.saida).with_name(f"{Path(a.saida).stem}-{pag // (cols * linhas) + 1}{Path(a.saida).suffix}")
        folha.save(destino, "JPEG", quality=85)
        saidas.append(str(destino))
    print(json.dumps({"folhas": saidas, "imagens": {i + 1: str(p) for i, p in enumerate(arquivos)}}, ensure_ascii=False))


# =========================================================================== transcrição (nuvem)
def modelo_whisper(nome):
    import tarfile
    pasta = MODELOS / f"sherpa-onnx-whisper-{nome}"
    if not (pasta / f"{nome}-tokens.txt").exists():
        arq = MODELOS / f"sherpa-onnx-whisper-{nome}.tar.bz2"
        print(f"Baixando Whisper {nome}...", file=sys.stderr)
        _baixar(f"{URL_MODELOS}/sherpa-onnx-whisper-{nome}.tar.bz2", arq)
        with tarfile.open(arq) as t:
            membros = [m for m in t.getmembers() if m.name.endswith(("int8.onnx", "tokens.txt"))]
            try:
                t.extractall(MODELOS, members=membros, filter="data")
            except TypeError:
                t.extractall(MODELOS, members=membros)
        arq.unlink()
    vad = MODELOS / "silero_vad.onnx"
    if not vad.exists():
        _baixar(f"{URL_MODELOS}/silero_vad.onnx", vad)
    pref = "int8." if (pasta / f"{nome}-encoder.int8.onnx").exists() else ""
    return pasta / f"{nome}-encoder.{pref}onnx", pasta / f"{nome}-decoder.{pref}onnx", pasta / f"{nome}-tokens.txt", vad


def ler_audio(arq, de=0.0, ate=None):
    import numpy as np
    cmd = ["ffmpeg", "-v", "error"] + (["-ss", f"{de:.3f}"] if de else []) + ["-i", str(arq)]
    if ate:
        cmd += ["-t", f"{float(ate) - de:.3f}"]
    pcm = subprocess.run(cmd + ["-f", "s16le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0


ALUCINACAO = re.compile(r"amara\.org|legendas? (pela|por|da)|inscreva-se|obrigad[oa] por assistir|"
                        r"transcri[cç][aã]o (e|por)|www\.|\.com\b|♪", re.I)


def _limpo(txt):
    txt = re.sub(r"[{}\\]", "", txt).strip()
    if not re.search(r"\w", txt) or ALUCINACAO.search(txt):
        return ""
    palavras = txt.lower().split()
    if len(palavras) >= 8 and len(set(palavras)) <= len(palavras) / 4:      # repetição em laço
        return ""
    return txt


def cmd_transcrever(a):
    import sherpa_onnx
    a.midia = achar(a.midia)
    enc, dec, tok, vad_path = modelo_whisper(a.modelo)
    rec = sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=str(enc), decoder=str(dec), tokens=str(tok), language=a.idioma, task="transcribe",
        num_threads=max(1, os.cpu_count() or 1))
    cfg = sherpa_onnx.VadModelConfig()
    cfg.silero_vad.model = str(vad_path)
    cfg.silero_vad.threshold = 0.5
    cfg.silero_vad.min_silence_duration = 0.2 if a.frases else 0.4
    cfg.silero_vad.min_speech_duration = 0.25
    if hasattr(cfg.silero_vad, "max_speech_duration"):
        cfg.silero_vad.max_speech_duration = 7 if a.frases else 20
    cfg.sample_rate = SR
    vad = sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=240)
    de = float(a.de or 0)
    amostras = ler_audio(a.midia, de, a.ate)
    base = de + float(a.desloca or 0)
    total = len(amostras) / SR
    janela = cfg.silero_vad.window_size
    segs, aviso = [], [0.0]

    def esvaziar():
        while not vad.empty():
            s = vad.front
            n = len(s.samples)
            i0 = max(0, s.start - int(0.2 * SR))
            i1 = min(len(amostras), s.start + n + int(0.15 * SR))
            st = rec.create_stream()
            st.accept_waveform(SR, amostras[i0:i1])
            rec.decode_stream(st)
            txt = _limpo(st.result.text)
            if txt:
                segs.append({"inicio": round(base + s.start / SR, 2), "fim": round(base + (s.start + n) / SR, 2),
                             "texto": txt})
            vad.pop()
            feito = (s.start + n) / SR
            if feito - aviso[0] >= 300:
                aviso[0] = feito
                print(f"[transcrever] {int(feito // 60)} de {int(total // 60)} min", file=sys.stderr, flush=True)

    for i in range(0, len(amostras), janela):
        vad.accept_waveform(amostras[i:i + janela])
        esvaziar()
    vad.flush()
    esvaziar()
    saida = Path(a.saida)
    saida.write_text(json.dumps({"midia": str(a.midia), "modelo": a.modelo, "idioma": a.idioma, "frases": a.frases,
                                 "de": de, "duracao": round(total, 1), "segmentos": segs},
                                ensure_ascii=False, indent=1), encoding="utf-8")

    def mmss(t):
        return f"{int(t // 60):02d}:{t % 60:04.1f}"

    saida.with_suffix(".txt").write_text("".join(f"[{mmss(s['inicio'])}–{mmss(s['fim'])}] {s['texto']}\n" for s in segs),
                                         encoding="utf-8")
    print(json.dumps({"segmentos": len(segs), "duracao_s": round(total, 1), "json": str(saida),
                      "txt": str(saida.with_suffix(".txt"))}))


# =========================================================================== legendas (ASS)
DESTAQUE_ASS = "&HFFA58F&"     # #8fa5ff (azul claro da paleta) para números
NUMERO = re.compile(r"(?:R\$\s?)?\d+(?:[.,]\d+)*(?:\s?%|\s(?:mil|milhões|milhão|bilhões|bilhão|anos|meses|dias|"
                    r"horas|vezes|médicos)\b)?")
ESTILO_ASS = ("Style: Legenda,Manrope ExtraLight,60,&H00FFFFFF,&H00FFFFFF,&H004D2100,&H78000000,-1,0,0,0,"
              "100,100,0.5,0,1,3.2,1.5,2,90,90,500,1")
UNIDADES = {"%", "mil", "milhões", "milhão", "bilhões", "bilhão", "anos", "meses", "dias", "horas", "vezes",
            "médicos", "pacientes", "reais", "por", "pontos"}
CURTAS = {"o", "a", "os", "as", "e", "é", "de", "do", "da", "em", "no", "na", "um", "uma", "que", "se", "por", "para",
          "com", "ao", "à", "dos", "das", "nos", "nas", "eu", "me", "te", "seu", "sua", "mais", "mas", "r$"}


def _ts(t):
    t = max(0.0, t)
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def _linhas(texto, max_chars=24):
    """Quebra em linhas de até max_chars sem terminar linha em artigo/preposição (a palavra curta desce)."""
    linhas, atual = [], []
    for p in texto.split():
        if atual and len(" ".join(atual + [p])) > max_chars:
            desce = []
            if len(atual) > 1 and re.fullmatch(r"(R\$)?\d[\d.,]*", atual[-1]) and \
                    p.lower().strip(",.;:!?") in UNIDADES:          # "60 horas" fica junto
                desce.insert(0, atual.pop())
            while (len(atual) > 1 and atual[-1].lower().strip(",.;:!?") in CURTAS
                   and len(" ".join(atual[:-1])) >= 10):           # não deixa a linha de cima minúscula
                desce.insert(0, atual.pop())
            linhas.append(" ".join(atual))
            atual = desce + [p]
        else:
            atual.append(p)
    if atual:
        linhas.append(" ".join(atual))
    return linhas


def _quebrar(texto, max_chars=24):
    """Blocos de até 2 linhas, cortando primeiro nas frases (. ! ?)."""
    blocos = []
    for frase in re.split(r"(?<=[.!?…])\s+", texto.strip()):
        linhas = _linhas(frase, max_chars)
        blocos += [linhas[i:i + 2] for i in range(0, len(linhas), 2)]
    return [b for b in blocos if b]


def _destacar(linha):
    return NUMERO.sub(lambda m: "{\\c" + DESTAQUE_ASS + "}" + m.group(0) + "{\\c&HFFFFFF&}", linha)


def gerar_ass(segmentos, desloca, duracao, destino):
    eventos = []
    for s in segmentos:
        ini, fim = s["inicio"] - desloca, s["fim"] - desloca
        if fim <= 0.05 or ini >= duracao:
            continue
        ini, fim = max(ini, 0.0), min(fim, duracao)
        blocos = _quebrar(s["texto"])
        pesos = [len(" ".join(b)) + 6 for b in blocos]
        t = ini
        for b, p in zip(blocos, pesos):
            d = (fim - ini) * p / sum(pesos)
            eventos.append([t, t + d, "\\N".join(_destacar(l) for l in b)])
            t += d
    for i in range(len(eventos) - 1):                       # sem sobreposição; emenda pausas curtas
        prox = eventos[i + 1][0]
        if eventos[i][1] > prox or prox - eventos[i][1] < 0.35:
            eventos[i][1] = prox
    cab = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 2\n"
           "ScaledBorderAndShadow: yes\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, "
           "SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, "
           "Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n" + ESTILO_ASS +
           "\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    corpo = "".join(f"Dialogue: 0,{_ts(i)},{_ts(f)},Legenda,,0,0,0,,{{\\fad(60,60)}}{txt}\n" for i, f, txt in eventos)
    Path(destino).write_text(cab + corpo, encoding="utf-8")
    return len(eventos)


# =========================================================================== enquadramento
def trilha_rosto(video, W, H, cw, pre, de=0.0, dur=None, passo=0.5):
    """Caminho do recorte vertical [(t, x em px)] seguindo o rosto principal, com zona morta, velocidade
    máxima e volta suave ao centro. Retorna (pontos, fração de amostras com rosto)."""
    import numpy as np
    lw = 640
    lh = par(H * lw / W)
    cmd = ["ffmpeg", "-v", "error"] + (["-ss", f"{de:.3f}"] if de else []) + ["-i", str(video)]
    cmd += (["-t", f"{dur:.3f}"] if dur else []) + ["-vf", f"fps={1 / passo},{pre},scale={lw}:{lh}",
                                                     "-pix_fmt", "bgr24", "-f", "rawvideo", "-"]
    bruto = subprocess.run(cmd, capture_output=True, check=True).stdout
    tam = lw * lh * 3
    n = len(bruto) // tam
    if n == 0:
        return None, 0.0
    quadros = np.frombuffer(bruto[:n * tam], np.uint8).reshape(n, lh, lw, 3)
    detectar = _detector()
    xs = []
    for q in quadros:
        r = detectar(np.ascontiguousarray(q))
        if r:
            x, _, fw, _, _ = _principal(r)
            xs.append((x + fw / 2) / lw)
        else:
            xs.append(None)
    validos = [i for i, x in enumerate(xs) if x is not None]
    frac = len(validos) / n
    if not validos:
        return None, 0.0
    cheio = [xs[min(validos, key=lambda j: abs(j - i))] for i in range(n)]
    suave = []
    for i in range(n):
        viz = sorted(cheio[max(0, i - 2):i + 3])
        suave.append(viz[len(viz) // 2])
    rel = cw / W
    zona, vmax, meia = 0.18 * rel, 0.10 * rel, rel / 2
    inicio = sorted(suave[:6])
    cam = min(max(inicio[len(inicio) // 2], meia), 1 - meia)
    pts = []
    for k, x in enumerate(suave):
        d = x - cam
        if abs(d) > zona:
            cam += math.copysign(min(abs(d) - zona, vmax), d)
        else:
            cam += d * 0.12                                   # recentraliza devagar quando o rosto para
        cam = min(max(cam, meia), 1 - meia)
        pts.append((round(k * passo, 2), int(min(max(round(cam * W - cw / 2), 0), W - cw))))
    simples = [pts[0]]
    for i in range(1, len(pts) - 1):
        (t0, x0), (t1, x1), (t2, x2) = simples[-1], pts[i], pts[i + 1]
        if abs(x0 + (x2 - x0) * (t1 - t0) / (t2 - t0) - x1) > 3:
            simples.append(pts[i])
    if len(pts) > 1:
        simples.append(pts[-1])
    return simples, frac


def _x_em(pts, t):
    for (t0, x0), (t1, x1) in zip(pts[:-1], pts[1:]):
        if t < t1:
            return int(x0 + (x1 - x0) * max(0.0, t - t0) / (t1 - t0))
    return pts[-1][1]


def _expr_x(pts):
    e = str(pts[-1][1])
    for (t0, x0), (t1, x1) in reversed(list(zip(pts[:-1], pts[1:]))):
        seg = str(x0) if x0 == x1 else f"{x0}+({x1 - x0})*(t-{t0:.2f})/{t1 - t0:.2f}"
        e = f"if(lt(t,{t1:.2f}),{seg},{e})"
    return e


def _moldura(entrada, pre, saida):
    return (f"{entrada}{pre},split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            "boxblur=28:2,eq=brightness=-0.16:saturation=0.85[bg];[b]scale=1080:-2:flags=lanczos[fg];"
            f"[bg][fg]overlay=0:(H-h)/2-120,setsar=1{saida}")


# =========================================================================== corte final
def _titulo_png(T, destino, titulo, rotulo):
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    col = Image.new("L", (1, 1920))
    for y in range(1920):
        col.putpixel((0, y), int(255 * 0.80 * (1 - y / 820) ** 1.3) if y < 820 else 0)
    veu = Image.new("RGBA", (1080, 1920), T.NAVY + (0,))
    veu.putalpha(col.resize((1080, 1920)))
    img.alpha_composite(veu)
    d = ImageDraw.Draw(img)
    linhas = [l.strip() for l in titulo.split("|") if l.strip()]

    def largura(l, s):
        return sum(d.textlength(p, font=T.font("serif-i" if i % 2 else "serif", s))
                   for i, p in enumerate(l.split("*")) if p)

    tam = 76
    while tam > 50 and max(largura(l, tam) for l in linhas) > 1080 - 2 * T.M:
        tam -= 2
    y = 300
    if rotulo:
        d.line([T.M, y, T.M + 56, y], fill=T.CARAMEL, width=2)
        T.spaced(d, T.M, y + 18, rotulo, T.font("sans-sb", 22), T.G2)
        y += 72
    for l in linhas:
        T.rich_line(d, T.M - 4, y, l, tam, T.OFF, T._h("aab8ff"))
        y += int(tam * 1.18)
    img.save(destino)


def _rodape_png(T, destino, rodape):
    from PIL import Image, ImageDraw
    T.set_formato("story")
    try:
        img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        img.alpha_composite(T._veu(alpha_topo=0.0, inicio=0.56, alpha_base=0.88))
        T._footer(img, ImageDraw.Draw(img), True, rodape)
    finally:
        T.set_formato("feed")
    img.save(destino)


def cmd_corte(a):
    sys.path.insert(0, str(RAIZ / "marca"))
    import ludo_templates as T
    from PIL import Image
    a.trecho = achar(a.trecho)
    info = sondar(a.trecho)
    W, H = _dims_trabalho(info["largura"], info["altura"], 1920)
    if info["hdr"]:
        W, H = _dims_trabalho(info["largura"], info["altura"], 1440)
    pre = _pre_video(info, W, H)
    de = float(a.de or 0)
    dur = (float(a.ate) if a.ate else info["duracao"]) - de
    tmp = Path(tempfile.mkdtemp())

    # 1) enquadramento vertical
    cw = min(W, par(H * 9 / 16))
    modo, pts, frac = a.modo, None, None
    if modo != "moldura":
        if W - cw > 8:
            pts, frac = trilha_rosto(a.trecho, W, H, cw, pre, de, dur)
            modo = "moldura" if (a.modo == "auto" and (pts is None or frac < 0.35)) else "recorte"
        else:
            modo = "recorte"
    if modo == "recorte":
        x = _expr_x(pts) if pts else str((W - cw) // 2)
        filtro = [f"[0:v]{pre},crop={cw}:{H}:'{x}':0,scale=1080:1920:flags=lanczos,setsar=1,fps=30[v0]"]
    else:
        filtro = [_moldura("[0:v]", pre, ",fps=30[v0]")]
    ultimo = "v0"

    # 2) legendas
    n_leg = 0
    if a.legendas:
        segs = json.loads(Path(a.legendas).read_text(encoding="utf-8"))
        segs = segs["segmentos"] if isinstance(segs, dict) else segs
        ass = tmp / "legendas.ass"
        n_leg = gerar_ass(segs, float(a.desloca or 0) + de, dur, ass)
        if n_leg:
            filtro.append(f"[{ultimo}]subtitles={ass}:fontsdir={FONTES}[v1]")
            ultimo = "v1"

    # 3) rodapé fixo e título nos primeiros segundos
    _rodape_png(T, tmp / "rodape.png", a.rodape)
    entradas = ["-loop", "1", "-framerate", "30", "-i", tmp / "rodape.png"]
    filtro.append(f"[{ultimo}][1:v]overlay=0:0:shortest=1[v2]")
    ultimo, n_img = "v2", 1
    if a.titulo:
        _titulo_png(T, tmp / "titulo.png", a.titulo, a.rotulo)
        entradas += ["-loop", "1", "-framerate", "30", "-t", "4.2", "-i", tmp / "titulo.png"]
        filtro.append("[2:v]format=rgba,fade=t=in:st=0:d=0.25:alpha=1,fade=t=out:st=3.4:d=0.6:alpha=1[tt];"
                      f"[{ultimo}][tt]overlay=0:0:eof_action=pass[v3]")
        ultimo, n_img = "v3", 2
    entrada_video = (["-ss", f"{de:.3f}"] if de else []) + (["-t", f"{dur:.3f}"] if (a.ate or de) else []) + \
        ["-i", a.trecho]
    if info["tem_audio"]:
        audio_in, audio = [], ["-map", "0:a:0", "-af", "highpass=f=70,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100"]
    else:
        audio_in, audio = ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"], ["-map", f"{n_img + 1}:a"]

    # 4) codificação com teto de tamanho (jsDelivr serve até 20 MB por arquivo)
    kbps = int(min(4500, a.limite_mb * 8000 / dur * 0.93 - 128))
    saida = Path(a.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(3):
        rodar(["ffmpeg", "-y", "-v", "error", *entrada_video, *entradas, *audio_in,
               "-filter_complex", ";".join(filtro), "-map", f"[{ultimo}]", *audio,
               "-c:v", "libx264", "-preset", a.preset, "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", "30",
               "-b:v", f"{kbps}k", "-maxrate", f"{int(kbps * 1.6)}k", "-bufsize", f"{kbps * 2}k", "-g", "60",
               "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-t", f"{dur:.3f}", "-movflags", "+faststart", saida])
        mb = saida.stat().st_size / 1e6
        if mb <= a.limite_mb + 1.0:
            break
        kbps = int(kbps * a.limite_mb / mb * 0.95)

    # 5) capa: mesmo enquadramento, com título e rodapé, sem legenda
    capa = Path(a.capa) if a.capa else saida.with_suffix(".jpg")
    t_capa = min(1.2, dur / 2)
    if modo == "recorte":
        xc = _x_em(pts, t_capa) if pts else (W - cw) // 2
        fc = f"[0:v]{pre},crop={cw}:{H}:{xc}:0,scale=1080:1920:flags=lanczos[c]"
    else:
        fc = _moldura("[0:v]", pre, "[c]")
    rodar(["ffmpeg", "-y", "-v", "error", "-ss", f"{de + t_capa:.3f}", "-i", a.trecho, "-filter_complex", fc,
           "-map", "[c]", "-frames:v", "1", tmp / "capa.png"])
    img = Image.open(tmp / "capa.png").convert("RGBA")
    img.alpha_composite(Image.open(tmp / "rodape.png").convert("RGBA"))
    if a.titulo:
        img.alpha_composite(Image.open(tmp / "titulo.png").convert("RGBA"))
    img.convert("RGB").save(capa, "JPEG", quality=92)

    res = {"corte": str(saida), "capa": str(capa), "modo": modo,
           "rostos_pct": None if frac is None else round(frac * 100), "movimentos": 0 if not pts else len(pts) - 1,
           "legendas": n_leg, "duracao_s": round(sondar(saida)["duracao"], 1),
           "mb": round(saida.stat().st_size / 1e6, 1), "kbps_video": kbps}
    if a.mosaico:                                            # 4 quadros lado a lado para conferir
        mos = saida.with_name(saida.stem + "-mosaico.jpg")
        quadros = []
        for k, t in enumerate([1.2] + [dur * f for f in (0.3, 0.55, 0.8)]):
            q = tmp / f"q{k}.jpg"
            rodar(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", saida, "-frames:v", "1",
                   "-vf", "scale=360:640", q])
            quadros.append(q)
        rodar(["ffmpeg", "-y", "-v", "error", *sum([["-i", q] for q in quadros], []), "-filter_complex",
               "".join(f"[{k}:v]" for k in range(len(quadros))) + f"hstack=inputs={len(quadros)}", mos])
        res["mosaico"] = str(mos)
    print(json.dumps(res, ensure_ascii=False))


# =========================================================================== linha de comando
def main():
    ap = argparse.ArgumentParser(description="LIAM – fotos e vídeos da equipe")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("listar")
    p.add_argument("pasta")
    p.add_argument("--sem-sondar", action="store_true")
    p.set_defaults(f=cmd_listar)
    p = sub.add_parser("audio")
    p.add_argument("video")
    p.add_argument("saida")
    p.add_argument("--de")
    p.add_argument("--ate")
    p.set_defaults(f=cmd_audio)
    p = sub.add_parser("trecho")
    for n in ("video", "inicio", "fim", "saida"):
        p.add_argument(n)
    p.add_argument("--preset", default="veryfast")
    p.add_argument("--altura-max", type=int, default=1440)
    p.set_defaults(f=cmd_trecho)
    p = sub.add_parser("juntar", help="juntar parte1.mp4 parte2.mp4 ... saida.mp4")
    p.add_argument("partes", nargs="+")
    p.set_defaults(f=None)
    p = sub.add_parser("foto")
    p.add_argument("arquivos", nargs="+")
    p.add_argument("--saida", required=True)
    p.add_argument("--prefixo")
    p.set_defaults(f=cmd_foto)
    p = sub.add_parser("folha")
    p.add_argument("arquivos", nargs="+")
    p.add_argument("--saida", required=True)
    p.set_defaults(f=cmd_folha)
    p = sub.add_parser("transcrever")
    p.add_argument("midia")
    p.add_argument("saida")
    p.add_argument("--modelo", default="small", choices=["tiny", "base", "small", "medium"])
    p.add_argument("--idioma", default="pt")
    p.add_argument("--frases", action="store_true")
    p.add_argument("--de")
    p.add_argument("--ate")
    p.add_argument("--desloca", default="0")
    p.set_defaults(f=cmd_transcrever)
    p = sub.add_parser("corte")
    p.add_argument("trecho")
    p.add_argument("saida")
    p.add_argument("--legendas")
    p.add_argument("--desloca", default="0")
    p.add_argument("--de")
    p.add_argument("--ate")
    p.add_argument("--titulo")
    p.add_argument("--rotulo")
    p.add_argument("--rodape", default="ludogroup.com.br")
    p.add_argument("--modo", default="auto", choices=["auto", "recorte", "moldura"])
    p.add_argument("--preset", default="medium")
    p.add_argument("--capa")
    p.add_argument("--limite-mb", type=float, default=18.0)
    p.add_argument("--mosaico", action="store_true")
    p.set_defaults(f=cmd_corte)
    a = ap.parse_args()
    if a.cmd == "juntar":
        if len(a.partes) < 3:
            ap.error("juntar: informe 2 ou mais partes e o arquivo de saída")
        a.partes, a.saida = a.partes[:-1], a.partes[-1]
        cmd_juntar(a)
    else:
        a.f(a)


if __name__ == "__main__":
    main()
