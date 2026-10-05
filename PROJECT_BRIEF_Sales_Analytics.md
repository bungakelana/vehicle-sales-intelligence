# Vehicle Sales & Customer Intelligence Dashboard
### Project Brief untuk Claude Code — Portofolio Data Analyst

> **Cara pakai dokumen ini:** simpan file ini di root folder proyek sebagai `PROJECT_BRIEF.md` (atau `CLAUDE.md`), lalu jalankan Claude Code dan minta: *"Baca PROJECT_BRIEF.md dan kerjakan Fase 0 sampai selesai."* Kerjakan per fase, review hasilnya, baru lanjut ke fase berikutnya.

---

## 1. Ringkasan Proyek

| Item | Keterangan |
|---|---|
| **Judul** | Vehicle Sales & Customer Intelligence Dashboard |
| **Domain** | Penjualan kendaraan (dealer / distributor) — Indonesia |
| **Tujuan** | Menganalisis performa penjualan, efektivitas diskon, ketergantungan leasing, sebaran geografis kabupaten/kota, dan efisiensi operasional (SPK → STNK) |
| **Output** | (1) Website dashboard statis yang ringan & interaktif, diakses dari web portofolio, (2) notebook analisis, (3) laporan insight singkat |
| **Tools** | Analisis: Python (pandas, geopandas, statsmodels, scikit-learn) · Web: Astro + Tailwind CSS + Apache ECharts (website statis, tanpa server) |
| **Target audiens** | Recruiter / hiring manager untuk posisi Data Analyst, Business Analyst, Sales Analyst |

**Business questions utama** (ini "cerita" portofolio kamu):

1. Di kabupaten/kota mana penjualan kita kuat, dan di mana ada *white space* (potensi yang belum digarap)?
2. Apakah diskon benar-benar menaikkan volume, atau hanya menggerus margin?
3. Seberapa besar ketergantungan pada leasing, dan leasing mana yang paling berisiko jika kredit diperketat?
4. Di tahap mana proses pengiriman unit & pengurusan STNK paling sering macet?
5. Salesman / SPV mana yang produktif *dan* disiplin diskon?

---

## 2. Konteks Pasar 2026 (untuk bagian "Why this matters" di dashboard)

Gunakan konteks ini di halaman *About / Executive Summary* agar analisis terlihat relevan dengan kondisi industri saat ini:

- **Pasar mobil nasional moderat.** Gaikindo mempertahankan target penjualan 2026 di **850.000 unit** (per akhir September 2026), dengan catatan daya beli kelas menengah masih tertekan. Juli 2026 mencatat ~81 ribu unit, tren membaik.
- **Kendaraan niaga ikut siklus komoditas.** Gaikindo menilai permintaan truk & pikap sangat bergantung pada pertumbuhan ekonomi dan harga komoditas — relevan untuk wilayah perkebunan/tambang (mis. Riau, Sumatera, Kalimantan).
- **Leasing memperketat kredit.** NPF gross multifinance naik ke **~3,04% (Agustus 2026)** vs ~2,55% di pertengahan 2025; pembiayaan kendaraan bermotor terkontraksi tipis secara tahunan, dan puluhan perusahaan pembiayaan memiliki NPF di atas 5%.
- **Aturan DP 0% (POJK 35/2025)** hanya berlaku untuk perusahaan pembiayaan yang sehat dengan NPF rendah, dan dibatasi maksimal 20% portofolio.
- **Pembiayaan kendaraan listrik tumbuh >30% YoY** meski pembiayaan mobil konvensional menurun.

**Implikasi untuk analisis:** dealer yang porsi leasing-nya tinggi dan terkonsentrasi di sedikit leasing partner rentan saat approval kredit diperketat. Diskon yang tidak terkontrol makin mahal saat volume pasar stagnan. → Inilah sudut pandang yang membuat proyek ini "nyambung" dengan kondisi pasar.

Sumber (cantumkan di dashboard):
- Gaikindo target 850 ribu unit — Suara.com, 23 Sep 2026
- Penjualan Juli 2026 — Kompas Otomotif, 9 Agu 2026
- Prospek kendaraan niaga 2026 — Kontan, Mar 2026
- NPF & pembiayaan kendaraan Agustus 2026 — Kontan Keuangan, Okt 2026
- 42 perusahaan pembiayaan NPF > 5% — Fortune IDN, Sep 2026
- POJK 35/2025 DP 0% — Bisnis.com, Jan 2026

---

## 3. Data Dictionary

Data mentah: satu baris = satu unit kendaraan terjual (transaksi billing).

| # | Kolom asli | Nama baru (snake_case) | Tipe | Kategori | Catatan |
|---|---|---|---|---|---|
| 1 | No. | `row_no` | int | ID | Buang setelah load |
| 2 | Filling Number | `filling_number` | str | ID | |
| 3 | No. Faktur | `invoice_no` | str | ID | Kunci unik transaksi (cek duplikat) |
| 4 | Tgl Billing | `billing_date` | date | **Tanggal** | Tanggal utama untuk analisis tren |
| 5 | Spes No | `spec_no` | str | **Produk** | Kode spesifikasi / tipe unit |
| 6 | No SO | `so_no` | str | ID | |
| 7 | No Customer | `customer_id` | str | **Customer** | Untuk repeat order & fleet |
| 8 | Nama Customer | `customer_name` | str | 🔒 PII | Anonimkan; ekstrak flag `PT/CV/UD` dulu |
| 9 | Address | `address` | str | 🔒 PII | Hapus setelah ekstrak wilayah |
| 10 | City | `city` | str | **Geografi** | Kabupaten/kota — wajib dinormalisasi |
| 11 | Handphone | `phone_mobile` | str | 🔒 PII | Hapus |
| 12 | Telp Rumah | `phone_home` | str | 🔒 PII | Hapus |
| 13 | Telp Kantor | `phone_office` | str | 🔒 PII | Hapus (boleh buat flag `has_office_phone`) |
| 14 | Nama STNK | `stnk_name` | str | 🔒 PII | Buat flag `stnk_same_as_buyer` lalu hapus |
| 15 | Alamat STNK | `stnk_address` | str | 🔒 PII | Hapus |
| 16 | Chasis | `chassis_no` | str | 🔒 Sensitif | Hapus / hash |
| 17 | No. Mesin | `engine_no` | str | 🔒 Sensitif | Hapus / hash |
| 18 | Karoseri Spec. | `body_spec` | str | **Produk** | Jenis karoseri (box, bak, dump, dll.) |
| 19 | Color Description | `color` | str | **Produk** | |
| 20 | Actual Physical GI Date | `actual_gi_date` | date | **Proses** | Unit benar-benar keluar gudang |
| 21 | Tgl. GI | `gi_date` | date | **Proses** | Goods Issue di sistem |
| 22 | Tgl.BSTK | `handover_date` | date | **Proses** | Serah terima ke customer |
| 23 | Leasing | `leasing` | str | **Pembayaran** | Kosong/“CASH” = tunai |
| 24 | Salesman name | `salesman` | str | **Sales** | Anonimkan → `SLS-001` |
| 25 | SPV Name | `supervisor` | str | **Sales** | Anonimkan → `SPV-01` |
| 26 | Sales Point | `sales_point` | str | **Cabang** | |
| 27 | Package Code | `package_code` | str | **Produk** | Paket program penjualan |
| 28 | BookNumber | `book_no` | str | ID | |
| 29 | Jatuh Tempo | `due_date` | date | **Piutang** | `due_date - billing_date` = term pembayaran |
| 30 | No Polisi | `plate_no` | str | 🔒 Sensitif | Ambil kode wilayah (BM, B, dll.) lalu hapus |
| 31 | No SPK | `spk_no` | str | ID | |
| 32 | Harga Unit | `unit_price` | float | **Harga** | Harga OTR / list |
| 33 | Harga Discount | `price_after_discount` | float | **Harga** | ⚠️ Verifikasi: harga setelah diskon atau nominal diskon? |
| 34 | Selesai STNK | `stnk_done_date` | date | **Proses** | |
| 35 | Cabang Serah Terima | `handover_branch` | str | **Cabang** | Bandingkan dengan `sales_point` |
| 36 | Total Discount | `total_discount` | float | **Harga** | |

> ⚠️ **Asumsi yang harus dicek di Fase 1:** apakah `unit_price - price_after_discount ≈ total_discount`? Jika tidak, dokumentasikan definisi yang benar di `docs/data_notes.md`.

---

## 4. ⚠️ Privasi Data (WAJIB sebelum publikasi)

Data ini berisi informasi pribadi pelanggan (nama, alamat, nomor HP, nomor rangka/mesin, nomor polisi) dan kemungkinan data rahasia perusahaan. Karena dashboard akan **dipublikasikan di web**, lakukan ini:

1. **Jangan pernah** commit data mentah ke GitHub. Masukkan `data/raw/` ke `.gitignore`.
2. Buat script `src/anonymize.py` yang menghasilkan `data/processed/sales_clean.parquet` **tanpa kolom PII**.
3. Ganti nama salesman/SPV/leasing dengan kode (`SLS-001`, `LEASING-A`) — atau minta izin eksplisit.
4. Pertimbangkan **menskalakan angka rupiah** (mis. dikali faktor acak 0,8–1,2 atau dijadikan indeks) agar data finansial perusahaan tidak bocor, dan tulis disclaimer: *"Data telah dianonimkan dan dimodifikasi untuk keperluan portofolio."*
5. Pastikan sudah mendapat izin dari pemilik data (perusahaan) — ini juga terkait UU PDP (UU No. 27/2022).
6. Opsi paling aman: buat **synthetic dataset** dengan distribusi meniru data asli (pakai `faker` + sampling distribusi) untuk versi publik.

---

## 5. Arsitektur & Tech Stack (tanpa Streamlit)

### 5.1 Prinsip arsitektur: *"Python di build-time, HTML statis di run-time"*

Semua komputasi berat (cleaning, agregasi, forecast, clustering) dijalankan **sekali** di Python. Hasilnya diekspor menjadi file JSON kecil yang sudah teragregasi, lalu dibaca oleh website statis. Tidak ada server Python yang berjalan saat recruiter membuka dashboard.

```
 ┌────────────────────────┐   build   ┌──────────────────────┐  deploy  ┌───────────────────┐
 │ PYTHON (analytics/)    │ ────────► │ site/public/data/    │ ───────► │ CDN statis        │
 │ load → clean → anonim  │  export   │ *.json (≤ 300 KB gz) │          │ (Cloudflare Pages │
 │ → features → metrics   │           │ geo/*.topojson       │          │  / GitHub Pages)  │
 │ → forecast → cluster   │           └──────────┬───────────┘          └─────────┬─────────┘
 └────────────────────────┘                      │ dibaca saat build              │
                                      ┌──────────▼───────────┐                    │
                                      │ ASTRO (site/)        │  HTML + CSS + JS   │
                                      │ halaman, komponen,   │ ───────────────────┘
                                      │ chart di-hydrate     │
                                      │ hanya saat terlihat  │
                                      └──────────────────────┘
```

**Kenapa bukan Streamlit:** Streamlit butuh server Python yang menyala (cold start 10–30 detik di hosting gratis, app "tertidur"), tampilannya mudah dikenali sebagai template, dan sulit di-custom. Website statis dibuka < 1,5 detik, gratis selamanya, bisa di-embed langsung di domain portofolio, dan memperlihatkan kemampuan *front-end* sekaligus *analytics*.

### 5.2 Rekomendasi stack

| Lapisan | Pilihan | Alasan |
|---|---|---|
| Analisis | `pandas`, `numpy`, `pyarrow` | Standar industri |
| Statistik / ML | `statsmodels` (SARIMA), `scikit-learn` (KMeans, IsolationForest) | Cukup ringan, tanpa Prophet |
| Geo (build-time) | `geopandas` + **mapshaper** (simplify → TopoJSON) | File peta kecil (target < 150 KB) |
| Visual notebook | `matplotlib` / `seaborn` | Hanya untuk eksplorasi |
| Export data | `orjson` / `json` → `site/public/data/` | Data siap pakai untuk web |
| **Framework web** | **Astro** (static site generator) | Default 0 KB JavaScript; JS hanya dikirim ke komponen interaktif (*islands*) |
| Styling | **Tailwind CSS** + CSS variables (design tokens) | CSS yang tidak terpakai dibuang otomatis; dark mode mudah |
| Chart | **Apache ECharts** (impor modular / tree-shaken) | Peta choropleth, treemap, heatmap, scatter, dark theme, render Canvas yang cepat |
| Interaktivitas | TypeScript vanilla (tanpa React) | Filter & slider stress test cukup dengan JS biasa |
| Font | **Inter** (variable, self-hosted, subset Latin, `font-display: swap`) | Tanpa request ke Google Fonts |
| Ikon | Lucide (SVG inline) | Hanya ikon yang dipakai yang masuk bundle |
| Kualitas | `ruff`, `pytest`, Lighthouse CI | Menjaga skor performa |
| Hosting | **Cloudflare Pages** (atau GitHub Pages / Netlify) | Gratis, CDN global, custom domain |

### 5.3 Alternatif yang dipertimbangkan

| Opsi | Kelebihan | Kekurangan | Verdict |
|---|---|---|---|
| **Astro + ECharts** | Sangat ringan, desain bebas, SEO baik, terlihat profesional | Perlu sedikit belajar JS/TS | ✅ **Rekomendasi utama** |
| Vite + HTML/JS vanilla + ECharts | Paling sederhana, tanpa framework | Tanpa komponen/routing, kode cepat berantakan saat halaman bertambah | Cocok jika ingin 1 halaman saja |
| Observable Framework | Data loader bisa ditulis di Python, dibuat khusus untuk dashboard | Komunitas lebih kecil, tampilan lebih "khas Observable" | Alternatif bagus |
| Evidence.dev | Dashboard dari SQL + Markdown, cepat dibuat | Analisis berbasis SQL, bukan Python; kurang fleksibel secara desain | Kurang pas dengan tujuan "Python" |
| React/Next.js + Recharts | Ekosistem besar | Bundle jauh lebih berat, berlebihan untuk dashboard statis | ❌ |

### 5.4 Strategi data agar tetap ringan dan filter tetap interaktif

1. **Jangan kirim data per transaksi ke browser.** Ekspor tabel fakta teragregasi dengan grain: `year_month × kabupaten × model_family × payment_type × sales_point` (berisi unit, gross, discount, net, median lead time). Biasanya hanya ribuan baris.
2. Simpan sebagai **JSON kolumnar** (`{"cols": [...], "rows": [[...]]}`) atau array-of-arrays agar ukurannya kecil; CDN mengompresi otomatis (gzip/brotli).
3. Filter (periode, cabang, kabupaten, tipe, cash/leasing) dihitung di browser dengan fungsi `groupBy` sederhana di TypeScript.
4. Data yang mahal dihitung (forecast, cluster, anomaly, quadrant salesman) diekspor **sudah jadi** sebagai JSON terpisah.
5. **Budget ukuran:** semua data ≤ 300 KB (gzip), TopoJSON ≤ 150 KB, JS awal ≤ 120 KB (gzip), CSS ≤ 20 KB.

**GeoJSON kabupaten/kota Indonesia:** gunakan data batas administrasi (mis. GADM level 2 atau repo GeoJSON kabupaten Indonesia di GitHub). Potong hanya provinsi yang relevan, simplify dengan mapshaper (`-simplify 5% keep-shapes`), lalu ubah ke TopoJSON. Siapkan tabel mapping nama kota di data → nama kabupaten di peta (`analytics/data/geo/city_mapping.csv`), karena penulisan nama sering tidak konsisten (`PEKANBARU`, `Kota Pekanbaru`, `PKU`).

---

## 6. Struktur Folder

```
vehicle-sales-intelligence/
├── PROJECT_BRIEF.md                ← dokumen ini
├── README.md                       ← versi portofolio (Fase 7)
├── .gitignore                      ← analytics/data/raw/ WAJIB masuk
├── analytics/                      ← semua kode PYTHON
│   ├── requirements.txt
│   ├── data/
│   │   ├── raw/                    ← data asli (TIDAK di-commit)
│   │   ├── processed/              ← sales_clean.parquet (sudah anonim)
│   │   └── geo/                    ← geojson mentah + city_mapping.csv
│   ├── notebooks/
│   │   ├── 01_data_audit.ipynb
│   │   ├── 02_eda.ipynb
│   │   ├── 03_discount_analysis.ipynb
│   │   ├── 04_leasing_risk.ipynb
│   │   ├── 05_geo_analysis.ipynb
│   │   └── 06_forecast_segmentation.ipynb
│   ├── src/
│   │   ├── config.py               ← path, konstanta
│   │   ├── load.py                 ← baca Excel/CSV mentah
│   │   ├── clean.py                ← cleaning & standarisasi
│   │   ├── anonymize.py            ← hapus/hash PII
│   │   ├── features.py             ← feature engineering
│   │   ├── metrics.py              ← fungsi KPI
│   │   ├── models.py               ← forecast, clustering, anomaly
│   │   └── export.py               ← tulis JSON ke site/public/data/
│   ├── build_data.py               ← 1 perintah: raw → JSON siap web
│   └── tests/test_metrics.py
├── site/                           ← WEBSITE (Astro)
│   ├── astro.config.mjs
│   ├── package.json
│   ├── public/
│   │   ├── data/                   ← *.json hasil export (di-commit, sudah anonim)
│   │   ├── geo/kabupaten.topojson
│   │   ├── fonts/inter-var.woff2
│   │   └── og-image.png            ← preview saat link dibagikan
│   └── src/
│       ├── styles/tokens.css       ← warna, spasi, radius (light & dark)
│       ├── lib/
│       │   ├── data.ts             ← fetch + cache + filter + groupBy
│       │   ├── format.ts           ← Rp 1,2 M · 12,3% · tanggal (id-ID)
│       │   └── echarts.ts          ← impor modular + tema custom
│       ├── components/
│       │   ├── KpiCard.astro
│       │   ├── FilterBar.astro
│       │   ├── ChartCard.astro     ← wrapper: judul-insight, chart, tabel fallback
│       │   ├── Takeaways.astro
│       │   └── ThemeToggle.astro
│       ├── layouts/Base.astro      ← <head>, nav, footer, meta SEO
│       └── pages/
│           ├── index.astro         ← Executive Overview + ringkasan cerita
│           ├── geography.astro
│           ├── product.astro
│           ├── discount.astro
│           ├── financing.astro     ← termasuk slider stress test
│           ├── sales-team.astro
│           ├── operations.astro
│           ├── outlook.astro       ← forecast + rekomendasi
│           └── about.astro         ← metodologi, data notes, tech stack
└── .github/workflows/deploy.yml    ← build Astro → Cloudflare/GitHub Pages
```

### 6.1 Kontrak data (output `analytics/build_data.py`)

| File | Isi | Dipakai di halaman |
|---|---|---|
| `meta.json` | Periode data, tanggal update, daftar nilai filter | Semua |
| `fact_monthly.json` | Tabel fakta teragregasi (grain di 5.4) | Overview, Geography, Product, Financing |
| `discount.json` | Distribusi diskon per tipe, pola akhir bulan, hasil regresi diskon→volume, anomali | Discount |
| `leasing.json` | Share per leasing, HHI, % leasing per kabupaten, baseline stress test | Financing |
| `salesforce.json` | Metrik per salesman/SPV (anonim) + label kuadran | Sales Team |
| `leadtime.json` | Median & P90 per tahap, per cabang, % SLA breach | Operations |
| `forecast.json` | Aktual + forecast + interval kepercayaan, MAPE | Outlook |
| `clusters.json` | Label cluster per kabupaten + profil cluster | Geography, Outlook |
| `insights.json` | Teks Key Takeaways per halaman (dihasilkan Python dengan angka aktual) | Semua |

> Tips: buat **`insights.json` di Python** (mis. *"Top-5 kabupaten = 62% unit"*), sehingga teks insight di web selalu sinkron dengan data dan tidak perlu diketik manual.

---

## 7. Feature Engineering

Buat di `src/features.py`:

| Fitur | Rumus / logika | Dipakai untuk |
|---|---|---|
| `discount_pct` | `total_discount / unit_price` | Analisis diskon |
| `net_price` | `unit_price - total_discount` | Revenue bersih |
| `payment_type` | `"Cash"` jika leasing kosong/“CASH”, selain itu `"Leasing"` | Financing mix |
| `customer_type` | `"Fleet/Corporate"` jika nama mengandung PT/CV/UD/KOPERASI atau customer beli ≥ 3 unit; selain itu `"Retail"` | Segmentasi |
| `is_repeat` | `customer_id` muncul > 1 kali | Loyalitas |
| `units_per_customer` | groupby `customer_id` | Fleet detection |
| `days_billing_to_gi` | `gi_date - billing_date` | Lead time |
| `days_gi_to_physical` | `actual_gi_date - gi_date` | Lead time gudang |
| `days_gi_to_handover` | `handover_date - actual_gi_date` | Lead time pengiriman |
| `days_to_stnk` | `stnk_done_date - billing_date` | Lead time STNK |
| `payment_term_days` | `due_date - billing_date` | Piutang |
| `cross_branch` | `sales_point != handover_branch` | Efisiensi cabang |
| `plate_region` | prefix huruf `plate_no` (BM, B, BK…) | Validasi wilayah |
| `year_month`, `quarter`, `week_of_month`, `is_month_end` | dari `billing_date` | Seasonality & pola diskon akhir bulan |
| `kabupaten_std`, `provinsi` | hasil mapping `city` | Peta |
| `model_family` | ekstrak dari `spec_no`/`package_code` | Product mix |

---

## 8. Analisis yang Direkomendasikan

Disusun dari yang **wajib (core)** sampai **pembeda (advanced)**. Untuk portofolio, kualitas cerita > jumlah chart.

### 8.1 Executive Overview — *core*
- KPI cards: Total unit, Gross revenue, Net revenue, Rata-rata diskon %, % Leasing, Median lead time SPK→STNK, Jumlah customer, % Repeat customer.
- Tren bulanan unit & revenue (line + bar combo) dengan perbandingan YoY / MoM.
- **Insight box** otomatis: "Penjualan Q3 naik X% vs Q2, didorong oleh kabupaten Y dan tipe Z."

### 8.2 Geographic Insights — *core, sangat menarik secara visual*
- **Choropleth map** unit terjual per kabupaten/kota.
- Ranking kabupaten: unit, revenue, avg diskon, % leasing.
- **Market concentration:** berapa % penjualan dari Top-5 kabupaten (Pareto 80/20).
- **White space analysis:** bandingkan penjualan per kabupaten dengan indikator eksternal (PDRB, jumlah penduduk, atau luas perkebunan dari BPS) → kabupaten dengan potensi tinggi tapi penjualan rendah = peluang ekspansi. *Ini yang paling disukai recruiter karena actionable.*
- Analisis `cross_branch`: seberapa sering unit dijual di satu cabang tapi diserahterimakan di cabang lain.

### 8.3 Product Mix — *core*
- Treemap: model → karoseri → warna.
- Tipe unit terlaris per kabupaten (heatmap kabupaten × tipe).
- Preferensi karoseri per wilayah (mis. dump truck di area tambang, box di kota).
- Preferensi warna (berguna untuk perencanaan stok).

### 8.4 Discount & Pricing Effectiveness — *pembeda utama*
- Distribusi `discount_pct` (histogram + box plot per tipe unit).
- **Diskon vs volume:** scatter per bulan/tipe — apakah diskon lebih besar benar-benar menaikkan unit? Hitung korelasi & regresi sederhana (*price elasticity proxy*).
- **Month-end discount spike:** bandingkan diskon di minggu terakhir bulan vs minggu lain (indikasi kejar target).
- **Discount leakage per salesman:** salesman dengan diskon rata-rata jauh di atas median untuk tipe unit yang sama.
- Diskon Cash vs Leasing (biasanya pola berbeda karena subsidi leasing).
- **Anomaly detection** (IsolationForest / z-score) untuk transaksi diskon tidak wajar.

### 8.5 Financing & Leasing Risk — *paling relevan dengan pasar 2026*
- Cash vs Leasing share, tren per bulan.
- Market share tiap leasing partner + **Herfindahl-Hirschman Index (HHI)** untuk mengukur konsentrasi.
- % leasing per kabupaten → wilayah mana paling bergantung pada kredit.
- **Stress test sederhana:** "Jika approval leasing turun 10% / 20% (karena NPF industri naik ke ~3%), berapa unit & revenue yang berisiko?" — tampilkan sebagai slider interaktif. *Fitur ini sangat kuat untuk portofolio.*
- Payment term (`payment_term_days`) per leasing.

### 8.6 Sales Team Performance — *core*
- Leaderboard salesman: unit, revenue, avg diskon, % leasing.
- **Quadrant chart:** sumbu X = unit terjual, sumbu Y = avg diskon % → 4 kuadran ("Star", "Discount-driven", "Efficient-low volume", "Needs coaching").
- Performa per SPV (tim) dan per sales point.
- Konsistensi bulanan (koefisien variasi penjualan per salesman).

### 8.7 Operations & Lead Time — *pembeda*
- **Funnel waktu proses:** Billing → GI → Physical GI → BSTK → STNK selesai (median hari per tahap).
- Box plot lead time per cabang & per leasing.
- Persentase unit dengan STNK > 30 hari (SLA breach).
- Identifikasi bottleneck: tahap mana menyumbang delay terbesar.

### 8.8 Customer Analytics — *advanced*
- Retail vs Fleet/Corporate: kontribusi unit, diskon, dan payment type.
- Repeat customer rate & top fleet customers (anonim).
- **RFM-like segmentation** untuk customer korporat.
- `stnk_same_as_buyer`: indikasi pembelian untuk pihak lain / perusahaan.

### 8.9 Forecast & Segmentation — *advanced*
- Forecast unit 3–6 bulan ke depan (SARIMA/Prophet) dengan confidence interval; evaluasi MAPE pada data holdout.
- **K-Means clustering kabupaten** berdasarkan (unit, avg diskon, % leasing, pertumbuhan) → label seperti "Core market", "Growth market", "Credit-dependent", "Price-sensitive".
- Halaman **Recommendations**: 3–5 rekomendasi bisnis konkret yang diturunkan dari analisis di atas.

### Prioritas jika waktu terbatas
1. Executive Overview  2. Geographic (map + white space)  3. Discount Effectiveness  4. Leasing Risk + stress test  5. Recommendations.
Sisanya bisa ditambahkan sebagai versi 2.

---

## 9. Desain Dashboard (Web Best Practice)

### 9.1 Konsep: *"Case study yang bisa dieksplor"*
Recruiter rata-rata hanya melihat portofolio 1–2 menit. Jadi desainnya menggabungkan dua mode:
1. **Narasi (scroll)** di halaman utama: hero dengan 1 kalimat insight terkuat → 4–6 KPI → 3 temuan kunci, masing-masing dengan 1 chart → rekomendasi → tombol "Explore dashboard".
2. **Eksplorasi** di halaman per topik, dengan filter bar *sticky* untuk yang ingin menggali lebih dalam.

Prinsip lain:
- **Satu halaman = satu pertanyaan bisnis.** Judul chart berupa insight (*"3 leasing menguasai 78% transaksi kredit"*), bukan "Leasing Share".
- Pola tiap halaman: KPI → chart utama → chart pendukung → **Key Takeaways**.
- Filter: periode, sales point, kabupaten, tipe unit, cash/leasing. Simpan status filter di **URL query string** (`?period=2025Q3&branch=PKU`) agar tampilan tertentu bisa dibagikan lewat link.
- Format Indonesia via `Intl.NumberFormat('id-ID')`: `Rp 1,2 M`, `Rp 350 jt`, `12,3%`.

### 9.2 Layout (desktop ≥ 1024 px)

```
┌───────────────────────────────────────────────────────────────────┐
│ ◆ Vehicle Sales Intelligence   Overview Geo Product Discount ... ☾ │ ← nav sticky
├───────────────────────────────────────────────────────────────────┤
│ [Periode ▾] [Cabang ▾] [Kabupaten ▾] [Tipe ▾] [Cash|Leasing] Reset │ ← filter bar sticky
├────────────┬────────────┬────────────┬────────────┬───────────────┤
│ Unit       │ Net Revenue│ Avg Disc   │ % Leasing  │ Lead time STNK │
│ 1.240 ▲8%  │ Rp 412 M   │ 6,3% ▼0,4  │ 68%        │ 21 hari        │ ← KPI + sparkline
│ ╱╲╱‾‾      │ ╱‾╲╱‾      │ ‾╲╱╲_      │ ‾‾╲_╱      │ ╲_╱‾╲          │
├────────────┴────────────┴─────┬──────┴────────────┴───────────────┤
│ Penjualan naik 8% QoQ,         │ 62% unit dari 5 kabupaten          │
│ didorong segmen dump truck     │                                    │
│ [bar + line bulanan]           │ [peta choropleth]                  │
├────────────────────────────────┴───────────────────────────────────┤
│ 💡 Key Takeaways  ·  1) …  2) …  3) …                               │
└────────────────────────────────────────────────────────────────────┘
```
Mobile (< 640 px): KPI menjadi grid 2 kolom, chart 1 kolom, filter masuk *bottom sheet*, nav menjadi menu.

### 9.3 Design tokens (light & dark)

| Token | Light | Dark | Dipakai untuk |
|---|---|---|---|
| `--bg` | `#F7F8FA` | `#0B1220` | Latar halaman |
| `--surface` | `#FFFFFF` | `#111A2B` | Card |
| `--border` | `#E5E7EB` | `#1F2A3D` | Garis card/tabel |
| `--text` | `#0F172A` | `#E5E7EB` | Teks utama |
| `--muted` | `#6B7280` | `#94A3B8` | Label, caption |
| `--primary` | `#0F2A44` | `#7FB3E6` | Judul, brand |
| `--accent` | `#1F77B4` | `#4EA1E8` | Seri data utama |
| `--highlight` | `#F28C28` | `#F5A65B` | Sorotan insight |
| `--positive` | `#2E9E6A` | `#3DC184` | Delta naik |
| `--negative` | `#D64545` | `#F07171` | Delta turun |

- **Warna data:** maksimal 1 warna sorotan per chart; seri lain abu-abu. Ini membuat insight langsung terbaca.
- Palet kategorikal untuk ≤ 6 kategori; kategori lain digabung menjadi "Lainnya".
- Peta: skala sequential 1 hue (biru muda → navy), 5 kelas *quantile*.
- Tema ECharts dibuat dari token yang sama dan berganti otomatis mengikuti `prefers-color-scheme` + toggle manual.
- Tipografi: Inter; angka KPI memakai `font-variant-numeric: tabular-nums`. Skala: 32 / 24 / 18 / 14 / 12 px.
- Spasi grid 8 px, radius card 12 px, shadow sangat halus (atau border saja).

### 9.4 Performance best practice
- **Tidak ada JS di halaman narasi** kecuali chart; chart di-hydrate dengan `client:visible` (hanya dimuat saat di-scroll ke layar).
- ECharts diimpor **modular** (hanya `LineChart`, `BarChart`, `MapChart`, `TreemapChart`, `HeatmapChart`, `ScatterChart` + komponen yang dipakai) dan memakai `CanvasRenderer`.
- Data di-`fetch` sekali lalu di-cache di memori; filter memakai debounce 150 ms.
- Font self-hosted + `preload`; gambar `og-image` dalam format WebP/AVIF.
- Card dibuat dengan tinggi tetap + **skeleton** agar tidak ada layout shift (CLS ≈ 0).
- **Target Lighthouse:** Performance ≥ 95, Accessibility ≥ 95, Best Practices 100, SEO 100. LCP < 1,5 s di 4G. Total transfer halaman utama < 400 KB.

### 9.5 Aksesibilitas & kredibilitas
- Kontras teks ≥ 4.5:1 (cek di dua tema). Jangan mengandalkan warna saja; pakai label dan ▲▼.
- Setiap chart punya `aria-label` berisi kesimpulan, plus tombol **"Lihat tabel"** (tabel data sebagai fallback & bisa di-copy).
- Navigasi keyboard untuk filter dan tab; `focus-visible` yang jelas.
- Tombol **Download CSV** untuk data hasil filter (dibuat di browser, tanpa server).
- Footer: *"Data telah dianonimkan dan dimodifikasi untuk keperluan portofolio"*, tanggal update data, link GitHub, LinkedIn, dan CV.
- Meta SEO + Open Graph (judul, deskripsi, `og-image`) agar link terlihat bagus saat dibagikan di LinkedIn/WhatsApp.

### 9.6 Detail "wow" yang tetap ringan
- KPI angka *count-up* singkat (≤ 600 ms, nonaktif jika `prefers-reduced-motion`).
- Klik kabupaten di peta → semua chart di halaman ikut terfilter (*cross-filtering*).
- Slider **stress test leasing** (0–30%) yang langsung memperbarui unit & revenue berisiko.
- Quadrant chart salesman dengan anotasi nama kuadran.
- Anotasi di chart tren (mis. "Program diskon Lebaran", "Lonjakan akhir kuartal").

---

## 10. Deployment ke Web Portofolio

| Opsi | Cara | Catatan |
|---|---|---|
| **A. Cloudflare Pages** (rekomendasi) | Hubungkan repo GitHub → build command `npm run build` (root `site/`) → output `dist/` | Gratis, CDN cepat di Asia, preview per branch, custom domain |
| B. GitHub Pages | GitHub Actions `deploy.yml` → upload `site/dist` | Gratis, cocok jika portofolio sudah di GitHub Pages |
| C. Netlify / Vercel | Import repo, preset Astro | Gratis untuk personal |

**Integrasi ke web portofolio (pilih salah satu):**
1. **Subdomain** (paling profesional): `sales.namakamu.dev` → arahkan DNS CNAME ke Cloudflare Pages.
2. **Sub-path** di portofolio: build Astro dengan `base: '/projects/sales-intelligence'` lalu salin `dist/` ke folder portofolio.
3. **Embed** halaman tertentu dengan iframe (hanya untuk preview kecil di kartu proyek):

```html
<iframe src="https://sales.namakamu.dev/?embed=1" loading="lazy"
        title="Vehicle Sales Intelligence" width="100%" height="720"
        style="border:0;border-radius:12px"></iframe>
```
Mode `?embed=1` menyembunyikan nav & footer.

**Alur update data:**
```bash
cd analytics && python build_data.py      # raw → anonim → JSON di site/public/data
cd ../site && npm run build               # build website statis
git push                                  # Cloudflare/GitHub Pages deploy otomatis
```

---

## 11. Rencana Kerja per Fase (prompt untuk Claude Code)

Salin prompt di bawah ke Claude Code satu per satu.

**Fase 0 — Setup**
> Buat struktur folder sesuai Bagian 6. Di `analytics/`: `requirements.txt` dan `src/config.py`. Di `site/`: inisialisasi proyek Astro (TypeScript strict) dengan Tailwind CSS dan Apache ECharts. Buat `.gitignore` (wajib berisi `analytics/data/raw/`, `node_modules`, `dist`).

**Fase 1 — Data Audit**
> Buat `analytics/src/load.py` dan `notebooks/01_data_audit.ipynb`. Load file di `data/raw/`, rename kolom sesuai Bagian 3, cek: jumlah baris, missing value per kolom, duplikat `invoice_no`, rentang tanggal, nilai unik `city`/`leasing`/`spec_no`, outlier harga & diskon, dan verifikasi hubungan `unit_price`, `price_after_discount`, `total_discount`. Tulis temuan ke `docs/data_notes.md`.

**Fase 2 — Cleaning & Anonimisasi**
> Buat `src/clean.py` dan `src/anonymize.py`: standarisasi nama kota (buat `data/geo/city_mapping.csv`), parse tanggal, standarisasi nama leasing, buat flag dari kolom PII lalu hapus kolom PII sesuai Bagian 4, kodekan salesman/SPV/leasing. Simpan ke `data/processed/sales_clean.parquet`. Tambahkan unit test sederhana.

**Fase 3 — Feature Engineering, Metrics & Models**
> Implementasikan semua fitur di Bagian 7 pada `src/features.py`, fungsi KPI di `src/metrics.py`, serta forecast (SARIMA), clustering kabupaten (KMeans), dan anomaly detection diskon (IsolationForest) di `src/models.py`.

**Fase 4 — Analisis (Notebook)**
> Kerjakan notebook 02–06 sesuai Bagian 8. Setiap notebook diakhiri ringkasan "Key Findings" berisi angka konkret. Kumpulkan temuan ke `reports/insight_report.md`.

**Fase 5 — Export Data untuk Web**
> Buat `src/export.py` dan `build_data.py` yang menghasilkan semua file di Bagian 6.1 ke `site/public/data/`, termasuk `insights.json`. Simplify peta ke TopoJSON ≤ 150 KB. Tambahkan pengecekan otomatis: total ukuran JSON ≤ 300 KB (gzip) dan **tidak ada kolom PII** di file output (gagal jika ada).

**Fase 6 — Website Dashboard**
> Bangun website Astro sesuai Bagian 9: design tokens light/dark di `tokens.css`, layout `Base.astro`, komponen `KpiCard`, `FilterBar`, `ChartCard` (dengan tabel fallback), `Takeaways`, `ThemeToggle`. Buat semua halaman di `src/pages/`. Chart ECharts diimpor modular dan di-hydrate `client:visible`; filter disimpan di URL; cross-filter dari peta; slider stress test di halaman financing. Pastikan responsif (mobile-first) dan accessible.

**Fase 7 — Polish, Audit & Deploy**
> Jalankan Lighthouse dan perbaiki hingga target Bagian 9.4 tercapai. Tambahkan meta SEO/Open Graph dan `og-image`. Tulis `README.md` portofolio (problem, dataset, arsitektur, insight utama dengan angka, screenshot, link live demo, cara menjalankan lokal). Buat `.github/workflows/deploy.yml` untuk deploy otomatis. Cek ulang tidak ada PII di repo.

---

## 12. Checklist Kualitas Portofolio

- [ ] Ada **problem statement** bisnis yang jelas, bukan sekadar "EDA data penjualan".
- [ ] Setiap chart punya judul berupa insight (mis. *"68% penjualan bergantung pada leasing — 3 partner menguasai 80%"*).
- [ ] Minimal **3 rekomendasi bisnis** yang actionable dan berbasis angka.
- [ ] Data sudah dianonimkan + disclaimer.
- [ ] README dengan screenshot/GIF dashboard.
- [ ] Kode modular (`src/`), bukan semua di notebook.
- [ ] Live demo terbuka < 1,5 detik (Lighthouse Performance ≥ 95) dan nyaman di HP.
- [ ] Bagian "Limitations & Next Steps" (mis. tidak ada data margin/cost, tidak ada data prospek yang gagal closing).

---

## 13. Contoh Format Insight (untuk README & Key Takeaways)

> **Insight:** Diskon di minggu terakhir bulan rata-rata 2,1 poin persentase lebih tinggi, tetapi tidak diikuti kenaikan volume yang sebanding.
> **Dampak:** Potensi kebocoran margin ± Rp X juta per bulan.
> **Rekomendasi:** Terapkan batas approval diskon bertingkat di akhir bulan dan alihkan insentif ke program paket (Package Code) yang terbukti mendorong volume.

*(Angka di atas hanya ilustrasi — ganti dengan hasil analisis sebenarnya.)*
