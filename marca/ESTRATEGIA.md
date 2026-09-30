# Linha editorial – Instagram Ludo Group

Referências de padrão: W1 Consultoria e Portfel (wealth/consultoria premium).
Objetivo: autoridade e sofisticação. A Ludo fala como um family office, não como uma fintech de varejo.

## Estética (obrigatório)
- Usar SEMPRE `marca/ludo_templates.py` (layouts: editorial, pontos, numero, manifesto). Não criar layouts do zero.
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

## Pilares (rodízio semanal)
1. Contexto & Mercado – cruzar notícias relevantes (Valor, Bloomberg Línea, Banco Central, Receita,
   Google Notícias) com o impacto para o médico e a solução do grupo. Ex.: juros, dividendos, IR, câmbio.
2. Estrutura & Patrimônio – holding, sucessão, planejamento tributário, organização societária (Law, A&T, Wealth).
3. Proteção – seguros, previdência, reserva, riscos da carreira médica (Care, People).
4. Gestão do consultório/clínica – fluxo de caixa, BPO, CFO, meios de pagamento, crédito (Company, Pay, CredEx).
5. Manifesto & Marca – posicionamento, valores, ecossistema, bastidores e eventos (Institucional).

## Formatos
- `editorial`: capa com tese + parágrafo curto (bom para temas de contexto).
- `pontos`: 3 decisões/erros/perguntas numerados (alto valor de salvamento).
- `numero`: 1 dado oficial monumental (só números confirmados em fonte oficial).
- `manifesto`: frase de posicionamento da marca (1x por semana no máximo).
- Carrossel (quando o Make estiver configurado para carrossel): capa `editorial` + 3-5 `pontos`/`numero` + fechamento `manifesto`.

## Programação semanal (formatos)
| Dia | Formato principal | Pilar sugerido |
|---|---|---|
| Segunda | Carrossel (5 slides) | Contexto & Mercado (notícia da semana → impacto → solução) |
| Terça | Feed (1 arte) | Estrutura & Patrimônio |
| Quarta | Reels (vídeo 9:16, ~12 s) | Proteção ou Gestão do consultório |
| Quinta | Carrossel (5 slides) | Gestão do consultório / educativo |
| Sexta | Carrossel "Resumo da Semana" (5 slides) | Contexto & Mercado (4 fatos + fechamento) |
| Sábado | Reels | Manifesto & Marca ou dica rápida |
| Domingo | Feed (manifesto ou reflexão) | Manifesto & Marca |
Stories: 1 por dia, publicado ~2 h depois do post principal, convidando para ver o post do dia (arte 9:16 com o mesmo título).
O PDCA pode alterar esta grade conforme os resultados.

## Especificações técnicas
- Feed: 1 JPEG 1080x1350 → "Link da imagem".
- Carrossel: SEMPRE 5 JPEGs 1080x1350 (capa `editorial` com swipe=True e page="01/05"; slides 02-04 com conteúdo; 05 fechamento `manifesto` ou CTA) → "Link da imagem" (slide 1) + "Slide 2" a "Slide 5".
- Reels: set_formato("story"); 3 a 5 quadros 1080x1920 → `reel(frames, "posts/...mp4")` → "Link do vídeo" (usar URL jsDelivr com o hash do commit: https://cdn.jsdelivr.net/gh/ludogroup/ludo-instagram@<sha>/posts/<arquivo>.mp4); capa = primeiro quadro em JPEG → "Link da imagem" (raw GitHub).
- Story: set_formato("story"); 1 JPEG 1080x1920 → "Link da imagem". Sem legenda (a API não publica stickers, links nem enquetes em Stories).
- Links de imagens (JPEG): https://raw.githubusercontent.com/ludogroup/ludo-instagram/main/posts/<arquivo>.jpg
