# Research Architecture

## Overview

This research is structured in three processing layers. Each layer has a defined scope, inputs, and outputs. Work progresses sequentially — a layer is not considered complete until its evidence requirements are met.

```
[Edge Processing] → [Temporal Analysis] → [Intelligence]
      ↓                     ↓                    ↓
  Raw CSI data        Variance / energy      Classification
  Timestamps          Environment comparison  Confidence scoring
  RSSI                RF density analysis     Detection logic
```

---

## Layer 1 — Edge Processing

**Status: COMPLETE**

**Scope:** Hardware configuration, CSI acquisition, structured logging, reproducible capture workflow.

**Inputs:**
- ESP32-C6 connected to WiFi network
- Directed traffic to ESP32 IP (ping or equivalent)
- Serial output captured via `tee` to CSV

**Outputs:**
- Raw CSI CSV files: `timestamp, RSSI, len, csi_0..csi_n`
- Structured per-run metadata logs

**Key finding at this layer:**
CSI acquisition is traffic-dependent. Callbacks fire reliably only when directed traffic targets the ESP32. Passive ambient capture produces inconsistent or absent callbacks. This challenges assumptions in published CSI research conducted under controlled lab conditions and is the primary research differentiator.

**Known limitations:**
- Early firmware (hotel datasets) capped capture at 16 subcarriers (`i < 16`).
  This was resolved prior to the placement experiment. All datasets from desk,
  kitchen, and work_rf_dense use full subcarrier capture (`data->len`).
  Hotel data is retained as documented v1 reference only.
- Raw CSV files contain firmware log noise requiring filtering at analysis layer
- Network topology and hotspot client isolation directly affect callback stability

---

## Layer 2 — Temporal Analysis

**Status: IN PROGRESS**

**Scope:** Signal energy extraction, environmental comparison, RF density analysis, repeatability testing.

**Inputs:**
- Raw CSI CSV files from Layer 1
- Per-run metadata (environment, placement, conditions)

**Outputs:**
- Per-run energy series
- Summary statistics: mean, variance, std dev, min, max
- Mean separation between capture conditions
- Movement/Baseline std dev ratio
- Environment comparison plots

**Experiment: Placement and RF Density Comparison**

Three environments × 5 runs × 10 minutes = 15 datasets.

| Environment | Description | Expected behavior |
|---|---|---|
| `desk` | Controlled home location | Most stable baseline |
| `kitchen` | Alternate home location | Environmental drift from surfaces, appliances |
| `work_rf_dense` | Office environment | Higher variance, RF density interference |

Each run produces a `*_run_*.csv` file. Analysis script auto-discovers files by environment folder and generates per-environment plots and a cross-environment comparison.

**Success criteria:**
- 5 usable datasets per environment
- Visible stability or drift trend across environments
- At least one documented limitation or anomaly per environment

---

## Layer 3 — Intelligence

**Status: NOT STARTED**

**Scope:** Threshold-based classification, confidence scoring, false positive testing, detection logic, WIDS applicability.

**Inputs:**
- Statistical summaries from Layer 2
- Thresholds derived from baseline variance analysis

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

---

## Data Flow

```
firmware/
└── csi_capture.c           → serial output → tee → data/raw/{env}/*.csv

data/raw/
└── {environment}/
    └── {capture_type}_{run}.csv

analysis/
└── compare_baseline_movement.py
    ├── discovers data/raw/ by environment
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