# MoldGuard — UI/UX Design Specification

> **Versi:** 2.0 — approved visual references (9 halaman)  
> **Platform:** Responsive Web Application (desktop, tablet, mobile)  
> **Konsep:** *Website dengan pengalaman seperti mobile app*  
> **Bahasa antarmuka:** Indonesia  
> **Tagline:** **Rumah Sehat, Keluarga Lebih Sehat**

---

## 1. Gambaran Produk

**MoldGuard** adalah web app untuk membantu pengguna memeriksa **indikasi jamur pada permukaan bangunan melalui foto**, mengelola riwayat pemeriksaan, membaca panduan pencegahan, dan mengatur pengingat perawatan rumah.

### Tujuan desain

1. Memberikan pengalaman yang **modern, bersih, tepercaya, dan mudah dipahami**.
2. Menampilkan website desktop yang tetap terasa seperti aplikasi: kartu interaktif, navigasi konsisten, respons cepat, dan animasi halus.
3. Memprioritaskan fitur **Deteksi Jamur** tanpa membuat pengguna harus mencari-cari.
4. Menyampaikan hasil analisis AI secara jelas dan **tidak berlebihan dalam mengklaim kepastian**.
5. Menjaga pengalaman mobile tetap optimal dengan **bottom navigation**, panel full-width, dan tombol yang nyaman disentuh.

### Target pengguna

- Penghuni rumah, kos, atau apartemen.
- Pemilik bangunan dan pengelola properti.
- Pengguna yang ingin mendokumentasikan titik lembap atau dugaan pertumbuhan jamur.

### Prinsip desain

- **Simple first:** alur utama maksimal tiga tahap: unggah/ambil foto → analisis → lihat hasil.
- **Visual hierarchy:** tindakan utama selalu paling menonjol.
- **Trustworthy AI:** tampilkan indikasi, batasan, dan tingkat keyakinan model secara proporsional.
- **Mobile-app feel:** bentuk membulat, transisi lembut, navigasi persisten, dan kartu yang dapat disentuh.
- **Accessible by default:** kontras memadai, label jelas, fokus keyboard, dan tidak mengandalkan warna saja.

---

## 2. Arah Visual

### Identitas

- **Nama:** MoldGuard
- **Logo:** siluet rumah dengan daun pada bagian tengah.
- **Karakter merek:** sehat, alami, protektif, cerdas, ramah.
- **Gaya:** clean modern, *soft organic*, sedikit nuansa *glassmorphism* hanya pada elemen dekoratif (bukan teks penting).
- **Dominasi:** putih hangat, emerald green, mint lembut, abu-abu netral.
- **Fotografi:** interior rumah terang, dedaunan, ventilasi alami, dan dokumentasi permukaan bangunan yang realistis.

### Palet warna

| Token | Hex | Fungsi |
|---|---|---|
| `primary-900` | `#064E3B` | Judul besar dan area hero gelap |
| `primary-800` | `#065F46` | Heading/teks aksen hijau |
| `primary-700` | `#047857` | Hover tombol primer |
| `primary-600` | `#059669` | Warna utama, CTA, navigasi aktif |
| `primary-500` | `#10B981` | Grafik, indikator positif |
| `primary-100` | `#D1FAE5` | Ikon/kartu hijau lembut |
| `primary-50` | `#ECFDF5` | Background tint hijau |
| `canvas` | `#F6FAF8` | Latar belakang aplikasi |
| `surface` | `#FFFFFF` | Sidebar, card, modal |
| `text-primary` | `#101828` | Teks utama |
| `text-secondary` | `#667085` | Teks penjelas |
| `border` | `#E6EEEA` | Garis pemisah dan stroke |
| `danger` | `#DC2626` | Indikasi risiko tinggi |
| `danger-bg` | `#FEE2E2` | Badge/kartu tinggi |
| `warning` | `#D97706` | Indikasi risiko sedang |
| `warning-bg` | `#FEF3C7` | Badge/kartu sedang |
| `success` | `#15803D` | Status rendah/aman secara tampilan |
| `success-bg` | `#DCFCE7` | Badge/kartu rendah |
| `info` | `#2563EB` | Info netral dan bantuan |

> Warna status **bukan bukti diagnosis atau hasil uji laboratorium**. Label harus selalu disertai teks.

### Tipografi

**Rekomendasi:** `Inter` atau `Plus Jakarta Sans`, dengan fallback `system-ui, sans-serif`.

| Gaya | Desktop | Mobile | Berat |
|---|---:|---:|---:|
| Display / sapaan | 32 px | 25 px | 700 |
| Heading halaman | 26 px | 22 px | 700 |
| Heading section | 18 px | 17 px | 700 |
| Heading kartu | 16 px | 15 px | 600–700 |
| Body | 14–16 px | 14–15 px | 400–500 |
| Caption | 12–13 px | 12 px | 400–500 |
| Button | 14–15 px | 14 px | 600 |

- Line-height body: `1.5–1.6`.
- Hindari teks lebih kecil dari 12 px.
- Gunakan maksimal dua ketebalan dominan agar tampilan tidak ramai.

### Bentuk, bayangan, dan spacing

| Elemen | Nilai |
|---|---|
| Radius kartu | `20px` |
| Radius sidebar/panel utama | `24px` |
| Radius tombol | `12–14px` |
| Radius input | `12px` atau `999px` untuk pencarian |
| Radius badge | `999px` |
| Shadow kartu | `0 8px 30px rgba(16, 24, 40, 0.05)` |
| Shadow panel | `0 16px 50px rgba(6, 78, 59, 0.08)` |
| Border | `1px solid #E6EEEA` |
| Grid spacing | Kelipatan `4px` (`4, 8, 12, 16, 20, 24, 32`) |
| Tinggi tombol | `44–48px` minimum |
| Target interaktif | Minimal `44×44px` |

---

## 3. Responsive Layout — Website Berasa Mobile App

### Desktop (≥ 1280 px)

- Background halaman berupa **gradasi hijau mint yang sangat halus**; dekorasi daun blur hanya di pinggir luar layout.
- Kontainer utama maksimum `1440px`, margin horizontal `auto`, padding luar `24px`.
- Layout utama **sidebar kiri + workspace kanan**.
- Sidebar lebar `250–264px`, `position: sticky`, tinggi maksimal `calc(100dvh - 48px)`; scroll internal bila konten banyak.
- Workspace fleksibel, berbentuk panel putih membulat; konten dalamnya padding `32px`.
- Card tertata menggunakan CSS Grid, bukan lebar absolut.
- **Bottom navigation tidak tampil** pada desktop.

```text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  SIDEBAR 250px    │  WORKSPACE / KONTEN UTAMA                                      │
│                   │                                                                  │
│  Logo MoldGuard   │  Halo, Pengguna!                  Cari...      🔔      Avatar      │
│  Tagline          │                                                                  │
│                   │  ┌─────────────────────────────┐ ┌─────────────────────────┐   │
│  Beranda          │  │ HERO: Deteksi Jamur         │ │ Status Pemeriksaan /    │   │
│  Deteksi Jamur    │  │ Mulai Deteksi Sekarang      │ │ Kualitas Udara*         │   │
│  Riwayat          │  └─────────────────────────────┘ └─────────────────────────┘   │
│  Laporan          │                                                                  │
│  Tips & Edukasi   │  [Deteksi]     [Laporan]     [Tips]      [Pengingat]             │
│  Pengingat        │                                                                  │
│  Profil           │  ┌─────────────────────────────┐ ┌─────────────────────────┐   │
│                   │  │ Deteksi Terbaru             │ │ Tips Harian             │   │
│  Promo Edukasi    │  └─────────────────────────────┘ └─────────────────────────┘   │
│  Bantuan          │  ┌─────────────────────────────┐ ┌─────────────────────────┐   │
│                   │  │ Statistik                  │ │ Pengingat Selanjutnya   │   │
│                   │  └─────────────────────────────┘ └─────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

\* **Kualitas udara hanya ditampilkan bila tersedia data sensor yang benar-benar terhubung**. Jika tidak ada integrasi sensor, gantikan dengan kartu **Ringkasan Pemeriksaan** (contoh: jumlah deteksi, pemeriksaan terbaru). Jangan menghitung skor kualitas udara dari foto jamur.

### Tablet (768–1279 px)

- Sidebar berubah menjadi **rail ikon** `72–80px` atau drawer yang bisa dibuka.
- Konten utama padding `20–24px`.
- Hero dan kartu ringkasan bisa ditampilkan dua kolom ketika cukup ruang; jika sempit, ditumpuk.
- Quick action menjadi grid 2×2 jika empat kolom tidak nyaman.

### Mobile (< 768 px)

- **Satu kolom**, layar penuh seperti aplikasi mobile.
- **Tidak menggunakan sidebar permanen.**
- Header atas berisi logo mini/nama halaman, tombol notifikasi, dan avatar (sesuai konteks halaman).
- Navigasi utama berbentuk **fixed bottom navigation** dengan `safe-area-inset-bottom`.
- Padding halaman `16px`, jarak antar kartu `16px`.
- Banner hero memiliki tinggi adaptif dan tombol CTA lebar penuh atau hampir penuh.
- Kartu statistik tersusun 2 kolom hanya jika muat; daftar hasil dan tips satu kolom.
- Konten diberi padding bawah `calc(88px + env(safe-area-inset-bottom))` agar tidak tertutup navbar.
- Perhatikan pengalaman saat membuka keyboard, kamera, memilih gambar, atau modal.

### Breakpoint

```css
/* Mobile-first */
/* < 768px: smartphone */
@media (min-width: 768px)  { /* tablet */ }
@media (min-width: 1280px) { /* desktop */ }
```

---

## 4. Struktur Navigasi dan Routing

| Label | Route | Fungsi |
|---|---|---|
| Beranda | `/dashboard` | Ringkasan dan akses fitur |
| Deteksi Jamur | `/deteksi` | Kamera/unggah foto dan analisis |
| Hasil Deteksi | `/deteksi/hasil/[id]` | Detail hasil analisis |
| Riwayat | `/riwayat` | Daftar pemeriksaan terdahulu |
| Laporan | `/laporan` | Rangkuman pemeriksaan dan ekspor |
| Tips & Edukasi | `/edukasi` | Artikel dan panduan pencegahan |
| Detail Artikel | `/edukasi/[slug]` | Konten edukasi lengkap |
| Pengingat | `/pengingat` | Agenda perawatan |
| Profil | `/profil` | Informasi akun dan preferensi |
| Pengaturan | `/pengaturan` | Notifikasi, privasi, preferensi |

**Desktop sidebar:** tampilkan tujuh item utama (Beranda, Deteksi Jamur, Riwayat, Laporan, Tips & Edukasi, Pengingat, Profil).  
**Mobile bottom nav (kanonis):** lima tab persisten **Beranda, Deteksi, Laporan, Tips, Profil** sesuai mayoritas referensi. **Riwayat** diakses dari kartu Beranda, tautan pada Hasil Deteksi, atau menu Profil/More; **Pengingat** dari Beranda dan Profil/More. Jangan mengubah urutan tab secara acak saat berpindah halaman. Gunakan label aktif sesuai route; route turunan boleh menampilkan tombol kembali. Beberapa gambar konsep menampilkan tab alternatif—ikuti aturan kanonis dalam dokumen ini agar implementasi konsisten.

**Perilaku navigasi:**

- Menu aktif punya latar `primary-50`, teks dan ikon `primary-800`, serta penanda vertikal hijau di desktop.
- Navigasi halaman tidak membuat layout bergeser secara mendadak.
- Tombol kembali pada halaman turunan kembali ke konteks sebelumnya; gunakan fallback aman jika datang dari tautan langsung.
- Halaman detail hasil dapat dibuka dari URL secara langsung.

---

## 5. Spesifikasi Halaman

### 5.1 Beranda (`/dashboard`)

**Tujuan:** memberikan gambaran cepat dan pintu masuk ke deteksi.

1. **Header**: `Halo, [nama pengguna]! 👋`, deskripsi pendek, pencarian (desktop), notifikasi dan avatar.
2. **Hero banner**: foto interior bernuansa hijau, overlay gelap, judul **“Deteksi Jamur dengan Mudah dan Cepat”**, deskripsi singkat dan tombol **“Mulai Deteksi Sekarang”**.
3. **Kartu ringkasan**: jumlah total pemeriksaan, indikasi terdeteksi, atau status sensor apabila integrasi nyata tersedia.
4. **Quick actions**: Deteksi Jamur, Laporan, Tips & Edukasi, Pengingat. Setiap kartu punya ikon dalam persegi membulat, judul, satu kalimat penjelas, dan chevron.
5. **Hasil Deteksi Terbaru**: foto thumbnail, tanggal, lokasi yang diisi pengguna, label tingkat indikasi, tombol **Lihat Detail**.
6. **Tips Harian**: foto artikel, kategori, judul, ringkasan 1–2 baris, tautan untuk membaca.
7. **Statistik Deteksi**: bar chart jumlah pemeriksaan pada periode tertentu (misal 7 hari). Jangan membuat data fiktif tampak sebagai data aktual.
8. **Pengingat Selanjutnya**: maksimal dua agenda terdekat dengan status aktif.

**Empty state dashboard:** pengguna baru melihat pesan “Belum ada pemeriksaan” dengan CTA “Mulai Deteksi Pertama”.

### 5.2 Deteksi Jamur (`/deteksi`)

**Tujuan:** mengambil gambar atau mengunggah foto dengan mudah.

**Struktur layar:**

- Judul **“Deteksi Jamur”** dan petunjuk singkat.
- Segmented control: **Kamera** | **Unggah Foto**.
- Preview kamera atau dropzone gambar dengan rasio `4:3`/`3:4`, radius `20px`.
- Frame/corner guide di kamera dan tips **“Pastikan area terang dan permukaan terlihat jelas.”**
- Tombol **Ambil Foto**, **Pilih dari Galeri**, atau **Analisis Foto** sesuai state.
- Setelah foto tersedia: thumbnail, tombol Ganti Foto, pilihan lokasi pemeriksaan (opsional), tombol Analisis.
- Status proses dengan spinner/progress dan pesan **“Menganalisis gambar…”**.

**Flow:**

```text
Buka Deteksi
  → Pilih kamera atau unggah foto
  → Preview & konfirmasi gambar
  → Analisis AI
  → Hasil Deteksi
  → Simpan / ulangi / bagikan hasil
```

**Validasi dan error:**

- Tipe file: JPG, JPEG, PNG, WebP (sesuaikan dengan backend).
- Batas ukuran file harus mengikuti batas backend; tampilkan batas sebenarnya pada UI.
- Jika kamera ditolak: pesan jelas + opsi **Unggah Foto**.
- Jika analisis gagal: tombol **Coba Lagi**, foto tetap tersimpan di state sementara.
- Jangan menyimpan foto ke server sebelum pengguna menyetujui pengunggahan bila hal ini relevan dengan kebijakan produk.

### 5.3 Hasil Deteksi (`/deteksi/hasil/[id]`)

**Tujuan:** menjelaskan indikasi model dan tindakan lanjutan.

**Komponen:**

- Banner status: **“Indikasi Jamur Terdeteksi”** atau **“Tidak Ada Indikasi yang Terdeteksi”**.
- Label tingkat indikasi **Rendah / Sedang / Tinggi** *hanya jika metode penilaiannya memang tersedia dan telah didefinisikan dalam model/aturan produk*.
- Foto hasil dengan anotasi area terdeteksi **jika** backend menghasilkan bounding box/mask.
- Informasi analisis: tanggal, lokasi, model/versi (bila tersedia), dan confidence (bila memang dikembalikan API).
- Tips tindakan: perbaiki kelembapan, ventilasi, bersihkan area kecil dengan aman, dan konsultasikan dengan profesional bila area luas/berulang.
- Tombol utama **Simpan Hasil**, sekunder **Deteksi Ulang**, dan aksi **Bagikan / Unduh Laporan** jika fitur tersedia.
- Disclaimer: **“Hasil AI adalah indikasi visual, bukan identifikasi spesies jamur atau diagnosis kualitas udara. Pemeriksaan lanjutan mungkin diperlukan.”**

**Aturan confidence:** nilai confidence deteksi objek/klasifikasi **bukan** probabilitas bahaya kesehatan dan **bukan** kepastian spesies. Jangan menyajikannya sebagai “92% berbahaya”.

### 5.4 Riwayat (`/riwayat`)

- Daftar hasil berupa kartu dengan thumbnail, tanggal, lokasi, status indikasi, dan chevron.
- Filter: semua, terindikasi, tidak terindikasi; urutan terbaru/terlama.
- Pencarian lokasi/nama catatan bila data mendukung.
- Pada desktop tampilkan grid atau list yang mudah dipindai; pada mobile satu kolom.
- Konfirmasi sebelum menghapus item.
- Empty state: ilustrasi sederhana, teks **“Riwayat deteksi masih kosong”**, CTA **Mulai Deteksi**.

### 5.5 Laporan (`/laporan`)

- Ringkasan jumlah pemeriksaan dalam rentang tanggal.
- Statistik berdasarkan status hasil sesuai data nyata.
- Daftar laporan dengan tanggal, lokasi, ringkasan, dan akses detail.
- Tombol **Unduh PDF** hanya aktif bila generator PDF benar-benar tersedia; sediakan loading/error.
- Jangan membuat angka contoh dianggap sebagai aktivitas pengguna.

### 5.6 Tips & Edukasi (`/edukasi`)

- Filter kategori: **Semua, Pencegahan, Kebersihan, Ventilasi, Kelembapan**.
- Kartu artikel berisi foto, label kategori, judul, deskripsi 2 baris, dan aksi **Baca Artikel**.
- Pencarian artikel dan tampilan kosong bila tidak ada hasil.
- Detail artikel memuat sumber/referensi untuk klaim teknis atau kesehatan.

### 5.7 Pengingat (`/pengingat`)

- Daftar agenda perawatan: pembersihan rutin, pengecekan area lembap, ventilasi, filter AC.
- Setiap agenda berisi nama, frekuensi, tanggal berikutnya, dan switch aktif/nonaktif.
- Aksi tambah, edit, hapus, tandai selesai.
- Jika memakai notifikasi browser: mintakan izin secara kontekstual dan sediakan fallback apabila tidak diizinkan.
- Jangan menjanjikan notifikasi berjalan saat situs tertutup jika belum ada mekanisme push/background yang terimplementasi.

### 5.8 Profil & Pengaturan (`/profil`, `/pengaturan`)

- Avatar/inisial, nama dan email **jika autentikasi sudah tersedia**.
- Menu: Akun, Pengaturan, Tentang Aplikasi, Kebijakan Privasi, Bantuan, Keluar.
- Preferensi notifikasi dan pengelolaan data pengguna.
- Jika aplikasi belum memakai autentikasi, gunakan profil lokal/settings dan sembunyikan tindakan login/logout yang belum berfungsi.


### 5.9 Panduan visual terperinci berdasarkan 9 mockup yang telah disetujui

> **Sumber visual:** sembilan berkas di `design-references/`. **Gambar adalah target komposisi, estetika, hierarki, dan proporsi UI**, bukan bukti ketersediaan fitur atau data produk. Jika teks/angka pada gambar berbenturan dengan aturan kebenaran data, keamanan, aksesibilitas, atau kemampuan backend, aturan dalam `DESIGN.md` ini yang harus didahulukan.

#### A. Dashboard / Beranda — `01-dashboard.png`

**Desktop**
- Shell dua kolom: sidebar putih vertikal di kiri, workspace putih besar di kanan dengan sudut membulat.
- Baris atas workspace: sapaan pengguna dan deskripsi pendek di kiri; pencarian berbentuk pill, notifikasi, avatar di kanan.
- Baris berikut: hero hijau bergambar interior/tanaman (sekitar 60% lebar) dengan headline putih dan CTA pill; di kanan ringkasan pemeriksaan berbentuk kartu mint (sekitar 40%).
- Di bawah hero: empat atau lima action-card putih sejajar (Deteksi, Riwayat, Laporan, Tips & Edukasi, Pengingat); ikon di tile berwarna pastel, judul tebal, deskripsi ringkas.
- Bagian bawah dua kolom: kiri Riwayat/Hasil Deteksi Terbaru + Statistik; kanan Tips Harian + Pengingat Selanjutnya.
- Gunakan konten hingga fold pertama secara proporsional; jangan memaksa semua elemen muat dalam 100vh dan mengecilkan teks.

**Mobile**
- Header nama produk, notifikasi; sapaan besar dan ringkasan setelahnya.
- Ringkasan menjadi kartu mendatar penuh, action-card menjadi shortcut ikon horizontal yang dapat di-scroll jika tidak muat.
- Hero lebih rendah dan full-width; daftar hasil terbaru serta statistik menumpuk vertikal.
- Bottom navigation tetap terlihat dan konten terscroll di atasnya; slot tab mengikuti aturan kanonis di bagian navigasi.

**Interaksi**: CTA hero → halaman Deteksi; kartu hasil → detail; grafik berubah sesuai rentang tanggal; tips → artikel; jika tidak ada data tampilkan empty state. Kartu “kualitas udara” dari gambar hanya boleh muncul dengan sensor aktif; jika belum ada sensor gunakan **Ringkasan Pemeriksaan**.

#### B. Deteksi Jamur — `02-deteksi-jamur.png`

**Desktop**
- Judul + subjudul dan breadcrumb di atas.
- Panel kiri lebih besar (kurang lebih 65%) berisi tab Kamera/Galeri, frame kamera/foto dengan empat sudut crop guide putih, pesan overlay kontras di bagian bawah foto, tombol hijau besar Mulai Analisis.
- Panel kanan (35%) memuat langkah penggunaan bernomor 1–4 dan kartu format unggahan / batas ukuran berkas.
- Bagian bawah kiri berisi empat tips ringkas dalam kartu mint: pencahayaan, fokus, jarak, area dalam frame.

**Mobile**
- Header back + judul + bantuan, foto/preview portrait tinggi, frame guide, tombol shutter bundar hijau.
- Tombol Galeri sebagai aksi sekunder di samping shutter; segmented Kamera/Galeri di bawah atau atas preview (pilih satu konsisten dengan mockup dan ergonomi layar).
- Setelah mengambil gambar, ganti shutter dengan preview + tombol **Ganti Foto** dan **Mulai Analisis** yang jelas; tidak boleh menganalisis secara otomatis tanpa konfirmasi.

**Interaksi**: permission kamera (granted/denied/unavailable), unggah, validasi berkas, capture, konfirmasi, analisis/loading, retry/error, halaman hasil. Gunakan kamera dari browser hanya jika HTTPS/localhost dan izin tersedia.

#### C. Hasil Deteksi — `03-hasil-deteksi.png`

**Desktop**
- Tombol kembali dan judul di bagian atas.
- Kolom kiri memuat foto inspeksi besar serta kartu Informasi Gambar (tanggal, lokasi dari pengguna, metode jika tersedia).
- Kolom kanan memuat alert status warna merah/mint, confidence bar (jika backend menyediakan), kemungkinan kelas yang benar-benar didukung model, serta checklist rekomendasi berbentuk kartu hijau lembut.
- Sticky bottom action **hanya jika diperlukan**, atau baris akhir tiga tombol: Scan Ulang, Unduh Laporan, Simpan Hasil. Tombol utama hijau.

**Mobile**
- Foto di atas, status di bawah foto, lalu confidence (jika ada), label temuan, rekomendasi yang dapat dibaca, tombol Simpan Hasil full width, dua aksi sekunder di bawahnya.
- Jika hasil negatif, gunakan status hijau netral dan pesan “Tidak ditemukan indikasi pada foto ini”; hindari klaim “bebas jamur 100%”.

**Interaksi**: simpan menggunakan penyimpanan riil yang tersedia, scan ulang kembali ke Deteksi, unduh laporan saat generator tersedia. **DILARANG** menyimpulkan spesies jamur atau tingkat bahaya kesehatan dari confidence model umum.

#### D. Riwayat Deteksi — `04-riwayat.png`

**Desktop**
- Header judul dan field pencarian besar; deret filter berbentuk pill: Semua, Tinggi, Sedang, Rendah, Tidak Terdeteksi **hanya untuk kategori yang memang tersedia**.
- Kolom utama tabel/list ringkas berisi thumbnail, waktu, lokasi, status, chevron; panel detail/preview di kanan.
- Urutan terbaru dan pagination/load-more bila jumlah data banyak.

**Mobile**
- Header + pencarian/filter horizontal scroll; item riwayat satu kolom berbentuk card dengan thumbnail kiri, tanggal dan status kanan, chevron paling kanan.
- Navigasi tidak menghilangkan akses kembali ke dashboard; detail riwayat membuka hasil yang sesuai.

**Interaksi**: filter, search, sort, detail, delete dengan konfirmasi jika didukung API; empty state dengan CTA Deteksi.

#### E. Laporan — `05-laporan.png`

**Desktop**
- Judul, subjudul, date range picker dan shortcut 7 Hari / 30 Hari / 3 Bulan / 1 Tahun, aksi Unduh PDF/Bagikan jika implementasinya tersedia.
- Empat metric-card di baris pertama: Total Deteksi, Indikasi Jamur, Area Aman (jika definisi data ada), Laporan Dibuat.
- Grafik batang tren pemeriksaan dan donut distribusi pemeriksaan dalam dua kolom, lalu Analisis per Ruangan dan Laporan Terbaru di bawah.

**Mobile**
- Date range dan segmented filter di atas; empat metric-card menjadi 2×2, grafik full width, laporan terbaru dalam kartu vertikal.
- Jangan memotong label grafik; gunakan scroll/penyederhanaan axis yang terukur.

**Interaksi**: perubahan periode mengubah query dan semua visualisasi dengan konsisten. PDF hanya berdasarkan data yang ada; tanpa data tampilkan informasi “Belum ada laporan”.

#### F. Tips & Edukasi — `06-tips-edukasi.png`

**Desktop**
- Judul/subjudul, pencarian, pill filter kategori (Semua, Pencegahan, Kebersihan, Kesehatan, Ventilasi) bila konten sesuai.
- Featured article berupa banner lebar bergambar ruang keluarga/plant styling, judul overlay besar, deskripsi, CTA “Baca Selengkapnya”.
- Grid artikel 3 kolom: foto rasio 16:9, badge kategori, judul pendek 2 baris, excerpt ringkas, link hijau.

**Mobile**
- Tab kategori horizontal scroll, featured article menjadi kartu gambar di atas dan isi di bawah agar teks tetap terbaca; list artikel satu kolom dengan thumbnail samping.

**Interaksi**: filter, pencarian, buka artikel, related articles; konten pengetahuan disertai sumber yang relevan, hindari nasihat medis tanpa dasar.

#### G. Pengingat — `07-pengingat.png`

**Desktop**
- Judul dan tombol “+ Tambah Pengingat”; kolom utama daftar 4 reminder card dengan ikon berwarna, nama, penjelasan, frekuensi, tanggal berikutnya, toggle, chevron; kolom kanan kalender bulanan dan upcoming timeline.

**Mobile**
- Header back, ilustrasi lonceng hijau di bagian atas, headline dan subjudul; daftar kartu reminder dengan ikon, frekuensi dan toggle; kartu Tambah Pengingat serta tombol Simpan Pengaturan di bawah.

**Interaksi**: tambah/edit/hapus, set jadwal berulang dan zona waktu lokal, toggle, permission notification ketika benar-benar dibutuhkan. Bila belum punya infrastruktur push, gunakan reminder in-app; jangan menjanjikan notifikasi background.

#### H. Profil — `08-profil.png`

**Desktop**
- Kolom kiri profile card dengan cover hijau/tanaman, avatar bulat menumpang cover, nama/email bila autentikasi tersedia, metadata, kartu jenis akun/versi aplikasi di bawah.
- Kolom kanan menu white card terpisah untuk Akun, Pengaturan, Privasi, Bantuan, Tentang Aplikasi, dan Keluar berwarna merah hanya saat pengguna login.

**Mobile**
- Header Profil, logo MoldGuard terpusat dan tagline, profile summary kecil, menu list tinggi sentuh >=44px dan bottom nav.

**Interaksi**: edit akun hanya jika auth tersedia; tanpa auth tampilkan profil perangkat/lokal secara jujur, jangan membuat identitas atau email fiktif.

#### I. Pengaturan — `09-pengaturan.png`

**Desktop**
- Grid 2 kolom kartu pengaturan: Notifikasi, Privasi, Bahasa, Tema, Sinkronisasi Data, Izin Kamera, Tentang Aplikasi.
- Setiap baris berisi ikon, judul, helper text dan switch/chevron; tema segmented Terang/Gelap/Sistem, bahasa dropdown.
- Aksi berbahaya “Hapus Data Saya” dengan warna merah, modal konfirmasi, dan penjelasan dampak.

**Mobile**
- Single column dengan section cards Notifikasi dan Privasi, lalu Bahasa, Tema, Sinkronisasi, Kamera, Tentang Aplikasi. Back header dan bottom navigation yang tidak menutup setting terakhir.

**Interaksi**: simpan preferensi secara persisten (lokal atau akun sesuai arsitektur), perubahan tema terlihat langsung, perubahan izin kamera memicu instruksi browser yang benar. Jangan membuat switch terlihat aktif jika perubahan tidak dapat disimpan.

#### Aturan konsistensi lintas layar

- **Background desktop:** mint pucat dengan dekorasi daun blur ringan di sisi luar saja; konten utama menggunakan putih agar kontras tinggi.
- **Pemisah utama:** gap 16–24 px, panel putih melengkung, ikon minimalis (Lucide atau yang sudah ada di repo), tidak menggunakan ikon campur aduk.
- **Jangan copy contoh data** dari gambar ke produksi (nama “Besttan”, angka 85, 92%, 12 deteksi, tanggal Oktober 2026, gambar noda jamur) kecuali memang data yang sudah dihasilkan pengguna. Untuk development UI diperbolehkan *preview/storybook* berlabel **DEMO**, bukan aplikasi produksi.
- **Foto mockup** adalah referensi visual, bukan pengganti media dari repository atau data inspeksi aktual. Jangan hotlink file image-generation sementara ke UI produksi.
- **Kontrol akses**: tampilan yang memerlukan auth hanya muncul saat kemampuan auth tersedia; gunakan pola empty/guest yang konsisten.
- **Jangan melakukan refactor backend/AI** hanya untuk meniru angka/label di mockup; yang berubah adalah presentasi UI dan adaptasi antarmuka data secara aman.


---

## 6. Komponen UI Reusable

| Komponen | Deskripsi |
|---|---|
| `AppShell` | Wrapper sidebar/header/main/bottom nav responsif |
| `SidebarNav` | Navigasi vertikal desktop, active state |
| `MobileBottomNav` | Navigasi bawah dengan lima item |
| `TopBar` | Sapaan/judul, pencarian, notifikasi, avatar |
| `HeroBanner` | Image + overlay + CTA utama |
| `ActionCard` | Ikon, judul, subtitle, chevron |
| `MetricCard` | Statistik numerik atau status perangkat |
| `RiskBadge` | Status dengan teks, ikon, dan warna |
| `DetectionCard` | Thumbnail, metadata, hasil, aksi |
| `ImageUploader` | Dropzone/picker dengan preview dan validasi |
| `CameraCapture` | Preview kamera, capture, error permission |
| `DetectionOverlay` | Bounding box/mask hanya dari hasil API |
| `AnalysisProgress` | Indikator proses analisis |
| `ReminderItem` | Jadwal dan toggle |
| `EducationCard` | Thumbnail, kategori, judul, ringkasan |
| `StatsChart` | Visualisasi data aktual dengan state kosong |
| `EmptyState` | Ikon/ilustrasi, pesan, CTA |
| `ConfirmDialog` | Konfirmasi aksi destruktif |
| `Toast` | Umpan balik sukses/gagal yang dapat dibaca |
| `Skeleton` | Placeholder ketika data dimuat |

### Variasi tombol

- **Primary:** background `primary-600`, teks putih; hover `primary-700`.
- **Secondary:** background putih, border `border`, teks `text-primary`.
- **Ghost:** tanpa latar, hover `primary-50`.
- **Danger:** untuk penghapusan, butuh konfirmasi.
- **Disabled:** jelas secara visual dan semantik; bukan sekadar opacity tanpa penjelasan.

### Interaksi utama

- Hover kartu: `translateY(-2px)`, shadow sedikit meningkat, durasi 180–220 ms.
- Fokus: ring yang jelas (`outline`/`box-shadow`), tidak dihilangkan.
- Loading tombol: spinner + label seperti **“Memproses…”** dan cegah submit ganda.
- Toast: ringkas, tampilkan kesalahan yang relevan dan cara memperbaikinya.
- Modal: fokus terperangkap dan dapat ditutup dengan Escape jika aman.

---

## 7. Motion dan Microinteractions

| Peristiwa | Motion | Durasi |
|---|---|---:|
| Hover card | Geser naik 2px + shadow | 180 ms |
| Hover tombol | Ubah background | 150 ms |
| Buka drawer | Slide lembut | 220 ms |
| Pergantian halaman | Fade kecil, tanpa efek berlebihan | 180–220 ms |
| Progress analisis | Spinner atau determinate progress jika tersedia | Sesuai proses |
| Muncul toast | Fade + translate 6px | 200 ms |

Gunakan easing `cubic-bezier(0.2, 0.8, 0.2, 1)`. Hormati `prefers-reduced-motion: reduce` dengan menonaktifkan animasi non-esensial.

---

## 8. Data & Status yang Harus Jujur

Khusus aplikasi pendeteksi jamur berbasis AI, UI harus memisahkan:

1. **Prediksi visual model** — indikasi pada foto dan lokasi area yang ditandai.
2. **Tingkat keyakinan model** — angka dari API, jika tersedia; bukan bukti risiko klinis.
3. **Kategori tindakan** — rekomendasi yang ditentukan secara eksplisit oleh aturan produk, bukan asumsi UI.
4. **Kualitas udara/kelembapan** — hanya tampil jika ada **sensor atau sumber pengukuran valid**.

**Data demo:** untuk presentasi UI boleh memakai seed data, tetapi tampilkan label **“Contoh data”**. Di versi produksi, default adalah empty state hingga tersedia data asli.

Contoh skema UI (konseptual, sesuaikan dengan API nyata):

```ts
type DetectionResult = {
  id: string;
  createdAt: string;
  imageUrl: string;
  locationLabel?: string;
  hasMoldIndication: boolean;
  confidence?: number; // 0..1; jika disediakan backend
  annotations?: Array<{
    label: string;
    confidence?: number;
    box?: [number, number, number, number]; // format koordinat disepakati API
  }>;
  riskLevel?: 'low' | 'medium' | 'high'; // hanya jika didukung aturan valid
  modelVersion?: string;
};
```

Jangan mengarang jenis jamur (`Aspergillus`, `Penicillium`, dll.) jika model tidak dilatih/divalidasi untuk itu.

---

## 9. Accessibility & Usability

- Kontras teks normal minimal **4.5:1**; elemen UI/nonteks minimal **3:1** jika berlaku.
- Navigasi bisa digunakan dengan keyboard.
- Semua input punya label; ikon-only button punya `aria-label`.
- Status risiko menyertakan **teks dan ikon**, bukan warna saja.
- Gambar informatif diberi `alt`; gambar dekoratif diberi `alt=""`.
- Error ditampilkan dekat input dan tidak hilang sebelum pengguna sempat membacanya.
- Hindari layout shift dan potongan konten saat zoom 200%.
- Pastikan navbar bawah tidak menutupi tombol aksi utama.
- Uji perangkat lebar kecil (mulai sekitar 320px), ponsel besar, tablet, laptop, dan desktop.

---

## 10. Saran Implementasi Frontend

> Stack berikut bersifat **rekomendasi**, bukan syarat desain.

- **Framework:** Next.js (App Router) + TypeScript.
- **Styling:** Tailwind CSS dengan CSS custom properties untuk design token.
- **UI components:** shadcn/ui atau komponen buatan sendiri yang konsisten.
- **Icons:** Lucide React.
- **Chart:** Recharts (untuk data nyata).
- **Animation:** CSS transitions; Framer Motion hanya jika memang diperlukan.
- **Images:** `next/image` untuk foto statis/thumbnail jika sesuai sumber gambar.
- **Detection API:** integrasikan dengan backend yang sudah dimiliki proyek; jangan memaksakan arsitektur AI baru dari spesifikasi desain ini.

### Struktur frontend yang direkomendasikan

```text
src/
├── app/
│   ├── (app)/
│   │   ├── dashboard/page.tsx
│   │   ├── deteksi/page.tsx
│   │   ├── deteksi/hasil/[id]/page.tsx
│   │   ├── riwayat/page.tsx
│   │   ├── laporan/page.tsx
│   │   ├── edukasi/page.tsx
│   │   ├── edukasi/[slug]/page.tsx
│   │   ├── pengingat/page.tsx
│   │   ├── profil/page.tsx
│   │   ├── pengaturan/page.tsx
│   │   └── layout.tsx
│   ├── globals.css
│   └── layout.tsx
├── components/
│   ├── layout/
│   ├── dashboard/
│   ├── detection/
│   ├── education/
│   ├── reminders/
│   └── ui/
├── hooks/
├── lib/
│   ├── api/
│   ├── utils/
│   └── constants/
├── types/
└── public/ (atau gunakan folder public di root Next.js)
```

> Catatan: pada Next.js, folder **`public/` sebenarnya berada di root proyek**, bukan di dalam `src/`. Gunakan `public/` di root saat implementasi.

### Contoh design tokens CSS

```css
:root {
  --mg-primary: #059669;
  --mg-primary-hover: #047857;
  --mg-primary-dark: #064e3b;
  --mg-primary-soft: #ecfdf5;
  --mg-background: #f6faf8;
  --mg-surface: #ffffff;
  --mg-text: #101828;
  --mg-muted: #667085;
  --mg-border: #e6eeea;
  --mg-danger: #dc2626;
  --mg-warning: #d97706;
  --mg-success: #15803d;
  --mg-radius-card: 20px;
  --mg-radius-panel: 24px;
  --mg-radius-button: 12px;
  --mg-shadow-card: 0 8px 30px rgba(16, 24, 40, 0.05);
  --mg-shadow-panel: 0 16px 50px rgba(6, 78, 59, 0.08);
}
```

### Performa

- Lazy-load chart dan elemen berat yang tidak berada di viewport pertama.
- Kompres gambar hero dan thumbnail; tetapkan ukuran untuk mengurangi CLS.
- Kamera hanya diaktifkan setelah tindakan pengguna dan berhenti saat komponen tidak aktif.
- Usahakan UI tetap responsif saat proses analisis berjalan; sediakan status dan timeout yang ditangani.

---

## 11. Acceptance Criteria (Checklist)

### Visual

- [ ] Palet, tipografi, ikon, radius, shadow konsisten.
- [ ] Desktop mirip aplikasi dalam jendela website: sidebar permanen + panel konten.
- [ ] Mobile terasa seperti aplikasi native: header ringkas + bottom nav tetap.
- [ ] Semua kartu dan tombol memiliki state hover, fokus, aktif, loading, dan disabled sesuai kebutuhan.
- [ ] Tidak ada overflow horizontal atau konten tertutup navbar.

### Fungsional

- [ ] Semua navigasi menuju route yang benar.
- [ ] CTA **Mulai Deteksi Sekarang** membuka `/deteksi`.
- [ ] Alur kamera/unggah → preview → analisis → hasil dapat digunakan.
- [ ] Error izin kamera dan kegagalan API ditangani.
- [ ] Riwayat menampilkan data aktual atau empty state yang jujur.
- [ ] Laporan dan pengingat tidak memakai tombol palsu tanpa fungsi.

### Kepercayaan dan aksesibilitas

- [ ] Nilai confidence tidak dijelaskan sebagai tingkat bahaya kesehatan.
- [ ] Skor kualitas udara tidak direkayasa dari foto.
- [ ] Tidak ada klasifikasi spesies yang tidak didukung model.
- [ ] Warna risiko selalu punya label teks.
- [ ] Tampilan dapat digunakan lewat keyboard dan screen reader dasar.
- [ ] Animasi mematuhi pengaturan reduced motion.

---

## 12. Ringkasan prompt implementasi untuk AI Coding Agent

> Buat ulang frontend MoldGuard berdasarkan `DESIGN.md` ini. Implementasikan **responsive web app yang terasa seperti mobile application**, mengikuti tampilan referensi: background mint lembut, sidebar putih membulat di desktop, workspace white rounded, hero hijau dengan foto interior, quick action cards, ringkasan pemeriksaan, riwayat terbaru, tips harian, statistik, dan pengingat. Pada mobile hilangkan sidebar, gunakan fixed bottom navigation dan layout satu kolom. Buat halaman Dashboard, Deteksi, Hasil Deteksi, Riwayat, Laporan, Edukasi, Pengingat, Profil, dan Pengaturan. Gunakan komponen reusable, TypeScript, loading/empty/error states, aksesibilitas, dan seluruh token visual pada dokumen. **Pertahankan integrasi backend/model AI proyek yang sudah ada; jangan mengarang hasil analisis, sensor kualitas udara, klasifikasi spesies, atau endpoint baru.** Jangan memasang konten dummy sebagai data produksi. Pastikan seluruh tombol dan navigasi berfungsi sesuai kapabilitas yang tersedia.

---

**Status dokumen:** Disetujui sebagai acuan implementasi visual MoldGuard — desktop & mobile, 9 layar.

---

## 13. Peta aset referensi dan instruksi handoff

Semua gambar berikut adalah mockup **desktop + mobile dalam satu gambar**. Di paket ZIP, simpan pada lokasi `design-references/` dengan penamaan yang persis sama.

| Halaman | Rute | Referensi gambar |
|---|---|---|
| Dashboard | `/dashboard` | `design-references/01-dashboard.png` |
| Deteksi Jamur | `/deteksi` | `design-references/02-deteksi-jamur.png` |
| Hasil Deteksi | `/deteksi/hasil/[id]` (atau route yang sudah ada) | `design-references/03-hasil-deteksi.png` |
| Riwayat | `/riwayat` | `design-references/04-riwayat.png` |
| Laporan | `/laporan` | `design-references/05-laporan.png` |
| Tips & Edukasi | `/edukasi` | `design-references/06-tips-edukasi.png` |
| Pengingat | `/pengingat` | `design-references/07-pengingat.png` |
| Profil | `/profil` | `design-references/08-profil.png` |
| Pengaturan | `/pengaturan` | `design-references/09-pengaturan.png` |

**Prioritas jika terjadi perbedaan:** (1) keamanan data dan kemampuan proyek, (2) spesifikasi UX/fitur dan aksesibilitas di dokumen ini, (3) komposisi dan identitas visual gambar, (4) contoh angka/teks pada gambar (demo saja).

**Viewport wajib dicek:** 360×800, 390×844, 768×1024, 1024×768, 1366×768, 1440×900, dan 1920×1080. Jangan ada scroll horizontal halaman, header/tab terpotong, atau tombol tak terjangkau.

**Output developer yang diharapkan:** ringkasan audit repository sebelum perubahan, daftar file UI yang diubah, cara menjalankan proyek sesuai stack aktual, bukti lint/build/test jika tersedia, catatan fitur yang tidak dapat diimplementasikan karena backend belum mendukung, serta daftar pencocokan 9 halaman terhadap referensi.

**Final quality gate**

- [ ] 9 halaman berfungsi dan tampil konsisten pada desktop & mobile.
- [ ] Identitas MoldGuard, sidebar, header, CTA, warna, spacing, radius, iconography mirip referensi.
- [ ] Pindah route memberi active state yang benar pada sidebar/bottom nav.
- [ ] Kamera + upload + analisis menghormati API aktual dan izin browser.
- [ ] Data kosong, error, loading, sukses, dan akses tanpa izin ditangani dengan benar.
- [ ] Tidak ada fabricated AI output/sensor score/user stats.
- [ ] Tidak ada `href="#"` atau tombol visual tanpa aksi: fungsi diimplementasikan atau dinonaktifkan secara jujur.
- [ ] Lint/build dan uji manual mobile/desktop berjalan sejauh tooling repo memungkinkan.

