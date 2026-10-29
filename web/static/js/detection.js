/**
 * MoldGuard — detection.js
 * Mengelola kamera, unggahan foto, validasi, pemanggilan /predict,
 * dan penyerahan hasil ke halaman /hasil melalui sessionStorage.
 */
"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const { store, fmt, toast, uid, compressImage } = window.MG;

  const MAX_BYTES = 16 * 1024 * 1024;
  const ALLOWED_TYPES = ["image/png", "image/jpeg", "image/jpg", "image/webp", "image/bmp"];
  const ALLOWED_EXT = /\.(png|jpe?g|webp|bmp)$/i;
  const CONF = 0.35;

  const tabCamera = document.getElementById("tab-kamera");
  const tabUpload = document.getElementById("tab-unggah");
  const panelCamera = document.getElementById("panel-kamera");
  const panelUpload = document.getElementById("panel-unggah");

  const video = document.getElementById("camera-video");
  const canvas = document.getElementById("camera-canvas");
  const photoPreview = document.getElementById("camera-photo-preview");
  const placeholder = document.getElementById("camera-placeholder");
  const cameraTip = document.getElementById("camera-tip");
  const cameraStatus = document.getElementById("camera-status-msg");
  const cornerGuide = document.querySelector(".corner-guide");

  const btnOpenCamera = document.getElementById("btn-buka-kamera");
  const btnCapture = document.getElementById("btn-ambil-foto");
  const btnRetake = document.getElementById("btn-ulangi-foto");
  const btnUse = document.getElementById("btn-gunakan-foto");
  const btnCloseCamera = document.getElementById("btn-tutup-kamera");

  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("file-input");
  const uploadWrap = document.getElementById("upload-preview-wrap");
  const uploadImg = document.getElementById("upload-preview-img");
  const fileNameEl = document.getElementById("upload-filename");
  const btnRemoveUpload = document.getElementById("btn-hapus-foto");

  const locationInput = document.getElementById("location-input");
  const analyzeBtn = document.getElementById("btn-periksa");
  const analyzeLabel = analyzeBtn ? analyzeBtn.querySelector(".btn-label") : null;
  const analyzeSpinner = analyzeBtn ? analyzeBtn.querySelector(".btn-spinner") : null;
  const errorBox = document.getElementById("analysis-error");
  const overlay = document.getElementById("loading-overlay");

  let stream = null;
  let cameraState = "idle"; // idle | live | captured
  let selectedFile = null;
  let capturedBlob = null;
  let analyzing = false;
  let objectUrl = null;

  // ── Bantuan UI ──────────────────────────────────────────────────────────────
  function showError(message) {
    if (!errorBox) return;
    errorBox.hidden = false;
    errorBox.innerHTML = `<svg class="icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><use href="#i-alert-circle"></use></svg><span>${window.MG.escapeHtml(message)}</span>`;
    if (typeof errorBox.scrollIntoView === "function") {
      errorBox.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }

  function clearError() {
    if (errorBox) {
      errorBox.hidden = true;
      errorBox.textContent = "";
    }
  }

  function setCameraMessage(html) {
    if (cameraStatus) cameraStatus.innerHTML = `<svg class="icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><use href="#i-info"></use></svg><span>${html}</span>`;
  }

  function cameraErrorMessage(err) {
    const name = err && err.name ? err.name : "";
    if (!window.isSecureContext) {
      return "Kamera memerlukan HTTPS atau localhost. Anda masih bisa mengunggah foto dari galeri.";
    }
    if (name === "NotAllowedError" || name === "SecurityError") {
      return "Izin kamera ditolak. Aktifkan izin kamera di pengaturan browser, lalu coba lagi — atau gunakan tab Galeri.";
    }
    if (name === "NotFoundError" || name === "OverconstrainedError") {
      return "Kamera tidak ditemukan pada perangkat ini. Silakan unggah foto dari galeri.";
    }
    if (name === "NotReadableError" || name === "TrackStartError") {
      return "Kamera sedang dipakai aplikasi lain. Tutup aplikasi tersebut lalu coba lagi.";
    }
    return "Kamera tidak dapat diakses. Periksa izin browser atau gunakan unggahan foto.";
  }

  function stopStream() {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      stream = null;
    }
    if (video) video.srcObject = null;
  }

  function syncCameraUi() {
    if (video) video.hidden = cameraState !== "live";
    if (photoPreview) photoPreview.hidden = cameraState !== "captured";
    if (placeholder) placeholder.hidden = cameraState !== "idle";
    if (cornerGuide) cornerGuide.hidden = cameraState === "captured";
    if (cameraTip) cameraTip.hidden = cameraState === "captured";

    if (btnOpenCamera) btnOpenCamera.hidden = cameraState !== "idle";
    if (btnCapture) btnCapture.hidden = cameraState !== "live";
    if (btnRetake) btnRetake.hidden = cameraState !== "captured";
    if (btnUse) btnUse.hidden = cameraState !== "captured";
    if (btnCloseCamera) btnCloseCamera.hidden = cameraState === "idle";
  }

  function syncAnalyzeBtn() {
    if (!analyzeBtn) return;
    analyzeBtn.disabled = !selectedFile || analyzing;
  }

  function setSelectedFile(file) {
    selectedFile = file;
    syncAnalyzeBtn();
  }

  function resetUploadPreview() {
    if (objectUrl) {
      URL.revokeObjectURL(objectUrl);
      objectUrl = null;
    }
    if (uploadWrap) uploadWrap.hidden = true;
    if (uploadImg) uploadImg.removeAttribute("src");
    if (fileNameEl) fileNameEl.textContent = "";
    if (fileInput) fileInput.value = "";
    if (dropZone) dropZone.hidden = false;
  }

  function resetCapture() {
    cameraState = "idle";
    stopStream();
    if (photoPreview) photoPreview.removeAttribute("src");
    capturedBlob = null;
    syncCameraUi();
  }

  // ── Tab ─────────────────────────────────────────────────────────────────────
  function activateTab(which) {
    const isCamera = which === "camera";
    if (tabCamera) {
      tabCamera.classList.toggle("is-active", isCamera);
      tabCamera.setAttribute("aria-selected", String(isCamera));
    }
    if (tabUpload) {
      tabUpload.classList.toggle("is-active", !isCamera);
      tabUpload.setAttribute("aria-selected", String(!isCamera));
    }
    if (panelCamera) panelCamera.hidden = !isCamera;
    if (panelUpload) panelUpload.hidden = isCamera;

    if (!isCamera) {
      // Lepaskan kamera saat tidak terlihat agar indikator perangkat mati.
      stopStream();
      if (cameraState === "live") {
        cameraState = "idle";
        syncCameraUi();
      }
    }
  }

  if (tabCamera) tabCamera.addEventListener("click", () => activateTab("camera"));
  if (tabUpload) tabUpload.addEventListener("click", () => activateTab("upload"));

  // ── Kamera ──────────────────────────────────────────────────────────────────
  async function openCamera() {
    clearError();
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      showError("Browser ini tidak mendukung akses kamera. Gunakan tab Galeri untuk mengunggah foto.");
      return;
    }
    btnOpenCamera.disabled = true;
    setCameraMessage("Meminta izin kamera…");
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: false,
        video: { facingMode: { ideal: "environment" }, width: { ideal: 1920 }, height: { ideal: 1440 } },
      });
      video.srcObject = stream;
      await video.play().catch(() => {});
      cameraState = "live";
      syncCameraUi();
      setCameraMessage("Kamera aktif. Arahkan ke area yang dicurigai, lalu tekan <strong>Ambil Foto</strong>.");
    } catch (err) {
      console.warn("Kamera gagal dibuka", err);
      cameraState = "idle";
      syncCameraUi();
      setCameraMessage("Kamera tidak aktif.");
      showError(cameraErrorMessage(err));
    } finally {
      btnOpenCamera.disabled = false;
    }
  }

  function capturePhoto() {
    if (!video || !canvas || cameraState !== "live") return;
    const w = video.videoWidth;
    const h = video.videoHeight;
    if (!w || !h) {
      showError("Kamera belum siap. Tunggu sebentar lalu coba lagi.");
      return;
    }
    canvas.width = w;
    canvas.height = h;
    canvas.getContext("2d").drawImage(video, 0, 0, w, h);
    canvas.toBlob((blob) => {
      if (!blob) {
        showError("Gagal mengambil foto. Coba lagi.");
        return;
      }
      capturedBlob = blob;
      photoPreview.src = URL.createObjectURL(blob);
      photoPreview.alt = "Foto hasil kamera, siap dianalisis";
      cameraState = "captured";
      stopStream();
      syncCameraUi();
      setCameraMessage("Foto siap. Periksa hasilnya, lalu tekan <strong>Gunakan Foto</strong> untuk melanjutkan.");
    }, "image/jpeg", 0.92);
  }

  function useCapturedPhoto() {
    if (!capturedBlob) return;
    const stamp = new Date().toISOString().replace(/[:.]/g, "-");
    const file = new File([capturedBlob], `kamera-${stamp}.jpg`, { type: "image/jpeg" });
    setSelectedFile(file);
    toast("Foto kamera siap dianalisis.", "success");
    const target = document.getElementById("btn-periksa");
    if (target) target.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  if (btnOpenCamera) btnOpenCamera.addEventListener("click", openCamera);
  if (btnCapture) btnCapture.addEventListener("click", capturePhoto);
  if (btnRetake) btnRetake.addEventListener("click", () => {
    capturedBlob = null;
    cameraState = "idle";
    if (photoPreview) photoPreview.removeAttribute("src");
    syncCameraUi();
    openCamera();
  });
  if (btnUse) btnUse.addEventListener("click", useCapturedPhoto);
  if (btnCloseCamera) btnCloseCamera.addEventListener("click", () => {
    resetCapture();
    setSelectedFile(null);
    setCameraMessage("Kamera ditutup. Anda dapat membukanya kembali atau mengunggah foto dari galeri.");
  });

  // ── Unggah ──────────────────────────────────────────────────────────────────
  function validateFile(file) {
    if (!file) return "Tidak ada file yang dipilih.";
    const typeOk = file.type ? ALLOWED_TYPES.includes(file.type) : ALLOWED_EXT.test(file.name);
    if (!typeOk || !ALLOWED_EXT.test(file.name)) {
      return "Format tidak didukung. Gunakan PNG, JPG, JPEG, WEBP, atau BMP.";
    }
    if (file.size > MAX_BYTES) {
      return `Ukuran file ${(file.size / 1024 / 1024).toFixed(1)}MB melebihi batas 16MB.`;
    }
    if (file.size === 0) return "File kosong. Pilih file lain.";
    return "";
  }

  function handleFile(file) {
    clearError();
    const error = validateFile(file);
    if (error) {
      showError(error);
      resetUploadPreview();
      setSelectedFile(null);
      return;
    }
    if (objectUrl) URL.revokeObjectURL(objectUrl);
    objectUrl = URL.createObjectURL(file);
    uploadImg.src = objectUrl;
    uploadImg.alt = `Pratinjau ${file.name}`;
    fileNameEl.textContent = `${file.name} · ${(file.size / 1024).toFixed(0)}KB`;
    uploadWrap.hidden = false;
    dropZone.hidden = true;
    setSelectedFile(file);
  }

  if (dropZone) {
    dropZone.addEventListener("click", () => fileInput.click());
    dropZone.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        fileInput.click();
      }
    });
    ["dragenter", "dragover"].forEach((name) => {
      dropZone.addEventListener(name, (event) => {
        event.preventDefault();
        dropZone.classList.add("is-dragover");
      });
    });
    ["dragleave", "drop"].forEach((name) => {
      dropZone.addEventListener(name, (event) => {
        event.preventDefault();
        dropZone.classList.remove("is-dragover");
      });
    });
    dropZone.addEventListener("drop", (event) => {
      const file = event.dataTransfer && event.dataTransfer.files ? event.dataTransfer.files[0] : null;
      handleFile(file);
    });
  }

  if (fileInput) {
    fileInput.addEventListener("change", () => handleFile(fileInput.files[0]));
  }

  if (btnRemoveUpload) {
    btnRemoveUpload.addEventListener("click", () => {
      resetUploadPreview();
      setSelectedFile(null);
      clearError();
    });
  }

  // ── Analisis ────────────────────────────────────────────────────────────────
  async function analyze() {
    if (!selectedFile || analyzing) return;
    clearError();
    analyzing = true;
    syncAnalyzeBtn();
    if (analyzeLabel) analyzeLabel.innerHTML = '<span class="spin icon-wrap">Menganalisis…</span>';
    if (analyzeSpinner) analyzeSpinner.hidden = false;
    if (overlay) overlay.hidden = false;
    document.body.classList.add("is-loading");

    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 120000);

    try {
      const body = new FormData();
      body.append("file", selectedFile, selectedFile.name || "foto.jpg");
      body.append("conf", String(CONF));

      const response = await fetch("/predict", { method: "POST", body, signal: controller.signal });
      let payload = null;
      try {
        payload = await response.json();
      } catch (err) {
        payload = null;
      }

      if (!response.ok) {
        const message = payload && payload.error
          ? payload.error
          : `Analisis gagal (HTTP ${response.status}). Coba lagi beberapa saat.`;
        throw new Error(message);
      }
      if (!payload) throw new Error("Respons server tidak dapat dibaca. Coba lagi.");
      if (payload.error) throw new Error(payload.error);

      await handoff(payload);
    } catch (err) {
      console.warn("Analisis gagal", err);
      const message = err && err.name === "AbortError"
        ? "Analisis melebihi waktu tunggu. Periksa koneksi lalu coba lagi."
        : (err && err.message ? err.message : "Terjadi kesalahan saat menganalisis gambar.");
      showError(`${message} Foto Anda masih tersimpan di halaman ini, silakan coba lagi.`);
      toast("Analisis gagal. Silakan coba lagi.", "error");
    } finally {
      window.clearTimeout(timeout);
      analyzing = false;
      if (overlay) overlay.hidden = true;
      document.body.classList.remove("is-loading");
      if (analyzeLabel) analyzeLabel.innerHTML = '<svg class="icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><use href="#i-scan"></use></svg> Mulai Analisis';
      if (analyzeSpinner) analyzeSpinner.hidden = true;
      syncAnalyzeBtn();
    }
  }

  async function handoff(payload) {
    const annotated = payload.annotated_image ? `data:image/jpeg;base64,${payload.annotated_image}` : null;
    const original = payload.original_image ? `data:image/jpeg;base64,${payload.original_image}` : null;

    const [originalThumb, annotatedThumb] = await Promise.all([
      compressImage(original, 900, 0.78),
      compressImage(annotated, 900, 0.8),
    ]);

    const detections = Array.isArray(payload.yolo)
      ? payload.yolo.map((det) => ({
        class: det.class,
        confidence: Number(det.confidence) || 0,
        bbox: Array.isArray(det.bbox) ? det.bbox : null,
        species: det.species || null,
        species_confidence: det.species_confidence == null ? null : Number(det.species_confidence),
      }))
      : [];

    const species = [];
    detections.forEach((det) => {
      if (det.species && !species.includes(det.species)) species.push(det.species);
    });

    const topConfidence = detections.length
      ? Math.max(...detections.map((det) => det.confidence))
      : null;

    const item = {
      id: uid(),
      createdAt: new Date().toISOString(),
      location: (locationInput && locationInput.value.trim()) || "",
      status: payload.status || "no_mold",
      boxes: detections.length,
      detections,
      species,
      topConfidence,
      speciesDistribution: Array.isArray(payload.mobilenet)
        ? payload.mobilenet.map((cls) => ({ class: cls.class, confidence: Number(cls.confidence) || 0 }))
        : [],
      originalThumb: originalThumb || original,
      annotatedThumb: annotatedThumb || originalThumb || annotated,
      thumb: annotatedThumb || originalThumb || original,
      errors: Array.isArray(payload.error_details) ? payload.error_details : [],
      models: {
        yolo: Boolean(payload.yolo_available),
        mobile: Boolean(payload.mobile_available),
      },
    };

    store.savePending(item);
    window.location.assign("/hasil");
  }

  if (analyzeBtn) analyzeBtn.addEventListener("click", analyze);

  // ── Kebersihan saat halaman ditinggalkan ────────────────────────────────────
  window.addEventListener("pagehide", stopStream);
  document.addEventListener("visibilitychange", () => {
    if (document.hidden && cameraState === "live") {
      // Jangan matikan kamera otomatis saat pengguna berpindah aplikasi sebentar;
      // cukup hentikan ketika halaman benar-benar ditinggalkan (pagehide).
      return;
    }
  });

  syncCameraUi();
  syncAnalyzeBtn();
});