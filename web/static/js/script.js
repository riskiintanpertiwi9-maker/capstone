/**
 * MoldGuard — script.js (shared utilities)
 * File ini berisi utilitas global yang dapat digunakan oleh halaman mana pun.
 * Logika halaman spesifik ada di masing-masing template HTML.
 */

"use strict";

// Hamburger menu — diinisialisasi jika elemen tersedia
(function initHamburger() {
  const hamburger = document.getElementById('hamburger');
  const mobileNav = document.getElementById('mobile-nav');
  if (!hamburger || !mobileNav) return;
  hamburger.addEventListener('click', () => {
    const open = hamburger.classList.toggle('open');
    mobileNav.classList.toggle('open', open);
    hamburger.setAttribute('aria-expanded', String(open));
    mobileNav.setAttribute('aria-hidden', String(!open));
  });
  mobileNav.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => {
      hamburger.classList.remove('open');
      mobileNav.classList.remove('open');
      hamburger.setAttribute('aria-expanded', 'false');
      mobileNav.setAttribute('aria-hidden', 'true');
    });
  });
})();

// Health check badge (opsional)
(async function checkHealth() {
  try {
    const res  = await fetch('/health');
    const data = await res.json();
    const badge = document.getElementById('health-badge');
    if (badge && data.status === 'ok') {
      badge.title = `Device: ${data.device} | YOLO: ${data.yolo_available} | MobileNet: ${data.mobile_available}`;
    }
  } catch (_) { /* server mungkin belum aktif */ }
})();
