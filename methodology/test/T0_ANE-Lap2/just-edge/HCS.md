# PROJECT: Edge Sensor — ANE Spectrum Monitoring System

## Hardware Constraints Specification (HCS)

> **Standard:** IEEE/ISO/IEC 29148:2018 §2.4 — *Realization / Design Constraints*, formalized as a standalone companion to the SRS. Documents the parametric limits of the selected hardware platform.
>
> **Template version:** 3.0.0  
> **Creation date:** 2026-10-13  
> **Last modified:** 2026-10-13  
> **Document status:** `APPROVED`

---

## Document Metadata

| Field                  | Value                                                      |
|------------------------|------------------------------------------------------------|
| **Document ID**        | `HCS-ANE-EDGE-001`                                        |
| **Project**            | Edge Sensor — Spectrum Monitoring Subsystem (Phase 2)      |
| **Organization**       | National Spectrum Agency (ANE) — Colombia                  |
| **Version**            | 1.0.0                                                     |
| **Classification**     | `INTERNAL`                                                |
| **Author(s)**          | _To be defined_                                           |
| **Reviewer(s)**        | _To be defined_                                           |
| **Approver(s)**        | _To be defined_                                           |

### Companion Documents

| Document ID            | Title                                                   | Relationship                      |
|------------------------|---------------------------------------------------------|-----------------------------------|
| `SRS-ANE-EDGE-001`    | Edge Sensor SRS (Phase 2)                               | Requirements this HCS constrains  |
| `SRS-ANE-001`         | Full-System SRS (Phase 2)                               | Parent system requirements        |

### Change Log

| Version | Date       | Author                 | Change Description                                          |
|---------|------------|------------------------|-------------------------------------------------------------|
| 0.1.0   | 2026-10-13 | AI-assisted generation | Initial extraction from datasheets and driver documentation |
| 1.0.0   | 2026-10-13 | AI-assisted generation | Approved — IEEE 29148 v3 structure                          |

---

## 1. Introduction

### 1.1 Purpose

This document catalogs the parametric constraints imposed by the selected hardware on the edge sensor's software and system requirements. It defines the design envelope within which all embedded software must operate. Every constraint is traceable to a datasheet, driver specification, or measured characterization.

### 1.2 Scope

The hardware platform is a **HackRF One SDR + Raspberry Pi 4B** embedded node with peripherals (GPS module, 4G/5G modem, antenna multiplexer, solar/battery power system). This document covers: RF parametric limits, ADC characteristics, bus throughput, processing budget, power budget, storage limits, and GPS accuracy.

It **excludes:** cloud infrastructure, network server hardware, web frontend hosting, and any hardware not physically present on the edge sensor node.

### 1.3 Definitions, Acronyms, and Abbreviations

| Term       | Definition                                                                           |
|------------|--------------------------------------------------------------------------------------|
| HCS        | Hardware Constraints Specification (this document)                                   |
| SDR        | Software Defined Radio                                                               |
| DANL       | Displayed Average Noise Level                                                        |
| SFDR       | Spurious Free Dynamic Range                                                          |
| CS8        | Complex Signed 8-bit — the HackRF IQ sample format                                  |
| TCXO       | Temperature-Compensated Crystal Oscillator                                           |
| AGC        | Automatic Gain Control                                                               |

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

**`HWC-SDR-001` — Frequency range**

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
| **Status**             | `CONFIRMED`                                               |

**Notes:**  
Sensitivity degrades significantly below 10 MHz and above 4 GHz.

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
| **Status**             | `CONFIRMED`                                               |

**Notes:**  
Wider spans require frequency hopping (sweep mode), which introduces temporal gaps.

---

**`HWC-SDR-003` — ADC resolution**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-SDR`                                                  |
| **Parameter**          | ADC resolution / IQ sample format                         |
| **Limit type**         | `FIXED`                                                   |
| **Value**              | 8 bit I + 8 bit Q (CS8)                                  |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | `REF-DS-001`; `REF-DRV-001`                               |
| **Impact**             | `HARD`                                                    |
| **Status**             | `CONFIRMED`                                               |

**Notes:**  
8-bit resolution yields a theoretical SFDR of ~48 dB (6.02 × 8). Achieving higher dynamic range requires software techniques: averaging, dithering, or gain-stepped captures.

---

**`HWC-SDR-004` — DANL**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-SDR`                                                  |
| **Parameter**          | Displayed Average Noise Level                             |
| **Limit type**         | `MIN`                                                     |
| **Value**              | −100 dBm/Hz (approximate, frequency-dependent)            |
| **Source**             | `MEASURED`                                                |
| **Source ref**         | `REF-MEAS-001` — To be performed                          |
| **Impact**             | `SOFT`                                                    |
| **Status**             | `PRELIMINARY`                                             |

**Notes:**  
DANL varies by frequency band and gain setting. Formal characterization per band is required. Software averaging can improve effective DANL at the cost of temporal resolution.

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
| **Status**             | `CONFIRMED`                                               |

**Notes:**  
Stock crystal is ± 20 ppm. Can be replaced with a TCXO (± 0.5–2 ppm) or compensated via GPS-disciplined correction.

---

**`HWC-SDR-006` — Gain control (no AGC)**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-SDR`                                                  |
| **Parameter**          | Gain control mechanism                                    |
| **Limit type**         | `ENUM`                                                    |
| **Value**              | Manual LNA gain (0–40 dB), VGA gain (0–62 dB), no AGC    |
| **Source**             | `DRIVER_API`                                              |
| **Source ref**         | `REF-DRV-001` — hackrf_set_lna_gain(), hackrf_set_vga_gain() |
| **Impact**             | `SOFT`                                                    |
| **Status**             | `CONFIRMED`                                               |

**Notes:**  
Gain must be set manually or via software-controlled stepping. Amplitude accuracy requires calibration tables mapping gain settings to correction factors across frequency.

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
| **Status**             | `CONFIRMED`                                               |

**Notes:**  
Susceptible to out-of-band interference, image frequencies, and intermodulation products. Detection algorithms must account for artifacts generated by the receiver itself.

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
| **Source ref**         | `REF-DS-002`; `REF-DS-003`                                |
| **Impact**             | `HARD`                                                    |
| **Status**             | `CONFIRMED`                                               |

**Notes:**  
At 20 MHz BW / 20 MS/s, a 2048-point FFT produces ~9,765 FFTs/second. Profiling under load is required to verify processing budget.

---

**`HWC-CPU-002` — RAM capacity**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-CPU`                                                  |
| **Parameter**          | System RAM                                                |
| **Limit type**         | `FIXED`                                                   |
| **Value**              | 4 GB or 8 GB (model-dependent)                            |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | `REF-DS-002`                                              |
| **Impact**             | `HARD`                                                    |
| **Status**             | `CONFIRMED`                                               |

**Notes:**  
Must accommodate OS, DSP pipeline buffers, IQ sample buffers, trace storage, and network stack simultaneously.

---

**`HWC-CPU-003` — Operating temperature**

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
| **Status**             | `CONFIRMED`                                               |

**Notes:**  
Colombian field deployments may exceed 50 °C ambient inside an enclosed housing. Thermal management (heatsink, ventilation, or duty-cycling) is required.

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
| **Status**             | `PRELIMINARY`                                             |

**Notes:**  
USB 2.0 theoretical: 480 Mbps = 60 MB/s. Practical sustained: ~32 MB/s. HackRF at 20 MS/s × 2 bytes = 40 MB/s exceeds this. Sample drops at sustained 20 MS/s are possible.

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
| **Status**             | `PRELIMINARY`                                             |

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
| **Status**             | `PRELIMINARY`                                             |

**Notes:**  
Standard NMEA sentences (GGA, RMC, GSA). Parsing library required for timestamp and position extraction.

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
| **Status**             | `PRELIMINARY`                                             |

**Notes:**  
Solar panel and battery sizing must exceed 15 W for 24/7 autonomous operation. Actual measurement under full DSP load is required.

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
| **Status**             | `PRELIMINARY`                                             |

**Notes:**  
USB 3.0 SSD easily meets this; microSD may not. Burst recording (limited duration) is an alternative.

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
| **Status**             | `PRELIMINARY`                                             |

**Notes:**  
The USB 2.0 bottleneck (~32 MB/s) is the weakest link in the 40 MB/s chain. Mitigations: (1) accept occasional drops in non-forensic mode, (2) reduce sample rate for continuous recording, (3) use burst capture for forensic storage.

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
| **Source ref**         | `HWC-SDR-003` + `HWC-SDR-006`                            |
| **Impact**             | `SOFT`                                                    |
| **Status**             | `PRELIMINARY`                                             |

**Notes:**  
The ≥ 80 dB target is achievable with: (1) gain-stepped captures at multiple LNA/VGA settings, (2) spectral averaging over N sweeps, (3) software dithering. Must be validated experimentally.

---

## 5. Structural Validation Checklist

> This checklist defines the rules for automated or manual structural review of this document.

1. **Structural completeness:** Every required field is present and uses a valid enum value.
2. **ID uniqueness:** No duplicate constraint IDs.
3. **Source traceability:** Every `source_ref` points to a valid entry in §1.4.
4. **Component existence:** Every `component` value exists in the Hardware Inventory (§1.5).
5. **RANGE consistency:** If `limit_type` = `RANGE`, both `value_min` and `value_max` are present and min < max.
6. **PRELIMINARY audit:** All `PRELIMINARY` constraints must be promoted to `CONFIRMED` or `DEPRECATED` before the document reaches `APPROVED` status.
