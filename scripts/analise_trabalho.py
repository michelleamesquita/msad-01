#!/usr/bin/env python3
"""
MSAD 2026.1 - Primeiro Trabalho
Caracterização estatística: Bellcore e Silence of the Lambs
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import (
    expon,
    gamma,
    kurtosis,
    lognorm,
    norm,
    pareto,
    skew,
    weibull_min,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIG = ROOT / "figures"
RESULTS = ROOT / "results"
FIG.mkdir(parents=True, exist_ok=True)
RESULTS.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))


def basic_stats(x: np.ndarray) -> dict:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    return {
        "n": int(x.size),
        "media": float(np.mean(x)),
        "variancia": float(np.var(x, ddof=1)) if x.size > 1 else 0.0,
        "desvio_padrao": float(np.std(x, ddof=1)) if x.size > 1 else 0.0,
        "min": float(np.min(x)),
        "max": float(np.max(x)),
        "mediana": float(np.median(x)),
        "skewness": float(skew(x, bias=False)) if x.size > 2 else float("nan"),
        "kurtosis": float(kurtosis(x, fisher=False, bias=False)) if x.size > 3 else float("nan"),
    }


def plot_histogram_cdf(x: np.ndarray, title: str, prefix: str) -> None:
    x = np.asarray(x, dtype=float)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].hist(x, bins=80, density=True, alpha=0.75, edgecolor="black", linewidth=0.3)
    axes[0].set_title(f"Histograma — {title}")
    axes[0].set_xlabel("Tamanho (bytes)")
    axes[0].set_ylabel("Densidade")
    sorted_x = np.sort(x)
    cdf = np.arange(1, len(sorted_x) + 1) / len(sorted_x)
    axes[1].plot(sorted_x, cdf, linewidth=1)
    axes[1].set_title(f"CDF — {title}")
    axes[1].set_xlabel("Tamanho (bytes)")
    axes[1].set_ylabel("F(x)")
    plt.tight_layout()
    fig.savefig(FIG / f"{prefix}_hist_cdf.png", dpi=150)
    plt.close(fig)


def fit_distributions(x: np.ndarray, name: str) -> list[dict]:
    """Ajuste MLE e comparação por AIC/KS para distribuições comuns."""
    x = np.asarray(x, dtype=float)
    x = x[x > 0]
    if x.size < 50:
        return []

    candidates = []

    def add(dist_name: str, dist, params, n_params: int):
        try:
            loglik = np.sum(dist.logpdf(x, *params))
            aic = 2 * n_params - 2 * loglik
            ks_stat, ks_p = stats.kstest(x, dist.cdf, args=params)
            candidates.append(
                {
                    "sequencia": name,
                    "distribuicao": dist_name,
                    "params": [float(p) for p in params],
                    "aic": float(aic),
                    "ks_stat": float(ks_stat),
                    "ks_pvalue": float(ks_p),
                }
            )
        except Exception:
            pass

    # Normal (pode falhar em dados positivos assimétricos — ainda útil como baseline)
    mu, sigma = norm.fit(x)
    add("normal", norm, (mu, sigma), 2)

    # Lognormal
    shape, loc, scale = lognorm.fit(x, floc=0)
    add("lognormal", lognorm, (shape, loc, scale), 3)

    # Exponencial
    loc, scale = expon.fit(x, floc=0)
    add("exponencial", expon, (loc, scale), 2)

    # Gamma
    a, loc, scale = gamma.fit(x, floc=0)
    add("gamma", gamma, (a, loc, scale), 3)

    # Weibull
    c, loc, scale = weibull_min.fit(x, floc=0)
    add("weibull", weibull_min, (c, loc, scale), 3)

    # Pareto (tipo I, com loc=0)
    b, loc, scale = pareto.fit(x, floc=0)
    add("pareto", pareto, (b, loc, scale), 3)

    candidates.sort(key=lambda d: d["aic"])
    return candidates


def plot_ccdf_loglog(x: np.ndarray, title: str, prefix: str) -> None:
    x = np.sort(np.asarray(x, dtype=float))
    x = x[x > 0]
    n = len(x)
    ccdf = 1.0 - (np.arange(1, n + 1) / n)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.loglog(x, ccdf, ".", markersize=1, alpha=0.6)
    ax.set_title(f"CCDF (log-log) — {title}")
    ax.set_xlabel("Tamanho (bytes)")
    ax.set_ylabel("P(X > x)")
    ax.grid(True, which="both", alpha=0.3)
    plt.tight_layout()
    fig.savefig(FIG / f"{prefix}_ccdf.png", dpi=150)
    plt.close(fig)


def autocorrelation(x: np.ndarray, max_lag: int | None = None) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    x = x - np.mean(x)
    n = len(x)
    if max_lag is None:
        max_lag = min(500, n // 10)
    acf = np.correlate(x, x, mode="full")
    acf = acf[n - 1 : n + max_lag] / acf[n - 1]
    return acf


def plot_acf(acf: np.ndarray, title: str, prefix: str) -> None:
    lags = np.arange(len(acf))
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(lags, acf, linewidth=0.8)
    ax.axhline(0, color="gray", linewidth=0.5)
    ax.set_xlim(0, len(acf) - 1)
    ax.set_title(f"Autocorrelação — {title}")
    ax.set_xlabel("Lag")
    ax.set_ylabel("ACF")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fig.savefig(FIG / f"{prefix}_acf.png", dpi=150)
    plt.close(fig)


def aggregate_bellcore(times: np.ndarray, sizes: np.ndarray, interval_s: float) -> tuple[np.ndarray, np.ndarray]:
    """Agrega por intervalo: tamanho médio e contagem de pacotes por bin."""
    t0 = times.min()
    bin_id = np.floor((times - t0) / interval_s).astype(np.int64)
    df = pd.DataFrame({"bin": bin_id, "size": sizes})
    agg = df.groupby("bin").agg(mean_size=("size", "mean"), count=("size", "count"))
    return agg["mean_size"].to_numpy(), agg["count"].to_numpy()


def analyze_bellcore() -> dict:
    print("Carregando Bellcore...")
    path = DATA / "Bellcore_data.txt"
    data = np.loadtxt(path)
    times = data[:, 0]
    sizes = data[:, 1]

    out: dict = {"nome": "Bellcore", "tarefas": {}}

    # (a) Original
    stats_orig = basic_stats(sizes)
    out["tarefas"]["a_original"] = stats_orig
    plot_histogram_cdf(sizes, "Bellcore — pacotes (original)", "bellcore_original")
    print("  (a) original OK")

    # (b) Agregações
    mean_100ms, count_100ms = aggregate_bellcore(times, sizes, 0.1)
    mean_1s, count_1s = aggregate_bellcore(times, sizes, 1.0)
    out["tarefas"]["b_agregacao"] = {
        "100ms": {"n_intervalos": len(mean_100ms), "mean_size_stats": basic_stats(mean_100ms), "count_stats": basic_stats(count_100ms)},
        "1s": {"n_intervalos": len(mean_1s), "mean_size_stats": basic_stats(mean_1s), "count_stats": basic_stats(count_1s)},
    }

    # (c) Stats agregações (tamanho médio por intervalo)
    stats_100 = basic_stats(mean_100ms)
    stats_1s = basic_stats(mean_1s)
    out["tarefas"]["c_comparacao"] = {"original": stats_orig, "100ms_mean": stats_100, "1s_mean": stats_1s}
    plot_histogram_cdf(mean_100ms, "Bellcore — tamanho médio (100 ms)", "bellcore_100ms")
    plot_histogram_cdf(mean_1s, "Bellcore — tamanho médio (1 s)", "bellcore_1s")
    print("  (b)(c) agregações OK")

    # (d) Skewness / kurtosis
    out["tarefas"]["d_momentos"] = {
        "original": {"skewness": stats_orig["skewness"], "kurtosis": stats_orig["kurtosis"]},
        "100ms": {"skewness": stats_100["skewness"], "kurtosis": stats_100["kurtosis"]},
        "1s": {"skewness": stats_1s["skewness"], "kurtosis": stats_1s["kurtosis"]},
    }

    # (e) Ajuste de distribuições
    fits = {
        "original": fit_distributions(sizes, "original")[:5],
        "100ms": fit_distributions(mean_100ms, "100ms")[:5],
        "1s": fit_distributions(mean_1s, "1s")[:5],
    }
    out["tarefas"]["e_distribuicoes"] = fits
    print("  (d)(e) momentos e fits OK")

    # (f) CCDF
    plot_ccdf_loglog(sizes, "Bellcore — original", "bellcore_original")
    plot_ccdf_loglog(mean_100ms, "Bellcore — 100 ms", "bellcore_100ms")
    plot_ccdf_loglog(mean_1s, "Bellcore — 1 s", "bellcore_1s")

    fig, ax = plt.subplots(figsize=(6, 5))
    for arr, lab in [(sizes, "original"), (mean_100ms, "100 ms"), (mean_1s, "1 s")]:
        xs = np.sort(arr[arr > 0])
        ccdf = 1 - np.arange(1, len(xs) + 1) / len(xs)
        ax.loglog(xs, ccdf, ".", markersize=0.5, alpha=0.5, label=lab)
    ax.legend()
    ax.set_title("Bellcore — CCDF comparativa")
    ax.set_xlabel("Tamanho (bytes)")
    ax.set_ylabel("P(X > x)")
    ax.grid(True, which="both", alpha=0.3)
    plt.tight_layout()
    fig.savefig(FIG / "bellcore_ccdf_comparativo.png", dpi=150)
    plt.close(fig)
    print("  (f) CCDF OK")

    # (g) ACF
    max_lag = 300
    acf_orig = autocorrelation(sizes, max_lag)
    acf_100 = autocorrelation(mean_100ms, max_lag)
    acf_1s = autocorrelation(mean_1s, max_lag)
    plot_acf(acf_orig, "Bellcore — original", "bellcore_original")
    plot_acf(acf_100, "Bellcore — 100 ms", "bellcore_100ms")
    plot_acf(acf_1s, "Bellcore — 1 s", "bellcore_1s")

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(acf_orig[:200], label="original", alpha=0.8)
    ax.plot(acf_100[:200], label="100 ms", alpha=0.8)
    ax.plot(acf_1s[:200], label="1 s", alpha=0.8)
    ax.legend()
    ax.set_title("Bellcore — ACF comparativa (lags 0–199)")
    ax.set_xlabel("Lag")
    ax.set_ylabel("ACF")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fig.savefig(FIG / "bellcore_acf_comparativo.png", dpi=150)
    plt.close(fig)

    out["tarefas"]["g_acf"] = {
        "max_lag": max_lag,
        "original_lag50": float(acf_orig[50]) if len(acf_orig) > 50 else None,
        "100ms_lag50": float(acf_100[50]) if len(acf_100) > 50 else None,
        "1s_lag50": float(acf_1s[50]) if len(acf_1s) > 50 else None,
    }
    print("  (g) ACF OK")

    return out


def load_movie_trace() -> pd.DataFrame:
    path = DATA / "Silence_of_the_Lambs_movietrace_data.txt"
    df = pd.read_csv(
        path,
        sep=r"\s+",
        header=None,
        usecols=[0, 1, 2, 3],
        names=["display_seq", "display_time", "frame_type", "size"],
    )
    df["frame_type"] = df["frame_type"].astype(str).str.upper()
    return df


def analyze_movie() -> dict:
    print("Carregando Silence of the Lambs...")
    df = load_movie_trace()
    out: dict = {"nome": "Silence of the Lambs", "tarefas": {}}

    # (a) Stats por tipo
    stats_by_type = {}
    for ft in ["I", "P", "B"]:
        x = df.loc[df["frame_type"] == ft, "size"].to_numpy()
        stats_by_type[ft] = basic_stats(x)
        plot_histogram_cdf(x, f"Frames {ft}", f"movie_{ft}")
    all_sizes = df["size"].to_numpy()
    stats_by_type["ALL"] = basic_stats(all_sizes)
    plot_histogram_cdf(all_sizes, "Todos os frames", "movie_ALL")
    out["tarefas"]["a_estatisticas"] = stats_by_type
    print("  (a) estatísticas OK")

    # (b) Distribuições
    fits = {}
    for key in ["I", "P", "B", "ALL"]:
        x = df["size"].to_numpy() if key == "ALL" else df.loc[df["frame_type"] == key, "size"].to_numpy()
        fits[key] = fit_distributions(x, key)[:5]
    out["tarefas"]["b_distribuicoes"] = fits
    print("  (b) distribuições OK")

    # (c) CCDF
    for key in ["I", "P", "B", "ALL"]:
        x = df["size"].to_numpy() if key == "ALL" else df.loc[df["frame_type"] == key, "size"].to_numpy()
        plot_ccdf_loglog(x, f"Frames {key}", f"movie_{key}")

    fig, ax = plt.subplots(figsize=(6, 5))
    for key, lab in [("I", "I"), ("P", "P"), ("B", "B"), ("ALL", "todos")]:
        x = df["size"].to_numpy() if key == "ALL" else df.loc[df["frame_type"] == key, "size"].to_numpy()
        xs = np.sort(x[x > 0])
        ccdf = 1 - np.arange(1, len(xs) + 1) / len(xs)
        ax.loglog(xs, ccdf, ".", markersize=0.5, alpha=0.5, label=lab)
    ax.legend()
    ax.set_title("Movie trace — CCDF comparativa")
    ax.set_xlabel("Tamanho (bytes)")
    ax.set_ylabel("P(X > x)")
    ax.grid(True, which="both", alpha=0.3)
    plt.tight_layout()
    fig.savefig(FIG / "movie_ccdf_comparativo.png", dpi=150)
    plt.close(fig)
    print("  (c) CCDF OK")

    # (d) ACF transmissão vs exibição
    tx_sizes = df["size"].to_numpy()
    display_df = df.sort_values(["display_seq", "display_time"])
    disp_sizes = display_df["size"].to_numpy()

    max_lag = 300
    acf_tx = autocorrelation(tx_sizes, max_lag)
    acf_disp = autocorrelation(disp_sizes, max_lag)
    plot_acf(acf_tx, "Transmissão", "movie_transmissao")
    plot_acf(acf_disp, "Exibição", "movie_exibicao")

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(acf_tx[:200], label="transmissão", alpha=0.8)
    ax.plot(acf_disp[:200], label="exibição", alpha=0.8)
    ax.legend()
    ax.set_title("Movie — ACF transmissão vs exibição")
    ax.set_xlabel("Lag")
    ax.set_ylabel("ACF")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fig.savefig(FIG / "movie_acf_comparativo.png", dpi=150)
    plt.close(fig)

    out["tarefas"]["d_acf"] = {
        "transmissao_lag50": float(acf_tx[50]),
        "exibicao_lag50": float(acf_disp[50]),
        "transmissao_lag100": float(acf_tx[100]),
        "exibicao_lag100": float(acf_disp[100]),
    }
    print("  (d) ACF OK")

    return out


def main() -> None:
    bellcore = analyze_bellcore()
    movie = analyze_movie()
    combined = {"bellcore": bellcore, "movie": movie}
    out_path = RESULTS / "metricas.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)
    print(f"Métricas salvas em {out_path}")
    print(f"Figuras em {FIG}")


if __name__ == "__main__":
    main()
