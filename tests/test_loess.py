"""Tests for loess module: lowess and loess."""

import numpy as np
import pandas as pd
import pytest

import sondaggi.loess as loess


class TestLowess:
    """lowess: weighted local regression."""

    def test_output_shape(self, simple_xy):
        x, y, w = simple_xy
        out = loess.lowess(x, y, w, frac=0.6)
        assert out.shape == (len(x), 2)
        np.testing.assert_array_equal(out[:, 0], x)

    def test_identity_data_smooth_preserved(self, simple_xy):
        x, y, w = simple_xy
        out = loess.lowess(x, y, w, frac=1.0)
        np.testing.assert_allclose(out[:, 1], y, rtol=0.5)

    @pytest.mark.parametrize("frac", [0.4, 0.6, 0.8])
    def test_frac_affects_smooth(self, frac):
        x = np.linspace(0, 10, 20)
        y = np.sin(x) + np.random.randn(20) * 0.1
        w = np.ones(20)
        out = loess.lowess(x, y, w, frac=frac)
        assert out.shape == (20, 2)
        assert np.all(np.isfinite(out[:, 1]))

    def test_weights_change_result(self):
        x = np.array([0.0, 1.0, 2.0])
        y = np.array([0.0, 10.0, 2.0])
        out_uniform = loess.lowess(x, y, np.ones(3), frac=0.67)
        out_heavy_middle = loess.lowess(x, y, np.array([0.1, 2.0, 0.1]), frac=0.67)
        # With heavy weight on middle, middle fit should be closer to 10
        assert out_heavy_middle[1, 1] >= out_uniform[1, 1]

    def test_zero_weight_sum_uses_observed_y(self):
        """When local weight sum is 0, lowess falls back to observed y (lines 21-24)."""
        x = np.array([0.0, 1.0, 2.0])
        y = np.array([1.0, 2.0, 3.0])
        w = np.array([0.0, 0.0, 1.0])  # k=2 nearest to x[0] have weight 0
        out = loess.lowess(x, y, w, frac=0.67)
        assert out.shape == (3, 2)
        assert out[0, 1] == y[0]  # fallback to observed value
        assert np.all(np.isfinite(out[:, 1]))


class TestLoess:
    """loess: dense curve on time grid."""

    def test_returns_two_series(self, loess_result, dates_series):
        t, v = loess_result
        assert hasattr(t, "__len__") and pd.api.types.is_datetime64_any_dtype(t)
        assert isinstance(v, pd.Series)
        assert len(t) == len(v)

    def test_dense_grid_more_points_than_input(self, loess_result, dates_series):
        t, v = loess_result
        assert len(t) >= len(dates_series)
        assert len(v) == len(t)

    def test_dates_span_same_range(self, loess_result, dates_series):
        t, v = loess_result
        assert t.min() == dates_series.min()
        assert t.max() == dates_series.max()

    def test_uniform_weights_acceptable(self, dates_series, values_series):
        weights = pd.Series(1.0, index=dates_series.index)
        t, v = loess.loess(dates_series, values_series, frac=0.5, weights=weights)
        assert len(t) == len(v)
        assert np.all(np.isfinite(v))

    def test_nan_weights_filled(self, dates_series, values_series):
        weights = pd.Series([1.0, np.nan, 1.0, 1.0], index=dates_series.index)
        t, v = loess.loess(dates_series, values_series, frac=0.5, weights=weights)
        assert np.all(np.isfinite(v))
