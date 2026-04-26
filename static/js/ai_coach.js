/* ai_coach.js — AI Coach chat + daily plan page interactivity */
'use strict';

// Read CSRF token from meta tag (set in base.html)
function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute('content') : '';
}

/* ─── Daily Plan: Generate button → loading overlay ──────── */
const generateForm = document.getElementById('generate-form');
if (generateForm) {
  generateForm.addEventListener('submit', () => {
    const btn = document.getElementById('generate-btn');
    if (btn) {
      btn.disabled = true;
      btn.querySelector('.btn-generate-icon').textContent = '⏳';
      btn.querySelector('.btn-generate-text').textContent = 'Generating…';
    }

    // Show full-page loading overlay
    const overlay = document.createElement('div');
    overlay.className = 'page-loading-overlay';
    overlay.innerHTML = `
      <div class="page-loading-spinner"></div>
      <div class="page-loading-text">
        Generating your personalised plan<span class="page-loading-dots"></span>
      </div>
      <p style="color:var(--clr-text-muted);font-size:0.85rem;margin-top:-0.5rem;">
        Gemini AI is crafting workouts &amp; meals just for you
      </p>
    `;
    document.body.appendChild(overlay);
  });
}

/* ─── AI Coach Chat ───────────────────────────────────────── */
const chatApiUrl      = window.CHAT_API_URL || null;
const chatWindow      = document.getElementById('chat-window');
const typingIndicator = document.getElementById('typing-indicator');
const chatInput       = document.getElementById('chat-input');
const sendBtn         = document.getElementById('send-btn');

if (!chatApiUrl || !chatWindow) {
  // Not on the coach page
} else {
  const conversationHistory = [];

  /* ── Render a message bubble ── */
  function appendMessage(text, role) {
    const msg = document.createElement('div');
    msg.className = `chat-msg chat-msg--${role}`;
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble chat-bubble--${role}`;
    bubble.textContent = text;
    msg.appendChild(bubble);
    chatWindow.appendChild(msg);
    chatWindow.scrollTop = chatWindow.scrollHeight;
    return bubble;
  }

  /* ── Typewriter effect for AI responses ── */
  function typeWriter(bubble, text, speed = 12) {
    bubble.textContent = '';
    let i = 0;
    const interval = setInterval(() => {
      bubble.textContent += text[i];
      i++;
      chatWindow.scrollTop = chatWindow.scrollHeight;
      if (i >= text.length) clearInterval(interval);
    }, speed);
  }

  /* ── Send message ── */
  async function sendMessage() {
    const text = (chatInput.value || '').trim();
    if (!text) return;

    chatInput.value = '';
    chatInput.style.height = 'auto';
    sendBtn.disabled = true;

    appendMessage(text, 'user');
    conversationHistory.push({ role: 'user', parts: [text] });

    if (typingIndicator) typingIndicator.style.display = 'flex';
    chatWindow.scrollTop = chatWindow.scrollHeight;

    try {
      const resp = await fetch(chatApiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({
          message: text,
          history: conversationHistory.slice(-10),
        }),
      });
      const data  = await resp.json();
      const reply = data.reply || 'Sorry, I could not generate a response.';
      conversationHistory.push({ role: 'model', parts: [reply] });

      const bubble = appendMessage('', 'ai');
      typeWriter(bubble, reply);

    } catch (err) {
      appendMessage('⚠️ Network error. Please try again.', 'ai');
    } finally {
      if (typingIndicator) typingIndicator.style.display = 'none';
      sendBtn.disabled = false;
      chatInput.focus();
    }
  }

  if (sendBtn) sendBtn.addEventListener('click', sendMessage);

  if (chatInput) {
    chatInput.addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });
    chatInput.addEventListener('input', () => {
      chatInput.style.height = 'auto';
      chatInput.style.height = Math.min(chatInput.scrollHeight, 140) + 'px';
    });
  }

  /* ── Suggestion chips ── */
  document.querySelectorAll('.suggestion-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      if (chatInput) {
        chatInput.value = chip.dataset.msg;
        const bar = document.getElementById('suggestions-bar');
        if (bar) bar.style.display = 'none';
        sendMessage();
      }
    });
  });

  /* ── Voice Input (Web Speech API) ── */
  const voiceBtn = document.getElementById('voice-btn');
  if (voiceBtn && ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)) {
    voiceBtn.style.display = 'flex';
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SR();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    let isListening = false;

    voiceBtn.addEventListener('click', () => {
      if (isListening) {
        recognition.stop();
      } else {
        recognition.start();
        isListening = true;
        voiceBtn.classList.add('listening');
        voiceBtn.title = 'Listening… click to stop';
        if (window.showToast) showToast('🎤 Listening… speak now', 'info');
      }
    });

    recognition.addEventListener('result', e => {
      const transcript = e.results[0][0].transcript;
      if (chatInput) {
        chatInput.value = transcript;
        chatInput.dispatchEvent(new Event('input'));
      }
    });
    recognition.addEventListener('end', () => {
      isListening = false;
      voiceBtn.classList.remove('listening');
      voiceBtn.title = 'Voice input';
      // Auto-send if transcript was captured
      if (chatInput && chatInput.value.trim()) sendMessage();
    });
    recognition.addEventListener('error', () => {
      isListening = false;
      voiceBtn.classList.remove('listening');
      if (window.showToast) showToast('Voice input not available.', 'warning');
    });
  } else if (voiceBtn) {
    voiceBtn.style.display = 'none'; // hide if not supported
  }

  if (chatInput) chatInput.focus();
}

/* ─── Daily Plan: Tab Switching ──────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  const tabBtns = document.querySelectorAll('.ai-tab-btn');
  const panes = document.querySelectorAll('.ai-tab-pane');

  if (tabBtns.length > 0) {
    tabBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const target = btn.dataset.target;

        // Update buttons
        tabBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // Update panes
        panes.forEach(pane => {
          pane.classList.remove('active');
          if (pane.id === target) {
            pane.classList.add('active');
          }
        });

        // Optional: Save preference to localStorage
        localStorage.setItem('fitai-active-tab', target);
      });
    });

    // Restore last active tab
    const lastTab = localStorage.getItem('fitai-active-tab');
    if (lastTab) {
      const targetBtn = document.querySelector(`.ai-tab-btn[data-target="${lastTab}"]`);
      if (targetBtn) targetBtn.click();
    }
  }

  // ── Format Generated Time (Local Timezone + 12h) ──────────
  const genTimeEl = document.querySelector('.ai-gen-time');
  if (genTimeEl) {
    let utcStr = genTimeEl.dataset.utcTime;
    if (utcStr) {
      // Ensure UTC by adding Z if not present
      if (!utcStr.endsWith('Z') && !utcStr.includes('+')) utcStr += 'Z';
      
      const date = new Date(utcStr);
      if (!isNaN(date.getTime())) {
        const options = { 
          month: 'long', 
          day: 'numeric', 
          year: 'numeric', 
          hour: 'numeric', 
          minute: '2-digit', 
          hour12: true 
        };
        const formatted = date.toLocaleString(undefined, options);
        const target = document.getElementById('formatted-gen-time');
        if (target) target.textContent = formatted;
      }
    }
  }
});
