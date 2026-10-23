# Penyebaran Covid 19 se Jawa Barat

Aplikasi Streamlit berbahasa Indonesia untuk menampilkan tren data COVID-19 Jawa Barat. Dashboard mencoba mengambil CSV provinsi dari sumber yang ditentukan; jika gagal, aplikasi memakai data lokal yang sebelumnya disimpan atau meminta pengguna mengunggah CSV/Excel. Aplikasi tidak membuat data COVID-19 sintetis.

## Struktur

```text
covid_dashboard/
├── app.py
├── covid_dashboard_jupyter.ipynb
├── requirements.txt
├── README.md
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
2. Jalankan sel pertama untuk memulai aplikasi dengan Python dari `.venv`.
3. Buka tautan lokal yang dicetak oleh notebook.
4. Setelah selesai, jalankan sel **Hentikan dashboard**.

Notebook adalah peluncur untuk `app.py`; dashboard tetap dirender oleh Streamlit di browser. Dengan demikian tampilan dan interaksi dashboard tetap sama seperti saat dijalankan dari terminal.

## Data dan pemetaan kolom

Kolom tanggal perlu dapat dikenali sebagai `tanggal`, `date`, `waktu`, atau `tgl`. Nama kolom indikator dikenali secara otomatis untuk nama umum yang tercantum dalam kode. Jika dataset memakai nama lain, ubah nama kolom di CSV/Excel sebelum mengunggahnya agar pemetaan lebih mudah.

Dataset yang hanya berisi nilai kumulatif dapat dipakai untuk menghitung perubahan harian, tetapi nilai perubahan negatif dipertahankan sebagai kemungkinan koreksi. Makna kolom tidak dapat dipastikan hanya dari bentuk angkanya; verifikasi dokumentasi sumber terlebih dahulu.

### Sumber yang disiapkan

- CSV provinsi: https://raw.githubusercontent.com/zakiego/dataset-sebaran-covid19goid/main/provinsi/JAWA_BARAT.csv
- Dokumentasi: https://github.com/zakiego/dataset-sebaran-covid19goid

Dashboard hanya menampilkan analisis tingkat Provinsi Jawa Barat. Data kabupaten/kota atau kecamatan tidak ditampilkan karena sumber terverifikasi belum tersedia dan tidak dapat digantikan dengan data administratif seperti jumlah kecamatan.

## Batasan yang perlu diketahui

- Dashboard menampilkan hanya informasi yang didukung kolom dataset yang dimuat.
- Peta tidak ditampilkan karena batas geografis dan identifier peta tidak disertakan.
- Gejala tidak ditampilkan tanpa dataset gejala yang terverifikasi.
- Dataset unggahan untuk dashboard harus berada pada tingkat provinsi dan menyertakan definisi indikator yang dapat diverifikasi.
- Periksa tab **Sumber & metodologi** sebelum menggunakan angka dalam laporan.

## Panduan penggunaan

Klik tombol **Panduan** di bagian atas dashboard untuk membuka popup penjelasan kontrol waktu, tema, indikator, grafik, tab, pengelolaan dataset, dan unduhan. Ikon bantuan di samping kontrol memberi penjelasan kontekstual.

Untuk membandingkan jumlah kasus antar tahun dan mengetahui tahun puncaknya, pilih **Seluruh periode (awal–akhir)** pada filter Rentang data, lalu pilih **Tahunan** pada Pengelompokan grafik. Dashboard menampilkan nilai tahunan dan menandai tahun dengan nilai tertinggi untuk indikator yang dipilih.

Pilih **Rentang khusus** untuk menentukan tanggal mulai dan akhir melalui kalender. Gunakan navigasi kalender untuk berpindah bulan dan tahun.
