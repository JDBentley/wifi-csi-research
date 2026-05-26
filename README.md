# WiFi CSI Physical Reconnaissance Research

Real-world validation of WiFi Channel State Information (CSI) for physical security intelligence and motion detection.

**Core Findings:**

> 1. **CSI acquisition on ESP32-C6 is traffic-dependent**, not purely passive. This challenges assumptions in published CSI research conducted under controlled lab conditions.
>
> 2. **A firmware configuration commonly seen in published CSI research code produces a bimodal baseline amplitude distribution** that looks like environmental signal but is actually a frame-format mixing artifact. Constraining acquisition and filtering by per-packet metadata reduces baseline variance by 46% under identical environmental conditions.

This research differentiates itself through real-world field testing outside lab environments, documenting environmental RF density effects, placement sensitivity, methodology artifacts, and the practical limitations of CSI-based sensing.

---

## What This Research Explores

- **RF-assisted environmental awareness** — detecting environmental changes through WiFi signal perturbation
- **Methodology validity** — auditing what published CSI research code actually measures vs what it assumes
- **Temporal signal intelligence** — comparing signal behavior across time and environments
- **Offensive methodology awareness** — understanding CSI as a passive reconnaissance vector
- **Defensive/WIDS detection opportunities** — identifying CSI-based reconnaissance and developing detection signatures
- **Physical pentesting intelligence applications** — leveraging CSI data for site reconnaissance and ingress planning

**Future directions:**
- Lightweight edge processing for real-time classification
- SIM card exfiltration to remote analysis laptop
- Adversarial RF stimulation (controlled lab only)

---

## Research Architecture

Three layers, sequential completion required:

| Layer | Status | Scope |
|---|---|---|
| **1. Edge Processing** | ✅ COMPLETE (v0.2.0) | CSI acquisition, structured logging with per-packet metadata, reproducible capture workflow |
| **2. Temporal Analysis** | 🔄 IN PROGRESS | Energy extraction, environmental comparison, RF density analysis |
| **3. Intelligence** | ⏸️ NOT STARTED | Threshold classification, confidence scoring, false positive testing, WIDS logic |

See [`docs/architecture.md`](docs/architecture.md) for detailed layer descriptions, including the v0.1.x → v0.2.0 firmware iteration that resulted from the methodology artifact discovery.

---

## Project Structure

```
wifi-csi-research/
├── firmware/
│   └── esp32-c6/csi_capture/
│       ├── main/
│       │   ├── csi_capture.c          # ESP32-C6 CSI capture firmware (v0.2.0)
│       │   └── wifi_config.h.example  # Credential template (copy to wifi_config.h, gitignored)
│       └── ...
├── data/
│   └── raw/
│       ├── hotel/                     # Early baseline/movement datasets (v0.1.0, 16-subcarrier)
│       ├── desk_baseline_v01/         # v0.1.x desk runs — preserved as methodology-finding evidence
│       ├── desk_active/               # v0.2.0 captures (current placement experiment, desk)
│       ├── kitchen/                   # Planned: v0.2.0 only
│       └── work_rf_dense/             # Planned: v0.2.0 only
├── analysis/
│   └── compare_baseline_movement.py   # Auto-discovery, per-env plots, cross-env comparison
├── results/
│   └── figures/                       # Generated plots and visualizations
├── docs/
│   ├── architecture.md                # Layer definitions and data flow
│   └── research-methodology.md        # Experimental standards and procedures
└── CHANGELOG.md                       # Research findings and code changes (versioned releases)
```

---

## Quick Start

### Hardware Requirements

- ESP32-C6 development board
- USB cable for serial connection
- WiFi network (2.4 GHz; 802.11n recommended for current firmware configuration)
- Laptop for traffic generation and serial capture

### Firmware Setup

1. **Configure WiFi credentials:**
   ```bash
   cd firmware/esp32-c6/csi_capture/main
   cp wifi_config.h.example wifi_config.h
   # Edit wifi_config.h with your network SSID and password (gitignored, will not be committed)
   ```

2. **Flash ESP32-C6 with ESP-IDF v6.1+:**
   ```bash
   cd firmware/esp32-c6/csi_capture
   idf.py build
   idf.py -p /dev/ttyUSB0 flash monitor
   ```

3. **Verify firmware version on boot:**
   Serial monitor should show:
   ```
   I (xxx) CSI_CAPTURE: CSI capture firmware 0.2.0-csi-rxctrl
   ESP IP: 192.168.x.x
   ```

4. **Verify CSI output schema:**
   Each CSI line has 11 metadata fields before the I/Q bytes:
   ```
   CSI,<ts>,<rssi>,<rate>,<noise_floor>,<channel>,<second>,<cur_bb_format>,<sig_len>,<rx_state>,<rxend_state>,<n_csi_bytes>,<iq_bytes...>
   ```

5. **Verify link negotiation (important):**
   Boot log shows the link mode. On a typical 2.4 GHz home router, expect:
   ```
   wifi:ifidx:0, rssi:-XX, nf:-XX, phytype(0x3, CBW20-SGI), phymode(0x3, 11bgn), max_rate:144, he:0, vht:0, ht:1
   ```
   If `he:1` (Wi-Fi 6 negotiation), the current acquisition config will produce zero captures — update the firmware to enable `acquire_csi_su = true`.

### Data Capture

1. **Note ESP32 IP** from serial output

2. **Start traffic generation** (1 packet/sec, 5 minutes; adjust `-c` for longer captures):
   ```bash
   ping <ESP32_IP> -i 1 -s 64 -c 300
   ```

3. **Capture to CSV:**
   ```bash
   idf.py monitor | tee data/raw/{env}/{env}_run_XX_esp32.csv
   ```

4. **Record metadata immediately** — firmware version, link mode, people present, doors, appliances, traffic command

5. Stop both processes when capture is complete

### Analysis

```bash
# Install dependencies
pip install -r requirements.txt

# Analyze specific environment (applies v0.2.0 filter rule automatically)
python analysis/compare_baseline_movement.py --env desk_active

# Analyze all environments
python analysis/compare_baseline_movement.py

# Cross-environment comparison (requires 2+ placement environments with data)
# Automatically generated when multiple environments exist
```

**Required filter (v0.2.0):**
```
rx_state == 0 AND n_csi_bytes == 128
```
Applied before any statistics. Filter rate reported per capture.

**Output:**
- Per-environment plots: `results/figures/placement_runs_{env}.png`
- Cross-environment comparison: `results/figures/environment_comparison.png`
- Statistics printed to stdout (mean, variance, std dev, filter rate)

---

## Current Experiment: Placement and RF Density Comparison

**Goal:** Compare CSI signal behavior across three environments with different RF characteristics, using v0.2.0 firmware only.

| Environment | Description | Hypothesis |
|---|---|---|
| `desk_active` | Controlled home location | Most stable baseline (validated under v0.2.0) |
| `kitchen` | Alternate home location | Environmental drift from surfaces, appliances |
| `work_rf_dense` | RF-dense office | Higher variance due to device movement and RF interference |

**Plan:** 5 runs × 10 minutes × 3 environments = 15 total datasets

**Progress (v0.2.0 firmware):**
- `desk_active`: 1 of 5 baseline captures complete (`desk_run_04_esp32.csv`); 1 movement capture pending
- `kitchen`: 0 of 5
- `work_rf_dense`: 0 of 5

**Preserved comparison data (not part of the 15-dataset plan):**
- `data/raw/desk_baseline_v01/` — three v0.1.x desk runs retained as the "before" half of the methodology-finding comparison
- `data/raw/hotel/` — v0.1.0 hotel datasets

See [`docs/research-methodology.md`](docs/research-methodology.md) for full experimental design and the firmware methodology discipline section.

---

## Key Research Findings

### Traffic Dependency (Layer 1)

CSI callbacks on ESP32-C6 require directed traffic to the device IP. Passive monitoring of ambient WiFi traffic does not consistently trigger callbacks.

**Validation:**
- No directed traffic → sparse or absent callbacks
- Continuous ping to ESP32 IP → callbacks at packet rate
- Traffic stopped → callbacks drop or cease

**Implication:** Most published CSI research assumes passive monitoring works. This finding challenges that assumption and positions this work as real-world field validation.

**Documented limitation:** Behavior may be ESP32-specific or firmware-dependent. Other hardware (Intel 5300, Atheros) may behave differently.

### Methodology Artifact: Bimodal Baseline (Layer 1, v0.1.x → v0.2.0)

A firmware configuration commonly seen in published CSI research code — enabling all `acquire_csi_*` flags by default — produces a reproducible bimodal baseline amplitude distribution that looks like environmental signal but is actually a frame-format mixing artifact.

**Validation:**
- Three v0.1.x desk runs showed reproducible bimodal distribution (clusters at ~45 and ~24, 10–18% of packets in low cluster) with stable RSSI
- v0.2.0 with constrained acquisition (`acquire_csi_legacy + acquire_csi_ht20`) and per-packet metadata filtering produces unimodal distribution under identical environmental conditions
- Baseline standard deviation reduced by 46% from firmware change alone

**Implication:** Acquisition methodology is part of the result, not implementation detail. CSI research that does not publish firmware versions, acquisition flags, and filter rules cannot be meaningfully reproduced. Detection systems calibrated against unfiltered baselines may be measuring firmware behavior rather than the environment.

**Documented limitation:** Finding validated on one chip, one network, one environment. Generalization requires further validation.

### Energy Separation (Layer 1, v0.1.0)

Hotel dataset under 16-subcarrier firmware showed clear separation:
- Baseline: ~520–820 mean energy
- Movement: ~2000 mean energy

This separation was captured under v0.1.0 firmware and is **pending re-validation under v0.2.0** to confirm that the observed separation reflects actual movement rather than partial contribution from the bimodality artifact.

---

## Research Constraints

- **Passive capture only** in production and corporate environments
- **No offensive testing** on live networks without authorization
- **Adversarial RF stimulation** restricted to isolated home lab
- **Defensible claims only** — all findings must be reproducible from documented data
- **Per-packet metadata logging required** — captures without `rx_state` and `n_csi_bytes` cannot be cleanly filtered

---

## Contributing

This is an individual research project developed for conference presentation and publication. Issues and feedback are welcome, especially from RF researchers or pentesters working with CSI.

If you reproduce this work or extend it, please cite this repository and document your environment, hardware, firmware version, acquisition flags, and any deviations from the methodology.

---

## References

- ESP32-C6 CSI documentation: [Espressif CSI Guide](https://docs.espressif.com/projects/esp-idf/en/latest/esp32c6/api-guides/wifi.html#wi-fi-channel-state-information)
- ESP-IDF v6.1 `esp_wifi_he_types.h` — source of truth for the C6 `esp_wifi_rxctrl_t` struct and `wifi_csi_acquire_config_t` layout
- Research methodology adapted from reproducible research standards in RF and security communities

---

## License

Research findings and documentation are released under MIT.

Firmware is provided as-is for educational and research purposes.
