/* Vanilla JS: mobile nav, card/table filters, sortable table. No dependencies. */
(function () {
  var t = document.querySelector('.navtoggle'), nav = document.getElementById('nav');
  if (t && nav) t.addEventListener('click', function () {
    var o = nav.classList.toggle('open'); t.setAttribute('aria-expanded', o ? 'true' : 'false');
  });

  document.querySelectorAll('.filters').forEach(function (bar) {
    var target = document.querySelector(bar.getAttribute('data-target'));
    if (!target) return;
    var state = { q: '', county: '', free: false, dog: false, verified: false, ocean: false };
    var items = function () { return target.querySelectorAll('[data-county]'); };
    var count = bar.querySelector('.fcount');
    function apply() {
      var shown = 0, all = 0;
      items().forEach(function (el) {
        all++;
        var ok = (!state.q || el.dataset.name.indexOf(state.q) !== -1) &&
          (!state.county || el.dataset.county === state.county) &&
          (!state.free || el.dataset.free === '1') &&
          (!state.dog || el.dataset.dog === '1') &&
          (!state.verified || el.dataset.status === 'verified') &&
          (!state.ocean || el.dataset.kind === 'ocean');
        el.classList.toggle('hidden', !ok);
        if (ok) shown++;
      });
      if (count) count.textContent = 'Showing ' + shown + ' of ' + all + ' towns';
    }
    var q = bar.querySelector('[data-f=q]');
    if (q) q.addEventListener('input', function () { state.q = q.value.trim().toLowerCase(); apply(); });
    bar.querySelectorAll('[data-county]').forEach(function (b) {
      b.addEventListener('click', function () {
        bar.querySelectorAll('[data-county]').forEach(function (x) { x.classList.remove('on'); });
        b.classList.add('on'); state.county = b.dataset.county; apply();
      });
    });
    bar.querySelectorAll('[data-toggle]').forEach(function (b) {
      b.addEventListener('click', function () {
        var k = b.dataset.toggle; state[k] = !state[k];
        b.setAttribute('aria-pressed', state[k] ? 'true' : 'false'); apply();
      });
    });
    // deep links: ?free=1&dog=1&county=Atlantic
    var p = new URLSearchParams(location.search);
    ['free', 'dog', 'verified', 'ocean'].forEach(function (k) {
      if (p.get(k) === '1') { state[k] = true; var b = bar.querySelector('[data-toggle=' + k + ']'); if (b) b.setAttribute('aria-pressed', 'true'); }
    });
    if (p.get('county')) { var cb = bar.querySelector('[data-county="' + p.get('county') + '"]'); if (cb) cb.click(); }
    apply();
  });

  document.querySelectorAll('table.sortable').forEach(function (tbl) {
    tbl.querySelectorAll('th').forEach(function (th, i) {
      var asc = true;
      th.addEventListener('click', function () {
        var tb = tbl.tBodies[0], rows = Array.prototype.slice.call(tb.rows);
        rows.sort(function (a, b) {
          var x = a.cells[i].dataset.v, y = b.cells[i].dataset.v, nx = parseFloat(x), ny = parseFloat(y);
          var r = (!isNaN(nx) && !isNaN(ny)) ? nx - ny : String(x).localeCompare(String(y));
          return asc ? r : -r;
        });
        rows.forEach(function (r) { tb.appendChild(r); }); asc = !asc;
      });
    });
  });
})();
