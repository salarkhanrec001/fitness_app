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

  // --- AAA SFX System ---
  function playBeep(type) {
    if (localStorage.getItem("monk-sfx-enabled") !== "1") return;
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      
      osc.connect(gain);
      gain.connect(ctx.destination);
      
      const now = ctx.currentTime;
      if (type === "check") {
        osc.type = "sine";
        osc.frequency.setValueAtTime(880, now);
        osc.frequency.exponentialRampToValueAtTime(1200, now + 0.1);
        gain.gain.setValueAtTime(0.1, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.2);
        osc.start();
        osc.stop(now + 0.2);
      } else if (type === "complete") {
        osc.type = "square";
        osc.frequency.setValueAtTime(200, now);
        osc.frequency.linearRampToValueAtTime(800, now + 0.5);
        gain.gain.setValueAtTime(0.05, now);
        gain.gain.linearRampToValueAtTime(0, now + 0.5);
        osc.start();
        osc.stop(now + 0.5);
      }
    } catch (e) {}
  }

  // --- AAA Confetti System ---
  function launchConfetti() {
    const canvas = document.createElement("canvas");
    canvas.style.position = "fixed";
    canvas.style.inset = "0";
    canvas.style.pointerEvents = "none";
    canvas.style.zIndex = "10000";
    document.body.appendChild(canvas);
    
    const ctx = canvas.getContext("2d");
    let w = canvas.width = window.innerWidth;
    let h = canvas.height = window.innerHeight;
    
    const pieces = [];
    for(let i=0; i<100; i++) {
      pieces.push({
        x: Math.random() * w,
        y: h + Math.random() * 100,
        r: 4 + Math.random() * 6,
        color: Math.random() > 0.5 ? "#ff3c3c" : "#fff",
        vx: -2 + Math.random() * 4,
        vy: -15 - Math.random() * 10
      });
    }
    
    function draw() {
      ctx.clearRect(0, 0, w, h);
      pieces.forEach(p => {
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();
        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.5; // gravity
      });
      if (pieces.some(p => p.y < h + 100)) requestAnimationFrame(draw);
      else canvas.remove();
    }
    draw();
  }

  async function apiPost(url, body) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": getCSRFToken() },
      credentials: "same-origin",
      body: JSON.stringify(body || {}),
    });
    if (res.status === 403) throw { ok: false, error: "Security Session Expired (CSRF). Refresh required." };
    const text = await res.text();
    let data;
    try { data = JSON.parse(text); } catch (e) { data = { ok: false, error: "Server error: " + text.slice(0, 100) }; }
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
    try { data = JSON.parse(text); } catch (e) { data = { ok: false, error: text.slice(0, 100) }; }
    if (!res.ok) throw data;
    return data;
  }

  function initSfxToggle() {
    const btn = qs("#monk-sfx-toggle");
    if (!btn) return;
    const saved = localStorage.getItem("monk-sfx-enabled") || "1";
    localStorage.setItem("monk-sfx-enabled", saved);
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
      if (!cur) playBeep("check");
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
      
      // Update Mission Focus & Quotes
      const titleEl = qs(".monk-title-block p");
      const quoteEl = qs(".monk-rules-subtitle");
      if (titleEl && data.mission_focus) titleEl.textContent = data.mission_focus.toUpperCase();
      if (quoteEl && data.protocol_quote) quoteEl.textContent = data.protocol_quote;

      if (percentEl && data.level) {
        percentEl.textContent = `${data.level.progress_percent}%`;
        if (ringFill) {
          const offset = 339 - (339 * data.level.progress_percent) / 100;
          ringFill.style.strokeDashoffset = offset;
        }
      }
      if (streakEl) streakEl.textContent = data.streak;
      if (currentDayEl && data.today) currentDayEl.textContent = data.today.day_index || 1;

      const taskGrid = qs("#monk-task-grid");
      if (taskGrid && data.tasks) {
        const remainingEl = qs("#monk-tasks-remaining");
        const pendingCount = data.tasks.filter(t => t.status !== 'completed').length;
        if (remainingEl) remainingEl.textContent = `${pendingCount} PENDING`;

        taskGrid.innerHTML = data.tasks.map(t => `
          <div class="monk-task-item premium-card mm-task" data-task-key="${t.task_key}" style="animation: fadeIn 0.4s ease forwards;">
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
    } catch (e) {
      console.error("Monk refresh failed", e);
    }
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
        launchConfetti();
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
    initFinalize();
    initCheckboxes();
    refreshStats();
  }

  if (document.readyState === "complete" || document.readyState === "interactive") bootstrap();
  else document.addEventListener("DOMContentLoaded", bootstrap);
})();
