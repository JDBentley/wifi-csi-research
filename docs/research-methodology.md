# Research Methodology

## Overview

This research follows a layered, evidence-based methodology. Every claim must be reproducible from documented data. Experiments are designed for incremental validation rather than speculative feature development.

**Core principle:**
> Define goal → identify layer → implement → test → capture evidence → analyze → document limitations → confirm completion

No layer advances until its evidence requirements are met.

---

## Experimental Standards

### Required Evidence Per Experiment

Every experiment must produce:

1. **[PHONE STILL]** — Physical environment capture (placement, conditions, setup)
2. **[SCREEN CAPTURE]** — Terminal output, analysis results, statistical summaries
3. **Metadata log** — date/time, location, firmware version, network, conditions, errors
4. **Raw data files** — CSVs preserved in `data/raw/{environment}/`
5. **Analysis output** — Plots saved to `results/figures/`, statistics logged
6. **Documented limitations** — What this data cannot support, what conditions invalidate it

### Success Criteria

An experiment is complete when:
- All planned datasets are collected
- Statistical comparison is defensible
- At least one limitation or anomaly is documented
- Results can be reproduced by someone else following the same capture workflow

**Incomplete data is acceptable if documented.** A run with an error or anomaly is still valuable if the limitation is recorded.

---

## Current Experiment: Placement and RF Density Comparison

**Research question:**
How does CSI signal energy and variance change across different physical environments and RF densities?

**Hypothesis:**
- Desk (controlled home): most stable baseline
- Kitchen (alternate home): environmental drift from surfaces, appliances, placement changes
- Work (RF-dense office): higher variance, less stable baselines due to RF density and device movement

**Dataset plan:**
- 3 environments × 5 runs × 10 minutes = 15 total datasets
- Same ESP32-C6 firmware version across all runs
- Same capture method: `tee` to CSV
- Same traffic method: directed ping to ESP32 IP
- All runs use full subcarrier capture (`data->len`)

**Metadata recorded per run:**
- Date/time
- Location (desk / kitchen / work_rf_dense)
- Firmware version / commit hash
- Distance to AP
- Distance to laptop
- Traffic method used
- People nearby (yes/no)
- Notable movement during capture
- Doors open/closed
- Appliances running
- WiFi network SSID
- Run duration
- Notes/errors

**Analysis approach:**
- Per-run energy calculation: sum of squared subcarrier values
- Per-environment statistics: mean, variance, std dev, min, max
- Cross-environment comparison: bar chart of mean ± std dev
- Visual inspection: per-environment time-series plots with all 5 runs overlaid

**What this supports:**
- Environmental RF drift claims
- Placement sensitivity
- RF density effects
- Repeatability challenges in real-world conditions
- Passive vs. assisted sensing model validation

---

## Traffic Dependency Testing

**Finding:**
CSI acquisition on ESP32-C6 is traffic-dependent, not purely passive. Callbacks fire reliably only when directed traffic (ping, TCP packets) targets the ESP32 IP. Ambient WiFi traffic from other devices does not consistently trigger callbacks.

**Validation method:**
1. ESP32 connected to WiFi, CSI enabled, no directed traffic → sparse or absent callbacks
2. Laptop pings ESP32 IP continuously → callbacks fire at packet rate
3. Ping stopped → callbacks drop or cease

**Implication:**
Most published CSI research assumes passive monitoring. This finding challenges that assumption and differentiates this work as real-world field testing rather than controlled lab capture.

**Documented limitation:**
This behavior may be ESP32-specific or firmware-configuration-dependent. Other hardware (Intel 5300, Atheros) may behave differently. Claims are scoped to ESP32-C6 under this firmware configuration.

---

## Data Collection Workflow

### Firmware Setup
1. Flash ESP32-C6 with `firmware/csi_capture.c`
2. Configure `wifi_config.h` with test network credentials
3. Verify serial output shows CSI data: `CSI,timestamp,rssi,len,subcarrier_0,...`

### Capture Procedure
1. Power ESP32, wait for WiFi connection and IP assignment
2. Note ESP32 IP from serial output
3. Start traffic generation: `ping <ESP32_IP> -i 0.2` (5 packets/sec)
4. Start capture: `cat /dev/ttyUSB0 | tee data/raw/{env}/{env}_run_XX.csv`
5. Run for 10 minutes
6. Stop capture (Ctrl+C), stop ping
7. Verify CSV file exists and contains CSI rows

### Post-Capture
1. Log metadata immediately while conditions are fresh
2. Take [PHONE STILL] of physical setup
3. Run analysis script to confirm data is valid: `python analysis/compare_baseline_movement.py --env {env}`
4. Review output for anomalies or errors
5. Document any deviations from expected behavior

---

## Analysis Standards

### Signal Energy Calculation

```
Energy = sum(CSI_subcarrier_i^2 for all i)
```

Columns 0-2 (timestamp, RSSI, len) are skipped. All remaining columns are subcarrier values.

### Statistical Comparison

Per-run metrics:
- Mean energy
- Variance
- Standard deviation
- Min / max energy

Cross-run metrics:
- Average std dev across runs (repeatability indicator)
- Mean separation between conditions (baseline vs. movement, or environment A vs. B)

### Thresholding (Layer 3)

Not yet implemented. Planned approach:
- Baseline std dev range defines "normal"
- Detection threshold = mean + k × std_dev (k determined empirically)
- Movement classified if sustained energy above threshold
- False positive rate measured against known-negative captures

---

## Defensive Research Posture

**No overclaiming:**
- Results are scoped to ESP32-C6 hardware
- Findings documented with limitations clearly stated
- Anomalies and errors are logged, not discarded
- CFP submissions and talks will not extrapolate beyond what the data supports

**Passive capture constraints:**
- No offensive testing on production networks
- Work environment captures are passive observation only
- No traffic injection, deauth, or RF interference at work

**Adversarial RF stimulation:**
- Restricted to isolated home lab only
- Future research direction, not current work
- Requires controlled environment with no unintended targets

**Reproducibility:**
- All datasets preserved in `data/raw/`
- Firmware version logged per capture
- Analysis scripts version-controlled
- Metadata recorded per run

### Cellular Exfiltration (Future Work)

Planned research direction: integrating SIM7600 LTE module for remote data exfiltration.

**Operational constraints:**
- Deployment restricted to authorized red team engagements only
- Testing conducted in isolated home lab
- Conference presentation focuses on defensive detection signatures
- No public release of operational drop box firmware