/* goals.js — Goals page interactivity */

document.addEventListener('DOMContentLoaded', () => {

  // ── Animate progress bars on load ───────────────────────
  document.querySelectorAll('.goal-progress-fill').forEach(bar => {
    const target = bar.style.width;
    bar.style.width = '0%';
    requestAnimationFrame(() => {
      setTimeout(() => { bar.style.width = target; }, 100);
    });
  });

  // ── Goal card entrance animation ─────────────────────────
  document.querySelectorAll('.goal-card').forEach((card, i) => {
    card.style.opacity   = '0';
    card.style.transform = 'translateY(12px)';
    card.style.transition = `opacity 0.4s ease ${i * 50}ms, transform 0.4s ease ${i * 50}ms`;
    setTimeout(() => {
      card.style.opacity   = '1';
      card.style.transform = 'translateY(0)';
    }, 80);
  });

  // ── Set today as minimum deadline date ───────────────────
  const deadlineInput = document.getElementById('g-deadline');
  if (deadlineInput) {
    const today = new Date().toISOString().split('T')[0];
    deadlineInput.setAttribute('min', today);
  }

  // ── AJAX Create Goal ─────────────────────────────────────
  const goalForm = document.getElementById('goal-form');
  if (goalForm) {
    goalForm.addEventListener('submit', async e => {
      e.preventDefault();

      const titleInput = goalForm.querySelector('#g-title');
      const targetInput = goalForm.querySelector('#g-target');
      const currentInput = goalForm.querySelector('#g-current');

      // Simple validation
      if (!titleInput.value.trim()) {
        titleInput.focus();
        titleInput.style.borderColor = 'var(--clr-danger)';
        return;
      }

      if (targetInput.value && currentInput.value) {
        if (parseFloat(currentInput.value) > parseFloat(targetInput.value)) {
          alert('Current value cannot exceed target value.');
          currentInput.focus();
          return;
        }
      }

      const btn = goalForm.querySelector('button[type="submit"]');
      const originalText = btn.textContent;
      btn.disabled = true;
      btn.textContent = 'Saving...';

      const formData = new FormData(goalForm);
      try {
        const resp = await fetch(goalForm.action, {
          method: 'POST',
          body: formData,
          headers: {
            'X-Requested-With': 'XMLHttpRequest'
          }
        });
        const data = await resp.json();

        if (data.success) {
          addNewGoalToGrid(data.goal);
          goalForm.reset();
          if (window.showToast) window.showToast('Goal created! Let\'s crush it! 🎯', 'success');
        } else {
          if (window.showToast) window.showToast(data.error || 'Failed to create goal', 'error');
        }
      } catch (err) {
        if (window.showToast) window.showToast('Connection error', 'error');
      } finally {
        btn.disabled = false;
        btn.textContent = originalText;
      }
    });
  }

  function addNewGoalToGrid(goal) {
    const container = document.getElementById('active-goals-container');
    const countSpan = document.getElementById('active-count');
    const csrfToken = document.querySelector('input[name="csrf_token"]').value;

    if (countSpan) {
      countSpan.textContent = parseInt(countSpan.textContent) + 1;
    }

    let grid = document.getElementById('active-goals-grid');
    if (!grid) {
      container.innerHTML = `<div class="goals-grid" id="active-goals-grid"></div>`;
      grid = document.getElementById('active-goals-grid');
    }

    const card = document.createElement('div');
    card.className = 'goal-card';
    card.id = `goal-${goal.id}`;
    card.style.opacity = '0';
    card.style.transform = 'translateY(15px)';
    card.style.transition = 'all 0.5s cubic-bezier(0.16, 1, 0.3, 1)';

    let progressHtml = '';
    let updateFormHtml = '';
    if (goal.target_value) {
      progressHtml = `
        <div class="goal-card-progress">
          <div class="goal-progress-bar">
            <div class="goal-progress-fill" style="width: 0%"></div>
          </div>
          <span class="goal-progress-label">${goal.current_value} / ${goal.target_value} ${goal.unit || ''} · 0%</span>
        </div>
      `;
      updateFormHtml = `
        <form method="POST" action="/goals/update/${goal.id}" class="inline-form">
          <input type="hidden" name="csrf_token" value="${csrfToken}" />
          <input type="number" name="current_value" class="form-input input-sm" value="${goal.current_value}" step="0.1" />
          <button type="submit" class="btn-sm btn-secondary">Update</button>
        </form>
      `;
    }

    card.innerHTML = `
      <div class="goal-card-header">
        <span class="goal-category-badge goal-category--${goal.category}">${goal.category}</span>
        <h4 class="goal-card-title">${goal.title}</h4>
      </div>
      ${goal.description ? `<p class="goal-card-desc">${goal.description}</p>` : ''}
      ${progressHtml}
      ${goal.deadline ? `<p class="goal-deadline" data-deadline="${goal.deadline}">⏳ <span class="countdown-timer">Calculating...</span></p>` : ''}
      <div class="goal-card-actions">
        ${updateFormHtml}
        <form method="POST" action="/goals/complete/${goal.id}" style="display:inline;">
          <input type="hidden" name="csrf_token" value="${csrfToken}" />
          <button type="submit" class="btn-sm btn-success">✓ Complete</button>
        </form>
        <form method="POST" action="/goals/delete/${goal.id}" style="display:inline;">
          <input type="hidden" name="csrf_token" value="${csrfToken}" />
          <button type="submit" class="btn-sm btn-danger" onclick="return confirm('Delete this goal?')">✕</button>
        </form>
      </div>
    `;

    grid.insertBefore(card, grid.firstChild);

    // Animate entrance
    requestAnimationFrame(() => {
      card.style.opacity = '1';
      card.style.transform = 'translateY(0)';
      
      // Animate progress bar if it exists
      if (goal.target_value) {
        setTimeout(() => {
          const fill = card.querySelector('.goal-progress-fill');
          const label = card.querySelector('.goal-progress-label');
          if (fill) fill.style.width = goal.progress_percent + '%';
          if (label) label.textContent = `${goal.current_value} / ${goal.target_value} ${goal.unit || ''} · ${goal.progress_percent}%`;
        }, 100);
      }
    });
  }

  // ── Backward Timer (Countdown) ───────────────────────────
  function updateCountdowns() {
    document.querySelectorAll('.goal-deadline').forEach(el => {
      const deadlineStr = el.dataset.deadline;
      if (!deadlineStr) return;

      const target = new Date(deadlineStr).getTime();
      const now = new Date().getTime();
      const diff = target - now;

      const timer = el.querySelector('.countdown-timer');
      if (!timer) return;

      if (diff <= 0) {
        timer.textContent = 'Past Deadline';
        timer.parentElement.style.color = 'var(--clr-danger)';
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

  // ── Highlight update-inline input on focus ───────────────
  document.querySelectorAll('.goal-card-actions .form-input').forEach(input => {
    input.addEventListener('focus', () => {
      input.style.borderColor = 'var(--clr-primary)';
      input.style.boxShadow   = '0 0 0 3px rgba(108,99,255,0.15)';
    });
    input.addEventListener('blur', () => {
      input.style.borderColor = '';
      input.style.boxShadow   = '';
    });
  });

  // ── Confetti burst on completed goal badge ────────────────
  document.querySelectorAll('.goal-done-badge').forEach(badge => {
    badge.title = '🎉 Completed!';
  });
});
