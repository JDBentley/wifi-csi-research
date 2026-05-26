# Research Methodology

## Overview

This research follows a layered, evidence-based methodology. Every claim must be reproducible from documented data. Experiments are designed for incremental validation rather than speculative feature development.

**Core principle:**
> Define goal → identify layer → implement → test → capture evidence → analyze → document limitations → confirm completion

No layer advances until its evidence requirements are met. Completion of a layer is not permanent: discovery of a methodology artifact at any layer requires iteration before the layer is considered closed for downstream work.

---

## Experimental Standards

### Required Evidence Per Experiment

Every experiment must produce:

1. **[PHONE STILL]** — Physical environment capture (placement, conditions, setup)
2. **[SCREEN CAPTURE]** — Terminal output, analysis results, statistical summaries
3. **Metadata log** — date/time, location, **firmware version**, network, conditions, errors
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

## Firmware Methodology Discipline

### Lesson from v0.1.x → v0.2.0

The v0.1.x firmware produced reproducible baseline data that appeared internally consistent across runs. The baseline distribution was bimodal in a way that looked like environmental signal. It was not. Root cause was firmware-level: the acquisition configuration enabled all `acquire_csi_*` flags by default, mixing CSI extracted from frames with different buffer schemas, which the naive analysis averaged together as if they were the same measurement.

This finding has direct methodology implications for any CSI research:

1. **Audit acquisition flags before treating any baseline as defensible.** The default of "enable everything" is convenient but contaminates the data with frame-format mixing. Constrain acquisition to the frame formats actually expected on the target link.

2. **Log per-packet metadata or accept that some hypotheses cannot be tested.** Without `rx_state`, `n_csi_bytes`, and `cur_bb_format` logged per packet, researchers cannot distinguish degraded receptions, buffer-schema variation, or frame-format mixing from real environmental signal.

3. **Verify chip-specific struct details against headers, not memory.** The C6 `esp_wifi_rxctrl_t` struct differs from classic ESP32 layouts. Fields commonly referenced in generic CSI tutorials (`sig_mode`, `mcs`, `cwb`, `ant`) do not exist on this chip. The discriminator field is `cur_bb_format`. The config struct and rxctrl struct can be on different version branches in the same header — verify each independently.

4. **Repeatability across runs is not sufficient evidence of correctness.** The v0.1.x bimodality was reproducible across three runs precisely because the underlying error was structural, not random. Reproducibility validates that the measurement is *consistent*; it does not validate that the measurement is *correct*.

### Required Acquisition Configuration (v0.2.0)

Current production firmware uses:
```c
acquire_csi_legacy = true
acquire_csi_ht20 = true
// All other acquire_csi_* flags = false
```

This is appropriate for the current test network where the C6-to-router link negotiates 802.11n. Networks negotiating Wi-Fi 6 (HE) would require `acquire_csi_su = true` instead of or in addition to `acquire_csi_ht20`. Confirm link negotiation via boot log (`he:0` vs `he:1`) before assuming any specific configuration.

### Required Analysis Filter (v0.2.0)

Before computing any statistics over CSI data:
```text
rx_state == 0          # drop degraded receptions
AND
n_csi_bytes == 128     # drop packets with non-standard CSI buffer size
```

Filter rate should be reported per capture. High filter rates (>5%) indicate environmental or network issues worth flagging in metadata.

---

## Current Experiment: Placement and RF Density Comparison

**Research question:**
How does CSI signal energy and variance change across different physical environments and RF densities?

**Hypothesis:**
- Desk (controlled home): most stable baseline (validated under v0.2.0)
- Kitchen (alternate home): environmental drift from surfaces, appliances, placement changes
- Work (RF-dense office): higher variance, less stable baselines due to RF density and device movement

**Dataset plan:**
- 3 environments × 5 runs × 10 minutes = 15 total datasets
- All runs under v0.2.0 firmware (v0.1.x captures excluded from cross-environment claims)
- Same capture method: `tee` to CSV
- Same traffic method: directed ping to ESP32 IP, controlled rate (`ping -i 1 -s 64 -c 300` baseline)
- All runs use full subcarrier capture with per-packet metadata

**Metadata recorded per run:**
- Date/time
- Location (`desk_active` / `kitchen` / `work_rf_dense`)
- **Firmware version** (e.g., `v0.2.0-csi-rxctrl`) — required, used to confirm filter compatibility
- Distance to AP
- Distance to laptop
- Traffic method used (exact command)
- People nearby (count, approximate position, whether moving)
- Notable movement during capture (per 1-minute window if useful)
- Doors open/closed
- Appliances running
- WiFi network SSID
- Link mode (HT / HE) from boot log
- Run duration
- Notes/errors

**Analysis approach:**
- Apply filter rule (`rx_state == 0 AND n_csi_bytes == 128`) before any statistics
- Per-run energy calculation: sum of squared subcarrier values from the I/Q data
- Per-environment statistics: mean, variance, std dev, min, max
- Cross-environment comparison: bar chart of mean ± std dev
- Visual inspection: per-environment time-series plots with all 5 runs overlaid

**What this supports:**
- Environmental RF drift claims (under v0.2.0 firmware only)
- Placement sensitivity
- RF density effects
- Repeatability challenges in real-world conditions
- Passive vs. assisted sensing model validation

**What this does not support (without further work):**
- Generalization to other ESP32 variants, other chips, or non-ESP hardware
- Generalization to networks negotiating different link modes
- Movement detection claims (pending v0.2.0 movement re-validation)

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
This behavior may be ESP32-specific or firmware-configuration-dependent. Other hardware (Intel 5300, Atheros) may behave differently. Claims are scoped to ESP32-C6 under the documented firmware configuration.

---

## Data Collection Workflow

### Firmware Setup
1. Flash ESP32-C6 with `firmware/esp32-c6/csi_capture/main/csi_capture.c`
2. Configure `wifi_config.h` with test network credentials (file is gitignored)
3. Verify boot log shows firmware version line: `I (xxx) CSI_CAPTURE: CSI capture firmware 0.2.0-csi-rxctrl`
4. Verify CSI output format includes the 11 metadata fields before the I/Q bytes:
   `CSI,<ts>,<rssi>,<rate>,<noise_floor>,<channel>,<second>,<cur_bb_format>,<sig_len>,<rx_state>,<rxend_state>,<n_csi_bytes>,<iq_bytes...>`

### Capture Procedure
1. Power ESP32, wait for WiFi connection and IP assignment
2. Note ESP32 IP from serial output, and note link mode from boot log (`ht:` and `he:` values)
3. Start traffic generation: `ping <ESP32_IP> -i 1 -s 64 -c 300` (1 packet/sec, 5 minutes; adjust `-c` for longer captures)
4. Start capture: `cat /dev/ttyUSB0 | tee data/raw/{env}/{env}_run_XX.csv`
5. Run for planned duration (5 or 10 minutes typical)
6. Stop capture (Ctrl+C), stop ping
7. Verify CSV file exists and contains CSI rows with the v0.2.0 schema

### Post-Capture
1. Log metadata immediately while conditions are fresh — especially firmware version, link mode, people positions
2. Take [PHONE STILL] of physical setup
3. Run analysis script to confirm data is valid: `python analysis/compare_baseline_movement.py --env {env}`
4. Review output for anomalies, errors, and filter rate (high filter rate is a flag)
5. Document any deviations from expected behavior

---

## Analysis Standards

### Pre-Analysis Filtering (Required)

```
rx_state == 0          # drop degraded receptions
AND
n_csi_bytes == 128     # drop packets with non-standard CSI buffer size
```

Report filter rate per capture. Document anomalies.

### Signal Energy Calculation

```
Energy = sum(I^2 + Q^2 for all subcarriers in the packet)
```

Operates on I/Q pairs from the CSI buffer (bytes 12 onward in the v0.2.0 schema). Metadata columns (ts, rssi, rate, noise_floor, channel, second, cur_bb_format, sig_len, rx_state, rxend_state, n_csi_bytes) are skipped.

### Statistical Comparison

Per-run metrics:
- Mean energy
- Variance
- Standard deviation
- Min / max energy
- Filter rate (percentage of packets dropped)

Cross-run metrics:
- Average std dev across runs (repeatability indicator)
- Mean separation between conditions (baseline vs. movement, or environment A vs. B)

### Thresholding (Layer 3)

Not yet implemented. Planned approach:
- Baseline std dev range defines "normal" (computed from filtered v0.2.0 baseline data only)
- Detection threshold = mean + k × std_dev (k determined empirically)
- Movement classified if sustained energy above threshold
- False positive rate measured against known-negative captures

---

## Defensive Research Posture

**No overclaiming:**
- Results are scoped to ESP32-C6 hardware under the documented firmware version
- Findings documented with limitations clearly stated
- Anomalies and errors are logged, not discarded
- CFP submissions and talks will not extrapolate beyond what the data supports
- Methodology critiques are scoped to "configurations commonly seen in published CSI research code and reference implementations" — not universal claims about the field

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
- Firmware version logged per capture and in repository tags
- Analysis scripts version-controlled
- Filter rules documented and applied uniformly
- Metadata recorded per run

### Cellular Exfiltration (Future Work)

Planned research direction: integrating SIM7600 LTE module for remote data exfiltration.

**Operational constraints:**
- Deployment restricted to authorized red team engagements only
- Testing conducted in isolated home lab
- Conference presentation focuses on defensive detection signatures
- No public release of operational drop box firmware
