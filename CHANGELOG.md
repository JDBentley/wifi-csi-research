# Changelog

## Unreleased

### Added
- Initialized WiFi CSI research repository structure.
- Added folders for firmware, raw data, processed data, analysis, experiments, captures, logs, and docs.
- Added initial architecture and methodology documentation placeholders.
- Implemented initial CSI capture firmware for ESP32-C6
- Enabled WiFi CSI and verified callback execution
- Confirmed continuous CSI output via serial monitor
- Implemented structured CSI logging with timestamps and expanded CSI sample extraction
- Added directed traffic testing workflow using ESP32 IP targeting
- Generated first reproducible baseline and movement CSI datasets
- Established reproducible CSV capture methodology using tee

### Fixed
- Resolved ESP32-C6 CSI struct mismatch (updated to acquire config)
- Corrected WiFi configuration placement
- Ensured CSI initialization timing after WiFi connection
- Resolved ESP32-C6 CSI configuration API mismatch
- Corrected network/IP timing and interface initialization issues
- Identified hotspot/client isolation impacts on CSI acquisition

### Research Findings
- CSI sensing is strongly dependent on active packet flow
- Directed traffic significantly improves CSI callback stability
- Network topology and hotspot behavior directly affect sensing reliability

### Known Limitations
- Datasets still contain monitor/WiFi log noise
- No automated parsing or feature extraction yet
- CSI collection currently requires active traffic generation