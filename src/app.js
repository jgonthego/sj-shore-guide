/* South Jersey Shore Town Guide: vanilla JS, no dependencies.
   - mobile nav
   - "Ask Google AI" box (opens Google AI Mode, udm=50, in a new tab)
   - distance / category / weekend explorer (haversine, approx straight-line miles)
   - town & table filters, sortable tables */
(function () {
  'use strict';
  var t = document.querySelector('.navtoggle'), nav = document.getElementById('nav');
  if (t && nav) t.addEventListener('click', function () {
    var o = nav.classList.toggle('open'); t.setAttribute('aria-expanded', o ? 'true' : 'false');
  });

  /* ---------- Ask Google AI ---------- */
  document.querySelectorAll('form[data-askai]').forEach(function (f) {
    f.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var q = (f.querySelector('input[name=q]').value || '').trim();
      if (!q) return;
      var url = 'https://www.google.com/search?udm=50&q=' + encodeURIComponent(q + ' South Jersey shore');
      window.open(url, '_blank', 'noopener');
    });
  });

  /* ---------- explorer ---------- */
  function haversine(a, b, c, d) {
    var R = 3958.8, r = Math.PI / 180, dp = (c - a) * r, dl = (d - b) * r;
    var h = Math.sin(dp / 2) * Math.sin(dp / 2) + Math.cos(a * r) * Math.cos(c * r) * Math.sin(dl / 2) * Math.sin(dl / 2);
    return 2 * R * Math.asin(Math.sqrt(h));
  }
  function iso(d) { return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2); }
  function weekend() {
    var n = new Date(), wd = n.getDay(), s = new Date(n), e;
    if (wd === 6 || wd === 0) { e = new Date(n); e.setDate(n.getDate() + (wd === 6 ? 1 : 0)); }
    else { s.setDate(n.getDate() + (5 - wd)); e = new Date(s); e.setDate(s.getDate() + 2); }
    return [iso(s), iso(e)];
  }

  document.querySelectorAll('[data-explorer]').forEach(function (X) {
    var sel = X.querySelector('[data-origin]'), status = X.querySelector('[data-geostatus]');
    var params = new URLSearchParams(location.search);
    var today = iso(new Date()), wk = weekend();
    var state = { lat: null, lon: null, label: '', r: 30, cat: '', wk: false, slug: 'linwood' };
    var limits = {};

    function setOriginFromSelect() {
      var o = sel.options[sel.selectedIndex];
      if (!o || o.value === 'geo') return false;
      state.lat = parseFloat(o.dataset.lat); state.lon = parseFloat(o.dataset.lon); state.label = o.textContent; state.slug = o.value;
      return true;
    }
    var from = params.get('from') || (window.localStorage && localStorage.getItem('sjFrom'));
    if (from && sel.querySelector('option[value="' + from + '"]') && from !== 'geo') sel.value = from;
    setOriginFromSelect();
    var pr = params.get('r'); if (pr !== null && !isNaN(parseInt(pr, 10))) state.r = parseInt(pr, 10);
    if (params.get('cat')) state.cat = params.get('cat');
    if (params.get('wk') === '1') state.wk = true;

    function syncButtons() {
      X.querySelectorAll('.rad').forEach(function (b) { b.setAttribute('aria-pressed', parseInt(b.dataset.r, 10) === state.r ? 'true' : 'false'); });
      X.querySelectorAll('.chip-btn').forEach(function (b) { var on = b.dataset.cat === state.cat; b.classList.toggle('on', on); b.setAttribute('aria-pressed', on ? 'true' : 'false'); });
      var w = X.querySelector('[data-weekend]'); if (w) w.setAttribute('aria-pressed', state.wk ? 'true' : 'false');
    }
    function saveUrl() {
      try {
        var p = new URLSearchParams(location.search);
        if (state.slug && state.slug !== 'geo') p.set('from', state.slug); else p.delete('from');
        p.set('r', state.r); if (state.cat) p.set('cat', state.cat); else p.delete('cat');
        if (state.wk) p.set('wk', '1'); else p.delete('wk');
        history.replaceState(null, '', location.pathname + '?' + p.toString() + location.hash);
        if (state.slug !== 'geo') localStorage.setItem('sjFrom', state.slug);
      } catch (e) { /* ignore */ }
    }
    function apply() {
      X.querySelectorAll('[data-sec]').forEach(function (sec) {
        var list = sec.querySelector('[data-list]'), cards = Array.prototype.slice.call(list.children);
        var lim = limits[sec.dataset.sec] || parseInt(list.dataset.limit || '24', 10);
        var vis = [];
        cards.forEach(function (c) {
          var lat = parseFloat(c.dataset.lat), lon = parseFloat(c.dataset.lon), d = null;
          if (!isNaN(lat) && !isNaN(lon) && state.lat !== null) d = haversine(state.lat, state.lon, lat, lon);
          c._d = d;
          var ds = c.querySelector('[data-dist]'); if (ds) ds.textContent = d === null ? 'distance n/a' : '≈ ' + Math.round(d) + ' mi';
          var ok = true;
          if (state.r > 0) ok = d !== null && d <= state.r;
          if (ok && state.cat) ok = c.dataset.cat === state.cat;
          if (ok && c.dataset.type === 'event') {
            if (c.dataset.end < today) ok = false;
            if (ok && state.wk) ok = c.dataset.start <= wk[1] && c.dataset.end >= wk[0];
          }
          c._ok = ok; if (ok) vis.push(c);
        });
        vis.sort(function (a, b) {
          if (a.dataset.type === 'event') return a.dataset.start < b.dataset.start ? -1 : a.dataset.start > b.dataset.start ? 1 : (a._d || 999) - (b._d || 999);
          return (a._d || 999) - (b._d || 999);
        });
        cards.forEach(function (c) { if (!c._ok) { c.hidden = true; list.appendChild(c); } });
        vis.forEach(function (c, i) { list.appendChild(c); c.hidden = i >= lim; });
        cards.forEach(function (c) { if (!c._ok) list.appendChild(c); });
        var cnt = sec.querySelector('[data-count]'), noun = sec.dataset.sec === 'event' ? 'event' : 'place';
        var where = state.r > 0 ? ' within ' + state.r + ' mi of ' + state.label : ' (any distance)';
        if (cnt) cnt.textContent = vis.length + ' ' + noun + (vis.length === 1 ? '' : 's') + where + (state.wk && noun === 'event' ? ', this weekend' : '');
        var em = sec.querySelector('[data-empty]'); if (em) em.hidden = vis.length > 0;
        var more = sec.querySelector('[data-more]');
        if (more) { more.hidden = vis.length <= lim; more.textContent = 'Show more (' + (vis.length - lim) + ' left)'; }
      });
      syncButtons(); saveUrl();
    }
    sel.addEventListener('change', function () {
      if (sel.value === 'geo') {
        if (!navigator.geolocation) { status.textContent = 'Location not available in this browser.'; sel.value = state.slug || 'linwood'; return; }
        status.textContent = 'Finding you…';
        navigator.geolocation.getCurrentPosition(function (pos) {
          state.lat = pos.coords.latitude; state.lon = pos.coords.longitude; state.label = 'your location'; state.slug = 'geo';
          status.textContent = 'Using your location (stays in your browser).'; apply();
        }, function () {
          status.textContent = 'Couldn\u2019t get your location. Pick a town instead.';
          sel.value = (state.slug && state.slug !== 'geo') ? state.slug : 'linwood'; setOriginFromSelect(); apply();
        }, { enableHighAccuracy: false, timeout: 10000, maximumAge: 600000 });
        return;
      }
      status.textContent = ''; setOriginFromSelect(); limits = {}; apply();
    });
    X.querySelectorAll('.rad').forEach(function (b) { b.addEventListener('click', function () { state.r = parseInt(b.dataset.r, 10); limits = {}; apply(); }); });
    X.querySelectorAll('.chip-btn').forEach(function (b) { b.addEventListener('click', function () { state.cat = b.dataset.cat; limits = {}; apply(); }); });
    var w = X.querySelector('[data-weekend]'); if (w) w.addEventListener('click', function () { state.wk = !state.wk; limits = {}; apply(); });
    X.querySelectorAll('[data-sec]').forEach(function (sec) {
      var more = sec.querySelector('[data-more]'), list = sec.querySelector('[data-list]');
      if (more) more.addEventListener('click', function () {
        var k = sec.dataset.sec; limits[k] = (limits[k] || parseInt(list.dataset.limit, 10)) + parseInt(list.dataset.limit, 10); apply();
      });
    });
    X.classList.add('js-on');
    apply();
  });

  /* ---------- town / table filters ---------- */
  document.querySelectorAll('.filters').forEach(function (bar) {
    var target = document.querySelector(bar.getAttribute('data-target'));
    if (!target) return;
    var state = { q: '', county: '', free: false, dog: false, verified: false, ocean: false };
    var count = bar.querySelector('.fcount');
    function apply() {
      var shown = 0, all = 0;
      target.querySelectorAll(':scope > [data-county]').forEach(function (el) {
        all++;
        var ok = (!state.q || el.dataset.name.indexOf(state.q) !== -1) && (!state.county || el.dataset.county === state.county) &&
          (!state.free || el.dataset.free === '1') && (!state.dog || el.dataset.dog === '1') &&
          (!state.verified || el.dataset.status === 'verified') && (!state.ocean || el.dataset.kind === 'ocean');
        el.classList.toggle('hidden', !ok); if (ok) shown++;
      });
      if (count) count.textContent = 'Showing ' + shown + ' of ' + all + ' towns';
    }
    var q = bar.querySelector('[data-f=q]');
    if (q) q.addEventListener('input', function () { state.q = q.value.trim().toLowerCase(); apply(); });
    bar.querySelectorAll('button[data-county]').forEach(function (b) {
      b.addEventListener('click', function () {
        bar.querySelectorAll('button[data-county]').forEach(function (x) { x.classList.remove('on'); });
        b.classList.add('on'); state.county = b.dataset.county; apply();
      });
    });
    bar.querySelectorAll('[data-toggle]').forEach(function (b) {
      b.addEventListener('click', function () { var k = b.dataset.toggle; state[k] = !state[k]; b.setAttribute('aria-pressed', state[k] ? 'true' : 'false'); apply(); });
    });
    var p = new URLSearchParams(location.search);
    ['free', 'dog', 'verified', 'ocean'].forEach(function (k) {
      if (p.get(k) === '1') { state[k] = true; var b = bar.querySelector('[data-toggle=' + k + ']'); if (b) b.setAttribute('aria-pressed', 'true'); }
    });
    if (p.get('county')) { var cb = bar.querySelector('button[data-county="' + p.get('county') + '"]'); if (cb) cb.click(); }
    apply();
  });

  document.querySelectorAll('table.sortable').forEach(function (tbl) {
    tbl.querySelectorAll('th').forEach(function (th, i) {
      var asc = true; th.tabIndex = 0; th.setAttribute('role', 'button');
      function sort() {
        var tb = tbl.tBodies[0], rows = Array.prototype.slice.call(tb.rows);
        rows.sort(function (a, b) {
          var x = a.cells[i].dataset.v, y = b.cells[i].dataset.v, nx = parseFloat(x), ny = parseFloat(y);
          var r = (!isNaN(nx) && !isNaN(ny)) ? nx - ny : String(x).localeCompare(String(y));
          return asc ? r : -r;
        });
        rows.forEach(function (r) { tb.appendChild(r); }); asc = !asc;
      }
      th.addEventListener('click', sort);
      th.addEventListener('keydown', function (ev) { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); sort(); } });
    });
  });
})();
