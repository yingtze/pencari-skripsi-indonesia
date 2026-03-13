# Pencari Skripsi Full Text — Repository PT Indonesia v1.2

Script Python untuk mencari skripsi yang **dapat diunduh penuh (Bab 1 s/d Akhir)**
dari 75+ repository perguruan tinggi di Indonesia.

---

## Struktur File

```
📁 folder-anda/
├── pencari_skripsi_v12.py   ← Script utama
├── repositories.json         ← Konfigurasi 75+ universitas (PISAH dari script)
└── README.md
```

> **Penting:** `pencari_skripsi_v12.py` dan `repositories.json` harus berada di folder yang sama.

---

## Instalasi

```bash
pip install requests beautifulsoup4 lxml tqdm colorama openpyxl
```

---

## Cara Pakai

### Mode CLI

```bash
# Cari di semua universitas
python pencari_skripsi_v12.py --keyword "machine learning"

# Filter PTN di Jawa Timur
python pencari_skripsi_v12.py --keyword "ekonomi" --tipe PTN --provinsi "jawa timur"

# Pakai OAI-PMH saja (lebih cepat & terstandar), tampilkan hanya full text
python pencari_skripsi_v12.py --keyword "hukum pidana" --metode oai --hanya-full

# Pilih universitas tertentu, max 30 hasil/univ
python pencari_skripsi_v12.py --keyword "sistem informasi" --universitas ums umm umy --max 30

# Simpan dengan nama tertentu, hanya CSV
python pencari_skripsi_v12.py --keyword "kesehatan" --output hasil_kesehatan --format csv

# Lihat semua universitas yang didukung
python pencari_skripsi_v12.py --list-universitas

# Filter daftar universitas
python pencari_skripsi_v12.py --list-universitas --tipe PTN --provinsi "jawa barat"
```

### Mode Interaktif (Tanya-Jawab)

```bash
python pencari_skripsi_v12.py --interactive
```

---

## Parameter Lengkap

| Parameter | Pendek | Keterangan | Default |
|-----------|--------|------------|---------|
| `--keyword` | `-k` | Kata kunci pencarian | (wajib) |
| `--universitas` | `-u` | ID universitas (bisa lebih dari satu) | semua |
| `--tipe` | | `PTN` atau `PTS` | semua |
| `--provinsi` | `-p` | Filter provinsi | semua |
| `--max` | `-m` | Maks hasil per universitas | 10 |
| `--metode` | | `auto` / `oai` / `html` | `auto` |
| `--hanya-full` | | Hanya tampilkan full/partial text | false |
| `--output` | `-o` | Prefix nama file output | auto |
| `--format` | `-f` | `csv` / `json` / `xlsx` / `semua` | `semua` |
| `--workers` | | Jumlah concurrent worker | 3 |
| `--delay` | | Jeda antar request (detik) | 1.2 |
| `--no-cache` | | Nonaktifkan cache lokal | false |
| `--list-universitas` | | Tampilkan daftar universitas | |
| `--interactive` | `-i` | Mode interaktif | |
| `--quiet` | `-q` | Minimal output | |

---

## Metode Fetch

| Metode | Keterangan |
|--------|------------|
| `auto` | Coba OAI-PMH dulu, fallback ke HTML scraping |
| `oai` | Paksa OAI-PMH (lebih cepat, butuh endpoint tersedia) |
| `html` | Paksa HTML scraping (lebih lambat, tapi lebih lengkap) |

**OAI-PMH** adalah protokol standar (openarchives.org) yang digunakan oleh EPrints dan DSpace
— platform yang dipakai 86%+ PT di Indonesia. Protokol ini memberikan akses terstruktur ke
metadata Dublin Core (judul, penulis, abstrak, URL, tahun, dll).

---

## Interpretasi Status

| Status | Artinya |
|--------|---------|
| ✓ FULL | Kemungkinan besar seluruh bab tersedia (skor ≥ 15) |
| ~ PARTIAL | Ada beberapa bab tapi belum pasti lengkap (skor ≥ 5) |
| ✗ LOCKED | Terdeteksi pembatasan akses |
| ? ??? | Status tidak dapat ditentukan |

Skor dihitung berdasarkan keberadaan kata kunci seperti "full text", "open access",
nama-nama bab (pendahuluan, metodologi, kesimpulan, dll), dan ada/tidaknya link PDF.

---

## Tambah Universitas Baru

Edit `repositories.json`, tambahkan entri baru di array `universitas`:

```json
{
  "id": "kode_unik",
  "nama": "Nama Universitas",
  "kota": "Kota",
  "provinsi": "Nama Provinsi",
  "tipe": "PTN",
  "platform": "eprints",
  "url_base": "https://repository.universitas.ac.id",
  "oai_endpoint": "https://repository.universitas.ac.id/cgi/oai2",
  "search_url": "https://repository.universitas.ac.id/cgi-bin/search/search.cgi",
  "search_params": {"q": "{keyword}", "action_search": "Search"},
  "search_method": "GET",
  "parser": "eprints"
}
```

**Mengetahui platform repository:**
- URL mengandung `/cgi-bin/search` atau `/cgi/oai2` → EPrints
- URL mengandung `/xmlui/` atau `/handle/` → DSpace
- URL mengandung `slims` atau Senayan → SLiMS

**Menemukan OAI endpoint:**
- EPrints: `https://[domain]/cgi/oai2`
- DSpace: `https://[domain]/oai/request`

---

## Output

Script menghasilkan tiga file:

- `skripsi_[keyword]_[timestamp].csv` — dapat dibuka di Excel
- `skripsi_[keyword]_[timestamp].json` — untuk pemrosesan program
- `skripsi_[keyword]_[timestamp].xlsx` — Excel berwarna (hijau=full, kuning=partial)

---

## Universitas yang Didukung (75+)

### PTN — Pulau Jawa
UI, UGM, ITB, ITS, IPB, Unair, Undip, Unpad, UNY, UM, Unnes, UPI,
UNS, UB, Unej, Unsoed, UPNVJ, UPNVYK, UPNVJT, UIN Surabaya, UIN Yogyakarta,
UIN Bandung, UIN Malang, UIN Jakarta, UIN Walisongo, IAIN Purwokerto,
Sultan Ageng Tirtayasa

### PTN — Luar Jawa
USU, Unand, Unsri, Unri, Unib, Unja, Unila, Unhas, Unram, Undana,
Unpatti, Uncen, Unkhair, Unimed, UNP, ULM, Unmul, Unud, Undiksha

### PTS
UII, UMY, UMS, UMM, UAD, Ubaya, Unisba, Itenas, Telkom, Binus,
Mercu Buana, Gunadarma, Unjani, STIKOM Bali, UKDW, UKRIDA,
Unika Soegijapranata, Untar, UTA45, Unissula, Unusida, STIKI Malang,
UMJ, Unisma, Ubhara, dan lainnya

### Politeknik
Polinema, PENS, Poltekkes Surabaya

---

## Catatan

- Script mematuhi `robots.txt` secara implisit dengan menambahkan delay antar request
- Cache disimpan di folder `.cache_skripsi/` dan otomatis kedaluwarsa setelah 24 jam
- Beberapa universitas mungkin memblokir akses otomatis; hasilnya akan ditandai sebagai `unknown`
- Repository bisa berubah URL/struktur sewaktu-waktu; perbarui `repositories.json` jika diperlukan
