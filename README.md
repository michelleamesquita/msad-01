# MSAD 2026.1 — Primeiro Trabalho

Caracterização estatística de séries temporais: trace **Bellcore** (Ethernet) e trace **Silence of the Lambs** (MPEG).

## Conteúdo

| Arquivo / pasta | Descrição |
|-----------------|-----------|
| [`RESPOSTAS.md`](RESPOSTAS.md) | Relatório com todas as respostas, tabelas e figuras |
| [`scripts/analise_trabalho.py`](scripts/analise_trabalho.py) | Script principal da análise |
| [`notebooks/trabalho_msad.ipynb`](notebooks/trabalho_msad.ipynb) | Notebook Jupyter (mesma análise) |
| `data/` | Traces de entrada |
| `figures/` | Gráficos gerados (PNG) |
| `results/metricas.json` | Métricas numéricas em JSON |

## Requisitos

- Python 3.10+
- Dependências: `numpy`, `pandas`, `matplotlib`, `scipy`

```bash
pip install -r requirements.txt
```

## Como executar

```bash
cd /Users/mac/Documents/msad-01
export MPLCONFIGDIR=.matplotlib
python3 scripts/analise_trabalho.py
```

Isso gera/atualiza:

- `figures/*.png` — histogramas, CDF, CCDF (log–log), ACF
- `results/metricas.json` — estatísticas e ajustes de distribuição

## Notebook

```bash
jupyter notebook notebooks/trabalho_msad.ipynb
```

Ou abra o notebook no VS Code / Cursor.

## Dados

Os arquivos em `data/` foram copiados dos traces originais:

- `Bellcore_data.txt` — `<tempo (s)> <tamanho (bytes)>`
- `Silence_of_the_Lambs_movietrace_data.txt` — frames MPEG (colunas 0–3)

## Leitura dos resultados

Abra [`RESPOSTAS.md`](RESPOSTAS.md) no preview do editor para ver o relatório completo com imagens embutidas.
