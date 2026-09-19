/* Shared behaviour: phone menu, copy buttons, image gallery. No dependencies. */
(function () {
  'use strict';

  var I18N = JSON.parse(document.getElementById('i18n').textContent);
  var live = document.getElementById('live');  // a visible toast that is also a polite live region

  function announce(message, isError) {
    live.textContent = '';
    live.hidden = false;
    live.classList.toggle('toast-error', !!isError);
    window.setTimeout(function () { live.textContent = message; }, 60);
    window.clearTimeout(live._hide);
    live._hide = window.setTimeout(function () { live.hidden = true; }, isError ? 6000 : 2600);
  }

  /* ---------- language switch keeps the catalog filters and the selected balancer ---------- */
  document.querySelectorAll('.lang a').forEach(function (a) {
    a.addEventListener('click', function () {
      a.href = a.href.split(/[?#]/)[0] + window.location.search + window.location.hash;
    });
  });

  /* ---------- phone menu ---------- */
  var bar = document.querySelector('[data-menu]');
  var menuButton = bar && bar.querySelector('.menu-btn');
  function setMenu(open) {
    bar.toggleAttribute('data-open', open);
    menuButton.setAttribute('aria-expanded', String(open));
    menuButton.setAttribute('aria-label', open ? menuButton.dataset.labelClose : menuButton.dataset.labelOpen);
  }
  if (menuButton) {
    menuButton.addEventListener('click', function () { setMenu(!bar.hasAttribute('data-open')); });
    document.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape' && bar.hasAttribute('data-open')) { setMenu(false); menuButton.focus(); }
    });
  }

  /* ---------- clipboard ---------- */
  function fetchText(url) {
    return fetch(url).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.text();
    }).then(function (text) { return text.trim(); });
  }

  function legacyCopy(text) {
    var area = document.createElement('textarea');
    area.value = text;
    area.setAttribute('readonly', '');
    area.style.position = 'fixed';
    area.style.opacity = '0';
    document.body.appendChild(area);
    area.select();
    var ok = false;
    try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
    area.remove();
    return ok ? Promise.resolve() : Promise.reject(new Error('copy failed'));
  }

  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text).catch(function () { return legacyCopy(text); });
    }
    return legacyCopy(text);
  }

  /* Safari only allows clipboard writes inside the click, so the download is handed over as a promise. */
  function copyFromUrl(url) {
    var text = fetchText(url);
    if (navigator.clipboard && window.ClipboardItem) {
      try {
        var item = new ClipboardItem({
          'text/plain': text.then(function (t) { return new Blob([t], { type: 'text/plain' }); })
        });
        return navigator.clipboard.write([item]).catch(function () { return text.then(copyText); });
      } catch (e) { /* ClipboardItem without promise support: fall through */ }
    }
    return text.then(copyText);
  }

  function setFeedback(button, message, state) {
    var label = button.querySelector('[data-copy-label]');
    var date = !label && button.closest('.card-actions') && button.closest('.card-actions').querySelector('.card-date');
    var target = label || date;
    if (target && !('original' in target.dataset)) target.dataset.original = target.textContent;
    if (target) target.textContent = message;
    if (state) button.dataset.state = state; else delete button.dataset.state;
    window.clearTimeout(button._reset);
    if (state) {
      button._reset = window.setTimeout(function () {
        if (target) target.textContent = target.dataset.original;
        delete button.dataset.state;
      }, 2500);
    }
  }

  function runCopy(button, promise, doneMessage) {
    setFeedback(button, I18N.copying, null);
    button.setAttribute('aria-busy', 'true');
    return promise.then(function () {
      setFeedback(button, doneMessage, 'done');
      announce(doneMessage, false);
    }, function () {
      setFeedback(button, I18N.copy_failed, 'error');
      announce(I18N.copy_failed, true);
    }).then(function () { button.removeAttribute('aria-busy'); });
  }

  document.addEventListener('click', function (ev) {
    var button = ev.target.closest('[data-copy]');
    if (!button || !button.dataset.copy) return;
    ev.preventDefault();
    runCopy(button, copyFromUrl(button.dataset.copy), I18N.copied);
  });

  /* ---------- gallery ---------- */
  document.querySelectorAll('[data-gallery]').forEach(function (gallery) {
    var img = gallery.querySelector('[data-gallery-img]');
    var link = gallery.querySelector('[data-gallery-link]');
    var full = gallery.querySelector('[data-gallery-full]');
    gallery.addEventListener('click', function (ev) {
      var thumb = ev.target.closest('[data-thumb]');
      if (!thumb) return;
      ev.preventDefault();
      img.width = +thumb.dataset.w;
      img.height = +thumb.dataset.h;
      img.sizes = thumb.dataset.sizes;
      img.srcset = thumb.dataset.srcset;
      img.src = thumb.dataset.src;
      img.alt = thumb.dataset.alt;
      link.href = full.href = thumb.href;
      gallery.querySelectorAll('[data-thumb]').forEach(function (t) { t.removeAttribute('aria-current'); });
      thumb.setAttribute('aria-current', 'true');
    });
  });

  window.FB = { announce: announce, copyText: copyText, copyFromUrl: copyFromUrl, runCopy: runCopy, i18n: I18N };
})();
