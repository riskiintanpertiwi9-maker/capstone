"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const { store, fmt, statusMeta, escapeHtml, icon } = window.MG;

  // ── Sapaan ────────────────────────────────────────────────────────────────
  const settings = store.getSettings();
  const tipsCard = document.getElementById("tips-card");
  if (tipsCard && settings.notifyTips === false) tipsCard.hidden = true;

  const profile = store.getProfile();
  const nameEl = document.getElementById("greeting-name");
  if (nameEl && profile.name) nameEl.textContent = profile.name;

  // ── Ringkasan ─────────────────────────────────────────────────────────────
  const history = store.getHistory();
  const moldCount = history.filter((row) => row.status === "mold_detected").length;
  const cleanCount = history.filter((row) => row.status !== "mold_detected").length;

  document.getElementById("summary-total").textContent = String(history.length);
  document.getElementById("summary-mold").textContent = String(moldCount);
  document.getElementById("summary-clean").textContent = String(cleanCount);

  const lastChip = document.getElementById("summary-last");
  if (history.length) {
    lastChip.hidden = false;
    lastChip.textContent = `Terakhir ${fmt.relative(history[0].createdAt)}`;
  }

  // ── Hasil terbaru ─────────────────────────────────────────────────────────
  const latest = document.getElementById("latest-list");
  if (latest) {
    if (!history.length) {
      latest.innerHTML = `
        <div class="empty-state empty-state--compact">
          <span class="empty-state__icon">${icon('scan', 24)}</span>
          <p>Belum ada pemeriksaan</p>
          <a class="btn btn--primary btn--sm" href="/deteksi">Mulai Deteksi Pertama</a>
        </div>`;
    } else {
      latest.innerHTML = history.slice(0, 2).map((row) => {
        const meta = statusMeta(row.status);
        const thumb = row.thumb
          ? `<img src="${row.thumb}" alt="Foto pemeriksaan ${escapeHtml(row.location || "tanpa lokasi")}" loading="lazy" />`
          : `<span class="thumb-fallback">${icon('mushroom', 26)}</span>`;
        return `
          <a class="latest-item" href="/hasil?id=${encodeURIComponent(row.id)}">
            <span class="latest-item__thumb">${thumb}</span>
            <span class="latest-item__body">
              <span class="latest-item__date">${escapeHtml(fmt.dateTime(row.createdAt))}</span>
              <span class="latest-item__place">${escapeHtml(row.location || "Tanpa lokasi")}</span>
              <span class="status-badge status-badge--${meta.tone}">${icon(meta.icon, 13)} ${escapeHtml(meta.label)}</span>
            </span>
            <span class="latest-item__go" aria-hidden="true">${icon('chevron-right', 18)}</span>
          </a>`;
      }).join("");
    }
  }

  // ── Pengingat ─────────────────────────────────────────────────────────────
  const reminderBox = document.getElementById("reminder-list");
  if (reminderBox) {
    const reminders = store.getReminders()
      .filter((rem) => rem.active !== false)
      .sort((a, b) => String(a.nextDate).localeCompare(String(b.nextDate)))
      .slice(0, 2);
    if (!reminders.length) {
      reminderBox.innerHTML = `
        <div class="empty-state empty-state--compact">
          <span class="empty-state__icon">${icon('bell', 24)}</span>
          <p>Belum ada pengingat aktif</p>
          <a class="btn btn--secondary btn--sm" href="/pengingat">Tambah Pengingat</a>
        </div>`;
    } else {
      reminderBox.innerHTML = reminders.map((rem) => {
        const due = new Date(rem.nextDate);
        const days = Math.ceil((due - new Date()) / 86400000);
        const soon = days <= 3;
        return `
          <div class="reminder-mini">
            <span class="tile tile--mint">${icon(rem.icon || 'calendar', 18)}</span>
            <span class="reminder-mini__body">
              <span class="reminder-mini__title">${escapeHtml(rem.name)}</span>
              <span class="reminder-mini__meta">${escapeHtml(fmt.date(rem.nextDate))}${soon ? " · segera" : ""}</span>
            </span>
            <span class="toggle toggle--static ${rem.active !== false ? "is-on" : ""}" aria-hidden="true"></span>
          </div>`;
      }).join("");
    }
  }

  // ── Statistik ─────────────────────────────────────────────────────────────
  const rangeSelect = document.getElementById("stats-range");
  const chart = document.getElementById("stats-chart");
  const note = document.getElementById("stats-note");
  const legend = document.getElementById("stats-legend");

  function dayKey(date) {
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
  }

  function buildSeries(days) {
    const buckets = [];
    const now = new Date();
    now.setHours(0, 0, 0, 0);
    const weekly = days > 30;
    const step = weekly ? 7 : 1;
    const count = Math.ceil(days / step);
    for (let i = count - 1; i >= 0; i -= 1) {
      const start = new Date(now);
      start.setDate(start.getDate() - i * step);
      buckets.push({ start, end: new Date(start.getTime() + step * 86400000), total: 0, mold: 0 });
    }
    history.forEach((row) => {
      const created = new Date(row.createdAt);
      if (isNaN(created)) return;
      const bucket = buckets.find((b) => created >= b.start && created < b.end);
      if (!bucket) return;
      bucket.total += 1;
      if (row.status === "mold_detected") bucket.mold += 1;
    });
    return { buckets, weekly };
  }

  function renderChart(days) {
    const { buckets, weekly } = buildSeries(days);
    const max = Math.max(1, ...buckets.map((b) => b.total));
    const label = (b) => weekly
      ? `${fmt.date(b.start)}`
      : `${b.start.getDate()}/${b.start.getMonth() + 1}`;

    chart.innerHTML = buckets.map((bucket, index) => {
      const every = Math.ceil(buckets.length / 10);
      const showLabel = buckets.length <= 14 || index % every === 0 || index === buckets.length - 1;
      return `
      <div class="chart-col">
        <div class="chart-col__bars">
          <span class="chart-bar chart-bar--total" style="height:${(bucket.total / max) * 100}%" title="${bucket.total} pemeriksaan"></span>
          <span class="chart-bar chart-bar--mold" style="height:${(bucket.mold / max) * 100}%" title="${bucket.mold} indikasi"></span>
        </div>
        <span class="chart-col__label">${showLabel ? escapeHtml(label(bucket)) : ""}</span>
      </div>`;
    }).join("");

    const totalInRange = buckets.reduce((sum, b) => sum + b.total, 0);
    legend.hidden = false;
    if (!totalInRange) {
      note.hidden = false;
      note.textContent = days > 30
        ? "Belum ada pemeriksaan dalam 3 bulan terakhir."
        : `Belum ada pemeriksaan dalam ${days} hari terakhir.`;
    } else {
      note.hidden = true;
    }
    chart.setAttribute("aria-label", `Grafik pemeriksaan: total ${totalInRange} dalam rentang ini.`);
  }

  if (rangeSelect && chart) {
    rangeSelect.addEventListener("change", () => renderChart(Number(rangeSelect.value)));
    renderChart(7);
  }
});