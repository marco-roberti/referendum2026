"""Tests for plot module: plot_loess."""

import pytest

import sondaggi.plot as plot


class TestPlotLoess:
    """plot_loess runs without error and writes file when path given."""

    @pytest.mark.parametrize("frac", [0.3, 0.4, 0.5, 0.8])
    def test_plot_loess_writes_file(self, clean_plot_minimal, tmp_path, frac):
        out = tmp_path / "plot.png"
        plot.plot_loess(clean_plot_minimal, frac=frac, output_path=out)
        assert out.exists()
        if frac == 0.5:
            assert out.stat().st_size > 0
