/* auth.js — Toggle animation, avatar upload preview, password strength */

'use strict';

document.addEventListener('DOMContentLoaded', () => {

  const container = document.getElementById('auth-container');

  // ── Toggle between login / signup ──────────────────────────
  function switchMode(mode) {
    if (!container) return;
    container.dataset.mode = mode;
    // Update URL without reload so back button works
    const url = new URL(window.location.href);
    url.searchParams.set('mode', mode);
    window.history.replaceState({}, '', url.toString());
  }

  document.querySelectorAll('[data-target]').forEach(el => {
    el.addEventListener('click', () => switchMode(el.dataset.target));
  });

  // ── Password visibility toggle ──────────────────────────────
  document.querySelectorAll('.btn-toggle-pw').forEach(btn => {
    btn.addEventListener('click', () => {
      const input = document.getElementById(btn.dataset.target);
      if (!input) return;
      const isPassword = input.type === 'password';
      input.type   = isPassword ? 'text' : 'password';
      btn.textContent = isPassword ? '🙈' : '👁';
    });
  });

  // ── Password strength meter (signup) ───────────────────────
  const pwInput      = document.getElementById('su-password');
  const strengthFill = document.getElementById('strength-fill');
  const strengthLbl  = document.getElementById('strength-label');

  if (pwInput && strengthFill && strengthLbl) {
    pwInput.addEventListener('input', () => {
      const score = calcStrength(pwInput.value);
      const pct   = score * 25;
      strengthFill.style.width = `${pct}%`;
      const colors = ['#ff5252', '#ffa94d', '#ffd43b', '#40c97e'];
      const labels = ['Weak', 'Fair', 'Good', 'Strong'];
      strengthFill.style.backgroundColor = colors[score - 1] || '#ff5252';
      strengthLbl.textContent = pwInput.value.length === 0
        ? 'Password strength'
        : (labels[score - 1] || 'Very Weak');
    });
  }

  function calcStrength(pw) {
    let s = 0;
    if (pw.length >= 6)  s++;
    if (pw.length >= 10) s++;
    if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) s++;
    if (/\d/.test(pw) || /[^A-Za-z0-9]/.test(pw)) s++;
    return Math.max(s, pw.length > 0 ? 1 : 0);
  }

  // ── Animated submit buttons ─────────────────────────────────
  document.querySelectorAll('.btn-auth').forEach(btn => {
    btn.closest('form')?.addEventListener('submit', () => {
      btn.disabled = true;
      const span = btn.querySelector('.btn-text');
      if (span) span.textContent = 'Please wait…';
    });
  });

  // ── Signup avatar upload preview ────────────────────────────
  const signupAvatarZone  = document.getElementById('signup-avatar-zone');
  const signupAvatarInput = document.getElementById('signup-avatar-input');
  const signupAvatarPrev  = document.getElementById('signup-avatar-preview');
  const signupAvatarRow   = signupAvatarZone?.closest('.signup-avatar-row');

  if (signupAvatarZone && signupAvatarInput && signupAvatarPrev) {
    // Click on zone OR the whole row opens picker
    [signupAvatarZone, signupAvatarRow].forEach(el => {
      el?.addEventListener('click', e => {
        if (e.target === signupAvatarInput) return;
        signupAvatarInput.click();
      });
    });

    signupAvatarInput.addEventListener('change', () => {
      const file = signupAvatarInput.files?.[0];
      if (!file) return;
      if (!file.type.startsWith('image/')) {
        alert('Please select an image file.');
        return;
      }
      if (file.size > 8 * 1024 * 1024) {
        alert('Image must be under 8 MB.');
        return;
      }
      const reader = new FileReader();
      reader.onload = e => {
        signupAvatarPrev.src = e.target.result;
        signupAvatarPrev.style.border = '2px solid var(--clr-primary)';
        // Update label
        const label = document.querySelector('.signup-avatar-main');
        if (label) label.textContent = file.name.length > 22
          ? file.name.slice(0, 20) + '…'
          : file.name;
      };
      reader.readAsDataURL(file);
    });

    // Drag & drop on the row
    if (signupAvatarRow) {
      signupAvatarRow.addEventListener('dragover', e => {
        e.preventDefault();
        signupAvatarRow.style.borderColor = 'var(--clr-primary)';
      });
      signupAvatarRow.addEventListener('dragleave', () => {
        signupAvatarRow.style.borderColor = '';
      });
      signupAvatarRow.addEventListener('drop', e => {
        e.preventDefault();
        signupAvatarRow.style.borderColor = '';
        const file = e.dataTransfer?.files?.[0];
        if (file && file.type.startsWith('image/')) {
          const dt = new DataTransfer();
          dt.items.add(file);
          signupAvatarInput.files = dt.files;
          signupAvatarInput.dispatchEvent(new Event('change'));
        }
      });
    }
  }

  // ── Onboarding radio card selection ─────────────────────────
  document.querySelectorAll('.choice-card').forEach(card => {
    card.addEventListener('click', () => {
      const group = card.closest('.choice-grid');
      if (group) group.querySelectorAll('.choice-card').forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
    });
  });

});
