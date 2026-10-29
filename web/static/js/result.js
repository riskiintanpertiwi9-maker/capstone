/**
 * MoldGuard — result.js
 * Merender hasil analisis dari riwayat (localStorage) atau hasil sementara
 * (sessionStorage). Tidak mengarang nilai di luar respons /predict.
 */
"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const { store, fmt, statusMeta, escapeHtml, toast } = window.MG;

  const params = new URLSearchParams(window.location.search);
  const requestedId = params.get("id");
  const pending = store.getPendingSession() || store.getPending();

  let item = null;
  let source = "pending";
  let saved = false;

  if (requestedId) {
    item = store.findHistory(requestedId);
    if (item) {
      source = "history";
      saved = true;
    } else if (pending && pending.id === requestedId) {
      item = pending;
    }
  } else if (pending) {
    item = pending;
  }

  const emptyEl = document.getElementById("result-empty");
  const viewEl = document.getElementById("result-view");

  function svg(name, size = 20) {
    return `<svg class="icon" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><use href="#i-${name}"></use></svg>`;
  }

  if (!item) {
    if (emptyEl) {
      emptyEl.hidden = false;
      if (requestedId) {
        document.getElementById("result-empty-title").textContent = "Hasil tidak ditemukan";
        document.getElementById("result-empty-text").textContent =
          "Hasil mungkin sudah dihapus dari riwayat perangkat ini, atau dibuka dari perangkat lain. Riwayat MoldGuard hanya tersimpan di browser Anda.";
      }
    }
    return;
  }

  if (emptyEl) emptyEl.hidden = true;
  if (viewEl) viewEl.hidden = false;

  // ── Status ──────────────────────────────────────────────────────────────────
  const meta = statusMeta(item.status);
  const banner = document.getElementById("result-status");
  banner.className = `result-banner result-banner--${meta.tone}`;
  document.getElementById("result-status-icon").innerHTML = svg(meta.icon, 24);

  const copy = {
    mold_detected: {
      title: "Indikasi Jamur Terdeteksi",
      text: "Model menandai area pada foto yang menyerupai pertumbuhan jamur. Ini adalah indikasi visual, bukan diagnosis atau hasil uji laboratorium.",
    },
    no_mold: {
      title: "Tidak Ada Indikasi yang Terdeteksi",
      text: "Model tidak menemukan area yang menyerupai jamur pada foto ini. Hasil ini bukan jaminan bahwa permukaan sepenuhnya bebas jamur.",
    },
    model_unavailable: {
      title: "Model Tidak Tersedia",
      text: "Pemeriksaan tidak dapat diselesaikan karena model AI tidak tersedia saat ini. Foto Anda tidak dianalisis.",
    },
  };
  const statusCopy = copy[item.status] || copy.model_unavailable;
  document.getElementById("result-status-title").textContent = statusCopy.title;
  document.getElementById("result-status-text").textContent = statusCopy.text;

  // ── Metadata ────────────────────────────────────────────────────────────────
  const models = item.models || {};
  const modelLine = models.yolo && models.mobile
    ? "YOLO + MobileNetV2"
    : models.yolo
      ? "YOLO (classifier tidak tersedia)"
      : models.mobile
        ? "MobileNetV2"
        : "Model tidak tersedia";

  document.getElementById("result-date").textContent = fmt.dateTime(item.createdAt);
  document.getElementById("result-location").textContent = item.location || "Tanpa lokasi";
  document.getElementById("result-boxes").textContent = String(item.boxes || 0);
  document.getElementById("result-models").textContent = modelLine;
  document.getElementById("result-model-line").textContent = `Diperiksa ${fmt.dateTime(item.createdAt)} · ${modelLine}`;

  // ── Foto ────────────────────────────────────────────────────────────────────
  const imageEl = document.getElementById("result-image");
  const badgeEl = document.getElementById("result-image-badge");
  const toggleEl = document.getElementById("image-toggle");

  const hasAnnotated = Boolean(item.annotatedThumb);
  const hasOriginal = Boolean(item.originalThumb);
  // Tanpa kotak deteksi, gambar "anotasi" identik dengan foto asli. Jangan
  // menampilkan tombol pembanding agar tidak menyiratkan ada anotasi.
  const hasBoxes = Array.isArray(item.detections) && item.detections.length > 0;
  let currentView = hasAnnotated && hasBoxes ? "annotated" : "original";

  function paintImage(view) {
    currentView = view;
    const src = view === "annotated"
      ? (item.annotatedThumb || item.originalThumb)
      : (item.originalThumb || item.annotatedThumb);
    if (!src) {
      imageEl.removeAttribute("src");
      imageEl.hidden = true;
      return;
    }
    imageEl.hidden = false;
    imageEl.src = src;
    imageEl.alt = `Foto pemeriksaan ${item.location || "tanpa lokasi"} — ${view === "annotated" ? "dengan anotasi model" : "foto asli"}`;
    badgeEl.textContent = view === "annotated" ? "Anotasi model" : "Foto asli";
    if (toggleEl) {
      toggleEl.querySelectorAll("[data-image-view]").forEach((btn) => {
        const active = btn.dataset.imageView === view;
        btn.classList.toggle("is-active", active);
        btn.setAttribute("aria-selected", String(active));
      });
    }
  }

  if (hasBoxes && hasAnnotated && hasOriginal && item.annotatedThumb !== item.originalThumb) {
    toggleEl.hidden = false;
    toggleEl.querySelectorAll("[data-image-view]").forEach((btn) => {
      btn.addEventListener("click", () => paintImage(btn.dataset.imageView));
    });
  }

  imageEl.addEventListener("error", () => {
    imageEl.hidden = true;
    badgeEl.textContent = "Pratinjau tidak tersedia";
  });

  paintImage(currentView);

  // ── Keyakinan model ─────────────────────────────────────────────────────────
  const confidenceCard = document.getElementById("confidence-card");
  const detections = Array.isArray(item.detections) ? item.detections : [];
  const hasConfidence = typeof item.topConfidence === "number" && Number.isFinite(item.topConfidence);

  if (hasConfidence && item.status === "mold_detected") {
    confidenceCard.hidden = false;
    const percent = Math.max(0, Math.min(100, item.topConfidence * 100));
    document.getElementById("confidence-fill").style.width = `${percent.toFixed(1)}%`;
    document.getElementById("confidence-value").textContent = `${percent.toFixed(1)}% keyakinan deteksi`;
    document.getElementById("confidence-meter").setAttribute(
      "aria-label",
      `Keyakinan deteksi model ${percent.toFixed(1)} persen untuk area paling yakin`
    );
  }

  // ── Daftar temuan ───────────────────────────────────────────────────────────
  const detectionList = document.getElementById("detection-list");
  const boxesCount = document.getElementById("boxes-count");

  if (!detections.length) {
    boxesCount.textContent = "0 area";
    detectionList.innerHTML = `<p class="muted-small">Tidak ada area yang ditandai model pada foto ini.</p>`;
  } else {
    boxesCount.textContent = `${detections.length} area`;
    detectionList.innerHTML = detections.map((det, index) => {
      const confidence = Number(det.confidence) || 0;
      const species = det.species
        ? `<span class="detection-item__species">Perkiraan spesies: <strong>${escapeHtml(det.species)}</strong>${det.species_confidence != null ? ` · ${(det.species_confidence * 100).toFixed(1)}%` : ""}</span>`
        : "";
      return `
        <article class="detection-item">
          <span class="detection-item__index">${index + 1}</span>
          <div class="detection-item__body">
            <div class="detection-item__head">
              <strong>Area menyerupai jamur</strong>
              <span class="chip chip--danger">${(confidence * 100).toFixed(1)}%</span>
            </div>
            ${species}
            <span class="detection-item__meta">Kotak ${index + 1}${det.bbox ? ` · posisi ${det.bbox.map((v) => Math.round(v)).join(", ")} px` : ""}</span>
          </div>
        </article>`;
    }).join("");
  }

  // ── Spesies ─────────────────────────────────────────────────────────────────
  const speciesCard = document.getElementById("species-card");
  const species = Array.isArray(item.species) ? item.species : [];
  const distribution = Array.isArray(item.speciesDistribution) ? item.speciesDistribution : [];
  const topSpecies = [];

  detections.forEach((det) => {
    if (!det.species) return;
    const found = topSpecies.find((row) => row.name === det.species);
    const conf = Number(det.species_confidence) || 0;
    if (found) found.confidence = Math.max(found.confidence, conf);
    else topSpecies.push({ name: det.species, confidence: conf });
  });

  if (species.length || distribution.length) {
    speciesCard.hidden = false;
    document.getElementById("species-list").innerHTML = topSpecies.length
      ? topSpecies.map((row) => `
        <div class="species-item">
          <span class="tile tile--mint">${svg("mushroom", 18)}</span>
          <div class="species-item__body">
            <strong>${escapeHtml(row.name)}</strong>
            <span>Keyakinan classifier ${(row.confidence * 100).toFixed(1)}% pada area yang ditandai</span>
          </div>
        </div>`).join("")
      : `<p class="muted-small">Classifier tidak memberikan label spesies pada area yang ditandai.</p>`;

    if (distribution.length) {
      document.getElementById("species-distribution").hidden = false;
      const sorted = distribution.slice().sort((a, b) => b.confidence - a.confidence);
      document.getElementById("distribution-list").innerHTML = sorted.map((row) => {
        const percent = Math.max(0, Math.min(100, row.confidence * 100));
        return `
          <div class="dist-row">
            <span class="dist-row__label">${escapeHtml(row.class)}</span>
            <span class="dist-row__track"><span style="width:${percent.toFixed(1)}%"></span></span>
            <span class="dist-row__value">${percent.toFixed(1)}%</span>
          </div>`;
      }).join("");
    }
  }

  // ── Rekomendasi ─────────────────────────────────────────────────────────────
  const RECOMMENDATIONS = {
    mold_detected: [
      ["Perbaiki sumber kelembapan", "Cari sumber rembesan atau kebocoran di sekitar area. Membasmi jamur tanpa memperbaiki sumber air hanya menunda masalah."],
      ["Tingkatkan sirkulasi udara", "Buka jendela secara rutin dan gunakan exhaust fan di area lembap seperti kamar mandi dan dapur."],
      ["Bersihkan area kecil dengan aman", "Gunakan sarung tangan dan masker, hindari menyikat kering agar spora tidak beterbangan, lalu keringkan permukaan."],
      ["Pertimbangkan bantuan profesional", "Jika area luas, berulang, atau menembus material berpori seperti gipsum, konsultasikan dengan jasa remediasi."],
    ],
    no_mold: [
      ["Tetap periksa secara berkala", "Ulangi pemeriksaan pada area rawan seperti sudut kamar mandi, bawah wastafel, dan belakang lemari."],
      ["Jaga kelembapan ruangan", "Ventilasi yang baik dan permukaan yang kering membantu mengurangi risiko pertumbuhan jamur."],
      ["Perhatikan tanda perubahan", "Noda gelap baru, bau apek, atau cat mengelupas adalah tanda yang perlu diperiksa lebih lanjut."],
    ],
    model_unavailable: [
      ["Coba lagi nanti", "Model AI sedang tidak tersedia. Foto Anda tidak dianalisis dan tidak disimpan oleh server."],
      ["Periksa koneksi dan pencahayaan", "Pastikan foto jelas dan terang sebelum mencoba pemeriksaan ulang."],
    ],
  };

  const recommendationList = document.getElementById("recommendation-list");
  recommendationList.innerHTML = (RECOMMENDATIONS[item.status] || RECOMMENDATIONS.model_unavailable)
    .map(([title, text]) => `
      <li>
        <span class="checklist__icon">${svg("check", 14)}</span>
        <div>
          <strong>${escapeHtml(title)}</strong>
          <p>${escapeHtml(text)}</p>
        </div>
      </li>`).join("");

  // ── Catatan teknis ──────────────────────────────────────────────────────────
  const errors = Array.isArray(item.errors) ? item.errors : [];
  const errorBox = document.getElementById("result-errors");
  if (errors.length) {
    errorBox.hidden = false;
    errorBox.innerHTML = `<strong>Catatan teknis:</strong><ul>${errors.map((err) => `<li>${escapeHtml(err)}</li>`).join("")}</ul>`;
  }

  // ── Simpan ──────────────────────────────────────────────────────────────────
  const saveBtn = document.getElementById("btn-save");
  const saveLabel = document.getElementById("btn-save-label");

  function paintSaveButton() {
    if (!saveBtn) return;
    saveBtn.disabled = saved;
    saveBtn.setAttribute("aria-disabled", String(saved));
    if (saveLabel) saveLabel.textContent = saved ? "Tersimpan di Riwayat" : "Simpan Hasil";
    saveBtn.classList.toggle("btn--primary", !saved);
    saveBtn.classList.toggle("btn--secondary", saved);
  }

  function saveResult() {
    if (saved) return;
    const stored = {
      id: item.id,
      createdAt: item.createdAt,
      location: item.location || "",
      status: item.status,
      boxes: item.boxes || 0,
      detections: item.detections || [],
      species: item.species || [],
      topConfidence: item.topConfidence == null ? null : item.topConfidence,
      speciesDistribution: item.speciesDistribution || [],
      originalThumb: item.originalThumb || null,
      annotatedThumb: item.annotatedThumb || null,
      thumb: item.thumb || item.annotatedThumb || item.originalThumb || null,
      errors: item.errors || [],
      models: item.models || { yolo: false, mobile: false },
    };
    store.addHistory(stored);
    saved = true;
    source = "history";
    store.clearPending();
    paintSaveButton();
    try {
      window.history.replaceState({}, "", `/hasil?id=${encodeURIComponent(stored.id)}`);
    } catch (err) { /* URL boleh gagal diperbarui di beberapa browser */ }
    toast("Hasil disimpan ke riwayat perangkat ini.", "success");
    if (window.MG.renderNotifications) window.MG.renderNotifications();
  }

  if (saveBtn) saveBtn.addEventListener("click", saveResult);
  paintSaveButton();

  // ── Cetak ───────────────────────────────────────────────────────────────────
  const printBtn = document.getElementById("btn-print");
  if (printBtn) {
    printBtn.addEventListener("click", () => {
      toast("Dialog cetak dibuka. Pilih “Simpan sebagai PDF” untuk menyimpan laporan.", "info");
      window.setTimeout(() => window.print(), 150);
    });
  }

  // Jika hasil dibuka langsung dari sesi baru, pastikan URL dapat dibagikan
  // di perangkat yang sama setelah disimpan.
  if (source === "pending" && saved) {
    try { window.history.replaceState({}, "", `/hasil?id=${encodeURIComponent(item.id)}`); } catch (err) { /* noop */ }
  }
});