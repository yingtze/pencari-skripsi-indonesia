"""
pdf_analyzer.py — Analisis konten PDF untuk deteksi skripsi full text
======================================================================
Versi  : 1.3.0
Tanggal: 2025-03-15
Bagian dari: pencari-skripsi-indonesia (github.com/yingtze/pencari-skripsi-indonesia)

──────────────────────────────────────────────────────────────────
 RIWAYAT VERSI MODUL INI
──────────────────────────────────────────────────────────────────

v1.3.0 — 2025-03-15  [rilis pertama modul ini]
  ✓ Analisis isi PDF via HTTP Range request (~250KB, bukan download penuh)
  ✓ Ekstraksi teks dengan pdfminer.six + deteksi 12 bagian struktural skripsi
  ✓ Mode multi-file: klasifikasi + verifikasi akses PDF per bab
  ✓ HasilAnalisisPDF dataclass dengan ringkasan, bab_semua, url_per_bab
  ✓ analisis_penuh() sebagai entry point tunggal dari pencari_skripsi.py
  ✓ Self-check: jalankan `python pdf_analyzer.py` untuk verifikasi instalasi
  ✓ Bekerja tanpa pdfminer.six (mode multi-file tetap aktif)

──────────────────────────────────────────────────────────────────

Modul ini melakukan dua hal yang tidak bisa dilakukan oleh html-scraping biasa:

1. ANALISIS ISI PDF
   Baca teks dari 150KB pertama (dan opsional 150KB terakhir) file PDF,
   lalu cari struktur bab secara langsung di dalam dokumen.
   Hasilnya jauh lebih akurat dari sekadar membaca label di halaman HTML.

2. DETEKSI PDF MULTI-FILE (per bab)
   Beberapa repository memecah skripsi menjadi banyak file terpisah
   (cover.pdf, bab1.pdf, bab2.pdf, ..., daftar_pustaka.pdf).
   Modul ini mengumpulkan semua URL itu, memverifikasi aksesibilitas
   masing-masing, dan melaporkan bab mana yang tersedia vs terkunci.

Cara pakai dari pencari_skripsi.py:
    from pdf_analyzer import analisis_pdf_skripsi, kumpulkan_pdf_per_bab, HasilAnalisisPDF

Kebutuhan tambahan:
    pip install pdfminer.six

Jika pdfminer tidak tersedia, modul tetap bisa digunakan tapi
hanya fitur "multi-file per bab" yang aktif (analisis isi dinonaktifkan).
"""

from __future__ import annotations

import io
import re
import time
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urljoin

# ── Cek ketersediaan pdfminer ────────────────────────────────────────
try:
    from pdfminer.high_level import extract_text_to_fp
    from pdfminer.layout import LAParams
    PDFMINER_TERSEDIA = True
except ImportError:
    PDFMINER_TERSEDIA = False

import requests
from bs4 import BeautifulSoup


# ─────────────────────────────────────────────────────────────────────
#  KONSTANTA — DETEKSI STRUKTUR BAB
# ─────────────────────────────────────────────────────────────────────

# Pola heading bab. Urutan penting: dari yang paling spesifik ke generik.
# Tiap tuple: (nama_bab_pendek, [pola_regex, ...])
POLA_BAB: list[tuple[str, list[str]]] = [
    ("cover/judul", [
        r"halaman\s+judul",
        r"lembar\s+judul",
        r"title\s+page",
        r"universitas\s+\w+",          # biasanya ada di halaman pertama
    ]),
    ("persetujuan/pengesahan", [
        r"lembar\s+persetujuan",
        r"lembar\s+pengesahan",
        r"halaman\s+persetujuan",
        r"approval\s+sheet",
    ]),
    ("abstrak", [
        r"\babstrak\b",
        r"\babstract\b",
        r"intisari",
    ]),
    ("kata pengantar", [
        r"kata\s+pengantar",
        r"prakata",
        r"foreword",
        r"preface",
    ]),
    ("daftar isi", [
        r"daftar\s+isi",
        r"table\s+of\s+contents",
        r"contents",
    ]),
    ("bab 1 - pendahuluan", [
        r"bab\s+[i1]\s*[\.\:\-]?\s*(pendahuluan|latar\s+belakang|introduction)",
        r"chapter\s+[i1]\s*[\.\:\-]?\s*(introduction|background)",
        r"^1[\.\s]+(pendahuluan|latar\s+belakang|introduction)",
        r"latar\s+belakang\s+(masalah|penelitian)",
        r"rumusan\s+masalah",
        r"tujuan\s+penelitian",
    ]),
    ("bab 2 - tinjauan pustaka", [
        r"bab\s+[ii2]\s*[\.\:\-]?\s*(tinjauan|kajian|landasan|kerangka|teori)",
        r"chapter\s+(ii|2)\s*[\.\:\-]?\s*(literature|review|theoretical)",
        r"^2[\.\s]+(tinjauan|kajian|landasan)",
        r"tinjauan\s+pustaka",
        r"kajian\s+pustaka",
        r"landasan\s+teori",
        r"kerangka\s+teori",
        r"kerangka\s+konsep",
    ]),
    ("bab 3 - metodologi", [
        r"bab\s+[iii3]\s*[\.\:\-]?\s*(metod|penelitian)",
        r"chapter\s+(iii|3)\s*[\.\:\-]?\s*(method|research)",
        r"^3[\.\s]+(metod)",
        r"metode\s+penelitian",
        r"metodologi\s+penelitian",
        r"desain\s+penelitian",
        r"populasi\s+dan\s+sampel",
        r"teknik\s+(pengumpulan|analisis)\s+data",
    ]),
    ("bab 4 - hasil", [
        r"bab\s+[iv4]\s*[\.\:\-]?\s*(hasil|analisis|pembahasan|temuan|finding)",
        r"chapter\s+(iv|4)\s*[\.\:\-]?\s*(result|finding|analysis|discussion)",
        r"^4[\.\s]+(hasil|analisis|pembahasan)",
        r"hasil\s+penelitian",
        r"hasil\s+dan\s+pembahasan",
        r"analisis\s+data",
        r"temuan\s+penelitian",
    ]),
    ("bab 5 - kesimpulan", [
        r"bab\s+[v5]\s*[\.\:\-]?\s*(kesimpulan|penutup|simpulan|saran|conclusion)",
        r"chapter\s+(v|5)\s*[\.\:\-]?\s*(conclusion|closing|recommendation)",
        r"^5[\.\s]+(kesimpulan|penutup|simpulan)",
        r"kesimpulan\s+dan\s+saran",
        r"simpulan\s+dan\s+saran",
        r"penutup",
    ]),
    ("daftar pustaka", [
        r"daftar\s+pustaka",
        r"daftar\s+referensi",
        r"references",
        r"bibliography",
        r"kepustakaan",
    ]),
    ("lampiran", [
        r"lampiran",
        r"appendix",
        r"appendices",
    ]),
]

# Bab-bab yang wajib ada untuk diklasifikasikan sebagai full text
BAB_WAJIB = {
    "bab 1 - pendahuluan",
    "bab 3 - metodologi",
    "bab 4 - hasil",
    "bab 5 - kesimpulan",
    "daftar pustaka",
}

# Bab minimum untuk "partial"
BAB_PARTIAL_MIN = 3

# Pola nama file yang menandakan bab tertentu (untuk multi-file detection)
POLA_NAMA_FILE_BAB: list[tuple[str, re.Pattern]] = [
    ("cover/judul",              re.compile(r"cover|sampul|judul|halaman.?judul|title", re.I)),
    ("persetujuan/pengesahan",   re.compile(r"persetujuan|pengesahan|approval|lembar", re.I)),
    ("abstrak",                  re.compile(r"abstrak|abstract|intisari", re.I)),
    ("kata pengantar",           re.compile(r"kata.?pengantar|prakata|foreword|preface", re.I)),
    ("daftar isi",               re.compile(r"daftar.?isi|contents|toc", re.I)),
    ("bab 1 - pendahuluan",      re.compile(r"bab.?[i1](?!\w)|bab.?1|chapter.?[i1](?!\w)|chapter.?1|pendahuluan", re.I)),
    ("bab 2 - tinjauan pustaka", re.compile(r"bab.?i{2}(?!\w)|bab.?2|chapter.?2|tinjauan|kajian|landasan", re.I)),
    ("bab 3 - metodologi",       re.compile(r"bab.?i{3}(?!\w)|bab.?3|chapter.?3|metod", re.I)),
    ("bab 4 - hasil",            re.compile(r"bab.?iv(?!\w)|bab.?4|chapter.?4|hasil|pembahasan|analisis", re.I)),
    ("bab 5 - kesimpulan",       re.compile(r"bab.?v(?!\w)|bab.?5|chapter.?5|kesimpulan|penutup|simpulan", re.I)),
    ("daftar pustaka",           re.compile(r"daftar.?pustaka|referensi|bibliography|references", re.I)),
    ("lampiran",                 re.compile(r"lampiran|appendix|appendices", re.I)),
]

# Pola login redirect (disalin dari script utama agar modul mandiri)
POLA_LOGIN = re.compile(
    r"login|signin|sign.in|shibboleth|cas\.(?:ac|edu|go)\.id|"
    r"auth\..*redirect|/account/|/user/login",
    re.IGNORECASE,
)


# ─────────────────────────────────────────────────────────────────────
#  DATA CLASS HASIL ANALISIS
# ─────────────────────────────────────────────────────────────────────

@dataclass
class HasilAnalisisPDF:
    """Hasil analisis mendalam satu skripsi."""

    # Status akhir berdasarkan analisis PDF (override status dari HTML)
    status: str = "unknown"          # full / partial / locked / unknown

    # Bab yang berhasil dideteksi dari ISI PDF
    bab_dari_pdf: list[str] = field(default_factory=list)

    # Bab yang terdeteksi dari NAMA FILE (multi-file mode)
    bab_dari_nama_file: list[str] = field(default_factory=list)

    # URL PDF tunggal yang terverifikasi bisa diakses
    url_pdf_verified: str = ""

    # Untuk kasus multi-file: mapping nama_bab → url
    url_per_bab: dict[str, str] = field(default_factory=dict)

    # Bab yang ada di multi-file tapi terkunci/tidak bisa diakses
    bab_terkunci: list[str] = field(default_factory=list)

    # Apakah analisis isi PDF berhasil dijalankan
    pdf_dibaca: bool = False

    # Jumlah halaman estimasi (dari jumlah teks yang diekstrak)
    estimasi_halaman: int = 0

    # Catatan teknis untuk debugging
    catatan_teknis: str = ""

    @property
    def bab_semua(self) -> list[str]:
        """Gabungan bab dari semua sumber deteksi, tanpa duplikat."""
        return list(dict.fromkeys(self.bab_dari_pdf + self.bab_dari_nama_file))

    @property
    def ringkasan(self) -> str:
        """Ringkasan satu baris untuk ditampilkan di terminal."""
        bab = self.bab_semua
        n = len(bab)
        if self.status == "full":
            return f"✓ Full text terverifikasi — {n} bab/bagian terdeteksi"
        if self.status == "partial":
            bab_str = ", ".join(bab[:3])
            sisa = f" +{n-3} lainnya" if n > 3 else ""
            return f"~ Partial — {bab_str}{sisa}"
        if self.status == "locked":
            return "✗ PDF ada tapi tidak bisa diakses"
        if self.url_per_bab:
            return f"? Multi-file: {len(self.url_per_bab)} file ditemukan"
        return "? Tidak dapat dianalisis"


# ─────────────────────────────────────────────────────────────────────
#  CORE: BACA DAN ANALISIS ISI PDF
# ─────────────────────────────────────────────────────────────────────

def _unduh_potongan_pdf(session: requests.Session, url: str,
                        bytes_awal: int = 150_000,
                        bytes_akhir: int = 100_000,
                        timeout: int = 20) -> Optional[bytes]:
    """
    Unduh sebagian kecil PDF menggunakan HTTP Range requests.

    Strategi:
    - Minta N byte pertama → biasanya cukup untuk TOC dan beberapa bab awal
    - Tambah N byte terakhir → untuk bab kesimpulan + daftar pustaka
    - Gabungkan keduanya; total maksimal ~250KB dari file yang mungkin 10MB+

    Ini jauh lebih efisien daripada mengunduh seluruh file.
    """
    try:
        # Cek ukuran file dulu via HEAD
        head = session.head(url, timeout=timeout, allow_redirects=True)
        if head.status_code not in (200, 206):
            return None

        content_length = int(head.headers.get("Content-Length", 0))
        accepts_ranges = head.headers.get("Accept-Ranges", "").lower() == "bytes"

        # Kalau server mendukung Range request, ambil awal + akhir
        if accepts_ranges and content_length > bytes_awal + bytes_akhir:
            bagian_awal = _range_get(session, url, 0, bytes_awal - 1, timeout)
            bagian_akhir = _range_get(
                session, url,
                max(0, content_length - bytes_akhir),
                content_length - 1,
                timeout
            )
            if bagian_awal and bagian_akhir:
                return bagian_awal + bagian_akhir
            if bagian_awal:
                return bagian_awal

        # Fallback: download stream, berhenti setelah bytes_awal
        r = session.get(url, stream=True, timeout=timeout, allow_redirects=True)
        if r.status_code != 200:
            return None

        ct = r.headers.get("Content-Type", "").lower()
        if "html" in ct:
            # Kemungkinan halaman login
            return None

        data = b""
        for chunk in r.iter_content(8192):
            data += chunk
            if len(data) >= bytes_awal:
                break
        r.close()
        return data if data else None

    except Exception:
        return None


def _range_get(session: requests.Session, url: str,
               start: int, end: int, timeout: int) -> Optional[bytes]:
    """HTTP Range GET sederhana."""
    try:
        headers = {"Range": f"bytes={start}-{end}"}
        r = session.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        if r.status_code in (200, 206):
            return r.content
        return None
    except Exception:
        return None


def ekstrak_teks_dari_bytes(pdf_bytes: bytes) -> Optional[str]:
    """
    Ekstrak teks dari bytes PDF menggunakan pdfminer.

    Mengembalikan None jika pdfminer tidak tersedia atau PDF tidak bisa dibaca.
    """
    if not PDFMINER_TERSEDIA:
        return None

    try:
        output = io.StringIO()
        laparams = LAParams(
            line_margin=0.3,
            word_margin=0.1,
            char_margin=2.0,
            boxes_flow=0.5,
        )
        extract_text_to_fp(
            io.BytesIO(pdf_bytes),
            output,
            laparams=laparams,
            output_type="text",
            codec="utf-8",
        )
        return output.getvalue()
    except Exception:
        return None


def deteksi_bab_dari_teks(teks: str) -> list[str]:
    """
    Cari heading bab di dalam teks PDF.

    Mengembalikan list nama bab yang ditemukan, berurutan sesuai POLA_BAB.
    """
    if not teks:
        return []

    teks_lower = teks.lower()
    bab_ditemukan = []

    for nama_bab, pola_list in POLA_BAB:
        for pola in pola_list:
            try:
                if re.search(pola, teks_lower, re.MULTILINE):
                    bab_ditemukan.append(nama_bab)
                    break   # satu match per bab sudah cukup
            except re.error:
                continue

    return bab_ditemukan


def hitung_estimasi_halaman(teks: str) -> int:
    """
    Estimasi kasar jumlah halaman berdasarkan volume teks.
    ~250 kata per halaman untuk skripsi Indonesia.
    """
    if not teks:
        return 0
    jumlah_kata = len(teks.split())
    return max(1, jumlah_kata // 250)


def tentukan_status_dari_bab(bab_terdeteksi: list[str],
                              pdf_dibaca: bool = True) -> str:
    """
    Tentukan status full/partial/unknown berdasarkan bab yang ditemukan.

    Logika:
    - full    : semua BAB_WAJIB ada
    - partial : minimal BAB_PARTIAL_MIN bab ada, atau ada bab isi utama
    - unknown : kurang dari itu, atau PDF tidak bisa dibaca
    """
    if not bab_terdeteksi:
        return "unknown"

    bab_set = set(bab_terdeteksi)

    if BAB_WAJIB.issubset(bab_set):
        return "full"

    # Cek partial: ada bab isi (bukan hanya cover/abstrak)
    bab_isi = {b for b in bab_set if any(
        kata in b for kata in ["bab 1", "bab 2", "bab 3", "bab 4", "bab 5",
                               "metodologi", "hasil", "kesimpulan", "daftar pustaka"]
    )}

    if len(bab_set) >= BAB_PARTIAL_MIN or len(bab_isi) >= 2:
        return "partial"

    return "unknown"


# ─────────────────────────────────────────────────────────────────────
#  CORE: DETEKSI MULTI-FILE PER BAB
# ─────────────────────────────────────────────────────────────────────

def klasifikasikan_pdf_per_bab(daftar_pdf: list[dict]) -> dict[str, str]:
    """
    Dari daftar PDF yang ditemukan di halaman detail, coba petakan
    tiap file ke nama bab berdasarkan label dan nama file-nya.

    Input: list of {"url": str, "label": str}
    Output: dict {nama_bab: url}
    """
    hasil = {}

    for pdf in daftar_pdf:
        url   = pdf.get("url", "")
        label = pdf.get("label", "")
        teks_cari = f"{label} {url}".lower()

        for nama_bab, pola in POLA_NAMA_FILE_BAB:
            if pola.search(teks_cari):
                # Jangan overwrite kalau sudah ada (ambil yang pertama ditemukan)
                if nama_bab not in hasil:
                    hasil[nama_bab] = url
                break

    return hasil


def verifikasi_akses_batch(session: requests.Session,
                           url_per_bab: dict[str, str],
                           delay: float = 0.5,
                           timeout: int = 10) -> tuple[dict[str, str], list[str]]:
    """
    Verifikasi aksesibilitas setiap URL dalam url_per_bab via HEAD request.

    Mengembalikan:
    - bab_bisa_diakses: dict {nama_bab: url} — yang berhasil
    - bab_terkunci: list nama_bab — yang gagal/terkunci
    """
    bisa_diakses = {}
    terkunci = []

    for nama_bab, url in url_per_bab.items():
        try:
            time.sleep(delay)
            resp = session.head(url, timeout=timeout, allow_redirects=True)

            # Cek redirect ke login
            redirect_ke_login = False
            for r in resp.history:
                if POLA_LOGIN.search(r.headers.get("Location", "")):
                    redirect_ke_login = True
                    break
            if POLA_LOGIN.search(resp.url):
                redirect_ke_login = True

            if redirect_ke_login or resp.status_code in (401, 403):
                terkunci.append(nama_bab)
                continue

            ct = resp.headers.get("Content-Type", "").lower()
            if resp.status_code == 200 and (
                "pdf" in ct or "octet" in ct or "application" in ct
            ):
                bisa_diakses[nama_bab] = url
            elif resp.status_code in (200, 206):
                # Content-type tidak jelas, asumsikan bisa diakses
                bisa_diakses[nama_bab] = url
            else:
                terkunci.append(nama_bab)

        except Exception:
            terkunci.append(nama_bab)

    return bisa_diakses, terkunci


def kumpulkan_semua_pdf_dari_halaman(soup: BeautifulSoup,
                                     base_url: str) -> list[dict]:
    """
    Kumpulkan SEMUA link PDF dari halaman detail, termasuk yang
    mungkin per bab.

    Berbeda dari ekstrak_pdf_dari_detail() di script utama yang hanya
    mengembalikan satu URL fulltext — fungsi ini mengembalikan semua.
    """
    hasil = []
    seen_urls = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]

        # Cek apakah ini link ke file (PDF atau bitstream/download)
        adalah_file = (
            href.lower().endswith(".pdf") or
            re.search(r"/bitstream/|/retrieve/|/download/|/files/|/content/", href, re.I)
        )
        if not adalah_file:
            continue

        url_abs = urljoin(base_url, href)
        if url_abs in seen_urls:
            continue
        seen_urls.add(url_abs)

        # Ambil label dari teks link atau parent cell
        label = a.get_text(strip=True)
        if not label:
            for parent_tag in ["td", "th", "li", "div", "span"]:
                p = a.find_parent(parent_tag)
                if p:
                    label = p.get_text(separator=" ", strip=True)[:80]
                    break

        # Cari ukuran file dari teks sekitar
        ukuran_kb = 0
        parent_row = a.find_parent(["tr", "li", "div"])
        if parent_row:
            m = re.search(r"([\d.,]+)\s*(B|Kb|KB|Mb|MB|Gb|GB)\b",
                          parent_row.get_text(separator=" "))
            if m:
                nilai = float(m.group(1).replace(",", "."))
                satuan = m.group(2).upper()
                ukuran_kb = (
                    nilai / 1024 if satuan == "B" else
                    nilai         if "KB" in satuan else
                    nilai * 1024  if "MB" in satuan else
                    nilai * 1024 * 1024
                )

        hasil.append({
            "url":       url_abs,
            "label":     label,
            "ukuran_kb": ukuran_kb,
            "href_raw":  href,
        })

    # Urutkan: ukuran terbesar dulu (file fulltext hampir selalu lebih besar)
    hasil.sort(key=lambda x: x["ukuran_kb"], reverse=True)
    return hasil


# ─────────────────────────────────────────────────────────────────────
#  FUNGSI UTAMA — ENTRY POINT DARI pencari_skripsi.py
# ─────────────────────────────────────────────────────────────────────

def analisis_pdf_skripsi(
    session: requests.Session,
    url_pdf: str,
    delay: float = 0.5,
) -> HasilAnalisisPDF:
    """
    Analisis mendalam satu file PDF untuk menentukan apakah ini skripsi full text.

    Proses:
    1. Unduh 150KB awal + 100KB akhir PDF (via Range request jika didukung)
    2. Ekstrak teks dengan pdfminer
    3. Cari pola heading bab di dalam teks
    4. Tentukan status berdasarkan bab yang ditemukan

    Mengembalikan HasilAnalisisPDF.
    """
    hasil = HasilAnalisisPDF()

    if not url_pdf:
        hasil.catatan_teknis = "URL PDF kosong"
        return hasil

    if not PDFMINER_TERSEDIA:
        hasil.catatan_teknis = "pdfminer tidak tersedia — install: pip install pdfminer.six"
        return hasil

    time.sleep(delay)

    # Step 1: Unduh sebagian PDF
    pdf_bytes = _unduh_potongan_pdf(session, url_pdf)
    if not pdf_bytes:
        hasil.catatan_teknis = "Gagal mengunduh PDF (timeout, locked, atau bukan PDF)"
        return hasil

    # Step 2: Cek magic bytes — PDF harus dimulai dengan %PDF
    if not pdf_bytes[:5].startswith(b"%PDF"):
        hasil.catatan_teknis = "Bukan file PDF (magic bytes salah — kemungkinan halaman login HTML)"
        return hasil

    hasil.pdf_dibaca = True

    # Step 3: Ekstrak teks
    teks = ekstrak_teks_dari_bytes(pdf_bytes)
    if not teks or len(teks.strip()) < 100:
        # PDF bisa jadi scan/image — tidak ada teks yang bisa diekstrak
        hasil.catatan_teknis = "PDF tidak mengandung teks (kemungkinan scan/image-only)"
        # Untuk scan PDF, kita tidak bisa analisis bab — kembalikan unknown
        # tapi tandai pdf_dibaca=True karena file memang ada dan bisa diakses
        hasil.status = "unknown"
        hasil.catatan_teknis += " — cek manual di URL detail"
        return hasil

    # Step 4: Deteksi bab dari teks
    hasil.bab_dari_pdf = deteksi_bab_dari_teks(teks)
    hasil.estimasi_halaman = hitung_estimasi_halaman(teks)

    # Step 5: Tentukan status
    hasil.status = tentukan_status_dari_bab(hasil.bab_dari_pdf, pdf_dibaca=True)
    hasil.url_pdf_verified = url_pdf

    # Catatan informatif
    n_bab = len(hasil.bab_dari_pdf)
    n_kata = len(teks.split())
    hasil.catatan_teknis = (
        f"Teks diekstrak: {n_kata} kata | "
        f"{n_bab} bab terdeteksi | "
        f"~{hasil.estimasi_halaman} hal"
    )

    return hasil


def kumpulkan_pdf_per_bab(
    session: requests.Session,
    detail_soup: BeautifulSoup,
    base_url: str,
    delay: float = 0.5,
) -> HasilAnalisisPDF:
    """
    Untuk repository yang memecah skripsi menjadi banyak file per bab,
    kumpulkan semua URL, klasifikasikan ke bab, dan verifikasi aksesnya.

    Fungsi ini bekerja meski pdfminer tidak tersedia.

    Mengembalikan HasilAnalisisPDF.
    """
    hasil = HasilAnalisisPDF()

    # Kumpulkan semua PDF dari halaman detail
    semua_pdf = kumpulkan_semua_pdf_dari_halaman(detail_soup, base_url)

    if not semua_pdf:
        hasil.catatan_teknis = "Tidak ada link PDF ditemukan di halaman detail"
        return hasil

    if len(semua_pdf) == 1:
        # Single file — gunakan analisis_pdf_skripsi() sebagai gantinya
        hasil.catatan_teknis = "Single PDF — gunakan analisis_pdf_skripsi()"
        hasil.url_pdf_verified = semua_pdf[0]["url"]
        return hasil

    # Multi-file: klasifikasikan per bab
    url_per_bab_raw = klasifikasikan_pdf_per_bab(semua_pdf)

    if not url_per_bab_raw:
        # Tidak bisa klasifikasi — simpan semua URL sebagai-adalah
        hasil.url_per_bab = {f"file_{i+1}": p["url"] for i, p in enumerate(semua_pdf)}
        hasil.bab_dari_nama_file = []
        hasil.catatan_teknis = (
            f"{len(semua_pdf)} file PDF ditemukan tapi tidak bisa diklasifikasi per bab"
        )
        hasil.status = "unknown"
        return hasil

    # Verifikasi aksesibilitas
    bisa_diakses, terkunci = verifikasi_akses_batch(
        session, url_per_bab_raw, delay=delay
    )

    hasil.url_per_bab    = bisa_diakses
    hasil.bab_terkunci   = terkunci
    hasil.bab_dari_nama_file = list(bisa_diakses.keys())

    # Tentukan status berdasarkan bab yang bisa diakses
    if bisa_diakses:
        hasil.status = tentukan_status_dari_bab(
            list(bisa_diakses.keys()), pdf_dibaca=False
        )
    else:
        hasil.status = "locked"

    n_total  = len(url_per_bab_raw)
    n_akses  = len(bisa_diakses)
    n_locked = len(terkunci)
    hasil.catatan_teknis = (
        f"Multi-file: {n_total} file | "
        f"{n_akses} bisa diakses | "
        f"{n_locked} terkunci"
    )

    return hasil


def analisis_penuh(
    session: requests.Session,
    url_pdf: str,
    detail_soup: Optional[BeautifulSoup],
    base_url: str,
    delay: float = 0.5,
) -> HasilAnalisisPDF:
    """
    Analisis komprehensif: coba semua metode secara berurutan.

    Urutan prioritas:
    1. Deteksi multi-file per bab dari halaman detail (tidak perlu unduh PDF)
    2. Analisis isi PDF langsung (butuh pdfminer)

    Jika (1) sudah memberikan hasil "full", (2) dilewati untuk hemat bandwidth.

    Ini adalah fungsi yang dipanggil dari pencari_skripsi.py.
    """
    hasil_multifile = HasilAnalisisPDF()

    # Step 1: Cek apakah ada multi-file di halaman detail
    if detail_soup is not None:
        semua_pdf = kumpulkan_semua_pdf_dari_halaman(detail_soup, base_url)
        if len(semua_pdf) >= 2:
            hasil_multifile = kumpulkan_pdf_per_bab(
                session, detail_soup, base_url, delay
            )
            # Kalau sudah ketemu full dari multi-file, tidak perlu analisis PDF
            if hasil_multifile.status == "full":
                return hasil_multifile

    # Step 2: Analisis isi PDF langsung
    if url_pdf:
        hasil_pdf = analisis_pdf_skripsi(session, url_pdf, delay)

        # Gabungkan bab dari multi-file (jika ada) dengan bab dari PDF
        if hasil_multifile.bab_dari_nama_file:
            hasil_pdf.bab_dari_nama_file = hasil_multifile.bab_dari_nama_file
            hasil_pdf.url_per_bab        = hasil_multifile.url_per_bab
            hasil_pdf.bab_terkunci       = hasil_multifile.bab_terkunci

            # Re-tentukan status dengan data gabungan
            semua_bab = hasil_pdf.bab_semua
            if semua_bab:
                status_baru = tentukan_status_dari_bab(semua_bab, hasil_pdf.pdf_dibaca)
                # Ambil status yang lebih optimistis
                urutan = {"full": 0, "partial": 1, "unknown": 2, "locked": 3}
                if urutan.get(status_baru, 3) < urutan.get(hasil_pdf.status, 3):
                    hasil_pdf.status = status_baru

        return hasil_pdf

    # Tidak ada yang bisa dianalisis
    return hasil_multifile if hasil_multifile.bab_semua else HasilAnalisisPDF(
        catatan_teknis="Tidak ada URL PDF dan tidak ada halaman detail"
    )


# ─────────────────────────────────────────────────────────────────────
#  UTILITAS DISPLAY
# ─────────────────────────────────────────────────────────────────────

def format_bab_list(bab: list[str], max_tampil: int = 6) -> str:
    """Format list bab untuk ditampilkan di terminal."""
    if not bab:
        return "(tidak ada)"
    tampil = bab[:max_tampil]
    sisa = len(bab) - max_tampil
    result = " → ".join(tampil)
    if sisa > 0:
        result += f" (+{sisa} lainnya)"
    return result


def format_url_per_bab(url_per_bab: dict[str, str],
                       bab_terkunci: list[str]) -> str:
    """Format daftar URL per bab untuk ditampilkan di terminal."""
    if not url_per_bab and not bab_terkunci:
        return ""
    baris = []
    for nama, url in url_per_bab.items():
        baris.append(f"  ✓ {nama:<30} {url}")
    for nama in bab_terkunci:
        baris.append(f"  ✗ {nama:<30} [TERKUNCI]")
    return "\n".join(baris)


# ─────────────────────────────────────────────────────────────────────
#  SELF-CHECK — jalankan langsung untuk test
# ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("  pdf_analyzer.py — self check")
    print("=" * 60)
    print(f"  pdfminer tersedia : {'Ya' if PDFMINER_TERSEDIA else 'Tidak (install: pip install pdfminer.six)'}")
    print(f"  Jumlah pola bab   : {len(POLA_BAB)}")
    print(f"  Bab wajib (full)  : {', '.join(BAB_WAJIB)}")
    print()

    # Test deteksi bab dari teks dummy
    teks_contoh = """
    BAB I PENDAHULUAN
    1.1 Latar Belakang Masalah
    Penelitian ini bertujuan untuk menganalisis...

    BAB II TINJAUAN PUSTAKA
    2.1 Landasan Teori

    BAB III METODOLOGI PENELITIAN
    3.1 Desain Penelitian
    3.2 Populasi dan Sampel

    BAB IV HASIL DAN PEMBAHASAN
    4.1 Hasil Penelitian
    4.2 Analisis Data

    BAB V KESIMPULAN DAN SARAN
    5.1 Kesimpulan

    DAFTAR PUSTAKA
    """

    bab = deteksi_bab_dari_teks(teks_contoh)
    status = tentukan_status_dari_bab(bab)

    print(f"  Teks contoh → bab terdeteksi: {bab}")
    print(f"  Status: {status}")
    print()

    if len(sys.argv) > 1:
        # Test dengan URL nyata jika diberikan
        url_test = sys.argv[1]
        print(f"  Test URL: {url_test}")
        s = requests.Session()
        s.headers["User-Agent"] = "Mozilla/5.0 (compatible; PDFAnalyzerTest/1.0)"
        hasil = analisis_pdf_skripsi(s, url_test)
        print(f"  Status      : {hasil.status}")
        print(f"  Bab dari PDF: {format_bab_list(hasil.bab_dari_pdf)}")
        print(f"  Halaman est : ~{hasil.estimasi_halaman}")
        print(f"  Catatan     : {hasil.catatan_teknis}")
