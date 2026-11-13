### 1.4 Black boxes: modules

#### SUB-001/acq

| Field            | Value |
|------------------|-------|
| subsystem_id       | `SUB-001` |
| Functional layer | HAL |
| Responsibility   | Schedule and execute the three-step scan, configure the receiver, capture 39 frames per step, count overflows and dropped frames, flag saturation and publish IQ blocks with capture metadata. |
| depends_on       | `HW-IQ-001`, `SW-HACKRF-001`, `time_status.v1`, `config_status.v1` |
| provides         | `INT-IQ-001` (IQ block plus capture counters) |
| hw_dependency    | true |
| required_vl      | VL-2 |

**Rationale for the required VL:** The correctness of this module depends on the real HackRF: 10 Msps sustained over USB 2.0, the fixed gain steps, the 8 MHz usable bandwidth, saturation at full scale, and the overflow/dropped-frame behaviour. A Mock HAL proves the scheduling and counters, but only HIL at VL-2 proves that the real receiver sustains the scan without loss.

#### SUB-001/estimator

| Field            | Value |
|------------------|-------|
| subsystem_id       | `SUB-001` |
| Functional layer | DSP |
| Responsibility   | Convert each IQ block into 199 channel powers in dBFS and an 819-point spectrum using a 4 096-point Hann FFT, 50 % overlap, 2 495 segments and DC-spike replacement. |
| depends_on       | `INT-IQ-001`, `INT-CTRL-001` (frequency correction and reference state) |
| provides         | `INT-PWR-001` |
| hw_dependency    | false |
| required_vl      | VL-1 |

**Rationale for the required VL:** The algorithm is deterministic: the same IQ block must produce the same channel powers and spectrum. Golden vectors at VL-1 prove the FFT, window, DC replacement, 105-bin integration and 3.4648 kHz mapping bound. The real-hardware timing (2.5 s per scan) is a PATH-001 VL-2 measurement, not an algorithm property.

#### SUB-001/calibration

| Field            | Value |
|------------------|-------|
| subsystem_id       | `SUB-001` |
| Functional layer | DSP |
| Responsibility   | Apply K(f) and the frequency correction to the estimator output, attach uncertainty and its basis, enforce the calibration validity state and the configuration SHA-256 check, and withhold power when the correction cannot be demonstrated. |
| depends_on       | `INT-PWR-001`, `INT-CTRL-001`, the active `calibration_record` file, `time_status.v1`, `config_status.v1` |
| provides         | `INT-CAL-001`, `INT-CTRL-001` |
| hw_dependency    | false |
| required_vl      | VL-1 |

**Rationale for the required VL:** Interpolation, validity transitions, uncertainty arithmetic and the configuration comparison are file and state logic, fully testable with deterministic records. The real amplitude accuracy is established by `calibrate` and `verify` at VL-2.

#### SUB-001/detector

| Field            | Value |
|------------------|-------|
| subsystem_id       | `SUB-001` |
| Functional layer | Decision |
| Responsibility   | Classify each channel as Occupied, Free or Uncertain from the calibrated excess over the verified noise floor, applying hysteresis, the adjacent-channel ratio and all Free-release conditions. |
| depends_on       | `INT-CAL-001`, `config_status.v1` (declared minimum power) |
| provides         | `INT-OCC-001` |
| hw_dependency    | false |
| required_vl      | VL-1 |

**Rationale for the required VL:** The decision is a fixed table of thresholds and rules. Synthetic golden scans at SNR 0 dB, vacant channels and adjacent leakage prove the state machine, the hysteresis and every Uncertain reason at VL-1. Real-signal detection and false-alarm probabilities are acceptance measurements on PATH-001 at VL-2.

#### SUB-001/comparator

| Field            | Value |
|------------------|-------|
| subsystem_id       | `SUB-001` |
| Functional layer | Decision |
| Responsibility   | Compare each channel's occupancy with the site station reference and emit one of four results, leaving all channels indeterminate when the reference is absent or invalid. |
| depends_on       | `INT-OCC-001`, `config_status.v1` (station reference) |
| provides         | `INT-ASG-001` |
| hw_dependency    | false |
| required_vl      | VL-1 |

**Rationale for the required VL:** The result is a six-row decision table over two enums. Deterministic vectors cover every row, including the absent/invalid reference and the “Uncertain never becomes a verdict” rule.

#### SUB-001/duty_cycle

| Field            | Value |
|------------------|-------|
| subsystem_id       | `SUB-001` |
| Functional layer | DSP |
| Responsibility   | Accumulate Occupied/Free/Uncertain counts per UTC-aligned interval and publish the duty cycle and uncertain fraction when the interval closes. |
| depends_on       | `INT-OCC-001` |
| provides         | `SSC-DUTY-001` (`duty_cycle.v1`) |
| hw_dependency    | false |
| required_vl      | VL-1 |

**Rationale for the required VL:** Counting and the UTC interval boundary are deterministic. Replay scans across two interval boundaries prove the counts and the null-denominator rule.

#### SUB-001/records

| Field            | Value |
|------------------|-------|
| subsystem_id       | `SUB-001` |
| Functional layer | Output |
| Responsibility   | Assemble the per-scan header, 199 channel records and health record with power, uncertainty, occupancy inputs, comparison, limit comparison, flags and the evidence label. |
| depends_on       | `INT-CAL-001`, `INT-OCC-001`, `INT-ASG-001`, `time_status.v1`, `config_status.v1` |
| provides         | `SSC-SCAN-001` (`scan_records.v1`) |
| hw_dependency    | false |
| required_vl      | VL-1 |

**Rationale for the required VL:** The module is a schema assembler. Golden expected records prove every field, the `not_configured` rule, the withheld-power reason, the Free-release evidence and the prohibited-word check at VL-1.

#### SUB-001/calibrate

| Field            | Value |
|------------------|-------|
| subsystem_id       | `SUB-001` |
| Functional layer | DSP |
| Responsibility   | Run the operator's `establish_amplitude_calibration` procedure, measure K(f), the dynamic range and the crystal correction, and write one immutable calibration record. |
| depends_on       | `HW-IQ-001`, `SW-HACKRF-001`, `INT-PWR-001` |
| provides         | `calibration_record` file (persistent) and the new active correction |
| hw_dependency    | true |
| required_vl      | VL-2 |

**Rationale for the required VL:** The procedure depends on the real receiver response, the real cable loss and the traceable source HW-010. The Mock HAL can exercise the procedure's data flow, but the resulting K(f) only has meaning against real hardware and a real reference.

#### SUB-001/verify

| Field            | Value |
|------------------|-------|
| subsystem_id       | `SUB-001` |
| Functional layer | DSP |
| Responsibility   | Run the operator's `verify_amplitude_correction` procedure at 12 points, compare the median differences with the 1.0 dB tolerance and the ±20 ppm frequency limit, and write one immutable validation record. |
| depends_on       | `HW-IQ-001`, `SW-HACKRF-001`, `INT-PWR-001`, `calibration_record` |
| provides         | `validation_record` file (persistent) and the updated `verified_until` |
| hw_dependency    | true |
| required_vl      | VL-2 |

**Rationale for the required VL:** The verification is only meaningful with the independent reference HW-011 and the real receiver; it is the evidence that keeps the calibration valid. Deterministic replay cannot establish independence of the traceability chain.

#### SUB-002/history

| Field            | Value |
|------------------|-------|
| subsystem_id       | `SUB-002` |
| Functional layer | Output |
| Responsibility   | Keep 744 h of 60 s bins per channel and the latest scan in memory, answer bounded queries and expose the 60 min noise-floor medians and the 24 h duty cycle. |
| depends_on       | `SSC-SCAN-001`, `SSC-DUTY-001`, `time_status.v1` |
| provides         | `SSC-HIST-001` (`history.v1`), `latest_scan` |
| hw_dependency    | false |
| required_vl      | VL-1 |

**Rationale for the required VL:** The ring buffer, bin aliasing, query caps (2 000 bins per channel, 40 000 total) and the “insufficient history” answer are deterministic data structures. The 512 MB memory ceiling is checked by the resource envelope.

#### SUB-002/alerts

| Field            | Value |
|------------------|-------|
| subsystem_id       | `SUB-002` |
| Functional layer | Decision |
| Responsibility   | Evaluate the five alert rules over scan records and history, maintain their persistence counters and credit, and publish active alerts, recent events and rule states. |
| depends_on       | `SSC-SCAN-001`, `SSC-HIST-001` (internal query), `time_status.v1`, `supervisor_status.v1` |
| provides         | `SSC-ALERT-001` (`alerts.v1`) |
| hw_dependency    | false |
| required_vl      | VL-1 |

**Rationale for the required VL:** The rules are explicit counters and thresholds over record values. Replay scenarios (silent channel, unexpected occupancy, missing health, expiring calibration, 6 dB drift) prove each rule, its clearing rule and the `not_configured`/`insufficient_history` states at VL-1.

#### SUB-003/writer

| Field            | Value |
|------------------|-------|
| subsystem_id       | `SUB-003` |
| Functional layer | Output |
| Responsibility   | Write the screening report as results are produced, with atomic headers, fsynced scan lines, 3 600 s segments, 60 s progress, space checks and interrupted-run recovery. |
| depends_on       | `SSC-SCAN-001`, `SSC-DUTY-001`, `time_status.v1`, `config_status.v1`, `SSC-REPORT-001` |
| provides         | `SSC-CAT-001` (`report_catalog.v1`) |
| hw_dependency    | false |
| required_vl      | VL-1 |

**Rationale for the required VL:** Run/segment lifecycle, atomic rename, fsync ordering, rotation and recovery are filesystem logic testable in a temporary directory. The real card's sustained write (≤0.05 s per scan) and endurance are PATH-001 VL-2 measurements.

#### SUB-004/http

| Field            | Value |
|------------------|-------|
| subsystem_id       | `SUB-004` |
| Functional layer | Output |
| Responsibility   | Serve HTTP GET/HEAD on port 8080 with the four views and report downloads, enforce the request/download limits and attach the evidence headers. |
| depends_on       | `INT-QRY-001` (view responses), `SSC-HIST-001`, `SSC-ALERT-001`, `SSC-STATUS-001`, `SSC-CAT-001` |
| provides         | `SW-NET-001` (HTTP endpoint) |
| hw_dependency    | false |
| required_vl      | VL-1 |

**Rationale for the required VL:** HTTP semantics, status codes, `Retry-After`, the 8/64/30 s limits and the read-only rule are testable with a local server and fake data. The real Ethernet throughput and 8-client load are PATH-002/PATH-009 VL-2 measurements.

#### SUB-004/views

| Field            | Value |
|------------------|-------|
| subsystem_id       | `SUB-004` |
| Functional layer | Output |
| Responsibility   | Shape the four views and API payloads from released values only, applying the null-plus-reason rule, UTC formatting and the evidence label. |
| depends_on       | `SSC-HIST-001`, `SSC-ALERT-001`, `SSC-STATUS-001`, `SSC-CAT-001` |
| provides         | `INT-QRY-001` |
| hw_dependency    | false |
| required_vl      | VL-1 |

**Rationale for the required VL:** The release rule, the fixed color scale, the “never 0 or last value” rule and the alert-bar states are deterministic payload transformations. Golden JSON vectors prove each view at VL-1.

#### SUB-005/ntp

| Field            | Value |
|------------------|-------|
| subsystem_id       | `SUB-005` |
| Functional layer | Decision |
| Responsibility   | Synchronize the node clock from the configured NTP sources and publish a 1 s UTC status with resolution, offset and sync state. |
| depends_on       | `config_status.v1` (time sources) |
| provides         | `SSC-TIME-001` (`time_status.v1`) |
| hw_dependency    | false |
| required_vl      | VL-1 |

**Rationale for the required VL:** The NTP client state machine, the 50 ms/3 600 s unsynced rule, the 120 s startup wait and the leap detection are testable against a fake NTP peer. The site network is not a COTS device and does not raise the level.

#### SUB-006/config

| Field            | Value |
|------------------|-------|
| subsystem_id       | `SUB-006` |
| Functional layer | Decision |
| Responsibility   | Load, validate and atomically accept or reject `site-config.json` and the station reference, compute their SHA-256 and publish `config_status.v1`. |
| depends_on       | `site-config.json`, `station_reference_file` (files) |
| provides         | `SSC-CFG-001` (`config_status.v1`) |
| hw_dependency    | false |
| required_vl      | VL-1 |

**Rationale for the required VL:** Field ranges, the whole-file accept/reject rule, the “keep the last valid configuration” rule and the station table are file logic with deterministic vectors. No hardware property is involved.

#### SUB-006/processes

| Field            | Value |
|------------------|-------|
| subsystem_id       | `SUB-006` |
| Functional layer | Decision |
| Responsibility   | Start, watch, restart and stop the five units, maintain the restart ladder and publish the node state and progress view. |
| depends_on       | `SSC-PROG-001` (`progress.v1`) |
| provides         | `SSC-STATUS-001` (`supervisor_status.v1`), `SSC-REPORT-001` (`report_command.v1`), `SSC-SHUT-001` (`shutdown.v1`) |
| hw_dependency    | false |
| required_vl      | VL-1 |

**Rationale for the required VL:** The progress counter, 10 s stuck rule, 5/10/20/40/60 s ladder, loop detection and ordered shutdown are process-control logic testable with fake children on any Linux host.

#### SUB-006/watchdog

| Field            | Value |
|------------------|-------|
| subsystem_id       | `SUB-006` |
| Functional layer | HAL |
| Responsibility   | Feed the hardware watchdog every 5 s only when the supervision loop ran, read the SoC temperature every 10 s, apply the unit resource limits and raise or clear the thermal condition. |
| depends_on       | `HW-TEMP-001`, `SW-WDOG-001` |
| provides         | Thermal condition and resource limits to `processes` |
| hw_dependency    | true |
| required_vl      | VL-2 |

**Rationale for the required VL:** `/dev/watchdog`, the Pi thermal zone and cgroups only exist on the target. The Mock device API proves the feed/hold logic, but the real reset and thermal behaviour are HIL properties.

#### SUB-006/metrics

| Field            | Value |
|------------------|-------|
| subsystem_id       | `SUB-006` |
| Functional layer | Decision |
| Responsibility   | Compute availability over a 30-day report and supervisor log and run the 72 h field-validation analysis, without adding runtime functions. |
| depends_on       | report files and supervisor event log (read-only) |
| provides         | `availability` and `field_validation` analysis records (operator output) |
| hw_dependency    | false |
| required_vl      | VL-1 |

**Rationale for the required VL:** Both procedures are file analyses with explicit counting rules (R-48/R-49 and `run_field_validation`). Deterministic report/log fixtures prove the counts and the acceptance result at VL-1.

### 1.5 Supplied ML model (optional)

Not applicable: no module uses machine learning. The detector is a fixed threshold and ratio rule, and the estimator is a deterministic FFT.

### 1.6 HAL substitution ladder

**Where each level runs:**

| Level | Subsystem / PATH-* | Execution target | HAL | Required target capabilities |
|-------|------------------|------------------|-----|------------------------------|
| VL-0 | All six subsystems; PATH-001…PATH-009 with fake peers | `local` | Mock HAL / fake device API | Python 3.12 + uv, Node.js + pnpm, no radio |
| VL-1 | All six subsystems; all paths except the hardware-only acceptance | `local` | Mock HAL synthetic inputs | Same as VL-0; golden IQ, replay scans, fake NTP and fake watchdog |
| VL-2 | SUB-001 `acq`/`calibrate`/`verify`, SUB-006 `watchdog`; PATH-001, PATH-006, PATH-008, PATH-009 | `Raspberry Pi 5 node` | Real HW HAL | HackRF One, Pi 5 with `/dev/watchdog` and thermal zone, microSD, traceable source HW-010, independent reference HW-011, site NTP and Ethernet |

#### Mock HAL

| Field | Value |
|-------|-------|
| Base-layer port | `SdrPort` (`open`, `info`, `configure`, `read_frames`, `close`), `WatchdogPort`, `ThermalPort`, `ClockPort`, `NtpPort`, `ReportStorePort`, `DataPort` |
| VL-0: deterministic vectors | 39 frames × 131 072 interleaved `int8` I/Q per step; known tones at exact FFT bins; a DC spike at the step centre; one saturated frame; one dropped frame; a vacant-noise-only scan; an adjacent-channel-leakage scan |
| VL-1: synthetic generator | FM stereo signal (mono + 19 kHz pilot + stereo subcarrier), 100 % modulation, SNR 0 dB and 20 dB; 199 channels with a configurable occupancy pattern; 60 min of scans for duty-cycle and alert tests; generation with a fixed seed |
| Generation tool | `verification/golden/generate.py` (Python, NumPy), writing the vectors and `verification/golden/manifest.md` |

**Golden vectors (governance):**

| Vector ID | Simulated condition | SHA-256 digest | Generation parameters | Expected output at consumer |
|-----------|---------------------|----------------|-----------------------|-----------------------------|
| GV-001 | Nominal single carrier, channel 100, −60 dBm equivalent | recorded in `verification/golden/manifest.md` at generation (S2) | 10 Msps, 39 frames, tone at the channel centre, SNR 30 dB, fixed seed | Occupied on channel 100, power within ±0.1 dB of the synthetic level, no withheld flag |
| GV-002 | Occupied channel at SNR 0 dB | same | tone plus AWGN, SNR 0 dB, 20 repetitions | Detection ≥95 % over the repetitions, `e_k ≈ 3.01 dB` |
| GV-003 | Vacant channel | same | noise only, 20 repetitions | False alarm ≤5 %, state Free when the release conditions hold |
| GV-004 | Adjacent-channel leakage | same | strong carrier at channel n, weak carrier at n+2, 20 dB difference | Adjacent channel Uncertain (`uncertain_adjacent_leakage`), never Occupied or Free |
| GV-005 | Saturated capture | same | one frame at full scale in step 1 | Only step-1 channels saturated, power withheld, occupancy Uncertain |
| GV-006 | Dropped frame | same | 38 of 39 frames delivered in step 2 | All 199 records marked, power withheld, occupancy Uncertain, health count = 1 |
| GV-007 | DC spike | same | tone exactly at a step centre | DC-adjacent channels marked, spectrum spike replaced, no false Occupied |
| GV-008 | Crystal offset | same | 20 ppm frequency offset | Estimator correction and mapping bound within 5 kHz at 100 MHz |
| GV-009 | Time unsynced | same | fake clock with no NTP sync | Scans continue with `sync_state = unsynced`, never held |
| GV-010 | Calibration expiring | same | calibration record with `verified_until` in the margin | Power released, calibration alert state `expiring` |

#### Real HW HAL (mock+real only)

| Field | Value |
|-------|-------|
| Base-layer port | The same `SdrPort` as the Mock HAL; the same `WatchdogPort`/`ThermalPort` for the supervisor |
| COTS device | HW-001 HackRF One; HW-002 Pi 5 watchdog and thermal zone |
| Measurement method | Functional and metric scripts against SYS-ACQ-001, SYS-EST-001, SYS-CAL-001, SYS-VER-001 and SYS-SUP-001: P-075 (1 h at 10 Msps, 0 events), P-077 (estimator ≤2.5 s), P-078 (detector ≤0.2 s), P-079 (report write ≤0.05 s), P-087 (scan chain ≤6 s), P-089 (detection ≥95 % at SNR 0 dB), P-090 (mapping ≤5 kHz at 40 °C), P-091 (weak channel next to +20 dB, ≥95 %) |
| Lab procedures | PROTO-003 (`scan_cycle`), PROTO-004 (`estimate_channel_power`), PROTO-005 (`establish_amplitude_calibration`), PROTO-009 (`verify_amplitude_correction`) from SyRS §6; the operator CLI reads its session file and writes the records |
| Reference / calibration | HW-010 traceable source ≤0.5 dB (k = 2), ≤1 ppm; HW-011 independent reference ≤0.5 dB (k = 2), different instrument and chain (R-20); no calibration is invented when the instruments are absent |
| Correction chains | SyRS §4: reference plane at the receiver antenna connector; calibration-cable loss; crystal correction `c` in ppm; antenna gain and antenna-cable loss recorded but not applied to the calibrated quantity |
| Declared tolerances | R-10: absolute error ≤3 dB; acceptance uses 2.5 dB after subtracting the 0.5 dB source uncertainty; verification: 1.0 dB with 0.59 dB measurement uncertainty; mapping: 5 kHz at 100 MHz; crystal: ±20 ppm; power uncertainty: 1.28 dB (1.37 dB DC-adjacent), k = 2 |
| Calibration grade | Development-team screening grade, not a normative calibration; the final compliance use is out of scope (R-32/R-33) |
| Device probe | `hackrf_info`/SoapySDR enumerate: board ID, firmware, serial, USB speed; read the watchdog identity and the thermal zone; failure output names the missing device and the port |
| Capability guard | Reject before configure: centre outside 1–6 000 MHz, sample rate outside 2–20 Msps, LNA outside 0–40 dB, RF amp outside 0–14 dB, AGC on, missing device, or input level above −5 dBm when the level is known; never bypass via a raw device API |
| Safe stop | Stop the stream, never enable TX, close the device, release USB; on timeout or disconnect retry 10 times at 1 s, then stop and let the supervisor restart; close `/dev/watchdog` last |
| Fake device API | `verification/fm_measure/fakes/fake_hackrf.py` and `verification/fm_supervisor/fakes/fake_watchdog.py` implement the same ports from GV-001…GV-010, so the Real HW HAL code path runs at VL-0 without the device |

**Substitution check:**

The same contract vectors (`INT-IQ-001`, `HW-IQ-001`, `SW-WDOG-001`) run against the Mock HAL and the Real HW HAL's fake device API. The check compares the message schema, the frame counts, the counter fields and the error paths; it does not compare RF noise, which is device-specific. A schema or count mismatch fails the check and blocks VL-2.

### 1.7 Telemetry companion

| Field | Value |
|-------|-------|
| Monitored signals | CPU % per process, RSS MB, SoC temperature °C, USB dropped frames, scheduling latency p99, free disk GB, scan duration, report write duration |
| Sampling interval | 1 s |
| Resource budget | ≤2 % of one core and ≤50 MB RSS; the companion never writes to the report |
| Output format | JSON Lines: `{ts_utc_us, target, signal, value, unit, run_id}` |
| Evidence attachment | Each test run writes `verification/telemetry/<run_id>.jsonl`; the `measurement.json` of the run names the file and the run_id |

**Compute-unit operating envelope (repeat per execution target):**

| Field | Value |
|-------|-------|
| Execution target | `local` |
| Subsystems / PATH-* | All VL-0/VL-1 evidence |
| COTS basis | Development host; the GT limits apply to the node, not to the host. The readings are diagnostic and never turn a Mock HAL result into VL-2 evidence. |

| Signal | Nominal threshold | Action if exceeded |
|--------|-------------------|--------------------|
| Temperature | Not applicable on the host | Record only |
| CPU | ≤90 % sustained for the run | Flag evidence as host-limited |
| Dropped buffers | 0 for the Mock HAL | Flag evidence; a non-zero value is an infrastructure defect |
| Scheduling latency | ≤1 000 ms p99 (derived from the 1.02 s scan slack) | Flag evidence and diagnose the host |

| Field | Value |
|-------|-------|
| Execution target | `Raspberry Pi 5 node` |
| Subsystems / PATH-* | VL-2 evidence: PATH-001, PATH-006, PATH-008, PATH-009 |
| COTS basis | HWC-CPU-001…005 (4 cores, 8 GB, 0–70 °C), HWC-ENV-004/005 (40 °C ambient, 60 °C internal air), REF-001 §4.5 (70 % CPU, 1 738 MB demand, 12.8 GB free floor, 20 W power) |

| Signal | Nominal threshold | Action if exceeded |
|--------|-------------------|--------------------|
| Temperature | SoC ≤70 °C; internal air ≤60 °C at 40 °C ambient | Set the `thermal` condition at 70 °C, clear at 65 °C; flag evidence above 80 °C |
| CPU | ≤70 % sustained | Flag evidence; the run is not a valid timing acceptance |
| Dropped buffers | 0 (R-25) | Mark the scan and flag the evidence |
| Scheduling latency | ≤1 000 ms p99 (1.02 s slack) | Flag evidence and repeat the timing measurement |
| Free disk | ≥12.8 GB | Flag evidence; the report rotation rule applies |
| Power | ≤20 W for board + receiver + fan | Flag evidence; the power measurement is P-086 |