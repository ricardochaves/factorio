/* Book page: tabs, variant switch and, for balancer books (viewer "nxm-matrix"), the N x M matrix with a preview
   drawn in the browser from the blueprint string itself. */
(function () {
  'use strict';

  var FB = window.FB;

  /* ---------- tabs ---------- */
  var tabs = Array.prototype.slice.call(document.querySelectorAll('[role="tab"]'));
  function selectTab(tab, focus) {
    tabs.forEach(function (t) {
      var on = t === tab;
      t.setAttribute('aria-selected', String(on));
      t.tabIndex = on ? 0 : -1;
      document.getElementById(t.getAttribute('aria-controls')).hidden = !on;
    });
    if (focus) tab.focus();
  }
  tabs.forEach(function (tab, i) {
    tab.addEventListener('click', function () { selectTab(tab, false); });
    tab.addEventListener('keydown', function (ev) {
      var next = { ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: tabs.length - 1 }[ev.key];
      if (next === undefined) return;
      ev.preventDefault();
      selectTab(tabs[(next + tabs.length) % tabs.length], true);
    });
  });
  var first = tabs.filter(function (t) { return t.getAttribute('aria-selected') === 'true'; })[0] || tabs[0];
  if (first) selectTab(first, false);

  /* ---------- variant (one file of the book) ---------- */
  var variantButtons = Array.prototype.slice.call(document.querySelectorAll('.variants [data-file]'));
  var headerCopy = document.querySelector('[data-book-actions] [data-copy]');
  var headerDownload = document.querySelector('[data-book-actions] [data-download]');
  var slug = window.location.pathname.replace(/\/$/, '').split('/').pop();
  var storeKey = 'fb-file-' + slug;
  var fileIndex = variantButtons.length
    ? +(variantButtons.filter(function (b) { return b.getAttribute('aria-pressed') === 'true'; })[0] || variantButtons[0]).dataset.file
    : 0;
  var onFileChange = [];

  function setFile(i, remember) {
    fileIndex = i;
    variantButtons.forEach(function (b) { b.setAttribute('aria-pressed', String(+b.dataset.file === i)); });
    document.querySelectorAll('[data-file-panel]').forEach(function (p) { p.hidden = +p.dataset.filePanel !== i; });
    var btn = variantButtons[i];
    if (btn && headerCopy) {
      headerCopy.dataset.copy = btn.dataset.url;
      headerDownload.href = btn.dataset.url;
      headerDownload.querySelector('[data-size-label]').textContent = btn.dataset.size;
      headerDownload.querySelector('.sr-only').textContent = btn.dataset.name + ': ';
    }
    if (remember) { try { window.localStorage.setItem(storeKey, String(i)); } catch (e) { /* private mode */ } }
    onFileChange.forEach(function (fn) { fn(i); });
  }
  variantButtons.forEach(function (b) { b.addEventListener('click', function () { setFile(+b.dataset.file, true); }); });

  var dataEl = document.getElementById('book-data');
  if (!dataEl) {
    var saved = null;
    try { saved = window.localStorage.getItem(storeKey); } catch (e) { saved = null; }
    setFile(saved !== null && variantButtons[+saved] ? +saved : fileIndex, false);
    return;
  }

  /* ---------- N x M matrix ---------- */
  var D = JSON.parse(dataEl.textContent);
  var T = D.t;
  var ORIGIN = {};
  D.origins.forEach(function (o) { ORIGIN[o.code] = { name: o[D.lang], color: o.color }; });
  ORIGIN.u = { name: '—', color: '#5d564d' };
  var SIZE_COLORS = [[50, '#3a342c'], [150, '#6b4f22'], [400, '#a36c1c'], [1000, '#d98f1e'], [Infinity, '#f7b84a']];
  var matrix = document.getElementById('matrix');
  var selN = document.getElementById('sel-n');
  var selM = document.getElementById('sel-m');
  var $ = function (id) { return document.getElementById(id); };
  var state = { mode: 'origin', n: 8, m: 8, variant: null };
  var cache = {};
  var renderToken = 0;

  function fmt(n) { return n.toLocaleString(document.documentElement.lang); }
  function fill(template, values) {
    return template.replace(/\{(\w+)\}/g, function (_, k) { return values[k] !== undefined ? values[k] : ''; });
  }
  function file() { return D.files[fileIndex]; }
  function idx(n, m) { return (n - 1) * file().grid.size + (m - 1); }
  function sizeColor(e) {
    for (var i = 0; i < SIZE_COLORS.length; i++) if (e <= SIZE_COLORS[i][0]) return SIZE_COLORS[i][1];
    return SIZE_COLORS[SIZE_COLORS.length - 1][1];
  }
  function variantsOf(n, m) { return file().grid.v[n + '-' + m] || null; }
  function stringUrl(n, m, variant) {
    return D.root + 'files/' + D.slug + '/' + file().id + '/' + n + '-' + m + (variant ? '-' + variant : '') + '.txt';
  }

  function buildMatrix() {
    var g = file().grid;
    matrix.parentElement.style.setProperty('--size', g.size);  // .matrix-axes computes the cell size from it
    matrix.textContent = '';
    var head = document.createElement('div');
    head.setAttribute('role', 'row');
    var corner = document.createElement('span');
    corner.className = 'lbl';
    head.appendChild(corner);
    for (var m = 1; m <= g.size; m++) {
      var col = document.createElement('span');
      col.className = 'lbl';
      col.setAttribute('role', 'columnheader');
      col.textContent = m;
      head.appendChild(col);
    }
    matrix.appendChild(head);
    for (var n = 1; n <= g.size; n++) {
      var row = document.createElement('div');
      row.setAttribute('role', 'row');
      var rl = document.createElement('span');
      rl.className = 'lbl lbl-row';
      rl.setAttribute('role', 'rowheader');
      rl.textContent = n;
      row.appendChild(rl);
      for (var k = 1; k <= g.size; k++) {
        var b = document.createElement('button');
        b.type = 'button';
        b.setAttribute('role', 'gridcell');
        b.dataset.n = n;
        b.dataset.m = k;
        b.tabIndex = -1;
        var code = g.o[idx(n, k)];
        if (code === '-') { b.disabled = true; b.setAttribute('aria-disabled', 'true'); }
        row.appendChild(b);
      }
      matrix.appendChild(row);
    }
    colorMatrix();
  }

  function colorMatrix() {
    var g = file().grid;
    matrix.querySelectorAll('button').forEach(function (b) {
      var n = +b.dataset.n, m = +b.dataset.m, i = idx(n, m), code = g.o[i];
      if (code === '-') return;
      var origin = ORIGIN[code] || ORIGIN.u;
      b.style.setProperty('--c', state.mode === 'origin' ? origin.color : sizeColor(g.e[i]));
      var label = fill(T.cell_label, { n: n, m: m, origin: origin.name, e: fmt(g.e[i]) });
      b.setAttribute('aria-label', label);
      b.title = label;
    });
    document.querySelectorAll('[data-legend]').forEach(function (l) { l.hidden = l.dataset.legend !== state.mode; });
    document.querySelectorAll('[data-mode]').forEach(function (b) {
      b.setAttribute('aria-pressed', String(b.dataset.mode === state.mode));
    });
  }

  function fillSelects() {
    var size = file().grid.size;
    [selN, selM].forEach(function (sel) {
      if (sel.options.length === size) return;
      sel.textContent = '';
      for (var i = 1; i <= size; i++) sel.add(new Option(String(i), String(i)));
    });
  }

  function select(n, m, variant, focus) {
    var g = file().grid;
    n = Math.max(1, Math.min(g.size, n));
    m = Math.max(1, Math.min(g.size, m));
    var variants = variantsOf(n, m);
    state.n = n; state.m = m;
    state.variant = variants ? (variants.some(function (v) { return v[0] === variant; }) ? variant : variants[0][0]) : null;
    matrix.querySelectorAll('button[aria-selected]').forEach(function (b) {
      b.removeAttribute('aria-selected'); b.tabIndex = -1;
    });
    var cell = matrix.querySelector('button[data-n="' + n + '"][data-m="' + m + '"]');
    if (cell) {
      cell.setAttribute('aria-selected', 'true');
      cell.tabIndex = 0;
      if (focus) cell.focus();
    }
    selN.value = String(n); selM.value = String(m);
    showSelected();
    var hash = '#' + file().id + '/' + n + '/' + m + (state.variant ? '/' + state.variant : '');
    window.history.replaceState(null, '', window.location.pathname + window.location.search + hash);
  }

  function showSelected() {
    var f = file(), g = f.grid, n = state.n, m = state.m, i = idx(n, m), code = g.o[i];
    var origin = ORIGIN[code] || ORIGIN.u;
    var tier = D.lang === 'en' ? f.name : f.name.toLowerCase();
    $('sel-book').textContent = fill(T.book_tier, { tier: tier, n: g.sub[i] || n });
    $('sel-title').textContent = n + ' → ' + m;
    var badge = $('sel-origin');
    badge.textContent = origin.name;
    badge.style.setProperty('--c', origin.color);
    setStats(g.e[i], g.w[i], g.h[i]);
    var thr = g.t[i];
    $('sel-thr').textContent = thr ? fill(thr === 1 ? T.belts_one : T.belts_many, { n: thr }) : '—';
    var variants = variantsOf(n, m);
    var box = $('sel-variants');
    box.hidden = !variants;
    if (variants) {
      $('sel-variants-note').textContent = fill(T.variants_note, { n: variants.length });
      var holder = box.querySelector('.sel-variant-buttons');
      holder.textContent = '';
      variants.forEach(function (v) {
        var b = document.createElement('button');
        b.type = 'button';
        b.textContent = v[1];
        b.setAttribute('aria-pressed', String(v[0] === state.variant));
        b.addEventListener('click', function () { select(n, m, v[0], false); });
        holder.appendChild(b);
      });
    }
    var url = stringUrl(n, m, state.variant);
    var copy = $('sel-copy');
    copy.dataset.copy = url;
    var dl = $('sel-download');
    dl.href = url;
    dl.setAttribute('download', f.id + '-' + n + '-' + m + (state.variant ? '-' + state.variant : '') + '.txt');
    $('preview').setAttribute('aria-label', fill(T.preview_label, { n: n, m: m }));
    drawSelected(url);
  }

  function setStats(entities, w, h) {
    $('sel-ent').textContent = fmt(entities);
    $('sel-dim').textContent = w + ' × ' + h;
  }

  /* ---------- decode + draw ---------- */
  function decode(text) {
    if (!('DecompressionStream' in window)) return Promise.reject(new Error('no DecompressionStream'));
    var bin = window.atob(text.trim().slice(1));
    var bytes = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    var stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('deflate'));
    return new Response(stream).text().then(JSON.parse);
  }

  function load(url) {
    if (!cache[url]) {
      cache[url] = fetch(url).then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.text();
      }).then(decode);
      cache[url].catch(function () { delete cache[url]; });
    }
    return cache[url];
  }

  function drawSelected(url) {
    var token = ++renderToken;
    var preview = $('preview');
    var status = document.createElement('p');
    status.className = 'muted small';
    status.textContent = T.preview_loading;
    preview.replaceChildren(status);
    $('sel-desc').textContent = '…';
    $('sel-verif').hidden = true;
    load(url).then(function (data) {
      if (token !== renderToken) return;
      var bp = data.blueprint;
      var drawn = draw(bp.entities || []);
      preview.replaceChildren(drawn.svg);
      setStats((bp.entities || []).length, drawn.w, drawn.h);
      $('sel-desc').textContent = bp.description || '—';
      if (T.in_game) {
        var splitter = (bp.entities || []).some(function (e) { return /splitter$/.test(e.name); });
        var verif = $('sel-verif');
        verif.querySelector('span').textContent = splitter ? T.verif_splitter : T.verif_plain;
        verif.hidden = false;
      }
    }).catch(function () {
      if (token !== renderToken) return;
      status.textContent = T.preview_error;
      $('sel-desc').textContent = '—';
    });
  }

  var TIER = { '': '#e9c53f', 'fast-': '#e8604c', 'express-': '#4ea6e6' };
  var S = 15;  // pixels per tile

  function tierColor(name) {
    var m = name.match(/^(fast-|express-)?/);
    return TIER[m ? (m[1] || '') : ''] || '#4ea6e6';
  }

  function rot(x, y, deg) {
    var r = deg * Math.PI / 180, c = Math.cos(r), s = Math.sin(r);
    return [x * c - y * s, x * s + y * c];
  }

  function draw(entities) {
    var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    var shapes = entities.map(function (e) {
      var dir = e.direction || 0;
      var horizontal = dir === 4 || dir === 12;
      var kind = /splitter$/.test(e.name) ? 'splitter' : /underground-belt$/.test(e.name) ? 'underground'
        : /transport-belt$/.test(e.name) ? 'belt' : 'other';
      var w = kind === 'splitter' ? (horizontal ? 1 : 2) : 1;
      var h = kind === 'splitter' ? (horizontal ? 2 : 1) : 1;
      var x = e.position.x, y = e.position.y;
      minX = Math.min(minX, x - w / 2); maxX = Math.max(maxX, x + w / 2);
      minY = Math.min(minY, y - h / 2); maxY = Math.max(maxY, y + h / 2);
      return { kind: kind, x: x, y: y, w: w, h: h, angle: dir * 22.5, color: tierColor(e.name), type: e.type };
    });
    if (!shapes.length) { minX = minY = 0; maxX = maxY = 1; }
    var W = Math.round(maxX - minX), H = Math.round(maxY - minY);
    var chevrons = {}, bars = {}, boxes = '', others = '', lines = '';
    function P(v) { return v.toFixed(1); }
    shapes.forEach(function (s) {
      var cx = (s.x - minX) * S, cy = (s.y - minY) * S;
      if (s.kind === 'splitter') {
        var rw = s.w === 2 ? 26 : 6.3, rh = s.h === 2 ? 26 : 6.3;
        boxes += 'M' + P(cx - rw / 2) + ' ' + P(cy - rh / 2) + 'h' + P(rw) + 'v' + P(rh) + 'h' + P(-rw) + 'z';
        return;
      }
      if (s.kind === 'other') {
        others += 'M' + P(cx - 6) + ' ' + P(cy - 6) + 'h12v12h-12z';
        return;
      }
      var pts = [[-4.2, 1.9], [0, -1.9], [4.2, 1.9]].map(function (p) { return rot(p[0], p[1], s.angle); });
      chevrons[s.color] = (chevrons[s.color] || '') + 'M' + P(cx + pts[0][0]) + ' ' + P(cy + pts[0][1]) +
        'L' + P(cx + pts[1][0]) + ' ' + P(cy + pts[1][1]) + 'L' + P(cx + pts[2][0]) + ' ' + P(cy + pts[2][1]);
      if (s.kind === 'underground') {
        var by = s.type === 'input' ? -4.6 : 4.6;
        var a = rot(-5, by, s.angle), b = rot(5, by, s.angle);
        bars[s.color] = (bars[s.color] || '') + 'M' + P(cx + a[0]) + ' ' + P(cy + a[1]) + 'L' + P(cx + b[0]) + ' ' + P(cy + b[1]);
      }
    });
    for (var gx = 0; gx <= W; gx++) lines += 'M' + gx * S + ' 0V' + H * S;
    for (var gy = 0; gy <= H; gy++) lines += 'M0 ' + gy * S + 'H' + W * S;
    var NS = 'http://www.w3.org/2000/svg';
    var svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('viewBox', '-1 -1 ' + (W * S + 2) + ' ' + (H * S + 2));
    svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
    svg.setAttribute('aria-hidden', 'true');
    function path(d, attrs) {
      if (!d) return;
      var el = document.createElementNS(NS, 'path');
      el.setAttribute('d', d);
      Object.keys(attrs).forEach(function (k) { el.setAttribute(k, attrs[k]); });
      svg.appendChild(el);
    }
    path(lines, { stroke: 'rgba(255,255,255,0.07)', 'stroke-width': 1, fill: 'none' });
    Object.keys(chevrons).forEach(function (c) {
      path(chevrons[c], { stroke: c, 'stroke-width': 1.6, fill: 'none', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' });
    });
    Object.keys(bars).forEach(function (c) {
      path(bars[c], { stroke: c, 'stroke-width': 2.6, fill: 'none', 'stroke-linecap': 'round' });
    });
    path(others, { fill: '#6b645b' });
    path(boxes, { fill: '#efe9df' });
    return { svg: svg, w: W, h: H };
  }

  /* ---------- events ---------- */
  matrix.addEventListener('click', function (ev) {
    var b = ev.target.closest('button[data-n]');
    if (b && !b.disabled) select(+b.dataset.n, +b.dataset.m, null, false);
  });
  matrix.addEventListener('keydown', function (ev) {
    var moves = { ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] };
    var size = file().grid.size;
    if (moves[ev.key]) {
      ev.preventDefault();
      select(state.n + moves[ev.key][0], state.m + moves[ev.key][1], null, true);
    } else if (ev.key === 'Home' || ev.key === 'End') {
      ev.preventDefault();
      select(state.n, ev.key === 'Home' ? 1 : size, null, true);
    }
  });
  selN.addEventListener('change', function () { select(+selN.value, state.m, null, false); });
  selM.addEventListener('change', function () { select(state.n, +selM.value, null, false); });
  document.querySelectorAll('[data-mode]').forEach(function (b) {
    b.addEventListener('click', function () { state.mode = b.dataset.mode; colorMatrix(); });
  });
  $('sel-link').addEventListener('click', function () {
    FB.runCopy($('sel-link'), FB.copyText(window.location.href), FB.i18n.link_copied);
  });
  onFileChange.push(function () {
    fillSelects();
    buildMatrix();
    select(state.n, state.m, state.variant, false);
  });

  /* ---------- start: #<file>/<n>/<m>[/<variant>] wins over the remembered variant ---------- */
  var hash = window.location.hash.slice(1).split('/');
  var start = fileIndex;
  var fromHash = D.files.map(function (f) { return f.id; }).indexOf(hash[0]);
  if (fromHash >= 0) {
    start = fromHash;
    if (+hash[1]) state.n = +hash[1];
    if (+hash[2]) state.m = +hash[2];
    state.variant = hash[3] || null;
  } else {
    try {
      var saved2 = window.localStorage.getItem(storeKey);
      if (saved2 !== null && D.files[+saved2]) start = +saved2;
    } catch (e) { /* private mode */ }
  }
  setFile(start, false);
})();
