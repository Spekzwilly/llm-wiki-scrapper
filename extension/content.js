// Content script: text selection → highlight tooltip → chrome.storage

let tooltip = null;
let pendingText = '';

document.addEventListener('mouseup', (e) => {
  if (tooltip && tooltip.contains(e.target)) return;

  const sel = window.getSelection();
  const text = sel ? sel.toString().trim() : '';

  removeTooltip();

  if (text.length >= 10) {
    pendingText = text;
    showTooltip(sel.getRangeAt(0));
  }
});

// Dismiss tooltip on click outside
document.addEventListener('mousedown', (e) => {
  if (tooltip && !tooltip.contains(e.target)) {
    removeTooltip();
    pendingText = '';
  }
});

function removeTooltip() {
  if (tooltip) {
    tooltip.remove();
    tooltip = null;
  }
}

function showTooltip(range) {
  const rect = range.getBoundingClientRect();

  tooltip = document.createElement('div');
  tooltip.style.cssText = `
    position: fixed;
    top: ${Math.max(8, rect.top - 44)}px;
    left: ${rect.left + rect.width / 2}px;
    transform: translateX(-50%);
    background: #1e1e2e;
    color: #cdd6f4;
    padding: 6px 14px;
    border-radius: 8px;
    font-size: 13px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    cursor: pointer;
    z-index: 2147483647;
    white-space: nowrap;
    box-shadow: 0 4px 16px rgba(0,0,0,0.4);
    border: 1px solid rgba(99,102,241,0.4);
    user-select: none;
    pointer-events: all;
  `;
  tooltip.textContent = '✦ Add to Highlights';

  tooltip.addEventListener('mousedown', (e) => {
    e.stopPropagation();
    e.preventDefault();
    const captured = pendingText;
    removeTooltip();
    pendingText = '';
    window.getSelection().removeAllRanges();
    storeHighlight(captured);
  });

  document.body.appendChild(tooltip);

  // Flip below selection if tooltip would clip above viewport
  const tipRect = tooltip.getBoundingClientRect();
  if (tipRect.top < 0) {
    tooltip.style.top = `${rect.bottom + 8}px`;
  }
}

function storeHighlight(text) {
  const url = location.href;
  const key = `highlights_${url}`;
  chrome.storage.local.get([key], (result) => {
    const updated = [...(result[key] || []), text];
    chrome.storage.local.set({ [key]: updated }, () => {
      chrome.runtime.sendMessage({ type: 'updateBadge', url, count: updated.length });
    });
  });
}

// Respond to popup requesting page content
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.type === 'getPageContent') {
    sendResponse({ content: document.body.innerText || '' });
  }
});
