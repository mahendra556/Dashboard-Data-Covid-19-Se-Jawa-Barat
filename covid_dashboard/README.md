# Penyebaran Covid 19 se Jawa Barat

Aplikasi Streamlit berbahasa Indonesia untuk menampilkan tren data COVID-19 Jawa Barat. Dashboard mencoba mengambil CSV provinsi dari sumber yang ditentukan; jika gagal, aplikasi memakai data lokal yang sebelumnya disimpan atau meminta pengguna mengunggah CSV/Excel. Aplikasi tidak membuat data COVID-19 sintetis.

## Struktur

```text
covid_dashboard/
├── app.py
├── covid_dashboard_jupyter.ipynb
├── requirements.txt
├── README.md
├── assets/
│   └── lambang-jawa-barat.png
└── data/
    └── README.md
```

## Menjalankan dari terminal

```bash
cd covid_dashboard
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Buka alamat lokal yang ditampilkan Streamlit, biasanya `http://localhost:8501`.

## Menjalankan dari Jupyter Notebook lokal

1. Buka [`covid_dashboard_jupyter.ipynb`](./covid_dashboard_jupyter.ipynb) di Jupyter Notebook atau JupyterLab.
2. Notebook berisi salinan kode `app.py` yang dibagi per judul dan kegunaan. Sel-sel ini untuk dibaca; jangan jalankan satu per satu.
3. Jalankan sel **Run Streamlit** paling akhir untuk memulai aplikasi dengan Python dari `.venv`.
4. Buka tautan lokal yang dicetak oleh notebook.
5. Setelah selesai, jalankan sel **Stop Streamlit** paling akhir untuk menghentikan aplikasi.

Kode aplikasi utama tetap berada di `app.py`; notebook menampilkan salinannya untuk dipelajari dan menjalankan aplikasi melalui dua sel terakhir. Dashboard tetap dirender oleh Streamlit di browser.

## Data dan pemetaan kolom

Kolom tanggal perlu dapat dikenali sebagai `tanggal`, `date`, `waktu`, atau `tgl`. Nama kolom indikator dikenali secara otomatis untuk nama umum yang tercantum dalam kode. Jika dataset memakai nama lain, ubah nama kolom di CSV/Excel sebelum mengunggahnya agar pemetaan lebih mudah.

Dataset yang hanya berisi nilai kumulatif dapat dipakai untuk menghitung perubahan harian, tetapi nilai perubahan negatif dipertahankan sebagai kemungkinan koreksi. Makna kolom tidak dapat dipastikan hanya dari bentuk angkanya; verifikasi dokumentasi sumber terlebih dahulu.

### Sumber yang disiapkan

- CSV provinsi: https://raw.githubusercontent.com/zakiego/dataset-sebaran-covid19goid/main/provinsi/JAWA_BARAT.csv
- Dokumentasi: https://github.com/zakiego/dataset-sebaran-covid19goid
- Lambang Provinsi Jawa Barat: [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Coat_of_arms_of_West_Java.svg). Commons mencatat lambang ini sebagai domain publik berdasarkan Perda No. 21 Tahun 1962.

Dashboard hanya menampilkan analisis tingkat Provinsi Jawa Barat. Data kabupaten/kota atau kecamatan tidak ditampilkan karena sumber terverifikasi belum tersedia dan tidak dapat digantikan dengan data administratif seperti jumlah kecamatan.

## Batasan yang perlu diketahui

- Dashboard menampilkan hanya informasi yang didukung kolom dataset yang dimuat.
- Peta tidak ditampilkan karena batas geografis dan identifier peta tidak disertakan.
- Dataset unggahan untuk dashboard harus berada pada tingkat provinsi dan menyertakan definisi indikator yang dapat diverifikasi.
- Periksa tab **Sumber & metodologi** sebelum menggunakan angka dalam laporan.

## Panduan penggunaan

Klik tombol **Panduan** di bagian atas dashboard untuk membuka popup penjelasan kontrol waktu, tema, indikator, grafik, tab, pengelolaan dataset, dan unduhan. Ikon bantuan di samping kontrol memberi penjelasan kontekstual.

Gunakan **Cakupan waktu** untuk memilih **Seluruh periode**, **Pilih tahun**, atau **Rentang khusus**. Pilihan tahun mencakup seluruh tanggal yang tersedia antara 1 Januari dan 31 Desember pada tahun tersebut. Setelah memilih cakupan, gunakan **Kelompokkan data per** untuk melihat angka per hari, per 7 hari, atau per 14 hari. Kelompok 7/14 hari dihitung berurutan mulai dari tanggal awal cakupan.

Untuk **Kasus baru**, angka dalam setiap kelompok dijumlahkan. Untuk **Kumulatif**, grafik mengambil observasi terakhir dalam kelompok agar nilai total tidak dijumlahkan berulang. Pemilihan indikator (positif, sembuh, meninggal, atau semua indikator) tetap bekerja terpisah dari pilihan waktu dan interval.

Pada tab **Ringkasan**, grafik tren tampil berdampingan dengan diagram donat komposisi status terbaru (sembuh, masih dirawat/isolasi, dan meninggal). Diagram hanya muncul saat data kumulatif yang dibutuhkan tersedia dan valid.

Pilih **Rentang khusus** untuk menentukan tanggal mulai dan akhir melalui kalender. Tombol **Reset filter** mengembalikan waktu, interval, indikator, dan bentuk grafik ke pilihan awal, sekaligus membuka kembali panduan.
