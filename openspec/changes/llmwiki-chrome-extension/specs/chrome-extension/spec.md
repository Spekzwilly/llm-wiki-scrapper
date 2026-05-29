## ADDED Requirements

### Requirement: Content script captures text selections

The content script SHALL listen for `mouseup` events on the active page and display a floating "Add to Highlights" button above any text selection of 10 or more characters. The button SHALL NOT appear when the selection originates inside the extension popup.

#### Scenario: Short selection ignored

- **WHEN** user selects fewer than 10 characters on the page
- **THEN** no tooltip appears

#### Scenario: Valid selection shows tooltip

- **WHEN** user selects 10 or more characters on the page
- **THEN** a floating "Add to Highlights" button appears above the selected text

#### Scenario: Tooltip dismisses on click outside

- **WHEN** user clicks anywhere outside the tooltip without clicking the button
- **THEN** the tooltip disappears and the selection is discarded

---

### Requirement: Highlights stored per URL

The content script SHALL store accepted highlights in `chrome.storage.local` under the key `highlights_<url>` as a JSON array of strings. Highlights SHALL persist across popup open/close cycles and page navigations until explicitly removed or the article is saved.

#### Scenario: Highlight added to storage

- **WHEN** user clicks "Add to Highlights" in the tooltip
- **THEN** the selected text is appended to `chrome.storage.local["highlights_<url>"]`
- **AND** the tooltip disappears
- **AND** the text selection is cleared

#### Scenario: Highlights survive popup close

- **WHEN** user adds a highlight then closes the popup
- **THEN** the highlight is still present when the popup is reopened on the same tab

---

### Requirement: Extension icon badge shows highlight count

The background script SHALL update the extension icon badge to display the number of stored highlights for the currently active tab. The badge SHALL be cleared when highlights are removed or after a successful save.

#### Scenario: Badge shows count

- **WHEN** the active tab has 2 stored highlights
- **THEN** the extension icon badge displays "2"

#### Scenario: Badge cleared after save

- **WHEN** a save completes successfully
- **THEN** the extension icon badge is cleared to empty

---

### Requirement: Popup auto-fills article metadata

The popup SHALL read the active tab's title and URL via the `chrome.tabs` API and pre-populate the title field (editable) and URL display (read-only, muted style) on open.

#### Scenario: Popup opens with title and URL

- **WHEN** user opens the popup on an article page
- **THEN** the title field contains the page title
- **AND** the URL is displayed in muted text below the title

---

### Requirement: Popup renders highlights with removal

The popup SHALL load stored highlights for the current tab URL from `chrome.storage.local` and render each as a list item with a × remove button. When no highlights exist, a hint reading "Select text on the page to highlight" SHALL be displayed.

#### Scenario: Highlights listed with remove button

- **WHEN** the current tab has 2 stored highlights
- **THEN** both are shown as list items with × buttons

#### Scenario: Removing a highlight

- **WHEN** user clicks × on a highlight
- **THEN** the highlight is removed from the list and from `chrome.storage.local`
- **AND** the badge count decreases by 1

#### Scenario: Empty highlights state

- **WHEN** no highlights are stored for the current tab
- **THEN** the hint "Select text on the page to highlight" is shown

---

### Requirement: Popup saves article to bridge server

The popup SHALL POST to `http://localhost:7842/ingest` with the payload `{title, url, content, highlights, note}` when the user clicks Save. The content field SHALL contain the page's readable text extracted by the content script.

#### Scenario: Successful save flow

- **WHEN** user clicks Save
- **THEN** the button transitions to "Saving…" with a spinner
- **AND** a POST request is sent to `http://localhost:7842/ingest`
- **AND** on 200 response, highlights and note are cleared from storage

#### Scenario: Already saved

- **WHEN** the bridge server returns 409
- **THEN** the popup displays "Already saved"

#### Scenario: Bridge server not running

- **WHEN** the POST fails with a network error or non-200/409 response
- **THEN** the popup displays "Bridge server not running"
