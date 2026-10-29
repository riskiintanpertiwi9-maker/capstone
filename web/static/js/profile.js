/**
 * MoldGuard — profile.js
 * Menampilkan profil perangkat lokal, statistik, dan penyimpanan.
 */
"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const { store, fmt, escapeHtml, toast, openModal, closeModal } = window.MG;

  const nameEl = document.getElementById("profile-name");
  const avatarEl = document.getElementById("profile-avatar");
  const joinedEl = document.getElementById("profile-joined");
  const editBtn = document.getElementById("btn-edit-profile");

  const hasStoredProfile = (() => {
    try { return Boolean(localStorage.getItem("moldguard.profile")); }
    catch (err) { return false; }
  })();

  let profile = store.getProfile();
  if (!hasStoredProfile) {
    // Simpan profil default sekali agar tanggal bergabung tidak berubah setiap muat.
    profile = store.saveProfile({ name: profile.name || "Pengguna MoldGuard" });
  }

  function initialOf(name) {
    return (name || "P").trim().charAt(0).toUpperCase() || "P";
  }

  function paintProfile() {
    const name = profile.name || "Pengguna MoldGuard";
    nameEl.textContent = name;
    avatarEl.textContent = initialOf(name);
    joinedEl.textContent = `Profil dibuat ${fmt.dateLong(profile.createdAt)} · hanya di perangkat ini`;

    document.querySelectorAll(".avatar").forEach((el) => {
      el.textContent = initialOf(name);
    });

    const history = store.getHistory();
    const reminders = store.getReminders();
    document.getElementById("profile-total").textContent = String(history.length);
    document.getElementById("profile-mold").textContent = String(history.filter((row) => row.status === "mold_detected").length);
    document.getElementById("profile-reminders").textContent = String(reminders.filter((row) => row.active !== false).length);
  }

  function paintStorage() {
    let bytes = 0;
    let entries = 0;
    try {
      Object.keys(localStorage).forEach((key) => {
        if (!key.startsWith("moldguard.")) return;
        const value = localStorage.getItem(key) || "";
        bytes += (key.length + value.length) * 2;
      });
      entries = store.getHistory().length + store.getReminders().length;
    } catch (err) {
      bytes = 0;
    }

    const usedKb = bytes / 1024;
    const quotaBytes = 5 * 1024 * 1024;
    const percent = Math.min(100, (bytes / quotaBytes) * 100);

    document.getElementById("storage-used").textContent = usedKb >= 1024
      ? `${(usedKb / 1024).toFixed(2)} MB`
      : `${usedKb.toFixed(1)} KB`;
    document.getElementById("storage-fill").style.width = `${percent.toFixed(1)}%`;
    document.getElementById("storage-detail").textContent = entries
      ? `${store.getHistory().length} pemeriksaan dan ${store.getReminders().length} pengingat tersimpan.`
      : "Belum ada data tersimpan.";

    const meter = document.querySelector(".storage-block .meter");
    if (meter) {
      meter.setAttribute("aria-label", `Perkiraan penggunaan penyimpanan ${percent.toFixed(1)} persen dari kuota lima megabyte`);
    }
  }

  function openEdit() {
    const modal = openModal(`
      <form class="form" id="profile-form" novalidate>
        <div class="field">
          <label for="pf-name">Nama tampilan <span class="req">*</span></label>
          <input id="pf-name" type="text" maxlength="40" required value="${escapeHtml(profile.name || "")}" placeholder="Nama Anda" />
          <p class="field-hint">Nama ini hanya dipakai untuk sapaan di Beranda dan avatar. Tidak dikirim ke server.</p>
        </div>
        <p class="field-error" id="pf-error" role="alert" hidden></p>
        <div class="modal-actions">
          <button class="btn btn--secondary" type="button" data-cancel>Batal</button>
          <button class="btn btn--primary" type="submit">Simpan Nama</button>
        </div>
      </form>`, { title: "Edit Profil Perangkat" });

    if (!modal) return;
    const form = modal.querySelector("#profile-form");
    const errorEl = modal.querySelector("#pf-error");
    const cancelBtn = modal.querySelector("[data-cancel]");
    if (cancelBtn) cancelBtn.addEventListener("click", closeModal);

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const name = form.querySelector("#pf-name").value.trim();
      if (name.length < 2) {
        errorEl.hidden = false;
        errorEl.textContent = "Nama minimal 2 karakter.";
        form.querySelector("#pf-name").focus();
        return;
      }
      profile = store.saveProfile({ name });
      paintProfile();
      closeModal();
      toast("Nama profil diperbarui.", "success");
    });
  }

  if (editBtn) editBtn.addEventListener("click", openEdit);

  paintProfile();
  paintStorage();
});