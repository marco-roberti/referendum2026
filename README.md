# Referendum 2026 — Sondaggi

**Italian referendum 2026 polling:** fetch poll tables from Wikipedia, clean the data (Italian locale, optional merge by date), and plot LOESS curves for Sì/No.

## Running

### Install

```bash
conda env create -f environment.yml
conda activate referendum2026
```

### Run

From the project root:

```bash
python -m sondaggi [options]
```

Options:

- `--frac FLOAT` – LOESS smoothing fraction (default: 0.4)
- `-o`, `--output PATH` – output plot path (default: show interactively)
- `--merge` – merge polls on the same date

Example:

```bash
python -m sondaggi --frac 0.5 -o plot.png
```

This downloads the table from Wikipedia, writes `sondaggi.csv` and `sondaggi_clean.csv`, and saves the plot.

The image currently on [Wikipedia](https://commons.wikimedia.org/wiki/File:Sondaggi_referendum_costituzionale_italiano_2026_-_weighted_LOESS.png) has been generated with:

```bash
python -m sondaggi --frac .5 -o referendum2026-lowess-YYYYMMDD.png
```

---

## Developing

Activate the conda env, then use the Makefile:

```bash
conda activate referendum2026
```

| Command | Action |
|---------|--------|
| `make all` | Format, lint, test (run everything) |
| `make test` | Tests with coverage (terminal + `htmlcov/`); omits `sondaggi/__main__.py` |
| `make lint` | Ruff check |
| `make format` | Ruff format |
| `make clean` | Remove caches and coverage data |

**Project layout:** `sondaggi/` (data, fetch, loess, plot, __main__), `tests/`
