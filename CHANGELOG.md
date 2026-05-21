# Changelog

All notable changes to this research project are documented in this file.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) (adapted for research work).

Sections used:
- **Added** — new code, firmware, data, or documentation
- **Changed** — modifications to existing components
- **Fixed** — bug fixes and resolved issues
- **Research Findings** — confirmed findings from experiments
- **Known Limitations** — documented constraints affecting interpretation

---

## Unreleased

### Added
- Repository structure: firmware, data, analysis, experiments, captures, logs, docs
- Initial CSI capture firmware for ESP32-C6
- Structured CSI logging with timestamps, RSSI, and subcarrier values
- Directed traffic testing workflow using ESP32 IP targeting
- Reproducible CSV capture methodology using `tee`
- First reproducible baseline and movement CSI datasets (hotel environment)
- `analysis/compare_baseline_movement.py` — auto-discovery, per-environment plots, cross-environment comparison
- Placement experiment plan: desk, kitchen, work_rf_dense (5 runs each)
- `firmware/wifi_config.h.example` template for credential management

### Changed
- Removed 16-subcarrier cap in `csi_callback` — now captures full `data->len` subcarrier values
- Moved WiFi credentials out of `csi_capture.c` into gitignored `wifi_config.h`
- Reorganized repo layout: data moved to `data/raw/{environment}/`, analysis script relocated to `analysis/`, figures output to `results/figures/`

### Fixed
- ESP32-C6 CSI struct mismatch (updated to acquire config)
- WiFi configuration placement
- CSI initialization timing after WiFi connection
- ESP32-C6 CSI configuration API mismatch
- Network/IP timing and interface initialization issues
- Hotspot client isolation impacts on CSI acquisition

### Research Findings
- **CSI acquisition is traffic-dependent, not purely passive.** Callbacks fire reliably only when directed traffic targets the ESP32. This challenges assumptions in published CSI research conducted under controlled lab conditions.
- Directed traffic significantly improves CSI callback stability
- Network topology and hotspot behavior directly affect sensing reliability
- Clear energy separation observed between baseline (~520-820) and movement (~2000) in initial hotel dataset under 16-subcarrier firmware

### Known Limitations
- Hotel datasets (`baseline_01.csv`, `movement_01.csv`) were captured under early firmware capped at 16 subcarriers. Retained as documented v1 reference only — not used for cross-environment statistical claims.
- Raw CSV files contain firmware log noise; filtering handled at analysis layer
- CSI collection requires active traffic generation (research finding, not a defect)
- No automated feature extraction beyond signal energy at current stage
- Threshold-based classification only — no ML at current stage by design (interpretability and auditability)