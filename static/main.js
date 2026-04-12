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

  function showCopyFeedback(message) {
    message = message || '\u2705 \u06A9\u067E\u06CC \u0634\u062F!'; // ✅ کپی شد!
    const toast = ensureCopyToast();
    toast.textContent = message;
    toast.hidden = false;
    toast.classList.add('copy-toast--visible');
    clearTimeout(toast._hideTimer);
    toast._hideTimer = setTimeout(function() {
      toast.classList.remove('copy-toast--visible');
      toast.hidden = true;
    }, 2000);
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

  function applyTheme(theme, skipPersist) {
    const t = theme === 'dark' ? 'dark' : 'light';
    root.setAttribute('data-theme', t);
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

      function onScroll() {
          const scrolled = window.scrollY || document.documentElement.scrollTop || document.body.scrollTop;
          btn.classList.toggle('visible', scrolled > 300);
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

  function bindCopyHandlers(selector) {
    doc.querySelectorAll(selector).forEach(el => {
      el.setAttribute('title', 'کلیک کنید تا کپی شود');
      el.setAttribute('role', 'button');
      el.setAttribute('tabindex', '0');
      el.addEventListener('click', e => {
        e.preventDefault();
        e.stopPropagation();
        copySmart(el.textContent.trim(), el);
      });
      el.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          copySmart(el.textContent.trim(), el);
        }
      });
    });
  }

  // ── Init ─────────────────────────────────────────────────
  function init() {
    initTheme();
    bindThemeToggles();
    bindBackToTop();
    bindCopyHandlers('.step-code,.table-row__link,.link-card__url');
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
})();