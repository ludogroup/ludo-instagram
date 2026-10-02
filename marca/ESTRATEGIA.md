# Linha editorial – Instagram Ludo Group (LIAM)

**LIAM – Ludo Inteligência Artificial de Marketing.** Agente autônomo, sem viés humano, que decide e publica
o conteúdo com base em dados estatísticos dos próprios posts e dos concorrentes, em ciclo PDCA e com
aprendizado contínuo (machine learning). Premissas completas: página "🤖 LIAM – Dados e Aprendizado" no Notion.
Motor de aprendizado: `liam/` (Score LIAM, efeitos bayesianos, Thompson sampling, radar de concorrentes).

Referências de padrão: W1 Consultoria e Portfel (wealth/consultoria premium).
Objetivo: autoridade e sofisticação com utilidade. A Ludo fala como um family office, não como uma fintech de varejo.

## O que é fixo (LIAM não muda)
- Compliance: sem promessa ou projeção de rentabilidade, sem recomendação de investimento específica,
  sem superlativos não comprováveis; regras de CFM, CVM, Anbima e Susep; avisos e temas proibidos da Base.
- Identidade visual (este arquivo + `marca/README.md` + `marca/ludo_templates.py`).
- Verdade: produtos e serviços só como estão na Base de Conhecimento / portfólio institucional; dados só de
  fonte oficial ou veículo de referência, confirmados em 2 fontes.
- Concorrentes: ADAPTAR estratégias vencedoras (tema, formato, gancho, horário, estrutura), NUNCA copiar texto,
  arte, slogan ou imagem.

## O que o LIAM decide (com dados, registrando no PDCA)
Formatos, pilares, temas, ganchos, layouts, horários, frequência (1 a 2 posts/dia), mix 80/20, séries,
testes A/B e a própria grade semanal abaixo. Toda mudança relevante vai para o PDCA com a evidência
(Score LIAM, P(melhor), n) e a hipótese seguinte.

## Conteúdo: útil, rico em dados e em evidência
- **Notícia em evidência × Ludo**: partir do que está em alta (mais lidas de Valor, InfoMoney, Bloomberg Línea,
  Folha/Estadão Economia, Google Notícias; posts de concorrentes fora da curva) e cruzar com um produto do
  grupo. Pergunta-guia: "o que isso muda na vida financeira do médico hoje?".
- **Entretenimento útil** (o técnico vira prático e leve, sem perder a sobriedade):
  - Analogia médica: "check-up financeiro", "prontuário do patrimônio", "triagem da carteira", "pós-operatório do IR".
  - Mito x Verdade: 1 crença comum, 1 correção com fonte.
  - Números que contam histórias: 1 dado oficial monumental (`numero`) ou série (`grafico`).
  - Séries recorrentes: "Plantão de mercado" (contexto), "Prontuário financeiro" (casos hipotéticos de médicos),
    "Resumo da Semana" (sexta).
  - Bastidores e eventos com pessoas reais (sócios, time, clientes que autorizaram).
- **Humanizar**: fotos e vídeos reais da pasta `fotos/` (layout `foto` e `reel_de_video`). Nos dados da conta,
  posts com pessoas/eventos tiveram alcance mediano ~10× maior que as artes recentes (comparação bruta, ainda
  misturada com a época; o LIAM está testando). Sempre que houver material novo, use.
- Rico em dados: cada post traz ao menos 1 número, regra ou data verificável, com "Fonte: ..." na legenda.

## Estética (obrigatório)
- Usar SEMPRE `marca/ludo_templates.py` (layouts: editorial, pontos, numero, manifesto, grafico, foto; vídeos:
  reel e reel_de_video). Não criar layouts do zero.
- Muito respiro. No máximo 1 ideia por arte. Títulos curtos (até ~9 palavras), 1 palavra-chave em *itálico*.
- Nada de emojis nas artes, ícones genéricos, cores fora da paleta, sombras, molduras ou "cara de template".
- Alternar fundos: papel (#f6f4ee) e marinho (#00214d); degradê azul só em manifestos.
- Rodapé assina a empresa responsável pelo tema (ex.: "Ludo Law · Ludo A&T") ou "ludogroup.com.br".

## Tom de voz
- Sóbrio, seguro, preciso. Frases curtas. Vocabulário de gestão patrimonial: estrutura, patrimônio,
  proteção, sucessão, eficiência tributária, governança, longo prazo, decisão.
- Evitar: gírias, exclamações em excesso, "imperdível", "segredo", "fique rico", promessas, superlativos.
- Emojis na legenda: no máximo 1, preferencialmente nenhum.
- Legenda: gancho de 1 linha, 3 a 6 parágrafos curtos, fechamento com convite discreto
  ("Converse com um especialista Ludo pelo direct."), 3 a 5 hashtags sóbrias.

## Pilares
1. Contexto & Mercado – notícia em evidência → impacto para o médico → solução do grupo.
2. Estrutura & Patrimônio – holding, sucessão, planejamento tributário, organização societária (Law, A&T, Capital).
3. Proteção – seguros, previdência, reserva, riscos da carreira médica (Care, People).
4. Gestão do consultório/clínica – fluxo de caixa, BPO, CFO, meios de pagamento, crédito (Company, Pay, CredEx).
5. Manifesto & Marca – posicionamento, valores, ecossistema.
6. Bastidores & Eventos – pessoas reais, eventos, feiras, time (com fotos/vídeos de `fotos/`).

## Grade semanal (ponto de partida; o LIAM altera quando os dados mostrarem)
| Dia | Formato principal | Pilar sugerido |
|---|---|---|
| Segunda | Carrossel (5 slides) | Contexto & Mercado (notícia da semana → impacto → solução) |
| Terça | Feed (1 arte) | Estrutura & Patrimônio |
| Quarta | Reels | Proteção ou Gestão do consultório |
| Quinta | Carrossel (5 slides) | Gestão do consultório / educativo |
| Sexta | Carrossel "Resumo da Semana" (5 slides) | Contexto & Mercado (4 fatos + fechamento) |
| Sábado | Reels | Manifesto & Marca, Bastidores ou dica rápida |
| Domingo | Feed (manifesto ou reflexão) | Manifesto & Marca |
Stories: NÃO entram na fila (o Make não publica Stories; um item "Story" seria publicado no feed por engano).

## Horários (janelas do publicador)
O Make publica só dentro de 4 janelas (economia de operações): **07h–09h59, 12h–13h59, 18h–19h59, 21h–22h59**
(America/Sao_Paulo). Agende o post no início da janela (07:05, 12:05, 18:05 ou 21:05) e use a mesma faixa
em "Faixa testada". Fora das janelas o post só sai na janela seguinte.

## Especificações técnicas
- Feed: 1 JPEG 1080x1350 → "Link da imagem".
- Carrossel: SEMPRE 5 JPEGs 1080x1350 (capa `editorial` ou `foto` com swipe=True e page="01/05"; slides 02-04 com
  conteúdo; 05 fechamento `manifesto` ou CTA) → "Link da imagem" (slide 1) + "Slide 2" a "Slide 5".
- Reels de artes: set_formato("story"); 3 a 5 quadros 1080x1920 → `reel(frames, "posts/...mp4")`.
- Reels com vídeo real: `reel_de_video("fotos/<video>", "posts/...mp4", title=[...], duracao=...)`.
- Reels → "Link do vídeo" (URL jsDelivr com o hash do commit:
  https://cdn.jsdelivr.net/gh/ludogroup/ludo-instagram@<sha>/posts/<arquivo>.mp4); capa = primeiro quadro em JPEG
  → "Link da imagem" (raw GitHub).
- Links de imagens (JPEG): https://raw.githubusercontent.com/ludogroup/ludo-instagram/main/posts/<arquivo>.jpg
- Fila: preencher sempre Pilar, Layout, Gancho, Origem, Tema / empresa, Faixa testada e Teste A/B (hipótese).
  São as variáveis que o LIAM aprende.

## Fotos e vídeos da equipe (`fotos/`)
- A equipe sobe arquivos em github.com/ludogroup/ludo-instagram → pasta `fotos` → "Add file" → "Upload files".
- Nome sugerido: `AAAA-MM-DD-evento-descricao.jpg` (ou .mp4). Contexto do evento: registrar em 💡 Sugestões
  Instagram (Tipo, Detalhes / links) para a legenda usar só o que for informado.
- Fotos anexadas apenas no Notion não podem ser usadas pelo LIAM (o ambiente não baixa anexos do Notion).
