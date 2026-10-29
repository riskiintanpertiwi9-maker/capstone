/**
 * MoldGuard — laporan.js
 * Menghitung ringkasan laporan dari riwayat lokal. Tidak ada angka contoh.
 */
"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const { store, fmt, statusMeta, escapeHtml, toast } = window.MG;

  const fromEl = document.getElementById("range-from");
  const toEl = document.getElementById("range-to");
  const applyBtn = document.getElementById("btn-apply-range");
  const printBtn = document.getElementById("btn-print-report");
  const emptyEl = document.getElementById("report-empty");
  const bodyEl = document.getElementById("report-body");
  const presetBtns = Array.from(document.querySelectorAll("[data-days]"));

  const DAY = 86400000;

  function startOfDay(date) {
    const d = new Date(date);
    d.setHours(0, 0, 0, 0);
    return d;
  }

  function endOfDay(date) {
    const d = new Date(date);
    d.setHours(23, 59, 59, 999);
    return d;
  }

  function isoDay(date) {
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
  }

  function parseDay(value) {
    if (!value) return null;
    const [y, m, d] = value.split("-").map(Number);
    if (!y || !m || !d) return null;
    const date = new Date(y, m - 1, d);
    return isNaN(date) ? null : date;
  }

  function setPreset(days) {
    const today = startOfDay(new Date());
    const from = new Date(today.getTime() - (days - 1) * DAY);
    fromEl.value = isoDay(from);
    toEl.value = isoDay(today);
    presetBtns.forEach((btn) => {
      const active = Number(btn.dataset.days) === days;
      btn.classList.toggle("is-active", active);
      btn.setAttribute("aria-pressed", String(active));
    });
    render();
  }

  function getRange() {
    let from = parseDay(fromEl.value);
    let to = parseDay(toEl.value);
    if (!from || !to) return null;
    if (from > to) {
      const tmp = from;
      from = to;
      to = tmp;
      fromEl.value = isoDay(from);
      toEl.value = isoDay(to);
    }
    return { start: startOfDay(from), end: endOfDay(to) };
  }

  function inRange(rows, range) {
    return rows.filter((row) => {
      const t = new Date(row.createdAt).getTime();
      return !isNaN(t) && t >= range.start.getTime() && t <= range.end.getTime();
    });
  }

  function svg(name, size = 18) {
    return `<svg class="icon" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><use href="#i-${name}"></use></svg>`;
  }

  // ── Chart ───────────────────────────────────────────────────────────────────
  function buildBuckets(rows, range) {
    const totalDays = Math.max(1, Math.round((range.end - range.start) / DAY));
    let mode = "day";
    if (totalDays > 200) mode = "month";
    else if (totalDays > 31) mode = "week";

    const buckets = [];
    if (mode === "month") {
      const cursor = new Date(range.start.getFullYear(), range.start.getMonth(), 1);
      const last = new Date(range.end.getFullYear(), range.end.getMonth(), 1);
      while (cursor <= last) {
        const start = new Date(cursor);
        const end = new Date(cursor.getFullYear(), cursor.getMonth() + 1, 1);
        buckets.push({ start, end, total: 0, mold: 0, label: new Intl.DateTimeFormat("id-ID", { month: "short" }).format(cursor) });
        cursor.setMonth(cursor.getMonth() + 1);
      }
    } else {
      const step = mode === "week" ? 7 : 1;
      let cursor = new Date(range.start);
      while (cursor <= range.end) {
        const start = new Date(cursor);
        const end = new Date(start.getTime() + step * DAY);
        buckets.push({ start, end, total: 0, mold: 0, label: `${start.getDate()}/${start.getMonth() + 1}` });
        cursor = end;
      }
    }

    rows.forEach((row) => {
      const time = new Date(row.createdAt).getTime();
      const bucket = buckets.find((b) => time >= b.start.getTime() && time < b.end.getTime());
      if (!bucket) return;
      bucket.total += 1;
      if (row.status === "mold_detected") bucket.mold += 1;
    });

    return { buckets, mode };
  }

  function renderTrend(rows, range) {
    const chart = document.getElementById("trend-chart");
    const note = document.getElementById("trend-note");
    const { buckets, mode } = buildBuckets(rows, range);
    const max = Math.max(1, ...buckets.map((b) => b.total));

    chart.innerHTML = buckets.map((bucket, index) => {
      const every = Math.ceil(buckets.length / 10);
      const showLabel = buckets.length <= 14 || index % every === 0 || index === buckets.length - 1;
      const totalBar = bucket.total
        ? `<span class="chart-bar chart-bar--total" style="height:${(bucket.total / max) * 100}%" title="${bucket.total} pemeriksaan"></span>`
        : "";
      const moldBar = bucket.mold
        ? `<span class="chart-bar chart-bar--mold" style="height:${(bucket.mold / max) * 100}%" title="${bucket.mold} indikasi"></span>`
        : "";
      return `
      <div class="chart-col">
        <div class="chart-col__bars">${totalBar}${moldBar}</div>
        <span class="chart-col__label">${showLabel ? escapeHtml(bucket.label) : ""}</span>
      </div>`;
    }).join("");

    document.getElementById("trend-range").textContent =
      `${fmt.date(range.start)} – ${fmt.date(range.end)} · ${mode === "day" ? "per hari" : mode === "week" ? "per minggu" : "per bulan"}`;

    chart.setAttribute("aria-label", `Grafik tren: ${rows.length} pemeriksaan dalam rentang ini.`);

    note.hidden = rows.length > 0;
    if (!rows.length) note.textContent = "Belum ada pemeriksaan dalam rentang tanggal ini.";
  }

  // ── Donut ───────────────────────────────────────────────────────────────────
  function renderDonut(rows) {
    const donut = document.getElementById("report-donut");
    const legend = document.getElementById("donut-legend");
    const mold = rows.filter((row) => row.status === "mold_detected").length;
    const clean = rows.filter((row) => row.status === "no_mold").length;
    const unavailable = rows.filter((row) => row.status === "model_unavailable").length;
    const total = rows.length;

    document.getElementById("donut-total").textContent = String(total);

    const segments = [];
    if (total) {
      let acc = 0;
      const push = (value, color) => {
        if (!value) return;
        const start = (acc / total) * 100;
        acc += value;
        const end = (acc / total) * 100;
        segments.push(`${color} ${start.toFixed(2)}% ${end.toFixed(2)}%`);
      };
      push(mold, "var(--mg-danger)");
      push(clean, "var(--mg-success)");
      push(unavailable, "var(--mg-warning)");
    }
    donut.style.background = total
      ? `conic-gradient(${segments.join(", ")})`
      : "conic-gradient(var(--mg-border) 0 100%)";
    donut.setAttribute("aria-label", total
      ? `Distribusi: ${mold} terindikasi, ${clean} tanpa indikasi${unavailable ? `, ${unavailable} model tidak tersedia` : ""}.`
      : "Belum ada data pada rentang ini.");

    const rowsLegend = [
      { label: "Terindikasi", value: mold, tone: "danger" },
      { label: "Tanpa indikasi", value: clean, tone: "success" },
    ];
    if (unavailable) rowsLegend.push({ label: "Model tidak tersedia", value: unavailable, tone: "warning" });

    legend.innerHTML = rowsLegend.map((row) => `
      <li class="donut-legend__item">
        <span class="legend-dot legend-dot--${row.tone}"></span>
        <span class="donut-legend__label">${escapeHtml(row.label)}</span>
        <strong>${row.value}</strong>
        <span class="muted-small">${total ? `${((row.value / total) * 100).toFixed(0)}%` : "—"}</span>
      </li>`).join("");
  }

  // ── Per ruangan ─────────────────────────────────────────────────────────────
  function renderRooms(rows) {
    const container = document.getElementById("room-list");
    if (!rows.length) {
      container.innerHTML = `<p class="muted-small">Belum ada data lokasi pada rentang ini.</p>`;
      return;
    }
    const groups = new Map();
    rows.forEach((row) => {
      const name = (row.location || "").trim() || "Tanpa lokasi";
      if (!groups.has(name)) groups.set(name, { name, total: 0, mold: 0, last: row.createdAt });
      const group = groups.get(name);
      group.total += 1;
      if (row.status === "mold_detected") group.mold += 1;
      if (new Date(row.createdAt) > new Date(group.last)) group.last = row.createdAt;
    });

    const list = Array.from(groups.values())
      .sort((a, b) => b.total - a.total || a.name.localeCompare(b.name))
      .slice(0, 6);

    container.innerHTML = list.map((group) => {
      const ratio = group.total ? (group.mold / group.total) * 100 : 0;
      return `
        <div class="room-row">
          <span class="tile tile--mint">${svg("map-pin", 17)}</span>
          <div class="room-row__main">
            <div class="room-row__head">
              <strong>${escapeHtml(group.name)}</strong>
              <span class="muted-small">Terakhir ${escapeHtml(fmt.date(group.last))}</span>
            </div>
            <div class="room-row__bar" aria-hidden="true"><span style="width:${ratio.toFixed(1)}%"></span></div>
            <p class="muted-small">${group.total} pemeriksaan · ${group.mold} terindikasi${group.mold ? ` (${ratio.toFixed(0)}%)` : ""}</p>
          </div>
        </div>`;
    }).join("");
  }

  // ── Laporan terbaru ─────────────────────────────────────────────────────────
  function renderRecent(rows) {
    const container = document.getElementById("report-recent");
    if (!rows.length) {
      container.innerHTML = `<p class="muted-small">Belum ada pemeriksaan pada rentang ini.</p>`;
      return;
    }
    container.innerHTML = rows.slice(0, 6).map((row) => {
      const meta = statusMeta(row.status);
      return `
        <a class="recent-row" href="/hasil?id=${encodeURIComponent(row.id)}">
          <span class="status-dot status-dot--${meta.tone}" aria-hidden="true"></span>
          <span class="recent-row__main">
            <strong>${escapeHtml(row.location || "Tanpa lokasi")}</strong>
            <span class="muted-small">${escapeHtml(fmt.dateTime(row.createdAt))} · ${row.boxes || 0} area</span>
          </span>
          <span class="status-badge status-badge--${meta.tone}">${escapeHtml(meta.short)}</span>
          <span aria-hidden="true">${svg("chevron-right", 17)}</span>
        </a>`;
    }).join("");
  }

  // ── Render utama ────────────────────────────────────────────────────────────
  function render() {
    const range = getRange();
    if (!range) return;

    const history = store.getHistory();
    const rows = inRange(history, range).sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));

    const hasAny = history.length > 0;
    emptyEl.hidden = hasAny;
    bodyEl.hidden = !hasAny;
    if (printBtn) {
      printBtn.disabled = !hasAny;
      printBtn.setAttribute("aria-disabled", String(!hasAny));
    }
    if (!hasAny) return;

    const mold = rows.filter((row) => row.status === "mold_detected").length;
    const clean = rows.filter((row) => row.status === "no_mold").length;
    const rooms = new Set(rows.map((row) => (row.location || "").trim().toLowerCase()).filter(Boolean));

    document.getElementById("metric-total").textContent = String(rows.length);
    document.getElementById("metric-mold").textContent = String(mold);
    document.getElementById("metric-clean").textContent = String(clean);
    document.getElementById("metric-rooms").textContent = String(rooms.size);

    renderTrend(rows, range);
    renderDonut(rows);
    renderRooms(rows);
    renderRecent(rows);
  }

  // ── Kontrol ─────────────────────────────────────────────────────────────────
  presetBtns.forEach((btn) => {
    btn.addEventListener("click", () => setPreset(Number(btn.dataset.days)));
  });

  if (applyBtn) {
    applyBtn.addEventListener("click", () => {
      if (!getRange()) {
        toast("Isi tanggal mulai dan tanggal akhir terlebih dahulu.", "error");
        return;
      }
      presetBtns.forEach((btn) => {
        btn.classList.remove("is-active");
        btn.setAttribute("aria-pressed", "false");
      });
      render();
    });
  }

  [fromEl, toEl].forEach((input) => {
    input.addEventListener("change", () => {
      presetBtns.forEach((btn) => {
        btn.classList.remove("is-active");
        btn.setAttribute("aria-pressed", "false");
      });
      render();
    });
  });

  if (printBtn) {
    printBtn.addEventListener("click", () => {
      if (printBtn.disabled) return;
      toast("Dialog cetak dibuka. Pilih “Simpan sebagai PDF” untuk menyimpan laporan.", "info");
      window.setTimeout(() => window.print(), 150);
    });
  }

  setPreset(30);
});