"use strict";

(function () {
  const qs = (sel, root = document) => root.querySelector(sel);
  const qsa = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  const rootEl = qs("#monk-mode-section");
  const config = {
    statusUrl: rootEl?.getAttribute("data-status-url") || "/dashboard/monk/status",
    completeTaskUrl: rootEl?.getAttribute("data-complete-task-url") || "/dashboard/monk/complete-task",
    completeDayUrl: rootEl?.getAttribute("data-complete-day-url") || "/dashboard/monk/complete-day",
    gridUrl: rootEl?.getAttribute("data-grid-url") || "/dashboard/monk/days",
    startUrl: rootEl?.getAttribute("data-start-url") || "/dashboard/monk/page/start",
  };

  function getCSRFToken() {
    const el = document.querySelector('meta[name="csrf-token"]');
    return el ? el.getAttribute("content") : null;
  }

  // --- AAA SFX ---
  function playBeep(type) {
    if (localStorage.getItem("monk-sfx-enabled") !== "1") return;
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain); gain.connect(ctx.destination);
      const now = ctx.currentTime;
      if (type === "check") {
        osc.frequency.setValueAtTime(880, now);
        osc.frequency.exponentialRampToValueAtTime(1200, now + 0.1);
        gain.gain.setValueAtTime(0.1, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.2);
        osc.start(); osc.stop(now + 0.2);
      } else if (type === "complete") {
        osc.frequency.setValueAtTime(200, now);
        osc.frequency.linearRampToValueAtTime(800, now + 0.5);
        gain.gain.setValueAtTime(0.05, now);
        gain.gain.linearRampToValueAtTime(0, now + 0.5);
        osc.start(); osc.stop(now + 0.5);
      }
    } catch (e) {}
  }

  // --- AAA Digital Particles ---
  function initParticles() {
    if (!rootEl) return;
    const canvas = document.createElement("canvas");
    canvas.className = "monk-particles";
    canvas.style.position = "absolute";
    canvas.style.inset = "0";
    canvas.style.pointerEvents = "none";
    canvas.style.zIndex = "0";
    canvas.style.opacity = "0.3";
    rootEl.appendChild(canvas);

    const ctx = canvas.getContext("2d");
    let w, h, particles = [];

    const resize = () => {
      w = canvas.width = rootEl.offsetWidth;
      h = canvas.height = rootEl.offsetHeight;
    };
    window.addEventListener("resize", resize);
    resize();

    for(let i=0; i<40; i++) {
      particles.push({
        x: Math.random() * w, y: Math.random() * h,
        s: Math.random() * 2,
        vx: -0.5 + Math.random(), vy: -0.5 + Math.random()
      });
    }

    function draw() {
      ctx.clearRect(0,0,w,h);
      ctx.fillStyle = "rgba(255, 60, 60, 0.5)";
      particles.forEach(p => {
        ctx.fillRect(p.x, p.y, p.s, p.s);
        p.x += p.vx; p.y += p.vy;
        if(p.x<0) p.x=w; if(p.x>w) p.x=0;
        if(p.y<0) p.y=h; if(p.y>h) p.y=0;
      });
      requestAnimationFrame(draw);
    }
    draw();
  }

  // --- AAA Mouse Tracking ---
  function initMouseTracking() {
    if (!rootEl) return;
    rootEl.addEventListener("mousemove", (e) => {
      const rect = rootEl.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 100;
      const y = ((e.clientY - rect.top) / rect.height) * 100;
      rootEl.style.setProperty("--mouse-x", `${x}%`);
      rootEl.style.setProperty("--mouse-y", `${y}%`);
    });
  }

  function triggerGlitch() {
    rootEl?.classList.add("monk-glitch-active");
    setTimeout(() => rootEl?.classList.remove("monk-glitch-active"), 200);
  }

  // --- Task Collapse System ---
  function initTaskToggle() {
    const btn = qs("#monk-tasks-toggle");
    const container = qs("#monk-task-container");
    if (!btn || !container) return;

    const saved = localStorage.getItem("monk-tasks-collapsed") === "1";
    if (saved) {
      container.style.display = "none";
      btn.textContent = "EXPAND";
    }

    btn.onclick = () => {
      const isHidden = container.style.display === "none";
      container.style.display = isHidden ? "block" : "none";
      btn.textContent = isHidden ? "MINIMIZE" : "EXPAND";
      localStorage.setItem("monk-tasks-collapsed", isHidden ? "0" : "1");
    };
  }

  async function apiPost(url, body) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": getCSRFToken() },
      credentials: "same-origin",
      body: JSON.stringify(body || {}),
    });
    if (res.status === 403) throw { ok: false, error: "CSRF Expired. Refresh required." };
    const text = await res.text();
    let data;
    try { data = JSON.parse(text); } catch (e) { data = { ok: false, error: "Server error" }; }
    if (!res.ok) throw data;
    return data;
  }

  async function apiGet(url) {
    const res = await fetch(url, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
    });
    const text = await res.text();
    let data;
    try { data = JSON.parse(text); } catch (e) { data = { ok: false, error: "Server error" }; }
    if (!res.ok) throw data;
    return data;
  }

  function initSfxToggle() {
    const btn = qs("#monk-sfx-toggle");
    if (!btn) return;
    const apply = () => {
      const enabled = localStorage.getItem("monk-sfx-enabled") === "1";
      const status = qs(".monk-sfx-status", btn);
      const icon = qs(".monk-sfx-icon", btn);
      if (status) status.textContent = enabled ? "ENABLED" : "DISABLED";
      if (icon) icon.textContent = enabled ? "🔊" : "🔇";
      btn.style.opacity = enabled ? "1" : "0.5";
    };
    apply();
    btn.onclick = () => {
      const cur = localStorage.getItem("monk-sfx-enabled") === "1";
      localStorage.setItem("monk-sfx-enabled", cur ? "0" : "1");
      apply();
    };
  }

  async function refreshStats() {
    try {
      const data = await apiGet(config.statusUrl);
      if (!data.ok) return;

      const percentEl = qs("#monk-progress-percent");
      const ringFill = qs("#monk-ring-fill");
      const streakEl = qs("#monk-streak-val");
      const currentDayEl = qs("#monk-current-day");
      const rankBadge = qs("#monk-rank-badge");
      const titleEl = qs(".monk-title-block p");
      const quoteEl = qs(".monk-rules-subtitle");

      if (titleEl && data.mission_focus) titleEl.textContent = data.mission_focus.toUpperCase();
      if (quoteEl && data.protocol_quote) quoteEl.textContent = data.protocol_quote;
      
      if (rankBadge && data.rank_title) {
        rankBadge.textContent = data.rank_title.toUpperCase();
        const colors = { "Initiate": "#ff3c3c", "Iron Will": "#ffb800", "Ascended": "#ffd700" };
        rankBadge.style.color = colors[data.rank_title] || "#ff3c3c";
        rankBadge.style.textShadow = `0 0 15px ${colors[data.rank_title]}88`;
      }

      if (percentEl && data.level) {
        percentEl.textContent = `${data.level.progress_percent}%`;
        if (ringFill) {
          const offset = 339 - (339 * data.level.progress_percent) / 100;
          ringFill.style.strokeDashoffset = offset;
        }
      }
      if (streakEl) streakEl.textContent = data.streak;
      if (currentDayEl && data.today) currentDayEl.textContent = data.today.day_index || 1;

      // Update Badge Strip
      const badgeSlots = qsa(".monk-badge-slot");
      const pathLine = qs(".monk-badge-path");
      let lastUnlockedIndex = -1;

      badgeSlots.forEach((slot, idx) => {
        const title = slot.getAttribute("title");
        const match = title.match(/Survive (\d+) Days/);
        if (match) {
          const target = parseInt(match[1]);
          const icon = qs(".monk-badge-icon", slot);
          if (data.streak >= target) {
            icon?.classList.remove("locked");
            icon?.classList.add("unlocked");
            slot.style.opacity = "1";
            lastUnlockedIndex = idx;
          } else {
            icon?.classList.add("locked");
            icon?.classList.remove("unlocked");
            slot.style.opacity = "0.5";
          }
        }
      });
      
      // Dynamic Path Glow
      if (pathLine) {
        const pct = (lastUnlockedIndex + 1) / badgeSlots.length * 100;
        pathLine.style.background = `linear-gradient(90deg, var(--monk-red) ${pct}%, rgba(255,255,255,0.05) ${pct}%)`;
        pathLine.style.boxShadow = lastUnlockedIndex >= 0 ? "0 0 10px rgba(255, 60, 60, 0.2)" : "none";
      }

      const taskGrid = qs("#monk-task-grid");
      if (taskGrid && data.tasks) {
        const remainingEl = qs("#monk-tasks-remaining");
        const pendingCount = data.tasks.filter(t => t.status !== 'completed').length;
        if (remainingEl) remainingEl.textContent = `${pendingCount} PENDING`;

        taskGrid.innerHTML = data.tasks.map(t => `
          <div class="monk-task-item mm-task" data-task-key="${t.task_key}" style="animation: mmFadeIn 0.4s ease forwards;">
            <div style="display: flex; align-items: center; gap: 1rem;">
              <label class="monk-checkbox">
                <input type="checkbox" class="monk-task-checkbox" ${t.status === 'completed' ? 'checked disabled' : ''}>
                <div class="monk-checkbox-ui"></div>
              </label>
              <div class="monk-task-text" style="${t.status === 'completed' ? 'color: #fff; text-decoration: line-through; opacity: 0.5;' : ''}">
                ${t.task_key.replace(/_/g, ' ').toUpperCase()}
              </div>
            </div>
          </div>
        `).join('');
        initCheckboxes();
      }
    } catch (e) {}
  }

  function initCheckboxes() {
    qsa(".monk-task-checkbox").forEach(cb => {
      cb.onclick = async (e) => {
        const checkbox = e.currentTarget;
        const row = checkbox.closest(".mm-task");
        if (!row) return;
        const taskKey = row.getAttribute("data-task-key");
        if (!checkbox.checked) { checkbox.checked = true; return; }
        try {
          playBeep("check");
          triggerGlitch();
          await apiPost(config.completeTaskUrl, { task_key: taskKey });
          refreshStats();
        } catch (err) {
          checkbox.checked = false;
          if (err.error === "Monk Mode not active") { window.location.href = config.startUrl; return; }
          alert(err.error || "Failed to record task");
        }
      };
    });
  }

  function initFinalize() {
    const btn = qs("#monk-complete-day-btn");
    if (!btn) return;
    btn.onclick = async () => {
      try {
        btn.disabled = true;
        btn.textContent = "VERIFYING...";
        await apiPost(config.completeDayUrl, {});
        playBeep("complete");
        triggerGlitch();
        btn.textContent = "PROTOCOL CLEARED";
        setTimeout(() => window.location.href = config.gridUrl, 2000);
      } catch (err) {
        btn.disabled = false;
        btn.textContent = "RETRY FINALIZATION";
        if (err.error === "Monk Mode not active") { window.location.href = config.startUrl; return; }
        alert(err.error || "Ensure all contracts are signed.");
      }
    };
  }

  function bootstrap() {
    initSfxToggle();
    initParticles();
    initMouseTracking();
    initTaskToggle();
    initFinalize();
    initCheckboxes();
    refreshStats();
  }

  if (document.readyState === "complete" || document.readyState === "interactive") bootstrap();
  else document.addEventListener("DOMContentLoaded", bootstrap);
})();
