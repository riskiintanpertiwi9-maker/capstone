/**
 * MoldGuard — settings.js
 * Preferensi lokal, tema, izin kamera, status model, dan hapus data.
 */
"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const { store, toast, confirmDialog, applyTheme } = window.MG;

  let settings = store.getSettings();
  const toggles = Array.from(document.querySelectorAll("[data-setting]"));
  const themeButtons = Array.from(document.querySelectorAll("[data-theme-choice]"));

  // ── Switch preferensi ───────────────────────────────────────────────────────
  function paintToggles() {
    toggles.forEach((btn) => {
      const key = btn.dataset.setting;
      const value = settings[key] !== false;
      btn.classList.toggle("is-on", value);
      btn.setAttribute("aria-checked", String(value));
    });
  }

  toggles.forEach((btn) => {
    btn.addEventListener("click", () => {
      const key = btn.dataset.setting;
      const next = !(settings[key] !== false);
      settings = store.saveSettings({ [key]: next });
      paintToggles();
      toast(next ? "Preferensi diaktifkan." : "Preferensi dinonaktifkan.", "info");
      if (window.MG.renderNotifications) window.MG.renderNotifications();
    });
  });

  // ── Tema ────────────────────────────────────────────────────────────────────
  function paintTheme() {
    themeButtons.forEach((btn) => {
      const active = btn.dataset.themeChoice === settings.theme;
      btn.classList.toggle("is-active", active);
      btn.setAttribute("aria-pressed", String(active));
    });
  }

  themeButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      settings = store.saveSettings({ theme: btn.dataset.themeChoice });
      applyTheme(settings.theme);
      paintTheme();
      toast("Tema diperbarui.", "success");
    });
  });

  // ── Penyimpanan ─────────────────────────────────────────────────────────────
  function paintStorage() {
    let bytes = 0;
    try {
      Object.keys(localStorage).forEach((key) => {
        if (!key.startsWith("moldguard.")) return;
        bytes += (key.length + (localStorage.getItem(key) || "").length) * 2;
      });
    } catch (err) {
      bytes = 0;
    }
    const kb = bytes / 1024;
    const size = kb >= 1024 ? `${(kb / 1024).toFixed(2)} MB` : `${kb.toFixed(1)} KB`;
    const history = store.getHistory().length;
    const reminders = store.getReminders().length;
    const el = document.getElementById("settings-storage");
    if (el) {
      el.textContent = `${size} terpakai · ${history} pemeriksaan · ${reminders} pengingat. Perkiraan kuota browser ±5 MB.`;
    }
  }

  // ── Izin kamera ─────────────────────────────────────────────────────────────
  const cameraText = document.getElementById("camera-permission");
  const cameraBadge = document.getElementById("camera-permission-badge");

  function paintCamera(state) {
    if (!cameraText || !cameraBadge) return;
    const map = {
      granted: { text: "Diizinkan browser. Kamera dapat dibuka dari halaman Deteksi.", label: "Diizinkan", tone: "success" },
      denied: { text: "Ditolak. Aktifkan izin kamera melalui pengaturan situs di browser, atau gunakan unggahan galeri.", label: "Ditolak", tone: "danger" },
      prompt: { text: "Belum diputuskan. Browser akan meminta izin saat Anda membuka kamera.", label: "Belum diputuskan", tone: "warning" },
    };
    const info = map[state] || { text: "Status izin tidak dapat dibaca di browser ini.", label: "Tidak diketahui", tone: "neutral" };
    cameraText.textContent = info.text;
    cameraBadge.textContent = info.label;
    cameraBadge.className = `badge badge--${info.tone}`;
  }

  async function checkCameraPermission() {
    if (!navigator.permissions || !navigator.permissions.query) {
      paintCamera("unknown");
      return;
    }
    try {
      const status = await navigator.permissions.query({ name: "camera" });
      paintCamera(status.state);
      status.onchange = () => paintCamera(status.state);
    } catch (err) {
      paintCamera("unknown");
    }
  }

  const checkBtn = document.getElementById("btn-check-camera");
  if (checkBtn) checkBtn.addEventListener("click", checkCameraPermission);

  // ── Status model ────────────────────────────────────────────────────────────
  async function paintModelStatus() {
    const el = document.getElementById("model-status");
    if (!el) return;
    try {
      const response = await fetch("/health", { headers: { Accept: "application/json" } });
      if (!response.ok) throw new Error("health gagal");
      const data = await response.json();
      if (data.yolo_available && data.mobile_available) {
        el.textContent = "Tersedia (YOLO + MobileNetV2)";
      } else if (data.yolo_available) {
        el.textContent = "YOLO tersedia, classifier tidak tersedia";
      } else {
        el.textContent = "Tidak tersedia";
      }
    } catch (err) {
      el.textContent = "Tidak dapat diperiksa";
    }
  }

  // ── Hapus data ──────────────────────────────────────────────────────────────
  const deleteBtn = document.getElementById("btn-delete-data");
  if (deleteBtn) {
    deleteBtn.addEventListener("click", async () => {
      const ok = await confirmDialog({
        title: "Hapus semua data?",
        message: "Seluruh riwayat pemeriksaan, pengingat, profil, dan preferensi akan dihapus dari perangkat ini. Tindakan ini tidak dapat dibatalkan.",
        confirmLabel: "Ya, hapus semua",
        cancelLabel: "Batal",
        danger: true,
      });
      if (!ok) return;
      store.clearAll();
      toast("Semua data perangkat telah dihapus.", "success");
      window.setTimeout(() => window.location.reload(), 900);
    });
  }

  // ── Render awal ─────────────────────────────────────────────────────────────
  paintToggles();
  paintTheme();
  paintStorage();
  checkCameraPermission();
  paintModelStatus();
});