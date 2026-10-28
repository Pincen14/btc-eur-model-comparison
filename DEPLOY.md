# Deployment Streamlit Community Cloud

Paket web sudah diuji lokal oleh pengguna. Dokumen ini memandu tahap GitHub dan deployment publik tanpa mengulang training atau evaluasi API.

## Pengaturan aplikasi

| Pengaturan | Nilai |
|---|---|
| Repository | Pincen14/btc-eur-model-comparison |
| Branch | main |
| Main file path | app.py |
| Python version | 3.13 |
| API key | GROQ_API_KEY melalui Secrets |

1. Buka https://share.streamlit.io dan login dengan akun yang dapat mengakses repository tersebut.
2. Pilih Create app, lalu aplikasi dari repository GitHub yang sudah ada.
3. Isi repository, branch, dan main file sesuai tabel. Folder deploy_btc di komputer sudah menjadi root repository, jadi main file adalah app.py.
4. Buka Advanced settings, pilih Python 3.13 agar sesuai lingkungan training, dan isi Secrets dengan GROQ_API_KEY milik sendiri. Contoh format tersedia di `.streamlit/secrets.toml.example`. Masukkan nilai asli hanya di pengaturan Streamlit, bukan di GitHub atau percakapan.
5. Simpan pengaturan dan mulai Deploy. Amati build log sampai aplikasi dapat dibuka.
6. Catat URL `https://...streamlit.app` yang benar-benar diberikan Streamlit. URL localhost atau URL repository bukan URL deployment aplikasi.

## Uji setelah deployment

- Buka URL dari jendela browser tanpa sesi login, sesuai pengaturan akses aplikasi yang dimaksudkan.
- Pastikan tabel evaluasi menampilkan perbandingan pada 60 sampel test.
- Coba input manual menggunakan Random Forest.
- Coba satu prediksi Groq untuk memastikan Secrets berfungsi. Ini memakai kuota API.
- Unduh kedua sampel, unggah kembali, lalu unduh hasil prediksi.
- Simpan screenshot halaman, hasil dua metode, sampel unduhan, dan URL publik untuk laporan.

## Jika terjadi kendala

- `No module named ...`: periksa apakah requirements.txt berada di root dan berhasil dipasang.
- Versi scikit-learn berbeda: pertahankan versi 1.9.1 pada requirements.txt; jangan mengganti versi sembarang untuk memuat artefak lama.
- Artefak/hash tidak cocok: gunakan file asli dari paket yang telah diuji, tanpa mengubah classifier atau fitur.
- GROQ_API_KEY tidak ditemukan: isi menu Secrets di Streamlit Cloud. Model library tetap tersedia tanpa key.
- Groq 429: kuota akun sedang dibatasi. Uji library terlebih dahulu dan coba Groq setelah kuota pulih. Kegagalan kuota tidak berarti training harus diulang.

## Status untuk pengumpulan

URL publik belum tersedia pada saat panduan ini dibuat, 29 Oktober 2026. Isi URL nyata dan catatan hasil uji setelah deployment selesai. Uji lokal dan pengujian kode tidak boleh ditulis sebagai bukti deployment publik sudah berhasil.

Referensi resmi yang diperiksa 29 Oktober 2026: [deployment](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy), [dependensi](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies), dan [Secrets](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).
