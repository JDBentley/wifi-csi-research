# WiFi CSI Physical Reconnaissance Research

Real-world validation of WiFi Channel State Information (CSI) for physical security intelligence and motion detection.

**Core Finding:**
> CSI acquisition on ESP32-C6 is traffic-dependent, not purely passive. This challenges assumptions in published CSI research conducted under controlled lab conditions.

This research differentiates itself through real-world field testing outside lab environments, documenting environmental RF density effects, placement sensitivity, and the practical limitations of CSI-based sensing.

---

## What This Research Explores

- **RF-assisted environmental awareness** — detecting environmental changes through WiFi signal perturbation
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
| **1. Edge Processing** | ✅ COMPLETE | CSI acquisition, structured logging, reproducible capture workflow |
| **2. Temporal Analysis** | 🔄 IN PROGRESS | Energy extraction, environmental comparison, RF density analysis |
| **3. Intelligence** | ⏸️ NOT STARTED | Threshold classification, confidence scoring, false positive testing, WIDS logic |

See [`docs/architecture.md`](docs/architecture.md) for detailed layer descriptions.

---

## Project Structure

```
wifi-csi-research/
├── firmware/
│   ├── csi_capture.c              # ESP32-C6 CSI capture firmware
│   └── wifi_config.h.example      # Credential template (copy to wifi_config.h)
├── data/
│   └── raw/
│       ├── hotel/                 # Early baseline/movement datasets (16-subcarrier firmware)
│       ├── desk/                  # Controlled home environment (5 runs planned)
│       ├── kitchen/               # Alternate home environment (5 runs planned)
│       └── work_rf_dense/         # RF-dense office environment (5 runs planned)
├── analysis/
│   └── compare_baseline_movement.py   # Auto-discovery, per-env plots, cross-env comparison
├── results/
│   └── figures/                   # Generated plots and visualizations
├── docs/
│   ├── architecture.md            # Layer definitions and data flow
│   └── research-methodology.md    # Experimental standards and procedures
└── CHANGELOG.md                   # Research findings and code changes
```

---

## Quick Start

### Hardware Requirements

- ESP32-C6 development board
- USB cable for serial connection
- WiFi network (2.4 GHz for best compatibility)
- Laptop for traffic generation and serial capture

### Firmware Setup

1. **Configure WiFi credentials:**
   ```bash
   cd firmware
   cp wifi_config.h.example wifi_config.h
   # Edit wifi_config.h with your network SSID and password
   ```

2. **Flash ESP32-C6:**
   ```bash
   # Using ESP-IDF or Arduino — adjust for your toolchain
   idf.py flash monitor
   ```

3. **Verify CSI output:**
   Serial monitor should show:
   ```
   ESP IP: 192.168.x.x
   CSI,<timestamp>,<rssi>,<len>,<subcarrier_0>,...
   ```

### Data Capture

1. **Note ESP32 IP** from serial output

2. **Start traffic generation:**
   ```bash
   ping <ESP32_IP> -i 0.2   # 5 packets/sec
   ```

3. **Capture to CSV:**
   ```bash
   cat /dev/ttyUSB0 | tee data/raw/test/test_run_01.csv
   ```

4. **Run for desired duration** (10 minutes recommended), then stop both processes

### Analysis

```bash
# Install dependencies
pip install -r requirements.txt

# Analyze specific environment
python analysis/compare_baseline_movement.py --env desk

# Analyze all environments
python analysis/compare_baseline_movement.py

# Cross-environment comparison (requires 2+ placement environments with data)
# Automatically generated when multiple environments exist
```

**Output:**
- Per-environment plots: `results/figures/placement_runs_{env}.png`
- Cross-environment comparison: `results/figures/environment_comparison.png`
- Statistics printed to stdout

---

## Current Experiment: Placement and RF Density Comparison

**Goal:** Compare CSI signal behavior across three environments with different RF characteristics.

| Environment | Description | Hypothesis |
|---|---|---|
| `desk` | Controlled home location | Most stable baseline |
| `kitchen` | Alternate home location | Environmental drift from surfaces, appliances |
| `work_rf_dense` | RF-dense office | Higher variance due to device movement and RF interference |

**Plan:** 5 runs × 10 minutes × 3 environments = 15 total datasets

**Progress:** 0 / 15 datasets collected (hotel baseline/movement datasets captured under early firmware)

See [`docs/research-methodology.md`](docs/research-methodology.md) for full experimental design.

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

### Energy Separation (Layer 1)

Hotel dataset under 16-subcarrier firmware showed clear separation:
- Baseline: ~520–820 mean energy
- Movement: ~2000 mean energy

Current experiment uses full subcarrier capture for improved fidelity.

---

## Research Constraints

- **Passive capture only** in production and corporate environments
- **No offensive testing** on live networks without authorization
- **Adversarial RF stimulation** restricted to isolated home lab
- **Defensible claims only** — all findings must be reproducible from documented data

---

## Contributing

This is an individual research project developed for conference presentation and publication. Issues and feedback are welcome, especially from RF researchers or pentesters working with CSI.

If you reproduce this work or extend it, please cite this repository and document your environment, hardware, and any deviations from the methodology.

---

## References

- ESP32-C6 CSI documentation: [Espressif CSI Guide](https://docs.espressif.com/projects/esp-idf/en/latest/esp32c6/api-guides/wifi.html#wi-fi-channel-state-information)
- Research methodology adapted from reproducible research standards in RF and security communities

---

## License

Research findings and documentation are released under MIT.

Firmware is provided as-is for educational and research purposes.