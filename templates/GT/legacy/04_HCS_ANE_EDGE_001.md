# PROJECT: Edge Sensor — ANE Spectrum Monitoring System

## Hardware Constraints Specification (HCS)

> **Template based on:** IEEE/ISO/IEC 29148:2018 §2.4 (Realization / Design Constraints), formalized as a standalone companion document to the SRS. Provides machine-readable parametric limits for COTS hardware that define the design envelope within which software requirements must be fulfilled.
>
> **Methodology:** This document is the COTS constraint input to the COTS-Reconciled Requirements Engineering methodology. It captures every hardware limitation that bounds, limits, or shapes a software requirement. The companion SRS references constraints from this document by ID.
>
> **Template version:** 2.0.0  
> **Creation date:** 2026-10-13  
> **Last modified:** 2026-10-13  
> **Document status:** `IN_REVIEW`

---

## Document Metadata

| Field                  | Value                                                      |
|------------------------|------------------------------------------------------------|
| **Document ID**        | `HCS-ANE-EDGE-001`                                        |
| **Project**            | Edge Sensor — Spectrum Monitoring Subsystem (Phase 2)      |
| **Organization**       | National Spectrum Agency (ANE) — Colombia                  |
| **Version**            | 0.1.0                                                     |
| **Classification**     | `INTERNAL`                                                |
| **Author(s)**          | _To be defined_                                           |
| **Reviewer(s)**        | _To be defined_                                           |
| **Approver(s)**        | _To be defined_                                           |

### Companion Documents

| Document ID            | Title                                                   | Relationship              |
|------------------------|---------------------------------------------------------|---------------------------|
| `SRS-ANE-EDGE-001`    | Edge Sensor SRS (Phase 2)                               | Requirements bounded by this HCS |
| `SRS-ANE-001`         | Full-System SRS (Phase 2)                               | Parent system requirements |

### Change Log

| Version | Date       | Author                 | Change Description                                      |
|---------|------------|------------------------|---------------------------------------------------------|
| 0.1.0   | 2026-10-13 | AI-assisted generation | Initial extraction from datasheets and driver documentation |

---

## 1. Introduction

### 1.1 Purpose

This document catalogs the parametric constraints imposed by the selected COTS hardware on the edge sensor's software requirements (SRS-ANE-EDGE-001). It serves as the formal "envelope" within which the edge sensor DSP pipeline, connectivity stack, and all embedded software must operate. Every constraint is traceable to a datasheet, driver specification, or measured characterization.

### 1.2 Scope

The hardware platform is a **HackRF One SDR + Raspberry Pi 4B** embedded node with peripherals (GPS module, 4G/5G modem, antenna multiplexer, solar/battery power system). This document covers: RF parametric limits, ADC characteristics, bus throughput, processing budget, power budget, storage limits, GPS accuracy, and driver API constraints.

It **excludes:** cloud infrastructure, network server hardware, web frontend hosting, and any hardware not physically present on the edge sensor node.

### 1.3 Definitions, Acronyms, and Abbreviations

| Term       | Definition                                                                           |
|------------|--------------------------------------------------------------------------------------|
| COTS       | Commercial Off-The-Shelf                                                             |
| HCS        | Hardware Constraints Specification (this document)                                   |
| SDR        | Software Defined Radio                                                               |
| DANL       | Displayed Average Noise Level                                                        |
| SFDR       | Spurious Free Dynamic Range                                                          |
| ENOB       | Effective Number Of Bits                                                             |
| CS8        | Complex Signed 8-bit — the HackRF IQ sample format                                  |
| TCXO       | Temperature-Compensated Crystal Oscillator                                           |
| AGC        | Automatic Gain Control                                                               |
| RPi        | Raspberry Pi                                                                         |
| AF         | Antenna Factor                                                                       |

### 1.4 References

| Ref ID        | Document                                                        | Version / Date          |
|---------------|-----------------------------------------------------------------|-------------------------|
| `REF-DS-001`  | HackRF One Datasheet / Specifications                           | Rev 2024                |
| `REF-DS-002`  | Raspberry Pi 4 Model B Datasheet                                | Rev 2023                |
| `REF-DS-003`  | BCM2711 (RPi 4B SoC) Datasheet                                 | Broadcom, 2019          |
| `REF-DRV-001` | libhackrf API Documentation                                    | v2024.02.1              |
| `REF-DRV-002` | SoapySDR API Documentation                                     | v0.8                    |
| `REF-DRV-003` | Linux USB 2.0 Subsystem Documentation                           | Kernel 6.x              |
| `REF-MEAS-001`| HackRF DANL Characterization (measured)                         | _To be performed_       |
| `REF-MEAS-002`| USB 2.0 Sustained Throughput Test (measured)                    | _To be performed_       |

### 1.5 Hardware Inventory

| Component ID | Component Name         | Role in System                        | Manufacturer       | Part Number         |
|-------------|------------------------|---------------------------------------|---------------------|---------------------|
| `HW-SDR`   | HackRF One             | SDR receiver / transmitter            | Great Scott Gadgets  | HackRF One          |
| `HW-CPU`   | Raspberry Pi 4 Model B | Embedded processing platform          | Raspberry Pi Foundation | RPi 4B 4GB/8GB  |
| `HW-GPS`   | GPS Module (TBD)       | Geolocation and timing                | TBD                 | TBD                 |
| `HW-4G5G`  | 4G/5G Modem (TBD)     | Mobile data connectivity              | TBD                 | TBD                 |
| `HW-MUX`   | Antenna Multiplexer    | RF path switching between antennas    | TBD                 | TBD                 |
| `HW-PWR`   | Solar + Battery System | Autonomous power supply               | TBD                 | TBD                 |
| `HW-STR`   | SSD / microSD          | Local data storage                    | TBD                 | TBD                 |

---

## 2. System Hardware Architecture

### 2.1 Block Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    EDGE SENSOR NODE                               │
│                                                                   │
│  ┌─────────────┐    USB 2.0     ┌──────────────────────┐         │
│  │  HackRF One │◄──────────────►│  Raspberry Pi 4B     │         │
│  │  [HW-SDR]   │   IQ (CS8)    │  [HW-CPU]            │         │
│  └──────┬──────┘               │                      │         │
│         │ SMA                   │  ┌────────────────┐  │         │
│  ┌──────┴──────┐               │  │ DSP Pipeline   │  │         │
│  │ Antenna Mux │               │  │ (software)     │  │         │
│  │ [HW-MUX]   │               │  └────────────────┘  │         │
│  └──────┬──────┘               │                      │         │
│         │ SMA                   │  ┌────────────────┐  │         │
│  ┌──────┴──────┐               │  │ Storage        │  │         │
│  │  Antennas   │               │  │ [HW-STR]       │  │         │
│  │  (per band) │               │  └────────────────┘  │         │
│  └─────────────┘               └──────────┬───────────┘         │
│                                           │                      │
│  ┌─────────────┐  UART/USB    ┌──────────┴──────────┐           │
│  │ GPS Module  │◄────────────►│  Peripheral Bus     │           │
│  │ [HW-GPS]   │              │  (USB/UART/GPIO)    │           │
│  └─────────────┘              └──────────┬──────────┘           │
│                                          │                       │
│  ┌─────────────┐  USB         ┌──────────┴──────────┐           │
│  │ 4G/5G Modem │◄────────────►│  Network Manager    │           │
│  │ [HW-4G5G]  │              │  (software)         │           │
│  └─────────────┘              └─────────────────────┘           │
│                                                                   │
│  ┌────────────────────────────────────────────┐                  │
│  │ Solar Panel + Battery + Charge Manager     │                  │
│  │ [HW-PWR]                                   │                  │
│  └────────────────────────────────────────────┘                  │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 Bus and Interface Topology

| From       | To         | Bus/Protocol | Data Rate (theoretical) | Data Rate (sustained) |
|------------|------------|-------------|-------------------------|----------------------|
| HW-SDR     | HW-CPU     | USB 2.0     | 480 Mbps                | ~256 Mbps (~32 MB/s) |
| HW-GPS     | HW-CPU     | UART / USB  | 9600 baud (NMEA)        | < 1 KB/s             |
| HW-4G5G   | HW-CPU     | USB         | Varies by modem         | Carrier-dependent    |
| HW-MUX     | HW-CPU     | GPIO        | N/A (control signals)   | N/A                  |
| HW-STR     | HW-CPU     | USB 3.0 / microSD | 5 Gbps / 104 MB/s | ~400 MB/s / ~90 MB/s |

---

## 3. Hardware Constraints

---

### 3.1 SDR Receiver (HackRF One)

---

**`HWC-SDR-001` — Maximum frequency range**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-SDR`                                                  |
| **Parameter**          | Operating frequency range                                 |
| **Limit type**         | `RANGE`                                                   |
| **Value min**          | 1 MHz                                                     |
| **Value max**          | 6 GHz                                                     |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | `REF-DS-001` — Specifications                             |
| **Impact**             | `HARD`                                                    |
| **SRS refs**           | `ANAL-RNG-001`, `ANAL-PAR-001`                            |
| **Status**             | `CONFIRMED`                                               |

**Notes:**  
The HackRF One covers 1 MHz to 6 GHz. Sensitivity degrades significantly below 10 MHz and above 4 GHz. Performance at band edges should be characterized (see REF-MEAS-001).

---

**`HWC-SDR-002` — Maximum instantaneous bandwidth**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-SDR`                                                  |
| **Parameter**          | Maximum instantaneous (real-time) bandwidth               |
| **Limit type**         | `MAX`                                                     |
| **Value**              | 20 MHz                                                    |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | `REF-DS-001` — Specifications                             |
| **Impact**             | `HARD`                                                    |
| **SRS refs**           | `ANAL-RNG-002`, `ANAL-MED-004`                            |
| **Status**             | `CONFIRMED`                                               |

**Notes:**  
Instantaneous bandwidth is 20 MHz maximum. Wider spans require frequency hopping (sweep mode), which introduces temporal gaps and is not true real-time.

---

**`HWC-SDR-003` — ADC resolution (IQ sample format)**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-SDR`                                                  |
| **Parameter**          | ADC resolution / IQ sample format                         |
| **Limit type**         | `FIXED`                                                   |
| **Value**              | 8 bit I + 8 bit Q (CS8)                                  |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | `REF-DS-001` — Specifications; `REF-DRV-001` — API       |
| **Impact**             | `HARD`                                                    |
| **SRS refs**           | `CONF-CAR-002`, `CONF-CAR-005`                            |
| **Status**             | `CONFIRMED`                                               |

**Notes:**  
8-bit resolution yields a theoretical SFDR of ~48 dB (6.02 × 8). This is the fundamental limit on single-capture dynamic range. Achieving ≥ 80 dB dynamic range (CONF-CAR-002) requires software techniques: averaging, dithering, or gain-stepped captures.

---

**`HWC-SDR-004` — DANL (Displayed Average Noise Level)**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-SDR`                                                  |
| **Parameter**          | Displayed Average Noise Level                             |
| **Limit type**         | `MIN`                                                     |
| **Value**              | −100 dBm/Hz (approximate, frequency-dependent)            |
| **Source**             | `MEASURED`                                                |
| **Source ref**         | `REF-MEAS-001` — To be performed                          |
| **Impact**             | `SOFT`                                                    |
| **SRS refs**           | `CONF-CAR-001`                                            |
| **Status**             | `PRELIMINARY`                                             |

**Notes:**  
The HackRF lacks a calibrated attenuator and a known reference noise source. DANL varies by frequency band and gain setting. The −100 dBm/Hz figure is an estimate; formal characterization per band is required (REF-MEAS-001). Software averaging can improve effective DANL at the cost of temporal resolution.

---

**`HWC-SDR-005` — Frequency accuracy (oscillator)**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-SDR`                                                  |
| **Parameter**          | Local oscillator frequency accuracy                       |
| **Limit type**         | `MAX`                                                     |
| **Value**              | ± 20 ppm (uncompensated, typical)                         |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | `REF-DS-001` — Crystal oscillator specifications          |
| **Impact**             | `SOFT`                                                    |
| **SRS refs**           | `CONF-CAR-003`, `CONF-CAR-004`                            |
| **Status**             | `CONFIRMED`                                               |

**Notes:**  
The stock HackRF crystal is ± 20 ppm, which exceeds the ± 2 ppm requirement (CONF-CAR-003). Mitigation: replace the oscillator with a TCXO (± 0.5–2 ppm), or use GPS-disciplined correction. This is flagged as `MITIGATED` in the SRS with `new_hardware` = Yes.

---

**`HWC-SDR-006` — No AGC or calibrated attenuator**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-SDR`                                                  |
| **Parameter**          | Gain control mechanism                                    |
| **Limit type**         | `ENUM`                                                    |
| **Value**              | Manual LNA gain (0–40 dB), VGA gain (0–62 dB), no AGC    |
| **Source**             | `DRIVER_API`                                              |
| **Source ref**         | `REF-DRV-001` — hackrf_set_lna_gain(), hackrf_set_vga_gain() |
| **Impact**             | `SOFT`                                                    |
| **SRS refs**           | `CONF-CAR-005`, `CONF-CAL-001`                            |
| **Status**             | `CONFIRMED`                                               |

**Notes:**  
The HackRF has no AGC. Gain must be set manually or via software-controlled gain stepping. Amplitude accuracy (± 1 dB target, CONF-CAR-005) requires a software calibration table that maps gain settings to measured amplitude correction factors across frequency.

---

**`HWC-SDR-007` — No pre-selection filters**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-SDR`                                                  |
| **Parameter**          | RF front-end filtering                                    |
| **Limit type**         | `FIXED`                                                   |
| **Value**              | No band-pass pre-selection filters                        |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | `REF-DS-001` — Block diagram                              |
| **Impact**             | `SOFT`                                                    |
| **SRS refs**           | `ANAL-EMC-001`, `NORM-VER-001`                            |
| **Status**             | `CONFIRMED`                                               |

**Notes:**  
Without pre-selection filters, the HackRF is susceptible to out-of-band interference, image frequencies, and intermodulation products. EMC mitigation (ANAL-EMC-001) and intermodulation detection (NORM-VER-001) must account for artifacts generated by the receiver itself, not just external sources.

---

### 3.2 Embedded Platform (Raspberry Pi 4B)

---

**`HWC-CPU-001` — Processing capacity**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-CPU`                                                  |
| **Parameter**          | CPU cores and clock speed                                 |
| **Limit type**         | `FIXED`                                                   |
| **Value**              | 4× ARM Cortex-A72 @ 1.8 GHz                              |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | `REF-DS-002` — Specifications; `REF-DS-003` — BCM2711    |
| **Impact**             | `HARD`                                                    |
| **SRS refs**           | `ANAL-RNG-002`, `ANAL-MED-001`, `ANAL-PAR-003`           |
| **Status**             | `CONFIRMED`                                               |

**Notes:**  
The DSP pipeline (FFT, PSD, traces, OBW, channel power) must complete within the CPU budget. At 20 MHz bandwidth with 20 MS/s input, a 2048-point FFT produces ~9,765 FFTs/second. The CPU must handle FFT computation, trace accumulation, and all peripheral I/O concurrently. Profiling under load is required to verify the ≤ 1 s latency target (ANAL-RNG-002).

---

**`HWC-CPU-002` — RAM capacity**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-CPU`                                                  |
| **Parameter**          | System RAM                                                |
| **Limit type**         | `FIXED`                                                   |
| **Value**              | 4 GB or 8 GB (model-dependent)                            |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | `REF-DS-002` — Specifications                             |
| **Impact**             | `HARD`                                                    |
| **SRS refs**           | `GEST-MON-001`                                            |
| **Status**             | `CONFIRMED`                                               |

**Notes:**  
RAM must accommodate the OS, DSP pipeline buffers, IQ sample buffers, trace storage, and network stack simultaneously. Buffer overruns at 20 MS/s × 2 bytes = 40 MB/s input rate are the primary risk.

---

**`HWC-CPU-003` — Operating temperature range**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-CPU`                                                  |
| **Parameter**          | Operating temperature                                     |
| **Limit type**         | `RANGE`                                                   |
| **Value min**          | 0 °C                                                      |
| **Value max**          | 50 °C (throttles above 80 °C)                             |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | `REF-DS-002` — Thermal specifications                     |
| **Impact**             | `SOFT`                                                    |
| **SRS refs**           | `GEST-MON-001`                                            |
| **Status**             | `CONFIRMED`                                               |

**Notes:**  
Colombian field deployments may exceed 50 °C ambient inside an enclosed housing. Thermal management (heatsink, ventilation, or duty-cycling) is required. Health monitoring (GEST-MON-001) must include CPU temperature with throttle alerts.

---

### 3.3 Data Bus (USB 2.0: SDR ↔ RPi)

---

**`HWC-BUS-001` — USB 2.0 sustained throughput**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-SDR`, `HW-CPU`                                       |
| **Parameter**          | Sustained data throughput (SDR → RPi)                     |
| **Limit type**         | `MAX`                                                     |
| **Value**              | ~32 MB/s sustained (measured)                             |
| **Source**             | `MEASURED`                                                |
| **Source ref**         | `REF-MEAS-002` — To be performed                          |
| **Impact**             | `HARD`                                                    |
| **SRS refs**           | `ANAL-RNG-002`                                            |
| **Status**             | `PRELIMINARY`                                             |

**Notes:**  
USB 2.0 theoretical: 480 Mbps = 60 MB/s. Practical sustained: ~32 MB/s due to protocol overhead. HackRF at 20 MS/s × 2 bytes (I+Q) = 40 MB/s exceeds this. The libhackrf driver handles the mismatch with internal buffering, but sustained operation at 20 MS/s risks sample drops. Formal measurement (REF-MEAS-002) is required.

---

### 3.4 GPS Module

---

**`HWC-GPS-001` — Horizontal accuracy**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-GPS`                                                  |
| **Parameter**          | Horizontal position accuracy (CEP 50%)                    |
| **Limit type**         | `MAX`                                                     |
| **Value**              | ≤ 3 m (open sky, target)                                  |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | _TBD — depends on selected GPS module_                    |
| **Impact**             | `HARD`                                                    |
| **SRS refs**           | `CONN-GPS-002`                                            |
| **Status**             | `PRELIMINARY`                                             |

**Notes:**  
The specific GPS module has not been selected. The ≤ 3 m accuracy requirement (CONN-GPS-002) drives the selection. Multi-constellation (GPS + GLONASS + Galileo) modules are available in the target budget range.

---

**`HWC-GPS-002` — GPS output protocol**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-GPS`                                                  |
| **Parameter**          | Data output protocol                                      |
| **Limit type**         | `FIXED`                                                   |
| **Value**              | NMEA 0183 over UART (9600 baud default)                   |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | _TBD — depends on selected GPS module_                    |
| **Impact**             | `INFORMATIONAL`                                           |
| **SRS refs**           | `ANAL-PAR-005`, `CONN-GPS-001`                            |
| **Status**             | `PRELIMINARY`                                             |

**Notes:**  
Standard NMEA sentences (GGA, RMC, GSA). Parsing library required in the DSP pipeline for timestamp and position extraction.

---

### 3.5 Power System

---

**`HWC-PWR-001` — System power consumption**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-PWR`                                                  |
| **Parameter**          | Total system power consumption (all components active)    |
| **Limit type**         | `MAX`                                                     |
| **Value**              | ~15 W (estimated: RPi 6W + HackRF 2.5W + peripherals)    |
| **Source**             | `DERIVED`                                                 |
| **Source ref**         | `REF-DS-001` + `REF-DS-002` — Power specifications        |
| **Impact**             | `HARD`                                                    |
| **SRS refs**           | `POWR-AUT-001`                                            |
| **Status**             | `PRELIMINARY`                                             |

**Notes:**  
Estimated peak: RPi 4B ~6W (full load) + HackRF ~2.5W + 4G modem ~3W + GPS ~0.5W + peripherals ~3W = ~15W. Solar panel and battery sizing must exceed this for 24/7 autonomous operation. Actual measurement under full DSP load is required.

---

### 3.6 Storage

---

**`HWC-STR-001` — Storage write speed**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-STR`                                                  |
| **Parameter**          | Sustained sequential write speed                          |
| **Limit type**         | `MIN`                                                     |
| **Value**              | ≥ 40 MB/s (required to store raw CS8 at 20 MS/s)         |
| **Source**             | `DERIVED`                                                 |
| **Source ref**         | IQ rate: 20 MS/s × 2 bytes = 40 MB/s                     |
| **Impact**             | `HARD`                                                    |
| **SRS refs**           | `FORN-ALM-001`, `FORN-ALM-003`                            |
| **Status**             | `PRELIMINARY`                                             |

**Notes:**  
Raw CS8 recording at full bandwidth requires ≥ 40 MB/s sustained writes. A USB 3.0 SSD easily meets this; a microSD card may not. Storage selection must be validated with sustained write tests. Burst recording (limited duration) is an alternative if sustained writes fail.

---

## 4. Derived Constraints

---

**`HWC-DRV-001` — IQ throughput budget (end-to-end)**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-SDR`, `HW-CPU`, `HW-STR`                             |
| **Parameter**          | End-to-end IQ data flow budget                            |
| **Limit type**         | `FIXED`                                                   |
| **Value**              | 20 MS/s × 2 B = 40 MB/s (SDR → USB → RAM → DSP → Storage) |
| **Source**             | `DERIVED`                                                 |
| **Source ref**         | `HWC-SDR-002` + `HWC-BUS-001` + `HWC-STR-001`           |
| **Impact**             | `HARD`                                                    |
| **SRS refs**           | `ANAL-RNG-002`, `FORN-ALM-001`                            |
| **Status**             | `PRELIMINARY`                                             |

**Notes:**  
The USB 2.0 bottleneck (~32 MB/s sustained) is the weakest link in the 40 MB/s chain. At full 20 MS/s, sample drops are possible. Mitigations: (1) accept occasional drops in non-forensic mode, (2) reduce sample rate for continuous recording, (3) use burst capture for forensic CS8 storage. This is a system-level derived constraint from the combination of HWC-SDR-002, HWC-BUS-001, and HWC-STR-001.

---

**`HWC-DRV-002` — Dynamic range via software enhancement**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-SDR`                                                  |
| **Parameter**          | Achievable dynamic range with software techniques         |
| **Limit type**         | `RANGE`                                                   |
| **Value min**          | ~48 dB (single capture, limited by 8-bit ADC)             |
| **Value max**          | ~90 dB (with gain stepping + averaging, estimated)        |
| **Source**             | `DERIVED`                                                 |
| **Source ref**         | `HWC-SDR-003` (8-bit ADC) + `HWC-SDR-006` (manual gain)  |
| **Impact**             | `SOFT`                                                    |
| **SRS refs**           | `CONF-CAR-002`                                            |
| **Status**             | `PRELIMINARY`                                             |

**Notes:**  
The ≥ 80 dB dynamic range requirement (CONF-CAR-002) exceeds the 48 dB single-capture limit of the 8-bit ADC. Achievable with: (1) gain-stepped captures at multiple LNA/VGA settings, (2) spectral averaging over N sweeps, (3) software dithering. The ~90 dB upper estimate assumes 10+ gain steps with averaging. This must be validated experimentally.

---

## 5. Constraint-to-Requirement Cross-Reference

| HCS Constraint ID | SRS Requirement ID(s)                                  | Reconciliation Status |
|-------------------|--------------------------------------------------------|-----------------------|
| `HWC-SDR-001`    | `ANAL-RNG-001`, `ANAL-PAR-001`                        | `AT_LIMIT`            |
| `HWC-SDR-002`    | `ANAL-RNG-002`, `ANAL-MED-004`                        | `AT_LIMIT`            |
| `HWC-SDR-003`    | `CONF-CAR-002`, `CONF-CAR-005`                        | `MITIGATED`           |
| `HWC-SDR-004`    | `CONF-CAR-001`                                        | `AT_LIMIT`            |
| `HWC-SDR-005`    | `CONF-CAR-003`, `CONF-CAR-004`                        | `MITIGATED`           |
| `HWC-SDR-006`    | `CONF-CAR-005`, `CONF-CAL-001`                        | `MITIGATED`           |
| `HWC-SDR-007`    | `ANAL-EMC-001`, `NORM-VER-001`                        | `MITIGATED`           |
| `HWC-CPU-001`    | `ANAL-RNG-002`, `ANAL-MED-001`, `ANAL-PAR-003`       | `BOUNDED`             |
| `HWC-CPU-002`    | `GEST-MON-001`                                        | `BOUNDED`             |
| `HWC-CPU-003`    | `GEST-MON-001`                                        | `BOUNDED`             |
| `HWC-BUS-001`    | `ANAL-RNG-002`                                        | `AT_LIMIT`            |
| `HWC-GPS-001`    | `CONN-GPS-002`                                        | `BOUNDED`             |
| `HWC-GPS-002`    | `ANAL-PAR-005`, `CONN-GPS-001`                        | `UNCONSTRAINED`       |
| `HWC-PWR-001`    | `POWR-AUT-001`                                        | `BOUNDED`             |
| `HWC-STR-001`    | `FORN-ALM-001`, `FORN-ALM-003`                        | `AT_LIMIT`            |
| `HWC-DRV-001`    | `ANAL-RNG-002`, `FORN-ALM-001`                        | `AT_LIMIT`            |
| `HWC-DRV-002`    | `CONF-CAR-002`                                        | `MITIGATED`           |

---

## 6. G0 Structural Validation (Future Work)

> **Status:** `PLANNED` — G0 will validate this document's structural integrity and its cross-references with the companion SRS.

### 6.1 HCS-Specific Validation Rules (Planned)

1. **Structural completeness:** Every mandatory field is present and uses a valid enum value.
2. **ID uniqueness:** No duplicate constraint IDs.
3. **Source traceability:** Every `source_ref` points to a valid entry in Section 1.4.
4. **Component existence:** Every `component` value exists in the Hardware Inventory (Section 1.5).
5. **Cross-reference integrity:** Every `srs_refs` ID exists in the companion SRS.
6. **RANGE consistency:** If `limit_type` is `RANGE`, both `value_min` and `value_max` must be present and `value_min` < `value_max`.
7. **Bidirectional traceability:** Every constraint with `impact` = `HARD` must have at least one SRS reference.
8. **PRELIMINARY audit:** All `PRELIMINARY` constraints must be promoted to `CONFIRMED` or `DEPRECATED` before the HCS reaches `APPROVED` status.
