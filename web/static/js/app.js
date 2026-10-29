/**
 * MoldGuard — utilitas bersama (app.js)
 * Berisi penyimpanan lokal, format tanggal, toast, modal, dan perilaku app shell.
 * Tidak ada data contoh yang di-hardcode sebagai data pengguna.
 */
"use strict";

const MG = (function () {
  const KEYS = {
    settings: "moldguard.settings",
    profile: "moldguard.profile",
    history: "moldguard.history",
    reminders: "moldguard.reminders",
    pending: "moldguard.pending",
  };

  const DEFAULT_SETTINGS = {
    theme: "light",
    notifyResults: true,
    notifyTips: true,
    notifyReminders: true,
    dataUsage: true,
    analytics: false,
    language: "id",
  };

  const DEFAULT_PROFILE = {
    name: "Pengguna MoldGuard",
    email: "",
    createdAt: new Date().toISOString(),
  };

  // ── Penyimpanan ─────────────────────────────────────────────────────────────
  function read(key, fallback) {
    try {
      const raw = localStorage.getItem(key);
      if (!raw) return fallback;
      const parsed = JSON.parse(raw);
      return parsed == null ? fallback : parsed;
    } catch (err) {
      console.warn("Gagal membaca penyimpanan", key, err);
      return fallback;
    }
  }

  function write(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (err) {
      console.warn("Gagal menyimpan", key, err);
      toast("Penyimpanan perangkat penuh. Hapus beberapa riwayat lama.", "error");
      return false;
    }
  }

  const store = {
    getSettings() { return Object.assign({}, DEFAULT_SETTINGS, read(KEYS.settings, {})); },
    saveSettings(next) {
      const merged = Object.assign({}, store.getSettings(), next);
      write(KEYS.settings, merged);
      return merged;
    },
    getProfile() { return Object.assign({}, DEFAULT_PROFILE, read(KEYS.profile, {})); },
    saveProfile(next) {
      const merged = Object.assign({}, store.getProfile(), next);
      write(KEYS.profile, merged);
      return merged;
    },
    getHistory() {
      const list = read(KEYS.history, []);
      return Array.isArray(list) ? list : [];
    },
    saveHistory(list) { return write(KEYS.history, Array.isArray(list) ? list : []); },
    addHistory(item) {
      const list = store.getHistory().filter((row) => row.id !== item.id);
      list.unshift(item);
      // Batasi agar penyimpanan browser tidak penuh (thumbnail sudah dikompres).
      store.saveHistory(list.slice(0, 40));
      return item;
    },
    findHistory(id) { return store.getHistory().find((row) => row.id === id) || null; },
    removeHistory(id) {
      store.saveHistory(store.getHistory().filter((row) => row.id !== id));
    },
    getReminders() {
      const list = read(KEYS.reminders, []);
      return Array.isArray(list) ? list : [];
    },
    saveReminders(list) { return write(KEYS.reminders, Array.isArray(list) ? list : []); },
    getPending() { return read(KEYS.pending, null); },
    savePending(item) {
      try {
        sessionStorage.setItem(KEYS.pending, JSON.stringify(item));
      } catch (err) {
        console.warn("Hasil sementara terlalu besar untuk sessionStorage", err);
        write(KEYS.pending, item);
      }
    },
    getPendingSession() {
      try {
        const raw = sessionStorage.getItem(KEYS.pending);
        return raw ? JSON.parse(raw) : null;
      } catch (err) {
        return null;
      }
    },
    clearPending() {
      try { sessionStorage.removeItem(KEYS.pending); } catch (err) { /* noop */ }
    },
    clearAll() {
      Object.values(KEYS).forEach((key) => {
        try { localStorage.removeItem(key); } catch (err) { /* noop */ }
        try { sessionStorage.removeItem(key); } catch (err) { /* noop */ }
      });
    },
  };

  // ── Format ──────────────────────────────────────────────────────────────────
  const dateFmt = new Intl.DateTimeFormat("id-ID", { day: "numeric", month: "short", year: "numeric" });
  const dateLongFmt = new Intl.DateTimeFormat("id-ID", { day: "numeric", month: "long", year: "numeric" });
  const timeFmt = new Intl.DateTimeFormat("id-ID", { hour: "2-digit", minute: "2-digit" });

  const fmt = {
    date(value) {
      const d = value instanceof Date ? value : new Date(value);
      return isNaN(d) ? "—" : dateFmt.format(d);
    },
    dateLong(value) {
      const d = value instanceof Date ? value : new Date(value);
      return isNaN(d) ? "—" : dateLongFmt.format(d);
    },
    dateTime(value) {
      const d = value instanceof Date ? value : new Date(value);
      return isNaN(d) ? "—" : `${dateFmt.format(d)} ${timeFmt.format(d)}`;
    },
    time(value) {
      const d = value instanceof Date ? value : new Date(value);
      return isNaN(d) ? "—" : timeFmt.format(d);
    },
    isoDay(value) {
      const d = value instanceof Date ? value : new Date(value);
      if (isNaN(d)) return "";
      const mm = String(d.getMonth() + 1).padStart(2, "0");
      const dd = String(d.getDate()).padStart(2, "0");
      return `${d.getFullYear()}-${mm}-${dd}`;
    },
    pct(value) {
      const n = Number(value);
      return Number.isFinite(n) ? `${(n * 100).toFixed(1)}%` : "—";
    },
    relative(value) {
      const d = new Date(value);
      if (isNaN(d)) return "—";
      const diff = Date.now() - d.getTime();
      const day = 86400000;
      if (diff < day && d.getDate() === new Date().getDate()) return `Hari ini, ${timeFmt.format(d)}`;
      if (diff < day * 2) return `Kemarin, ${timeFmt.format(d)}`;
      if (diff < day * 7) return `${Math.floor(diff / day)} hari lalu`;
      return dateFmt.format(d);
    },
  };

  function uid() {
    if (window.crypto && typeof window.crypto.randomUUID === "function") return window.crypto.randomUUID();
    return `mg-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;
  }

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function statusMeta(status) {
    if (status === "mold_detected") {
      return { label: "Indikasi terdeteksi", short: "Terindikasi", tone: "danger", icon: "mushroom" };
    }
    if (status === "model_unavailable") {
      return { label: "Model tidak tersedia", short: "Model tidak tersedia", tone: "warning", icon: "alert-triangle" };
    }
    return { label: "Tidak ada indikasi", short: "Tidak terindikasi", tone: "success", icon: "check-circle" };
  }

  // ── Tema ────────────────────────────────────────────────────────────────────
  function applyTheme(theme) {
    const value = theme || store.getSettings().theme || "light";
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const dark = value === "dark" || (value === "system" && prefersDark);
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    document.querySelectorAll("[data-theme-choice]").forEach((btn) => {
      const active = btn.dataset.themeChoice === value;
      btn.classList.toggle("is-active", active);
      btn.setAttribute("aria-pressed", String(active));
    });
  }

  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    if (store.getSettings().theme === "system") applyTheme("system");
  });

  // ── Toast ───────────────────────────────────────────────────────────────────
  function toast(message, type = "info") {
    const root = document.getElementById("toast-root");
    if (!root) return;
    const el = document.createElement("div");
    const iconName = type === "error" ? "alert-circle" : type === "success" ? "check-circle" : "info";
    el.className = `toast toast--${type}`;
    el.setAttribute("role", type === "error" ? "alert" : "status");
    el.innerHTML = `<svg class="icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><use href="#i-${iconName}"></use></svg><span>${escapeHtml(message)}</span>`;
    root.appendChild(el);
    // Jaga agar tumpukan toast tidak menutupi konten saat aksi beruntun.
    while (root.children.length > 3) root.firstElementChild.remove();
    requestAnimationFrame(() => el.classList.add("is-visible"));
    window.setTimeout(() => {
      el.classList.remove("is-visible");
      window.setTimeout(() => el.remove(), 220);
    }, 3600);
  }

  // ── Modal & konfirmasi ──────────────────────────────────────────────────────
  let lastFocused = null;

  function closeModal() {
    const root = document.getElementById("modal-root");
    if (!root) return;
    root.innerHTML = "";
    document.body.classList.remove("modal-open");
    if (lastFocused && typeof lastFocused.focus === "function") lastFocused.focus();
    lastFocused = null;
  }

  function openModal(innerHtml, options = {}) {
    const root = document.getElementById("modal-root");
    if (!root) return null;
    lastFocused = document.activeElement;
    root.innerHTML = `
      <div class="modal-scrim" data-modal-close="1"></div>
      <div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <div class="modal__head">
          <h2 id="modal-title">${escapeHtml(options.title || "Konfirmasi")}</h2>
          <button class="icon-btn icon-btn--ghost" type="button" data-modal-close="1" aria-label="Tutup dialog">
            <svg class="icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><use href="#i-x"></use></svg>
          </button>
        </div>
        <div class="modal__body">${innerHtml}</div>
      </div>`;
    document.body.classList.add("modal-open");
    root.querySelectorAll("[data-modal-close]").forEach((el) => el.addEventListener("click", closeModal));
    const focusable = root.querySelector("input, select, textarea, button:not([data-modal-close])");
    if (focusable) focusable.focus();
    root.querySelector(".modal").addEventListener("keydown", trapFocus);
    return root.querySelector(".modal");
  }

  function trapFocus(event) {
    if (event.key === "Escape") { closeModal(); return; }
    if (event.key !== "Tab") return;
    const nodes = this.querySelectorAll('a[href], button:not([disabled]), input, select, textarea, [tabindex]:not([tabindex="-1"])');
    if (!nodes.length) return;
    const first = nodes[0];
    const last = nodes[nodes.length - 1];
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  }

  function confirmDialog(opts = {}) {
    return new Promise((resolve) => {
      const modal = openModal(`
        <p class="modal-text">${escapeHtml(opts.message || "Lanjutkan tindakan ini?")}</p>
        <div class="modal-actions">
          <button class="btn btn--secondary" type="button" data-answer="no">${escapeHtml(opts.cancelLabel || "Batal")}</button>
          <button class="btn ${opts.danger ? "btn--danger" : "btn--primary"}" type="button" data-answer="yes">${escapeHtml(opts.confirmLabel || "Lanjutkan")}</button>
        </div>`, { title: opts.title || "Konfirmasi" });
      if (!modal) { resolve(false); return; }
      modal.querySelectorAll("[data-answer]").forEach((btn) => {
        btn.addEventListener("click", () => {
          const answer = btn.dataset.answer === "yes";
          closeModal();
          resolve(answer);
        });
      });
      modal.querySelector('[data-answer="no"]').focus();
    });
  }

  // ── Kompresi gambar ─────────────────────────────────────────────────────────
  function compressImage(source, maxSize = 560, quality = 0.72) {
    return new Promise((resolve) => {
      if (!source) { resolve(null); return; }
      const img = new Image();
      img.onload = () => {
        const scale = Math.min(1, maxSize / Math.max(img.width, img.height));
        const canvas = document.createElement("canvas");
        canvas.width = Math.max(1, Math.round(img.width * scale));
        canvas.height = Math.max(1, Math.round(img.height * scale));
        const ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        try { resolve(canvas.toDataURL("image/jpeg", quality)); }
        catch (err) { resolve(null); }
      };
      img.onerror = () => resolve(null);
      img.src = source;
    });
  }

  // ── Notifikasi popover ──────────────────────────────────────────────────────
  function renderNotifications() {
    const list = document.getElementById("notif-list");
    const dot = document.getElementById("notif-dot");
    if (!list) return;
    const history = store.getHistory();
    const reminders = store.getReminders().filter((r) => r.active !== false);
    const settings = store.getSettings();
    const items = [];

    if (settings.notifyResults !== false) history.slice(0, 3).forEach((row) => {
      const meta = statusMeta(row.status);
      items.push(`
        <a class="notif-item" href="/hasil?id=${encodeURIComponent(row.id)}">
          <span class="notif-item__icon notif-item__icon--${meta.tone}">
            <svg class="icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><use href="#i-${meta.icon}"></use></svg>
          </span>
          <span class="notif-item__body">
            <span class="notif-item__title">${escapeHtml(meta.label)}</span>
            <span class="notif-item__meta">${escapeHtml(row.location || "Tanpa lokasi")} · ${escapeHtml(fmt.relative(row.createdAt))}</span>
          </span>
        </a>`);
    });

    const soon = settings.notifyReminders === false
      ? []
      : reminders
        .slice()
        .sort((a, b) => String(a.nextDate).localeCompare(String(b.nextDate)))
        .slice(0, 2);
    soon.forEach((rem) => {
      items.push(`
        <a class="notif-item" href="/pengingat">
          <span class="notif-item__icon notif-item__icon--info">
            <svg class="icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><use href="#i-calendar"></use></svg>
          </span>
          <span class="notif-item__body">
            <span class="notif-item__title">${escapeHtml(rem.name)}</span>
            <span class="notif-item__meta">Jadwal ${escapeHtml(fmt.date(rem.nextDate))}</span>
          </span>
        </a>`);
    });

    if (!items.length) {
      list.innerHTML = '<p class="muted-small">Belum ada aktivitas. Mulai pemeriksaan atau tambahkan pengingat.</p>';
    } else {
      list.innerHTML = items.join("");
    }
    if (dot) dot.hidden = items.length === 0;
  }

  function initShell() {
    applyTheme();
    const profile = store.getProfile();
    const initial = (profile.name || "P").trim().charAt(0).toUpperCase() || "P";
    document.querySelectorAll(".avatar").forEach((el) => { el.textContent = initial; });

    const drawerToggle = document.getElementById("drawer-toggle");
    const scrim = document.getElementById("drawer-scrim");
    const setDrawer = (open) => {
      document.body.classList.toggle("drawer-open", open);
      if (drawerToggle) drawerToggle.setAttribute("aria-expanded", String(open));
    };
    if (drawerToggle) drawerToggle.addEventListener("click", () => setDrawer(!document.body.classList.contains("drawer-open")));
    if (scrim) scrim.addEventListener("click", () => setDrawer(false));
    document.querySelectorAll(".side-link").forEach((link) => link.addEventListener("click", () => setDrawer(false)));
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") setDrawer(false);
    });

    const notifBtn = document.getElementById("btn-notifications");
    const notifPanel = document.getElementById("notif-panel");
    if (notifBtn && notifPanel) {
      notifBtn.addEventListener("click", (event) => {
        event.stopPropagation();
        const open = notifPanel.hidden;
        notifPanel.hidden = !open;
        notifBtn.setAttribute("aria-expanded", String(open));
        if (open) renderNotifications();
      });
      document.addEventListener("click", (event) => {
        if (!notifPanel.hidden && !notifPanel.contains(event.target) && !notifBtn.contains(event.target)) {
          notifPanel.hidden = true;
          notifBtn.setAttribute("aria-expanded", "false");
        }
      });
    }
    renderNotifications();

    // Pencarian global mengikuti konteks halaman.
    const searchForm = document.querySelector(".topbar-search");
    if (searchForm) {
      const page = document.body.dataset.page;
      if (page === "edukasi") searchForm.setAttribute("action", "/edukasi");
    }
  }

  document.addEventListener("DOMContentLoaded", initShell);

  return {
    KEYS, store, fmt, uid, escapeHtml, statusMeta, applyTheme,
    toast, openModal, closeModal, confirmDialog, compressImage,
    renderNotifications,
  };
})();

window.MG = MG;