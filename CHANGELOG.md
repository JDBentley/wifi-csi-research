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

## [v0.2.0-csi-rxctrl] - 2026-05-26

Firmware version bump. Full per-packet metadata logging, constrained CSI acquisition, and the discovery of a methodology artifact that affected all v0.1.x baseline data.

### Added
- v0.2.0 firmware: full `rx_ctrl` per-packet metadata logging (11 fields: `ts, rssi, rate, noise_floor, channel, second, cur_bb_format, sig_len, rx_state, rxend_state, n_csi_bytes`)
- `FIRMWARE_VERSION` constant printed at boot for auditable capture provenance
- Filter rule for all v0.2.0 analysis: `rx_state == 0 AND n_csi_bytes == 128`
- `data/raw/desk_baseline_v01/` directory preserving the three v0.1.x desk runs as methodology-finding evidence
- Documented ESP-IDF v6.1 + C6 struct layout for future researchers (rxctrl uses v3-MAC layout; config struct uses smaller variant — the two are on different version branches in the same header)

### Changed
- CSI acquisition constrained from all 7 `acquire_csi_*` flags enabled to `acquire_csi_legacy + acquire_csi_ht20` only. Other flags disabled. This network's C6-to-router link negotiates 802.11n (HT), not Wi-Fi 6 (HE), so HT20 is required to capture data frames; legacy covers management traffic.
- v0.1.x desk runs relocated to `data/raw/desk_baseline_v01/` and preserved as comparison data (the "before" of the methodology finding). Not used for cross-environment statistical claims going forward.

### Fixed
- ESP32-C6 RX control struct field names corrected. v0.1.x firmware code referenced classic ESP32 fields (`sig_mode`, `mcs`, `cwb`, `ant`) that do not exist on the C6 `esp_wifi_rxctrl_t` struct. Discriminator field on this chip is `cur_bb_format`.

### Research Findings
- **Bimodal baseline amplitude in v0.1.x captures is a firmware artifact, not environmental signal.** Three v0.1.x desk runs showed reproducible bimodal amplitude distribution (high cluster ~45, low cluster ~24, 10–18% of packets in low cluster) with stable RSSI. Root cause: v0.1.x mixed CSI from frames producing different buffer sizes (128 vs 256 bytes). Naive `mean(amp where amp > 0)` averaging counted near-zero guard/null bins in the 256-byte schema as real subcarriers, dragging the mean down by half.
- **v0.2.0 with constrained acquisition produces unimodal baseline distribution** (mean 43.8, std 4.51) vs v0.1.x bimodal (mean 42.6, std 8.43). Std reduced by 46% from firmware change alone, same desk and traffic conditions.
- **C6 RX control struct has no `ant` field** because the chip has a single RF chain. Antenna diversity is not a viable bimodality hypothesis on this hardware.
- **C6 negotiates 802.11n (HT), not Wi-Fi 6 (HE), with typical home routers.** Verified from boot log: `phytype CBW20-SGI, phymode 11bgn, he:0, vht:0, ht:1`. Wi-Fi 6 capable hardware does not guarantee HE frame acquisition in practice.

### Known Limitations
- v0.1.x datasets cannot be perfectly re-filtered retroactively because the required per-packet metadata was never logged. They are preserved as the "before" half of the methodology comparison only.
- v0.2.0 movement validation has not yet been completed. The previously observed energy separation between baseline and movement (~520-820 vs ~2000 in hotel datasets) needs to be re-validated under the cleaner v0.2.0 baseline.
- Testing to date is on a single chip, a single router, and a single environment. Generalization to other hardware, network conditions, and environments requires further validation.

---

## [v0.1.0] - 2026-05-25

Initial firmware and analysis pipeline. Reproducible CSI capture established. Baseline and movement separation observed under early firmware. This release is preserved as the pre-methodology-audit reference; all baseline data captured under this firmware exhibits the bimodality artifact documented under v0.2.0.

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
- **All v0.1.x baseline captures exhibit the bimodal amplitude artifact documented under v0.2.0.** Affected captures are preserved as methodology-comparison evidence in `data/raw/desk_baseline_v01/`.
