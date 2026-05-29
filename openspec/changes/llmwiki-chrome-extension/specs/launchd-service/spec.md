## ADDED Requirements

### Requirement: launchd plist auto-starts bridge server at login

A macOS launchd plist file SHALL be provided that configures the bridge server to start automatically at user login and restart automatically if it crashes. The plist SHALL be loadable via `launchctl load`.

#### Scenario: Server starts at login

- **WHEN** the plist is loaded via `launchctl load ~/Library/LaunchAgents/com.llmwiki.bridge.plist`
- **THEN** the bridge server process starts and listens on `localhost:7842`

#### Scenario: Server restarts after crash

- **WHEN** the bridge server process exits unexpectedly
- **THEN** launchd restarts it automatically

---

### Requirement: Setup script installs the service

A setup script (`bridge/install.sh`) SHALL be provided that copies the plist to `~/Library/LaunchAgents/`, loads it via `launchctl`, and verifies the server is reachable on `localhost:7842`.

#### Scenario: Install script completes successfully

- **WHEN** user runs `bash bridge/install.sh`
- **THEN** the plist is copied to `~/Library/LaunchAgents/com.llmwiki.bridge.plist`
- **AND** the service is loaded
- **AND** a confirmation message is printed indicating the server is running
