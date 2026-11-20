# AGENTS.md — Project guide for AI coding agents

> Read this first. It explains what the project is, how it is put together, and the rules that keep changes safe.
> (Also usable as `CLAUDE.md`. README.md is the user-facing description; this file is the engineering view.)

## 1. What this is

**جعبه‌ابزار آفلاین (Offline Toolbox)** — a Persian-first, RTL, installable PWA with ~137 small tools (calculators, text/dev utilities, file tools, Iranian-specific data tools, games). Live at https://mahdiyar.info. Version **11.0** (service-worker cache `toolbox-v11.0`). It also has a full **English UI** (runtime-translated).

Hard product constraints (never violate):
- **Offline-first.** After first visit everything except the "online" tools works without internet.
- **Self-hosted, no CDN.** Every library is a local file in `static/lib/`. No external scripts, fonts, or icons at runtime.
- **Privacy.** Offline tools process data in the browser only. Only online tools talk to the network, and only through our own proxy.
- **No framework, no npm at runtime.** Vanilla JS, one big HTML file.
- **Persian is the source language.** Layout must work in both RTL (fa) and LTR (en).
- Owner preferences: **targeted edits over full rewrites; remove a broken feature rather than patching it badly; keep it light.**

Stack: static `index.html` + `static/{main.css,tools.css,icons.css,main.js}`; `sw.js`; `manifest.json`; Python 3 proxy `api_proxy.py` (loopback :8085) behind **Caddy** on an Iranian VPS (reaches Iranian sites, not most foreign ones).

## 2. Repository map

```
index.html            the whole app (~2.8 MB): markup, per-tool templates, scripts, translation dictionary
iran.html             standalone page: Iranian internet resources (separate from the SPA)
sw.js                 service worker (cache toolbox-v11.1, network-first navigations)
manifest.json         PWA manifest (relative URLs, maskable icon)
scripts/              server-side: api_proxy.py, ai_service.py (TTS/OCR/STT), bale_bot.py, parse_logs.py, tests/
static/lib/           vendored libs: math.js, function-plot, jsQR, qr-code-styling, browser-image-compression,
                      mozjpeg wasm, UPNG, fflate, heic2any, pdf-lib, pdf.js, background-removal + ONNX runtime
static/poems/<poet>/  Ganjoor EPUB data (structure.json per poet)
static/holidays/      Jalali holiday JSON per year (1390–1420)
static/maps/          official metro maps (jpg/pdf)
```

## 3. Editing workflow (there is no build step)

The project ships exactly what is in the repo: edit `index.html` and the files in `static/` **directly**. There is no bundler, transpiler or generator.

- Make **small, exact replacements** (find a unique anchor, replace it); never regenerate or reformat the whole file. It is ~2.8 MB — read only the part you need (grep for ids/function names first).
- Keep every change self-contained and re-runnable-safe: don't leave half-applied edits; check that an anchor occurs exactly once before replacing.
- After editing, verify: (1) syntax-check every inline `<script>` (`node --check` on the extracted code; the `type="module"` ones are fine to skip); (2) load the page in Playwright (Chromium is installed) in **fa and en** and look for `pageerror`; (3) screenshot anything visual.
- Stylesheets referenced from `index.html` carry a `?v=<hash>` cache-buster — if you change a CSS file, update the hash/number so browsers refetch.

## 4. Anatomy of `index.html`

- **`<head>`**: small early script sets `lang`/`dir` from `localStorage['maddy-lang']` before paint; theme bootstrap (`maddy-theme`); stylesheet links with `?v=` hashes.
- **Shell**: top app bar (back button, title, palette, dark-mode, **language button EN/FA**), `<nav class="nav-rail" id="nav-rail">` (desktop) with `#rail-flyout` popup, `<nav id="bottom-nav">` (mobile).
- **Home** (`#home`): hero + search, then sections `#sec-popular/#sec-recent/#sec-favs`, then one `<div class="section" id="sec-…">` per topic category: `general finance time learn text image file dev security design iran culture games`, then `share` (About). Online tools carry a `.link-card__net` wifi badge (list `ONLINE`/`window.TB_ONLINE`); an empty category (e.g. «culture» in EN) is hidden by a small script. Each tool is a `.link-card` with `onclick="showTool('<id>')"`, `.link-card__icon` (emoji), `__name`, `__desc`, a favourite button, and `data-kw` search keywords. **Home card order is the canonical ordering** (the rail flyouts copy it at runtime).
- **Tool panels**: `<div id="<id>" class="tool-card" data-lazy="1"></div><template id="tpl-<id>">…</template>` (≈141 lazy templates). `TBL.hydrate(id)` copies the template into the placeholder on first open. Use `TBL.on(id, fn)` to run code after hydration. Tool ids are global DOM ids — keep them unique.
- **Routing**: `showTool(id)` → `_applyTool(id)`; state saved/restored per tool (`_saveToolState/_restoreToolState`); URL via `?tool=<id>` (Bale WebView strips `#`) or `#<id>`; popstate supported. Metro also accepts `?tool=metromap&city=&from=&to=`. `showTool('invoice')` is aliased to `docsuite`.
- **Registries you must keep in sync for a tool** (the category is simply which `#sec-…` section the card sits in; `RAIL_CATS` must list it too): the `.link-card`, the `.tool-card` + template, `TOOL_TITLES` (id→Persian title), `RAIL_CATS` (category → `{id,icon,name}` list; flyout order actually comes from the home cards, §6), `ONLINE_ONLY` (ids that need internet; shows an offline note), and the SW `SHELL_URLS` if the tool needs a new static file.
- **Helpers**: `haptic(el)`, `showToast()`, favourites/recents (`toggleFav`, localStorage `tb-use-counts` etc.), `IS_BALE` flag (running inside the Bale mini-app).
- **`TBX` toolkit** (≈ line 10190): `TBX.dl(blob,name)` direct download; **`TBX.dlAs(blob,name)`** Save-as dialog (returns a Promise) — use for image/PDF outputs; `TBX.share`, `TBX.base/ext`, `TBX.zip` (fflate), `TBX.zone` (drag-drop), `TBX.mkCanvas`; `.tbx-*` CSS. Do not add the dialog to docsuite/résumé downloads (they use `TBX.dl` on purpose).
- **Stateful stores**: `localStorage` keys are prefixed (`tb-*`, `tm2-*`, `maddy-*`). Always wrap storage in try/catch.

## 5. Design system / CSS

- Material 3 Expressive tokens: CSS variables `--m3-*` (primary, surface-container-*, on-surface…), shapes (`--shape-cookie` badges), Vazirmatn variable font.
- Files: `main.css` (shell + shared), `tools.css` (per-tool styles), `icons.css` (Material Symbols as SVG masks: `<span class="ms" data-i="wifi_off"></span>`; add icons there, never via CDN font).
- **Use logical properties** (`margin-inline-start`, `inset-inline-end`, `text-align:start`); the body inherits direction from `<html dir>` — do not hard-code `direction:rtl`/`text-align:right` on body.
- Emoji are used as card icons; for a guaranteed-render icon use an `.ms` icon.

## 6. Navigation rail & flyouts

`.rail-item[data-cat]` buttons (home + each `sec-*`). Hover/focus shows `#rail-flyout` built by `_buildFlyout(catId)`: it reads the live `#sec-…  .link-card` list (so order == homepage, hidden cards skipped) and falls back to `RAIL_CATS`. The **home** rail item has no flyout (by design). Click scrolls the home section into view.

## 7. Internationalisation (Persian ⇄ English)

Goal: in EN mode **zero Persian characters** are visible (text, placeholders, titles, aria-labels, option text, dynamically created UI).

How it works (all inlined in `index.html`):
- `window.UI_KEYS` — ~8,260 fa→en entries. `translateText` = whitespace-tolerant exact lookup → per-run fallback `trRun` (greedy longest phrase, digit-normalised keys, trailing punctuation peeled) → `latin()` (Persian digits/punctuation → Latin).
- A `MutationObserver` re-translates added nodes and changed attributes; originals are restored when switching back to FA. `attrPass/attrRestore` cover `placeholder/title/aria-label/alt`, button values, textarea defaults, `option` text (value kept).
- `window.tbLang()` / `window.tbSetLang('fa'|'en')`; stored in `localStorage['maddy-lang']`.
- Five FA-only tools are hidden in EN: `diwan, constitution, pasban, kbfix, textfix` (the `FA` list in the small script near the end of `index.html`, plus a CSS rule hiding their cards; the guard wraps `showTool`).
- Translation data: the dictionary object `window.UI_KEYS = {"فارسی": "English", …}` inside `index.html` (one very long line; edit it with an exact-match replacement, keep the JSON/JS valid). Station, country, province and weather-station names also come from the tools' own data (bilingual).

**When you add or change any Persian UI string**: add its English to `UI_KEYS`, then switch to EN in a browser (Playwright script or by hand), open the tool, exercise it, and confirm no Persian remains — scan text nodes and the attributes `placeholder/title/aria-label/alt` for `[\u0600-\u06FF]`. Persian-only external data (Ganjoor poems, unknown IRSC place names) is the accepted exception. English must read naturally (e.g. «مهر» = Mehr, not "stamp"; context matters).

## 8. Notable subsystems

- **Metro (`tm2`, inline in `index.html`)**: data blob `tb-metro-data` (stations `[en, fa, lat, lon, address, id, lines, …]`, `ln` lines with main list `m` and branches `b`, `ed` edges, `sv` timetable services), four cities (Tehran, Shiraz, Isfahan, Mashhad). Dijkstra over (station,line) states with transfer penalty (`mode` fast/fewest); legs rendered by `renderLeg`; `dirTerm(leg)` computes the terminal station in the travel direction and shows «به سمت X» at the start and at every line change. Station names are bilingual in the data (EN is free).
- **Scan tab (`pdftool` → `sc`)**: pages hold the original File + corner points; only the current page keeps decoded canvases (others are released; warped result kept as a JPEG blob). Auto-detect = `scanDocument(canvas,{mode:'detect'})` from `static/lib/scanic.mjs` (lazy `import()`, MIT, WASM inlined); our own homography + bilinear warp; filters are plain Canvas code (levels stretch, background-division “magic colour” for shadow removal, Otsu B&W). Output goes through `TBX.compress` → pdf-lib and `saved('scp', …)`.
- **Image/PDF tools**: `imgtool` (editor + batch, mozjpeg/UPNG/browser-image-compression, HEIC), `pdftool` (pdf-lib + pdf.js: merge/split/organize/compress/extract/security/edit; helper `saved(id, bytes, orig, name)`), all outputs go through `TBX.dlAs`.
- **Doc suite / résumé / payroll / expenses**: inline in `index.html`; PDF/Word/print export, data in localStorage.
- **Weather / earthquake / prices / movies / translate / post-tracking**: all go through the proxy. Earthquake data = IRSC via Bale channel (cached to `earthquakes.json` by cron) + EMSC.
- **Server AI tools** (`scripts/ai_service.py`): Tesseract OCR, faster-whisper STT, Piper TTS; online-only.
- **Bale mini-app**: `IS_BALE` changes URL handling and disables the service worker.

## 9. Backend & deployment

`api_proxy.py` (stdlib HTTP, loopback `:8085`) routes: `/weather-proxy`, `/weather-static`, `/irsc-proxy`, `/post-track`, `/api-proxy`, `/translate-proxy`, `/img-proxy`. Each needs a Caddy `reverse_proxy 127.0.0.1:8085` rule. `ALLOWED_ORIGINS` controls cross-origin access. Background removal needs COOP/COEP headers. `sw.js` must be served `Cache-Control: no-cache`. Python's urllib fails some TLS fingerprints (Bale) → those fetches use a `curl` subprocess. The VPS cannot reach most foreign hosts: never add a server-side dependency on one without an Iranian fallback.

Deploy checklist: upload `index.html`, `static/*`, `sw.js`, `manifest.json`, `api_proxy.py` → **bump `CACHE_VERSION` in `sw.js`** → restart `api_proxy` if it changed.

## 10. Service worker & manifest

- Shell files pre-cached from `SHELL_URLS` (add new static files there). Navigations: **network-first (4 s timeout) → cache**, fresh copy stored as `/index.html`. Other same-origin GETs: stale-while-revalidate; `/maps/` and `*.pdf`: cache-first. Old caches are deleted on activate; clients get `SW_UPDATED`.
- If a user "does not see changes": it is almost always the SW cache (bump version; DevTools → Unregister + Clear site data).
- `manifest.json`: relative `id/start_url/scope`, icons `favicon.png` (192), `icon-512.png`, `icon-maskable-512.jpg` (maskable), shortcuts use `#calc #jcal #qr #emergency`.

## 11. How to add a tool (checklist)

1. Panel: `<div id="X" class="tool-card" data-lazy="1"></div><template id="tpl-X">…</template>`; init code via `TBL.on('X', fn)`.
2. Home card in the right `#sec-…` (position = display order everywhere), with `data-kw` keywords.
3. `TOOL_TITLES.X`; `RAIL_CATS` entry (icon/name fallback); `ONLINE_ONLY` if it needs internet.
4. Static assets → `static/` and `SHELL_URLS`; libraries go in `static/lib/` (vendored, license-compatible, as small as possible).
5. Downloads: `TBX.dlAs` for file outputs where renaming is useful; `TBX.dl` otherwise.
6. Add English for every Persian string to `UI_KEYS` (§7); verify EN.
7. Test: open at `?tool=X`, fa + en, light + dark, mobile (≈430 px) + desktop (≈1300 px); `node --check` inline scripts.
8. Bump the SW version when deploying.

## 12. Gotchas learned the hard way

- A literal `</script>` inside JS in the HTML must be escaped; in JS template strings use a real `\n`, not a doubled backslash.
- Persian text pitfalls: ZWNJ (U+200C) inside words breaks naive matching; Persian/Arabic digits and `ي/ك` vs `ی/ک`; use the existing normalisers.
- Emoji prefixes: the i18n run regex must not span surrogate pairs (uses `豈`).
- `<option>` translation must keep `value`; never translate attribute values that are identifiers.
- Overriding very short common words in the dictionary (e.g. «ساعت» → "at") breaks other phrases — prefer phrase-level keys.
- Icons for `.ms` must exist in `icons.css`; otherwise nothing renders.
- Tool ids are DOM ids and URL fragments — renaming one breaks links, favourites, and saved state.
- Heavy libs (ONNX, pdf.js) are lazy-loaded; keep first load small.

## 13. Testing recipes

Playwright + Chromium are available. Typical: serve with `python3 -m http.server 8766` from the output dir, then script `chromium.launch()`; load `…/index.html?tool=<id>`; set language via `localStorage['maddy-lang']` in an init script; check `pageerror`; screenshot at `deviceScaleFactor: 2` for anything a human will see. Useful checks: no Persian left in EN mode (text nodes + attributes), language toggle round-trip, flyout order equals home order, `TBX.dlAs` filename sanitising (`my/new:name` → `mynewname.ext`), metro route with a transfer shows «به سمت …».

## 14. Working with the owner

Present changed files at the end of each reply and say what was done and what remains. Prefer exact, minimal replacements. If a feature is flaky, propose removing it. Say plainly when something could not be verified (e.g. live external APIs are untestable from the sandbox).
