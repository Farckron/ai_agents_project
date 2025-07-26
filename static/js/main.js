// static/js/main.js

document.addEventListener('DOMContentLoaded', () => {
    initStatusChecks();
    bindProcessRequest();
    bindUtilityLinks();
    bindAgentResetButtons();
  });
  
  function bindProcessRequest() {
    const btn = document.getElementById('submit-request');
    if (btn) btn.addEventListener('click', processRequest);
  }
  
  function bindUtilityLinks() {
    const viewLogs = document.getElementById('view-logs');
    if (viewLogs) {
      viewLogs.addEventListener('click', async (e) => {
        e.preventDefault();
        const res = await fetch('/logs');
        const lines = await res.json().catch(() => []);
        console.log('--- server logs ---\n' + (lines || []).join('\n'));
        alert('Logs printed to console.');
      });
    }
    const clearSession = document.getElementById('clear-session');
    if (clearSession) {
      clearSession.addEventListener('click', async (e) => {
        e.preventDefault();
        const res = await fetch('/api/session/clear', { method: 'POST' });
        if (res.ok) alert('Session cleared.');
      });
    }
  }
  
  function bindAgentResetButtons() {
    document.querySelectorAll('.agent-card .reset-agent').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const card = btn.closest('.agent-card');
        const agent = card?.dataset.agent;
        if (!agent) return;
        const res = await fetch(`/api/agents/${agent}/reset`, { method: 'POST' });
        if (!res.ok) return;
        const statusEl = card.querySelector('.agent-status');
        if (statusEl) statusEl.textContent = 'Loading...';
        const msgEl = card.querySelector('[data-stat="message_count"]');
        const tmpEl = card.querySelector('[data-stat="temperature"]');
        if (msgEl) msgEl.textContent = '-';
        if (tmpEl) tmpEl.textContent = '-';
        checkAgentStatus(agent);
      });
    });
  }
  
  // ──────────────────────────────────────────────────────────────
  // System & Agents
  // ──────────────────────────────────────────────────────────────
  
  async function initStatusChecks() {
    await checkSystemStatus();
    const agents = Array.from(document.querySelectorAll('.agent-card'))
      .map(c => c.dataset.agent)
      .filter(Boolean);
    for (const agent of agents) checkAgentStatus(agent);
  }
  
  async function checkSystemStatus() {
    let dot      = document.getElementById('systemStatusDot') || document.getElementById('system-status');
    let maxEl    = document.getElementById('maxMessages')     || document.getElementById('max-messages');
    let openaiEl = document.getElementById('openaiStatus')     || document.getElementById('openai-status');
    let ghEl     = document.getElementById('githubStatus')     || document.getElementById('github-status');
  
    try {
      const res = await fetch('/api/status');
      const { system, openai, github } = await res.json();
      if (dot)   { dot.classList.remove('offline'); dot.classList.add('online'); }
      if (maxEl) maxEl.textContent = system?.max_messages ?? '';
      if (openaiEl) openaiEl.textContent = openai?.api_key_valid ? '✔️' : '❌';
      if (ghEl)     ghEl.textContent     = github?.token_configured ? '✔️' : '❌';
    } catch {}
  }
  
  async function checkAgentStatus(agentName) {
    const card = document.querySelector(`.agent-card[data-agent="${agentName}"]`);
    if (!card) return;
    const statusEl = card.querySelector('.agent-status');
  
    try {
      const res  = await fetch(`/api/agents/${agentName}/status`);
      const json = await res.json();
      if (statusEl) { statusEl.textContent = 'Online'; statusEl.classList.remove('loading'); }
      const msgs = card.querySelector('[data-stat="message_count"]');
      const temp = card.querySelector('[data-stat="temperature"]');
      if (msgs) msgs.textContent = (json.message_count ?? '-').toString();
      if (temp) temp.textContent = (json.temperature   ?? '-').toString();
    } catch {
      if (statusEl) { statusEl.textContent = 'Offline'; statusEl.classList.remove('loading'); }
    }
  }
  
  // ──────────────────────────────────────────────────────────────
  // Request → Task → Polling (+ прогрес‑кроки)
  // ──────────────────────────────────────────────────────────────
  
  async function processRequest() {
    clearToast();
    const btn = document.getElementById('submit-request');
    const userRequest = document.getElementById('user-request')?.value || '';
    const repoUrl     = document.getElementById('repo-url')?.value || '';
  
    if (btn) btn.disabled = true;
    setStep(1, 'Repository Analysis');
    showProgress(true, 'Submitting request...');
  
    hideResultPanel();
  
    try {
      const res  = await fetch('/api/pr/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_request: userRequest, repo_url: repoUrl })
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || 'Server error');
      startTaskPolling(data.task_id);
    } catch (err) {
      showToast(`Error: ${err.message}`);
      showProgress(false);
    } finally {
      if (btn) btn.disabled = false;
    }
  }
  
  function startTaskPolling(taskId) {
    updateProgress(25, 'Queued / Processing...');
    setStep(2, 'Request Analysis');
  
    const timer = setInterval(async () => {
      try {
        const res = await fetch(`/api/async/task/${taskId}/status`);
        const data = await res.json();
  
        if (data.status === 'processing') {
          updateProgress(60, 'Generating code...');
          setStep(3, 'Code Planning');
        }
  
        if (data.status === 'completed' || data.status === 'failed') {
          clearInterval(timer);
          if (data.status === 'completed') {
            updateProgress(100, 'Completed');
            setStep(4, 'Implementation');
            renderResult(data.result || {});
            showToast('PR workflow completed');
          } else {
            showProgress(false);
            showToast(`PR failed: ${data.error || 'Unknown error'}`);
          }
        }
      } catch (e) {
        clearInterval(timer);
        showProgress(false);
        showToast(`Polling error: ${e.message}`);
      }
    }, 1200);
  }
  
  function setStep(stepNumber, label) {
    const sec = document.getElementById('progress-section');
    if (!sec) return;
    const steps = Array.from(sec.querySelectorAll('.progress-steps .step'));
    steps.forEach((el, idx) => {
      el.classList.toggle('active', (idx + 1) <= stepNumber);
    });
    const cur = document.getElementById('current-status');
    if (cur) cur.querySelector('span').textContent = label;
  }
  
  function showProgress(show, label = 'Processing...') {
    const section = document.getElementById('progress-section');
    const cur = document.getElementById('current-status');
    if (!section || !cur) return;
    section.style.display = show ? 'block' : 'none';
    if (show) cur.querySelector('span').textContent = label;
  }
  
  function updateProgress(percent, label) {
    const fill = document.getElementById('progress-fill');
    const cur = document.getElementById('current-status');
    if (!fill || !cur) return;
    fill.style.width = Math.max(0, Math.min(100, percent)) + '%';
    if (label) cur.querySelector('span').textContent = label;
  }
  
  // ──────────────────────────────────────────────────────────────
  // Result panel
  // ──────────────────────────────────────────────────────────────
  
  function hideResultPanel() {
    const p = document.getElementById('result-panel');
    if (p) p.style.display = 'none';
  }
  
  function renderResult(result) {
    const panel = document.getElementById('result-panel');
    const list  = document.getElementById('result-file-list');
    const title = document.getElementById('result-title');
    const code  = document.getElementById('result-code');
    const prBox = document.getElementById('result-pr');
  
    if (!panel || !list || !title || !code || !prBox) return;
  
    prBox.innerHTML = '';
    if (result.pr_result?.created && result.pr_result?.pr_url) {
      const a = document.createElement('a');
      a.href = result.pr_result.pr_url;
      a.target = '_blank';
      a.rel = 'noopener';
      a.textContent = 'View Pull Request';
      prBox.appendChild(a);
    } else if (result.pr_result?.error) {
      prBox.textContent = `PR not created: ${result.pr_result.error}`;
    } else {
      prBox.textContent = 'PR not created (no GitHub token or error).';
    }
  
    list.innerHTML = '';
    const files = result.generated_files || [];
    if (!files.length) {
      title.textContent = 'No files generated';
      code.textContent = '';
      panel.style.display = 'block';
      return;
    }
  
    files.forEach((f, idx) => {
      const li = document.createElement('li');
      const btn = document.createElement('button');
      btn.className = 'button is-small';
      btn.textContent = f.path;
      btn.addEventListener('click', () => {
        title.textContent = f.path;
        code.textContent = f.content || '';
      });
      li.appendChild(btn);
      list.appendChild(li);
      if (idx === 0) {
        title.textContent = f.path;
        code.textContent = f.content || '';
      }
    });
  
    panel.style.display = 'block';
  }
  
  // ──────────────────────────────────────────────────────────────
  function clearToast() {
    const t = document.getElementById('toast');
    if (t) t.remove();
  }
  function showToast(msg) {
    let toast = document.getElementById('toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'toast';
      toast.className = 'notification is-danger';
      document.body.appendChild(toast);
    }
    toast.textContent = msg;
  }
  