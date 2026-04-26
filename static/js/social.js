/* social.js — Friend search debounce & chat enhancements */

document.addEventListener('DOMContentLoaded', () => {

  // ── Debounced live search (fires after 500ms of no typing) ──
  const searchInput = document.getElementById('friend-search');
  const searchForm  = searchInput?.closest('form');
  let searchTimer;

  if (searchInput && searchForm) {
    searchInput.addEventListener('input', () => {
      clearTimeout(searchTimer);
      const q = searchInput.value.trim();
      if (q.length === 0) return; // Don't auto-search on empty
      searchTimer = setTimeout(() => {
        searchForm.submit();
      }, 600);
    });

    // Highlight matching text in results
    searchInput.addEventListener('focus', () => {
      searchInput.select();
    });
  }

  // ── Accept/Reject request confirmation ──────────────────
  document.querySelectorAll('.request-actions form').forEach(form => {
    const btn = form.querySelector('button');
    if (btn && btn.classList.contains('btn-danger')) {
      form.addEventListener('submit', e => {
        if (!confirm('Reject this friend request?')) e.preventDefault();
      });
    }
  });

  // ── Animate friend cards on load ─────────────────────────
  document.querySelectorAll('.friend-card').forEach((card, i) => {
    card.style.opacity   = '0';
    card.style.transform = 'translateY(16px)';
    card.style.transition = `opacity 0.4s ease ${i * 60}ms, transform 0.4s ease ${i * 60}ms`;
    setTimeout(() => {
      card.style.opacity   = '1';
      card.style.transform = 'translateY(0)';
    }, 50);
  });
});
