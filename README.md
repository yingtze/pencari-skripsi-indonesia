<div align="center">

# 📚 Pencari Skripsi Indonesia

**Cari skripsi full text dari 75+ repository perguruan tinggi Indonesia — sekali jalan.**

Tidak perlu buka satu per satu website kampus. Tidak perlu tebak-tebak mana yang bisa diunduh lengkap.  
Cukup satu perintah, script ini yang kerja.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Universitas](https://img.shields.io/badge/Universitas-75%2B-orange)](repositories.json)
[![Platform](https://img.shields.io/badge/Platform-EPrints%20%7C%20DSpace%20%7C%20SLiMS-purple)](repositories.json)

</div>

---

## Masalah yang Diselesaikan

Siapapun yang pernah riset atau nulis skripsi pasti tahu frustrasinya:

- Buka repository kampus A → hanya tersedia Bab 1
- Buka repository kampus B → perlu login atau akses kampus
- Buka repository kampus C → 404, situsnya down
- Ulangi untuk 20 kampus lain... 😮‍💨

**Pencari Skripsi Indonesia** mengotomatisasi seluruh proses itu. Script mencari di 75+ repository sekaligus, mendeteksi mana yang benar-benar bisa diunduh penuh (Bab 1 sampai Daftar Pustaka), dan langsung menyajikan hasilnya lengkap dengan link PDF-nya.

---

## Fitur Utama

- 🔍 **75+ repository** PTN, PTS, dan Politeknik dari Sabang sampai Merauke
- 📡 **OAI-PMH harvesting** — protokol standar EPrints & DSpace, lebih andal dari scraping biasa
- 🎯 **Deteksi full text berbasis skor** — bukan sekadar cek ada/tidaknya PDF, tapi menganalisis keberadaan tiap bab secara terpisah
- ⚡ **Concurrent fetch** — cari di beberapa universitas secara paralel, lebih cepat
- 💾 **Cache 24 jam** — tidak re-fetch halaman yang sama, hemat bandwidth dan waktu
- 📊 **Output lengkap** — CSV, JSON, dan Excel berwarna (hijau = full text, kuning = partial)
- 🗂️ **Konfigurasi terpisah** — tambah atau ubah universitas cukup edit `repositories.json`, tanpa sentuh kode
- 🖥️ **Mode interaktif** — cocok untuk yang tidak familiar dengan CLI

---

## Instalasi

```bash
# 1. Clone repo ini
git clone https://github.com/yingtze/pencari-skripsi-indonesia.git
cd pencari-skripsi-indonesia

# 2. Install dependensi
pip install requests beautifulsoup4 lxml tqdm colorama openpyxl
```

> Butuh Python 3.8 atau lebih baru. Cek versi Python kamu dengan `python --version`.

---

## Cara Pakai

### Pencarian Dasar

```bash
python pencari_skripsi_v12.py --keyword "machine learning"
```

### Dengan Filter

```bash
# Cari di PTN wilayah Jawa Timur saja
python pencari_skripsi_v12.py --keyword "ekonomi syariah" --tipe PTN --provinsi "jawa timur"

# Pilih universitas spesifik
python pencari_skripsi_v12.py --keyword "sistem informasi" --universitas ums umm umy

# Tampilkan hanya yang bisa diunduh penuh
python pencari_skripsi_v12.py --keyword "hukum pidana" --hanya-full
```

### Pilih Metode Fetch

```bash
# OAI-PMH — lebih cepat dan terstruktur (direkomendasikan)
python pencari_skripsi_v12.py --keyword "kesehatan masyarakat" --metode oai

# HTML scraping — jangkauan lebih luas, cocok untuk repo yang tidak punya OAI
python pencari_skripsi_v12.py --keyword "arsitektur" --metode html
```

### Simpan Hasil

```bash
# Simpan ke CSV, JSON, dan Excel sekaligus (default)
python pencari_skripsi_v12.py --keyword "pendidikan" --output hasil_pendidikan

# Hanya Excel
python pencari_skripsi_v12.py --keyword "kimia" --format xlsx
```

### Mode Interaktif

Tidak suka CLI? Jalankan mode tanya-jawab:

```bash
python pencari_skripsi_v12.py --interactive
```

### Lihat Daftar Universitas

```bash
# Semua universitas yang didukung
python pencari_skripsi_v12.py --list-universitas

# Filter berdasarkan tipe atau provinsi
python pencari_skripsi_v12.py --list-universitas --tipe PTS --provinsi "jawa barat"
```

---

## Memahami Hasil

Setiap skripsi yang ditemukan akan diberi status:

| Status | Arti |
|--------|------|
| ✅ **FULL** | Seluruh bab tersedia dan kemungkinan besar bisa diunduh |
| 🟡 **PARTIAL** | Ada beberapa bab, tapi belum pasti lengkap |
| 🔴 **LOCKED** | Terdeteksi pembatasan akses (login, embargo, campus-only) |
| ⚪ **UNKNOWN** | Status tidak bisa ditentukan secara otomatis |

Status ditentukan berdasarkan sistem skor: script mencari indikator seperti `"full text"`, `"open access"`, keberadaan link PDF, serta nama-nama bab (pendahuluan, metodologi, pembahasan, kesimpulan, dan seterusnya) di halaman detail.

---

## Seluruh Parameter

| Parameter | Pendek | Keterangan | Default |
|-----------|--------|------------|---------|
| `--keyword` | `-k` | Kata kunci pencarian | *(wajib)* |
| `--universitas` | `-u` | Satu atau lebih ID universitas | semua |
| `--tipe` | | Filter `PTN` atau `PTS` | semua |
| `--provinsi` | `-p` | Filter berdasarkan provinsi | semua |
| `--max` | `-m` | Maksimal hasil per universitas | `10` |
| `--metode` | | `auto` / `oai` / `html` | `auto` |
| `--hanya-full` | | Sembunyikan hasil yang locked/unknown | `false` |
| `--output` | `-o` | Prefix nama file output | auto (timestamp) |
| `--format` | `-f` | `csv` / `json` / `xlsx` / `semua` | `semua` |
| `--workers` | | Jumlah thread paralel | `3` |
| `--delay` | | Jeda antar request dalam detik | `1.2` |
| `--no-cache` | | Nonaktifkan cache lokal | `false` |
| `--list-universitas` | | Tampilkan daftar universitas | — |
| `--interactive` | `-i` | Mode tanya-jawab interaktif | — |
| `--quiet` | `-q` | Kurangi output ke terminal | `false` |

---

## Struktur File

```
📁 pencari-skripsi-indonesia/
├── pencari_skripsi_v12.py   ← Script utama
├── repositories.json         ← Data 75+ universitas (edit di sini untuk tambah kampus)
├── README.md
└── .cache_skripsi/           ← Cache otomatis, dibuat saat pertama kali dijalankan
```

> `pencari_skripsi_v12.py` dan `repositories.json` harus selalu berada di folder yang sama.

---

## Menambah Universitas

Konfigurasi repository sepenuhnya ada di `repositories.json` — tidak perlu mengubah kode Python sama sekali.

Tambahkan entri baru seperti ini:

```json
{
  "id": "contoh_univ",
  "nama": "Universitas Contoh",
  "kota": "Kota",
  "provinsi": "Nama Provinsi",
  "tipe": "PTN",
  "platform": "eprints",
  "url_base": "https://repository.contoh.ac.id",
  "oai_endpoint": "https://repository.contoh.ac.id/cgi/oai2",
  "search_url": "https://repository.contoh.ac.id/cgi-bin/search/search.cgi",
  "search_params": {"q": "{keyword}", "action_search": "Search"},
  "search_method": "GET",
  "parser": "eprints"
}
```

**Cara mengenali platform repository:**

| Tanda di URL | Platform | Parser |
|---|---|---|
| `/cgi-bin/search` atau `/cgi/oai2` | EPrints | `eprints` |
| `/xmlui/` atau `/handle/` | DSpace | `dspace` |
| `slims` atau `senayan` | SLiMS | `senayan` |
| Lainnya | — | `generic` |

**Cara menemukan OAI-PMH endpoint:**
- EPrints → `https://[domain]/cgi/oai2`
- DSpace → `https://[domain]/oai/request`

Buka URL tersebut di browser. Jika muncul XML dengan tag `<OAI-PMH>`, berarti endpoint aktif dan bisa digunakan.

---

## Universitas yang Didukung

<details>
<summary><strong>PTN — Pulau Jawa (27 universitas)</strong></summary>
<br>

UI, UGM, ITB, ITS, IPB, Universitas Airlangga, Universitas Diponegoro, Universitas Padjadjaran, UNY, Universitas Negeri Malang, Unnes, UPI, UNS, Universitas Brawijaya, Universitas Jember, Universitas Jenderal Soedirman, UPN Veteran Jakarta, UPN Veteran Yogyakarta, UPN Veteran Jawa Timur, UIN Sunan Ampel Surabaya, UIN Sunan Kalijaga Yogyakarta, UIN Sunan Gunung Djati Bandung, UIN Maulana Malik Ibrahim Malang, UIN Syarif Hidayatullah Jakarta, UIN Walisongo Semarang, IAIN Purwokerto, Universitas Sultan Ageng Tirtayasa

</details>

<details>
<summary><strong>PTN — Luar Jawa (19 universitas)</strong></summary>
<br>

Universitas Sumatera Utara, Universitas Andalas, Universitas Sriwijaya, Universitas Riau, Universitas Bengkulu, Universitas Jambi, Universitas Lampung, Universitas Hasanuddin, Universitas Mataram, Universitas Nusa Cendana, Universitas Pattimura, Universitas Cenderawasih, Universitas Khairun, Universitas Negeri Medan, Universitas Negeri Padang, Universitas Lambung Mangkurat, Universitas Mulawarman, Universitas Udayana, Universitas Pendidikan Ganesha

</details>

<details>
<summary><strong>PTS (26 universitas)</strong></summary>
<br>

Universitas Islam Indonesia, Universitas Muhammadiyah Yogyakarta, Universitas Muhammadiyah Surakarta, Universitas Muhammadiyah Malang, Universitas Ahmad Dahlan, Universitas Surabaya, Universitas Islam Bandung, Institut Teknologi Nasional Bandung, Universitas Telkom, Binus University, Universitas Mercu Buana, Universitas Gunadarma, Universitas Jenderal Ahmad Yani, STIKOM Bali, Universitas Kristen Duta Wacana, Universitas Kristen Krida Wacana, Universitas Katolik Soegijapranata, Universitas Tarumanagara, Universitas 17 Agustus 1945 Jakarta, Universitas Islam Sultan Agung, Universitas Nahdlatul Ulama Sidoarjo, Universitas Islam Malang, Universitas Bhayangkara Jakarta Raya, Universitas Muhammadiyah Jakarta, STIKI Malang, Universitas Atma Jaya Yogyakarta

</details>

<details>
<summary><strong>Politeknik (3)</strong></summary>
<br>

Politeknik Negeri Malang, Politeknik Elektronika Negeri Surabaya, Politeknik Kesehatan Kemenkes Surabaya

</details>

---

## Tentang OAI-PMH

Script ini menggunakan **OAI-PMH** (Open Archives Initiative Protocol for Metadata Harvesting) sebagai metode fetch utama. Ini adalah protokol standar internasional yang diimplementasikan oleh hampir semua platform repository ilmiah — termasuk EPrints dan DSpace yang dipakai oleh 80%+ perguruan tinggi di Indonesia.

Bedanya dengan scraping HTML biasa: OAI-PMH memberikan data terstruktur langsung (judul, penulis, abstrak, URL, tahun) tanpa perlu menafsirkan HTML. Hasilnya lebih konsisten dan jauh lebih jarang rusak saat tampilan website berubah.

---

## Catatan Penggunaan

- Script menambahkan jeda antar request (default 1.2 detik) untuk tidak membebani server universitas
- Hasil cache disimpan di `.cache_skripsi/` dan otomatis kedaluwarsa setelah 24 jam
- Beberapa universitas membatasi akses dari luar kampus — hasilnya tetap muncul dengan status `unknown`
- URL dan struktur repository bisa berubah sewaktu-waktu; perbarui `repositories.json` jika ada yang tidak lagi berfungsi

---

## Kontribusi

Pull request sangat disambut, terutama untuk:

- **Menambah universitas baru** ke `repositories.json`
- **Memperbaiki parser** untuk repository dengan struktur HTML yang tidak umum
- **Memperbarui URL** repository yang sudah berubah domain atau path

---

## Lisensi

[MIT License](LICENSE) — bebas digunakan, dimodifikasi, dan didistribusikan.
