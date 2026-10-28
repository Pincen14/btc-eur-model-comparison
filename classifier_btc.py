"""Inferensi BTC/EUR yang dipakai bersama saat evaluasi dan deployment."""

import math
import re
import time

from fitur_btc import FEATURES, LABELS

SYSTEM_PROMPT = (
    "Klasifikasikan arah perubahan harga BTC/EUR pada observasi berikutnya, "
    "berdasarkan fitur historis yang tersedia setelah observasi saat ini selesai. "
    "Naik berarti Close berikutnya > Close saat ini; Tidak_Naik berarti selain itu.\n"
    "return_1/3/7 adalah perubahan Close terhadap 1/3/7 observasi sebelumnya. "
    "volatilitas_7/14 adalah standar deviasi return harian pada 7/14 observasi terakhir. "
    "rasio_sma_7/14 adalah Close dibagi rata-rata Close 7/14 observasi terakhir dikurangi 1. "
    "rasio_volume_7 adalah Volume dibagi rata-rata Volume 7 observasi terakhir dikurangi 1. "
    "perubahan_log_volume_1 adalah selisih log(1+Volume) terhadap observasi sebelumnya. "
    "Return dan rasio memakai desimal: 0.01 berarti 1 persen. "
    "Tidak ada aturan bahwa return positif saat ini pasti diikuti kenaikan. "
    "Gunakan pola fitur dan contoh berlabel jika tersedia. "
    "Jangan memakai tanggal, pengetahuan kejadian historis, pencarian web, atau tool. "
    "Jawab HANYA satu label: Naik atau Tidak_Naik. Tanpa penjelasan."
)


def format_features(row):
    values = {name: float(row[name]) for name in FEATURES}
    if not all(math.isfinite(value) for value in values.values()):
        raise ValueError("Fitur harus berupa angka finite.")
    return "; ".join(f"{name}={value:.10g}" for name, value in values.items())


def build_messages(cfg, row):
    messages = [{"role": "system", "content": cfg["system_prompt"]}]
    for example in cfg["few_shot"]:
        messages.extend([{"role": "user", "content": format_features(example["features"])},
                         {"role": "assistant", "content": example["label"]}])
    messages.append({"role": "user", "content": format_features(row)})
    return messages


def predict_one(client, cfg, row):
    options = {}
    if "reasoning_effort" in cfg:
        options["reasoning_effort"] = cfg["reasoning_effort"]
    start = time.perf_counter()
    response = client.chat.completions.create(
        model=cfg["model"], temperature=cfg["temperature"],
        max_completion_tokens=cfg["max_completion_tokens"],
        messages=build_messages(cfg, row), **options,
    )
    content = response.choices[0].message.content or ""
    normalized = re.sub(r"[^a-z]", "", content.lower())
    label_map = {re.sub(r"[^a-z]", "", label.lower()): label for label in LABELS}
    usage = response.usage
    return {"prediksi": label_map.get(normalized, "invalid"),
            "seconds": time.perf_counter() - start,
            "prompt_tokens": usage.prompt_tokens if usage else 0,
            "completion_tokens": usage.completion_tokens if usage else 0,
            "finish_reason": response.choices[0].finish_reason}
