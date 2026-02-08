"""Plot LOESS regression of referendum Sì/No data."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from .loess import loess


def plot_loess(df: pd.DataFrame, frac: float, output_path: Path | None = None) -> None:
    sns.set_style("whitegrid")
    _, ax = plt.subplots(figsize=(12, 6))
    sample_sizes = df.get("sample_size")
    use_w = sample_sizes is not None and not sample_sizes.isna().all()
    weights = sample_sizes if use_w else pd.Series(1.0, index=df.index)

    for col, label, (sc, lc) in [
        ("yes_norm", "Sì", ("green", "darkgreen")),
        ("no_norm", "No", ("red", "darkred")),
    ]:
        sz = 30 + sample_sizes / sample_sizes.max() * 100 if use_w else 50
        ax.scatter(
            df["date"], df[col], alpha=0.4, s=sz, label=f"{label} (raw)", color=sc
        )
        t, vals = loess(df["date"], df[col], frac, weights)
        ax.plot(
            t,
            vals,
            linewidth=2.5,
            label=f"{label} ({'weighted ' if use_w else ''}LOESS, frac={frac:.2f})",
            color=lc,
        )

    ax.set(
        xlabel="Data",
        ylabel="Percentuale normalizzata (%)",
        title="Regressione LOESS dei Sondaggi Referendum 2026\n(Sì e No normalizzati, esclusi astenuti)",
    )
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    (
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        if output_path
        else plt.show()
    )
