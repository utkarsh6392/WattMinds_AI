/* ==========================================================================
   WattMinds 2.0 - themes.js
   Theme switcher, command palette (Ctrl/Cmd + K), number count-up, skeleton
   loaders and the pointer glow. Loaded after app.js; it only reads app.js's
   globals (navigate, drawChart) and never changes app.js behaviour.
   Remove this file (and its <script> tag) to switch all of it off.
   ========================================================================== */
(function () {
  'use strict';

  var root = document.documentElement;
  var $ = function (id) { return document.getElementById(id); };
  var reduceMotion = function () {
    return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  };

  /* ---------------------------------------------------------------- themes */
  var THEMES = [
    { id: 'aurora', name: 'Aurora Glass', note: 'Frosted glass over drifting northern lights', icon: '✦' },
    { id: 'glass',  name: 'Midnight Glass', note: 'Calm, still frosted glass', icon: '◐' },
    { id: 'dusk',   name: 'Warm Dusk', note: 'Plum and peach, soft and cozy', icon: '☾' },
    { id: 'light',  name: 'Soft Sand', note: 'Light, creamy and gently raised', icon: '☀' }
  ];
  var KEY = 'wattminds-theme';

  function isTheme(id) { return THEMES.some(function (t) { return t.id === id; }); }
  function saved() { try { return localStorage.getItem(KEY); } catch (_) { return null; } }
  function save(id) { try { localStorage.setItem(KEY, id); } catch (_) { /* private mode: still works for this visit */ } }
  function systemDefault() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'aurora';
  }
  function current() { return root.getAttribute('data-theme') || 'aurora'; }

  function paint(id) {
    root.setAttribute('data-theme', id);
    markChecked();
    if (typeof window.drawChart === 'function') requestAnimationFrame(window.drawChart);
  }

  function setTheme(id, remember) {
    if (!isTheme(id) || id === current()) return;
    if (remember !== false) save(id);
    if (document.startViewTransition && !reduceMotion()) {
      try { document.startViewTransition(function () { paint(id); }); return; } catch (_) { /* fall through */ }
    }
    paint(id);
  }

  // The inline script in <head> normally sets this before first paint; this is the safety net.
  var first = saved();
  root.setAttribute('data-theme', isTheme(first) ? first : (isTheme(current()) && root.hasAttribute('data-theme') ? current() : systemDefault()));

  /* A visitor who never chose a theme follows the system light/dark setting live. */
  if (window.matchMedia) {
    var mq = window.matchMedia('(prefers-color-scheme: light)');
    var follow = function () { if (!isTheme(saved())) paint(systemDefault()); };
    if (mq.addEventListener) mq.addEventListener('change', follow);
  }

  /* ------------------------------------------------------- theme menu (top bar) */
  var themeBtn = $('theme-btn');
  var themeMenu = $('theme-menu');

  function markChecked() {
    if (!themeMenu) return;
    themeMenu.querySelectorAll('[role="menuitemradio"]').forEach(function (b) {
      b.setAttribute('aria-checked', String(b.dataset.theme === current()));
    });
  }

  function menuItems() { return Array.prototype.slice.call(themeMenu.querySelectorAll('[role="menuitemradio"]')); }

  function closeMenu(returnFocus) {
    if (!themeMenu || themeMenu.classList.contains('hidden')) return;
    themeMenu.classList.add('hidden');
    themeBtn.setAttribute('aria-expanded', 'false');
    if (returnFocus) themeBtn.focus();
  }

  function openMenu() {
    themeMenu.classList.remove('hidden');
    themeBtn.setAttribute('aria-expanded', 'true');
    var items = menuItems();
    (items.filter(function (b) { return b.getAttribute('aria-checked') === 'true'; })[0] || items[0]).focus();
  }

  if (themeBtn && themeMenu) {
    themeMenu.innerHTML = THEMES.map(function (t) {
      return '<button type="button" role="menuitemradio" aria-checked="false" data-theme="' + t.id + '">' +
        '<span class="swatch sw-' + t.id + '" aria-hidden="true"></span>' +
        '<span><b>' + t.name + '</b><small>' + t.note + '</small></span></button>';
    }).join('');
    markChecked();

    themeBtn.addEventListener('click', function () {
      themeMenu.classList.contains('hidden') ? openMenu() : closeMenu(false);
    });
    themeMenu.addEventListener('click', function (e) {
      var b = e.target.closest('[role="menuitemradio"]');
      if (!b) return;
      setTheme(b.dataset.theme);
      closeMenu(true);
    });
    themeMenu.addEventListener('keydown', function (e) {
      var items = menuItems();
      var i = items.indexOf(document.activeElement);
      if (e.key === 'ArrowDown') { e.preventDefault(); items[(i + 1) % items.length].focus(); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); items[(i - 1 + items.length) % items.length].focus(); }
      else if (e.key === 'Home') { e.preventDefault(); items[0].focus(); }
      else if (e.key === 'End') { e.preventDefault(); items[items.length - 1].focus(); }
      else if (e.key === 'Escape') { e.preventDefault(); closeMenu(true); }
      else if (e.key === 'Tab') { closeMenu(false); }
    });
    document.addEventListener('pointerdown', function (e) {
      if (!themeMenu.classList.contains('hidden') && !e.target.closest('#theme-wrap')) closeMenu(false);
    });
  }

  /* ---------------------------------------------------- command palette (Ctrl/Cmd+K) */
  var paletteBtn = $('palette-btn');
  var kbdHint = $('palette-kbd');
  if (kbdHint && /Mac|iPhone|iPad/.test(navigator.platform || '')) kbdHint.textContent = '⌘K';

  var pal = null;   // { scrim, input, list, items, shown, index, opener }

  function pageCommands() {
    return Array.prototype.slice.call(document.querySelectorAll('.nav-item[data-view]')).map(function (b) {
      var icon = b.querySelector('.nav-icon');
      var label = b.textContent.replace(icon ? icon.textContent : '', '').replace(/⌘\d/, '').trim();
      return { group: 'Go to', icon: icon ? icon.textContent : '→', label: label,
               run: function () { if (typeof window.navigate === 'function') window.navigate(b.dataset.view); } };
    });
  }
  function allCommands() {
    var cmds = pageCommands();
    THEMES.forEach(function (t) {
      cmds.push({ group: 'Theme', icon: t.icon, label: 'Theme: ' + t.name, hint: t.id === current() ? 'current' : '', run: function () { setTheme(t.id); } });
    });
    var out = $('logout-button');
    if (out) cmds.push({ group: 'Account', icon: '⎋', label: 'Sign out', run: function () { out.click(); } });
    return cmds;
  }

  function filterCommands(query) {
    var words = query.toLowerCase().split(/\s+/).filter(Boolean);
    var cmds = allCommands();
    if (!words.length) return cmds;
    return cmds.filter(function (c) {
      var hay = (c.group + ' ' + c.label).toLowerCase();
      return words.every(function (w) { return hay.indexOf(w) !== -1; });
    }).sort(function (a, b) {
      var sa = a.label.toLowerCase().indexOf(words[0]) === 0 ? 0 : 1;
      var sb = b.label.toLowerCase().indexOf(words[0]) === 0 ? 0 : 1;
      return sa - sb;
    });
  }

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

  function renderPalette() {
    var items = filterCommands(pal.input.value);
    pal.shown = items;
    pal.index = Math.min(pal.index, Math.max(0, items.length - 1));
    if (!items.length) {
      pal.list.innerHTML = '<li class="palette-empty" role="presentation">Nothing matches “' + esc(pal.input.value) + '”</li>';
      pal.input.removeAttribute('aria-activedescendant');
      return;
    }
    var html = '', lastGroup = '';
    items.forEach(function (c, i) {
      if (c.group !== lastGroup) { html += '<li class="palette-group" role="presentation">' + esc(c.group) + '</li>'; lastGroup = c.group; }
      html += '<li class="palette-item" role="option" id="pal-opt-' + i + '" data-i="' + i + '" aria-selected="' + (i === pal.index) + '">' +
        '<span class="pi-icon" aria-hidden="true">' + esc(c.icon) + '</span><span>' + esc(c.label) + '</span>' +
        (c.hint ? '<small>' + esc(c.hint) + '</small>' : '') + '</li>';
    });
    pal.list.innerHTML = html;
    pal.input.setAttribute('aria-activedescendant', 'pal-opt-' + pal.index);
    var sel = $('pal-opt-' + pal.index);
    if (sel && sel.scrollIntoView) sel.scrollIntoView({ block: 'nearest' });
  }

  function select(i) {
    if (!pal.shown.length) return;
    pal.index = (i + pal.shown.length) % pal.shown.length;
    pal.list.querySelectorAll('.palette-item').forEach(function (li) {
      li.setAttribute('aria-selected', String(Number(li.dataset.i) === pal.index));
    });
    pal.input.setAttribute('aria-activedescendant', 'pal-opt-' + pal.index);
    var sel = $('pal-opt-' + pal.index);
    if (sel && sel.scrollIntoView) sel.scrollIntoView({ block: 'nearest' });
  }

  function runSelected() {
    var cmd = pal && pal.shown[pal.index];
    if (!cmd) return;
    closePalette(false);
    cmd.run();
  }

  function openPalette() {
    if (pal) return;
    var scrim = document.createElement('div');
    scrim.className = 'palette-scrim';
    scrim.innerHTML =
      '<div class="palette" role="dialog" aria-modal="true" aria-label="Command palette">' +
      '<input type="text" id="palette-input" role="combobox" aria-expanded="true" aria-controls="palette-list" aria-autocomplete="list" ' +
      'autocomplete="off" spellcheck="false" placeholder="Jump to a page, switch theme…" aria-label="Search commands">' +
      '<ul class="palette-list" id="palette-list" role="listbox" aria-label="Commands"></ul>' +
      '<div class="palette-hint"><span><kbd>↑</kbd> <kbd>↓</kbd> move</span><span><kbd>Enter</kbd> open</span><span><kbd>Esc</kbd> close</span></div>' +
      '</div>';
    document.body.appendChild(scrim);
    pal = { scrim: scrim, input: scrim.querySelector('input'), list: scrim.querySelector('ul'), shown: [], index: 0, opener: document.activeElement };
    if (paletteBtn) paletteBtn.setAttribute('aria-expanded', 'true');
    renderPalette();
    pal.input.focus();

    pal.input.addEventListener('input', function () { pal.index = 0; renderPalette(); });
    scrim.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); select(pal.index + 1); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); select(pal.index - 1); }
      else if (e.key === 'Home') { e.preventDefault(); select(0); }
      else if (e.key === 'End') { e.preventDefault(); select(pal.shown.length - 1); }
      else if (e.key === 'Enter') { e.preventDefault(); runSelected(); }
      else if (e.key === 'Escape') { e.preventDefault(); closePalette(true); }
      else if (e.key === 'Tab') { e.preventDefault(); }   // focus stays in the search box
    });
    pal.list.addEventListener('pointermove', function (e) {
      var li = e.target.closest('.palette-item');
      if (li && Number(li.dataset.i) !== pal.index) select(Number(li.dataset.i));
    });
    pal.list.addEventListener('click', function (e) {
      var li = e.target.closest('.palette-item');
      if (!li) return;
      pal.index = Number(li.dataset.i);
      runSelected();
    });
    scrim.addEventListener('pointerdown', function (e) { if (e.target === scrim) closePalette(true); });
  }

  function closePalette(restoreFocus) {
    if (!pal) return;
    var opener = pal.opener;
    pal.scrim.remove();
    pal = null;
    if (paletteBtn) paletteBtn.setAttribute('aria-expanded', 'false');
    if (restoreFocus && opener && opener.focus && document.contains(opener)) opener.focus();
  }

  function paletteAllowed() { return document.body.classList.contains('authenticated'); }

  if (paletteBtn) paletteBtn.addEventListener('click', function () { pal ? closePalette(true) : openPalette(); });
  document.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && !e.altKey && !e.shiftKey && e.key.toLowerCase() === 'k') {
      if (!paletteAllowed()) return;
      e.preventDefault();
      pal ? closePalette(true) : openPalette();
    }
  });

  /* ------------------------------------------------------------- count-up numbers */
  var COUNT_IDS = ['metric-energy', 'metric-cost', 'metric-anomalies'];
  var NUMBER = /^[\d,]*\.?\d+$/;
  var counters = {};

  function countUp(el, fromZero) {
    var text = el.textContent.trim();
    if (counters[el.id] && counters[el.id].written === text) return;   // our own write
    if (!NUMBER.test(text)) { counters[el.id] = { written: text, value: null, raf: 0 }; return; }
    var end = parseFloat(text.replace(/,/g, ''));
    var prev = counters[el.id];
    if (prev && prev.raf) cancelAnimationFrame(prev.raf);
    var start = fromZero || !prev || prev.value === null ? 0 : prev.value;
    var state = { written: text, value: end, raf: 0 };
    counters[el.id] = state;
    if (reduceMotion() || start === end) return;
    var decimals = (text.split('.')[1] || '').length;
    var fmt = new Intl.NumberFormat('en-IN', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
    var t0 = performance.now(), dur = 700;
    (function frame(now) {
      var p = Math.min(1, (now - t0) / dur);
      var eased = 1 - Math.pow(1 - p, 3);
      var shown = p === 1 ? text : fmt.format(start + (end - start) * eased);
      state.written = shown;
      el.textContent = shown;
      if (p < 1) state.raf = requestAnimationFrame(frame);
    })(t0);
  }

  var counterObserver = new MutationObserver(function (muts) {
    muts.forEach(function (m) {
      var el = m.target.nodeType === 1 ? m.target : m.target.parentElement;
      if (el && COUNT_IDS.indexOf(el.id) !== -1) countUp(el, false);
    });
  });
  COUNT_IDS.forEach(function (id) {
    var el = $(id);
    if (el) counterObserver.observe(el, { childList: true, characterData: true, subtree: true });
  });

  var introDone = false;
  function intro() {
    if (introDone || !document.body.classList.contains('authenticated')) return;
    introDone = true;
    COUNT_IDS.forEach(function (id) { var el = $(id); if (el) countUp(el, true); });
  }
  new MutationObserver(intro).observe(document.body, { attributes: true, attributeFilter: ['class'] });
  intro();

  /* ------------------------------------------------------------ skeleton loaders */
  var SKELETON =
    '<div class="skeleton" aria-hidden="true"><div class="sk-line title"></div>' +
    '<div class="sk-row"><div class="sk-tile"></div><div class="sk-tile"></div><div class="sk-tile"></div></div>' +
    '<div class="sk-line w85"></div><div class="sk-line w60"></div><div class="sk-tile" style="height:110px"></div></div>';
  var pending = new WeakMap();

  function skeletonHost(button) {
    var view = button.closest('.view');
    var empty = view && view.querySelector('.empty-state');
    return empty ? empty.parentElement : null;
  }
  function startSkeleton(button) {
    if (pending.has(button)) return;
    pending.set(button, setTimeout(function () {       // wait 150 ms so quick answers do not flash
      var host = skeletonHost(button);
      if (!host || host.querySelector('.skeleton')) return;
      host.classList.add('is-loading');
      host.setAttribute('aria-busy', 'true');
      var heading = host.querySelector('.panel-heading');
      heading ? heading.insertAdjacentHTML('afterend', SKELETON) : host.insertAdjacentHTML('afterbegin', SKELETON);
    }, 150));
  }
  function stopSkeleton(button) {
    if (pending.has(button)) { clearTimeout(pending.get(button)); pending.delete(button); }
    var host = skeletonHost(button);
    if (!host) return;
    host.classList.remove('is-loading');
    host.removeAttribute('aria-busy');
    var sk = host.querySelector(':scope > .skeleton');
    if (sk) sk.remove();
  }
  new MutationObserver(function (muts) {
    muts.forEach(function (m) {
      var b = m.target;
      if (b.tagName !== 'BUTTON' || !b.closest('.view') || b.closest('.empty-state')) return;
      if (b.disabled && /Working/.test(b.textContent)) startSkeleton(b);
      else if (!b.disabled) stopSkeleton(b);
    });
  }).observe(document.body, { subtree: true, attributes: true, attributeFilter: ['disabled'] });

  /* ---------------------------------------------------------------- pointer glow */
  var GLOW = '.panel, .metric-card, .hero-card, .quick-link, .repl-card';
  var glowQueued = false, lastEvent = null;
  document.addEventListener('pointermove', function (e) {
    if (e.pointerType !== 'mouse') return;
    lastEvent = e;
    if (glowQueued) return;
    glowQueued = true;
    requestAnimationFrame(function () {
      glowQueued = false;
      var e2 = lastEvent;
      for (var n = e2.target.closest ? e2.target.closest(GLOW) : null; n; n = n.parentElement ? n.parentElement.closest(GLOW) : null) {
        var r = n.getBoundingClientRect();
        n.style.setProperty('--mx', (e2.clientX - r.left) + 'px');
        n.style.setProperty('--my', (e2.clientY - r.top) + 'px');
      }
    });
  }, { passive: true });
})();