"""Web perbandingan model library dan Groq. Dipaketkan menjadi deploy_btc/app.py."""

import json
import os
import time
from pathlib import Path

import pandas as pd
import streamlit as st
from groq import APIError, Groq

from classifier_btc import predict_one
from fitur_btc import FEATURES
from web_utils_btc import load_assets, prepare_csv, validate_features

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="Eksperimen BTC/EUR", page_icon="₿", layout="wide")
st.title("Klasifikasi arah harga BTC/EUR")
st.write("Bandingkan Random Forest dan AI model service Groq untuk memprediksi arah harga pada observasi berikutnya.")
st.caption("Input tersedia setelah observasi saat ini selesai. Naik berarti Close berikutnya lebih tinggi; selain itu Tidak Naik.")


@st.cache_resource
def assets():
    return load_assets(ROOT)


try:
    bundle, info, service, comparison = assets()
except (ValueError, OSError, KeyError) as exc:
    st.error(f"Artefak aplikasi belum siap: {exc}")
    st.stop()
cfg = service["config"]
config_json = json.dumps(cfg, sort_keys=True)

with st.sidebar:
    st.header("Model yang digunakan")
    st.write(f"Library: **{info['model_terpilih'].replace('_', ' ')}**")
    st.write(f"AI service: `{cfg['model']}`")
    st.caption(f"Prompt: {cfg['variant']}; fitur historis: {len(FEATURES)}")
    st.link_button("Sumber dataset Kaggle", "https://www.kaggle.com/datasets/hamdinizar/bitcoin")
    st.caption("Dataset historis 2014–2019; bukan harga pasar terkini.")
    with st.expander("Lihat prompt evaluasi"):
        st.code(cfg["system_prompt"], language=None)

with st.expander("Hasil evaluasi kedua pendekatan", expanded=True):
    st.write("Evaluasi terbatas pada 60 sampel test yang sama. Hasil eksperimen ini belum menunjukkan prediksi arah harga yang kuat.")
    shown = comparison.copy()
    for column in ["accuracy", "balanced_accuracy"]:
        shown[column] = (shown[column] * 100).round(2)
    shown["f1_macro"] = shown.f1_macro.round(3)
    st.dataframe(shown.rename(columns={"accuracy": "Accuracy (%)", "balanced_accuracy": "Balanced accuracy (%)"}), hide_index=True)
    st.download_button("Unduh tabel evaluasi", comparison.to_csv(index=False).encode(), "perbandingan_test_60.csv", "text/csv")


def get_key():
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        try:
            key = st.secrets.get("GROQ_API_KEY", "")
        except Exception:
            key = ""
    if not isinstance(key, str) or not key.strip():
        raise ValueError("Isi GROQ_API_KEY di Secrets untuk menggunakan model Groq. Model library tetap dapat digunakan.")
    return key.strip()


@st.cache_resource
def groq_client(key):
    return Groq(api_key=key, timeout=45, max_retries=0)


@st.cache_data(show_spinner=False, max_entries=1000)
def cached_service_prediction(serialized_config, values, _client):
    result = predict_one(_client, json.loads(serialized_config), dict(zip(FEATURES, values)))
    if result["prediksi"] == "invalid":
        raise ValueError("Model Groq tidak mengembalikan label valid. Coba kembali nanti.")
    return result["prediksi"]


def run_predictions(data, method):
    result = data.copy()
    if method in ["Random Forest", "Bandingkan keduanya"]:
        result["prediksi_library"] = bundle["model"].predict(data[FEATURES])
    if method in ["Groq", "Bandingkan keduanya"]:
        client = groq_client(get_key())
        progress = st.progress(0.0)
        labels = []
        for i, (_, row) in enumerate(data.iterrows(), 1):
            labels.append(cached_service_prediction(config_json, tuple(float(row[c]) for c in FEATURES), client))
            progress.progress(i / len(data))
            if i < len(data):
                time.sleep(3)
        result["prediksi_groq"] = labels
    return result


def report_error(exc):
    if isinstance(exc, APIError):
        status = getattr(exc, "status_code", None)
        messages = {429: "Kuota Groq sedang dibatasi. Tunggu sebelum mencoba kembali atau gunakan Random Forest.",
                    401: "API key Groq tidak valid. Periksa pengaturan Secrets.",
                    403: "Akun tidak mempunyai izin untuk model Groq ini.",
                    404: "Model Groq tidak tersedia. Konfigurasi perlu dievaluasi ulang dengan model aktif."}
        st.error(messages.get(status, "Groq belum dapat memproses request. Coba kembali nanti."))
    else:
        st.error(str(exc))


tab_manual, tab_csv, tab_sample = st.tabs(["Input manual", "Prediksi CSV", "Sampel data"])
sample_path = ROOT / "sampel" / "contoh_fitur.csv"
defaults = pd.read_csv(sample_path).iloc[0]
names = {
    "return_1": "Return 1 observasi", "return_3": "Return 3 observasi", "return_7": "Return 7 observasi",
    "volatilitas_7": "Volatilitas 7 observasi", "volatilitas_14": "Volatilitas 14 observasi",
    "rasio_sma_7": "Rasio terhadap SMA 7", "rasio_sma_14": "Rasio terhadap SMA 14",
    "rasio_volume_7": "Rasio volume 7 observasi", "perubahan_log_volume_1": "Perubahan log volume",
}
methods = ["Random Forest", "Groq", "Bandingkan keduanya"]

with tab_manual:
    st.write("Isi fitur historis atau gunakan nilai contoh yang sudah tersedia. Untuk menghitung fitur dari harga dan volume, gunakan tab Prediksi CSV.")
    st.caption("Return dan rasio dalam desimal: 0,01 berarti 1%. Nilai contoh berasal dari data train.")
    with st.form("manual_btc"):
        method = st.selectbox("Metode prediksi", methods)
        columns = st.columns(3)
        values = {}
        for i, feature in enumerate(FEATURES):
            with columns[i % 3]:
                values[feature] = st.number_input(names[feature], value=float(defaults[feature]), format="%.6f", step=0.001)
        submitted = st.form_submit_button("Prediksi arah harga")
    if submitted:
        try:
            data = validate_features(pd.DataFrame([values]))
            with st.spinner("Memproses prediksi..."):
                output = run_predictions(data, method)
            for column in [c for c in output if c.startswith("prediksi_")]:
                st.info(f"{column.replace('prediksi_', '').title()}: **{output[column].iloc[0].replace('_', ' ')}**")
        except (ValueError, APIError) as exc:
            report_error(exc)

with tab_csv:
    st.write("Unggah CSV fitur siap pakai atau riwayat harian dengan kolom Date, Close, Volume. Riwayat memerlukan minimal 15 observasi berurutan.")
    uploaded = st.file_uploader("Pilih CSV", type=["csv"])
    csv_method = st.selectbox("Metode untuk CSV", methods, key="csv_method")
    if uploaded is not None:
        try:
            data, input_type = prepare_csv(pd.read_csv(uploaded))
            st.caption(f"Input dikenali sebagai {input_type}. Tersedia {len(data)} baris fitur.")
            if len(data) > 10:
                st.info("Aplikasi memproses 10 baris terakhir per unggahan untuk menjaga waktu dan kuota.")
            data = data.tail(10)
            st.dataframe(data)
            identity = (uploaded.getvalue(), csv_method, config_json)
            if st.button("Prediksi CSV"):
                st.session_state.pop("btc_csv_output", None)
                with st.spinner("Memproses data..."):
                    output = run_predictions(data, csv_method)
                st.session_state["btc_csv_output"] = (identity, output)
            saved = st.session_state.get("btc_csv_output")
            if saved is not None and saved[0] == identity:
                output = saved[1]
                st.dataframe(output)
                payload = output.to_csv(index=input_type == "riwayat").encode("utf-8")
                st.download_button("Unduh hasil prediksi", payload, "hasil_prediksi_btc.csv", "text/csv")
        except (ValueError, UnicodeError, APIError) as exc:
            report_error(exc)

with tab_sample:
    st.write("Sampel berasal dari periode train dan hanya memuat input, tanpa label atau harga masa depan.")
    for filename, label in [("contoh_fitur.csv", "Unduh sampel fitur siap pakai"),
                            ("contoh_riwayat.csv", "Unduh sampel riwayat harga")]:
        path = ROOT / "sampel" / filename
        st.download_button(label, path.read_bytes(), filename, "text/csv")
    st.write("Alur uji: unduh sampel, buka tab Prediksi CSV, unggah file, pilih metode, lalu klik Prediksi CSV.")
