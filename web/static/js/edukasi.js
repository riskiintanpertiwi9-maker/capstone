/**
 * MoldGuard — edukasi.js
 * Pencarian dan filter kategori untuk daftar artikel.
 */
"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const searchEl = document.getElementById("edu-search");
  const grid = document.getElementById("article-grid");
  const emptyEl = document.getElementById("edu-empty");
  const countEl = document.getElementById("edu-count");
  const featuredEl = document.getElementById("edu-featured");
  const resetBtn = document.getElementById("edu-reset");
  const cards = grid ? Array.from(grid.querySelectorAll(".article-card")) : [];
  const buttons = Array.from(document.querySelectorAll("[data-category]"));

  const state = { category: "Semua", query: "" };

  const initial = new URLSearchParams(window.location.search).get("q");
  if (initial) {
    state.query = initial.trim().toLowerCase();
    searchEl.value = initial;
  }

  function apply() {
    let visible = 0;

    cards.forEach((card) => {
      const matchesCategory = state.category === "Semua" || card.dataset.category === state.category;
      const haystack = `${card.dataset.search || ""} ${card.dataset.category || ""}`.toLowerCase();
      const matchesQuery = !state.query || haystack.includes(state.query);
      const show = matchesCategory && matchesQuery;
      card.hidden = !show;
      if (show) visible += 1;
    });

    const filtering = state.category !== "Semua" || Boolean(state.query);
    if (featuredEl) featuredEl.hidden = filtering;
    if (emptyEl) emptyEl.hidden = visible !== 0;
    if (countEl) countEl.textContent = filtering ? `${visible} dari ${cards.length} artikel` : `${cards.length} artikel`;
  }

  if (searchEl) {
    searchEl.addEventListener("input", () => {
      state.query = searchEl.value.trim().toLowerCase();
      apply();
    });
  }

  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      state.category = btn.dataset.category || "Semua";
      buttons.forEach((other) => {
        const active = other === btn;
        other.classList.toggle("is-active", active);
        other.setAttribute("aria-pressed", String(active));
      });
      apply();
    });
  });

  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      state.category = "Semua";
      state.query = "";
      if (searchEl) searchEl.value = "";
      buttons.forEach((btn) => {
        const active = btn.dataset.category === "Semua";
        btn.classList.toggle("is-active", active);
        btn.setAttribute("aria-pressed", String(active));
      });
      apply();
    });
  }

  apply();
});