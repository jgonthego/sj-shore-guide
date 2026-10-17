/* South Jersey Shore Town Guide: live-weather background. Vanilla JS, no dependencies, no API key.
   Data: US National Weather Service API (api.weather.gov), public domain, CORS-enabled.
     1. /points/{lat},{lon}            -> nearest observation stations + hourly forecast URL (cached 7 days)
     2. /stations/{id}/observations/latest   (cached 15 min; falls back to the hourly forecast)
   Location: ?from= town, else the distance filter's saved town (localStorage sjFrom), else Linwood.
   Device geolocation is never sent. Fails silently to the static Dark Glass look.
   Preview: ?wx=clear-day | clear-night | partly | cloudy | rain | storm | snow | fog | windy | off
            (combine with commas or dashes, e.g. ?wx=rain-night, ?wx=cloudy,windy) */
(function () {
  'use strict';
  var root = document.documentElement;
  var hero = document.querySelector('[data-wx-hero], .phero, .thero');
  if (!hero || !window.fetch) return;

  var API = 'https://api.weather.gov', TTL = 15 * 60e3, PT_TTL = 7 * 864e5, STALE_OBS = 2.5 * 36e5;
  var RM = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)');
  var towns = {};
  try { towns = JSON.parse((document.getElementById('sj-towns') || {}).textContent || '{}'); } catch (e) { /* ignore */ }
  var DEF = 'linwood';
  var params = new URLSearchParams(location.search);

  function ls(k, v) {
    try {
      if (v === undefined) { var s = localStorage.getItem(k); return s ? JSON.parse(s) : null; }
      localStorage.setItem(k, JSON.stringify(v));
    } catch (e) { return null; }
  }
  function getJSON(url) {
    var ctl = window.AbortController ? new AbortController() : null;
    var tm = ctl ? setTimeout(function () { ctl.abort(); }, 9000) : 0;
    return fetch(url, { headers: { Accept: 'application/geo+json' }, signal: ctl ? ctl.signal : undefined })
      .then(function (r) { clearTimeout(tm); if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); });
  }
  function where() {
    var s = params.get('from');
    if (!s || !towns[s]) { try { s = localStorage.getItem('sjFrom'); } catch (e) { s = null; } }
    if (!s || !towns[s]) s = DEF;
    var t = towns[s] || [39.33984, -74.57515, 'Linwood'];
    return { slug: s, lat: t[0], lon: t[1], name: t[2] };
  }

  /* ---------- sun elevation (fallback for day/night) ---------- */
  function isDayAt(lat, lon, d) {
    var r = Math.PI / 180, n = d.getTime() / 864e5 + 2440587.5 - 2451545.0;
    var L = (280.46 + 0.9856474 * n) % 360, g = ((357.528 + 0.9856003 * n) % 360) * r;
    var lam = (L + 1.915 * Math.sin(g) + 0.02 * Math.sin(2 * g)) * r, eps = (23.439 - 4e-7 * n) * r;
    var dec = Math.asin(Math.sin(eps) * Math.sin(lam)), ra = Math.atan2(Math.cos(eps) * Math.sin(lam), Math.cos(lam));
    var gmst = (18.697374558 + 24.06570982441908 * n) % 24, ha = ((gmst * 15 + lon) * r) - ra;
    var el = Math.asin(Math.sin(lat * r) * Math.sin(dec) + Math.cos(lat * r) * Math.cos(dec) * Math.cos(ha));
    return el / r > -0.833;
  }

  /* ---------- classify NWS icon code / text ---------- */
  function classify(code, text) {
    var c = code || '', t = (text || '').toLowerCase(), windy = /^wind_/.test(c) || /wind|breezy|blustery/.test(t);
    c = c.replace(/^wind_/, '');
    var s = null;
    if (/^(tsra|tornado|hurricane|tropical_storm)/.test(c)) s = 'storm';
    else if (/^(snow|blizzard|sleet|rain_snow|snow_sleet|snow_fzra)/.test(c)) s = 'snow';
    else if (/^(rain|fzra|rain_fzra|rain_sleet)/.test(c)) s = 'rain';
    else if (/^(fog|haze|smoke|dust)/.test(c)) s = 'fog';
    else if (/^(bkn|ovc)/.test(c)) s = 'cloudy';
    else if (/^(few|sct)/.test(c)) s = 'partly';
    else if (/^(skc|hot|cold)/.test(c)) s = 'clear';
    if (!s) {
      if (/thunder|t-storm|tstm/.test(t)) s = 'storm';
      else if (/snow|sleet|flurr|ice pellet|wintry|blizzard/.test(t)) s = 'snow';
      else if (/rain|drizzle|shower/.test(t)) s = 'rain';
      else if (/fog|mist|haze|smoke/.test(t)) s = 'fog';
      else if (/partly|few|scattered|mostly sunny|mostly clear/.test(t)) s = 'partly';
      else if (/cloud|overcast/.test(t)) s = 'cloudy';
      else if (/clear|sunny|fair/.test(t)) s = 'clear';
    }
    return { scene: s, windy: windy };
  }
  function iconBits(icon) {
    var m = /\/icons\/land\/(day|night)\/([a-z_]+)/.exec(icon || '');
    return m ? { night: m[1] === 'night', code: m[2] } : { night: null, code: '' };
  }
  var LABEL = { clear: 'Clear', partly: 'Partly cloudy', cloudy: 'Cloudy', rain: 'Rain', storm: 'Thunderstorms', snow: 'Snow', fog: 'Fog' };

  /* ---------- NWS fetch chain ---------- */
  function point(loc) {
    var k = 'sjWxPt:' + loc.lat.toFixed(3) + ',' + loc.lon.toFixed(3), c = ls(k);
    if (c && Date.now() - c.t < PT_TTL && c.st && c.st.length) return Promise.resolve(c);
    return getJSON(API + '/points/' + loc.lat.toFixed(4) + ',' + loc.lon.toFixed(4)).then(function (j) {
      var p = j.properties || {};
      return getJSON(p.observationStations + '?limit=3').then(function (s) {
        var st = (s.features || []).slice(0, 3).map(function (f) { return [f.properties.stationIdentifier, f.properties.name]; });
        var out = { t: Date.now(), st: st, hr: p.forecastHourly };
        ls(k, out); return out;
      });
    });
  }
  function fromObs(j, stName) {
    var p = j.properties || {}, ts = Date.parse(p.timestamp);
    if (!ts || Date.now() - ts > STALE_OBS) return null;
    var ib = iconBits(p.icon), cl = classify(ib.code, p.textDescription);
    if (!cl.scene) return null;
    var tc = p.temperature && p.temperature.value, w = p.windSpeed && p.windSpeed.value, g = p.windGust && p.windGust.value;
    var mph = w == null ? null : w * 0.621371, gmph = g == null ? null : g * 0.621371;
    return { scene: cl.scene, night: ib.night, text: p.textDescription || LABEL[cl.scene], tempF: tc == null ? null : tc * 9 / 5 + 32,
      wind: mph, windy: cl.windy || (mph != null && mph >= 20) || (gmph != null && gmph >= 32), src: 'obs', station: stName, at: ts };
  }
  function fromHourly(j) {
    var p = ((j.properties || {}).periods || [])[0];
    if (!p) return null;
    var ib = iconBits(p.icon), cl = classify(ib.code, p.shortForecast);
    if (!cl.scene) return null;
    var nums = String(p.windSpeed || '').match(/\d+/g), mph = nums ? Math.max.apply(null, nums.map(Number)) : null;
    var tf = p.temperature == null ? null : (p.temperatureUnit === 'C' ? p.temperature * 9 / 5 + 32 : p.temperature);
    return { scene: cl.scene, night: p.isDaytime === false, text: p.shortForecast, tempF: tf, wind: mph,
      windy: cl.windy || (mph != null && mph >= 20), src: 'forecast', at: Date.parse(p.startTime) || Date.now() };
  }
  function load(loc) {
    var k = 'sjWx:' + loc.slug, c = ls(k);
    if (c && c.d && Date.now() - c.t < TTL) return Promise.resolve(c.d);
    return point(loc).then(function (pt) {
      var i = 0;
      function next() {
        if (i >= pt.st.length) return pt.hr ? getJSON(pt.hr).then(fromHourly) : null;
        var s = pt.st[i++];
        return getJSON(API + '/stations/' + encodeURIComponent(s[0]) + '/observations/latest')
          .then(function (j) { return fromObs(j, s[1]); }, function () { return null; })
          .then(function (d) { return d || next(); });
      }
      return next();
    }).then(function (d) {
      if (!d) throw new Error('no data');
      ls(k, { t: Date.now(), d: d }); return d;
    }).catch(function (err) {
      if (c && c.d && Date.now() - c.t < 3 * 36e5) return c.d; // offline: use a recent cached result
      throw err;
    });
  }

  /* ---------- scene layer ---------- */
  var layer, canvas, ctx, parts = [], raf = 0, last = 0, visible = true, cur = null;
  function build() {
    layer = document.createElement('div');
    layer.className = 'wx'; layer.setAttribute('aria-hidden', 'true');
    var clouds = '', i;
    for (i = 0; i < 7; i++) clouds += '<i></i>';
    layer.innerHTML = '<div class="wx-sky"></div><div class="wx-sun"></div><div class="wx-stars"><i></i><i></i></div><div class="wx-moon"></div>' +
      '<div class="wx-clouds">' + clouds + '</div><div class="wx-fog"><i></i><i></i><i></i></div><canvas class="wx-cv"></canvas><div class="wx-flash"></div><div class="wx-scrim"></div>';
    hero.insertBefore(layer, hero.firstChild);
    // stars: deterministic pseudo-random box-shadows
    var seed = 7, sh = [[], []];
    function rnd() { seed = (seed * 16807) % 2147483647; return seed / 2147483647; }
    for (i = 0; i < 110; i++) sh[i % 2].push((rnd() * 100).toFixed(2) + 'vw ' + Math.round(rnd() * 520) + 'px 0 ' + (rnd() < 0.15 ? '1px' : '0') + ' rgba(255,255,255,' + (0.35 + rnd() * 0.6).toFixed(2) + ')');
    var st = layer.querySelectorAll('.wx-stars i');
    st[0].style.boxShadow = sh[0].join(','); st[1].style.boxShadow = sh[1].join(',');
    canvas = layer.querySelector('canvas'); ctx = canvas.getContext && canvas.getContext('2d');
  }
  function size() {
    if (!canvas) return;
    var dpr = Math.min(window.devicePixelRatio || 1, 1.5), w = hero.clientWidth, h = hero.clientHeight;
    canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
    canvas.style.width = w + 'px'; canvas.style.height = h + 'px';
    if (ctx) ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    seedParts();
  }
  function seedParts() {
    parts = [];
    if (!cur || !ctx) return;
    var w = hero.clientWidth, h = hero.clientHeight, area = w * h, n = 0;
    if (cur.scene === 'rain') n = Math.min(110, area / 7000);
    else if (cur.scene === 'storm') n = Math.min(170, area / 4500);
    else if (cur.scene === 'snow') n = Math.min(90, area / 9000);
    for (var i = 0; i < n; i++) parts.push(newPart(w, h, true));
    if (RM && RM.matches) frame(0); // reduced motion: one still frame, no loop
  }
  function newPart(w, h, any) {
    var snow = cur.scene === 'snow';
    return { x: Math.random() * (w + 200) - 100, y: any ? Math.random() * h : -20 - Math.random() * 60,
      v: snow ? 28 + Math.random() * 40 : 620 + Math.random() * 380, l: snow ? 1 + Math.random() * 2.2 : 12 + Math.random() * 16,
      a: snow ? 0.45 + Math.random() * 0.45 : 0.25 + Math.random() * 0.3, p: Math.random() * 6.28 };
  }
  function frame(dt) {
    var w = hero.clientWidth, h = hero.clientHeight, snow = cur.scene === 'snow';
    var drift = (cur.windy ? 2.2 : 1) * (snow ? 14 : 70);
    ctx.clearRect(0, 0, w, h);
    ctx.lineCap = 'round';
    for (var i = 0; i < parts.length; i++) {
      var q = parts[i];
      q.y += q.v * dt; q.p += dt * 1.3;
      q.x += (drift + (snow ? Math.sin(q.p) * 18 : 0)) * dt;
      if (q.y > h + 20 || q.x > w + 120) { parts[i] = q = newPart(w, h, false); }
      if (snow) {
        ctx.fillStyle = 'rgba(255,255,255,' + q.a + ')';
        ctx.beginPath(); ctx.arc(q.x, q.y, q.l, 0, 6.283); ctx.fill();
      } else {
        var k = q.l / q.v;
        ctx.strokeStyle = 'rgba(190,215,255,' + q.a + ')'; ctx.lineWidth = 1.1;
        ctx.beginPath(); ctx.moveTo(q.x, q.y); ctx.lineTo(q.x - drift * k, q.y - q.l); ctx.stroke();
      }
    }
  }
  function loop(ts) {
    raf = 0;
    if (!running()) return;
    var dt = last ? Math.min((ts - last) / 1000, 0.05) : 0.016; last = ts;
    frame(dt);
    raf = requestAnimationFrame(loop);
  }
  function running() { return parts.length && !document.hidden && visible && !(RM && RM.matches); }
  function kick() {
    root.classList.toggle('wx-paused', document.hidden || !visible);
    if (running() && !raf) { last = 0; raf = requestAnimationFrame(loop); }
  }

  function apply(d, label, preview) {
    if (!layer) {
      build();
      window.addEventListener('resize', function () { clearTimeout(apply._r); apply._r = setTimeout(size, 150); });
      document.addEventListener('visibilitychange', kick);
      if (window.IntersectionObserver) new IntersectionObserver(function (es) { visible = es[0].isIntersecting; kick(); }).observe(hero);
      if (RM && RM.addEventListener) RM.addEventListener('change', function () { seedParts(); kick(); });
    }
    cur = d;
    root.setAttribute('data-wx', d.scene);
    root.setAttribute('data-wx-night', d.night ? '1' : '0');
    root.setAttribute('data-wx-windy', d.windy ? '1' : '0');
    size(); kick();
    chip(d, label, preview);
  }
  function chip(d, loc, preview) {
    var el = document.querySelector('[data-wxchip]');
    if (!el) return;
    var t = d.tempF == null ? '' : Math.round(d.tempF) + '°F · ';
    var txt = t + d.text + (d.windy ? ' · Windy' : '') + ' · ' + loc.name;
    var ico = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="' + ICON[d.scene === 'clear' && d.night ? 'moon' : d.scene] + '"/></svg>';
    var at = new Date(d.at);
    var when = at.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', timeZone: 'America/New_York', timeZoneName: 'short' });
    var title = preview ? 'Weather preview (?wx=' + params.get('wx') + '), not live data'
      : (d.src === 'obs' ? 'NWS observation at ' + d.station + ', ' + when : 'NWS hourly forecast from ' + when) + '. Opens the NWS forecast.';
    el.innerHTML = '';
    var a = document.createElement('a');
    a.href = 'https://forecast.weather.gov/MapClick.php?lat=' + loc.lat.toFixed(4) + '&lon=' + loc.lon.toFixed(4);
    a.target = '_blank'; a.rel = 'noopener'; a.title = title;
    a.innerHTML = ico + '<span></span>';
    a.lastChild.textContent = (preview ? 'Preview · ' : '') + txt;
    el.appendChild(a); el.hidden = false;
  }
  var ICON = {
    clear: 'M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10zM12 1v3M12 20v3M1 12h3M20 12h3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1',
    moon: 'M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z',
    partly: 'M8 3v2M3.5 8H2M4.5 4.5l1.4 1.4M12 8a4 4 0 0 0-7.5 2M7 20h10a4 4 0 0 0 0-8 5.5 5.5 0 0 0-10.6 1.5A3.3 3.3 0 0 0 7 20z',
    cloudy: 'M7 19h10a4.5 4.5 0 0 0 .5-9 6 6 0 0 0-11.5 2A3.5 3.5 0 0 0 7 19z',
    rain: 'M7 15h10a4 4 0 0 0 .4-8 5.5 5.5 0 0 0-10.6 1.8A3.1 3.1 0 0 0 7 15zM8 18l-1 3M12 18l-1 3M16 18l-1 3',
    storm: 'M7 14h10a4 4 0 0 0 .4-8 5.5 5.5 0 0 0-10.6 1.8A3.1 3.1 0 0 0 7 14zM13 15l-3 4h3l-2 4',
    snow: 'M7 14h10a4 4 0 0 0 .4-8 5.5 5.5 0 0 0-10.6 1.8A3.1 3.1 0 0 0 7 14zM8 18v.1M12 20v.1M16 18v.1M10 22v.1M14 22v.1',
    fog: 'M3 9h18M5 13h14M3 17h18M7 21h10'
  };

  /* ---------- debug override ---------- */
  function preview(v) {
    var tok = v.toLowerCase().split(/[\s,+-]+/), s = null, night = null, windy = false;
    var map = { clear: 'clear', sunny: 'clear', partly: 'partly', cloudy: 'cloudy', overcast: 'cloudy', clouds: 'cloudy', rain: 'rain',
      storm: 'storm', thunderstorm: 'storm', thunder: 'storm', tstorm: 'storm', snow: 'snow', fog: 'fog', haze: 'fog' };
    tok.forEach(function (x) {
      if (x === 'night') night = true; else if (x === 'day') night = false;
      else if (x === 'windy' || x === 'wind') windy = true;
      else if (!s && map[x]) s = map[x];
    });
    if (!s) s = (night !== null || windy) ? (windy && night === null ? 'partly' : 'clear') : null;
    if (!s) return null;
    return { scene: s, night: !!night, windy: windy, text: LABEL[s] + (night ? ' (night)' : ''), tempF: s === 'snow' ? 29 : s === 'clear' && !night ? 74 : 58, src: 'preview', at: Date.now() };
  }

  function run() {
    var loc = where(), wx = params.get('wx');
    if (wx) {
      if (wx === 'off' || wx === 'static') return;
      var p = preview(wx);
      if (p) { apply(p, loc, true); return; }
    }
    load(loc).then(function (d) {
      if (d.night == null) d.night = !isDayAt(loc.lat, loc.lon, new Date());
      apply(d, loc, false);
    }).catch(function () { /* stay on the static Dark Glass look */ });
  }
  run();

  // follow the distance filter's town picker
  document.querySelectorAll('[data-origin]').forEach(function (sel) {
    sel.addEventListener('change', function () {
      if (sel.value === 'geo' || !towns[sel.value]) return;
      setTimeout(function () { params = new URLSearchParams(location.search); params.set('from', sel.value); run(); }, 0);
    });
  });
})();
