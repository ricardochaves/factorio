/* Google Analytics 4 behind a consent choice: nothing from Google is requested until the visitor accepts.
   The choice is kept in localStorage and can be changed from the footer. No dependencies. */
(function () {
  'use strict';

  var tag = document.currentScript;
  var ID = tag.dataset.id;             // GA4 measurement id
  var HOST = tag.dataset.host;         // the only host allowed to send data: localhost, previews and forks stay silent
  var PATH = tag.dataset.path || '/';  // '/factorio': the cookies are not sent to the owner's other project sites
  var BASE = PATH === '/' ? '/' : PATH + '/';
  var KEY = 'fb-consent';
  var MONTHS_13 = 395 * 86400;         // seconds: the cookie lifetime, and how long a choice is remembered
  var banner = document.getElementById('consent');  // absent on the 404 page: it only loads GA if already accepted
  var opener = null;
  var injected = false;  // gtag.js was added to this page and cannot be removed again
  var on = false;        // events may be sent
  var wanted = false;    // the visitor's latest answer: a decline before the load event must win over an earlier accept

  /* ---------- the remembered choice ---------- */
  function stored() {
    try {
      var s = JSON.parse(window.localStorage.getItem(KEY));
      if (s && s.v === 1 && (s.choice === 'granted' || s.choice === 'denied') && Date.now() - s.at < MONTHS_13 * 1000) {
        return s.choice;
      }
    } catch (e) { /* storage blocked or corrupt: ask again */ }
    return null;
  }

  function store(choice) {
    try { window.localStorage.setItem(KEY, JSON.stringify({ v: 1, choice: choice, at: Date.now() })); } catch (e) { /* ignore */ }
  }

  /* ---------- Google Analytics ---------- */
  function start() {
    if (location.hostname !== HOST) return;
    window['ga-disable-' + ID] = false;
    on = true;
    if (injected) return;
    injected = true;
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag('consent', 'default', {
      analytics_storage: 'granted', ad_storage: 'denied', ad_user_data: 'denied', ad_personalization: 'denied'
    });
    window.gtag('js', new Date());
    window.gtag('config', ID, {
      cookie_domain: 'none', cookie_path: PATH, cookie_expires: MONTHS_13, cookie_flags: 'SameSite=Lax;Secure',
      allow_google_signals: false, allow_ad_personalization_signals: false
    });
    var script = document.createElement('script');
    script.async = true;
    script.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(ID);
    document.head.appendChild(script);
  }

  function clearCookies() {
    document.cookie.split(';').forEach(function (pair) {
      var name = pair.split('=')[0].trim();
      if (name !== '_ga' && name.indexOf('_ga_') !== 0) return;
      var gone = name + '=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=' + PATH;
      document.cookie = gone;
      document.cookie = gone + '; domain=' + HOST;
    });
  }

  function stop() {
    on = false;
    window['ga-disable-' + ID] = true;  // best effort: the automatic events (scroll, clicks) ignore it, the reload does not
    clearCookies();
  }

  /* After the page has loaded, so the script never competes with the content. */
  function whenLoaded(fn) {
    if (document.readyState === 'complete') fn(); else window.addEventListener('load', fn, { once: true });
  }

  /* ---------- the banner ---------- */
  /* While the banner floats over the page, --consent-h keeps the footer, the focus and the toast clear of it. */
  function layout() {
    var h = 0;
    if (banner && !banner.hidden && window.getComputedStyle(banner).position === 'fixed') h = banner.offsetHeight + 16;
    document.documentElement.style.setProperty('--consent-h', h + 'px');
  }

  function show(focus) {
    if (!banner) return;
    banner.hidden = false;
    layout();
    // floating: it is already on screen; in the flow (short screens) it sits at the top, so let the browser scroll to it
    if (focus) banner.focus({ preventScroll: window.getComputedStyle(banner).position === 'fixed' });
  }

  function hide() {
    if (!banner) return;
    banner.hidden = true;
    layout();
  }

  function choose(choice) {
    wanted = choice === 'granted';
    store(choice);
    hide();
    if (wanted) {
      start();
    } else {
      var running = injected;
      stop();
      // gtag.js cannot be unloaded, so its scroll and click listeners would keep sending: a reload is the only way out
      if (running) { window.location.reload(); return; }
    }
    if (opener) { opener.focus(); opener = null; }
  }

  /* An answer given in another tab, or before this page came back from the back/forward cache, must reach this page. */
  function sync() {
    var now = stored();
    if (now === 'denied') {
      wanted = false;
      if (injected) { stop(); window.location.reload(); } else { hide(); }
    } else if (now === 'granted') {
      wanted = true;
      hide();
      whenLoaded(function () { if (wanted) start(); });
    }
  }

  document.addEventListener('click', function (ev) {
    var open = ev.target.closest('[data-consent-open]');
    if (open) { opener = open; show(true); return; }
    var pick = ev.target.closest('[data-consent]');
    if (pick && banner && banner.contains(pick)) choose(pick.dataset.consent);
  });

  window.addEventListener('storage', function (ev) {
    if (ev.key !== KEY && ev.key !== null) return;
    // the record was removed or the site data cleared in another tab: without a granted choice GA must go
    if (injected && stored() === null) { stop(); window.location.reload(); return; }
    sync();
  });
  window.addEventListener('pageshow', function (ev) { if (ev.persisted) sync(); });
  window.addEventListener('resize', layout);
  if (banner && window.ResizeObserver) new ResizeObserver(layout).observe(banner);

  /* Copies of a blueprint: site.js announces them, only the file name goes to GA. */
  document.addEventListener('fb:copy', function (ev) {
    if (!on) return;
    try {
      var file = new URL(ev.detail.file, window.location.href).pathname;
      if (file.indexOf(BASE) === 0) file = file.slice(BASE.length);
      window.gtag('event', 'copy_blueprint', { blueprint_file: file });
    } catch (e) { /* ignore */ }
  });

  document.querySelectorAll('[data-consent-open]').forEach(function (b) { b.hidden = false; });

  var choice = stored();
  wanted = choice === 'granted';
  if (wanted) {
    whenLoaded(function () { if (wanted) start(); });
  } else {
    clearCookies();  // leftovers, for example from the unload beacon of the page that was reloaded after declining
    if (choice === null) show(false);
  }
})();
