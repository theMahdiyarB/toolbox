'use strict';

(() => {
  const THEME_KEY      = 'maddy-theme';
  const COPY_TOAST_ID  = 'copy-toast';
  const THEME_MQ       = '(prefers-color-scheme: dark)';

  const doc  = document;
  const root = doc.documentElement;

  // ── Storage ──────────────────────────────────────────────
  function getStorage() {
    try { return window.localStorage; } catch (_) { return null; }
  }

  function getStoredTheme() {
    const v = getStorage()?.getItem(THEME_KEY);
    return v === 'dark' || v === 'light' ? v : null;
  }

  function setStoredTheme(theme) {
    try { getStorage()?.setItem(THEME_KEY, theme); } catch (_) { /* ignore */ }
  }

  // ── Copy toast ───────────────────────────────────────────
  function ensureCopyToast() {
    let toast = doc.getElementById(COPY_TOAST_ID);
    if (toast) return toast;
    toast = doc.createElement('div');
    toast.id = COPY_TOAST_ID;
    toast.className = 'copy-toast';
    toast.setAttribute('role', 'status');
    toast.setAttribute('aria-live', 'polite');
    toast.setAttribute('aria-atomic', 'true');
    toast.hidden = true;
    doc.body.appendChild(toast);
    return toast;
  }

  function showCopyFeedback(message, ms) {
    message = message || '\u2705 \u06A9\u067E\u06CC \u0634\u062F!'; // ✅ کپی شد!
    const toast = ensureCopyToast();
    toast.classList.remove('copy-toast--visible');
    toast.hidden = false;
    toast.textContent = message;
    void toast.offsetWidth;                       // reflow so the fade/slide animation really runs
    toast.classList.add('copy-toast--visible');
    clearTimeout(toast._hideTimer);
    toast._hideTimer = setTimeout(function() {
      toast.classList.remove('copy-toast--visible');
      toast.hidden = true;
    }, ms || 2000);
  }

  // ── Clipboard ────────────────────────────────────────────
  function fallbackCopy(text) {
    const ta = doc.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.cssText = 'position:fixed;left:-9999px;top:0;opacity:0';
    doc.body.appendChild(ta);
    ta.focus();
    ta.select();
    ta.setSelectionRange(0, ta.value.length);
    let ok = false;
    try {
      ok = doc.execCommand('copy');
      if (!ok) throw new Error('execCommand failed');
      showCopyFeedback();
    } catch (e) {
      console.error('Fallback copy failed:', e);
      showCopyFeedback('\u274C \u06A9\u067E\u06CC \u0646\u0634\u062F'); // ❌ کپی نشد
    } finally {
      doc.body.removeChild(ta);
    }
    return ok;
  }

  async function copyToClipboard(text) {
    if (!text) return false;
    if (navigator.clipboard && window.isSecureContext) {
      try {
        await navigator.clipboard.writeText(text);
        showCopyFeedback();
        return true;
      } catch (e) {
        console.error('Clipboard API failed:', e);
      }
    }
    return fallbackCopy(text);
  }

  // ── Theme ────────────────────────────────────────────────
  function updateThemeButtons(theme) {
    const isDark    = theme === 'dark';
    const icon      = isDark ? '\u2600\uFE0F' : '\uD83C\uDF19'; // ☀️ / 🌙
    const ariaLabel = isDark
      ? '\u062A\u063A\u06CC\u06CC\u0631 \u0628\u0647 \u062D\u0627\u0644\u062A \u0631\u0648\u0634\u0646'   // تغییر به حالت روشن
      : '\u062A\u063A\u06CC\u06CC\u0631 \u0628\u0647 \u062D\u0627\u0644\u062A \u062A\u0627\u0631\u06CC\u06A9'; // تغییر به حالت تاریک

    // Update by ID (iran.html buttons)
    ['themeToggleRail', 'themeToggleFab'].forEach(function(id) {
      const btn = doc.getElementById(id);
      if (!btn) return;
      btn.textContent = icon;
      btn.setAttribute('aria-label', ariaLabel);
      btn.setAttribute('aria-pressed', String(isDark));
    });

    // Update by class (index.html theme-fab button)
    doc.querySelectorAll('.theme-fab').forEach(function(btn) {
      btn.textContent = icon;
      btn.setAttribute('aria-label', ariaLabel);
      btn.setAttribute('aria-pressed', String(isDark));
    });
  }

  const THEME_COLORS = { light: '#006874', dark: '#131c1e' };

  function applyTheme(theme, skipPersist) {
    const t = theme === 'dark' ? 'dark' : 'light';
    root.setAttribute('data-theme', t);
    root.style.colorScheme = t;                   // native scrollbars / inputs follow the theme
    const meta = doc.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute('content', THEME_COLORS[t]);   // phone status bar
    updateThemeButtons(t);
    if (!skipPersist) setStoredTheme(t);
    return t;
  }

  function toggleTheme() {
    return applyTheme(root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
  }

  function initTheme() {
    const getBaleScheme = () => (typeof Bale !== 'undefined' && Bale.WebApp) ? Bale.WebApp.colorScheme : null;
    const stored = getStoredTheme();
    const mq = window.matchMedia ? window.matchMedia(THEME_MQ) : null;
    
    // Priority: Bale colorScheme > localStorage > system preference
    applyTheme(getBaleScheme() || stored || (mq && mq.matches ? 'dark' : 'light'), !stored);

    // Re-check Bale scheme on DOMContentLoaded
    if (doc.readyState === 'loading') {
      doc.addEventListener('DOMContentLoaded', () => {
        applyTheme(getBaleScheme() || stored || (mq && mq.matches ? 'dark' : 'light'), !stored);
      }, { once: true });
    }

    try { // follow later theme changes made inside Bale
      if (typeof Bale !== 'undefined' && Bale.WebApp && typeof Bale.WebApp.onEvent === 'function') {
        Bale.WebApp.onEvent('themeChanged', () => { const c = getBaleScheme(); if (c) applyTheme(c, true); });
      }
    } catch (_) { /* ignore */ }

    if (!mq) return;
    const onChange = function(e) {
      const baleScheme = getBaleScheme();
      if (!baleScheme && !getStoredTheme()) {
        applyTheme(e.matches ? 'dark' : 'light', true);
      }
    };
    if (typeof mq.addEventListener === 'function') {
      mq.addEventListener('change', onChange);
    } else if (typeof mq.addListener === 'function') {
      mq.addListener(onChange);
    }
  }

  function bindThemeToggles() {
    ['themeToggleRail', 'themeToggleFab'].forEach(function(id) {
      const btn = doc.getElementById(id);
      if (btn) btn.addEventListener('click', toggleTheme);
    });
  }

  function bindBackToTop() {
      const btn = doc.getElementById('back-to-top');
      if (!btn) return;
      let ticking = false;

      function update() {
          ticking = false;
          const scrolled = window.scrollY || document.documentElement.scrollTop || document.body.scrollTop;
          btn.classList.toggle('visible', scrolled > 300);
      }
      function onScroll() {
          if (ticking) return;       // one update per frame, even though two listeners fire
          ticking = true;
          requestAnimationFrame(update);
      }

      window.addEventListener('scroll', onScroll, { passive: true });
      document.addEventListener('scroll', onScroll, { passive: true });
      btn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
  }

  function flashCard(el) {
    const card = el.closest('.link-card,.info-card,.table-row,.step-item');
    if (!card) return;
    card.classList.remove('copy-flash');
    void card.offsetWidth;
    card.classList.add('copy-flash');
    card.addEventListener('animationend', () => card.classList.remove('copy-flash'), { once: true });
  }

  function copySmart(text, el) {
    copyToClipboard(text);
    if (el) flashCard(el);
  }

  // Delegated: works for elements added later (lazy tool panels, dynamic lists)
  const COPY_SELECTOR = '.step-code,.table-row__link,.link-card__url';

  function markCopyable(rootEl) {
    (rootEl || doc).querySelectorAll(COPY_SELECTOR).forEach(el => {
      if (el.dataset.copyReady) return;
      el.dataset.copyReady = '1';
      el.setAttribute('title', 'کلیک کنید تا کپی شود');
      // avoid a button nested inside another interactive element (cards are links)
      if (!el.parentElement || !el.parentElement.closest('a,[role="link"],[role="button"],.link-card')) {
        el.setAttribute('role', 'button');
        el.setAttribute('tabindex', '0');
      }
    });
  }

  function bindCopyHandlers(selector) {
    markCopyable(doc);
    doc.addEventListener('click', e => {
      const el = e.target.closest && e.target.closest(selector);
      if (!el) return;
      e.preventDefault();
      e.stopPropagation();
      copySmart(el.textContent.trim(), el);
    }, true);
    doc.addEventListener('keydown', e => {
      if (e.key !== 'Enter' && e.key !== ' ') return;
      const el = e.target.closest && e.target.closest(selector);
      if (!el || el !== e.target) return;
      e.preventDefault();
      copySmart(el.textContent.trim(), el);
    });
  }

  // ── Shared UX (used by index.html and iran.html) ─────────
  const ls = {
    get: k => { try { return localStorage.getItem(k); } catch (_) { return null; } },
    set: (k, v) => { try { localStorage.setItem(k, v); } catch (_) { /* ignore */ } }
  };
  const ICON_LABELS = { '✕': 'حذف', '×': 'بستن', '🗑': 'حذف', '▲': 'بالا', '▼': 'پایین', '◀': 'قبلی', '▶': 'بعدی', '↶': 'برگرداندن', '↷': 'جلو', '↻': 'چرخش', '⧉': 'کپی', '☆': 'افزودن به علاقه‌مندی‌ها', '★': 'حذف از علاقه‌مندی‌ها', '💾': 'دانلود', '📋': 'کپی', '🔍': 'جستجو', '+': 'افزودن', '−': 'کم کردن' };

  // Makes dynamically built UI accessible: labels for icon-only buttons, alerts for error boxes,
  // keyboard support for cards, click-to-copy values, one-line summaries under tool titles.
  function enhance(rootEl) {
    rootEl = rootEl || doc;
    try { if (window._wrapSelectInputs) window._wrapSelectInputs(); if (window._applySelectColorScheme) window._applySelectColorScheme(); if (window._initColorBtns) window._initColorBtns(); } catch (_) { /* ignore */ }
    try { if (window._updateRangeVal) rootEl.querySelectorAll('input[type="range"]').forEach(window._updateRangeVal); } catch (_) { /* ignore */ }
    rootEl.querySelectorAll('button:not([aria-label]),[role="button"]:not([aria-label])').forEach(b => {
      const t = (b.textContent || '').trim();
      if (t && /[؀-ۿA-Za-z0-9]/.test(t)) return;
      const l = b.title || ICON_LABELS[t] || ICON_LABELS[t.charAt(0)];
      if (l) b.setAttribute('aria-label', l);
    });
    rootEl.querySelectorAll('.tool-err:not([role])').forEach(e => e.setAttribute('role', 'alert'));
    rootEl.querySelectorAll('.link-card:not([role])').forEach(c => {
      c.setAttribute('role', 'link'); c.tabIndex = 0;
      c.setAttribute('aria-label', c.textContent.replace(/[☆★]/g, '').replace(/\s+/g, ' ').trim());
    });
    rootEl.querySelectorAll('input:not([aria-label]):not([type=hidden]):not([type=file])').forEach(i => {
      if (i.closest('label') || (i.id && rootEl.querySelector('label[for="' + i.id + '"]'))) return;
      const l = i.placeholder || i.title; if (l) i.setAttribute('aria-label', l);
    });
    rootEl.querySelectorAll('.tool-card:not([data-lazy]) .tool-title').forEach(t => {
      const n = t.nextElementSibling;
      if (n && (n.classList.contains('tool-sub') || n.tagName === 'P')) return;
      const d = (t.closest('.tool-card') || t.parentElement).querySelector('.tool-desc'); if (!d) return;
      let s = d.textContent.trim().split(/(?<=[.؟!])\s|\s*(?:کاربرد)/)[0].replace(/[.]$/, '');
      if (s.length > 110) s = s.slice(0, 107).replace(/\s\S*$/, '') + '…';
      if (s.length > 12) { const p = doc.createElement('div'); p.className = 'tool-sub'; p.textContent = s; t.after(p); }
    });
    rootEl.querySelectorAll('.data-row__val:not([data-copy])').forEach(v => { v.dataset.copy = '1'; if (!v.title) v.title = 'برای کپی کلیک کنید'; });
    markCopyable(rootEl);
  }

  // Status pill (offline / online / messages)
  let netEl = null, netTimer;
  function say(html, ms) {
    if (!netEl) {
      netEl = doc.createElement('div'); netEl.id = 'tb-net';
      netEl.setAttribute('role', 'status'); netEl.setAttribute('aria-live', 'polite');
      doc.body.appendChild(netEl);
    }
    netEl.innerHTML = html; netEl.classList.add('show');
    clearTimeout(netTimer);
    if (ms) netTimer = setTimeout(() => netEl.classList.remove('show'), ms);
    return netEl;
  }
  function hideSay() { if (netEl) netEl.classList.remove('show'); }

  function initShared() {
    if (window.__tbShared) return; window.__tbShared = true;
    enhance(doc);

    // keyboard activation for cards
    doc.addEventListener('keydown', e => {
      const c = e.target;
      if (c && c.classList && c.classList.contains('link-card') && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); c.click(); }
    });
    // click a result value to copy it
    doc.addEventListener('click', e => {
      const v = e.target.closest && e.target.closest('.data-row__val[data-copy]');
      if (!v || (window.getSelection && String(getSelection()))) return;
      const t = v.textContent.trim(); if (t && t !== '-') copyToClipboard(t);
    });
    // enhance content that appears later (lazy tool panels, re-rendered lists)
    doc.addEventListener('tb:hydrated', e => enhance(e.detail.el));
    let mo; new MutationObserver(() => { clearTimeout(mo); mo = setTimeout(() => { enhance(doc.querySelector('.tool-card.active') || doc.getElementById('home') || doc.querySelector('main') || doc.body); }, 120); })
      .observe(doc.body, { childList: true, subtree: true });

    // friendly errors instead of silent failures
    let lastErr = 0;
    const friendly = m => { m = String(m || ''); return /Failed to fetch|NetworkError|Load failed|network/i.test(m) ? 'اتصال برقرار نشد — آفلاین هستید یا سرور در دسترس نیست.' : /AbortError|aborted/i.test(m) ? 'عملیات لغو شد.' : /quota|memory|allocation/i.test(m) ? 'حافظه‌ی مرورگر کافی نیست؛ فایل کوچک‌تری امتحان کنید.' : 'مشکلی پیش آمد؛ دوباره تلاش کنید.'; };
    const onErr = m => { if (/ResizeObserver|Script error/.test(String(m))) return; if (Date.now() - lastErr < 4000) return; lastErr = Date.now(); showCopyFeedback(friendly(m), 3000); };
    window.addEventListener('unhandledrejection', e => onErr(e.reason && (e.reason.message || e.reason)));
    window.addEventListener('error', e => onErr(e.message));

    // offline status
    let wasOff = false;
    const upd = () => {
      if (!navigator.onLine) { wasOff = true; say('📴 آفلاین — ابزارهای ذخیره‌شده کار می‌کنند'); }
      else if (wasOff) { wasOff = false; say('✅ دوباره آنلاین شدید', 2500); }
    };
    window.addEventListener('offline', upd); window.addEventListener('online', upd); if (!navigator.onLine) upd();
    if ('serviceWorker' in navigator) navigator.serviceWorker.ready.then(async () => {
      if (window.caches && (await caches.keys()).length && !ls.get('tb-off-ready')) { ls.set('tb-off-ready', '1'); say('✅ برنامه برای استفاده‌ی آفلاین آماده است', 4000); }
    }).catch(() => { });

    // shortcuts
    doc.addEventListener('keydown', e => {
      const a = doc.activeElement, inField = a && (/INPUT|TEXTAREA|SELECT/.test(a.tagName) || a.isContentEditable);
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        const s = doc.getElementById('siteSearch'); if (!s) return; e.preventDefault();
        const h = doc.getElementById('home'); if (h && h.style.display === 'none' && window.showTool) window.showTool('home');
        s.focus(); s.select();
      } else if (e.key === 'Escape' && !inField) {
        if (doc.querySelector('.tool-card.active') && !doc.querySelector('.modal.open,dialog[open]') && window.showTool) window.showTool('home');
      } else if (e.key === '?' && !inField) showCopyFeedback('میان‌بر: / یا Ctrl+K جستجو · Esc بازگشت به خانه', 3500);
    });

    // install prompt (after a few visits)
    let dip = null;
    const standalone = (window.matchMedia && matchMedia('(display-mode: standalone)').matches) || navigator.standalone;
    const visits = (+ls.get('tb-visits') || 0) + 1; ls.set('tb-visits', visits);
    function showInstall(ios) {
      if (standalone || ls.get('tb-inst-no') || visits < 3 || doc.getElementById('tb-install')) return;
      const d = doc.createElement('div'); d.id = 'tb-install'; d.setAttribute('role', 'dialog'); d.setAttribute('aria-label', 'نصب برنامه');
      d.innerHTML = '<b>📲 ' + (ios ? 'برای دسترسی سریع و آفلاین: دکمه‌ی اشتراک‌گذاری ← «افزودن به صفحه‌ی اصلی»' : 'برنامه را نصب کنید تا سریع‌تر و بدون اینترنت باز شود') + '</b>' + (ios ? '' : '<button class="btn btn-filled btn-xs" id="tb-inst-ok">نصب</button>') + '<button class="btn btn-tonal btn-xs" id="tb-inst-no">بعداً</button>';
      doc.body.appendChild(d); d.classList.add('show');
      doc.getElementById('tb-inst-no').onclick = () => { ls.set('tb-inst-no', '1'); d.remove(); };
      const ok = doc.getElementById('tb-inst-ok'); if (ok) ok.onclick = async () => { d.remove(); if (dip) { dip.prompt(); await dip.userChoice; dip = null; } };
    }
    window.addEventListener('beforeinstallprompt', e => { e.preventDefault(); dip = e; setTimeout(() => showInstall(false), 6000); });
    if (/iP(hone|ad|od)/.test(navigator.userAgent) && !standalone) setTimeout(() => showInstall(true), 8000);
    window.addEventListener('appinstalled', () => { ls.set('tb-inst-no', '1'); const d = doc.getElementById('tb-install'); if (d) d.remove(); });
  }

  // ── Init ─────────────────────────────────────────────────
  function init() {
    initTheme();
    bindThemeToggles();
    bindBackToTop();
    bindCopyHandlers(COPY_SELECTOR);
    initShared();
  }

  if (doc.readyState === 'loading') {
    doc.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }

  // Public API — accessible via window.* from inline onclick handlers
  window.copyToClipboard  = copyToClipboard;
  window.showCopyFeedback = showCopyFeedback;
  window.toggleTheme      = toggleTheme;
  window.TBUX = { enhance: enhance, say: say, hideSay: hideSay, markCopyable: markCopyable };
})();