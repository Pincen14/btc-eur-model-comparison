"""Definisi fitur historis untuk training dan aplikasi BTC/EUR."""

import numpy as np
import pandas as pd


FEATURES = [
    "return_1", "return_3", "return_7", "volatilitas_7", "volatilitas_14",
    "rasio_sma_7", "rasio_sma_14", "rasio_volume_7", "perubahan_log_volume_1",
]
LABELS = ["Naik", "Tidak_Naik"]


def historical_features(data):
    """Input harus berurutan naik. Informasi pada t tersedia setelah observasi t selesai."""
    close = data["Close"]
    volume = data["Volume"]
    daily = close.pct_change(fill_method=None)
    result = pd.DataFrame(index=data.index)
    for window in [1, 3, 7]:
        result[f"return_{window}"] = close.pct_change(periods=window, fill_method=None)
    for window in [7, 14]:
        result[f"volatilitas_{window}"] = daily.rolling(window, min_periods=window).std(ddof=0)
        result[f"rasio_sma_{window}"] = close / close.rolling(window, min_periods=window).mean() - 1
    volume_average = volume.rolling(7, min_periods=7).mean().replace(0, np.nan)
    result["rasio_volume_7"] = volume / volume_average - 1
    result["perubahan_log_volume_1"] = np.log1p(volume).diff()
    return result[FEATURES].replace([np.inf, -np.inf], np.nan)
