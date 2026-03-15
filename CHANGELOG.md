# Changelog

Semua perubahan penting pada project ini didokumentasikan di file ini.

Format mengikuti [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
dan project ini menggunakan [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.3.0] — 2025-03-15

### Ditambahkan
- **`pdf_analyzer.py`** — modul baru untuk analisis konten PDF secara langsung
  - Unduh hanya ~250KB per file (awal + akhir) via HTTP Range request — tidak download penuh
  - Ekstrak teks dari PDF menggunakan `pdfminer.six` dan deteksi heading bab di dalam dokumen
  - Deteksi 12 bagian struktural: cover, abstrak, kata pengantar, bab 1–5, daftar pustaka, lampiran
  - **Mode multi-file**: otomatis mendeteksi repository yang memecah skripsi per bab, mengklasifikasikan setiap file, dan memverifikasi aksesibilitasnya satu per satu
  - Self-check bawaan: jalankan `python pdf_analyzer.py` untuk verifikasi instalasi
- Field baru di dataclass `Skripsi`: `pdf_analisis_status`, `bab_pdf`, `url_per_bab`, `bab_terkunci`, `estimasi_halaman`, `pdf_analisis_catatan`
- Tampilan terminal baru: daftar bab dari isi PDF, detail multi-file per bab, estimasi jumlah halaman
- Kolom baru di output CSV dan Excel: `pdf_analisis_status`, `bab_pdf`, `url_per_bab`, `bab_terkunci`, `estimasi_halaman`
- Fallback otomatis ke perilaku v1.2.1 jika `pdfminer.six` tidak terinstall — tidak ada yang rusak

### Diubah
- Status `full` sekarang hanya diberikan jika bab 1, 3, 4, 5, dan daftar pustaka **terdeteksi di dalam PDF** (bukan hanya label di HTML)
- Bonus skor dari verifikasi PDF: `+20` untuk full, `+10` untuk partial (sebelumnya flat `+5`)
- Versi diperbarui ke `1.3`
- Dependensi baru: `pdfminer.six` (opsional — fitur analisis PDF tidak aktif jika tidak diinstall)

---

## [1.2.1] — 2025-01-20

### Diperbaiki
- Deteksi cover vs fulltext — tidak lagi salah ambil file cover sebagai fulltext
- Verifikasi aksesibilitas PDF via HEAD request sebelum ditampilkan sebagai hasil
- Deteksi redirect ke halaman login (pola DSpace/EPrints seperti USU, Unair, dll.)
- Parsing ukuran file untuk prioritaskan PDF terbesar (fulltext > cover)
- Skor penalti tambahan untuk pola login-wall yang sebelumnya tidak terdeteksi
- Status `locked` lebih akurat — tidak lagi false positive `full` untuk repo berembargo

---

## [1.2.0] — 2025-01-10

### Ditambahkan
- **OAI-PMH harvesting** sebagai jalur fetch utama (lebih andal dan terstandar dari scraping HTML)
- **`repositories.json`** — konfigurasi 75+ repository dipisah dari kode Python sepenuhnya
- Resumption token support untuk harvest data ribuan rekaman
- Concurrent request dengan `ThreadPoolExecutor` — pencarian jauh lebih cepat
- Cache lokal per-repository (TTL 24 jam) — tidak re-fetch data yang sama
- Filter lanjutan: tahun, provinsi, tipe PT (PTN/PTS/Politeknik)
- Output Excel (XLSX) dengan color coding: hijau = full, kuning = partial, merah = locked
- Mode interaktif (`--interactive`) untuk pengguna yang tidak familiar dengan CLI
- Progress bar per-universitas dengan estimasi waktu tersisa

### Diubah
- Deteksi full text berbasis sistem skor berbobot (sebelumnya hanya cek ada/tidak PDF)
- Struktur `Skripsi` dataclass menggantikan dict biasa

---

## [1.1.0] — 2024-12-01

### Ditambahkan
- Dukungan platform DSpace selain EPrints
- Parser SLiMS/Senayan untuk perpustakaan berbasis Senayan
- Output JSON selain CSV
- Parameter `--hanya-full` untuk menyembunyikan hasil locked/unknown

### Diperbaiki
- Parser EPrints lebih robust dengan multiple CSS selector fallback
- Handling SSL error — fallback ke `verify=False` dengan warning

---

## [1.0.0] — 2024-11-01

### Rilis Pertama
- Pencarian di 40+ repository EPrints perguruan tinggi Indonesia
- Deteksi full text berbasis keyword di halaman HTML
- Output CSV
- CLI dengan parameter `--keyword`, `--universitas`, `--max`
- Cache sederhana berbasis file untuk menghindari re-fetch
