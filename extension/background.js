// Background service worker: badge management

chrome.runtime.onMessage.addListener((msg, sender) => {
  if (msg.type === 'updateBadge') {
    setBadge(sender.tab?.id, msg.count);
  }
  if (msg.type === 'clearBadge' && msg.tabId != null) {
    chrome.action.setBadgeText({ text: '', tabId: msg.tabId });
  }
});

// Refresh badge when user switches tabs
chrome.tabs.onActivated.addListener(({ tabId }) => {
  chrome.tabs.get(tabId, (tab) => {
    if (tab?.url) loadAndSetBadge(tabId, tab.url);
  });
});

// Refresh badge when a page finishes loading (URL may have changed)
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url) {
    loadAndSetBadge(tabId, tab.url);
  }
});

function loadAndSetBadge(tabId, url) {
  const key = `highlights_${url}`;
  chrome.storage.local.get([key], (result) => {
    setBadge(tabId, (result[key] || []).length);
  });
}

function setBadge(tabId, count) {
  const text = count > 0 ? String(count) : '';
  const opts = tabId != null ? { text, tabId } : { text };
  chrome.action.setBadgeText(opts);
  if (count > 0 && tabId != null) {
    chrome.action.setBadgeBackgroundColor({ color: '#6366f1', tabId });
  }
}
