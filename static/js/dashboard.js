/* dashboard.js — Chart.js analytics + micro-animations */
"use strict";

// ── Shared Chart.js theme helpers ─────────────────────────────
function getCssVar(name) {
  return getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
}

const PRIMARY = "#6c63ff";
const SECONDARY = "#00d4aa";
const ACCENT = "#ff6b6b";
const MUTED = "rgba(139,146,165,0.3)";
const GRID = "rgba(255,255,255,0.05)";

const BASE_CHART_OPTIONS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: "#1c2030",
      titleColor: "#e8eaf0",
      bodyColor: "#8b92a5",
      borderColor: "rgba(255,255,255,0.08)",
      borderWidth: 1,
      padding: 10,
      cornerRadius: 8,
    },
  },
  scales: {
    x: {
      grid: { color: GRID },
      ticks: { color: "#8b92a5", font: { size: 11 } },
    },
    y: {
      grid: { color: GRID },
      ticks: { color: "#8b92a5", font: { size: 11 } },
      beginAtZero: true,
    },
  },
  animation: { duration: 900, easing: "easeInOutQuart" },
};

// ── #1 Workouts per week Chart ─────────────────────────────────
const dataStr = document.getElementById("dashboard-data")?.textContent || "{}";
const data = JSON.parse(dataStr) || {};
const workoutsCtx = document.getElementById("workoutsChart");
if (workoutsCtx && Array.isArray(data.chartLabels)) {
  new Chart(workoutsCtx, {
    type: "bar",
    data: {
      labels: data.chartLabels || [],
      datasets: [
        {
          label: "Workouts",
          data: data.chartWorkouts || [],
          backgroundColor: `rgba(108,99,255,0.5)`,
          borderColor: PRIMARY,
          borderWidth: 2,
          borderRadius: 6,
          borderSkipped: false,
          hoverBackgroundColor: `rgba(108,99,255,0.8)`,
        },
      ],
    },
    options: {
      ...BASE_CHART_OPTIONS,
      scales: {
        ...BASE_CHART_OPTIONS.scales,
        y: {
          ...BASE_CHART_OPTIONS.scales.y,
          ticks: { ...BASE_CHART_OPTIONS.scales.y.ticks, stepSize: 1 },
        },
      },
    },
  });
}

// ── #1 Weight Trend Chart ──────────────────────────────────────
const weightCtx = document.getElementById("weightChart");
if (weightCtx && Array.isArray(data.weightLabels)) {
  const filteredData = data.weightData.filter((v) => v !== null);
  const minW = filteredData.length ? Math.min(...filteredData) - 3 : 50;
  const maxW = filteredData.length ? Math.max(...filteredData) + 3 : 120;

  new Chart(weightCtx, {
    type: "line",
    data: {
      labels: data.weightLabels || [],
      datasets: [
        {
          label: "Weight (kg)",
          data: data.weightData || [],
          borderColor: SECONDARY,
          backgroundColor: "rgba(0,212,170,0.08)",
          borderWidth: 2.5,
          pointBackgroundColor: SECONDARY,
          pointRadius: 4,
          pointHoverRadius: 6,
          tension: 0.4,
          fill: true,
          spanGaps: true,
        },
      ],
    },
    options: {
      ...BASE_CHART_OPTIONS,
      scales: {
        ...BASE_CHART_OPTIONS.scales,
        y: {
          ...BASE_CHART_OPTIONS.scales.y,
          min: minW,
          max: maxW,
          beginAtZero: false,
        },
      },
    },
  });
}

// ── #8 Count-up animation on stat numbers ─────────────────────
function countUp(el) {
  const target = parseFloat(el.dataset.target) || 0;
  const suffix = el.dataset.suffix || "";
  const dur = 1200;
  const step = 16;
  const inc = target / (dur / step);
  let current = 0;
  const timer = setInterval(() => {
    current += inc;
    if (current >= target) {
      current = target;
      clearInterval(timer);
    }
    el.textContent = (target % 1 === 0 ? Math.round(current) : current.toFixed(1)) + suffix;
  }, step);
}

// Run count-ups when elements enter the viewport
const countUpEls = document.querySelectorAll(".count-up");
if (countUpEls.length && "IntersectionObserver" in window) {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          countUp(entry.target);
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.5 },
  );
  countUpEls.forEach((el) => observer.observe(el));
} else {
  countUpEls.forEach(countUp);
}

// ── #8 Animated goal progress bars ────────────────────────────
const progressBars = document.querySelectorAll(".animate-fill");
if (progressBars.length && "IntersectionObserver" in window) {
  const barObs = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const bar = entry.target;
          const pct = bar.dataset.target + "%";
          setTimeout(() => {
            bar.style.width = pct;
          }, 100);
          barObs.unobserve(bar);
        }
      });
    },
    { threshold: 0.3 },
  );
  progressBars.forEach((b) => barObs.observe(b));
} else {
  progressBars.forEach((b) => {
    b.style.width = b.dataset.target + "%";
  });
}

// ── #8 Pulsing flame for 7+ day streak ───────────────────────
const flame = document.getElementById("streak-flame");
if (flame && data.streakCount >= 7) {
  flame.style.animation = "flame-pulse 1s ease-in-out infinite";
  flame.style.display = "inline-block";
}

// ── Goal Countdowns (Backward Timers) ───────────────────────
function updateCountdowns() {
  document.querySelectorAll('[data-deadline]').forEach(el => {
    const deadlineStr = el.dataset.deadline;
    if (!deadlineStr) return;

    const target = new Date(deadlineStr).getTime();
    const now = new Date().getTime();
    const diff = target - now;

    const timer = el.querySelector('.countdown-timer');
    if (!timer) return;

    if (diff <= 0) {
      timer.textContent = 'Past Deadline';
      el.style.color = 'var(--clr-danger)';
      return;
    }

    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const secs = Math.floor((diff % (1000 * 60)) / 1000);

    let parts = [];
    if (days > 0) parts.push(`${days}d`);
    if (hours > 0 || days > 0) parts.push(`${hours}h`);
    parts.push(`${mins}m`);
    if (days === 0) parts.push(`${secs}s`);

    timer.textContent = parts.join(' ') + ' left';
  });
}

setInterval(updateCountdowns, 1000);
updateCountdowns();
