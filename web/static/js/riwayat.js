/**
 * MoldGuard — riwayat.js
 * Daftar, pencarian, filter, pratinjau, dan penghapusan riwayat lokal.
 */
"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const { store, fmt, statusMeta, escapeHtml, toast, confirmDialog, renderNotifications } = window.MG;

  const listEl = document.getElementById("history-list");
  const previewEl = document.getElementById("history-preview");
  const searchEl = document.getElementById("history-search");
  const sortEl = document.getElementById("history-sort");
  const countEl = document.getElementById("history-count");
  const moreBtn = document.getElementById("btn-more");
  const countAll = document.getElementById("count-all");
  const countMold = document.getElementById("count-mold");
  const countClean = document.getElementById("count-clean");

  const state = {
    filter: "all",
    sort: "newest",
    query: "",
    limit: 8,
    selectedId: null,
  };

  const initialQuery = new URLSearchParams(window.location.search).get("q");
  if (initialQuery) {
    state.query = initialQuery;
    searchEl.value = initialQuery;
  }

  function svg(name, size = 20) {
    return `<svg class="icon" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><use href="#i-${name}"></use></svg>`;
  }

  function allHistory() {
    return store.getHistory().filter((row) => row && row.id);
  }

  function sortedHistory() {
    const rows = allHistory().slice();
    rows.sort((a, b) => {
      const diff = new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
      return state.sort === "oldest" ? -diff : diff;
    });
    return rows;
  }

  function matches(row, query) {
    if (!query) return true;
    const meta = statusMeta(row.status);
    const haystack = [
      row.location || "",
      meta.label,
      Array.isArray(row.species) ? row.species.join(" ") : "",
      fmt.date(row.createdAt),
    ].join(" ").toLowerCase();
    return haystack.includes(query);
  }

  function filteredHistory() {
    const rows = sortedHistory();
    return rows.filter((row) => {
      const isMold = row.status === "mold_detected";
      if (state.filter === "mold" && !isMold) return false;
      if (state.filter === "clean" && isMold) return false;
      return matches(row, state.query);
    });
  }

  function thumbMarkup(row, cls) {
    if (row.thumb || row.annotatedThumb || row.originalThumb) {
      const src = row.thumb || row.annotatedThumb || row.originalThumb;
      return `<img src="${src}" alt="Foto pemeriksaan ${escapeHtml(row.location || "tanpa lokasi")}" loading="lazy" />`;
    }
    return `<span class="thumb-fallback">${svg("mushroom", 24)}</span>`;
  }

  function rowMarkup(row) {
    const meta = statusMeta(row.status);
    const active = row.id === state.selectedId;
    return `
      <a class="history-row${active ? " is-selected" : ""}" href="/hasil?id=${encodeURIComponent(row.id)}" data-id="${escapeHtml(row.id)}">
        <span class="history-row__thumb">${thumbMarkup(row)}</span>
        <span class="history-row__main">
          <span class="history-row__date">${escapeHtml(fmt.dateTime(row.createdAt))}</span>
          <span class="history-row__place">${escapeHtml(row.location || "Tanpa lokasi")}</span>
          <span class="history-row__meta">${row.boxes ? `${row.boxes} area ditandai` : "Tidak ada area ditandai"}${row.species && row.species.length ? ` · ${escapeHtml(row.species[0])}` : ""}</span>
        </span>
        <span class="status-badge status-badge--${meta.tone}">${svg(meta.icon, 13)} ${escapeHtml(meta.short)}</span>
        <span class="history-row__chevron" aria-hidden="true">${svg("chevron-right", 18)}</span>
      </a>`;
  }

  function renderPreview() {
    if (!previewEl) return;
    const row = allHistory().find((item) => item.id === state.selectedId);

    if (!row) {
      previewEl.innerHTML = `
        <div class="empty-state empty-state--compact">
          <span class="empty-state__icon">${svg("history", 24)}</span>
          <p>Pilih pemeriksaan untuk melihat pratinjau.</p>
        </div>`;
      return;
    }

    const meta = statusMeta(row.status);
    const species = Array.isArray(row.species) ? row.species : [];
    previewEl.innerHTML = `
      <div class="preview-media">
        ${thumbMarkup(row, "preview-media__img")}
        <span class="status-badge status-badge--${meta.tone}">${svg(meta.icon, 13)} ${escapeHtml(meta.short)}</span>
      </div>
      <div class="preview-body">
        <p class="eyebrow">Pemeriksaan</p>
        <h2 class="preview-title">${escapeHtml(row.location || "Tanpa lokasi")}</h2>
        <p class="muted-small">${escapeHtml(fmt.dateTime(row.createdAt))}</p>
        <dl class="preview-meta">
          <div><dt>Area ditandai</dt><dd>${row.boxes || 0}</dd></div>
          <div><dt>Keyakinan tertinggi</dt><dd>${typeof row.topConfidence === "number" ? `${(row.topConfidence * 100).toFixed(1)}%` : "—"}</dd></div>
          <div><dt>Model</dt><dd>${row.models && row.models.yolo ? (row.models.mobile ? "YOLO + MobileNetV2" : "YOLO") : "Tidak tersedia"}</dd></div>
        </dl>
        ${species.length ? `<div class="tag-row">${species.map((name) => `<span class="badge badge--soft">${escapeHtml(name)}</span>`).join("")}</div>` : ""}
        <div class="preview-actions">
          <a class="btn btn--primary btn--sm" href="/hasil?id=${encodeURIComponent(row.id)}">Lihat Detail</a>
          <button class="btn btn--ghost btn--danger-text btn--sm" type="button" id="preview-delete">${svg("trash", 15)} Hapus</button>
        </div>
        <p class="privacy-note">${svg("lock", 14)} Data ini hanya ada di perangkat Anda.</p>
      </div>`;

    const deleteBtn = document.getElementById("preview-delete");
    if (deleteBtn) {
      deleteBtn.addEventListener("click", async () => {
        const ok = await confirmDialog({
          title: "Hapus pemeriksaan?",
          message: "Pemeriksaan ini akan dihapus dari riwayat perangkat dan tidak dapat dikembalikan.",
          confirmLabel: "Hapus",
          danger: true,
        });
        if (!ok) return;
        store.removeHistory(row.id);
        state.selectedId = null;
        toast("Pemeriksaan dihapus dari riwayat.", "success");
        renderNotifications();
        render();
      });
    }
  }

  function render() {
    const all = sortedHistory();
    const rows = filteredHistory();

    countAll.textContent = String(all.length);
    countMold.textContent = String(all.filter((row) => row.status === "mold_detected").length);
    countClean.textContent = String(all.filter((row) => row.status !== "mold_detected").length);

    if (state.selectedId && !rows.some((row) => row.id === state.selectedId)) {
      state.selectedId = null;
    }
    if (!state.selectedId && rows.length && window.matchMedia("(min-width: 1024px)").matches) {
      state.selectedId = rows[0].id;
    }

    if (!all.length) {
      listEl.innerHTML = `
        <div class="empty-state empty-state--page">
          <span class="empty-state__icon">${svg("history", 28)}</span>
          <h3 class="empty-state__title">Riwayat deteksi masih kosong</h3>
          <p class="empty-state__text">Hasil pemeriksaan yang Anda simpan akan muncul di sini.</p>
          <a class="btn btn--primary" href="/deteksi">Mulai Deteksi</a>
        </div>`;
      countEl.textContent = "Belum ada pemeriksaan tersimpan.";
      moreBtn.hidden = true;
      renderPreview();
      return;
    }

    if (!rows.length) {
      listEl.innerHTML = `
        <div class="empty-state empty-state--compact">
          <span class="empty-state__icon">${svg("search", 24)}</span>
          <h3 class="empty-state__title">Tidak ada hasil yang cocok</h3>
          <p class="empty-state__text">Coba kata kunci lain atau ubah filter status.</p>
          <button class="btn btn--secondary btn--sm" type="button" id="btn-reset-filter">Reset filter</button>
        </div>`;
      const resetBtn = document.getElementById("btn-reset-filter");
      if (resetBtn) {
        resetBtn.addEventListener("click", () => {
          state.filter = "all";
          state.query = "";
          searchEl.value = "";
          document.querySelectorAll("[data-filter]").forEach((btn) => {
            const active = btn.dataset.filter === "all";
            btn.classList.toggle("is-active", active);
            btn.setAttribute("aria-pressed", String(active));
          });
          render();
        });
      }
      countEl.textContent = `0 dari ${all.length} pemeriksaan.`;
      moreBtn.hidden = true;
      renderPreview();
      return;
    }

    const visible = rows.slice(0, state.limit);
    listEl.innerHTML = visible.map(rowMarkup).join("");

    listEl.querySelectorAll(".history-row").forEach((link) => {
      link.addEventListener("click", (event) => {
        if (!window.matchMedia("(min-width: 1024px)").matches) return;
        event.preventDefault();
        state.selectedId = link.dataset.id;
        listEl.querySelectorAll(".history-row").forEach((row) => row.classList.remove("is-selected"));
        link.classList.add("is-selected");
        renderPreview();
      });
    });

    countEl.textContent = `Menampilkan ${visible.length} dari ${rows.length} pemeriksaan.`;
    moreBtn.hidden = visible.length >= rows.length;
    renderPreview();
  }

  // ── Kontrol ─────────────────────────────────────────────────────────────────
  searchEl.addEventListener("input", () => {
    state.query = searchEl.value.trim().toLowerCase();
    state.limit = 8;
    render();
  });

  sortEl.addEventListener("change", () => {
    state.sort = sortEl.value;
    state.limit = 8;
    render();
  });

  document.querySelectorAll("[data-filter]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.filter = btn.dataset.filter;
      state.limit = 8;
      document.querySelectorAll("[data-filter]").forEach((other) => {
        const active = other === btn;
        other.classList.toggle("is-active", active);
        other.setAttribute("aria-pressed", String(active));
      });
      render();
    });
  });

  moreBtn.addEventListener("click", () => {
    state.limit += 8;
    render();
  });

  render();
});