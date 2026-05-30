// Popup script: metadata, highlights, save flow

const BRIDGE = 'http://localhost:7842/ingest';
const STATUS = 'http://localhost:7842/status';

let currentUrl = '';
let currentTabId = null;
let currentIsPdf = false;

function isPdfUrl(url) {
  return /\.pdf(\?|$)/i.test(url);
}

async function init() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) return;

  currentUrl = tab.url || '';
  currentTabId = tab.id;
  currentIsPdf = isPdfUrl(currentUrl);

  // Fill metadata
  document.getElementById('title-input').value = tab.title || '';
  document.getElementById('url-text').textContent = currentUrl;

  if (currentIsPdf) {
    document.getElementById('highlights-section').classList.add('hidden');
    document.getElementById('pdf-badge').classList.remove('hidden');
  }

  // Load highlights from storage (no-op for PDFs but harmless)
  await renderHighlights();

  // If the last ingestion finished for this tab's title, show the result instead of the form
  try {
    const statusRes = await fetch(STATUS);
    if (statusRes.ok) {
      const status = await statusRes.json();
      if (status.state === 'done' && status.title === (tab.title || '').trim()) {
        showSuccess(status.concepts || []);
      } else if (status.state === 'processing') {
        showView('view-processing');
        pollStatus(Date.now());
      }
    }
  } catch {
    // Bridge not running — stay on form view
  }
}

async function renderHighlights() {
  const key = `highlights_${currentUrl}`;
  const result = await chrome.storage.local.get([key]);
  const items = result[key] || [];
  const list = document.getElementById('highlights-list');
  list.innerHTML = '';

  if (items.length === 0) {
    const hint = document.createElement('div');
    hint.className = 'highlights-empty';
    hint.textContent = 'Select text on the page to highlight';
    list.appendChild(hint);
    return;
  }

  items.forEach((text, idx) => {
    const item = document.createElement('div');
    item.className = 'highlight-item';

    const span = document.createElement('span');
    span.className = 'highlight-text';
    span.textContent = text;

    const btn = document.createElement('button');
    btn.className = 'highlight-remove';
    btn.textContent = '×';
    btn.title = 'Remove highlight';
    btn.addEventListener('click', () => removeHighlight(idx));

    item.appendChild(span);
    item.appendChild(btn);
    list.appendChild(item);
  });
}

async function removeHighlight(idx) {
  const key = `highlights_${currentUrl}`;
  const result = await chrome.storage.local.get([key]);
  const items = result[key] || [];
  items.splice(idx, 1);
  await chrome.storage.local.set({ [key]: items });

  // Update badge
  chrome.runtime.sendMessage({
    type: 'updateBadge',
    url: currentUrl,
    count: items.length,
  });

  await renderHighlights();
}

function showView(id) {
  [
    'view-form', 'view-saving', 'view-processing',
    'view-success', 'view-duplicate', 'view-error', 'view-no-content',
  ].forEach((v) => {
    document.getElementById(v).classList.toggle('hidden', v !== id);
  });
}

function showSuccess(concepts) {
  const count = concepts.length;
  document.getElementById('success-title').textContent =
    count > 0 ? `${count} concept${count === 1 ? '' : 's'} extracted` : 'Saved to vault';

  const list = document.getElementById('concept-list');
  list.innerHTML = '';
  concepts.forEach((name) => {
    const el = document.createElement('div');
    el.className = 'concept-item';
    el.textContent = name;
    list.appendChild(el);
  });
  showView('view-success');
}

async function pollStatus(startTime) {
  const elapsed = Math.floor((Date.now() - startTime) / 1000);
  document.getElementById('processing-elapsed').textContent = `${elapsed}s elapsed`;

  try {
    const res = await fetch(STATUS);
    const data = await res.json();

    if (data.state === 'done') {
      showSuccess(data.concepts || []);
      return;
    }
    if (data.state === 'error') {
      document.getElementById('view-error').querySelector('.status-title').textContent =
        data.error || 'Extraction failed';
      showView('view-error');
      return;
    }
  } catch {
    // Bridge unreachable mid-poll — keep counting, macOS notification will still fire
  }

  setTimeout(() => pollStatus(startTime), 2000);
}

async function getPageContent() {
  try {
    const [{ result }] = await chrome.scripting.executeScript({
      target: { tabId: currentTabId },
      func: () => document.body.innerText,
    });
    return result || '';
  } catch {
    return '';
  }
}

async function save() {
  const title = document.getElementById('title-input').value.trim();
  const note = document.getElementById('note-input').value.trim();

  const key = `highlights_${currentUrl}`;
  const stored = await chrome.storage.local.get([key]);
  const highlights = stored[key] || [];

  let payload;
  if (currentIsPdf) {
    payload = { title, url: currentUrl, note, type: 'pdf' };
  } else {
    const content = await getPageContent();
    if (!content) {
      showView('view-no-content');
      return;
    }
    payload = { title, url: currentUrl, content, highlights, note };
  }

  showView('view-saving');
  document.getElementById('save-btn').disabled = true;

  try {
    const res = await fetch(BRIDGE, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (res.ok) {
      // Clear highlights and badge — sources file is written
      await chrome.storage.local.remove(key);
      chrome.runtime.sendMessage({ type: 'clearBadge', tabId: currentTabId });
      // Switch to live processing view and start polling
      showView('view-processing');
      pollStatus(Date.now());
    } else if (res.status === 409) {
      showView('view-duplicate');
    } else {
      showView('view-error');
    }
  } catch {
    showView('view-error');
  }
}

document.getElementById('save-btn').addEventListener('click', save);

// Auto-grow title textarea
const titleInput = document.getElementById('title-input');
titleInput.addEventListener('input', () => {
  titleInput.style.height = 'auto';
  titleInput.style.height = titleInput.scrollHeight + 'px';
});

init();
