// ── Constants ─────────────────────────────────────────
const SAMPLE_PORTFOLIO = {
  risk_profile: "moderate",
  currency: "USD",
  market: "US",
  portfolio: {
    holdings: [
      { symbol: "NVDA", name: "Nvidia", asset_type: "stock", current_value: 6000, cost_basis: 4000 },
      { symbol: "AAPL", name: "Apple", asset_type: "stock", current_value: 2500, cost_basis: 2200 },
      { symbol: "VTI",  name: "Vanguard Total Stock Market ETF", asset_type: "etf", current_value: 1500, cost_basis: 1400 }
    ]
  }
};

// ── Initialise ────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const $input       = document.getElementById('user-input');
  const $sendBtn     = document.getElementById('send-btn');
  const $sendLabel   = document.getElementById('send-label');
  const $responseArea = document.getElementById('response-area');
  const $portfolioToggle = document.getElementById('portfolio-toggle');
  const $portfolioHint   = document.getElementById('portfolio-hint');

  // ── Health check ────────────────────────────────────
  fetch('/health')
    .then(r => r.json())
    .then(d => {
      const dot  = document.getElementById('status-dot');
      const text = document.getElementById('status-text');
      if (d.status === 'ok') {
        dot.classList.add('online');
        text.textContent = 'Backend Online';
      } else {
        dot.classList.add('offline');
        text.textContent = 'Backend Offline';
      }
    })
    .catch(() => {
      const dot  = document.getElementById('status-dot');
      const text = document.getElementById('status-text');
      dot.classList.add('offline');
      text.textContent = 'Backend Offline';
    });

  // ── Portfolio toggle label ───────────────────────────
  $portfolioToggle.addEventListener('change', () => {
    $portfolioHint.textContent = $portfolioToggle.checked
      ? 'Sample portfolio is ACTIVE — will be sent with next request.'
      : 'Enable to send sample holdings with your request.';
  });

  // ── Quick prompt chips ───────────────────────────────
  document.querySelectorAll('.qchip').forEach(btn => {
    btn.addEventListener('click', () => {
      $input.value = btn.dataset.q;
      $input.focus();
    });
  });

  // ── Send on Enter ────────────────────────────────────
  $input.addEventListener('keypress', e => {
    if (e.key === 'Enter' && !$sendBtn.disabled) sendMessage();
  });
  $sendBtn.addEventListener('click', sendMessage);

  // ── Pipeline helpers ─────────────────────────────────
  function setPipe(id, state, label) {
    const step = document.getElementById('pipe-' + id);
    if (!step) return;
    const dot  = step.querySelector('.pipe-dot');
    const stEl = document.getElementById('pipe-' + id + '-state');
    dot.className = 'pipe-dot ' + state;
    if (stEl && label !== undefined) stEl.textContent = label;
  }

  function resetPipeline() {
    setPipe('safety',     'idle', 'Idle');
    setPipe('classifier', 'idle', 'Idle');
    setPipe('agent',      'idle', '—');
    setPipe('stream',     'idle', 'Idle');
  }

  // ── Render helpers ───────────────────────────────────

  function el(tag, cls, inner) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (inner !== undefined) e.innerHTML = inner;
    return e;
  }

  function renderClassifier(parsed) {
    const agent = parsed.agent || parsed.intent || '—';
    const row = el('div', 'resp-classifier',
      `<svg width="8" height="8" viewBox="0 0 8 8"><circle cx="4" cy="4" r="4" fill="#05a049"/></svg>
       Routed to agent: <span class="resp-classifier-badge">${agent}</span>`);
    return row;
  }

  function renderAgentResponse(parsed) {
    const p = parsed.payload || {};
    const frag = document.createDocumentFragment();

    // --- Stub response ---
    if (p.target_agent && p.message && p.message.toLowerCase().includes('not implemented')) {
      const card = el('div', 'resp-stub',
        `<strong>Agent: ${p.target_agent}</strong>
         This specialist agent is not implemented in this assignment build.`);
      frag.appendChild(card);
      return frag;
    }

    // --- Concentration risk metric card ---
    if (p.concentration_risk) {
      const cr = p.concentration_risk;
      const flag = (cr.flag || 'low').toLowerCase();
      const riskClass = flag === 'high' ? 'risk-high' : flag === 'medium' ? 'risk-medium' : 'risk-low';
      const flagIcon  = flag === 'high' ? '🔴' : flag === 'medium' ? '🟡' : '🟢';

      const card = el('div', 'resp-card');
      card.innerHTML = `<div class="resp-card-title">Concentration Risk</div>
        <div style="display:flex;align-items:center;gap:0.75rem;flex-wrap:wrap">
          <span class="risk-badge ${riskClass}">${flagIcon} ${flag.toUpperCase()}</span>
          ${cr.top_holding     ? `<span style="font-size:0.85rem">Top: <strong>${cr.top_holding}</strong></span>` : ''}
          ${cr.top_position_pct != null ? `<span style="font-size:0.85rem;color:#66736b">${cr.top_position_pct}% of portfolio</span>` : ''}
        </div>`;
      frag.appendChild(card);
    }

    // --- Observations ---
    if (p.observations && p.observations.length > 0) {
      const card = el('div', 'resp-card');
      card.innerHTML = `<div class="resp-card-title">Analysis</div>`;
      const list = el('ul', 'resp-obs');
      p.observations.forEach(obs => {
        const sev  = obs.severity || 'info';
        const icon = sev === 'warning' ? '⚠️' : sev === 'critical' ? '🔴' : sev === 'ok' ? '✅' : 'ℹ️';
        const li = el('li', '', `${icon} ${obs.text}`);
        list.appendChild(li);
      });
      card.appendChild(list);
      frag.appendChild(card);
    }

    // --- Fallback: no structured data ---
    if (!p.concentration_risk && !(p.observations && p.observations.length)) {
      // Show stub or message fallback
      const hasMsg = p.message;
      const card = el('div', 'resp-stub',
        hasMsg
          ? `<strong>${p.target_agent || 'Agent'}</strong>${p.message}`
          : `<strong>${p.target_agent || 'Agent'}</strong>This specialist agent is not implemented in this assignment build.`
      );
      frag.appendChild(card);
    }

    // --- Disclaimer ---
    if (p.disclaimer) {
      const disc = el('p', 'resp-disclaimer', `📋 ${p.disclaimer}`);
      frag.appendChild(disc);
    }

    // --- Raw JSON toggle ---
    const raw = el('div', '');
    const toggle = el('button', 'raw-toggle', 'Show raw JSON ▾');
    const rawBlock = el('pre', 'raw-block', JSON.stringify(p, null, 2));
    rawBlock.id = 'raw-' + Date.now();
    toggle.addEventListener('click', () => {
      rawBlock.classList.toggle('visible');
      toggle.textContent = rawBlock.classList.contains('visible') ? 'Hide raw JSON ▴' : 'Show raw JSON ▾';
    });
    raw.appendChild(toggle);
    raw.appendChild(rawBlock);
    frag.appendChild(raw);

    return frag;
  }

  function renderSafety(parsed) {
    const cat = (parsed.category || 'policy_violation').replace(/_/g, ' ');
    const msg = parsed.message || 'This query cannot be processed due to safety policies.';
    const card = el('div', 'resp-safety',
      `<div class="resp-safety-header">🚫 Safety Guard Blocked Request <span class="resp-safety-cat">${cat}</span></div>
       <p class="resp-safety-msg">${msg}</p>`);
    return card;
  }

  function renderError(parsed) {
    const card = el('div', 'resp-error',
      `<div class="resp-error-header">⚠️ Error</div>
       <p>${parsed.message || 'An unexpected error occurred.'}</p>`);
    return card;
  }

  // ── Main send function ───────────────────────────────
  async function sendMessage() {
    const text = $input.value.trim();
    if (!text) return;

    $input.value = '';
    $sendBtn.disabled = true;
    $sendLabel.textContent = 'Streaming…';
    resetPipeline();

    // Clear placeholder, add user bubble
    $responseArea.innerHTML = '';
    const userBubble = el('div', 'resp-bubble-user', text);
    $responseArea.appendChild(userBubble);

    // Thinking state
    const aiBubble = el('div', 'resp-bubble');
    const thinkDiv = el('div', 'thinking',
      `<div class="thinking-dots"><span></span><span></span><span></span></div> Valura AI is thinking…`);
    aiBubble.appendChild(thinkDiv);
    $responseArea.appendChild(aiBubble);
    $responseArea.scrollTop = $responseArea.scrollHeight;

    // Build request body
    const body = {
      message: text,
      user_id: 'user_001',
      session_id: 'dashboard-session',
    };
    if ($portfolioToggle.checked) {
      body.user_context = SAMPLE_PORTFOLIO;
    }

    let hasContent = false;
    let isDone = false;

    try {
      setPipe('safety', 'running', 'Running…');

      const resp = await fetch('/v1/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      const reader  = resp.body.getReader();
      const decoder = new TextDecoder();

      // Remove thinking indicator once stream starts
      thinkDiv.remove();

      while (!isDone) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const dataStr = line.slice(6).trim();

          if (dataStr === '[DONE]') {
            isDone = true;
            setPipe('stream', 'pass', 'Done');
            break;
          }
          if (!dataStr) continue;

          try {
            const parsed = JSON.parse(dataStr);

            if (parsed.type === 'classifier') {
              setPipe('safety',     'pass', 'Passed ✓');
              setPipe('classifier', 'pass', parsed.agent || parsed.intent || '—');
              setPipe('agent',      'pass', parsed.agent || '—');
              setPipe('stream',     'running', 'Streaming…');

              aiBubble.appendChild(renderClassifier(parsed));
              hasContent = true;

            } else if (parsed.type === 'agent_response') {
              const frag = renderAgentResponse(parsed);
              aiBubble.appendChild(frag);
              hasContent = true;

            } else if (parsed.type === 'safety') {
              setPipe('safety', 'fail', 'Blocked 🚫');
              aiBubble.appendChild(renderSafety(parsed));
              hasContent = true;

            } else if (parsed.type === 'error') {
              setPipe('safety', 'fail', 'Error');
              aiBubble.appendChild(renderError(parsed));
              hasContent = true;
            }

            $responseArea.scrollTop = $responseArea.scrollHeight;

          } catch (_) { /* skip unparseable */ }
        }
      }

    } catch (err) {
      thinkDiv.remove();
      aiBubble.appendChild(renderError({ message: 'Connection error. Please check the server.' }));
    }

    if (!hasContent) {
      aiBubble.innerHTML = '<span style="color:#66736b;font-size:0.88rem">No response received.</span>';
    }

    $sendBtn.disabled = false;
    $sendLabel.textContent = 'Ask';
    $responseArea.scrollTop = $responseArea.scrollHeight;
  }
});
