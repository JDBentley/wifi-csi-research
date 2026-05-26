# Research Architecture

## Overview

This research is structured in three processing layers. Each layer has a defined scope, inputs, and outputs. Work progresses sequentially — a layer is not considered complete until its evidence requirements are met. Completion is not permanent: the discovery of a methodology artifact at any layer may require iteration before the layer is considered closed for downstream work.

```
[Edge Processing] → [Temporal Analysis] → [Intelligence]
      ↓                     ↓                    ↓
  Raw CSI data        Variance / energy      Classification
  Timestamps          Environment comparison  Confidence scoring
  RX metadata         RF density analysis     Detection logic
  RSSI
```

---

## Layer 1 — Edge Processing

**Status: COMPLETE (v0.2.0 — iterated after firmware audit revealed methodology artifact)**

**Scope:** Hardware configuration, CSI acquisition, structured per-packet metadata logging, reproducible capture workflow.

**Inputs:**
- ESP32-C6 connected to WiFi network
- Directed traffic to ESP32 IP (ping or equivalent)
- Serial output captured via `tee` to CSV

**Outputs (v0.2.0 schema):**
- Raw CSI CSV files with per-packet header metadata:
  `ts_us, rssi, rate, noise_floor, channel, second, cur_bb_format, sig_len, rx_state, rxend_state, n_csi_bytes, <iq bytes...>`
- Structured per-run metadata logs (environment, firmware version, traffic method, people, doors, appliances)

**Key findings at this layer:**

1. **Traffic dependency.** CSI acquisition is traffic-dependent. Callbacks fire reliably only when directed traffic targets the ESP32. Passive ambient capture produces inconsistent or absent callbacks. This challenges assumptions in published CSI research conducted under controlled lab conditions.

2. **Acquisition methodology is part of the result.** The initial v0.1.x firmware enabled all CSI acquisition flags by default, a configuration commonly seen in published CSI research code and reference implementations. This produced a reproducible bimodal baseline amplitude distribution that looked like environmental signal but was actually a firmware artifact: CSI extracted from frames with different buffer schemas being averaged together. Constraining acquisition to a single PHY format and filtering by per-packet metadata collapsed the apparent bimodality and reduced baseline variance by 46% under identical environmental conditions. The acquisition methodology is part of the result, not implementation detail.

**Known limitations:**
- Early hotel firmware (v0.1.0) capped capture at 16 subcarriers (`i < 16`). Resolved before the placement experiment.
- All v0.1.x baseline captures (including the hotel datasets and the three preserved desk captures in `data/raw/desk_baseline_v01/`) contain the bimodality artifact. These are retained as the "before" half of the methodology comparison only — not used for cross-environment statistical claims.
- Raw CSV files contain firmware log noise (boot messages, WiFi driver output) requiring filtering at the analysis layer.
- Network topology and hotspot client isolation directly affect callback stability.
- v0.2.0 link reality: this network's C6 negotiates 802.11n (HT), not Wi-Fi 6 (HE). HE-only acquisition produces zero captures on this network.
- Findings are scoped to ESP32-C6 hardware under the documented firmware version. Generalization to other chips, SDKs, or network conditions requires independent validation.

---

## Layer 2 — Temporal Analysis

**Status: IN PROGRESS (v0.2.0 baseline validated; movement re-validation pending)**

**Scope:** Signal energy extraction, environmental comparison, RF density analysis, repeatability testing.

**Inputs:**
- Raw CSI CSV files from Layer 1 (v0.2.0 schema)
- Per-run metadata (environment, placement, conditions, firmware version)

**Required pre-analysis filtering (v0.2.0):**
- `rx_state == 0` (drop degraded receptions)
- `n_csi_bytes == 128` (drop packets with non-standard CSI buffer size)
- Document filter rate per capture; high filter rates indicate environmental or network issues worth flagging in metadata

**Outputs:**
- Per-run energy series (subject to filter rule above)
- Summary statistics: mean, variance, std dev, min, max
- Mean separation between capture conditions
- Movement/Baseline std dev ratio
- Environment comparison plots

**Experiment: Placement and RF Density Comparison**

Three environments × 5 runs × 10 minutes = 15 datasets (v0.2.0 firmware only).

| Environment | Description | Expected behavior |
|---|---|---|
| `desk_active` | Controlled home location | Most stable baseline (validated under v0.2.0) |
| `kitchen` | Alternate home location | Environmental drift from surfaces, appliances |
| `work_rf_dense` | Office environment | Higher variance, RF density interference |

Each run produces a `*_run_*.csv` file. Analysis script auto-discovers files by environment folder and generates per-environment plots and a cross-environment comparison.

**Success criteria:**
- 5 usable datasets per environment under v0.2.0 firmware
- Visible stability or drift trend across environments
- At least one documented limitation or anomaly per environment
- Movement vs baseline separation re-validated under v0.2.0 (the v0.1.x energy separation may have been partially driven by the bimodality artifact rather than real movement)

---

## Layer 3 — Intelligence

**Status: NOT STARTED**

**Scope:** Threshold-based classification, confidence scoring, false positive testing, detection logic, WIDS applicability.

**Inputs:**
- Statistical summaries from Layer 2
- Thresholds derived from baseline variance analysis (filtered v0.2.0 data only)

**Outputs:**
- Classification model (threshold-based, not ML)
- Confidence score per detection event
- False positive rate documentation
- Defensive detection recommendations

**Planned approach:**
- Define detection threshold from baseline std dev range
- Test threshold against movement captures
- Document false positive conditions (RF noise, appliance interference, environmental drift)
- Map detection logic to WIDS integration opportunities

**Dependencies:**
- Layer 2 movement validation must complete under v0.2.0 firmware before Layer 3 thresholds are computed against the wrong baseline distribution.

---

## Data Flow

```
firmware/
└── csi_capture.c           → serial output → tee → data/raw/{env}/*.csv

data/raw/
├── hotel/                  (v0.1.0 datasets, 16-subcarrier firmware)
├── desk_baseline_v01/      (v0.1.x desk runs, preserved as methodology evidence)
├── desk_active/            (v0.2.0 captures going forward)
├── kitchen/                (planned, v0.2.0 only)
└── work_rf_dense/          (planned, v0.2.0 only)

analysis/
└── compare_baseline_movement.py
    ├── discovers data/raw/ by environment
    ├── applies v0.2.0 filter rule (rx_state == 0 AND n_csi_bytes == 128)
    ├── auto-detects capture mode (baseline/movement or placement runs)
    └── writes results/figures/*.png

results/
├── figures/                → plots per environment + cross-environment comparison
└── summaries/              → statistical output logs (future)
```

---

## Design Constraints

- **Passive capture only** in production and corporate environments
- **No offensive testing** on live networks
- **Adversarial RF stimulation** restricted to isolated home lab
- **Defensible claims only** — all findings must be reproducible from documented data
- **No ML** at current stage — threshold-based classification preserves interpretability and auditability
- **Per-packet metadata logging required** — captures without `rx_state` and `n_csi_bytes` cannot be cleanly filtered and are not used for cross-environment statistical claims

## Future: Cellular Exfiltration Architecture

[Planned, not implemented]

Target architecture:
- ESP32-C6 + SIM7600 LTE module
- Local CSI buffering to SD card
- Periodic upload to remote server via HTTP/MQTT
- On-device classification reduces exfil bandwidth
- SMS alerts for high-confidence detection events

Dependencies:
- Layer 3 (Intelligence) threshold detection must be complete on v0.2.0-validated data
- Power budget analysis for battery operation
- SIM card cost modeling (data-only prepaid plan)

Constraints:
- Deployment restricted to authorized environments only
- Exfil testing in isolated home lab before field use
