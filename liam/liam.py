#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LIAM – Ludo Inteligência Artificial de Marketing
Motor de aprendizado do Instagram da Ludo (PDCA + machine learning bayesiano).

Entrada: exports JSON das consultas SQL do Notion (ver liam/README.md).
Saída (pasta --saida, padrão liam/saida/):
  scores.json        Score LIAM e métricas por post (para gravar na Fila)
  recomendacao.json  efeitos por variável, P(melhor), plano do dia e radar de concorrentes
  relatorio.md       resumo legível (vai para a página LIAM no Notion)

Método
  1. Cada post vira uma observação: y = ln(1 + pontos), com pontos =
     0,05·alcance + curtidas + 2·comentários + 3·salvamentos + 4·compartilhamentos
     + 5·seguidores ganhos + 0,5·visitas ao perfil.
  2. Regressão linear bayesiana (ridge) com todas as características ao mesmo tempo
     (formato, pilar, gancho, layout, tema, origem, faixa, dia, humano): cada opção
     ganha um coeficiente; e^coef = efeito multiplicativo sobre os pontos. Estimar
     tudo junto separa efeitos que andam juntos (ex.: Reels e posts com pessoas).
  3. Priors céticos (efeitos perto de zero até prova em contrário), peso maior para
     posts recentes (meia-vida de 120 dias) e menor para métricas ainda imaturas.
  4. Decisão por Thompson sampling linear: sorteia um cenário plausível dos
     coeficientes e escolhe a melhor opção de cada variável – explora o que tem
     pouca evidência e abandona o que já provou ser pior.
  5. Concorrentes: engajamento de cada post ÷ mediana do próprio perfil (índice);
     índices altos = estratégias vencedoras a adaptar (nunca copiar).

Só usa a biblioteca padrão do Python 3.9+.
"""
import argparse
import json
import math
import random
import re
import statistics
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
    SP = ZoneInfo("America/Sao_Paulo")
except Exception:  # pragma: no cover
    SP = timezone(timedelta(hours=-3))

# --------------------------------------------------------------------------- parâmetros
PESOS = {"alcance": 0.05, "curtidas": 1.0, "comentarios": 2.0, "salvos": 3.0,
         "compart": 4.0, "seguidores": 5.0, "visitas": 0.5}
MEIA_VIDA_DIAS = 120     # o peso de um post cai pela metade a cada 120 dias
MATURIDADE_DIAS = 2      # métricas medidas com menos de 2 dias de vida valem menos
PESO_IMATURO = 0.35
JANELA_BASE = 30         # Score 100 = mediana dos últimos 30 posts próprios maduros
PRIOR_EFEITO_VAR = 0.5   # dp 0,7 em escala log: a priori, efeitos típicos entre ×0,5 e ×2
SORTEIOS = 3000          # Monte Carlo para P(melhor)
P_FORTE, N_FORTE = 0.80, 4.0   # evidência forte: P(melhor) >= 80% com n efetivo >= 4
PROPRIOS = {"ludogroup.oficial", "luisdornela.oficial"}

PROGRAMACAO = {  # dia da semana (0 = segunda) -> (formato, pilar) da grade de marca/ESTRATEGIA.md
    0: ("Carrossel", "Contexto & Mercado"),
    1: ("Feed", "Estrutura & Patrimônio"),
    2: ("Reels", "Proteção"),
    3: ("Carrossel", "Gestão do consultório"),
    4: ("Carrossel", "Resumo da Semana"),
    5: ("Reels", "Manifesto & Marca"),
    6: ("Feed", "Manifesto & Marca"),
}
UNIVERSO = {
    "formato": ["Feed", "Carrossel", "Reels"],
    "pilar": ["Contexto & Mercado", "Estrutura & Patrimônio", "Proteção", "Gestão do consultório",
              "Manifesto & Marca", "Bastidores & Eventos", "Resumo da Semana"],
    "gancho": ["Pergunta", "Dado", "Afirmação forte", "Lista", "Notícia", "Mito x Verdade",
               "Analogia médica", "Bastidores"],
    "layout": ["editorial", "pontos", "numero", "manifesto", "grafico", "foto", "video"],
    "tema": ["People", "Capital", "Care", "Company", "A&T", "CredEx", "Pay", "Law", "Institucional"],
    "origem": ["Notícia em alta", "Concorrente", "Sugestão", "Base de Conhecimento", "Aprendizado LIAM"],
    "faixa": ["Manhã 7h-9h", "Almoço 12h-13h", "Fim de tarde 18h-19h", "Noite 21h-22h"],
    "dia": ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"],
    "humano": ["sim", "não"],
    "fonte": ["LIAM", "Histórico"],   # controle de época (não é decisão): separa a fase LIAM do histórico
}
VARIAVEIS = list(UNIVERSO)
CONTROLES = {"fonte"}
DIAS = UNIVERSO["dia"]
DECISOES = ["gancho", "layout", "faixa", "tema", "humano", "origem"]   # escolhidas por Thompson
LAYOUTS_POR_FORMATO = {
    "Feed": ["editorial", "pontos", "numero", "manifesto", "grafico", "foto"],
    "Carrossel": ["pontos", "numero", "grafico", "editorial", "foto"],   # miolo; capa editorial e fecho manifesto
    "Reels": ["video", "foto"],
}
INSIGHT_PARA_CAMPO = {"reach": "alcance", "likes": "curtidas", "comments": "comentarios",
                      "saved": "salvos", "shares": "compart", "follows": "seguidores",
                      "profile_visits": "visitas", "views": "views",
                      "total_interactions": "interacoes"}
CAMPOS = ["alcance", "curtidas", "comentarios", "salvos", "compart", "seguidores", "visitas",
          "views", "interacoes"]
HUMANO_RE = re.compile(
    r"\b(evento|estivemos|live|palestra|bastidor\w*|equipe|time|s[óo]cio|n[óo]s|eu e|encontro|feira|"
    r"congresso|depoimento|entrevista|falamos|convite|caf[ée]|febraban|andav)\b", re.I)


# --------------------------------------------------------------------------- utilidades
def carregar(caminho):
    """Lê o JSON exportado do Notion: aceita {"results": [...]} ou uma lista."""
    if not caminho:
        return []
    p = Path(caminho)
    if not p.exists():
        print(f"[aviso] arquivo não encontrado: {caminho}")
        return []
    txt = p.read_text(encoding="utf-8").strip()
    if not txt:
        return []
    dados = json.loads(txt)
    if isinstance(dados, dict):
        for k in ("results", "rows", "data"):
            if isinstance(dados.get(k), list):
                return dados[k]
        return [dados]
    return dados if isinstance(dados, list) else []


def data_hora(v):
    """Converte '2026-10-01 11:46:00Z', ISO com fuso ou só a data em datetime UTC."""
    if not v:
        return None
    s = str(v).strip()
    so_data = len(s) <= 10
    s = s.replace(" ", "T", 1)
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        d = datetime.fromisoformat(s)
    except ValueError:
        try:
            d = datetime.strptime(s[:10], "%Y-%m-%d")
            so_data = True
        except ValueError:
            return None
    if d.tzinfo is None:
        d = (d.replace(hour=12) if so_data else d).replace(tzinfo=SP)
    return d.astimezone(timezone.utc)


def numero(v):
    if v is None or v == "":
        return None
    try:
        return float(str(v).replace(",", "."))
    except ValueError:
        return None


def ler_metricas(s):
    """'reach=20;likes=0;...' -> {'alcance': 20.0, 'curtidas': 0.0, ...}"""
    out = {}
    for parte in str(s or "").split(";"):
        if "=" not in parte:
            continue
        k, v = parte.split("=", 1)
        val = numero(v.strip())
        if val is not None:
            out[INSIGHT_PARA_CAMPO.get(k.strip(), k.strip())] = val
    return out


def lista(v):
    """Multi-select do Notion: lista, JSON '["a","b"]' ou 'a, b'."""
    if v is None or v == "":
        return []
    if isinstance(v, list):
        return [str(x) for x in v if x]
    s = str(v).strip()
    if s.startswith("["):
        try:
            return [str(x) for x in json.loads(s) if x]
        except ValueError:
            pass
    return [x.strip() for x in s.split(",") if x.strip()]


def formato_de_tipo(t):
    t = (t or "").upper()
    if "CAROUSEL" in t:
        return "Carrossel"
    if "REELS" in t or "VIDEO" in t:
        return "Reels"
    if "IMAGE" in t:
        return "Feed"
    return None


def faixa_de(hora):
    if 6 <= hora <= 10:
        return "Manhã 7h-9h"
    if 11 <= hora <= 14:
        return "Almoço 12h-13h"
    if 15 <= hora <= 17:
        return "Tarde 15h-17h"
    if 18 <= hora <= 20:
        return "Fim de tarde 18h-19h"
    if 21 <= hora <= 23:
        return "Noite 21h-22h"
    return "Madrugada 0h-5h"


def pontos_de(m):
    return sum(PESOS[k] * (m.get(k) or 0.0) for k in PESOS)


def br(x, casas=1):
    """Número no padrão brasileiro (1.234,5)."""
    if x is None:
        return "–"
    if abs(x - round(x)) < 1e-9:
        return f"{int(round(x)):,}".replace(",", ".")
    return f"{x:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def vezes(x):
    return "×" + f"{x:.2f}".replace(".", ",")


def pct(x):
    return f"{100 * x:.0f}%"


def valores_do_post(p, var):
    v = p.get(var)
    if not v:
        return []
    return v if isinstance(v, list) else [v]


# --------------------------------------------------------------------------- posts próprios
def montar_posts(fila, metricas, ref, excluir):
    """Junta Fila (características) + Métricas (resultados). Retorna (posts, seguidores)."""
    seguidores, seg_col = None, None
    ultima = {}
    for r in metricas:
        pid = str(r.get("post_id") or "").strip()
        if not pid:
            continue
        col = data_hora(r.get("coletado"))
        if pid.upper() == "PERFIL":
            m = ler_metricas(r.get("metricas"))
            if m.get("followers") and (seg_col is None or (col and col > seg_col)):
                seguidores, seg_col = m["followers"], col
            continue
        if pid not in ultima or (col and (ultima[pid]["_col"] is None or col > ultima[pid]["_col"])):
            ultima[pid] = dict(r, _col=col)

    posts = {}
    for r in fila:
        pid = str(r.get("post_id") or "").strip()
        status = str(r.get("status") or "publicado").strip().lower()
        if not pid or status != "publicado" or pid in excluir:
            continue
        if "não entra na análise" in str(r.get("teste_ab") or "").lower():
            excluir.add(pid)
            continue
        formato = r.get("formato")
        if formato == "Story":           # Stories não passam pelo Make; se foi ao feed, foi engano
            excluir.add(pid)
            continue
        pilar = r.get("pilar")
        if formato == "Resumo da Semana":
            formato, pilar = "Carrossel", pilar or "Resumo da Semana"
        posts[pid] = {
            "post_id": pid, "fonte": "LIAM", "titulo": r.get("titulo"),
            "data": data_hora(r.get("data")), "formato": formato, "pilar": pilar,
            "gancho": r.get("gancho"), "layout": lista(r.get("layout")), "tema": r.get("tema"),
            "origem": r.get("origem"), "faixa_plano": r.get("faixa"),
            "met": {k: numero(r.get(k)) for k in CAMPOS},
            "met_col": data_hora(r.get("metricas_em")), "legenda": "",
        }

    for pid, r in ultima.items():
        if pid in excluir:
            continue
        m = ler_metricas(r.get("metricas"))
        if m.get("curtidas") is None:
            m["curtidas"] = numero(r.get("curtidas"))
        if m.get("comentarios") is None:
            m["comentarios"] = numero(r.get("comentarios"))
        p = posts.get(pid)
        if p is None:
            p = posts[pid] = {
                "post_id": pid, "fonte": "Histórico", "titulo": None,
                "data": data_hora(r.get("data_post")), "formato": formato_de_tipo(r.get("tipo")),
                "pilar": None, "gancho": None, "layout": [], "tema": None, "origem": None,
                "faixa_plano": None, "met": {}, "met_col": None, "legenda": r.get("legenda") or "",
            }
        for k, v in m.items():          # métricas coletadas pelo Make são a fonte principal
            if v is not None:
                p["met"][k] = v
        p["met_col"] = r["_col"] or p["met_col"]
        p["data"] = data_hora(r.get("data_post")) or p["data"]   # horário real de publicação

    saida = []
    for p in posts.values():
        met = p["met"]
        if not p["data"] or not any(met.get(k) for k in ("alcance", "curtidas", "views")):
            continue                     # sem data ou sem nenhuma métrica ainda
        local = p["data"].astimezone(SP)
        idade_med = ((p["met_col"] or ref) - p["data"]).total_seconds() / 86400
        idade_ref = max((ref - p["data"]).total_seconds() / 86400, 0)
        maduro = idade_med >= MATURIDADE_DIAS
        humano = ("sim" if ("foto" in p["layout"] or p["gancho"] == "Bastidores"
                            or p["pilar"] == "Bastidores & Eventos") else "não")
        if p["fonte"] == "Histórico":   # inferido: vídeos do perfil eram falas/lives; fotos de eventos
            humano = "sim" if (p["formato"] == "Reels" or HUMANO_RE.search(p["legenda"])) else "não"
        p.update({
            "data_sp": local.strftime("%Y-%m-%d %H:%M"), "dia": DIAS[local.weekday()],
            "faixa": faixa_de(local.hour), "humano": humano, "maduro": maduro,
            "idade_medicao": round(idade_med, 1),
            "peso": (0.5 ** (idade_ref / MEIA_VIDA_DIAS)) * (1.0 if maduro else PESO_IMATURO),
            "pontos": pontos_de(met),
        })
        p["y"] = math.log1p(p["pontos"])
        saida.append(p)
    saida.sort(key=lambda p: p["data"], reverse=True)
    return saida, seguidores


def aplicar_score(posts):
    maduros = [p for p in posts if p["maduro"]][:JANELA_BASE] or posts[:JANELA_BASE]
    base = statistics.median([p["pontos"] for p in maduros]) if maduros else 1.0
    base = base or 1.0
    for p in posts:
        p["score"] = round(100 * p["pontos"] / base)
    return base


# --------------------------------------------------------------------------- álgebra mínima
def cholesky(A):
    n = len(A)
    L = [[0.0] * n for _ in range(n)]
    for i in range(n):
        Li = L[i]
        for j in range(i + 1):
            Lj = L[j]
            s = A[i][j] - sum(Li[k] * Lj[k] for k in range(j))
            if i == j:
                Li[i] = math.sqrt(max(s, 1e-12))
            else:
                Li[j] = s / Lj[j]
    return L


def sub_inferior(L, b):          # resolve L·y = b
    y = [0.0] * len(L)
    for i, Li in enumerate(L):
        y[i] = (b[i] - sum(Li[k] * y[k] for k in range(i))) / Li[i]
    return y


def sub_superior(L, y):          # resolve Lᵀ·x = y
    n = len(L)
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        x[i] = (y[i] - sum(L[k][i] * x[k] for k in range(i + 1, n))) / L[i][i]
    return x


# --------------------------------------------------------------------------- modelo bayesiano
class Modelo:
    """Regressão linear bayesiana ponderada (ridge) com Thompson sampling."""

    def __init__(self, posts, priors=None):
        self.priors = priors or {}             # médias a priori vindas dos concorrentes {(var, valor): coef}
        self.cols = [("_base", None)]
        for var in VARIAVEIS:
            vals = list(UNIVERSO[var])
            for p in posts:
                for v in valores_do_post(p, var):
                    if v not in vals:
                        vals.append(v)
            self.cols += [(var, v) for v in vals]
        self.idx = {c: i for i, c in enumerate(self.cols)}
        k = len(self.cols)
        self.linhas = []
        self.n = [0.0] * k
        for p in posts:
            x = self.vetor(p)
            nz = [i for i, xi in enumerate(x) if xi]
            self.linhas.append((p, x, nz))
            for i in nz:
                self.n[i] += p["peso"] * x[i]
        W = sum(p["peso"] for p in posts)
        self.ybar = sum(p["peso"] * p["y"] for p in posts) / W
        var_y = sum(p["peso"] * (p["y"] - self.ybar) ** 2 for p in posts) / W
        piso = 0.25 if W < 15 else 0.15          # com poucos dados, assume ruído mínimo maior
        teto = max(var_y, piso)
        sigma2 = teto
        for _ in range(6):                       # ruído estimado pelo resíduo com graus de liberdade efetivos
            L, m = self._ajustar(sigma2)
            rss, gl = 0.0, 0.0
            for p, x, _nz in self.linhas:
                rss += p["peso"] * (p["y"] - sum(a * c for a, c in zip(x, m))) ** 2
                gl += (p["peso"] / sigma2) * sum(v * v for v in sub_inferior(L, x))
            if W - gl <= 1:
                break
            novo = min(max(rss / (W - gl), piso), teto)
            if abs(novo - sigma2) < 1e-3:
                sigma2 = novo
                break
            sigma2 = novo
        self.sigma2 = sigma2
        self.L, self.media = self._ajustar(sigma2)
        self.dp = []
        for i in range(k):
            e = [0.0] * k
            e[i] = 1.0
            self.dp.append(math.sqrt(max(sum(v * v for v in sub_inferior(self.L, e)), 0.0)))

    def _ajustar(self, sigma2):
        k = len(self.cols)
        A = [[0.0] * k for _ in range(k)]
        b = [0.0] * k
        for p, x, nz in self.linhas:
            w = p["peso"] / sigma2
            for i in nz:
                b[i] += w * x[i] * p["y"]
                Ai = A[i]
                for j in nz:
                    Ai[j] += w * x[i] * x[j]
        A[0][0] += 1 / 25.0                   # prior vago para o nível médio da conta
        b[0] += self.ybar / 25.0
        for i in range(1, k):
            A[i][i] += 1 / PRIOR_EFEITO_VAR   # prior cético: efeito 0 até prova em contrário,
            b[i] += self.priors.get(self.cols[i], 0.0) / PRIOR_EFEITO_VAR   # ou o sinal dos concorrentes
        L = cholesky(A)
        return L, sub_superior(L, sub_inferior(L, b))

    def vetor(self, p):
        x = [0.0] * len(self.cols)
        x[0] = 1.0
        for var in VARIAVEIS:
            vals = valores_do_post(p, var)
            for v in vals:
                i = self.idx.get((var, v))
                if i is not None:               # opção nunca vista = efeito a priori (zero)
                    x[i] += 1.0 / len(vals)
        return x

    def sortear(self, rng):
        z = [rng.gauss(0.0, 1.0) for _ in self.cols]
        u = sub_superior(self.L, z)
        return [m + d for m, d in zip(self.media, u)]

    def efeito(self, var, v):
        i = self.idx.get((var, v))
        if i is None:
            return None
        m, s = self.media[i], self.dp[i]
        return {"n": round(self.n[i], 2), "coef": m, "dp": s, "efeito": math.exp(m),
                "ic80": (math.exp(m - 1.2816 * s), math.exp(m + 1.2816 * s))}

    def opcoes(self, var, permitidas=None):
        return [v for (vv, v) in self.cols if vv == var and (permitidas is None or v in permitidas)]

    def prob_melhor(self, amostras, var, permitidas=None):
        nomes = self.opcoes(var, permitidas)
        cont = Counter(max(nomes, key=lambda v: beta[self.idx[(var, v)]]) for beta in amostras)
        return {v: cont[v] / len(amostras) for v in nomes}

    def prever(self, escolhas):
        """Pontos esperados (mediana) e intervalo de 80% para um post com essas escolhas."""
        x = self.vetor(escolhas)
        mu = sum(a * c for a, c in zip(x, self.media))
        s = math.sqrt(sum(v * v for v in sub_inferior(self.L, x)) + self.sigma2)
        return math.expm1(mu), (math.expm1(mu - 1.2816 * s), math.expm1(mu + 1.2816 * s))


def evidencia(p, n):
    if p >= P_FORTE and n >= N_FORTE:
        return "forte"
    if p >= 0.6 and n >= 2:
        return "moderada"
    return "fraca"


# --------------------------------------------------------------------------- plano do dia
def planejar(modelo, amostras, dia_alvo, rng, base):
    fmt_prog, pilar_prog = PROGRAMACAO[dia_alvo.weekday()]
    dia = DIAS[dia_alvo.weekday()]
    plano = {"data": dia_alvo.isoformat(), "dia": dia,
             "programacao": {"formato": fmt_prog, "pilar": pilar_prog}, "escolhas": {}}
    if modelo is None:
        plano["escolhas"]["formato"] = {"valor": fmt_prog, "motivo": "programação (sem dados)"}
        plano["escolhas"]["pilar"] = {"valor": pilar_prog, "motivo": "programação (sem dados)"}
        for var in DECISOES:
            plano["escolhas"][var] = {"valor": rng.choice(UNIVERSO[var]), "motivo": "sorteio (sem dados)"}
        return plano

    def contra_programacao(var, prior):
        pm = modelo.prob_melhor(amostras, var, UNIVERSO[var])
        melhor = max(pm, key=pm.get)
        info = modelo.efeito(var, melhor)
        if melhor != prior and evidencia(pm[melhor], info["n"]) == "forte":
            return melhor, (f"dados superam a programação: {melhor} com P(melhor) {pct(pm[melhor])}, "
                            f"efeito {vezes(info['efeito'])}, n={br(info['n'])}")
        return prior, f"programação mantida (melhor estimado: {melhor}, P {pct(pm[melhor])}, n={br(info['n'])})"

    formato, motivo = contra_programacao("formato", fmt_prog)
    plano["escolhas"]["formato"] = {"valor": formato, "motivo": motivo}
    if pilar_prog == "Resumo da Semana":
        plano["escolhas"]["pilar"] = {"valor": pilar_prog, "motivo": "sexta = Resumo da Semana"}
    else:
        pilar, motivo = contra_programacao("pilar", pilar_prog)
        plano["escolhas"]["pilar"] = {"valor": pilar, "motivo": motivo}

    beta = modelo.sortear(rng)                 # um cenário plausível (Thompson)
    permitidas = {"layout": LAYOUTS_POR_FORMATO.get(formato), "faixa": UNIVERSO["faixa"]}
    for var in DECISOES:
        nomes = modelo.opcoes(var, permitidas.get(var) or UNIVERSO[var])
        escolha = max(nomes, key=lambda v: beta[modelo.idx[(var, v)]])
        info = modelo.efeito(var, escolha)
        motivo = ("explorar: opção ainda não testada" if info["n"] == 0 else
                  f"Thompson: efeito estimado {vezes(info['efeito'])} "
                  f"(IC80% {vezes(info['ic80'][0])}–{vezes(info['ic80'][1])}, n={br(info['n'])})")
        plano["escolhas"][var] = {"valor": escolha, "motivo": motivo}
    if plano["escolhas"]["pilar"]["valor"] == "Resumo da Semana":
        plano["escolhas"]["tema"] = {"valor": "Resumo da Semana", "motivo": "o resumo cobre vários temas"}
    esc = plano["escolhas"]                    # coerência entre as escolhas
    if esc["humano"]["valor"] == "não" and (esc["gancho"]["valor"] == "Bastidores" or esc["layout"]["valor"] == "foto"):
        esc["humano"] = {"valor": "sim", "motivo": "coerência: gancho Bastidores ou layout foto pedem pessoas reais"}
    if esc["humano"]["valor"] == "sim" and esc["layout"]["valor"] not in ("foto", "video"):
        esc["layout"] = {"valor": "foto", "motivo": "coerência: conteúdo com pessoas pede foto/vídeo real"}

    post = {var: c["valor"] for var, c in plano["escolhas"].items()}
    post["dia"], post["fonte"] = dia, "LIAM"
    esperado, (lo, hi) = modelo.prever(post)
    plano["previsao"] = {"pontos": round(esperado, 1), "ic80": [round(lo, 1), round(hi, 1)],
                         "score": round(100 * esperado / base), "score_ic80": [round(100 * lo / base), round(100 * hi / base)]}
    return plano


# --------------------------------------------------------------------------- concorrentes
GANCHO_REGRAS = [
    ("Pergunta", re.compile(r"\?")),
    ("Bastidores/Evento", re.compile(r"(#tbt|\b(evento|celebr\w*|encontro|colaborador\w*|chegada|"
                                     r"edi[çc][ãa]o|sessions|convite|caf[ée] da manh[ãa]|day)\b)", re.I)),
    ("Notícia", re.compile(r"\b(copom|selic|ipca|pib|fed|juros|infla[çc][ãa]o|decis[ãa]o|divulg\w*|"
                           r"anunci\w*|lei|governo|elei[çc]\w*|receita federal|imposto|tribut\w*|d[óo]lar|"
                           r"ibovespa|recupera[çc][ãa]o judicial)\b", re.I)),
    ("Dado", re.compile(r"(\d+[\.,]?\d*\s?%|r\$\s?\d|\d+\s?(mil|milh\w*|bilh\w*))", re.I)),
    ("Lista", re.compile(r"^\s*\d+\s|\b(passos|dicas|erros|motivos|decis[õo]es|pontos)\b", re.I)),
    ("Depoimento/História", re.compile(r"\b(hist[óo]ria|depoimento|aluno|cliente|escolheu|jornada)\b", re.I)),
    ("Prêmio/Institucional", re.compile(r"\b(pr[êe]mio|reconhec\w*|finalista\w*|marca de|alcan[çc]amos|"
                                        r"lan[çc]amento|incorpora\w*|marco)\b", re.I)),
    ("Humor/Provocação", re.compile(r"(f\*da|kkk|amass|e ainda disseram|ningu[ée]m|sensacional)", re.I)),
]
STOP = set("""a o e é de da do das dos em no na nos nas um uma uns umas para por com sem que se
sua seu suas seus mais menos como mas ou ao aos à às já não sim isso esse essa este esta muito
muita foi ser ter tem são está estão entre sobre quando onde qual quais quem também ainda nosso
nossa nossos nossas você vocês hoje pelo pela pelos pelas cada todo toda todos todas aqui neste
nesta nessa nesse sábado domingo""".split())


def classificar_gancho(texto):
    t = (texto or "")[:110]
    for nome, rx in GANCHO_REGRAS:
        if rx.search(t):
            return nome
    return "Afirmação"


def analisar_concorrentes(rows):
    posts = []
    for r in rows:
        perfil = str(r.get("perfil") or "").strip()
        dt = data_hora(r.get("data"))
        cur, com = numero(r.get("curtidas")), numero(r.get("comentarios"))
        if not perfil or not dt or cur is None:
            continue                     # curtidas ocultas: fora da análise
        local = dt.astimezone(SP)
        posts.append({"perfil": perfil, "proprio": perfil in PROPRIOS, "post_id": r.get("post_id"), "data": dt,
                      "data_sp": local.strftime("%Y-%m-%d %H:%M"), "dia": DIAS[local.weekday()],
                      "faixa": faixa_de(local.hour), "formato": formato_de_tipo(r.get("tipo")),
                      "curtidas": cur, "comentarios": com or 0.0, "views": numero(r.get("views")),
                      "eng": cur + 2 * (com or 0.0), "legenda": (r.get("legenda") or "").strip(),
                      "link": r.get("link"), "gancho": classificar_gancho(r.get("legenda"))})
    if not posts:
        return None
    por_perfil = defaultdict(list)
    for p in posts:
        por_perfil[p["perfil"]].append(p)
    bench = []
    for perfil, ps in por_perfil.items():
        med = statistics.median([p["eng"] for p in ps]) or 1.0
        for p in ps:
            p["indice"] = p["eng"] / med
        datas = sorted(p["data"] for p in ps)
        dias = max((datas[-1] - datas[0]).total_seconds() / 86400, 1.0)
        reels_views = [p["views"] for p in ps if p["formato"] == "Reels" and p["views"]]
        bench.append({"perfil": perfil, "proprio": perfil in PROPRIOS, "posts": len(ps),
                      "posts_semana": round(7 * (len(ps) - 1) / dias, 1) if len(ps) > 1 else None,
                      "mediana_curtidas": statistics.median([p["curtidas"] for p in ps]),
                      "mediana_comentarios": statistics.median([p["comentarios"] for p in ps]),
                      "pct_reels": round(100 * sum(p["formato"] == "Reels" for p in ps) / len(ps)),
                      "mediana_views_reels": statistics.median(reels_views) if reels_views else None})
    bench.sort(key=lambda b: b["mediana_curtidas"], reverse=True)
    concorrentes = [p for p in posts if not p["proprio"]]

    def agrupar(chave):
        g = defaultdict(list)
        for p in concorrentes:
            g[p[chave]].append(p["indice"])
        return sorted(({"valor": k, "n": len(v), "indice_mediano": round(statistics.median(v), 2)}
                       for k, v in g.items() if k and len(v) >= 3), key=lambda x: -x["indice_mediano"])

    top = sorted(posts, key=lambda p: -p["indice"])
    outliers = [p for p in top if p["indice"] >= 1.5][:12] or top[:5]
    palavras = Counter()
    for p in outliers:
        for w in re.findall(r"[a-zà-ú]{5,}", p["legenda"].lower()):
            if w not in STOP:
                palavras[w] += p["indice"]

    def limpar(p):
        return {k: (round(v, 2) if isinstance(v, float) else v) for k, v in p.items() if k != "data"}

    return {"benchmark": bench, "por_formato": agrupar("formato"), "por_gancho": agrupar("gancho"),
            "por_dia": agrupar("dia"), "por_faixa": agrupar("faixa"),
            "outliers": [limpar(p) for p in outliers],
            "palavras_outliers": [w for w, _ in palavras.most_common(12)],
            "posts_analisados": len(posts), "_posts": concorrentes}


MAPA_GANCHO = {"Pergunta": "Pergunta", "Notícia": "Notícia", "Dado": "Dado", "Lista": "Lista",
               "Afirmação": "Afirmação forte", "Bastidores/Evento": "Bastidores"}


def priors_dos_concorrentes(conc, forca=0.5, limite=0.5, n_min=5):
    """Transfere o aprendizado dos concorrentes como ponto de partida (prior) do modelo.
    Usa metade do efeito observado neles (forca), limitado a ×0,6–×1,65, e só com n >= 5."""
    if not conc:
        return {}
    priors = {}

    def registrar(var, valor, indice, n):
        if n >= n_min and indice and indice > 0:
            priors[(var, valor)] = max(-limite, min(limite, forca * math.log(indice)))

    for g in conc["por_formato"]:
        registrar("formato", g["valor"], g["indice_mediano"], g["n"])
    for g in conc["por_gancho"]:
        if g["valor"] in MAPA_GANCHO:
            registrar("gancho", MAPA_GANCHO[g["valor"]], g["indice_mediano"], g["n"])
    pessoas = [p["indice"] for p in conc["_posts"] if p["gancho"] in ("Bastidores/Evento", "Depoimento/História")]
    outros = [p["indice"] for p in conc["_posts"] if p["gancho"] not in ("Bastidores/Evento", "Depoimento/História")]
    if pessoas and outros:
        registrar("humano", "sim", statistics.median(pessoas), len(pessoas))
        registrar("humano", "não", statistics.median(outros), len(outros))
    return priors


# --------------------------------------------------------------------------- relatório
def diagnostico(posts, ref):
    """Comparações brutas (medianas) para leitura rápida; o modelo é que decide."""
    def mediana(ps, chave):
        vals = [p["pontos"] if chave == "pontos" else p["met"].get(chave) for p in ps]
        vals = [v for v in vals if v is not None]
        return statistics.median(vals) if vals else None

    def recentes(dias):
        return [p for p in posts if (ref - p["data"]).days <= dias]

    linhas = []
    liam = [p for p in posts if p["fonte"] == "LIAM"]
    hist = [p for p in recentes(120) if p["fonte"] == "Histórico"]
    if liam and len(hist) >= 2:
        linhas.append(f"- LIAM (n={len(liam)}): {br(mediana(liam, 'pontos'))} pontos e alcance {br(mediana(liam, 'alcance'))} "
                      f"(medianas) vs. posts anteriores dos últimos 120 dias (n={len(hist)}): "
                      f"{br(mediana(hist, 'pontos'))} pontos e alcance {br(mediana(hist, 'alcance'))}.")
    ano = recentes(365)
    for var, rotulo in (("humano", "Com pessoas/bastidores"), ("formato", "Formato")):
        grupos = defaultdict(list)
        for p in ano:
            if p.get(var):
                grupos[p[var]].append(p)
        partes = [f"{v}: {br(mediana(ps, 'pontos'))} pontos, alcance {br(mediana(ps, 'alcance'))} (n={len(ps)})"
                  for v, ps in sorted(grupos.items(), key=lambda kv: -(mediana(kv[1], 'pontos') or 0)) if len(ps) >= 2]
        if len(partes) >= 2:
            linhas.append(f"- {rotulo} (últimos 12 meses): " + "; ".join(partes) + ".")
    return linhas


def tabela(cab, linhas):
    out = ["| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)]
    out += ["| " + " | ".join(str(c) for c in l) + " |" for l in linhas]
    return "\n".join(out)


def relatorio(posts, base, seguidores, modelo, amostras, plano, conc, ref):
    liam = [p for p in posts if p["fonte"] == "LIAM"]
    linhas = [f"# LIAM – relatório de aprendizado ({ref.astimezone(SP):%d/%m/%Y %H:%M})", ""]
    linhas.append(f"- Posts analisados: {len(posts)} (LIAM: {len(liam)}; histórico: {len(posts) - len(liam)}); "
                  f"maduros (≥{MATURIDADE_DIAS} dias de métricas): {sum(p['maduro'] for p in posts)}.")
    linhas.append(f"- Score 100 = mediana dos últimos {JANELA_BASE} posts maduros = {br(base)} pontos.")
    if seguidores:
        txt = f"- Seguidores: {br(seguidores)}."
        alc = [p["met"].get("alcance") for p in liam if p["met"].get("alcance")]
        if alc:
            med = statistics.median(alc)
            txt += f" Alcance mediano dos posts LIAM: {br(med)} ({br(100 * med / seguidores, 2)}% da base)."
        linhas.append(txt)
    if sum(p["maduro"] for p in liam) < 10:
        linhas.append("- **Fase de exploração**: menos de 10 posts LIAM maduros; conclusões ainda são hipóteses.")
    linhas += ["", "## Posts recentes", tabela(
        ["Data (SP)", "Fonte", "Formato", "Alcance", "Curt.", "Coment.", "Salv.", "Compart.", "Pontos", "Score", "Maduro"],
        [[p["data_sp"], p["fonte"], p["formato"] or "–", br(p["met"].get("alcance")), br(p["met"].get("curtidas")),
          br(p["met"].get("comentarios")), br(p["met"].get("salvos")), br(p["met"].get("compart")),
          br(p["pontos"]), p["score"], "sim" if p["maduro"] else "não"] for p in posts[:12]])]
    diag = diagnostico(posts, ref)
    if diag:
        linhas += ["", "## Diagnóstico rápido (medianas brutas)"] + diag

    if modelo:
        linhas += ["", "## O que está funcionando (efeito sobre os pontos, estimado em conjunto)"]
        for var in VARIAVEIS:
            if var in CONTROLES:
                continue
            testados = [(v, modelo.efeito(var, v)) for v in modelo.opcoes(var)]
            testados = [(v, i) for v, i in testados if i["n"] > 0]
            if not testados:
                continue
            pm = modelo.prob_melhor(amostras, var, [v for v, _ in testados])
            testados.sort(key=lambda x: -x[1]["coef"])
            partes = [f"{v} {vezes(i['efeito'])} (IC80% {vezes(i['ic80'][0])}–{vezes(i['ic80'][1])}; "
                      f"n={br(i['n'])}; P(melhor) {pct(pm[v])})" for v, i in testados[:4]]
            nao = [v for v in UNIVERSO[var] if modelo.efeito(var, v)["n"] == 0]
            linhas.append(f"- **{var}**: " + "; ".join(partes) + (f". Ainda não testado: {', '.join(nao)}." if nao else "."))
        epoca = modelo.efeito("fonte", "LIAM")
        if epoca and epoca["n"] > 0:
            linhas.append(f"- _Controle de época_ (fase LIAM vs. histórico, já descontado acima): "
                          f"{vezes(epoca['efeito'])} (IC80% {vezes(epoca['ic80'][0])}–{vezes(epoca['ic80'][1])}).")
        if modelo.priors:
            linhas.append("- _Ponto de partida vindo dos concorrentes_: " + "; ".join(
                f"{var}={v} {vezes(math.exp(c))}" for (var, v), c in sorted(modelo.priors.items())) + ".")

    linhas += ["", f"## Plano sugerido para {plano['data']} ({plano['dia']})",
               f"Grade: {plano['programacao']['formato']} · {plano['programacao']['pilar']}."]
    for var, c in plano["escolhas"].items():
        linhas.append(f"- **{var}**: {c['valor']} — {c['motivo']}")
    if plano.get("previsao"):
        pv = plano["previsao"]
        lo, hi = pv["score_ic80"]
        incerteza = "muito alta (fase de exploração)" if hi > 10 * max(lo, 1) else f"IC80% {lo}–{hi}"
        linhas.append(f"- Score esperado do plano: {pv['score']} (incerteza {incerteza}).")

    if conc:
        linhas += ["", f"## Radar de concorrentes ({conc['posts_analisados']} posts)", tabela(
            ["Perfil", "Posts", "Posts/sem.", "Curtidas (med.)", "Coment. (med.)", "% Reels", "Views Reels (med.)"],
            [[b["perfil"] + (" (próprio)" if b["proprio"] else ""), b["posts"], br(b["posts_semana"]),
              br(b["mediana_curtidas"]), br(b["mediana_comentarios"]), b["pct_reels"], br(b["mediana_views_reels"])]
             for b in conc["benchmark"]])]
        for titulo, chave in (("Formato", "por_formato"), ("Gancho", "por_gancho"),
                              ("Faixa de horário", "por_faixa"), ("Dia", "por_dia")):
            itens = "; ".join(f"{g['valor']} {vezes(g['indice_mediano'])} (n={g['n']})" for g in conc[chave][:5])
            if itens:
                linhas.append(f"- **{titulo}** (índice mediano vs. o próprio perfil): {itens}")
        linhas += ["", "### Posts fora da curva (engajamento ÷ mediana do perfil)"]
        for p in conc["outliers"]:
            linhas.append(f"- {vezes(p['indice'])} · @{p['perfil']}{' (próprio)' if p['proprio'] else ''} · "
                          f"{p['formato']} · {p['data_sp']} · gancho {p['gancho']} · \"{p['legenda'][:100]}\" "
                          f"{p['link'] or ''}")
        if conc["palavras_outliers"]:
            linhas.append(f"- Palavras recorrentes nos destaques: {', '.join(conc['palavras_outliers'])}")
    linhas += ["", "_Método: pontos = 0,05·alcance + curtidas + 2·comentários + 3·salvamentos + 4·compartilhamentos "
               "+ 5·seguidores + 0,5·visitas; regressão bayesiana conjunta em escala log, peso por recência "
               f"(meia-vida {MEIA_VIDA_DIAS} dias), decisão por Thompson sampling._"]
    return "\n".join(linhas) + "\n"


# --------------------------------------------------------------------------- principal
def main():
    ap = argparse.ArgumentParser(description="LIAM – motor de aprendizado do Instagram da Ludo")
    ap.add_argument("--fila", help="JSON da consulta da Fila Instagram")
    ap.add_argument("--metricas", help="JSON da consulta das Métricas Instagram")
    ap.add_argument("--concorrentes", help="JSON da consulta Concorrentes – Posts (opcional)")
    ap.add_argument("--data", help="data do post a planejar (AAAA-MM-DD); padrão: hoje em São Paulo")
    ap.add_argument("--saida", default=str(Path(__file__).parent / "saida"))
    ap.add_argument("--excluir", default=str(Path(__file__).parent / "excluidos.txt"),
                    help="arquivo com IDs de posts fora da análise (testes, duplicados)")
    a = ap.parse_args()

    agora = datetime.now(timezone.utc)
    dia_alvo = date.fromisoformat(a.data) if a.data else agora.astimezone(SP).date()
    excluir = set()
    if a.excluir and Path(a.excluir).exists():
        excluir = {l.split("#")[0].strip() for l in Path(a.excluir).read_text(encoding="utf-8").splitlines()
                   if l.split("#")[0].strip()}
    rng = random.Random(int(dia_alvo.strftime("%Y%m%d")))   # mesmo dia = mesma recomendação

    posts, seguidores = montar_posts(carregar(a.fila), carregar(a.metricas), agora, excluir)
    base = aplicar_score(posts) if posts else 1.0
    conc = analisar_concorrentes(carregar(a.concorrentes)) if a.concorrentes else None
    priors = priors_dos_concorrentes(conc)
    modelo = Modelo(posts, priors) if len(posts) >= 3 else None
    amostras = [modelo.sortear(rng) for _ in range(SORTEIOS)] if modelo else []
    plano = planejar(modelo, amostras, dia_alvo, rng, base)
    if conc:
        conc["priors_aplicados"] = {f"{var}={v}": round(math.exp(c), 2) for (var, v), c in priors.items()}

    out = Path(a.saida)
    out.mkdir(parents=True, exist_ok=True)
    scores = [{"post_id": p["post_id"], "fonte": p["fonte"], "data_sp": p["data_sp"], "formato": p["formato"],
               "score": p["score"], "pontos": round(p["pontos"], 2), "maduro": p["maduro"],
               "idade_medicao_dias": p["idade_medicao"], **{k: p["met"].get(k) for k in CAMPOS}}
              for p in posts]
    (out / "scores.json").write_text(json.dumps(scores, ensure_ascii=False, indent=1), encoding="utf-8")
    efeitos = {}
    if modelo:
        for var in VARIAVEIS:
            efeitos[var] = {v: {k: (round(x, 3) if isinstance(x, float) else [round(y, 3) for y in x]
                                    if isinstance(x, tuple) else x)
                                for k, x in modelo.efeito(var, v).items()} for v in modelo.opcoes(var)}
    conc_json = {k: v for k, v in (conc or {}).items() if not k.startswith("_")} or None
    (out / "recomendacao.json").write_text(json.dumps(
        {"gerado_em": agora.isoformat(), "base_pontos": base, "seguidores": seguidores, "plano": plano,
         "efeitos": efeitos, "concorrentes": conc_json}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    md = relatorio(posts, base, seguidores, modelo, amostras, plano, conc, agora)
    (out / "relatorio.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
