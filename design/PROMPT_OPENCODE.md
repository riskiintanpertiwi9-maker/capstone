# PROMPT OPENCODE — IMPLEMENTASI UI/UX MOLDGUARD (APPROVED DESIGN)

> **Cara pakai:** Letakkan `DESIGN.md` dan folder `design-references/` pada root repository MoldGuard. Salin semua isi blok **PROMPT UTAMA** di bawah ke OpenCode. Proyek existing adalah source of truth untuk stack, API, auth, model ML, dan penyimpanan.

## PROMPT UTAMA — Copy / Paste ke OpenCode

```text
Anda adalah senior frontend engineer, UI/UX engineer, dan codebase integration specialist.

TUGAS UTAMA
Implementasikan redesign penuh frontend MoldGuard menjadi RESPONSIVE WEBSITE dengan pengalaman visual seperti MOBILE APPLICATION, mengikuti 9 mockup desktop dan mobile yang SUDAH DISETUJUI. Kerjakan langsung di repository yang sedang terbuka, BUKAN membuat project baru. Pertahankan backend, alur AI/ML, fungsi API, penyimpanan, dan autentikasi existing.

SUMBER ACUAN WAJIB
- Baca file ./DESIGN.md sampai selesai; implementasikan design system, struktur layout, spesifikasi tiap halaman, behavior, accessibility, dan acceptance criteria.
- Baca SEMBILAN gambar berikut. Jadikan visual target utama untuk layout, hierarchy, card, warna, spacing, ikon, dan responsive composition:
  1) ./design-references/01-dashboard.png
  2) ./design-references/02-deteksi-jamur.png
  3) ./design-references/03-hasil-deteksi.png
  4) ./design-references/04-riwayat.png
  5) ./design-references/05-laporan.png
  6) ./design-references/06-tips-edukasi.png
  7) ./design-references/07-pengingat.png
  8) ./design-references/08-profil.png
  9) ./design-references/09-pengaturan.png
- Bila kemampuan proyek bertentangan dengan data dummy di gambar, dahulukan fakta backend dan DESIGN.md. Mockup adalah REFERENSI VISUAL, bukan spesifikasi output AI.

LANGKAH WAJIB — LAKUKAN, JANGAN HANYA MENULIS RENCANA
FASE 1 — AUDIT REPOSITORY
1. Periksa struktur folder, package manager, framework, styling, route, state management, backend/API, integrasi model AI/ML (termasuk YOLO/MobileNet JIKA memang ada), serta fitur yang sudah bekerja.
2. Baca package manifest, route/page, komponen, styles, API client, env example, dan dokumentasi. Jangan menebak nama endpoint/model.
3. Identifikasi area aman untuk refactor UI. Pertahankan nama env, kontrak API, integrasi backend, dan database. Jangan mengekspos credential.
4. Gunakan stack proyek existing. Jangan migrasi framework atau menambahkan dependency besar tanpa kebutuhan nyata.

FASE 2 — DESIGN SYSTEM + APP SHELL
5. Buat/reuse token tema emerald green, mint, putih, neutral, semantic states, typography, grid, shadow, radius, motion sesuai DESIGN.md.
6. Implementasikan global responsive AppShell:
   Desktop >=1280px: halaman mint soft leaf accents, sidebar kiri putih rounded ~250px, workspace kanan putih rounded, header search/notification/avatar, grid konten.
   Tablet 768–1279px: compact sidebar/rail atau drawer, layout adaptif.
   Mobile <768px: single column, top app bar, fixed bottom navigation 5 tab [Beranda, Deteksi, Laporan, Tips, Profil], safe-area support, scroll content.
7. Bangun komponen reusable: Sidebar, MobileBottomNav, Topbar, HeroBanner, ActionCard, MetricCard, DetectionCard, StatusBadge, ImageUploader, CameraCapture, DetectionOverlay, StatsChart, EducationCard, ReminderCard, PageHeader, EmptyState, Skeleton, Toast, ConfirmDialog.
8. Gunakan desain profesional: Inter/Plus Jakarta Sans jika tersedia, Lucide icons atau icon set existing, radius card 20px, panel 24px, tombol >=44px, spacing sistem 4/8/12/16/24/32, subtle hover, focus ring, tanpa emoji sebagai pengganti ikon navigasi.

FASE 3 — SEMBILAN HALAMAN
9. Dashboard: sapaan, hero deteksi, ringkasan real, shortcut fitur, riwayat terbaru, tips, statistik, upcoming reminders. Adaptasi desktop & mobile sama seperti 01-dashboard.png.
10. Deteksi Jamur: tab Kamera/Galeri, preview frame, capture/upload, tips pengambilan foto, validasi file, konfirmasi, tombol Mulai Analisis, loading/error/retry. Adaptasi 02-deteksi-jamur.png.
11. Hasil Deteksi: image preview dan anotasi aktual jika API menyediakan, banner hasil, confidence jika ada, rekomendasi yang valid, Simpan, Scan Ulang, Unduh (jika tersedia). Adaptasi 03-hasil-deteksi.png.
12. Riwayat: pencarian, filter status jika didukung, list/tabel desktop dengan preview, stacked cards mobile, detail, empty state. Adaptasi 04-riwayat.png.
13. Laporan: filter rentang tanggal, metric cards, chart tren, distribusi kategori, ringkasan ruangan, recent reports, PDF jika fitur real tersedia. Adaptasi 05-laporan.png.
14. Tips & Edukasi: featured hero artikel, kategori, article cards/grid desktop dan list mobile, search, halaman detail. Adaptasi 06-tips-edukasi.png.
15. Pengingat: list reminder, toggle, tambah/edit/hapus, tanggal berikutnya; calendar panel desktop bila data tersedia, tampilan sederhana mobile. Adaptasi 07-pengingat.png.
16. Profil: cover green, avatar, info user dari auth/penyimpanan bila tersedia, menu akun, privacy, bantuan, about, logout hanya bila auth. Adaptasi 08-profil.png.
17. Pengaturan: groups notifikasi, privasi, bahasa, tema, sinkronisasi jika ada, izin kamera, about, delete data dengan konfirmasi. Adaptasi 09-pengaturan.png.
18. Hubungkan seluruh route dan action. Pertahankan existing path apabila migrasi berisiko; lakukan mapping internal yang konsisten. Jangan membuat halaman yang terputus dari navigasi.

FASE 4 — INTEGRASI, VALIDASI, PERILAKU JUJUR
19. Semua data nyata harus berasal dari state/API/storage yang ada. Jangan hardcode nama Besttan, 85/100 kualitas udara, 92% confidence, tanggal, daftar riwayat, atau angka laporan dari gambar sebagai data pengguna produksi.
20. Foto JAMUR bukan sensor kualitas udara. Jika tidak ada sumber sensor, ganti indikator 85/100 menjadi kartu Ringkasan Pemeriksaan.
21. Jangan tampilkan identitas spesies jamur jika model tidak benar-benar memprediksi kelas tersebut. Confidence prediksi bukan risiko medis. Tampilkan disclaimer hasil deteksi visual dengan bahasa jelas.
22. Jika backend belum mendukung suatu fitur (PDF, notification push, CRUD reminder, auth, chart statistik), jangan membuat UI pura-pura berfungsi: implementasikan kemampuan frontend lokal yang aman jika relevan, atau disabled/empty state dengan pesan yang jelas. Catat keterbatasannya.
23. Kamera: tangani izin, HTTPS/localhost, stream cleanup, switch ke gallery, error browser. Jangan pernah meninggalkan stream aktif setelah keluar halaman.
24. Implementasikan responsive, alt text, keyboard focus, contrast WCAG AA, proper form label, tap target minimum 44x44, prefers-reduced-motion, dan semua empty/loading/error states.
25. Optimalkan image dimensions/lazy load, hindari overflow horizontal, duplikasi komponen, layout shift, memory leak, dan request ganda.

FASE 5 — QA & OUTPUT
26. Jalankan lint, typecheck, unit tests jika ada, dan build sesuai package scripts; perbaiki semua error yang disebabkan perubahan.
27. Review semua 9 halaman pada 360px, 390px, 768px, 1024px, 1366px, 1440px; pastikan kesamaan visual terhadap gambar desktop & mobile.
28. Pastikan semua navigation, CTA, button, dropdown, toggle, form, filter, back action, dan modal relevan bekerja. Jangan meninggalkan dead link atau placeholder UI yang menipu.
29. Rapikan struktur file SECARA MINIMAL dan konsisten dengan repo; hapus hanya file yang benar-benar tidak terpakai setelah diverifikasi. Jangan menghapus fitur existing.
30. Berikan laporan akhir singkat: file dibuat/diubah, 9 halaman selesai/belum, hasil test/build, integrasi existing yang dipertahankan, keterbatasan backend (jika ada), cara menjalankan.

KUALITAS AKHIR
Saya ingin visual yang benar-benar mendekati sembilan referensi (bukan dashboard generik): warna emerald, surface putih lembut, background organic mint, sidebar putih dengan promo green panel, card rounded clean, layout hierarchy rapi, grafik, green CTA, ikon konsisten, dan mobile seperti aplikasi native. Fokus pada kualitas UI, UX, responsive behavior, accessibility dan keutuhan integrasi dengan project MoldGuard sekarang. Jangan berhenti pada desain statis—implementasikan kode yang benar-benar berjalan.

Mulai dengan audit singkat lalu langsung lakukan implementasi berurutan sampai selesai. Jika ada fitur tanpa dukungan backend, lakukan fallback yang jujur dan lanjutkan semua bagian yang bisa dikerjakan. Jangan meminta konfirmasi untuk keputusan visual kecil yang sudah dijelaskan dalam DESIGN.md.
```

## Catatan pemakaian

- Folder gambar mockup sudah disertakan jika menggunakan paket ZIP.
- Jalankan OpenCode dari root repository MoldGuard, bukan dari folder lain.
- Jika codebase ternyata bukan Next.js atau bukan React, ikuti stack existing. Rekomendasi teknologi dalam `DESIGN.md` bukan perintah migrasi.
- Jika OpenCode tidak dapat melihat gambar, jelaskan bahwa referensi ada di `design-references/`, lalu lampirkan gambar yang dibutuhkan secara manual di UI OpenCode jika didukung.
