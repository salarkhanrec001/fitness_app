"use strict";

(function () {
  const qs = (sel, root = document) => root.querySelector(sel);
  const qsa = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  function getCSRFToken() {
    const el = document.querySelector('meta[name="csrf-token"]');
    return el ? el.getAttribute("content") : null;
  }

  async function apiPost(url, body) {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCSRFToken()
      },
      credentials: "same-origin",
      body: JSON.stringify(body || {}),
    });
    const text = await res.text();
    let data;
    try { data = JSON.parse(text); } catch (e) { data = { ok: false, error: text }; }
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
    try { data = JSON.parse(text); } catch (e) { data = { ok: false, error: text }; }
    if (!res.ok) throw data;
    return data;
  }

  function initSfxToggle() {
    const btn = qs("#monk-sfx-toggle");
    if (!btn) return;

    const saved = localStorage.getItem("monk-sfx-enabled");
    window.__monkSfxEnabled = saved === "1";

    const apply = () => {
      const enabled = !!window.__monkSfxEnabled;
      const status = qs(".monk-sfx-status", btn);
      const icon = qs(".monk-sfx-icon", btn);
      if (status) status.textContent = enabled ? "ENABLED" : "DISABLED";
      if (icon) icon.textContent = enabled ? "🔊" : "🔇";
      btn.style.opacity = enabled ? "1" : "0.5";
    };

    apply();
    btn.addEventListener("click", () => {
      window.__monkSfxEnabled = !window.__monkSfxEnabled;
      localStorage.setItem("monk-sfx-enabled", window.__monkSfxEnabled ? "1" : "0");
      apply();
    });
  }

  async function refreshStats() {
    try {
      const data = await apiGet("/dashboard/monk/status");
      if (!data.ok) return;

      const percentEl = qs("#monk-progress-percent");
      const ringFill = qs("#monk-ring-fill");
      const streakEl = qs("#monk-streak-val");
      const currentDayEl = qs("#monk-current-day");

      if (percentEl && data.level) {
        percentEl.textContent = `${data.level.progress_percent}%`;
        if (ringFill) {
          const offset = 339 - (339 * data.level.progress_percent) / 100;
          ringFill.style.strokeDashoffset = offset;
        }
      }
      if (streakEl) streakEl.textContent = data.streak;
      if (currentDayEl && data.today) currentDayEl.textContent = data.today.day_index || 1;

      // Update Task List if on dashboard
      const taskGrid = qs("#monk-task-grid");
      if (taskGrid && data.tasks) {
        const remainingEl = qs("#monk-tasks-remaining");
        const pendingCount = data.tasks.filter(t => t.status !== 'completed').length;
        if (remainingEl) remainingEl.textContent = `${pendingCount} PENDING`;

        taskGrid.innerHTML = data.tasks.map(t => `
          <div class="monk-task-item premium-card mm-task" data-task-key="${t.task_key}">
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

        // Re-bind checkboxes
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
          await apiPost("/dashboard/monk/complete-task", { task_key: taskKey });
          refreshStats();
        } catch (err) {
          checkbox.checked = false;
          alert(err.error || "Failed to record task");
        }
      };
    });
  }

  function initFinalize() {
    const btn = qs("#monk-complete-day-btn");
    if (!btn) return;

    btn.addEventListener("click", async () => {
      console.log("Monk: Finalize clicked");
      try {
        btn.disabled = true;
        btn.textContent = "FINALIZING...";
        const data = await apiPost("/dashboard/monk/complete-day", {});
        console.log("Monk: Finalize success", data);
        // Take user to the Grid page instead of just reloading
        window.location.href = "/dashboard/monk/days";
      } catch (err) {
        console.error("Monk: Finalize error", err);
        btn.disabled = false;
        btn.textContent = "RETRY FINALIZATION";
        alert(err.error || "Failed to finalize day. Ensure all tasks are complete.");
      }
    });
  }

  function bootstrap() {
    console.log("Monk: Bootstrap starting...");
    initSfxToggle();
    initFinalize();
    initCheckboxes();
    refreshStats();
  }

  // Startup: Run immediately if DOM ready, otherwise wait
  if (document.readyState === "complete" || document.readyState === "interactive") {
    bootstrap();
  } else {
    document.addEventListener("DOMContentLoaded", bootstrap);
  }
})();
