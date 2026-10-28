# Perbandingan klasifikasi arah harga BTC EUR menggunakan Random Forest dan Groq

Dokumen ini merupakan draf laporan berdasarkan hasil eksperimen yang tersimpan. Identitas penyusun, screenshot pengujian, dan URL aplikasi publik perlu dilengkapi pada dokumen pengumpulan. Uji web lokal dilaporkan berhasil oleh pengguna pada 29 Oktober 2026; deployment publik belum dinyatakan selesai.

## Studi kasus dan sumber data

Studi kasus mengklasifikasikan arah perubahan harga BTC/EUR pada observasi berikutnya. Label Naik diberikan ketika harga penutupan berikutnya lebih tinggi daripada harga penutupan saat ini. Harga sama atau turun diberi label Tidak_Naik. Prediksi menggunakan informasi yang tersedia setelah observasi saat ini selesai.

Sumber dataset yang diberikan pengguna adalah [bitcoin di Kaggle, akun hamdinizar](https://www.kaggle.com/datasets/hamdinizar/bitcoin). File lokal BTC-EUR.csv memuat 1.877 observasi dengan tujuh kolom: Date, Open, High, Low, Close, Adj Close, dan Volume. Rentang tanggal adalah 17 September 2014 sampai 6 November 2019. Penyedia asli serta lisensi belum diverifikasi dari deskripsi lengkap Kaggle; nama akun pengunggah tidak otomatis menunjukkan pembuat data asli.

## Inspeksi dan persiapan data

Inspeksi tidak menemukan nilai kosong, tanggal duplikat, baris duplikat penuh, harga nol/negatif, volume negatif, atau tanggal tanpa observasi dalam rentang harian. Close dan Adj Close identik. Terdapat 207 baris dengan hubungan OHLC yang tidak konsisten.

Baris tersebut dipertahankan dan diberi flag audit. Pemodelan hanya menggunakan turunan riwayat Close dan Volume; Open, High, Low, serta Adj Close tidak menjadi prediktor. Pendekatan ini menghindari penggunaan kolom OHLC yang bermasalah sebagai fitur, tetapi tidak membuktikan Close/Volume bebas dari semua kesalahan sumber.

Sembilan fitur historis adalah return 1, 3, dan 7 observasi; volatilitas return pada 7 dan 14 observasi; rasio harga terhadap SMA 7 dan 14; rasio Volume terhadap rata-rata 7 observasi; dan perubahan log(1+Volume) satu observasi. Return dan rasio dinyatakan dalam desimal. Semua fitur memakai informasi sampai observasi saat ini, tanpa memasukkan harga atau label masa depan.

Empat belas baris awal tidak memiliki riwayat fitur lengkap, dan satu baris akhir tidak memiliki target berikutnya. Data kemudian dibagi kronologis sekitar 70/15/15. Masing-masing satu sampel pada batas train dan validasi dikeluarkan karena tanggal targetnya menyentuh periode berikutnya.

| Partisi | Jumlah | Tanggal fitur awal | Tanggal fitur akhir |
|---|---:|---|---|
| Train | 1.302 | 2014-10-01 | 2018-04-24 |
| Validasi | 278 | 2018-04-26 | 2019-01-28 |
| Test | 280 | 2019-01-30 | 2019-11-05 |

Jumlah akhir adalah 1.860 baris. Tidak dilakukan shuffle, imputasi, atau normalisasi dengan statistik data masa depan. Fitur awal validasi/test dapat menggunakan riwayat sebelum periode tersebut, sebagaimana informasi yang tersedia pada waktu prediksi.

## Pemodelan berbasis library

Model library menggunakan scikit-learn. Baseline DummyClassifier selalu memprediksi kelas mayoritas train. Kandidat model adalah Logistic Regression dengan StandardScaler di dalam pipeline, dan Random Forest. Scaler hanya dipelajari dari train. Random Forest menggunakan 300 pohon, kedalaman maksimum 6, minimum sampel daun 15, max_features sqrt, dan random_state 42.

Pemilihan model menggunakan F1 macro validasi tertinggi di antara dua model terlatih, dengan parameter yang ditetapkan sebelumnya. Model terpilih tidak dilatih ulang pada validasi atau test.

| Kandidat | Accuracy validasi | Balanced accuracy | F1 macro | n |
|---|---:|---:|---:|---:|
| Baseline mayoritas | 50,36% | 50,00% | 0,335 | 278 |
| Logistic Regression | 49,64% | 49,34% | 0,390 | 278 |
| Random Forest | 49,28% | 49,04% | 0,426 | 278 |

Random Forest dipilih berdasarkan F1 macro, meskipun accuracy validasinya lebih rendah daripada baseline. Pada seluruh 280 data test, Random Forest memperoleh accuracy 56,79%, balanced accuracy 52,74%, dan F1 macro 0,494. Baseline memperoleh accuracy 56,43% dan F1 macro 0,361. Keunggulan accuracy hanya sekitar 0,36 poin persentase. Recall kelas Tidak_Naik adalah 21,31%, sehingga model masih lemah dalam mengenali kelas tersebut.

## Pemodelan menggunakan AI model service

Inferensi LLM dijalankan melalui API Groq dengan sembilan fitur yang sama. Tanggal, harga masa depan, dan target baris yang diprediksi tidak dikirim sebagai input. Tidak dilakukan training atau fine-tuning bobot LLM.

Eksperimen awal GPT-OSS 120B dengan rencana zero-shot dan few-shot tidak selesai karena batas token akun. Checkpoint disimpan sebagai eksperimen parsial, bukan hasil final pembanding. Kontrol transport kemudian ditambahkan untuk membaca retry-after dan membatasi waktu tunggu tanpa mengganti prompt atau classifier eksperimen tersebut.

Untuk mengurangi jumlah request, dibuat protokol terbatas terpisah dengan Qwen 3.8 27B melalui Groq, temperature 0, reasoning_effort none, dan maksimum completion 32 token. Satu prompt zero-shot diuji pada 30 posisi validasi yang tersebar merata menurut urutan waktu. Tidak ada pemilihan sampel berdasarkan label atau skor Groq. Hasil validasi adalah accuracy 66,67%, balanced accuracy 50,00%, F1 macro 0,400, dan nol output invalid. Karena hanya satu kandidat pada protokol cepat, hasil ini bukan bukti bahwa Qwen merupakan model Groq terbaik.

Konfigurasi kemudian diuji pada 60 posisi test yang juga dipilih secara deterministik dan merata sepanjang periode. Random Forest serta baseline melakukan inferensi pada 60 sampel yang persis sama, tanpa training ulang.

## Perbandingan pada sampel test yang sama

| Pendekatan | Accuracy | Balanced accuracy | F1 macro | n |
|---|---:|---:|---:|---:|
| Random Forest | 60,00% | 56,11% | 0,538 | 60 |
| Baseline mayoritas | 56,67% | 50,00% | 0,362 | 60 |
| Groq Qwen | 41,67% | 48,08% | 0,294 | 60 |

Pada sampel tersebut Random Forest mengungguli baseline dan Groq pada metrik yang dilaporkan. Qwen berada di bawah baseline. Perbandingan ini berlaku untuk 60 sampel dan konfigurasi yang diuji; skor tersebut tidak boleh disamakan dengan hasil Groq pada seluruh 280 data test. Tidak dilakukan pengujian signifikansi atau interval kepercayaan, sehingga keunggulan pada sampel tidak membuktikan generalisasi yang kuat.

## Implementasi web

Aplikasi Streamlit menyajikan input manual sembilan fitur, unggah CSV fitur siap pakai, serta unggah riwayat Date, Close, Volume. Riwayat memerlukan minimal 15 observasi harian berurutan untuk menghitung fitur yang sama dengan proses pemodelan. Pengguna dapat memilih Random Forest, Groq, atau keduanya.

Sampel unduhan disiapkan dari periode train: lima baris fitur dan 30 observasi riwayat, tanpa target atau harga masa depan. Aplikasi membatasi prediksi ke 10 baris fitur terakhir per unggahan. Pengguna dapat mengunduh hasil prediksi dan tabel evaluasi.

Model library dimuat dari joblib dengan pemeriksaan hash dan versi scikit-learn. Konfigurasi serta classifier Groq sama dengan saat evaluasi dan diperiksa konsistensinya. API key menggunakan Secrets/environment dan tidak dimasukkan ke repository. Client serta prediksi sukses menggunakan caching. Kegagalan API tidak dicache sebagai prediksi valid.

## Pengujian aplikasi

Empat pengujian dengan data buatan lulus: kolom target masa depan tidak masuk prediktor; riwayat dengan tanggal hilang ditolak; 15 observasi menghasilkan satu baris fitur; dan form library dapat bekerja tanpa Groq maupun artefak nyata melalui mock. Pengujian tersebut tidak memanggil API atau mengolah dataset pengguna.

Pengguna melaporkan uji web lokal berjalan lancar pada 29 Oktober 2026, meliputi alur input, prediksi, dan sampel yang diminta untuk diuji. Screenshot dan bukti rinci perlu dilampirkan oleh penyusun. Pemeriksaan endpoint lokal memberikan HTTP 200. Bukti lokal ini belum membuktikan keberhasilan deployment publik.

## Kesesuaian dan keterbatasan

Brief tambahan dipenuhi pada pemilihan dataset sendiri, dua pendekatan pemodelan, evaluasi, input/output web, dan sampel unduhan. Poin URL publik baru selesai setelah deployment dan pengujian URL nyata.

Modul 2B secara ketat mensyaratkan konfigurasi yang sudah lolos gerbang evaluasi. Konfigurasi Groq BTC/EUR saat ini berstatus dievaluasi_eksperimen, tanpa klaim lolos kualitas. Model di bawah baseline tidak dianggap berhasil hanya karena request API dan aplikasi berjalan. Ambang F1 kasus status akademik tidak otomatis diterapkan pada dataset BTC/EUR. Tidak dibuat ambang baru setelah melihat hasil untuk meloloskan model.

Keterbatasan utama meliputi kualitas OHLC sumber, penggunaan data historis 2014–2019, target arah harga yang sulit diprediksi dari fitur terbatas, evaluasi Groq yang dibatasi kuota, ukuran test pembanding 60, dan belum adanya konfirmasi independen pada periode baru. Tampilan web harus mempertahankan keterangan eksperimen dan hasil yang lemah tersebut.

## Deployment dan lampiran pengumpulan

Repository tujuan adalah [Pincen14/btc-eur-model-comparison](https://github.com/Pincen14/btc-eur-model-comparison). Deployment direncanakan pada Streamlit Community Cloud dengan app.py di root repository dan Python 3.13. API key diisi melalui pengaturan Secrets.

URL aplikasi publik belum dicatat. Setelah deployment, tambahkan URL yang benar-benar dapat dibuka, tanggal pengujian publik, dan screenshot hasil input manual, prediksi dua metode, tabel evaluasi, unduhan sampel, serta pengolahan CSV. Identitas penyusun dan format administrasi laporan disesuaikan dengan ketentuan mata kuliah.
