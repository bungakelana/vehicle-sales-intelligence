# Vehicle Sales & Customer Intelligence Dashboard

**Live demo:** https://vehicle-sales-intelligence.pages.dev

Dashboard analitik penjualan kendaraan niaga (dealer di Riau, 2024–2026) yang menjawab lima pertanyaan bisnis:

1. Di kabupaten/kota mana penjualan kuat, dan di mana ada *white space*?
2. Apakah diskon benar-benar menaikkan volume, atau hanya menggerus margin?
3. Seberapa besar ketergantungan pada leasing, dan partner mana yang paling berisiko jika kredit diperketat?
4. Di tahap mana pengiriman unit & pengurusan STNK paling sering macet?
5. Salesman / SPV mana yang produktif *dan* disiplin diskon?

> Data yang dipakai adalah **data dummy/sintetis** (1.000 transaksi, 36 kolom) yang meniru struktur data dealer. Seluruh PII dihapus dan nama salesman/SPV/leasing dikodekan.

## Arsitektur

```
Python (analytics/)                  JSON teragregasi             Website statis (site/)
load → clean → anonymize →   ───►    site/public/data/*.json  ───► Astro + Tailwind + ECharts
features → models → export           (~23 KB gzip)                 → Cloudflare Pages
```

Python hanya berjalan saat build; website tidak butuh server.

- **Analisis:** pandas, statsmodels (SARIMA forecast), scikit-learn (K-Means kabupaten, IsolationForest anomali diskon), shapely (simplifikasi peta)
- **Web:** Astro, Tailwind CSS, Apache ECharts (modular), TypeScript vanilla
- **Fitur:** filter tersimpan di URL, cross-filter dari peta, slider stress test leasing, tabel fallback + download CSV di setiap chart, tema terang/gelap

## Menjalankan lokal

```bash
# 1. (opsional) buat ulang data dummy → analytics/data/raw/
python generate_dummy_data.py

# 2. raw → JSON siap web
cd analytics
pip install -r requirements.txt
python build_data.py
python -m pytest -q tests

# 3. website
cd ../site
npm install
node node_modules/astro/astro.js dev      # http://localhost:4321
```

> Catatan Windows: jika nama folder mengandung `&`, `npm run dev`/`npx` gagal — panggil `node node_modules/...` langsung seperti di atas.

## Deploy

Setiap push ke `main` otomatis di-deploy ke Cloudflare Pages lewat GitHub Actions (`.github/workflows/deploy.yml`). Deploy manual dari `site/`: `npm run deploy`.

## Limitations

- Tidak ada data margin/cost, sehingga dampak diskon diukur terhadap harga, bukan profit.
- Tidak ada data prospek yang gagal closing.
- Peta memakai batas GADM lama (Kepulauan Meranti tergabung di poligon Bengkalis); populasi kabupaten adalah perkiraan.
