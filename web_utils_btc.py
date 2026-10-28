"""Validasi input web BTC/EUR dan pemuatan artefak evaluasi."""

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn

from fitur_btc import FEATURES, historical_features


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_assets(root):
    directory = Path(root) / "artefak"
    info = json.loads((directory / "model_info.json").read_text(encoding="utf-8"))
    service = json.loads((directory / "config_groq.json").read_text(encoding="utf-8"))
    if sklearn.__version__ != info["sklearn_version"]:
        raise ValueError(f"Gunakan scikit-learn {info['sklearn_version']} sesuai artefak training.")
    if sha(directory / "model_library.joblib") != info["model_sha256"]:
        raise ValueError("Artefak model library berubah dari hasil evaluasi.")
    if sha(Path(root) / "fitur_btc.py") != info["fitur_code_sha256"]:
        raise ValueError("Definisi fitur berubah dari saat training.")
    context = service["context"]
    if sha(Path(root) / "classifier_btc.py") != context["classifier_sha256"]:
        raise ValueError("Classifier Groq berubah dari saat evaluasi.")
    if context["features_sha256"] != info["fitur_code_sha256"] or context["split_sha256"] != info["split_sha256"]:
        raise ValueError("Sumber data model library dan Groq tidak cocok.")
    config = service["config"]
    digest = hashlib.sha256(json.dumps(config, sort_keys=True, allow_nan=False).encode()).hexdigest()
    if digest != service["config_sha256"] or config["features"] != FEATURES or info["fitur"] != FEATURES:
        raise ValueError("Konfigurasi prediksi berbeda dari hasil evaluasi.")
    bundle = joblib.load(directory / "model_library.joblib")
    return bundle, info, service, pd.read_csv(directory / "perbandingan_test.csv")


def validate_features(data):
    if data.empty or any(c not in data for c in FEATURES):
        raise ValueError("CSV harus berisi sembilan kolom fitur dan minimal satu baris.")
    values = data[FEATURES].apply(pd.to_numeric, errors="coerce")
    if not np.isfinite(values.to_numpy(dtype=float)).all():
        raise ValueError("Semua fitur harus berupa angka terisi dan finite.")
    if values[["volatilitas_7", "volatilitas_14"]].lt(0).any().any():
        raise ValueError("Volatilitas tidak boleh negatif.")
    ratios = ["return_1", "return_3", "return_7", "rasio_sma_7", "rasio_sma_14", "rasio_volume_7"]
    if values[ratios].lt(-1).any().any():
        raise ValueError("Return dan rasio tidak boleh kurang dari -1.")
    return values


def prepare_csv(data):
    if all(c in data for c in FEATURES):
        return validate_features(data), "fitur"
    if all(c in data for c in ["Date", "Close", "Volume"]):
        history = data[["Date", "Close", "Volume"]].copy()
        history["Date"] = pd.to_datetime(history.Date, format="%Y-%m-%d", errors="coerce")
        history[["Close", "Volume"]] = history[["Close", "Volume"]].apply(pd.to_numeric, errors="coerce")
        if history.isna().any().any() or not np.isfinite(history[["Close", "Volume"]].to_numpy()).all():
            raise ValueError("Riwayat harus mempunyai tanggal YYYY-MM-DD dan angka Close/Volume yang valid.")
        if history.Date.duplicated().any() or not history.Date.is_monotonic_increasing:
            raise ValueError("Tanggal riwayat harus unik dan berurutan dari paling lama.")
        if history.Close.le(0).any() or history.Volume.lt(0).any():
            raise ValueError("Close harus positif dan Volume tidak boleh negatif.")
        if not history.Date.diff().dropna().dt.total_seconds().eq(86400.0).all():
            raise ValueError("Riwayat harus berisi tanggal harian berurutan tanpa hari yang hilang.")
        if len(history) < 15:
            raise ValueError("Unggah minimal 15 observasi harian untuk menghitung fitur historis.")
        features = historical_features(history)
        valid = features.notna().all(axis=1)
        values = validate_features(features.loc[valid])
        values.index = history.loc[valid, "Date"].dt.strftime("%Y-%m-%d")
        values.index.name = "Date"
        return values, "riwayat"
    raise ValueError("Gunakan CSV fitur siap pakai, atau riwayat dengan kolom Date, Close, Volume.")
