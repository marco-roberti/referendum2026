"""LOESS regression; dense curve on a time grid."""

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d


def lowess(
    x: np.ndarray, y: np.ndarray, weights: np.ndarray, frac: float
) -> np.ndarray:
    n, k = len(x), max(int(frac * len(x)), 2)
    o = np.argsort(x)
    xs, ys, ws = x[o], y[o], weights[o]
    out = np.column_stack([xs, np.empty(n)])
    for i in range(n):
        j = np.argsort(np.abs(xs - xs[i]))[:k]
        x_n, y_n, w_n = xs[j], ys[j], ws[j]
        d = np.abs(x_n - xs[i])
        w = w_n * (
            (1 - np.minimum(d / d.max(), 1) ** 3) ** 3 if d.max() > 0 else np.ones(k)
        )
        if (s := w.sum()) <= 0:
            out[i, 1] = ys[i]
            continue
        x_c = x_n - xs[i]
        wx, wy = (w * x_c).sum() / s, (w * y_n).sum() / s
        wxy, wx2 = (w * x_c * y_n).sum() / s, (w * x_c**2).sum() / s
        out[i, 1] = (
            wy - (wxy - wx * wy) / (wx2 - wx**2) * wx
            if wx2 > 1e-10
            else np.average(y_n, weights=w)
        )
    return out


def loess(
    dates: pd.Series, values: pd.Series, frac: float, weights: pd.Series
) -> tuple[pd.Series, pd.Series]:
    days = (dates - dates.min()).dt.days.values
    days_dense = np.linspace(days.min(), days.max(), len(days) * 5)
    w = weights.fillna(weights.mean()).values
    w = np.where(np.isnan(w), 1.0, w) / np.nanmean(w) * len(w)
    sm = lowess(days, values.values, w, frac)
    xu, idx = np.unique(sm[:, 0], return_index=True)
    yu = sm[idx, 1]
    f = interp1d(xu, yu, kind="cubic", fill_value="extrapolate")
    vals = f(days_dense)
    return dates.min() + pd.to_timedelta(days_dense, unit="D"), pd.Series(vals)
