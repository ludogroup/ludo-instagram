# Linha editorial – Instagram Ludo Group (LIAM)

**LIAM – Ludo Inteligência Artificial de Marketing.** Agente autônomo, sem viés humano, que decide e publica
o conteúdo com base em dados estatísticos dos próprios posts e dos concorrentes, em ciclo PDCA e com
aprendizado contínuo (machine learning). Premissas completas: página "🤖 LIAM – Dados e Aprendizado" no Notion.
Orientações permanentes do usuário: seção "Manual do LIAM" no card DN® / Agentes / LIAM do Notion
(página 82858512ccb183d8b8fb819f4624bf6e). O manual vale acima deste arquivo, exceto compliance e identidade visual.
Motor de aprendizado: `liam/` (Score LIAM, efeitos bayesianos, Thompson sampling, radar de concorrentes).

Referências de padrão: W1 Consultoria e Portfel (wealth/consultoria premium).
Objetivo: autoridade e sofisticação com utilidade. A Ludo fala como um family office, não como uma fintech de varejo.

## Público (regra do usuário, 22/10/2026)
A Ludo não atende só médicos. O conteúdo fala com todos os clientes do grupo: pessoas e famílias que querem
organizar, proteger e fazer crescer o patrimônio (renda familiar acima de R$ 10 mil, a partir dos 30 anos),
profissionais liberais, empresários e empresas (BPO, CFO, contabilidade, crédito, meios de pagamento).
Médicos e profissionais da saúde são um dos segmentos (vertical Ludo Health), não o público único:
- a maioria dos posts fala com o público geral, sem citar profissão;
- post específico para a saúde só quando o tema for próprio do setor (ex.: equiparação hospitalar, PJ médica,
  eventos para médicos), como parte menor do mix (referência: até 1 em cada 4 posts); o LIAM ajusta com dados;
- varie os perfis nos exemplos e casos: família, profissional liberal, empresário, investidor, médico.

## O que é fixo (LIAM não muda)
- Compliance: sem promessa ou projeção de rentabilidade, sem recomendação de investimento específica,
  sem superlativos não comprováveis; regras de CFM, CVM, Anbima e Susep; avisos e temas proibidos da Base.
- Identidade visual (este arquivo + `marca/README.md` + `marca/ludo_templates.py`).
- Verdade: produtos e serviços só como estão na Base de Conhecimento / portfólio institucional; dados só de
  fonte oficial ou veículo de referência, confirmados em 2 fontes.
- Concorrentes: ADAPTAR estratégias vencedoras (tema, formato, gancho, horário, estrutura), NUNCA copiar texto,
  arte, slogan ou imagem.

## O que o LIAM decide (com dados, registrando no PDCA)
Formatos, pilares, temas, ganchos, layouts, horários, mix 80/20, séries,
testes A/B e a própria grade semanal abaixo. Toda mudança relevante vai para o PDCA com a evidência
(Score LIAM, P(melhor), n) e a hipótese seguinte.

## Conteúdo: útil, rico em dados e em evidência
- **Notícia em evidência × Ludo**: partir do que está em alta (mais lidas de Valor, InfoMoney, Bloomberg Línea,
  Folha/Estadão Economia, Google Notícias; posts de concorrentes fora da curva) e cruzar com um produto do
  grupo. Pergunta-guia: "o que isso muda hoje na vida financeira de uma pessoa, família ou empresa?".
- **Entretenimento útil** (o técnico vira prático e leve, sem perder a sobriedade):
  - Analogias do dia a dia: "check-up financeiro", "faxina nas contas", "manutenção preventiva do patrimônio".
    Analogias médicas ("prontuário do patrimônio", "pós-operatório do IR") só em posts para o público da saúde.
  - Mito x Verdade: 1 crença comum, 1 correção com fonte.
  - Números que contam histórias: 1 dado oficial monumental (`numero`) ou série (`grafico`).
  - Séries recorrentes: "Plantão de mercado" (contexto), "Raio-X financeiro" (casos hipotéticos de perfis
    variados: família, profissional liberal, empresário, médico), "Resumo da Semana" (sexta).
  - Bastidores e eventos com pessoas reais (sócios, time, clientes que autorizaram).
- **Humanizar**: fotos e vídeos reais da equipe, catalogados no 🎞️ Banco de mídia (Notion) pela rotina
  "LIAM – Mídias da equipe": fotos tratadas em `fotos/` (layout `foto`) e cortes de vídeo prontos em
  `fotos/cortes/` (Reels legendados, com título, rodapé e capa). Nos dados da conta, posts com pessoas/eventos
  tiveram alcance mediano ~10× maior que as artes recentes (comparação bruta, ainda misturada com a época; o LIAM
  está testando). Sempre que houver material disponível, use.
- Rico em dados: cada post traz ao menos 1 número, regra ou data verificável, com "Fonte: ..." na legenda.

## Estética (obrigatório)
- Usar SEMPRE `marca/ludo_templates.py` (layouts: editorial, pontos, numero, manifesto, grafico, foto; vídeo:
  reel_de_video, só com gravação real; `reel` de artes está desativado desde 26/10/2026). Não criar layouts do zero fora dele. Para reproduzir um padrão visual que funciona
  nos concorrentes (ex.: foto em tela cheia com manchete), o LIAM pode acrescentar um layout novo ao
  `ludo_templates.py`, com a paleta e as fontes da marca, e registrá-lo no PDCA como teste.
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
1. Contexto & Mercado – notícia em evidência → impacto para pessoas, famílias ou empresas → solução do grupo.
2. Estrutura & Patrimônio – holding, sucessão, planejamento tributário, organização societária (Law, A&T, Capital).
3. Proteção – seguros, previdência, reserva, riscos da carreira e da família (Care, People).
4. Gestão da empresa – empresa, escritório, consultório ou clínica: fluxo de caixa, BPO, CFO, meios de pagamento,
   crédito (Company, Pay, CredEx). Até 22/10/2026 chamava-se "Gestão do consultório"; o motor conta os dois como um.
5. Manifesto & Marca – posicionamento, valores, ecossistema.
6. Bastidores & Eventos – pessoas reais, eventos, palestras, feiras, time (fotos e cortes do Banco de mídia).

## Grade semanal (ponto de partida; o LIAM altera quando os dados mostrarem)
| Dia | Formato principal | Pilar sugerido |
|---|---|---|
| Segunda | Carrossel (5 slides) | Contexto & Mercado (notícia da semana → impacto → solução) |
| Terça | Feed (1 arte) | Estrutura & Patrimônio |
| Quarta | Carrossel (5 slides) | Proteção ou Gestão da empresa |
| Quinta | Feed (1 arte) | Gestão da empresa / educativo |
| Sexta | Carrossel "Resumo da Semana" (5 slides) | Contexto & Mercado (4 fatos + fechamento) |
| Sábado | Feed (1 arte) | Manifesto & Marca, Bastidores ou dica rápida |
| Domingo | Feed (manifesto ou reflexão) | Manifesto & Marca |
## Frequência (regra do usuário, 14/10/2026)
- Feed: 2 publicações por dia, em janelas diferentes. Uma de vídeo real da equipe (corte do Banco de mídia,
  dentro do limite por pasta) só quando houver gravação real disponível; a outra alternando entre Feed e
  Carrossel. Sem vídeo real disponível, as duas são Feed e Carrossel (uma de cada).
  A grade acima indica o formato da vaga variada (a grade de 26/10/2026 trocou os Reels por Feed/Carrossel).

## Vídeos: só com gravação real (regra do usuário, 26/10/2026)
- Reels e Stories em vídeo só com gravação real da pasta do Drive "Fotos e Vídeos Luis - LIAM" (cortes do
  🎞️ Banco de mídia ou `reel_de_video` com vídeo real). Sem gravação disponível, não há vídeo naquele dia.
- Proibido por ora: vídeo montado com artes, gráficos, números ou imagens estatísticas em sequência (o antigo
  "Reels de artes", função `reel`) ou com imagens geradas por IA. Esse conteúdo vira Carrossel ou Feed.
- Próxima etapa (ainda não liberada): vídeos do Luis criados com IAs de vídeo. Só quando o usuário liberar no
  Manual do LIAM.
- Stories: 2 por dia, de preferência um para cada post do feed (podem repetir o conteúdo), publicados depois
  do post e em horário diferente dele. Entram na fila todos os dias, mesmo antes do token da Meta: saem
  assim que o token estiver no Make. Publicados pelo cenário "LIAM – Publicador Stories" (Graph API); o
  publicador do feed ignora itens "Story".

## Limite por pasta: até 4–5 fotos e 2–3 vídeos (regra do usuário, 19/10/2026)
Cada pasta da equipe (um evento, palestra, entrevista ou vídeo original = uma subpasta do Drive) rende no
máximo 5 fotos (ideal 4) e 3 cortes de vídeo (ideal 2) no total, somando todos os posts e Stories. Cada foto
de um carrossel conta. Repetir nos Stories o post do próprio dia não conta. Atingido o teto, a pasta está
encerrada: o restante dela vai para "descartado" no Banco de mídia. Exemplo: a pasta da Dengo (O Médico CEO,
26/09) já usou 7 fotos e 2 cortes e foi encerrada em 19/10/2026.

## Imagens no estilo dos concorrentes (regra do usuário, 19/10/2026)
Com pouca foto real disponível, crie imagens e fotos como as dos posts de maior engajamento dos concorrentes e
influenciadores monitorados (📊 Concorrentes – Posts): foto editorial com manchete sobreposta, cenas de
escritório, empresa, casa e família, patrimônio e, quando o post for para a saúde, consultório; capas
fotográficas de carrossel etc. Adaptar o estilo, nunca
copiar a imagem, o texto ou a composição. As fotos geradas por IA (Canva) ficam no Banco de mídia como
"Imagem gerada (IA)": sem texto, sem logotipos, sem pessoas identificáveis e nunca apresentadas como foto real
de evento, cliente ou da equipe. A análise visual das referências fica na página "🎨 Referências visuais".

## Horários (janelas do publicador)
O Make verifica a fila só dentro de 4 janelas (feed e Stories, em cenários separados):
**07h–09h, 12h–14h, 18h–20h, 21h–23h** (America/Sao_Paulo). Ele roda exatamente no início de cada janela
(07:00, 12:00, 18:00, 21:00) e depois de hora em hora até o fim dela. Agende o post 5 minutos antes do
início da janela (06:55, 11:55, 17:55 ou 20:55) para sair na hora cheia, e use a mesma faixa em
"Faixa testada". Fora das janelas o post só sai na janela seguinte.

## Especificações técnicas
- Feed: 1 JPEG 1080x1350 → "Link da imagem".
- Carrossel: SEMPRE 5 JPEGs 1080x1350 (capa `editorial` ou `foto` com swipe=True e page="01/05"; slides 02-04 com
  conteúdo; 05 fechamento `manifesto` ou CTA) → "Link da imagem" (slide 1) + "Slide 2" a "Slide 5".
- Reels de artes (`reel`): desativado desde 26/10/2026 (regra do usuário: vídeo só com gravação real).
- Reels com vídeo real: corte pronto do Banco de mídia, usado como está (Link → "Link do vídeo", Capa → "Link da
  imagem", Layout "video"); ou `reel_de_video("fotos/<video>", "posts/...mp4", title=[...], duracao=...)`.
- Story: 1 JPEG 1080x1920 (set_formato("story"); layouts editorial, numero, foto, manifesto) → "Link da imagem",
  ou vídeo 9:16 de 3 a 60 s, só com gravação real → "Link do vídeo" (+ capa em "Link da imagem"). Formato "Story" na Fila. Sem link,
  enquete ou figurinhas pela API: a arte se explica sozinha (ex.: dado-chave + "post completo no perfil").
- Vídeos: até 18 MB por arquivo (o jsDelivr não serve arquivos acima de 20 MB).
- Reels → "Link do vídeo" (URL jsDelivr com o hash do commit:
  https://cdn.jsdelivr.net/gh/ludogroup/ludo-instagram@<sha>/posts/<arquivo>.mp4); capa = primeiro quadro em JPEG
  → "Link da imagem" (raw GitHub).
- Links de imagens (JPEG): https://raw.githubusercontent.com/ludogroup/ludo-instagram/main/posts/<arquivo>.jpg
- Fila: preencher sempre Pilar, Layout, Gancho, Origem, Tema / empresa, Faixa testada e Teste A/B (hipótese).
  São as variáveis que o LIAM aprende.

## Fotos e vídeos da equipe (pasta do Google Drive → Banco de mídia)
- A equipe coloca fotos e vídeos (inclusive palestras inteiras) na pasta do Google Drive "Fotos e Vídeos Luis - LIAM",
  uma subpasta por evento: `AAMMDD_Evento_Tema` (ex.: `260926_Palestra Dengo_O Médico CEO`). Opcional: um
  `contexto.txt` na subpasta com quem aparece e o que foi o evento. Nomes só entram na legenda se estiverem
  escritos ali ou em 💡 Sugestões Instagram.
- A rotina "LIAM – Mídias da equipe" (11:47 e 17:47, com o Mac ligado e o app Claude aberto) trata o que for novo
  com `liam/midia.py`:
  - fotos: JPEG sem EXIF/GPS em `fotos/`, com foco (rosto), qualidade e descrição; as 5 melhores da pasta entram
    no Banco de mídia como "disponível", as demais como "descartado";
  - vídeos: transcrição (Whisper), no máximo 3 cortes de 20 a 60 s por pasta (ideal 2), Reels 1080x1920 com recorte que
    acompanha o rosto, legendas na identidade Ludo, título e capa em `fotos/cortes/`; cópia dos cortes em
    `_LIAM/cortes` dentro da própria pasta do Drive (a equipe vê o resultado).
- A rotina diária escolhe no Banco de mídia (Status "disponível") e marca o item como "usado" ao agendar o post.
- O repositório é público: só material adequado ao Instagram e com autorização de quem aparece.
  Arquivos anexados no Notion não são lidos pelo LIAM.
