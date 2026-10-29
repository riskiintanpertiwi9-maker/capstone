/**
 * MoldGuard — reminders.js
 * CRUD pengingat perawatan rumah di localStorage, kalender, dan agenda.
 */
"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const { store, fmt, escapeHtml, toast, confirmDialog, openModal, closeModal, uid } = window.MG;

  const DAY = 86400000;
  const FREQ_LABEL = {
    daily: "Setiap hari",
    weekly: "Setiap minggu",
    biweekly: "Setiap 2 minggu",
    monthly: "Setiap bulan",
    quarterly: "Setiap 3 bulan",
    semiannual: "Setiap 6 bulan",
    yearly: "Setiap tahun",
  };
  const ICON_LABEL = {
    broom: "Kebersihan",
    droplet: "Kelembapan",
    wind: "Ventilasi",
    filter: "Perawatan alat",
    home: "Area rumah",
    spray: "Pembersih",
    bell: "Lainnya",
  };
  const TONE = {
    broom: "mint", droplet: "blue", wind: "mint", filter: "amber",
    home: "rose", spray: "blue", bell: "neutral",
  };
  const SUGGESTIONS = [
    { name: "Bersihkan kamar mandi", note: "Gosok sudut shower dan sambungan keramik, lalu keringkan.", frequency: "weekly", icon: "broom" },
    { name: "Periksa area lembap", note: "Cek bawah wastafel, belakang lemari, dan sekitar jendela.", frequency: "monthly", icon: "droplet" },
    { name: "Buka jendela pagi", note: "Biarkan udara berganti selama 10–15 menit setiap pagi.", frequency: "daily", icon: "wind" },
    { name: "Bersihkan filter AC", note: "Bersihkan atau ganti filter sesuai panduan perangkat.", frequency: "quarterly", icon: "filter" },
    { name: "Periksa talang air", note: "Bersihkan daun dan kotoran agar air tidak merembes ke dinding.", frequency: "semiannual", icon: "home" },
    { name: "Cuci tirai dan keset", note: "Cuci dan jemur di luar ruangan agar tidak menambah kelembapan.", frequency: "monthly", icon: "spray" },
  ];

  const listEl = document.getElementById("reminder-list");
  const countEl = document.getElementById("reminder-count");
  const suggestionEl = document.getElementById("suggestion-grid");
  const calGrid = document.getElementById("calendar-grid");
  const calTitle = document.getElementById("cal-title");
  const calNote = document.getElementById("cal-note");
  const upcomingEl = document.getElementById("upcoming-list");
  const addBtn = document.getElementById("btn-add-reminder");

  const state = {
    calendar: new Date(new Date().getFullYear(), new Date().getMonth(), 1),
    selectedDay: null,
  };

  function svg(name, size = 18) {
    return `<svg class="icon" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><use href="#i-${name}"></use></svg>`;
  }

  function startOfDay(date) {
    const d = new Date(date);
    d.setHours(0, 0, 0, 0);
    return d;
  }

  function isoDay(date) {
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
  }

  function parseDay(value) {
    if (!value) return null;
    const [y, m, d] = String(value).split("-").map(Number);
    if (!y || !m || !d) return null;
    const date = new Date(y, m - 1, d);
    return isNaN(date) ? null : startOfDay(date);
  }

  function addMonths(date, months) {
    const day = date.getDate();
    const next = new Date(date);
    next.setDate(1);
    next.setMonth(next.getMonth() + months);
    const dim = new Date(next.getFullYear(), next.getMonth() + 1, 0).getDate();
    next.setDate(Math.min(day, dim));
    return next;
  }

  function addFrequency(baseDate, frequency) {
    const d = new Date(baseDate);
    switch (frequency) {
      case "daily": d.setDate(d.getDate() + 1); break;
      case "weekly": d.setDate(d.getDate() + 7); break;
      case "biweekly": d.setDate(d.getDate() + 14); break;
      case "monthly": return addMonths(d, 1);
      case "quarterly": return addMonths(d, 3);
      case "semiannual": return addMonths(d, 6);
      case "yearly": return addMonths(d, 12);
      default: d.setDate(d.getDate() + 7);
    }
    return d;
  }

  function dueMeta(dateStr) {
    const due = parseDay(dateStr);
    if (!due) return { text: "Tanggal tidak valid", tone: "warning" };
    const today = startOfDay(new Date());
    const diff = Math.round((due - today) / DAY);
    if (diff < 0) return { text: `Terlambat ${Math.abs(diff)} hari`, tone: "danger" };
    if (diff === 0) return { text: "Hari ini", tone: "warning" };
    if (diff === 1) return { text: "Besok", tone: "info" };
    if (diff <= 7) return { text: `Dalam ${diff} hari`, tone: "info" };
    return { text: `Dalam ${diff} hari`, tone: "neutral" };
  }

  function load() {
    return store.getReminders().filter((rem) => rem && rem.name);
  }

  function persist(list) {
    store.saveReminders(list);
    if (window.MG.renderNotifications) window.MG.renderNotifications();
    paint();
  }

  // ── Daftar ──────────────────────────────────────────────────────────────────
  function reminderCard(rem) {
    const tone = TONE[rem.icon] || "mint";
    const due = dueMeta(rem.nextDate);
    const active = rem.active !== false;
    return `
      <article class="reminder-card${active ? "" : " is-inactive"}" data-id="${escapeHtml(rem.id)}">
        <span class="tile tile--${tone}">${svg(rem.icon || "bell", 19)}</span>
        <div class="reminder-card__body">
          <div class="reminder-card__head">
            <div>
              <h3 class="reminder-card__title">${escapeHtml(rem.name)}</h3>
              <p class="reminder-card__note">${escapeHtml(rem.note || "Tidak ada catatan tambahan.")}</p>
            </div>
            <button class="toggle${active ? " is-on" : ""}" type="button" role="switch"
              aria-checked="${active}" aria-label="${active ? "Nonaktifkan" : "Aktifkan"} pengingat ${escapeHtml(rem.name)}"
              data-act="toggle">
              <span></span>
            </button>
          </div>
          <div class="reminder-card__meta">
            <span class="badge badge--neutral">${svg("refresh", 13)} ${escapeHtml(FREQ_LABEL[rem.frequency] || "Kustom")}</span>
            <span class="chip chip--neutral">${svg("calendar", 13)} ${escapeHtml(fmt.date(rem.nextDate))}</span>
            <span class="chip chip--${due.tone}">${escapeHtml(due.text)}</span>
          </div>
          <div class="reminder-card__actions">
            <button class="btn btn--ghost btn--sm" type="button" data-act="done">${svg("check", 15)} Tandai selesai</button>
            <button class="btn btn--ghost btn--sm" type="button" data-act="edit">${svg("pencil", 15)} Edit</button>
            <button class="btn btn--ghost btn--sm btn--danger-text" type="button" data-act="delete">${svg("trash", 15)} Hapus</button>
          </div>
        </div>
      </article>`;
  }

  function paintList() {
    const reminders = load().sort((a, b) => String(a.nextDate).localeCompare(String(b.nextDate)));
    const activeCount = reminders.filter((rem) => rem.active !== false).length;

    countEl.textContent = reminders.length
      ? `${activeCount} aktif dari ${reminders.length}`
      : "Belum ada";

    if (!reminders.length) {
      listEl.innerHTML = `
        <div class="empty-state empty-state--page">
          <span class="empty-state__icon">${svg("bell", 28)}</span>
          <h3 class="empty-state__title">Belum ada pengingat</h3>
          <p class="empty-state__text">Tambahkan agenda perawatan pertama, atau pilih template di bawah. Pengingat tidak dibuat otomatis.</p>
          <button class="btn btn--primary" type="button" id="empty-add-reminder">${svg("plus", 16)} Tambah Pengingat</button>
        </div>`;
      const emptyBtn = document.getElementById("empty-add-reminder");
      if (emptyBtn) emptyBtn.addEventListener("click", () => openForm(null));
      return;
    }

    listEl.innerHTML = reminders.map(reminderCard).join("");
  }

  // ── Kalender ────────────────────────────────────────────────────────────────
  function paintCalendar() {
    const activeReminders = load().filter((rem) => rem.active !== false);
    const byDay = new Map();
    activeReminders.forEach((rem) => {
      if (!rem.nextDate) return;
      if (!byDay.has(rem.nextDate)) byDay.set(rem.nextDate, []);
      byDay.get(rem.nextDate).push(rem);
    });

    const year = state.calendar.getFullYear();
    const month = state.calendar.getMonth();
    const today = startOfDay(new Date());
    const todayIso = isoDay(today);

    calTitle.textContent = new Intl.DateTimeFormat("id-ID", { month: "long", year: "numeric" }).format(state.calendar);

    const firstWeekday = (new Date(year, month, 1).getDay() + 6) % 7;
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    let html = "";
    for (let i = 0; i < firstWeekday; i += 1) {
      html += '<span class="cal-day cal-day--empty" aria-hidden="true"></span>';
    }
    for (let day = 1; day <= daysInMonth; day += 1) {
      const date = new Date(year, month, day);
      const dateIso = isoDay(date);
      const events = byDay.get(dateIso) || [];
      const isToday = dateIso === todayIso;
      const selected = state.selectedDay === dateIso;
      const classes = ["cal-day"];
      if (isToday) classes.push("is-today");
      if (events.length) classes.push("has-event");
      if (selected) classes.push("is-selected");
      const label = `${day} ${new Intl.DateTimeFormat("id-ID", { month: "long", year: "numeric" }).format(date)}${events.length ? `, ${events.length} pengingat: ${events.map((e) => e.name).join(", ")}` : ""}`;
      html += `
        <button class="${classes.join(" ")}" type="button" data-day="${dateIso}"
          aria-label="${escapeHtml(label)}"${isToday ? ' aria-current="date"' : ""}>
          <span>${day}</span>${events.length ? '<i class="cal-dot" aria-hidden="true"></i>' : ""}
        </button>`;
    }
    calGrid.innerHTML = html;

    calGrid.querySelectorAll("[data-day]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const dateIso = btn.dataset.day;
        const events = byDay.get(dateIso) || [];
        if (!events.length) {
          state.selectedDay = null;
          calNote.innerHTML = `${svg("calendar", 14)} <span>Tidak ada pengingat pada tanggal ini.</span>`;
        } else {
          state.selectedDay = dateIso;
          calNote.innerHTML = `${svg("bell", 14)} <span>${escapeHtml(fmt.date(dateIso))}: ${events.map((e) => escapeHtml(e.name)).join(", ")}</span>`;
        }
        calGrid.querySelectorAll("[data-day]").forEach((cell) => cell.classList.toggle("is-selected", cell.dataset.day === state.selectedDay));
      });
    });
  }

  // ── Agenda ──────────────────────────────────────────────────────────────────
  function paintUpcoming() {
    const active = load()
      .filter((rem) => rem.active !== false)
      .sort((a, b) => String(a.nextDate).localeCompare(String(b.nextDate)))
      .slice(0, 6);

    if (!active.length) {
      upcomingEl.innerHTML = `<p class="muted-small">Belum ada pengingat aktif.</p>`;
      return;
    }

    upcomingEl.innerHTML = active.map((rem) => {
      const due = dueMeta(rem.nextDate);
      return `
        <div class="timeline-item">
          <span class="timeline-dot timeline-dot--${due.tone}" aria-hidden="true"></span>
          <div class="timeline-item__body">
            <strong>${escapeHtml(rem.name)}</strong>
            <span class="muted-small">${escapeHtml(fmt.date(rem.nextDate))} · ${escapeHtml(due.text)}</span>
          </div>
        </div>`;
    }).join("");
  }

  // ── Template ────────────────────────────────────────────────────────────────
  function paintSuggestions() {
    suggestionEl.innerHTML = SUGGESTIONS.map((item, index) => `
      <button class="suggestion" type="button" data-suggest="${index}">
        <span class="tile tile--${TONE[item.icon] || "mint"}">${svg(item.icon, 18)}</span>
        <span class="suggestion__body">
          <strong>${escapeHtml(item.name)}</strong>
          <span class="muted-small">${escapeHtml(FREQ_LABEL[item.frequency])}</span>
        </span>
        <span class="suggestion__add" aria-hidden="true">${svg("plus", 16)}</span>
      </button>`).join("");

    suggestionEl.querySelectorAll("[data-suggest]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const template = SUGGESTIONS[Number(btn.dataset.suggest)];
        if (!template) return;
        openForm({
          name: template.name,
          note: template.note,
          frequency: template.frequency,
          icon: template.icon,
          active: true,
          nextDate: isoDay(addFrequency(startOfDay(new Date()), template.frequency)),
        });
      });
    });
  }

  // ── Form ────────────────────────────────────────────────────────────────────
  function openForm(seed) {
    const isEdit = Boolean(seed && seed.id);
    const today = startOfDay(new Date());
    const initial = Object.assign({
      name: "",
      note: "",
      frequency: "weekly",
      icon: "broom",
      active: true,
      nextDate: isoDay(addFrequency(today, "weekly")),
    }, seed || {});

    const freqOptions = Object.entries(FREQ_LABEL)
      .map(([value, label]) => `<option value="${value}"${initial.frequency === value ? " selected" : ""}>${label}</option>`)
      .join("");
    const iconOptions = Object.entries(ICON_LABEL)
      .map(([value, label]) => `<option value="${value}"${initial.icon === value ? " selected" : ""}>${label}</option>`)
      .join("");

    const modal = openModal(`
      <form class="form" id="reminder-form" novalidate>
        <div class="field">
          <label for="rm-name">Nama pengingat <span class="req">*</span></label>
          <input id="rm-name" name="name" type="text" maxlength="60" required value="${escapeHtml(initial.name)}" placeholder="Contoh: Bersihkan kamar mandi" />
        </div>
        <div class="field">
          <label for="rm-note">Catatan <span class="muted-small">(opsional)</span></label>
          <textarea id="rm-note" name="note" rows="2" maxlength="140" placeholder="Apa yang perlu dilakukan?">${escapeHtml(initial.note || "")}</textarea>
        </div>
        <div class="form-row">
          <div class="field">
            <label for="rm-freq">Frekuensi</label>
            <select id="rm-freq" name="frequency">${freqOptions}</select>
          </div>
          <div class="field">
            <label for="rm-date">Tanggal berikutnya</label>
            <input id="rm-date" name="nextDate" type="date" required value="${escapeHtml(initial.nextDate)}" />
          </div>
        </div>
        <div class="field">
          <label for="rm-icon">Kategori</label>
          <select id="rm-icon" name="icon">${iconOptions}</select>
        </div>
        <label class="check-row">
          <input id="rm-active" name="active" type="checkbox"${initial.active !== false ? " checked" : ""} />
          <span>Aktifkan pengingat ini</span>
        </label>
        <p class="field-error" id="rm-error" role="alert" hidden></p>
        <div class="modal-actions">
          <button class="btn btn--secondary" type="button" data-cancel>Batal</button>
          <button class="btn btn--primary" type="submit">${isEdit ? "Simpan Perubahan" : "Tambah Pengingat"}</button>
        </div>
      </form>`, { title: isEdit ? "Edit Pengingat" : "Tambah Pengingat" });

    if (!modal) return;

    const form = modal.querySelector("#reminder-form");
    const errorEl = modal.querySelector("#rm-error");
    const cancelBtn = modal.querySelector("[data-cancel]");
    if (cancelBtn) cancelBtn.addEventListener("click", closeModal);

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const name = form.querySelector("#rm-name").value.trim();
      const note = form.querySelector("#rm-note").value.trim();
      const frequency = form.querySelector("#rm-freq").value;
      const nextDate = form.querySelector("#rm-date").value;
      const icon = form.querySelector("#rm-icon").value;
      const active = form.querySelector("#rm-active").checked;

      if (name.length < 2) {
        errorEl.hidden = false;
        errorEl.textContent = "Nama pengingat minimal 2 karakter.";
        form.querySelector("#rm-name").focus();
        return;
      }
      if (!parseDay(nextDate)) {
        errorEl.hidden = false;
        errorEl.textContent = "Pilih tanggal berikutnya yang valid.";
        form.querySelector("#rm-date").focus();
        return;
      }

      const list = load();
      if (isEdit) {
        const index = list.findIndex((rem) => rem.id === seed.id);
        if (index >= 0) {
          list[index] = Object.assign({}, list[index], { name, note, frequency, nextDate, icon, active });
        }
        persist(list);
        toast("Pengingat diperbarui.", "success");
      } else {
        list.push({
          id: uid(),
          name,
          note,
          frequency,
          nextDate,
          icon,
          active,
          createdAt: new Date().toISOString(),
        });
        persist(list);
        toast("Pengingat ditambahkan.", "success");
      }
      closeModal();
    });
  }

  // ── Aksi kartu ──────────────────────────────────────────────────────────────
  if (listEl) {
    listEl.addEventListener("click", async (event) => {
      const button = event.target.closest("[data-act]");
      if (!button) return;
      const card = button.closest("[data-id]");
      if (!card) return;
      const id = card.dataset.id;
      const list = load();
      const index = list.findIndex((rem) => rem.id === id);
      if (index < 0) return;
      const rem = list[index];
      const action = button.dataset.act;

      if (action === "toggle") {
        list[index] = Object.assign({}, rem, { active: rem.active === false });
        persist(list);
        toast(list[index].active ? "Pengingat diaktifkan." : "Pengingat dinonaktifkan.", "info");
        return;
      }

      if (action === "done") {
        const today = startOfDay(new Date());
        const due = parseDay(rem.nextDate);
        const base = due && due > today ? due : today;
        const next = addFrequency(base, rem.frequency);
        list[index] = Object.assign({}, rem, {
          nextDate: isoDay(next),
          lastDone: new Date().toISOString(),
        });
        persist(list);
        toast(`Selesai. Jadwal berikutnya ${fmt.date(isoDay(next))}.`, "success");
        return;
      }

      if (action === "edit") {
        openForm(rem);
        return;
      }

      if (action === "delete") {
        const ok = await confirmDialog({
          title: "Hapus pengingat?",
          message: `“${rem.name}” akan dihapus dari perangkat ini.`,
          confirmLabel: "Hapus",
          danger: true,
        });
        if (!ok) return;
        persist(load().filter((row) => row.id !== id));
        toast("Pengingat dihapus.", "success");
      }
    });
  }

  if (addBtn) addBtn.addEventListener("click", () => openForm(null));

  // ── Kalender navigasi ───────────────────────────────────────────────────────
  document.getElementById("cal-prev").addEventListener("click", () => {
    state.calendar = new Date(state.calendar.getFullYear(), state.calendar.getMonth() - 1, 1);
    state.selectedDay = null;
    paintCalendar();
  });
  document.getElementById("cal-next").addEventListener("click", () => {
    state.calendar = new Date(state.calendar.getFullYear(), state.calendar.getMonth() + 1, 1);
    state.selectedDay = null;
    paintCalendar();
  });

  // ── Render awal ─────────────────────────────────────────────────────────────
  function paint() {
    paintList();
    paintSuggestions();
    paintCalendar();
    paintUpcoming();
  }

  paint();
});