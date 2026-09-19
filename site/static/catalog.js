/* Catalog page: search, filters with counts, sorting, grid or list view. The cards are already in the HTML. */
(function () {
  'use strict';

  var DATA = JSON.parse(document.getElementById('catalog-data').textContent);
  var ITEMS = DATA.items;
  var grid = document.getElementById('results');
  var cards = {};
  grid.querySelectorAll('.card[data-slug]').forEach(function (card) {
    var link = card.querySelector('.card-title a');
    cards[card.dataset.slug] = { el: card, link: link, href: link.getAttribute('href') };
  });
  var input = document.getElementById('q');
  var sortSelect = document.getElementById('sort');
  var countEl = document.getElementById('count');
  var countLabel = document.getElementById('count-label');
  var clearBtn = document.getElementById('clear');
  var empty = document.getElementById('empty');
  var emptyText = document.getElementById('empty-text');
  var SINGLE = ['cat', 'kind', 'test'];
  var MULTI = ['phase', 'city', 'uses'];
  var STOP = ['de', 'da', 'do', 'das', 'dos', 'e', 'para', 'com', 'a', 'o', 'as', 'os', 'to', 'the', 'of', 'and',
    'for', 'with', 'el', 'la', 'los', 'las', 'en', 'con', 'del', 'y', 'un', 'una', 'um', 'uma'];
  var PAIR = /(\d+)\s*(?:para|to|a|x|×|->|→)\s*(\d+)/;

  var state = { q: '', cat: 'all', kind: 'all', test: 'all', phase: [], city: [], uses: [], sort: 'recent', view: 'grid' };

  function normalize(s) {
    return s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  }

  function parseQuery(q) {
    var text = normalize(q);
    var pair = null;
    var m = text.match(PAIR);
    if (m) { pair = [+m[1], +m[2]]; text = text.replace(m[0], ' '); }
    var tokens = text.split(/[\s,.;:/()!?"']+/).filter(function (t) { return t && STOP.indexOf(t) < 0; });
    return { pair: pair, tokens: tokens };
  }

  function has(list, value) { return list.indexOf(value) >= 0; }

  function valuesOf(item, group) {
    if (group === 'uses') return item.uses;
    return item.tags;  // phase and city block come from tags
  }

  /* skip: the filter group left out, so each option can count what it would add */
  function matches(item, query, skip) {
    for (var i = 0; i < SINGLE.length; i++) {
      var g = SINGLE[i];
      if (g !== skip && state[g] !== 'all' && item[g] !== state[g]) return false;
    }
    for (var j = 0; j < MULTI.length; j++) {
      var mg = MULTI[j];
      if (mg === skip || !state[mg].length) continue;
      var values = valuesOf(item, mg);
      if (!state[mg].some(function (v) { return has(values, v); })) return false;
    }
    if (query.pair) {
      if (!item.nxm || query.pair[0] < 1 || query.pair[1] < 1 ||
          query.pair[0] > item.nxm.size || query.pair[1] > item.nxm.size) return false;
    }
    return query.tokens.every(function (t) { return item.text.indexOf(t) >= 0; });
  }

  function optionMatches(item, group, value) {
    if (value === 'all') return true;
    if (has(SINGLE, group)) return item[group] === value;
    return has(valuesOf(item, group), value);
  }

  function compare(a, b) {
    if (state.sort === 'name') return a.title.localeCompare(b.title, document.documentElement.lang);
    if (state.sort === 'size') return b.size - a.size;
    return (b.date || '').localeCompare(a.date || '') || a.title.localeCompare(b.title, document.documentElement.lang);
  }

  function render() {
    var query = parseQuery(state.q);
    var shown = ITEMS.filter(function (it) { return matches(it, query, null); }).sort(compare);
    var visible = {};
    shown.forEach(function (it) {
      visible[it.slug] = true;
      var card = cards[it.slug];
      grid.appendChild(card.el);  // re-order
      card.link.setAttribute('href', query.pair && it.nxm
        ? card.href + '#' + it.nxm.file + '/' + query.pair[0] + '/' + query.pair[1] : card.href);
    });
    Object.keys(cards).forEach(function (slug) { cards[slug].el.hidden = !visible[slug]; });

    document.querySelectorAll('[data-filter]').forEach(function (btn) {
      var group = btn.dataset.filter;
      var value = btn.dataset.value;
      var pressed = has(SINGLE, group) ? state[group] === value : has(state[group], value);
      btn.setAttribute('aria-pressed', String(pressed));
      var countSpan = btn.querySelector('[data-count]');
      if (countSpan) {
        var n = ITEMS.filter(function (it) { return matches(it, query, group) && optionMatches(it, group, value); }).length;
        countSpan.textContent = String(n);
        btn.toggleAttribute('data-zero', n === 0 && !pressed);
      }
    });

    countEl.textContent = String(shown.length);
    countLabel.textContent = shown.length === 1 ? DATA.labels.one : DATA.labels.many;
    var filtered = !!state.q.trim() || SINGLE.some(function (g) { return state[g] !== 'all'; }) ||
      MULTI.some(function (g) { return state[g].length; });
    clearBtn.hidden = !filtered;
    empty.hidden = shown.length > 0;
    if (!shown.length) {
      var onlyCategory = state.cat !== 'all' && !state.q.trim() && state.kind === 'all' && state.test === 'all' &&
        MULTI.every(function (g) { return !state[g].length; });
      emptyText.textContent = onlyCategory
        ? DATA.labels.empty_category.replace('{cat}', DATA.cat_names[DATA.cats.indexOf(state.cat)])
        : DATA.labels.empty;
    }
    grid.dataset.view = state.view;
    document.querySelectorAll('[data-view]').forEach(function (b) {
      if (b !== grid) b.setAttribute('aria-pressed', String(b.dataset.view === state.view));
    });
    writeUrl();
  }

  /* ---------- URL <-> state ---------- */
  /* only values that exist as filter buttons or sort options are accepted from the URL */
  function allowed(group) {
    return Array.prototype.map.call(document.querySelectorAll('[data-filter="' + group + '"]'),
      function (b) { return b.dataset.value; });
  }

  function readUrl() {
    var p = new URLSearchParams(window.location.search);
    state.q = p.get('q') || '';
    SINGLE.forEach(function (g) { if (has(allowed(g), p.get(g))) state[g] = p.get(g); });
    MULTI.forEach(function (g) {
      var ok = allowed(g);
      state[g] = (p.get(g) || '').split(',').filter(function (v) { return has(ok, v); });
    });
    var sorts = Array.prototype.map.call(sortSelect.options, function (o) { return o.value; });
    if (has(sorts, p.get('sort'))) state.sort = p.get('sort');
  }

  function writeUrl() {
    var p = new URLSearchParams();
    if (state.q.trim()) p.set('q', state.q.trim());
    SINGLE.forEach(function (g) { if (state[g] !== 'all') p.set(g, state[g]); });
    MULTI.forEach(function (g) { if (state[g].length) p.set(g, state[g].join(',')); });
    if (state.sort !== 'recent') p.set('sort', state.sort);
    var qs = p.toString();
    window.history.replaceState(null, '', window.location.pathname + (qs ? '?' + qs : ''));
  }

  /* ---------- events ---------- */
  document.addEventListener('click', function (ev) {
    var btn = ev.target.closest('[data-filter]');
    if (btn) {
      var group = btn.dataset.filter;
      var value = btn.dataset.value;
      if (has(SINGLE, group)) {
        state[group] = state[group] === value && value !== 'all' ? 'all' : value;
      } else {
        state[group] = has(state[group], value)
          ? state[group].filter(function (v) { return v !== value; }) : state[group].concat([value]);
      }
      render();
      return;
    }
    var viewBtn = ev.target.closest('button[data-view]');
    if (viewBtn) {
      state.view = viewBtn.dataset.view;
      try { window.localStorage.setItem('fb-view', state.view); } catch (e) { /* private mode */ }
      render();
    }
  });

  var timer;
  input.addEventListener('input', function () {
    window.clearTimeout(timer);
    timer = window.setTimeout(function () { state.q = input.value; render(); }, 120);
  });
  sortSelect.addEventListener('change', function () { state.sort = sortSelect.value; render(); });
  clearBtn.addEventListener('click', function () {
    state.q = ''; input.value = '';
    SINGLE.forEach(function (g) { state[g] = 'all'; });
    MULTI.forEach(function (g) { state[g] = []; });
    render();
    input.focus();
  });

  var filters = document.getElementById('filters');
  var toggle = filters.querySelector('.filters-toggle');
  toggle.addEventListener('click', function () {
    var open = !filters.hasAttribute('data-open');
    filters.toggleAttribute('data-open', open);
    toggle.setAttribute('aria-expanded', String(open));
  });

  readUrl();
  try { state.view = window.localStorage.getItem('fb-view') || 'grid'; } catch (e) { state.view = 'grid'; }
  input.value = state.q;
  sortSelect.value = state.sort;
  render();
})();
