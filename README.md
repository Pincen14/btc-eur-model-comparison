# Klasifikasi arah harga BTC EUR

Aplikasi Streamlit untuk membandingkan Random Forest dan Qwen melalui Groq dalam memprediksi arah harga pada observasi berikutnya. Input berupa sembilan fitur historis atau riwayat harian Date, Close, Volume. Tersedia input manual, unggah CSV, sampel siap unduh, unduh hasil prediksi, dan tabel evaluasi.

Repository: [Pincen14/btc-eur-model-comparison](https://github.com/Pincen14/btc-eur-model-comparison).

## Hasil pada 60 sampel test yang sama

| Pendekatan | Accuracy | Balanced accuracy | F1 macro |
|---|---:|---:|---:|
| Random Forest | 60,00% | 56,11% | 0,538 |
| Baseline mayoritas | 56,67% | 50,00% | 0,362 |
| Groq Qwen 3.8 27B | 41,67% | 48,08% | 0,294 |

Ini adalah evaluasi terbatas. Groq berada di bawah baseline pada sampel ini, dan hasil belum membuktikan prediksi arah harga yang kuat. Aplikasi menyajikan eksperimen secara transparan; status sudah dievaluasi bukan klaim lolos gerbang kualitas Modul 2B. [Draf laporan](LAPORAN.md) menjelaskan metode dan batas interpretasi.

## Jalankan lokal

Gunakan Python 3.13 dan versi dependensi pada requirements.txt agar sesuai lingkungan artefak model.

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.port 8502
```

Buka http://localhost:8502. Random Forest dapat digunakan tanpa API key. Untuk Groq, buat `.streamlit/secrets.toml` lokal berdasarkan contoh `.streamlit/secrets.toml.example`, lalu isi key milik sendiri. File secrets asli dikecualikan dari Git. Pemanggilan API hanya dilakukan setelah pengguna memilih Groq dan menekan tombol prediksi; hasil sukses dicache.

## Deployment

Gunakan Streamlit Community Cloud dengan repository `Pincen14/btc-eur-model-comparison`, branch `main`, main file `app.py`, dan Python 3.13. Isi `GROQ_API_KEY` melalui Advanced settings > Secrets. Langkah lengkap dan pemeriksaan publik tersedia di [panduan deployment](DEPLOY.md).

Status: uji lokal dilaporkan berhasil oleh pengguna pada 29 Oktober 2026. URL deployment publik belum dicatat; jangan mengganti status ini menjadi sudah deploy sebelum aplikasi publik diuji.

## Struktur paket

- `app.py`: antarmuka Streamlit.
- `fitur_btc.py`: definisi sembilan fitur historis yang sama dengan training.
- `classifier_btc.py`: inferensi Groq yang sama dengan evaluasi.
- `web_utils_btc.py`: validasi input dan pemeriksaan konsistensi artefak.
- `artefak/`: model library, metadata, konfigurasi Groq, dan hasil perbandingan test.
- `sampel/`: contoh fitur serta riwayat dari periode train, tanpa target masa depan.

Model library diperiksa melalui hash serta versi scikit-learn. Konfigurasi, fitur, dan classifier Groq diperiksa terhadap metadata evaluasi. Jangan mengubah prompt, model, atau definisi fitur lalu menganggap skor evaluasi sebelumnya tetap berlaku.

## Data dan metode

Sumber yang diberikan pengguna: [bitcoin di Kaggle, akun hamdinizar](https://www.kaggle.com/datasets/hamdinizar/bitcoin). Dataset lokal berisi 1.877 observasi dari 17 September 2014 sampai 6 November 2019. Deskripsi penyedia asli dan lisensi perlu dirujuk ke halaman Kaggle; repository ini tidak menetapkan lisensi baru atas data tersebut.

Target `Naik` berarti Close berikutnya lebih tinggi; `Tidak_Naik` mencakup harga sama atau turun. Input tersedia setelah observasi saat ini selesai. Return dan rasio menggunakan desimal, misalnya 0,01 untuk 1%. Sampel fitur berisi lima input, sedangkan sampel riwayat berisi 30 observasi harian. Unggahan riwayat membutuhkan minimal 15 observasi berurutan; maksimal 10 baris fitur terakhir diprediksi per unggahan.
