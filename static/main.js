"use strict";
((() => {
  const t = "maddy-theme",
    e = "copy-toast",
    a = "(prefers-color-scheme: dark)",
    n = document,
    o = n.documentElement;
  function i() {
    try {
      return window.localStorage;
    } catch (t) {
      return null;
    }
  }
  function r() {
    const e = i()?.getItem(t);
    return "dark" === e || "light" === e ? e : null;
  }
  function s(t, a) {
    t = t || "✅ کپی شد!";
    const o = (function () {
      let t = n.getElementById(e);
      return (
        t ||
        ((t = n.createElement("div")),
        (t.id = e),
        (t.className = "copy-toast"),
        t.setAttribute("role", "status"),
        t.setAttribute("aria-live", "polite"),
        t.setAttribute("aria-atomic", "true"),
        (t.hidden = !0),
        n.body.appendChild(t),
        t)
      );
    })();
    (o.classList.remove("copy-toast--visible"),
      (o.hidden = !1),
      (o.textContent = t),
      o.offsetWidth,
      o.classList.add("copy-toast--visible"),
      clearTimeout(o._hideTimer),
      (o._hideTimer = setTimeout(function () {
        (o.classList.remove("copy-toast--visible"), (o.hidden = !0));
      }, a || 2e3)));
  }
  async function c(t) {
    if (!t) return !1;
    if (navigator.clipboard && window.isSecureContext)
      try {
        return (await navigator.clipboard.writeText(t), s(), !0);
      } catch (t) {
        console.error("Clipboard API failed:", t);
      }
    return (function (t) {
      const e = n.createElement("textarea");
      ((e.value = t),
        e.setAttribute("readonly", ""),
        (e.style.cssText = "position:fixed;left:-9999px;top:0;opacity:0"),
        n.body.appendChild(e),
        e.focus(),
        e.select(),
        e.setSelectionRange(0, e.value.length));
      let a = !1;
      try {
        if (((a = n.execCommand("copy")), !a))
          throw new Error("execCommand failed");
        s();
      } catch (t) {
        (console.error("Fallback copy failed:", t), s("❌ کپی نشد"));
      } finally {
        n.body.removeChild(e);
      }
      return a;
    })(t);
  }
  const l = { light: "#006874", dark: "#131c1e" };
  function d(e, a) {
    const r = "dark" === e ? "dark" : "light";
    (o.setAttribute("data-theme", r), (o.style.colorScheme = r));
    const s = n.querySelector('meta[name="theme-color"]');
    return (
      s && s.setAttribute("content", l[r]),
      (function (t) {
        const e = "dark" === t,
          a = e ? "☀️" : "🌙",
          o = e ? "تغییر به حالت روشن" : "تغییر به حالت تاریک";
        (["themeToggleRail", "themeToggleFab"].forEach(function (t) {
          const i = n.getElementById(t);
          i &&
            ((i.textContent = a),
            i.setAttribute("aria-label", o),
            i.setAttribute("aria-pressed", String(e)));
        }),
          n.querySelectorAll(".theme-fab").forEach(function (t) {
            ((t.textContent = a),
              t.setAttribute("aria-label", o),
              t.setAttribute("aria-pressed", String(e)));
          }));
      })(r),
      a ||
        (function (e) {
          try {
            i()?.setItem(t, e);
          } catch (t) {}
        })(r),
      r
    );
  }
  function u() {
    return d("dark" === o.getAttribute("data-theme") ? "light" : "dark");
  }
  function p(t, e) {
    (c(t),
      e &&
        (function (t) {
          const e = t.closest(".link-card,.info-card,.table-row,.step-item");
          e &&
            (e.classList.remove("copy-flash"),
            e.offsetWidth,
            e.classList.add("copy-flash"),
            e.addEventListener(
              "animationend",
              () => e.classList.remove("copy-flash"),
              { once: !0 },
            ));
        })(e));
  }
  const m = ".step-code,.table-row__link,.link-card__url";
  function f(t) {
    (t || n).querySelectorAll(m).forEach((t) => {
      t.dataset.copyReady ||
        ((t.dataset.copyReady = "1"),
        t.setAttribute("title", "کلیک کنید تا کپی شود"),
        (t.parentElement &&
          t.parentElement.closest(
            'a,[role="link"],[role="button"],.link-card',
          )) ||
          (t.setAttribute("role", "button"), t.setAttribute("tabindex", "0")));
    });
  }
  const h = (t) => {
      try {
        return localStorage.getItem(t);
      } catch (t) {
        return null;
      }
    },
    b = (t, e) => {
      try {
        localStorage.setItem(t, e);
      } catch (t) {}
    },
    v = {
      "✕": "حذف",
      "×": "بستن",
      "🗑": "حذف",
      "▲": "بالا",
      "▼": "پایین",
      "◀": "قبلی",
      "▶": "بعدی",
      "↶": "برگرداندن",
      "↷": "جلو",
      "↻": "چرخش",
      "⧉": "کپی",
      "☆": "افزودن به علاقه‌مندی‌ها",
      "★": "حذف از علاقه‌مندی‌ها",
      "💾": "دانلود",
      "📋": "کپی",
      "🔍": "جستجو",
      "+": "افزودن",
      "−": "کم کردن",
    };
  function g(t) {
    t = t || n;
    try {
      (window._wrapSelectInputs && window._wrapSelectInputs(),
        window._applySelectColorScheme && window._applySelectColorScheme(),
        window._initColorBtns && window._initColorBtns());
    } catch (t) {}
    try {
      window._updateRangeVal &&
        t
          .querySelectorAll('input[type="range"]')
          .forEach(window._updateRangeVal);
    } catch (t) {}
    (t
      .querySelectorAll(
        'button:not([aria-label]),[role="button"]:not([aria-label])',
      )
      .forEach((t) => {
        const e = (t.textContent || "").trim();
        if (e && /[؀-ۿA-Za-z0-9]/.test(e)) return;
        const a = t.title || v[e] || v[e.charAt(0)];
        a && t.setAttribute("aria-label", a);
      }),
      t
        .querySelectorAll(".tool-err:not([role])")
        .forEach((t) => t.setAttribute("role", "alert")),
      t.querySelectorAll(".link-card:not([role])").forEach((t) => {
        (t.setAttribute("role", "link"),
          (t.tabIndex = 0),
          t.setAttribute(
            "aria-label",
            t.textContent.replace(/[☆★]/g, "").replace(/\s+/g, " ").trim(),
          ));
      }),
      t
        .querySelectorAll(
          "input:not([aria-label]):not([type=hidden]):not([type=file])",
        )
        .forEach((e) => {
          if (
            e.closest("label") ||
            (e.id && t.querySelector('label[for="' + e.id + '"]'))
          )
            return;
          const a = e.placeholder || e.title;
          a && e.setAttribute("aria-label", a);
        }),
      t
        .querySelectorAll(".tool-card:not([data-lazy]) .tool-title")
        .forEach((t) => {
          const e = t.nextElementSibling;
          if (e && (e.classList.contains("tool-sub") || "P" === e.tagName))
            return;
          const a = (t.closest(".tool-card") || t.parentElement).querySelector(
            ".tool-desc",
          );
          if (!a) return;
          let o = a.textContent
            .trim()
            .split(/(?<=[.؟!])\s|\s*(?:کاربرد)/)[0]
            .replace(/[.]$/, "");
          if (
            (o.length > 110 &&
              (o = o.slice(0, 107).replace(/\s\S*$/, "") + "…"),
            o.length > 12)
          ) {
            const e = n.createElement("div");
            ((e.className = "tool-sub"), (e.textContent = o), t.after(e));
          }
        }),
      t.querySelectorAll(".data-row__val:not([data-copy])").forEach((t) => {
        ((t.dataset.copy = "1"), t.title || (t.title = "برای کپی کلیک کنید"));
      }),
      f(t));
  }
  let y,
    _ = null;
  function w(t, e) {
    return (
      _ ||
        ((_ = n.createElement("div")),
        (_.id = "tb-net"),
        _.setAttribute("role", "status"),
        _.setAttribute("aria-live", "polite"),
        n.body.appendChild(_)),
      (_.innerHTML = t),
      _.classList.add("show"),
      clearTimeout(y),
      e && (y = setTimeout(() => _.classList.remove("show"), e)),
      _
    );
  }
  function k() {
    if (window.__tbShared) return;
    let t;
    ((window.__tbShared = !0),
      g(n),
      n.addEventListener("keydown", (t) => {
        const e = t.target;
        e &&
          e.classList &&
          e.classList.contains("link-card") &&
          ("Enter" === t.key || " " === t.key) &&
          (t.preventDefault(), e.click());
      }),
      n.addEventListener("click", (t) => {
        const e =
          t.target.closest && t.target.closest(".data-row__val[data-copy]");
        if (!e || (window.getSelection && String(getSelection()))) return;
        const a = e.textContent.trim();
        a && "-" !== a && c(a);
      }),
      n.addEventListener("tb:hydrated", (t) => g(t.detail.el)),
      new MutationObserver(() => {
        (clearTimeout(t),
          (t = setTimeout(() => {
            g(
              n.querySelector(".tool-card.active") ||
                n.getElementById("home") ||
                n.querySelector("main") ||
                n.body,
            );
          }, 120)));
      }).observe(n.body, { childList: !0, subtree: !0 }));
    let e = 0;
    const a = (t) => {
      /ResizeObserver|Script error/.test(String(t)) ||
        Date.now() - e < 4e3 ||
        ((e = Date.now()),
        s(
          ((t) => (
            (t = String(t || "")),
            /Failed to fetch|NetworkError|Load failed|network/i.test(t)
              ? "اتصال برقرار نشد — آفلاین هستید یا سرور در دسترس نیست."
              : /AbortError|aborted/i.test(t)
                ? "عملیات لغو شد."
                : /quota|memory|allocation/i.test(t)
                  ? "حافظه‌ی مرورگر کافی نیست؛ فایل کوچک‌تری امتحان کنید."
                  : "مشکلی پیش آمد؛ دوباره تلاش کنید."
          ))(t),
          3e3,
        ));
    };
    (window.addEventListener("unhandledrejection", (t) =>
      a(t.reason && (t.reason.message || t.reason)),
    ),
      window.addEventListener("error", (t) => a(t.message)));
    let o = !1;
    const i = () => {
      navigator.onLine
        ? o && ((o = !1), w("✅ دوباره آنلاین شدید", 2500))
        : ((o = !0), w("📴 آفلاین — ابزارهای ذخیره‌شده کار می‌کنند"));
    };
    (window.addEventListener("offline", i),
      window.addEventListener("online", i),
      navigator.onLine || i(),
      "serviceWorker" in navigator &&
        navigator.serviceWorker.ready
          .then(async () => {
            window.caches &&
              (await caches.keys()).length &&
              !h("tb-off-ready") &&
              (b("tb-off-ready", "1"),
              w("✅ برنامه برای استفاده‌ی آفلاین آماده است", 4e3));
          })
          .catch(() => {}),
      n.addEventListener("keydown", (t) => {
        const e = n.activeElement,
          a =
            e &&
            (/INPUT|TEXTAREA|SELECT/.test(e.tagName) || e.isContentEditable);
        if ((t.ctrlKey || t.metaKey) && "k" === t.key.toLowerCase()) {
          const e = n.getElementById("siteSearch");
          if (!e) return;
          t.preventDefault();
          const a = n.getElementById("home");
          (a &&
            "none" === a.style.display &&
            window.showTool &&
            window.showTool("home"),
            e.focus(),
            e.select());
        } else
          "Escape" !== t.key || a
            ? "?" !== t.key ||
              a ||
              s("میان‌بر: / یا Ctrl+K جستجو · Esc بازگشت به خانه", 3500)
            : n.querySelector(".tool-card.active") &&
              !n.querySelector(".modal.open,dialog[open]") &&
              window.showTool &&
              window.showTool("home");
      }));
    let r = null;
    const l =
        (window.matchMedia &&
          matchMedia("(display-mode: standalone)").matches) ||
        navigator.standalone,
      d = (+h("tb-visits") || 0) + 1;
    function u(t) {
      if (l || h("tb-inst-no") || d < 3 || n.getElementById("tb-install"))
        return;
      const e = n.createElement("div");
      ((e.id = "tb-install"),
        e.setAttribute("role", "dialog"),
        e.setAttribute("aria-label", "نصب برنامه"),
        (e.innerHTML =
          "<b>📲 " +
          (t
            ? "برای دسترسی سریع و آفلاین: دکمه‌ی اشتراک‌گذاری ← «افزودن به صفحه‌ی اصلی»"
            : "برنامه را نصب کنید تا سریع‌تر و بدون اینترنت باز شود") +
          "</b>" +
          (t
            ? ""
            : '<button class="btn btn-filled btn-xs" id="tb-inst-ok">نصب</button>') +
          '<button class="btn btn-tonal btn-xs" id="tb-inst-no">بعداً</button>'),
        n.body.appendChild(e),
        e.classList.add("show"),
        (n.getElementById("tb-inst-no").onclick = () => {
          (b("tb-inst-no", "1"), e.remove());
        }));
      const a = n.getElementById("tb-inst-ok");
      a &&
        (a.onclick = async () => {
          (e.remove(), r && (r.prompt(), await r.userChoice, (r = null)));
        });
    }
    (b("tb-visits", d),
      window.addEventListener("beforeinstallprompt", (t) => {
        (t.preventDefault(), (r = t), setTimeout(() => u(!1), 6e3));
      }),
      /iP(hone|ad|od)/.test(navigator.userAgent) &&
        !l &&
        setTimeout(() => u(!0), 8e3),
      window.addEventListener("appinstalled", () => {
        b("tb-inst-no", "1");
        const t = n.getElementById("tb-install");
        t && t.remove();
      }));
  }
  function x() {
    var t;
    (!(function () {
      const t = () =>
          "undefined" != typeof Bale && Bale.WebApp
            ? Bale.WebApp.colorScheme
            : null,
        e = r(),
        o = window.matchMedia ? window.matchMedia(a) : null;
      (d(t() || e || (o && o.matches ? "dark" : "light"), !e),
        "loading" === n.readyState &&
          n.addEventListener(
            "DOMContentLoaded",
            () => {
              d(t() || e || (o && o.matches ? "dark" : "light"), !e);
            },
            { once: !0 },
          ));
      try {
        "undefined" != typeof Bale &&
          Bale.WebApp &&
          "function" == typeof Bale.WebApp.onEvent &&
          Bale.WebApp.onEvent("themeChanged", () => {
            const e = t();
            e && d(e, !0);
          });
      } catch (t) {}
      if (!o) return;
      const i = function (e) {
        t() || r() || d(e.matches ? "dark" : "light", !0);
      };
      "function" == typeof o.addEventListener
        ? o.addEventListener("change", i)
        : "function" == typeof o.addListener && o.addListener(i);
    })(),
      ["themeToggleRail", "themeToggleFab"].forEach(function (t) {
        const e = n.getElementById(t);
        e && e.addEventListener("click", u);
      }),
      (function () {
        const t = n.getElementById("back-to-top");
        if (!t) return;
        let e = !1;
        function a() {
          e = !1;
          const a =
            window.scrollY ||
            document.documentElement.scrollTop ||
            document.body.scrollTop;
          t.classList.toggle("visible", a > 300);
        }
        function o() {
          e || ((e = !0), requestAnimationFrame(a));
        }
        (window.addEventListener("scroll", o, { passive: !0 }),
          document.addEventListener("scroll", o, { passive: !0 }),
          t.addEventListener("click", () =>
            window.scrollTo({ top: 0, behavior: "smooth" }),
          ));
      })(),
      (t = m),
      f(n),
      n.addEventListener(
        "click",
        (e) => {
          const a = e.target.closest && e.target.closest(t);
          a &&
            (e.preventDefault(),
            e.stopPropagation(),
            p(a.textContent.trim(), a));
        },
        !0,
      ),
      n.addEventListener("keydown", (e) => {
        if ("Enter" !== e.key && " " !== e.key) return;
        const a = e.target.closest && e.target.closest(t);
        a && a === e.target && (e.preventDefault(), p(a.textContent.trim(), a));
      }),
      k());
  }
  ("loading" === n.readyState
    ? n.addEventListener("DOMContentLoaded", x, { once: !0 })
    : x(),
    (window.copyToClipboard = c),
    (window.showCopyFeedback = s),
    (window.toggleTheme = u),
    (window.TBTheme = {
      set: function (t) {
        return d(t);
      },
    }),
    (window.applyThemeAuto = function () {
      const t = window.matchMedia && window.matchMedia(a);
      return d(t && t.matches ? "dark" : "light", !0);
    }),
    (window.TBUX = {
      enhance: g,
      say: w,
      hideSay: function () {
        _ && _.classList.remove("show");
      },
      markCopyable: f,
    }));
})(),
  (function (t) {
    var e = 0.95047,
      a = 1.08883,
      n = 216 / 24389,
      o = 24389 / 27,
      i = function (t) {
        return (t /= 255) <= 0.04045
          ? t / 12.92
          : Math.pow((t + 0.055) / 1.055, 2.4);
      },
      r = function (t) {
        return (
          255 *
          (t <= 0.0031308 ? 12.92 * t : 1.055 * Math.pow(t, 1 / 2.4) - 0.055)
        );
      },
      s = function (t) {
        var e = t * t * t;
        return e > n ? e : (116 * t - 16) / o;
      },
      c = function (t) {
        return t > n ? Math.cbrt(t) : (o * t + 16) / 116;
      };
    function l(t, n, o) {
      var r =
          0.2126729 * (t = i(t)) +
          0.7151522 * (n = i(n)) +
          0.072175 * (o = i(o)),
        s = (0.0193339 * t + 0.119192 * n + 0.9503041 * o) / a,
        l = c((0.4124564 * t + 0.3575761 * n + 0.1804375 * o) / e),
        d = c(r);
      return [116 * d - 16, 500 * (l - d), 200 * (d - c(s))];
    }
    function d(t, n, i) {
      var c = (t + 16) / 116,
        l = e * s(c + n / 500),
        d = t > 8 ? c * c * c : t / o,
        u = a * s(c - i / 200);
      return [
        r(3.2404542 * l - 1.5371385 * d - 0.4985314 * u),
        r(-0.969266 * l + 1.8760108 * d + 0.041556 * u),
        r(0.0556434 * l - 0.2040259 * d + 1.0572252 * u),
      ];
    }
    var u = function (t) {
        return (
          t[0] >= -0.5 &&
          t[0] <= 255.5 &&
          t[1] >= -0.5 &&
          t[1] <= 255.5 &&
          t[2] >= -0.5 &&
          t[2] <= 255.5
        );
      },
      p = function (t) {
        return (
          "#" +
          t
            .map(function (t) {
              return (
                ((t = Math.max(0, Math.min(255, Math.round(t)))) < 16
                  ? "0"
                  : "") + t.toString(16)
              );
            })
            .join("")
        );
      };
    function m(t) {
      var e;
      return (e = (t = String(t || "").trim()).match(/^#?([0-9a-f]{6})$/i))
        ? [
            parseInt(e[1].slice(0, 2), 16),
            parseInt(e[1].slice(2, 4), 16),
            parseInt(e[1].slice(4), 16),
          ]
        : (e = t.match(/^#?([0-9a-f]{3})$/i))
          ? e[1].split("").map(function (t) {
              return parseInt(t + t, 16);
            })
          : (e = t.match(/rgba?\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)/))
            ? [+e[1], +e[2], +e[3]]
            : null;
    }
    function f(t, e, a) {
      if (t <= 0) return "#000000";
      if (t >= 100) return "#ffffff";
      var n = (e * Math.PI) / 180,
        o = a,
        i = Math.cos(n),
        r = Math.sin(n),
        s = d(t, o * i, o * r);
      if (!u(s)) {
        for (var c = 0, l = a, m = 0; m < 16; m++)
          ((s = d(t, (o = (c + l) / 2) * i, o * r)), u(s) ? (c = o) : (l = o));
        s = d(t, c * i, c * r);
      }
      return p(s);
    }
    function h(t) {
      var e = m(t) || [0, 104, 116],
        a = l(e[0], e[1], e[2]);
      return {
        h: ((180 * Math.atan2(a[2], a[1])) / Math.PI + 360) % 360,
        c: Math.hypot(a[1], a[2]),
        L: a[0],
      };
    }
    var b = function (t, e) {
      var a = ((e - t + 540) % 360) - 180;
      return (t + Math.max(-15, Math.min(15, 0.5 * a)) + 360) % 360;
    };
    function v(t, e, a) {
      var n = h(t),
        o = n.h,
        i = n.c < 8,
        r = i ? 6 : 40,
        s = i ? 4 : 16,
        c = i ? 6 : 28,
        l = i ? 2 : 4,
        d = i ? 3 : 8,
        u = (o + 60) % 360,
        p = e ? 1 : 0,
        m = {},
        v = function (t, e, a, n) {
          m[t] = f(e, a, n);
        },
        g = function (t, e, n, o) {
          return a
            ? p
              ? null == o
                ? Math.min(100, e + 8)
                : o
              : null == n
                ? Math.max(0, t - 10)
                : n
            : p
              ? e
              : t;
        };
      function y(t, e, a, n) {
        (v(n, g(40, 80, 30, 95), e, a),
          v("on-" + n, p ? 20 : 100, e, a),
          v(n + "-container", g(90, 30, 85, 20), e, a),
          v("on-" + n + "-container", g(10, 90, 5, 98), e, a));
      }
      (y(0, o, r, "primary"),
        y(0, o, s, "secondary"),
        y(0, u, c, "tertiary"),
        y(0, 25, 84, "error"),
        y(0, b(80, o), 44, "warning"),
        y(0, b(148, o), 40, "success"),
        ["primary", "secondary", "tertiary"].forEach(function (t, e) {
          var a = 2 === e ? u : o,
            n = [r, s, c][e];
          (v(t + "-fixed", 90, a, n),
            v(t + "-fixed-dim", 80, a, n),
            v("on-" + t + "-fixed", 10, a, n),
            v("on-" + t + "-fixed-variant", 30, a, n));
        }));
      var _ = function (t, e) {
        return f(p ? e : t, o, l);
      };
      return (
        (m.surface = _(98, 6)),
        (m["surface-dim"] = _(87, 6)),
        (m["surface-bright"] = _(98, 24)),
        (m["surface-container-lowest"] = _(100, 4)),
        (m["surface-container-low"] = _(96, 10)),
        (m["surface-container"] = _(94, 12)),
        (m["surface-container-high"] = _(92, 17)),
        (m["surface-container-highest"] = _(90, 22)),
        (m["on-surface"] = f(p ? (a ? 98 : 90) : a ? 4 : 10, o, l)),
        (m["surface-variant"] = f(p ? 30 : 90, o, d)),
        (m["on-surface-variant"] = f(p ? (a ? 92 : 80) : a ? 20 : 30, o, d)),
        (m.outline = f(p ? (a ? 80 : 62) : a ? 30 : 50, o, d)),
        (m["outline-variant"] = f(p ? (a ? 60 : 30) : a ? 50 : 80, o, d)),
        (m["inverse-surface"] = f(p ? 90 : 20, o, l)),
        (m["inverse-on-surface"] = f(p ? 20 : 95, o, l)),
        (m["inverse-primary"] = f(p ? 40 : 80, o, r)),
        (m["surface-tint"] = m.primary),
        (m.scrim = "#000000"),
        (m["shadow-color"] = "#000000"),
        m
      );
    }
    ((t.TBC = {
      scheme: v,
      css: function (t, e) {
        var a = "";
        return (
          [0, 1].forEach(function (n) {
            var o = v(t, !!n, e),
              i = Object.keys(o)
                .map(function (t) {
                  return "--m3-" + t + ":" + o[t];
                })
                .join(";");
            a +=
              (n ? 'html:root[data-theme="dark"]' : "html:root") +
              "{" +
              i +
              "}";
          }),
          a
        );
      },
      parse: m,
      hex: p,
      info: h,
      fromPixels: function (t) {
        var e,
          a = {},
          n = null;
        for (e = 0; e < t.length; e += 4)
          if (!(t[e + 3] < 200)) {
            var o = l(t[e], t[e + 1], t[e + 2]),
              i = Math.hypot(o[1], o[2]);
            if (!(i < 12 || o[0] < 15 || o[0] > 92)) {
              var r = ((180 * Math.atan2(o[2], o[1])) / Math.PI + 360) % 360,
                s = Math.floor(r / 15) % 24,
                c = a[s] || (a[s] = { w: 0, r: 0, g: 0, b: 0 }),
                d = i * i;
              ((c.w += d),
                (c.r += t[e] * d),
                (c.g += t[e + 1] * d),
                (c.b += t[e + 2] * d));
            }
          }
        return (
          Object.keys(a).forEach(function (t) {
            (!n || a[t].w > n.w) && (n = a[t]);
          }),
          n ? p([n.r / n.w, n.g / n.w, n.b / n.w]) : null
        );
      },
      tone: f,
    }),
      "undefined" != typeof module && (module.exports = t.TBC));
  })("undefined" != typeof window ? window : globalThis),
  (function () {
    var t = document,
      e = t.documentElement,
      a = window.TBC,
      n = function (t) {
        try {
          return localStorage.getItem(t);
        } catch (t) {
          return null;
        }
      },
      o = function (t, e) {
        try {
          localStorage.setItem(t, e);
        } catch (t) {}
      },
      i = function (t) {
        try {
          localStorage.removeItem(t);
        } catch (t) {}
      },
      r = !1,
      s = function (e, a) {
        return (a || t).querySelector(e);
      };
    function c(e, a, n) {
      var o = t.createElement(e);
      return (a && (o.className = a), null != n && (o.innerHTML = n), o);
    }
    function l(t, e) {
      return (
        '<span class="ms' +
        (e ? " " + e : "") +
        '" data-i="' +
        t +
        '" aria-hidden="true"></span>'
      );
    }
    var d = {
        tools: {
          calc: "calculate",
          calculus: "function",
          linsolve: "variables",
          bmi: "monitor_weight",
          avg: "bar_chart",
          pct: "percent",
          matrix: "table_chart",
          multable: "close",
          loan: "account_balance",
          deposit: "savings",
          inflationdebt: "trending_up",
          rentcalc: "home_work",
          taxdisc: "sell",
          tip: "restaurant",
          stopwatch: "timer",
          timer: "hourglass_top",
          pomodoro: "timelapse",
          counter: "123",
          timezone: "schedule",
          jcal: "calendar_month",
          dateconv: "event_repeat",
          age: "cake",
          unitconv: "straighten",
          geometry: "square_foot",
          periodic: "science",
          resistor: "settings_input_component",
          subnet: "lan",
          text: "edit",
          charcount: "tag",
          whitespace: "space_bar",
          oneline: "wrap_text",
          lorem: "notes",
          markdown: "markdown",
          diff: "difference",
          slugify: "link",
          morse: "settings_input_antenna",
          roman: "numbers",
          numconvert: "pin",
          textfix: "spellcheck",
          notes: "checklist",
          emojis: "mood",
          worldmap: "public",
          emotcn: "sentiment_satisfied",
          pasban: "menu_book",
          json: "data_object",
          xml: "code",
          htmlesc: "html",
          hash: "fingerprint",
          crypto: "lock",
          jwt: "key",
          pxrem: "format_size",
          regex: "regular_expression",
          cron: "update",
          urlparse: "travel_explore",
          numbase: "looks_two",
          asciitbl: "table_rows",
          enctools: "transform",
          chart: "insert_chart",
          fakejson: "database",
          numwords: "speaker_notes",
          seotools: "manage_search",
          htaccess: "settings",
          keypair: "vpn_key",
          uuid: "badge",
          randnum: "casino",
          textbeauty: "auto_fix_high",
          invoice: "receipt_long",
          rubik: "extension",
          randip: "router",
          randcolor: "palette",
          fake: "person",
          credit: "credit_card",
          avatar: "account_circle",
          placeholder: "wallpaper",
          qr: "qr_code_2",
          qrread: "qr_code_scanner",
          barcode: "barcode",
          colorpicker: "colorize",
          wcag: "contrast",
          colorblind: "visibility",
          gradient: "gradient",
          shadow: "layers",
          borderrad: "rounded_corner",
          aspect: "aspect_ratio",
          goldenratio: "view_quilt",
          svgviewer: "draw",
          gridbuilder: "grid_view",
          imgpalette: "invert_colors",
          imgtool: "photo_library",
          bgremove: "ink_eraser",
          ocrtool: "document_scanner",
          stttool: "mic",
          pdftool: "picture_as_pdf",
          filesplit: "merge",
          watermark: "water_drop",
          img2b64: "swap_horiz",
          csvjson: "sync_alt",
          emergency: "emergency",
          citycodes: "call",
          trafficfines: "directions_car",
          metromap: "subway",
          constitution: "gavel",
          device: "devices",
          ua: "info",
          minigames: "sports_esports",
          wordcloud: "cloud",
          diwan: "auto_stories",
          compass: "explore",
          bmc: "dashboard",
          eisenhower: "dataset",
          decmatrix: "rule",
          citation: "format_quote",
          langscores: "school",
          audiotools: "graphic_eq",
          tts: "record_voice_over",
          weather: "partly_cloudy_day",
          earthquake: "earthquake",
          translate: "translate",
          currency: "currency_exchange",
          movies: "movie",
          posttrack: "local_shipping",
          share: "share",
          pwa: "install_mobile",
          analytics: "monitoring",
          about: "info",
          plate: "directions_car",
          phone: "smartphone",
          bill: "receipt",
          bankid: "verified_user",
          kbfix: "keyboard",
          epoch: "more_time",
          typetest: "speed",
          flashcards: "style",
          expenses: "payments",
          habits: "task_alt",
          breathe: "self_improvement",
          exif: "camera",
          favicon: "web_asset",
          qrdata: "wifi",
          pass: "password",
        },
        cats: {
          home: "home",
          "sec-general": "functions",
          "sec-time": "schedule",
          "sec-science": "biotech",
          "sec-text": "edit_note",
          "sec-dev": "code",
          "sec-gen": "bolt",
          "sec-design": "palette",
          "sec-file": "folder",
          "sec-iran": "flag",
          "sec-sys": "memory",
          "sec-games": "sports_esports",
          "sec-pro": "work",
          "sec-online": "language",
          "sec-share": "info",
        },
        catlabel: {
          خانه: "home",
          محاسبه: "functions",
          زمان: "schedule",
          علوم: "biotech",
          متن: "edit_note",
          توسعه: "code",
          مولدها: "bolt",
          طراحی: "palette",
          فایل: "folder",
          ایران: "flag",
          سیستم: "memory",
          سرگرمی: "sports_esports",
          بازی: "sports_esports",
          تخصصی: "work",
          آنلاین: "language",
          "درباره و نصب": "info",
          درباره: "info",
        },
        m: {
          "📋": "content_copy",
          "💾": "download",
          "🌐": "language",
          "💻": "computer",
          "📄": "description",
          "✨": "star_shine",
          "🎨": "palette",
          "🔄": "sync",
          "🎬": "movie",
          "🔢": "123",
          "🖼️": "image",
          "🖼": "image",
          "📦": "inventory_2",
          "⏹": "stop",
          "📐": "square_foot",
          "📱": "mobile",
          "📊": "bar_chart",
          "🏛️": "account_balance",
          "🏛": "account_balance",
          "⚡": "bolt",
          "🔍": "search",
          "🔎": "search",
          "🗑": "delete",
          "🗑️": "delete",
          "🌟": "star",
          "🔗": "link",
          "✏️": "edit",
          "✏": "edit",
          "🔤": "abc",
          "📝": "edit_note",
          "💬": "chat",
          "🎓": "school",
          "🏠": "home",
          "🧭": "explore",
          "🌍": "public",
          "🌏": "public",
          "📖": "menu_book",
          "📲": "install_mobile",
          "▶️": "play_arrow",
          "▶": "play_arrow",
          ℹ️: "info",
          ℹ: "info",
          "🎮": "sports_esports",
          "✂️": "content_cut",
          "✂": "content_cut",
          "🔧": "build",
          "📡": "cell_tower",
          "🔐": "lock",
          "🔒": "lock",
          "🎲": "casino",
          "☁️": "cloud",
          "☁": "cloud",
          "📼": "videocam",
          "📁": "folder",
          "👁": "visibility",
          "👁️": "visibility",
          "🥇": "workspace_premium",
          "🧮": "calculate",
          "📅": "calendar_month",
          "🗓️": "calendar_month",
          "🗓": "calendar_month",
          "📆": "calendar_month",
          "🕐": "schedule",
          "⚖️": "balance",
          "⚖": "balance",
          "🏦": "account_balance",
          "🏷️": "sell",
          "🏷": "sell",
          "⚙️": "settings",
          "⚙": "settings",
          "👤": "person",
          "🖥️": "desktop_windows",
          "🖥": "desktop_windows",
          "💡": "lightbulb",
          "🌿": "eco",
          "⏱️": "timer",
          "⏱": "timer",
          "🔀": "shuffle",
          "🔬": "biotech",
          "🎙️": "mic",
          "🎙": "mic",
          "🎤": "mic",
          "🚗": "directions_car",
          "🚙": "directions_car",
          "📚": "library_books",
          "🔊": "volume_up",
          "🔇": "volume_off",
          "🌤️": "partly_cloudy_day",
          "📶": "signal_cellular_alt",
          "📤": "upload",
          "📥": "download",
          "🎯": "target",
          "🎵": "music_note",
          "🎶": "music_note",
          "🏫": "school",
          "🛠️": "build",
          "🛠": "construction",
          "📏": "straighten",
          "↔️": "swap_horiz",
          "↔": "swap_horiz",
          "⇄": "swap_horiz",
          "⇅": "swap_vert",
          "💳": "credit_card",
          "🌈": "looks",
          "🗂": "folder_copy",
          "🗂️": "folder_copy",
          "💹": "trending_up",
          "📈": "show_chart",
          "🪙": "paid",
          "📑": "article",
          "⬇️": "download",
          "⬇": "arrow_downward",
          "⬆": "arrow_upward",
          "🗺️": "map",
          "🗺": "map",
          "🚕": "local_taxi",
          "🤖": "smart_toy",
          "🌊": "waves",
          "🔠": "match_case",
          "📺": "tv",
          "📻": "radio",
          "🎧": "headphones",
          "🏥": "local_hospital",
          "🔑": "key",
          "🧩": "extension",
          "💧": "water_drop",
          "📞": "call",
          "☎️": "call",
          "🚇": "subway",
          "🕹️": "joystick",
          "🕹": "joystick",
          "🃏": "playing_cards",
          "✍️": "edit",
          "✍": "draw",
          "🔓": "lock_open",
          "⚠️": "warning",
          "⚠": "warning",
          "🧠": "psychology",
          "📌": "keep",
          "🎞️": "movie",
          "🌙": "dark_mode",
          "☀️": "light_mode",
          "🚀": "rocket_launch",
          "❤️": "favorite",
          "📣": "campaign",
          "📢": "campaign",
          "🛡️": "shield",
          "🛡": "shield",
          "🌩️": "thunderstorm",
          "🌩": "thunderstorm",
          "💼": "work",
          "🔥": "local_fire_department",
          "✖️": "close",
          "✖": "close",
          "💰": "payments",
          "💵": "payments",
          "💲": "attach_money",
          "🍽️": "restaurant",
          "⏳": "hourglass_top",
          "🎂": "cake",
          "⚗️": "experiment",
          "⚗": "experiment",
          "🖊️": "edit",
          "🖊": "edit",
          "🖋": "edit",
          "✒️": "edit",
          "🔏": "lock",
          "🔣": "special_character",
          "🔡": "text_fields",
          "🗄️": "dns",
          "🗄": "dns",
          "🪪": "badge",
          "🧾": "receipt_long",
          "📷": "photo_camera",
          "📸": "photo_camera",
          "♿": "accessible",
          "🚨": "emergency",
          "📜": "history_edu",
          "🎡": "attractions",
          "🖌": "brush",
          "🖌️": "brush",
          "📂": "folder_open",
          "🗜": "compress",
          "🗜️": "compress",
          "➕": "add",
          "🏳️": "flag",
          "🏁": "flag",
          "🚩": "flag",
          "🇮🇷": "flag",
          "✅": "check_circle",
          "❌": "cancel",
          "⭐": "star",
          "🔃": "sync",
          "✋": "pan_tool",
          "🧹": "cleaning_services",
          "🔦": "flashlight_on",
          "⏭": "skip_next",
          "⏸": "pause",
          "📭": "mail",
          "📧": "mail",
          "📩": "mail",
          "📮": "mail",
          "📍": "location_on",
          "🧰": "home_repair_service",
          "🔨": "hardware",
          "⏰": "alarm",
          "❓": "help",
          "🎁": "redeem",
          "🎉": "celebration",
          "🌡": "thermostat",
          "🌡️": "thermostat",
          "🧬": "genetics",
          "🚔": "local_police",
          "🚑": "emergency",
          "🛒": "shopping_cart",
          "🎟️": "confirmation_number",
          "✈️": "flight",
          "🛫": "flight_takeoff",
          "🚌": "directions_bus",
          "🛵": "two_wheeler",
          "🛣️": "route",
          "📎": "attach_file",
          "🏢": "apartment",
          "🏭": "factory",
          "🏪": "storefront",
          "🛍️": "shopping_bag",
          "💊": "medication",
          "🩺": "stethoscope",
          "🏅": "military_tech",
          "🌅": "wb_twilight",
          "🌸": "local_florist",
          "🔖": "bookmark",
          "🔰": "shield",
          "☕": "coffee",
          "🔔": "notifications",
          "🆕": "new_releases",
          "☂️": "umbrella",
          "🗞️": "newspaper",
          "📰": "newspaper",
          "🔭": "search",
          "🎭": "theater_comedy",
          "📔": "book",
          "📘": "book",
          "📕": "book",
          "📒": "book",
          "📓": "book",
          "📗": "book",
          "🎒": "backpack",
          "🏡": "home",
          "🕌": "mosque",
          "🏰": "castle",
          "📹": "videocam",
          "🎥": "videocam",
          "🎦": "movie",
          "💿": "album",
          "🏗️": "construction",
          "⚕️": "medical_services",
          "💉": "vaccines",
          "🩹": "healing",
          "🥼": "science",
          "🏃": "directions_run",
          "🎰": "casino",
          "🎼": "music_note",
          "🔆": "light_mode",
          "⛶": "fullscreen",
          "⌫": "backspace",
          "↶": "undo",
          "↷": "redo",
          "↺": "restart_alt",
          "↻": "refresh",
          "✓": "check",
          "✕": "close",
          "☆": "star",
          "★": "star",
          "♡": "favorite",
          "♥": "favorite",
          "🌷": "local_florist",
          "🌺": "local_florist",
          "🌱": "eco",
          "🌾": "grass",
          "🍁": "eco",
          "🍌": "nutrition",
          "🍎": "nutrition",
          "🍏": "nutrition",
          "🍕": "local_pizza",
          "🍚": "rice_bowl",
          "🍱": "lunch_dining",
          "🥘": "dinner_dining",
          "🏔": "landscape",
          "🏔️": "landscape",
          "⛰️": "landscape",
          "🏕️": "camping",
          "🌄": "landscape",
          "🌌": "nightlight",
          "🌦️": "rainy",
          "🌫": "foggy",
          "❄️": "ac_unit",
          "🌰": "nutrition",
          "🏙️": "location_city",
          "🛋": "chair",
          "🛩️": "flight",
          "🚂": "train",
          "🐈": "pets",
          "🐱": "pets",
          "🐶": "pets",
          "🐺": "pets",
          "🐴": "pets",
          "🐘": "pets",
          "🐧": "pets",
          "🐳": "pets",
          "🦊": "pets",
          "🦉": "pets",
          "🦜": "pets",
          "🦏": "pets",
          "🦖": "pets",
          "🦛": "pets",
          "👀": "visibility",
          "👁‍🗨": "visibility",
          "👃": "face",
          "👍🏻": "thumb_up",
          "👨‍⚕": "medical_services",
          "👩🏻": "person",
          "🧑🏻": "person",
          "👷": "engineering",
          "👻": "sentiment_very_satisfied",
          "👾": "sports_esports",
          "💎": "diamond",
          "💙": "favorite",
          "💜": "favorite",
          "🧡": "favorite",
          "❤": "favorite",
          "🔫": "water_drop",
          "🕊": "flutter_dash",
          "🕊️": "flutter_dash",
          "🗃": "inventory_2",
          "🗃️": "inventory_2",
          "😀": "mood",
          "😇": "mood",
          "😊": "mood",
          "🤝": "handshake",
          "🤲": "volunteer_activism",
          "🥸": "face",
          "🧨": "celebration",
          "🧵": "checkroom",
          "🪁": "air",
          "🏹": "target",
          "⚽️": "sports_soccer",
          "⚽": "sports_soccer",
          "♟": "chess",
          "⛩": "temple_buddhist",
          "✍🏻": "edit",
          "🇨🇳": "flag",
          "☝️": "keyboard_arrow_up",
          "🌥": "cloud",
          "🅱️": "sports_esports",
          "Ⓜ️": "subway",
          "0️⃣": "looks_one",
          "2️⃣": "looks_two",
          "7️⃣": "looks_one",
          "🈂️": "translate",
          "🐞": "bug_report",
          "🧱": "foundation",
          "🍔": "lunch_dining",
          "₿": "currency_bitcoin",
          "🐾": "pets",
        },
        f: [
          "account_balance",
          "biotech",
          "bolt",
          "bookmark",
          "build",
          "calculate",
          "chat",
          "check_circle",
          "code",
          "computer",
          "dark_mode",
          "description",
          "download",
          "edit_note",
          "explore",
          "extension",
          "favorite",
          "flag",
          "folder",
          "functions",
          "home",
          "image",
          "info",
          "language",
          "light_mode",
          "lock",
          "mail",
          "map",
          "memory",
          "movie",
          "palette",
          "person",
          "public",
          "schedule",
          "school",
          "science",
          "search",
          "sell",
          "settings",
          "shield",
          "sports_esports",
          "star",
          "sync",
          "timer",
          "work",
        ],
      },
      u = d.tools,
      p = d.cats,
      m = d.catlabel,
      f = Object.keys(d.m).sort(function (t, e) {
        return e.length - t.length;
      }),
      h = f.length
        ? new RegExp(
            "^(?:" +
              f
                .map(function (t) {
                  return t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
                })
                .join("|") +
              ")\\uFE0F?",
          )
        : null,
      b =
        /^(?:\p{Regional_Indicator}{2}|[#*0-9]\uFE0F?\u20E3|\p{Extended_Pictographic})(?:\uFE0F|\u20E3|\u200D\p{Extended_Pictographic}|\p{Emoji_Modifier})*/u,
      v =
        ".info-card__emoji,.alert-emoji,.info-card__note>span:first-child,.rail-item-icon,.bottom-nav-icon,.link-card__icon,.link-card__emoji,.section-heading-icon,.dl-card__icon,.share-card__icon,.upload-zone__icon,.footer-logo,.search-empty__icon,.flyout-item__icon,#flyout-icon,.field__icon,.iran-cta__icon,.btn,.ib,.chip,.recent-chip,.iran-cta__chip,.menu__item,.fav-btn,.tbx-ib,.tool-title,.section__title,.section-heading h2,.tb-quick,.fab,.fab-menu__item,.search-empty__btn,.about-details>summary",
      g =
        '[data-keep],.ms,textarea,input,select,script,style,.emoji-grid,.tool-card[id*="emoji"],.tool-card[id*="mini"],.tool-card[id*="world"]',
      y = g.replace(".ms,", "");
    function _(t) {
      return d.m[t] || d.m[t.replace(/\uFE0F/g, "")] || null;
    }
    function w(t) {
      var e = /showTool\('([^']+)'/.exec(t || "");
      return e && e[1];
    }
    function k(e) {
      if (h && !e.__ms && !e.closest(y)) {
        var a = (function (e) {
            var a;
            return e.matches(".link-card__icon")
              ? (a = e.closest('[onclick*="showTool("]')) &&
                  u[w(a.getAttribute("onclick"))]
              : e.matches(".flyout-item__icon")
                ? (a = e.closest("[data-tool]")) && u[a.dataset.tool]
                : e.matches(".recent-chip")
                  ? u[w(e.getAttribute("onclick"))]
                  : e.matches(".tool-title")
                    ? (a = e.closest(".tool-card")) && u[a.id]
                    : e.matches(".rail-item-icon,.bottom-nav-icon")
                      ? (a = e.closest("[data-cat]")) && p[a.dataset.cat]
                      : "flyout-icon" === e.id
                        ? (a = t.getElementById("flyout-title")) &&
                          m[a.textContent.trim()]
                        : null;
          })(e),
          n = e.textContent.trim();
        if (
          n &&
          n.length <= 5 &&
          !e.children.length &&
          e.matches(
            ".info-card__emoji,.alert-emoji,.info-card__note>span:first-child,.link-card__icon,.link-card__emoji,.section-heading-icon,.dl-card__icon,.share-card__icon,.upload-zone__icon,.footer-logo,.search-empty__icon,.iran-cta__icon,.field__icon,.flyout-item__icon,#flyout-icon",
          )
        ) {
          var o = a || _(n);
          if (o)
            return (
              (e.__ms = "flyout-icon" === e.id ? 0 : 1),
              e.classList.add("ms"),
              e.setAttribute("data-i", o),
              e.setAttribute("aria-hidden", "true"),
              void e.classList.toggle(
                "is-fill",
                d.f.indexOf(o) > -1 &&
                  !e.matches(".link-card__icon,.link-card__emoji"),
              )
            );
        }
        if (
          a &&
          e.matches(".tool-title,.recent-chip") &&
          e.querySelector(".ms")
        )
          return void (e.__ms = 1);
        if (!e.matches(".ms")) {
          for (
            var i,
              r = t.createTreeWalker(e, NodeFilter.SHOW_TEXT, {
                acceptNode: function (t) {
                  return t.parentNode.closest && t.parentNode.closest(g)
                    ? 3
                    : 1;
                },
              }),
              s = [],
              l = 0;
            (i = r.nextNode()) && s.length < 3;
          )
            s.push(i);
          if (
            (s.forEach(function (e) {
              if (!l) {
                var n = e.nodeValue,
                  o = n.match(/^\s*/)[0],
                  i = n.slice(o.length),
                  r = a ? b.exec(i) : h.exec(i);
                if (r) {
                  var s = a || _(r[0]);
                  if (s) {
                    var d = c("span", "ms", r[0]);
                    (d.setAttribute("data-i", s),
                      d.setAttribute("aria-hidden", "true"),
                      (e.nodeValue = i.slice(r[0].length).replace(/^\s+/, " ")),
                      e.parentNode.insertBefore(d, e),
                      o && e.parentNode.insertBefore(t.createTextNode(o), d),
                      (l = 1));
                  }
                }
              }
            }),
            !l && a && e.matches(".tool-title,.recent-chip"))
          ) {
            var f = c("span", "ms");
            (f.setAttribute("data-i", a),
              f.setAttribute("aria-hidden", "true"),
              e.insertBefore(t.createTextNode(" "), e.firstChild),
              e.insertBefore(f, e.firstChild));
          }
          e.__ms = 1;
        }
      }
    }
    function x(e) {
      if (1 === e.nodeType) {
        try {
          (!(function (e) {
            var a = e.querySelector && e.querySelector("#icp-main .btn-row");
            if (!a || a.querySelector("[data-seed-btn]")) return;
            var n = c("button", "btn btn-tonal", l("palette") + "رنگ برنامه");
            ((n.type = "button"),
              n.setAttribute("data-seed-btn", "1"),
              n.addEventListener("click", function () {
                var e = null,
                  a = -1;
                (t
                  .querySelectorAll("#icp-swatches > div")
                  .forEach(function (t) {
                    var n = R(t.textContent) || R(t.getAttribute("onclick"));
                    if (n) {
                      var o = parseInt(n.substr(1, 2), 16),
                        i = parseInt(n.substr(3, 2), 16),
                        r = parseInt(n.substr(5, 2), 16),
                        s = Math.max(o, i, r),
                        c = Math.min(o, i, r),
                        l = (s + c) / 510,
                        d = (s - c) * (1 - Math.abs(l - 0.5));
                      d > a && ((a = d), (e = n));
                    }
                  }),
                  e
                    ? (I(e), B("رنگ برنامه از تصویر تنظیم شد"))
                    : B("ابتدا یک تصویر انتخاب کنید"));
              }),
              a.appendChild(n),
              x(n));
          })(e),
            (function (e) {
              var a = e.querySelectorAll
                ? e.querySelectorAll(".tbx-row,.btn-row")
                : [];
              a.forEach(function (e) {
                if (!e.__split) {
                  var a = [].slice.call(e.children).filter(function (t) {
                      return t.matches("button.btn");
                    }),
                    n =
                      a.filter(function (t) {
                        return (
                          /btn-filled/.test(t.className) &&
                          !/ZIP/i.test(t.textContent)
                        );
                      })[0] ||
                      a.filter(function (t) {
                        return (
                          /دانلود|ذخیره/.test(t.textContent) &&
                          !/ZIP/i.test(t.textContent)
                        );
                      })[0],
                    o = a.filter(function (t) {
                      return t !== n && /ZIP/i.test(t.textContent);
                    });
                  if (n && o.length) {
                    e.__split = 1;
                    var i = c("div", "btn-split"),
                      r = c(
                        "button",
                        "btn btn-split__more " +
                          (/btn-filled/.test(n.className)
                            ? "btn-filled"
                            : "btn-tonal"),
                        l("keyboard_arrow_down"),
                      );
                    ((r.type = "button"),
                      r.setAttribute("aria-label", "گزینه‌های بیشتر"),
                      r.setAttribute("aria-haspopup", "menu"),
                      r.setAttribute("aria-expanded", "false"),
                      n.parentNode.insertBefore(i, n),
                      i.appendChild(n),
                      i.appendChild(r),
                      o.forEach(function (t) {
                        t.setAttribute("data-split-hid", "1");
                      }),
                      r.addEventListener("click", function (e) {
                        e.stopPropagation();
                        var a = s(".menu[data-split]");
                        if (a)
                          return (
                            a.remove(),
                            void r.setAttribute("aria-expanded", "false")
                          );
                        var n = c("div", "menu");
                        (n.setAttribute("role", "menu"),
                          n.setAttribute("data-split", "1"),
                          o.forEach(function (t) {
                            var e = c(
                              "button",
                              "menu__item",
                              l("download") +
                                t.textContent
                                  .replace(/^\s*\S+?\s/, "")
                                  .trim() || t.textContent.trim(),
                            );
                            ((e.type = "button"),
                              e.setAttribute("role", "menuitem"),
                              ("none" === t.style.display || t.disabled) &&
                                e.setAttribute("aria-disabled", "true"),
                              e.addEventListener("click", function () {
                                (n.remove(),
                                  r.setAttribute("aria-expanded", "false"),
                                  t.click());
                              }),
                              n.appendChild(e));
                          }),
                          t.body.appendChild(n));
                        var i = r.getBoundingClientRect();
                        ((n.style.top = i.bottom + 4 + "px"),
                          (n.style.insetInlineStart = "auto"),
                          (n.style.left =
                            Math.max(
                              8,
                              Math.min(
                                innerWidth - n.offsetWidth - 8,
                                i.right - n.offsetWidth,
                              ),
                            ) + "px"),
                          r.setAttribute("aria-expanded", "true"));
                        var d = function (e) {
                          n.contains(e.target) ||
                            (n.remove(),
                            r.setAttribute("aria-expanded", "false"),
                            t.removeEventListener("pointerdown", d, !0));
                        };
                        setTimeout(function () {
                          t.addEventListener("pointerdown", d, !0);
                        }, 0);
                      }));
                  }
                }
              });
            })(e));
        } catch (t) {}
        e.matches(v) && k(e);
        for (var a = e.querySelectorAll(v), n = 0; n < a.length; n++) k(a[n]);
      }
    }
    var E = [],
      A = 0;
    function L(t) {
      (E.push(t),
        A ||
          (A = requestAnimationFrame(function () {
            A = 0;
            var t = E;
            ((E = []),
              t.forEach(function (t) {
                t.isConnected && x(t);
              }));
          })));
    }
    window.TBIcon = { html: l, scan: x };
    var T = [
        "#006874",
        "#4355b9",
        "#7d57c1",
        "#b5267a",
        "#ba1a1a",
        "#b3501b",
        "#6a7a00",
        "#1b8a3a",
      ],
      S = [
        "فیروزه‌ای",
        "آبی",
        "بنفش",
        "سرخابی",
        "قرمز",
        "نارنجی",
        "زیتونی",
        "سبز",
      ],
      C = n("tb-seed") || T[0];
    function q() {
      var t = n("tb-hc");
      return (
        "1" === t ||
        (null === t &&
          window.matchMedia &&
          matchMedia("(prefers-contrast: more)").matches)
      );
    }
    function M() {
      var t = s('meta[name="theme-color"]');
      if (t) {
        var a = getComputedStyle(e).getPropertyValue("--m3-surface").trim();
        a && t.setAttribute("content", a);
      }
    }
    function I(e, n) {
      if (a && a.parse(e)) {
        C = e;
        var r = a.css(e, q()),
          l = s("#tb-dyn");
        (l || (((l = c("style")).id = "tb-dyn"), t.head.appendChild(l)),
          (l.textContent = r),
          !1 !== n &&
            (o("tb-seed", e),
            e !== T[0] || q() ? o("tb-dyn-css", r) : i("tb-dyn-css")),
          M());
      }
    }
    function B(t) {
      window.showCopyFeedback && window.showCopyFeedback(t, 2200);
    }
    function j() {
      var r = c("div", "dlg-scrim open"),
        d = c("div", "dlg");
      (d.setAttribute("role", "dialog"),
        d.setAttribute("aria-modal", "true"),
        d.setAttribute("aria-label", "ظاهر برنامه"));
      var u = T.map(function (t, e) {
          return (
            '<button type="button" class="swatch" role="radio" style="--sw:' +
            t +
            '" data-seed="' +
            t +
            '" aria-label="' +
            S[e] +
            '" aria-checked="' +
            (t === C) +
            '">' +
            l("check") +
            "</button>"
          );
        }).join(""),
        p = (function () {
          try {
            if (!CSS.supports("color", "AccentColor")) return null;
            var e = c("i");
            ((e.style.cssText = "color:AccentColor;position:fixed;opacity:0"),
              t.body.appendChild(e));
            var n = getComputedStyle(e).color;
            e.remove();
            var o = n.match(/\d+/g);
            return o ? a.hex([+o[0], +o[1], +o[2]]) : null;
          } catch (t) {
            return null;
          }
        })();
      ((d.innerHTML =
        '<h2 class="dlg__title">ظاهر برنامه</h2><div class="dlg__sec"><span class="label-l">حالت</span><div class="tbx-tabs" role="radiogroup" aria-label="حالت">' +
        [
          ["auto", "خودکار", "brightness_auto"],
          ["light", "روشن", "light_mode"],
          ["dark", "تاریک", "dark_mode"],
        ]
          .map(function (t) {
            return (
              '<button type="button" class="btn btn-tonal btn-toggle" role="radio" data-mode="' +
              t[0] +
              '" aria-checked="' +
              ((("dark" === (e = n("maddy-theme")) || "light" === e
                ? e
                : "auto") ===
                t[0]) +
                '">') +
              l(t[2]) +
              t[1] +
              "</button>"
            );
            var e;
          })
          .join("") +
        '</div></div><div class="dlg__sec"><span class="label-l">رنگ برنامه</span><div class="swatches" role="radiogroup" aria-label="رنگ">' +
        u +
        '</div><div class="swatch-src"><label class="btn btn-outlined">' +
        l("palette") +
        'رنگ دلخواه<input type="color" id="tb-cpick" value="' +
        C +
        '" style="position:absolute;opacity:0;width:0;height:0"></label><label class="btn btn-outlined">' +
        l("image") +
        'از روی تصویر<input type="file" accept="image/*" id="tb-cimg" hidden></label>' +
        (p
          ? '<button type="button" class="btn btn-outlined" data-sys="' +
            p +
            '">' +
            l("computer") +
            "رنگ سیستم</button>"
          : "") +
        '</div><div class="tb-prev" id="tb-prev"></div></div><div class="dlg__sec"><button type="button" class="btn btn-tonal btn-toggle" id="tb-hc" aria-pressed="' +
        q() +
        '">' +
        l("contrast") +
        'کنتراست بالا</button> <button type="button" class="btn btn-tonal btn-toggle" id="tb-rail" aria-pressed="' +
        ("expanded" === e.getAttribute("data-rail")) +
        '">' +
        l("menu") +
        'نوار کناری گسترده</button></div><div class="dlg__actions"><button type="button" class="btn btn-text" data-reset>بازنشانی</button><button type="button" class="btn btn-filled" data-close>تأیید</button></div>'),
        r.appendChild(d),
        t.body.appendChild(r));
      var m = d.querySelector("#tb-prev");
      function f() {
        getComputedStyle(e);
        m.innerHTML = [
          "--m3-primary",
          "--m3-secondary",
          "--m3-tertiary",
          "--m3-primary-container",
          "--m3-secondary-container",
          "--m3-tertiary-container",
        ]
          .map(function (t) {
            return '<i style="background:var(' + t + ')"></i>';
          })
          .join("");
      }
      function h(t) {
        d.querySelectorAll(".swatch").forEach(function (e) {
          e.setAttribute("aria-checked", String(e.dataset.seed === t));
        });
      }
      function b(t) {
        (I(t), h(t), f());
      }
      f();
      var v = t.activeElement;
      function g() {
        (t.removeEventListener("keydown", y, !0),
          r.classList.add("out"),
          setTimeout(
            function () {
              r.remove();
            },
            matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 200,
          ),
          v && v.focus && v.focus());
      }
      function y(e) {
        if ("Escape" === e.key) (e.stopPropagation(), g());
        else if ("Tab" === e.key) {
          var a = d.querySelectorAll("button,input:not([type=file]),label.btn"),
            n = a[0],
            o = a[a.length - 1];
          e.shiftKey && t.activeElement === n
            ? (e.preventDefault(), o.focus())
            : e.shiftKey ||
              t.activeElement !== o ||
              (e.preventDefault(), n.focus());
        }
      }
      (t.addEventListener("keydown", y, !0),
        r.addEventListener("click", function (t) {
          t.target === r && g();
        }),
        d.addEventListener("click", function (t) {
          var a = t.target.closest("button");
          if (a)
            if (a.dataset.seed) b(a.dataset.seed);
            else if (a.dataset.sys) b(a.dataset.sys);
            else if (a.dataset.mode)
              (d.querySelectorAll("[data-mode]").forEach(function (t) {
                t.setAttribute("aria-checked", String(t === a));
              }),
                "auto" === a.dataset.mode
                  ? (i("maddy-theme"),
                    window.applyThemeAuto && window.applyThemeAuto())
                  : window.TBTheme && window.TBTheme.set(a.dataset.mode),
                setTimeout(f, 50));
            else if ("tb-hc" === a.id) {
              var n = "true" !== a.getAttribute("aria-pressed");
              (a.setAttribute("aria-pressed", String(n)),
                o("tb-hc", n ? "1" : "0"),
                I(C),
                f());
            } else if ("tb-rail" === a.id) {
              var r = "true" !== a.getAttribute("aria-pressed");
              (a.setAttribute("aria-pressed", String(r)),
                r
                  ? e.setAttribute("data-rail", "expanded")
                  : e.removeAttribute("data-rail"),
                o("tb-rail", r ? "expanded" : ""));
            } else if (a.hasAttribute("data-reset")) {
              (i("tb-seed"), i("tb-dyn-css"), i("tb-hc"));
              var c = s("#tb-dyn");
              (c && c.remove(),
                h((C = T[0])),
                M(),
                f(),
                B("رنگ‌ها بازنشانی شد"));
            } else a.hasAttribute("data-close") && g();
        }),
        d.querySelector("#tb-cpick").addEventListener("input", function (t) {
          b(t.target.value);
        }),
        d.querySelector("#tb-cimg").addEventListener("change", function (t) {
          var e,
            n,
            o,
            i,
            r = t.target.files[0];
          r &&
            ((e = r),
            (n = function (t) {
              t ? b(t) : B("رنگ مناسبی پیدا نشد");
            }),
            (o = URL.createObjectURL(e)),
            ((i = new Image()).onload = function () {
              var t = c("canvas");
              t.width = t.height = 64;
              var e = t.getContext("2d");
              (e.drawImage(i, 0, 0, 64, 64),
                URL.revokeObjectURL(o),
                n(a.fromPixels(e.getImageData(0, 0, 64, 64).data)));
            }),
            (i.onerror = function () {
              n(null);
            }),
            (i.src = o));
        }),
        (
          d.querySelector("[aria-checked=true]") || d.querySelector("button")
        ).focus());
    }
    (new MutationObserver(M).observe(e, {
      attributes: !0,
      attributeFilter: ["data-theme"],
    }),
      (window.openAppearance = j));
    var N, F, O;
    function P() {
      var t = s(".tb-appbar"),
        a = t && s(".tb-appbar__search", t),
        n = s(".hero-search-wrapper"),
        o = s(".home-searchbar");
      if (a && n && o) {
        var i,
          r = matchMedia("(min-width: 840px)").matches;
        (r && n.parentNode !== a
          ? a.appendChild(n)
          : r || n.parentNode === o || o.appendChild(n),
          t.classList.toggle("has-search", r),
          e.classList.toggle("search-in-bar", r),
          (i = s(".home-searchbar")) &&
            e.style.setProperty(
              "--searchbar-h",
              (e.classList.contains("search-in-bar") ? 0 : i.offsetHeight) +
                "px",
            ));
      }
    }
    function R(t) {
      var e = /#[0-9a-f]{6}/i.exec(t || "");
      return e && e[0];
    }
    function z(t) {
      return String(t || "")
        .toLowerCase()
        .replace(/[۰-۹]/g, function (t) {
          return t.charCodeAt(0) - 1776;
        })
        .replace(/[٠-٩]/g, function (t) {
          return t.charCodeAt(0) - 1632;
        })
        .replace(/ي/g, "ی")
        .replace(/ك/g, "ک")
        .replace(/[‌ً-ٟ]/g, "");
    }
    function D() {
      try {
        return JSON.parse(n("tb-rq") || "[]");
      } catch (t) {
        return [];
      }
    }
    function W() {
      if (!O && window.showTool) {
        var e,
          a = s(".hero-search-bar"),
          n = a && a.getBoundingClientRect(),
          r =
            ((e = []),
            t
              .querySelectorAll('.link-card[onclick*="showTool("]')
              .forEach(function (t) {
                var a = w(t.getAttribute("onclick"));
                if (a) {
                  var n = t.querySelector(".link-card__name"),
                    o = t.querySelector(".link-card__desc"),
                    i = t.closest(".section"),
                    r = i && i.querySelector(".section__title"),
                    s = r
                      ? r.textContent
                          .replace(/[^؀-ۿA-Za-z0-9 ]/g, "")
                          .replace(/- کاملاً آفلاین/, "")
                          .trim()
                      : "ابزارها",
                    c = n ? n.textContent.trim() : a,
                    l = o ? o.textContent.trim() : "";
                  e.push({
                    id: a,
                    name: c,
                    desc: l,
                    cat: s,
                    h: z(c + " " + l + " " + (t.dataset.kw || "")),
                    n: z(c),
                  });
                }
              }),
            e),
          d = t.activeElement,
          p = c("div");
        ((p.id = "tb-sv"),
          (p.innerHTML =
            '<div class="sv-panel" role="dialog" aria-modal="true" aria-label="جستجو"><div class="sv-bar"><button type="button" class="ib" data-sv="close" aria-label="بستن">' +
            l("arrow_forward") +
            '</button><input class="sv-input" type="search" placeholder="جستجو در ابزارها…" autocomplete="off" spellcheck="false" aria-label="جستجو"><button type="button" class="ib" data-sv="clear" aria-label="پاک کردن" hidden>' +
            l("close") +
            '</button></div><div class="sv-body" role="listbox"></div></div>'),
          t.body.appendChild(p),
          (O = p));
        var m = p.firstChild,
          f = s(".sv-input", p),
          h = s(".sv-body", p),
          b = s("[data-sv=clear]", p);
        if (
          n &&
          m.animate &&
          !matchMedia("(prefers-reduced-motion: reduce)").matches
        ) {
          var v = m.getBoundingClientRect(),
            g =
              "inset(" +
              Math.max(0, n.top - v.top) +
              "px " +
              Math.max(0, v.right - n.right) +
              "px " +
              Math.max(0, v.bottom - n.bottom) +
              "px " +
              Math.max(0, n.left - v.left) +
              "px round 28px)";
          m.animate(
            [
              { clipPath: g, opacity: 0.6 },
              {
                clipPath:
                  "inset(0px round " + (innerWidth >= 840 ? 28 : 0) + "px)",
                opacity: 1,
              },
            ],
            { duration: 420, easing: "cubic-bezier(.05,.7,.1,1)" },
          );
        }
        var y = -1;
        ((p.__close = x),
          t.addEventListener("keydown", E, !0),
          f.addEventListener("input", _),
          p.addEventListener("click", function (t) {
            var e = t.target;
            if (e === p) return x();
            var a = e.closest("[data-sv],[data-id],[data-q]");
            a &&
              ("close" === a.dataset.sv
                ? x()
                : "clear" === a.dataset.sv
                  ? ((f.value = ""), _(), f.focus())
                  : "wipe" === a.dataset.sv
                    ? (i("tb-rq"), _())
                    : a.dataset.id
                      ? k(a.dataset.id)
                      : a.dataset.q &&
                        ((f.value = a.dataset.q), _(), f.focus()));
          }),
          _(),
          setTimeout(function () {
            f.focus();
          }, 30));
      }
      function _() {
        var t = z(f.value).trim();
        if (((b.hidden = !t), (y = -1), t)) {
          var e = t.split(/\s+/),
            a = r
              .filter(function (t) {
                return e.every(function (e) {
                  return t.h.indexOf(e) > -1;
                });
              })
              .sort(function (t, a) {
                return (
                  (0 === t.n.indexOf(e[0]) ? 0 : 1) -
                    (0 === a.n.indexOf(e[0]) ? 0 : 1) ||
                  t.n.indexOf(e[0]) - a.n.indexOf(e[0])
                );
              })
              .slice(0, 40);
          if (!a.length)
            return (
              (h.innerHTML =
                '<div class="sv-empty">' +
                l("search", "x") +
                "<p>نتیجه‌ای برای «" +
                f.value.replace(/</g, "&lt;") +
                "» پیدا نشد</p></div>"),
              void s(".sv-empty .ms", h).style.setProperty("--ms", "3rem")
            );
          var n = {},
            o = [];
          (a.forEach(function (t) {
            (n[t.cat] = n[t.cat] || (o.push(t.cat), [])).push(t);
          }),
            (h.innerHTML = o
              .map(function (t) {
                return (
                  '<div class="sv-h">' +
                  t +
                  "</div>" +
                  n[t]
                    .map(function (t) {
                      return (
                        (t.nameH = (function (t, e) {
                          var a = t.replace(/[&<>]/g, function (t) {
                            return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[
                              t
                            ];
                          });
                          return (
                            e.forEach(function (e) {
                              if (!(e.length < 1)) {
                                var n = z(t).indexOf(e);
                                n > -1 &&
                                  z(t).length === t.length &&
                                  (a =
                                    t.slice(0, n) +
                                    "" +
                                    t.slice(n, n + e.length) +
                                    "" +
                                    t.slice(n + e.length));
                              }
                            }),
                            a
                              .replace(/\u0001/g, "<mark>")
                              .replace(/\u0002/g, "</mark>")
                          );
                        })(t.name, e)),
                        '<button type="button" class="sv-item" role="option" data-id="' +
                          (a = t).id +
                          '"><span class="sv-ico">' +
                          l(u[a.id] || "build") +
                          '</span><span class="sv-t"><b>' +
                          a.nameH +
                          "</b><small>" +
                          a.desc +
                          "</small></span></button>"
                      );
                      var a;
                    })
                    .join("")
                );
              })
              .join("")));
        } else {
          var i = D(),
            c = [
              "calc",
              "imgtool",
              "pdftool",
              "qr",
              "unitconv",
              "jcal",
              "dateconv",
              "bgremove",
            ].filter(function (t) {
              return r.some(function (e) {
                return e.id === t;
              });
            });
          h.innerHTML =
            (i.length
              ? '<div class="sv-h">اخیراً جستجو شده<button type="button" data-sv="wipe">پاک کردن</button></div>' +
                i
                  .map(function (t) {
                    return (
                      '<button type="button" class="sv-item" data-q="' +
                      t.replace(/"/g, "&quot;") +
                      '">' +
                      l("history") +
                      '<span class="sv-t"><b>' +
                      t.replace(/</g, "&lt;") +
                      "</b></span></button>"
                    );
                  })
                  .join("")
              : "") +
            '<div class="sv-h">پرکاربردها</div><div class="sv-chips">' +
            c
              .map(function (t) {
                var e = r.filter(function (e) {
                  return e.id === t;
                })[0];
                return (
                  '<button type="button" class="chip" data-id="' +
                  t +
                  '">' +
                  l(u[t] || "build") +
                  e.name +
                  "</button>"
                );
              })
              .join("") +
            "</div>";
        }
      }
      function k(t) {
        var e = f.value.trim();
        if (e.length > 1) {
          var a = D().filter(function (t) {
            return t !== e;
          });
          (a.unshift(e), o("tb-rq", JSON.stringify(a.slice(0, 8))));
        }
        (x(!0), window.showTool(t));
      }
      function x(e) {
        if (O) {
          var a = O;
          ((O = null),
            t.removeEventListener("keydown", E, !0),
            a.classList.add("out"),
            setTimeout(
              function () {
                a.remove();
              },
              e ? 0 : 200,
            ));
          var n = s("#siteSearch");
          (n && n.blur(), d && d.focus && !e && d.focus());
        }
      }
      function E(e) {
        if ("Escape" === e.key) return (e.stopPropagation(), void x());
        var a = [].slice.call(h.querySelectorAll(".sv-item[data-id]"));
        if ("ArrowDown" === e.key || "ArrowUp" === e.key) {
          if (!a.length) return;
          (e.preventDefault(),
            (y = (y + ("ArrowDown" === e.key ? 1 : -1) + a.length) % a.length),
            a.forEach(function (t, e) {
              t.classList.toggle("sel", e === y);
            }),
            a[y].scrollIntoView({ block: "nearest" }));
        } else if ("Enter" === e.key && t.activeElement === f) {
          var n = a[y < 0 ? 0 : y];
          n && (e.preventDefault(), k(n.dataset.id));
        }
      }
    }
    function H() {
      (!(function () {
        var a = window.showTool;
        if (a && t.startViewTransition && !a.__vt) {
          var n = function (n) {
            if (
              (O && O.__close && O.__close(!0),
              matchMedia("(prefers-reduced-motion: reduce)").matches)
            )
              return a.apply(this, arguments);
            var o = window.event,
              i =
                o && o.target && o.target.closest
                  ? o.target.closest(
                      ".nav-rail,.bottom-navigation-bar,.rail-flyout",
                    )
                  : null,
              r = s(".tool-card.active"),
              c =
                !i && o && o.target && o.target.closest
                  ? o.target.closest(".link-card,.recent-chip")
                  : null,
              l = i ? "through" : "home" === n ? "back" : "fwd",
              d = this,
              u = arguments,
              p = [];
            if (r && r.id === n) return a.apply(d, u);
            (c && "home" !== n && c.isConnected
              ? ((l = "ct"), (c.style.viewTransitionName = "tb-ct"), p.push(c))
              : "home" === n &&
                r &&
                s(".link-card[onclick*=\"'" + r.id + "'\"]") &&
                ((l = "ctb"),
                (r.style.viewTransitionName = "tb-ct"),
                p.push(r)),
              (e.dataset.vt = l),
              t
                .startViewTransition(function () {
                  if ((a.apply(d, u), "ct" === l)) {
                    c.style.viewTransitionName = "";
                    var t = s(".tool-card.active");
                    t && ((t.style.viewTransitionName = "tb-ct"), p.push(t));
                  } else if ("ctb" === l) {
                    r.style.viewTransitionName = "";
                    var e = s(".link-card[onclick*=\"'" + r.id + "'\"]");
                    e &&
                      ((e.style.viewTransitionName = "tb-ct"),
                      p.push(e),
                      e.scrollIntoView({ block: "center" }));
                  }
                })
                .finished.finally(function () {
                  (delete e.dataset.vt,
                    p.forEach(function (t) {
                      t.style.viewTransitionName = "";
                    }));
                }));
          };
          ((n.__vt = 1), (window.showTool = n));
        }
      })(),
        setTimeout(P, 0),
        setTimeout(P, 600),
        addEventListener("resize", function () {
          P();
        }),
        a && n("tb-seed") && !s("#tb-dyn") ? I(C, !1) : M(),
        (function () {
          var a = s(".page-wrapper");
          if (a && !s(".tb-appbar")) {
            var n = (r = !!t.getElementById("home"))
                ? "جعبه‌ابزار آفلاین"
                : "منابع ایران",
              o = c("header", "tb-appbar is-sticky");
            ((o.innerHTML =
              '<div class="tb-appbar__lead"><button type="button" class="ib" data-back aria-label="بازگشت">' +
              l("arrow_forward") +
              '</button><div class="tb-appbar__title" id="tb-appbar-title">' +
              n +
              '</div></div><div class="tb-appbar__search"></div><div class="tb-appbar__actions"><button type="button" class="ib" data-act="theme" aria-label="تغییر پوسته">' +
              l("dark_mode") +
              '</button><button type="button" class="ib" data-act="look" aria-label="ظاهر و رنگ">' +
              l("palette") +
              "</button></div>"),
              a.insertBefore(o, a.firstChild));
            var i = o.querySelector("[data-act=theme] .ms");
            (f(),
              new MutationObserver(f).observe(e, {
                attributes: !0,
                attributeFilter: ["data-theme"],
              }),
              o.addEventListener("click", function (t) {
                var e = t.target.closest("button");
                e &&
                  ("theme" === e.dataset.act
                    ? window.toggleTheme && window.toggleTheme()
                    : "look" === e.dataset.act
                      ? j()
                      : e.hasAttribute("data-back") &&
                        window.showTool &&
                        window.showTool("home"));
              }));
            var d = function () {
              o.classList.toggle("scrolled", (window.scrollY || 0) > 8);
            };
            if ((addEventListener("scroll", d, { passive: !0 }), d(), r)) {
              var u = o.querySelector("#tb-appbar-title"),
                p = "",
                m = function () {
                  var t = s(".tool-card.active"),
                    e = t && s(".tool-title", t),
                    a = "";
                  if (e) {
                    var i = e.cloneNode(!0);
                    (i.querySelectorAll(".ms").forEach(function (t) {
                      t.remove();
                    }),
                      (a = i.textContent
                        .replace(/^[^\u0600-\u06FFA-Za-z0-9]+/, "")
                        .replace(/\s+/g, " ")
                        .trim()));
                  }
                  (o.classList.toggle("is-tool", !!t),
                    a !== p && ((p = a), (u.textContent = a || n)));
                };
              (new MutationObserver(m).observe(s(".tool-container") || a, {
                attributes: !0,
                subtree: !0,
                attributeFilter: ["class"],
                childList: !0,
              }),
                m());
            }
          }
          function f() {
            i.setAttribute(
              "data-i",
              "dark" === e.getAttribute("data-theme")
                ? "light_mode"
                : "dark_mode",
            );
          }
        })(),
        (function () {
          var t = s(".nav-rail");
          if (t && !s(".rail-menu", t)) {
            var a = c("button", "ib rail-menu");
            ((a.type = "button"),
              a.setAttribute("aria-label", "گسترش نوار کناری"),
              a.addEventListener("click", function () {
                var t = "expanded" !== e.getAttribute("data-rail");
                (t
                  ? e.setAttribute("data-rail", "expanded")
                  : e.removeAttribute("data-rail"),
                  o("tb-rail", t ? "expanded" : ""),
                  n());
              }),
              t.insertBefore(a, t.firstChild),
              n(),
              t.querySelectorAll(".rail-item").forEach(function (t) {
                var e = t.querySelector(".rail-item-label");
                e &&
                  !t.getAttribute("aria-label") &&
                  t.setAttribute("aria-label", e.textContent.trim());
              }));
          }
          function n() {
            var t = "expanded" === e.getAttribute("data-rail");
            ((a.innerHTML = l(t ? "menu_open" : "menu")),
              a.setAttribute("aria-expanded", String(t)));
          }
        })(),
        (function () {
          if (r) {
            var t = s("#siteSearch");
            t &&
              ["focus", "pointerdown"].forEach(function (e) {
                t.addEventListener(e, function (t) {
                  ("pointerdown" === e && t.preventDefault(), W());
                });
              });
          }
        })(),
        x(t.body),
        new MutationObserver(function (t) {
          t.forEach(function (t) {
            t.addedNodes.forEach(function (t) {
              if (1 === t.nodeType) L(t);
              else if (
                3 === t.nodeType &&
                t.parentNode &&
                1 === t.parentNode.nodeType
              ) {
                var e = t.parentNode.closest(v);
                e && ((e.__ms = 0), L(e));
              }
            });
          });
        }).observe(t.body, { childList: !0, subtree: !0 }),
        (function () {
          "expanded" === n("tb-rail") &&
            e.setAttribute("data-rail", "expanded");
          var a = s("#back-to-top");
          a &&
            !a.querySelector(".ms") &&
            (a.innerHTML = l("keyboard_arrow_up"));
          var o = t.querySelectorAll(".section-heading"),
            i = 0;
          o.length &&
            addEventListener(
              "scroll",
              function () {
                i ||
                  (i = requestAnimationFrame(function () {
                    ((i = 0),
                      o.forEach(function (t) {
                        var e = parseFloat(getComputedStyle(t).top) || 0;
                        t.classList.toggle(
                          "is-stuck",
                          t.getBoundingClientRect().top <= e + 1 &&
                            t.parentElement.getBoundingClientRect().bottom >
                              e + t.offsetHeight,
                        );
                      }));
                  }));
              },
              { passive: !0 },
            );
        })());
    }
    (t.addEventListener(
      "pointerdown",
      function (e) {
        if (!(e.button > 0)) {
          var a =
            e.target.closest &&
            e.target.closest(
              ".btn,.ib,.chip,.recent-chip,.link-card,.fab,.rail-item,.bottom-nav-item,.dl-card,.share-card,.menu__item,.flyout-item,.upload-zone,.tbx-ib,.calc-btn,.iran-cta,.fab-menu__item",
            );
          if (
            a &&
            !a.disabled &&
            !matchMedia("(prefers-reduced-motion: reduce)").matches
          ) {
            var n = a.getBoundingClientRect(),
              o = 2 * Math.max(n.width, n.height),
              i = t.createElement("span");
            ((i.className = "rpl"),
              (i.style.cssText =
                "width:" +
                o +
                "px;height:" +
                o +
                "px;left:" +
                (e.clientX - n.left - o / 2) +
                "px;top:" +
                (e.clientY - n.top - o / 2) +
                "px"),
              "static" === getComputedStyle(a).position &&
                (a.style.position = "relative"),
              a.appendChild(i),
              setTimeout(function () {
                i.remove();
              }, 700));
          }
        }
      },
      { passive: !0 },
    ),
      t.addEventListener(
        "pointerover",
        function (a) {
          if ("mouse" === a.pointerType) {
            var n =
              a.target.closest &&
              a.target.closest(
                ".ib[aria-label],.fab[aria-label],.rail-item[aria-label],[data-tip]",
              );
            !n ||
              (n.matches(".rail-item") &&
                "expanded" === e.getAttribute("data-rail")) ||
              (clearTimeout(F),
              (F = setTimeout(function () {
                (N ||
                  (((N = c("div")).id = "tb-tip"),
                  N.setAttribute("role", "tooltip"),
                  t.body.appendChild(N)),
                  (N.textContent =
                    n.getAttribute("data-tip") ||
                    n.getAttribute("aria-label")));
                var e = n.getBoundingClientRect();
                ((N.style.left =
                  Math.max(
                    8,
                    Math.min(
                      innerWidth - 8 - N.offsetWidth,
                      e.left + e.width / 2 - N.offsetWidth / 2,
                    ),
                  ) + "px"),
                  (N.style.top = e.bottom + 8 + "px"),
                  N.classList.add("on"));
              }, 500)));
          }
        },
        { passive: !0 },
      ),
      t.addEventListener(
        "pointerout",
        function () {
          (clearTimeout(F), N && N.classList.remove("on"));
        },
        { passive: !0 },
      ),
      t.addEventListener(
        "pointerdown",
        function () {
          (clearTimeout(F), N && N.classList.remove("on"));
        },
        { passive: !0 },
      ),
      (window.TBApplySeed = function (t) {
        I(t);
      }),
      t.addEventListener(
        "pointerdown",
        function (t) {
          "touch" === t.pointerType &&
            navigator.vibrate &&
            !matchMedia("(prefers-reduced-motion: reduce)").matches &&
            t.target.closest &&
            t.target.closest(
              '.btn,.rail-item,.bottom-nav-item,.chip,.recent-chip,.ib,.fab,.menu__item,.swatch,.link-card:not([onclick*="haptic"])',
            ) &&
            navigator.vibrate(6);
        },
        { passive: !0 },
      ),
      "loading" === t.readyState
        ? t.addEventListener("DOMContentLoaded", H)
        : H());
  })());
