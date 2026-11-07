(function () {
  "use strict";

  // ---------- countdown to the draw ----------
  // data-draw-date is an ISO 8601 timestamp set in the organiser panel
  var container = document.getElementById("zostalo");
  var doneMsg = document.getElementById("zostalo-done");

  if (container) {
    var target = Date.parse(container.dataset.drawDate || "");
    var units = {};
    ["days", "hours", "minutes", "seconds"].forEach(function (u) {
      units[u] = container.querySelector('[data-unit="' + u + '"]');
    });

    var pad = function (n) { return n < 10 ? "0" + n : String(n); };
    var timer;

    var tick = function () {
      var diff = target - Date.now();
      if (isNaN(diff) || diff <= 0) {
        container.hidden = true;
        if (doneMsg) doneMsg.hidden = false;
        clearInterval(timer);
        return;
      }
      var s = Math.floor(diff / 1000);
      units.days.textContent = Math.floor(s / 86400);
      units.hours.textContent = pad(Math.floor((s % 86400) / 3600));
      units.minutes.textContent = pad(Math.floor((s % 3600) / 60));
      units.seconds.textContent = pad(s % 60);
    };

    tick();
    timer = setInterval(tick, 1000);
  }

  var reducedMotion = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---------- sleigh: new random height on every pass ----------
  var sleigh = document.getElementById("sleigh");
  if (sleigh) {
    sleigh.addEventListener("animationiteration", function () {
      sleigh.style.top = (6 + Math.random() * 30) + "vh";
    });
  }

  // ---------- particles: falling snow (winter) or rising embers (cozy) ----------
  var canvas = document.getElementById("snow");
  if (canvas && canvas.getContext && !reducedMotion) {
    var ctx = canvas.getContext("2d");
    var embers = canvas.dataset.mode === "embers";
    var parts = [];
    var w = 0, h = 0;

    var makeSnow = function (anywhere) {
      var r = 0.8 + Math.random() * 2.6;
      return {
        x: Math.random() * w,
        y: anywhere ? Math.random() * h : -10,
        r: r,
        vy: 0.3 + r * 0.35 + Math.random() * 0.3,
        phase: Math.random() * Math.PI * 2,
        sway: 0.3 + Math.random() * 0.7,
        alpha: 0.45 + Math.random() * 0.5
      };
    };

    // embers start around the fireplace (bottom left) and fade as they rise
    var makeEmber = function (anywhere) {
      var fromFire = Math.random() < 0.7;
      var startY = fromFire ? h * (0.62 + Math.random() * 0.2) : h * (0.3 + Math.random() * 0.7);
      return {
        x: fromFire ? w * (0.05 + Math.random() * 0.25) : Math.random() * w,
        y: anywhere ? startY - Math.random() * h * 0.5 : startY,
        y0: startY,
        r: fromFire ? 0.8 + Math.random() * 1.8 : 0.6 + Math.random() * 1.2,
        vy: -(fromFire ? 0.4 + Math.random() * 0.9 : 0.1 + Math.random() * 0.25),
        phase: Math.random() * Math.PI * 2,
        sway: 0.4 + Math.random() * 0.8,
        hue: fromFire ? 20 + Math.random() * 25 : 38 + Math.random() * 10,
        span: h * (fromFire ? 0.35 + Math.random() * 0.35 : 0.3)
      };
    };

    var make = embers ? makeEmber : makeSnow;

    var resize = function () {
      var dpr = window.devicePixelRatio || 1;
      w = window.innerWidth;
      h = window.innerHeight;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      var target = embers ? Math.min(70, Math.round(w / 22)) : Math.min(220, Math.round(w * h / 9000));
      parts.length = 0;
      while (parts.length < target) parts.push(make(true));
    };

    var frame = function (t) {
      ctx.clearRect(0, 0, w, h);
      for (var i = 0; i < parts.length; i++) {
        var p = parts[i];
        p.y += p.vy;
        p.x += Math.sin(t / 1600 + p.phase) * p.sway * 0.5;
        if (embers) {
          var life = 1 - (p.y0 - p.y) / p.span;
          if (life <= 0) { parts[i] = make(false); continue; }
          ctx.globalAlpha = Math.max(0, Math.min(1, life)) * 0.9;
          ctx.fillStyle = "hsl(" + p.hue + ", 100%, 62%)";
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.r * 2.6, 0, Math.PI * 2);
          ctx.globalAlpha *= 0.25;
          ctx.fill();
          ctx.globalAlpha *= 4;
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
          ctx.fill();
        } else {
          if (p.y > h + 10 || p.x < -10 || p.x > w + 10) parts[i] = p = make(false);
          ctx.globalAlpha = p.alpha;
          ctx.fillStyle = "#fff";
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
          ctx.fill();
        }
      }
      requestAnimationFrame(frame);
    };

    resize();
    window.addEventListener("resize", resize);
    requestAnimationFrame(frame);
  }

  // ---------- prevent double submits ----------
  document.querySelectorAll("form").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (form.dataset.confirm && !window.confirm(form.dataset.confirm)) {
        e.preventDefault();
        return;
      }
      if (form.classList.contains("lang-switch")) return;

      var btn = e.submitter || form.querySelector('button[type="submit"]');
      if (!btn) return;
      // Disable only after the browser has collected the form data, otherwise
      // the clicked button's name/value would be left out of the request.
      setTimeout(function () {
        btn.disabled = true;
        var labels = document.body.dataset;
        btn.textContent = form.classList.contains("draw-form")
          ? (labels.drawing || "Losowanie…")
          : (labels.sending || "Wysyłanie…");
      }, 0);
    });
  });
})();
