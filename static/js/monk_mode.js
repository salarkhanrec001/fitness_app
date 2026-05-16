"use strict";

/**
 * Monk Mode UI logic (isolated, dashboard-embedded).
 * - Never trusts frontend state for completion: backend verifies tasks + deadlines.
 * - Polls status from /dashboard/monk/status after each mutation.
 */

(function () {
  const qs = (sel, root = document) => root.querySelector(sel);
  const qsa = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  function getCSRFToken() {
    // App base.html provides <meta name="csrf-token" content="...">
    const el = document.querySelector('meta[name="csrf-token"]');
    return el ? el.getAttribute("content") : null;
  }

  function buildJsonHeaders() {
    const headers = { "Content-Type": "application/json" };
    const csrfToken = getCSRFToken();
    if (csrfToken) headers["X-CSRFToken"] = csrfToken;
    return headers;
  }

  function safeJsonParse(text) {
    try {
      return JSON.parse(text);
    } catch (e) {
      return null;
    }
  }

  async function apiPost(url, body) {
    const res = await fetch(url, {
      method: "POST",
      headers: buildJsonHeaders(),
      credentials: "same-origin",
      body: JSON.stringify(body || {}),
    });
    const text = await res.text();
    const data = safeJsonParse(text) || {
      ok: false,
      error: text || "Request failed",
    };
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
    const data = safeJsonParse(text) || {
      ok: false,
      error: text || "Request failed",
    };
    if (!res.ok) throw data;
    return data;
  }

  function playBeep(kind) {
    // Lightweight, no assets. Uses WebAudio for optional tiny blips.
    // Respect user toggle + avoid autoplay blocking by requiring interaction first.
    if (!window.__monkSfxEnabled) return;
    if (!window.AudioContext && !window.webkitAudioContext) return;

    const AudioContext = window.AudioContext || window.webkitAudioContext;
    const ctx = new AudioContext();

    const o = ctx.createOscillator();
    const g = ctx.createGain();

    const now = ctx.currentTime;
    const base = kind === "complete" ? 420 : kind === "start" ? 300 : 520;

    o.type = "square";
    o.frequency.setValueAtTime(base, now);

    g.gain.setValueAtTime(0.0001, now);
    g.gain.exponentialRampToValueAtTime(0.04, now + 0.02);
    g.gain.exponentialRampToValueAtTime(0.0001, now + 0.12);

    o.connect(g);
    g.connect(ctx.destination);

    o.start(now);
    o.stop(now + 0.14);

    setTimeout(() => {
      try {
        ctx.close();
      } catch (e) {}
    }, 250);
  }

  function refreshEmbedFromServer() {
    const root = qs(".monk-mode-section");
    const url = root?.getAttribute("data-status-url") || "/dashboard/monk/status";
    
    return apiGet(url)
      .then((data) => {
        if (!data || !data.ok) return;

        const setText = (id, value) => {
          const el = qs(id);
          if (el) el.textContent = String(value ?? "");
        };

        setText("#monk-streak", data.streak ?? 0);
        setText("#monk-current-day", data.current_day ?? 1);

        // Update progress ring stroke-dashoffset.
        // Our SVG uses stroke-dasharray=325 and stroke-dashoffset=325 by default.
        const pct = Math.max(
          0,
          Math.min(
            100,
            data.level && typeof data.level.progress_percent === "number"
              ? data.level.progress_percent
              : 0,
          ),
        );
        setText("#monk-completion-pct", pct);

        const svgFg = document.querySelector(".monk-ring-fg");
        if (svgFg) {
          // dashoffset = 325 - (pct/100)*325
          const dash = 325;
          svgFg.style.strokeDasharray = dash;
          svgFg.style.strokeDashoffset = String(dash - (pct / 100) * dash);
        }

        // Update mission quote text already static; mission text is based on status.
        const missionText = qs("#monk-today-mission");
        if (missionText) {
          missionText.textContent =
            data.status === "active"
              ? "Complete every mandatory task. No excuses."
              : "Locked. Begin transformation to reveal today’s mission.";
        }

        // Update level label.
        const phaseEl = qs("#monk-phase");
        if (phaseEl) {
          const levelKey =
            data.level && data.level.level_key
              ? data.level.level_key
              : "weak_mind";
          phaseEl.textContent =
            data.status === "active"
              ? `Level: ${String(levelKey)
                  .replaceAll("_", " ")
                  .replace(/\b\w/g, (m) => m.toUpperCase())}`
              : "Level locked.";
        }

        // Update task checkboxes.
        const tasks = data.tasks || [];
        qsa(".monk-task-item").forEach((item) => {
          const taskKey = item.getAttribute("data-task-key");
          const t = tasks.find((x) => x.task_key === taskKey);
          const cb = qs(".monk-task-checkbox", item);
          const notesInput = qs(".monk-task-notes-input", item);
          if (!cb || !t) return;

          const completed = t.status === "completed";
          cb.checked = completed;

          // Disable if not pending/active
          const disabled =
            data.status !== "active" ||
            (t.status !== "pending" && t.status !== "completed");
          cb.disabled = disabled;
          if (notesInput) notesInput.disabled = disabled;

          const statusEl = qs(".monk-task-status", item);
          if (statusEl) {
            if (completed) statusEl.textContent = "✓ Completed";
            else if (t.status === "pending") statusEl.textContent = "Pending";
            else statusEl.textContent = "Locked";
          }
        });
      })
      .catch(() => {
        // Silent fail: UI can remain; backend is source of truth.
      });
  }

  function openModal() {
    const overlay = qs("#monk-modal-overlay");
    const modal = qs("#monk-modal");
    if (!overlay || !modal) return;
    overlay.style.display = "block";
    modal.style.display = "block";
    overlay.style.opacity = "1";
  }

  function closeModal() {
    const overlay = qs("#monk-modal-overlay");
    const modal = qs("#monk-modal");
    if (!overlay || !modal) return;
    overlay.style.display = "none";
    modal.style.display = "none";
  }

  function initSfxToggle() {
    const btn = qs("#monk-sfx-btn");
    if (!btn) return;

    const saved = localStorage.getItem("monk-sfx-enabled");
    window.__monkSfxEnabled = saved === "1";

    const apply = () => {
      const pressed = !!window.__monkSfxEnabled;
      btn.setAttribute("aria-pressed", pressed ? "true" : "false");
      const icon = qs(".monk-sfx-icon", btn);
      const text = qs(".monk-sfx-text", btn);
      if (icon) icon.textContent = pressed ? "🔊" : "🔇";
      if (text) text.textContent = pressed ? "SFX" : "SFX";
    };

    apply();

    btn.addEventListener("click", () => {
      window.__monkSfxEnabled = !window.__monkSfxEnabled;
      localStorage.setItem(
        "monk-sfx-enabled",
        window.__monkSfxEnabled ? "1" : "0",
      );
      apply();
      // Optional feedback beep only after user click
      playBeep("toggle");
    });
  }

  function initStart() {
    const startBtn = qsa(".monk-start-btn")[0];
    if (!startBtn) return;

    startBtn.addEventListener("click", () => {
      openModal();
    });

    const beginBtn = qs("#monk-begin-btn");
    const notReadyBtn = qs("#monk-not-ready-btn");

    if (beginBtn) {
      beginBtn.addEventListener("click", async () => {
        try {
          playBeep("start");
          const root = qs(".monk-mode-section");
          const url = root?.getAttribute("data-start-url") || "/dashboard/monk/start";
          const data = await apiPost(url, {});
          if (data && data.ok) {
            closeModal();
            await refreshEmbedFromServer();
          }
        } catch (e) {
          // show toast if available
          if (window.showToast && e && e.error)
            window.showToast(e.error, "error");
        }
      });
    }

    if (notReadyBtn) {
      notReadyBtn.addEventListener("click", () => {
        closeModal();
      });
    }

    // Click overlay to close
    const overlay = qs("#monk-modal-overlay");
    if (overlay) {
      overlay.addEventListener("click", () => closeModal());
    }
  }

  function initTaskCheckboxes() {
    const container = qs(".monk-task-grid");
    if (!container) return;

    qsa(".monk-task-checkbox", container).forEach((cb) => {
      cb.addEventListener("change", async (e) => {
        const checkbox = e.currentTarget;
        const item = checkbox.closest(".monk-task-item");
        if (!item) return;

        const taskKey = item.getAttribute("data-task-key");
        if (!taskKey) return;

        // We only allow completing (no uncheck).
        if (checkbox.checked === false) {
          checkbox.checked = true;
          return;
        }

        try {
          playBeep("task");
          const root = qs(".monk-mode-section");
          const url = root?.getAttribute("data-complete-task-url") || "/dashboard/monk/complete-task";
          await apiPost(url, {
            task_key: taskKey,
            notes: (qs(".monk-task-notes-input", item)?.value || "").slice(
              0,
              120,
            ),
          });
          await refreshEmbedFromServer();
        } catch (err) {
          // If backend resets the monk run, UI will be out of date until refresh.
          if (window.showToast && err && err.error)
            window.showToast(err.error, "error");
          await refreshEmbedFromServer();
        }
      });
    });
  }

  function initCompleteDay() {
    const btn = qs(".monk-complete-day-btn");
    if (!btn) return;

    btn.addEventListener("click", async () => {
      try {
        playBeep("complete");
        const root = qs(".monk-mode-section");
        const url = root?.getAttribute("data-complete-day-url") || "/dashboard/monk/complete-day";
        await apiPost(url, {});
        await refreshEmbedFromServer();
        // Optional: confetti could go here; keeping it lightweight without extra libs.
        // If you want, we can add a small canvas confetti later.
      } catch (err) {
        if (window.showToast && err && err.error)
          window.showToast(err.error, "error");
        await refreshEmbedFromServer();
      }
    });
  }

  function initRingAnimation() {
    const fg = document.querySelector(".monk-ring-fg");
    const pct =
      parseFloat(
        (qs("#monk-completion-pct")?.textContent || "0").replace("%", ""),
      ) || 0;
    if (!fg) return;
    const dash = 325;
    fg.style.strokeDasharray = String(dash);
    fg.style.strokeDashoffset = String(dash - (pct / 100) * dash);
  }

  document.addEventListener("DOMContentLoaded", () => {
    // Initialize ring on first paint
    initRingAnimation();
    initSfxToggle();
    initStart();
    initTaskCheckboxes();
    initCompleteDay();

    // Small poll to sync quickly when server-rendered data is stale
    setTimeout(() => {
      refreshEmbedFromServer();
    }, 900);
  });
})();
