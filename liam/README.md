# LIAM – motor de aprendizado

LIAM (Ludo Inteligência Artificial de Marketing) decide o conteúdo do Instagram com base em dados:
dos próprios posts e dos concorrentes. Este script é a parte "machine learning" do ciclo PDCA.

- **Score LIAM** de cada post: 100 = mediana dos últimos 30 posts próprios maduros (200 = o dobro).
  Pontos = 0,05·alcance + curtidas + 2·comentários + 3·salvamentos + 4·compartilhamentos
  + 5·seguidores ganhos + 0,5·visitas ao perfil.
- **Efeitos**: regressão bayesiana conjunta (formato, pilar, gancho, layout, tema, origem, faixa,
  dia, humano), com peso maior para posts recentes, controle de época (fase LIAM × histórico)
  e ponto de partida vindo dos concorrentes.
- **Decisão**: Thompson sampling (explora o que tem pouca evidência; abandona o que já perdeu).
  Formato e pilar seguem a grade de `marca/ESTRATEGIA.md`, salvo evidência forte
  (P(melhor) ≥ 80% com n ≥ 4).
- **Concorrentes**: índice = engajamento do post ÷ mediana do próprio perfil. Índice alto =
  estratégia vencedora para ADAPTAR (tema, formato, gancho, horário), nunca copiar texto ou arte.

Os dados ficam fora do Git (`liam/dados/` e `liam/saida/` estão no .gitignore; o repositório é público).

## Uso diário (rotina LIAM)

1. Rode as 3 consultas abaixo com a ferramenta de SQL do Notion (`notion-query-data-sources`) e salve
   cada resultado, como veio, em `liam/dados/fila.json`, `liam/dados/metricas.json` e
   `liam/dados/concorrentes.json`.
2. `python3 liam/liam.py --fila liam/dados/fila.json --metricas liam/dados/metricas.json --concorrentes liam/dados/concorrentes.json --data AAAA-MM-DD`
   (`--data` = dia do post que será criado).
3. Leia `liam/saida/relatorio.md` (diagnóstico, efeitos, plano sugerido, radar de concorrentes).
   `liam/saida/scores.json` traz o Score LIAM e as métricas de cada post para gravar na Fila.
4. Posts de teste, duplicados ou publicados por engano: acrescente o ID em `liam/excluidos.txt`.

### Consulta 1 – Fila (características + resultados)
```sql
SELECT "ID do post" AS post_id, "date:Data:start" AS data, Formato AS formato, Pilar AS pilar, Layout AS layout, Gancho AS gancho, Origem AS origem, "Tema / empresa" AS tema, "Faixa testada" AS faixa, "Teste A/B" AS teste_ab, Alcance AS alcance, Curtidas AS curtidas, "Comentários" AS comentarios, Salvamentos AS salvos, Compartilhamentos AS compart, "Seguidores ganhos" AS seguidores, "Visitas ao perfil" AS visitas, "Visualizações" AS views, "date:Métricas em:start" AS metricas_em, "Título" AS titulo, Status AS status FROM "collection://f10340ae-785a-44ea-aca0-6a30fd6523b9" WHERE Status = 'publicado' AND "ID do post" IS NOT NULL
```

### Consulta 2 – Métricas (última coleta de cada post + linha PERFIL com seguidores)
```sql
SELECT m."Post ID" AS post_id, m."date:Data do post:start" AS data_post, m.Tipo AS tipo, m.Curtidas AS curtidas, m."Comentários" AS comentarios, m."Métricas" AS metricas, substr(m.Legenda,1,100) AS legenda, m."date:Coletado em:start" AS coletado FROM "collection://d1d8ac53-e8aa-4d0c-91fb-b0ead7034cdf" m JOIN (SELECT "Post ID" AS pid, MAX("date:Coletado em:start") AS mx FROM "collection://d1d8ac53-e8aa-4d0c-91fb-b0ead7034cdf" GROUP BY "Post ID") x ON m."Post ID" = x.pid AND m."date:Coletado em:start" = x.mx
```

### Consulta 3 – Concorrentes (últimos 60 dias, última coleta de cada post)
```sql
SELECT c.Perfil AS perfil, c."Post ID" AS post_id, c."date:Data:start" AS data, c.Tipo AS tipo, c.Curtidas AS curtidas, c."Comentários" AS comentarios, c."Visualizações" AS views, substr(replace(c.Legenda, char(10), ' '), 1, 110) AS legenda, c.Link AS link FROM "collection://cc55fb12-4ac8-4bc4-bb2d-460eda105553" c JOIN (SELECT "Post ID" AS pid, MAX("date:Coletado em:start") AS mx FROM "collection://cc55fb12-4ac8-4bc4-bb2d-460eda105553" GROUP BY "Post ID") x ON c."Post ID" = x.pid AND c."date:Coletado em:start" = x.mx WHERE c."date:Data:start" >= date('now','-60 days')
```

## De onde vêm os dados

- Cenário Make **"LIAM – Dados (métricas e concorrentes)"**: insights dos posts próprios
  (alcance, curtidas, comentários, salvamentos, compartilhamentos, visualizações) e posts públicos
  dos perfis ativos em 🎯 Perfis monitorados (Business Discovery: curtidas, comentários, views).
  No plano grátis do Make roda 1x por semana (segunda, 05:10); com o plano Core pode ser diário.
- Fila Instagram: características de cada post (preenchidas pela rotina LIAM ao criar o post).

## Limites conhecidos

- Poucos posts = muita incerteza: o relatório avisa "fase de exploração" até haver 10 posts LIAM maduros.
- Concorrentes não têm alcance nem salvamentos (a API não fornece); o índice usa curtidas + 2·comentários.
- "humano" em posts antigos é inferido pela legenda/formato; nos posts LIAM vem do Layout "foto",
  do Gancho "Bastidores" ou do Pilar "Bastidores & Eventos".
