# Anexo A — Parámetros de la solución

Todos los valores numéricos de diseño, agrupados por módulo. «Rango» es el intervalo dentro del cual el valor puede ajustarse sin romper otro requisito; «crítico» marca los valores que afectan directamente un criterio de aceptación. «Origen» indica si el valor viene de los requisitos (declarado), se calculó (derivado) o lo propuso el diseñador (propuesto).

> Los nombres de parámetros, campos, estados y códigos de error se conservan en inglés porque son los identificadores que se implementan en el código y en los archivos. Las descripciones breves de estos anexos mantienen el texto técnico original.

## Servicio de hora

| Parámetro | Valor | Rango | Crít. | Origen | Significado |
|---|---|---|---|---|---|
| `timestamp_resolution` | 1 us | 1 a 1000 us | sí | propuesto | el criterio de R-28 requires a scan timestamp resolution of at most 1 ms = 1000 us; the timestamp is an integer count of microseconds, 1000 times finer than the limit. |
| `time_sync_poll_min` | 64 s | 16 a 1024 s |  | propuesto | Shortest interval between network time queries; a value of 64 s is a conventional lower poll for a stable client and costs one small packet per interval on the board Gigabit Ethernet. |
| `time_sync_poll_max` | 1024 s | 64 a 2048 s |  | propuesto | Longest interval between network time queries once the offset is stable; it bounds how long a lost source stays unseen to under `max_sync_age`. |
| `max_clock_offset` | 50 ms | 10 a 200 ms |  | propuesto | Estimated offset above which the clock is declared unsynced. |
| `max_sync_age` | 3600 s | 600 a 7200 s |  | propuesto | Longest time since the last successful network time exchange before the clock is declared unsynced; no fallback clock exists ( chose network time, Q-02-01), so a lost source must become visible within one hour. |
| `startup_sync_wait` | 120 s | 30 a 600 s |  | propuesto | The board real-time clock needs an external battery that is not in the bill of materials (out of scope of this version), so after a power cycle the time is wrong until the first exchange; the first scan waits at most this long. |
| `clock_step_alarm_threshold` | 1000 ms | 100 a 5000 ms |  | propuesto | A jump of the real-time clock against the monotonic clock larger than this between two status refreshes is a clock step, which breaks the order of scan stamps. |
| `time_status_refresh` | 1 s | 0.5 a 5 s |  | propuesto | The time status message is refreshed once per second so that every scan (period of at most 10 s, R-01) reads a status at most 1 s old. |
| `time_sources_min` | 1 count | 1 a 4 count |  | propuesto | The site configuration («Configuración del sitio») must list at least one network time source; no default source is written here because none is cited by the inputs (Q-02-01 gave no source). |

## Configuración del sitio

| Parámetro | Valor | Rango | Crít. | Origen | Significado |
|---|---|---|---|---|---|
| `record_time_minimum` | 10 min | fijo | sí | declarado | R-74 requires that the user can configure the record-taking time with a minimum of 10 minutes; the configuration rejects a smaller value. |
| `record_time_maximum` | 43200 min | 4320 a 129600 min |  | derivado | Longest configurable timed run: the 30-day continuous run of R-48. |
| `mapping_error_limit_default` | 5 kHz | 1 a 20 kHz | sí | declarado | Default limit of the channel-mapping error: the value of R-50. |
| `mapping_error_limit_maximum` | 20 kHz | fijo | sí | declarado | R-75: the user may adjust the limit of the channel-mapping error up to a maximum of 20 kHz; the configuration rejects a larger value. |
| `mapping_error_limit_minimum` | 1 kHz | 0.5 a 5 kHz |  | propuesto | Smallest limit a user may set: below about 1 kHz the limit is finer than the resolution of the frequency check of «Estimador espectral» and every scan would exceed it. |
| `declared_min_power_floor` | -130 dBm | -140 a -110 dBm |  | propuesto | Lowest declared minimum received power per channel the configuration accepts (closes the field of la potencia mínima recibida declarada); about 10 dB below the thermal noise power in 256 kHz of roughly -120 dBm, so no realistic value is refused. |
| `declared_min_power_ceiling` | -5 dBm | fijo |  | declarado | Highest declared minimum received power per channel: the maximum input power of the SDR. |
| `duty_cycle_interval_default` | 60 min | 1 a 1440 min |  | propuesto | Default declared reporting interval of the duty cycle and Uncertain fraction (R-08 says 'declared', no value): one hour; used by «Detector de ocupación». |
| `time_sources_max` | 4 count | 1 a 8 count |  | propuesto | Most network time sources the configuration lists; four allow one fault and one outlier without a listing the board must poll too often. |
| `config_file_max_size` | 1048576 bytes | 65536 a 4194304 bytes |  | propuesto | Largest configuration file accepted: 1 MiB, about 13 times the largest expected file (199 station entries x 400 bytes = 79600 bytes plus about 4 KiB of other fields). |
| `station_entries_max` | 199 count | fijo |  | declarado | One station-assignment entry per channel of the FM Technical Plan, channels 1 to 199 (R-02). |
| `text_field_max_bytes` | 256 bytes | 64 a 1024 bytes |  | propuesto | Longest free-text field (place name or address of R-70, station name): 256 bytes of UTF-8. |
| `silent_hours_field_min` | 0.1 h | 0.1 a 1 h |  | propuesto | Lowest value the alert configuration field 'silent on-air hours' (las horas de silencio) accepts: 6 minutes, above one scan period. |
| `silent_hours_field_max` | 720 h | 24 a 720 h |  | derivado | Highest value of the 'silent on-air hours' field: 30 days, the longest run of R-48. |
| `config_retry_interval` | 30 s | 10 a 300 s |  | propuesto | Interval between attempts to read a missing configuration file; 30 s is far below a scan period of minutes for the first valid scan to pick it up. |

## Adquisición y barrido

| Parámetro | Valor | Rango | Crít. | Origen | Significado |
|---|---|---|---|---|---|
| `sample_rate` | 10 Msps | 10 a 20 Msps | sí | propuesto | Cheapest rate that meets the AC: 20, 16 and 10 Msps all cover the band and the 10 s scan with margin; 10 Msps needs 3 steps but halves the USB payload (20 MB/s) and the estimator load (1.2 Gflop/s) of 20 Msps (40 MB/s, 2.4 Gflop/s), and both are unverified on this board. |
| `usable_bandwidth_fraction` | 0.8 | 0.7 a 0.9 dimensionless |  | propuesto | Share of the complex sample rate assumed flat and free of alias; the analog filter roll-off of the SDR is not in any datasheet, so 0.8 is a conventional assumption checked by the calibration sweep of «Calibración de amplitud». |
| `usable_bandwidth` | 8 MHz | 7 a 9 MHz |  | derivado | Usable band of one step. |
| `band_edge_guard` | 0.1 MHz | 0.05 a 0.3 MHz |  | propuesto | Distance kept between the edge of a channel integration window and the edge of the usable band, so the roll-off does not enter the 256 kHz window. |
| `step_overlap` | 0.5 MHz | 0.3 a 1 MHz | sí | derivado | Overlap of the usable bands of two adjacent steps: at least the 256 kHz window plus the two guards (0.256 + 2 x 0.1 = 0.456 MHz), rounded up to 0.5 MHz, so every channel window fits wholly in one step. |
| `step_count` | 3 count | fijo | sí | derivado | Number of stepped captures per scan that cover every channel window. |
| `step1_centre_frequency` | 90.25 MHz | fijo | sí | propuesto | Centre of step 1: lower band edge 90.25 - 4 = 86.25 MHz, 1.722 MHz below the lowest window edge 87.972 MHz; placed between channel centres (90.2 and 90.3) so the DC spike of the SDR lies in only two windows instead of three. |
| `step2_centre_frequency` | 97.75 MHz | fijo | sí | derivado | Centre of step 2 = step 1 centre + 7.5 MHz advance (`usable_bandwidth` - `step_overlap`); between channel centres 97.7 and 97.8. |
| `step3_centre_frequency` | 105.25 MHz | fijo | sí | derivado | Centre of step 3 = step 2 centre + 7.5 MHz; upper band edge 109.25 MHz, 1.222 MHz above the highest window edge 108.028 MHz; between channel centres 105.2 and 105.3. |
| `step1_last_channel` | 60 count | fijo | sí | derivado | Last channel measured in step 1: channel 60 (94.0 MHz) has its window upper edge 94.128 MHz <= 94.25 - 0.1 = 94.15 MHz; channel 61 (94.228 MHz upper edge) does not. |
| `step2_last_channel` | 135 count | fijo | sí | derivado | Last channel measured in step 2: channel 135 (101.5 MHz) has upper window edge 101.628 <= 101.75 - 0.1 = 101.65 MHz; channel 136 does not and goes to step 3 (lower edge 101.472 >= 101.25 + 0.1 = 101.35 MHz). |
| `retune_settle` | 0.1 s | 0.05 a 0.5 s |  | propuesto | Time from the retune command until the first sample used; covers synthesizer lock and filter transient. |
| `frame_samples` | 131072 count | 16384 a 524288 count |  | propuesto | Complex samples in one frame (one transfer block of 262144 bytes): a multiple of 2048 (half the transform length of «Estimador espectral») so the estimator never splits a segment across frames. |
| `frames_per_dwell` | 39 count | 20 a 78 count | sí | derivado | Whole number of frames in one capture: ceil(0.5 s x 10 Msps / 131072) = ceil(38.15) = 39, so a capture holds an integer number of frames and a loss is a whole number of frames. |
| `dwell` | 0.5112 s | 0.25 a 1.02 s |  | derivado | Duration of one capture. |
| `scan_period` | 6 s | 3 a 7 s | sí | propuesto | Interval between scan starts: 40 % below the 10 s of R-01 (margin rule 30 % allows up to 7 s); the active capture time is 1.8335 s so about 4.2 s remain for processing and the rest of the chain. |
| `scan_late_threshold` | 7 s | fijo |  | derivado | A scan that takes longer than 70 % of the R-01 limit is flagged late. |
| `rf_amp_gain` | 0 dB | 0 a 14 dB | sí | propuesto | The front-end amplifier is off: strong FM transmitters near the site overload the front end and the 8-bit converter has little headroom. |
| `lna_gain` | 16 dB | 0 a 40 dB | sí | propuesto | Fixed first-stage gain, a starting value, a multiple of 8 dB as assumed step; confirmed or changed by the dynamic-range characterization of «Calibración de amplitud». |
| `baseband_gain` | 16 dB | 0 a 40 dB | sí | propuesto | Fixed baseband gain, a starting value and a multiple of 2 dB as assumed step; total gain 0 + 16 + 16 = 32 dB; range ceiling 40 dB is an assumption, the device range is not in a datasheet. |
| `clip_sample_count_threshold` | 1 count | fijo | sí | derivado | R-24 flags a capture when any retained raw sample is at converter full scale: one sample is enough. |
| `ring_buffer_frames` | 64 count | 16 a 256 count | sí | propuesto | Frames the host ring buffer holds between the transfer thread and the estimator: 64 x 13.1 ms = 0.839 s of data, enough to ride out a processing stall of under 0.8 s without an overflow. |
| `retune_retry_max` | 3 count | 1 a 5 count |  | propuesto | Attempts to retune before a step is declared failed: 3 attempts at 0.1 s add at most 0.3 s to a scan. |
| `retune_retry_interval` | 0.1 s | 0.05 a 0.5 s |  | propuesto | Wait between retune attempts, equal to the settle time. |
| `device_reopen_max` | 10 count | 3 a 30 count |  | propuesto | Attempts to reopen the SDR after a USB error before the acquisition process stops and the supervisor restarts it («Supervisión y manejo de errores»): 10 attempts at 1 s are 10 s, about 2 scan periods. |
| `device_reopen_interval` | 1 s | 0.5 a 5 s |  | propuesto | Wait between reopen attempts. |
| `consecutive_flagged_scan_limit` | 3 count | 2 a 10 count |  | propuesto | After 3 consecutive scans flagged for overflow, dropped frames or retune failure the acquisition process is restarted by the supervisor: 3 scan periods (18 s), the same count as the sensor-offline rule of R-37. |
| `frame_period` | 13.1072 ms | fijo |  | derivado | Time one frame of `frame_samples` samples takes at `sample_rate`. |

## Estimador espectral

| Parámetro | Valor | Rango | Crít. | Origen | Significado |
|---|---|---|---|---|---|
| `fft_length` | 4096 count | 2048 a 8192 count | sí | propuesto | Candidates by parameter-rules: 2048 (bin 4.88 kHz: mapping bound 2.44 + 0.49 + 2.0 = 4.93 kHz, 1.4 % margin to 5 kHz), 4096 (bin 2.44 kHz: 3.46 kHz, 30.7 % margin), 8192 (bin 1.22 kHz: 0.61 + 0.12 + 2.0 = 2.73 kHz, 45 % margin, +8 % operations per sample). |
| `window_family` | Hann | fijo | sí | propuesto | w[n] = 0.5 (1 - cos(2 pi n / N)), n = 0..N-1. |
| `segment_overlap` | 0.5 | 0.5 a 0.75 dimensionless |  | propuesto | 50 % overlap with a Hann window uses every sample twice with similar weight and is the cheapest overlap that avoids the loss of data at the window edges. |
| `hop_size` | 2048 count | fijo |  | derivado | Samples between the starts of two segments. |
| `segments_per_capture` | 2495 count | fijo |  | derivado | Number of segments averaged for one capture (the averaging count). |
| `bin_spacing` | 2441.40625 Hz | fijo |  | derivado | Frequency spacing of the transform bins. |
| `integration_bins` | 105 count | fijo | sí | derivado | Bins summed for one channel: the bins with centres within 128 kHz of the channel centre, offsets -52 to +52 bins; 105 bins cover at least 256 kHz. |
| `integration_bandwidth` | 256.347 kHz | 256 a 260 kHz | sí | derivado | Bandwidth over which the channel power is integrated (R-69): equals the number of bins times the bin spacing; at least the 256 kHz necessary bandwidth of a stereophonic FM emission. |
| `hann_equivalent_noise_bandwidth` | 1.5 | fijo |  | derivado | Noise-equivalent bandwidth of the Hann window in bins, used to normalise the power: sum(w) = N/2 and sum(w^2) = 3N/8 give ENBW = N x sum(w^2) / sum(w)^2 = 1.5 bins. |
| `dc_mask_half_width` | 3 count | 2 a 6 count |  | propuesto | Bins removed on each side of the DC bin to suppress the zero-frequency spike of the SDR: the Hann main lobe is 2 bins wide on each side, so 3 bins cover it; 7 bins = 17.1 kHz of the 256 kHz window. |
| `dc_interpolation_bins` | 3 count | 2 a 6 count |  | propuesto | The masked bins are replaced by the mean of the bins at offsets 4 to 6 on both sides (3 bins on each side). |
| `dc_adjacent_uncertainty` | 0.5 dB | 0.2 a 2 dB |  | propuesto | Extra uncertainty written for the six channels whose window contains the masked bins (7 of 105 bins, 6.7 %, 0.29 dB if the replaced power were wrong by 100 %); 0.5 dB is the proposed bound. |
| `frequency_estimate_error_bound` | 244.14 Hz | 100 a 1220.7 Hz | sí | propuesto | Error bound of the tone frequency found by parabolic interpolation on the logarithm of three bins: 0.1 bin = 244.14 Hz, an assumption verified with the synthetic tone vectors of the test spec. |
| `frequency_reference_tolerance_100mhz` | 2.0 kHz | fijo | sí | derivado | Largest frequency error of the stock crystal at 100 MHz: the relative tolerance of (20 ppm) times 100 MHz. |
| `mapping_rounding_error` | 1.2207 kHz | fijo | sí | derivado | Half a bin: the channel window is centred on the nearest bin, so the window centre can be off the channel centre by up to half the bin spacing. |
| `mapping_error_bound_100mhz` | 3.4648 kHz | 0 a 5 kHz | sí | derivado | Worst-case channel-mapping error at 100 MHz: rounding `mapping_rounding_error` + interpolation `frequency_estimate_error_bound` + crystal tolerance `frequency_reference_tolerance_100mhz` = 1.2207 + 0.2441 + 2.0 = 3.4648 kHz, which is 30.7 % below the 5 kHz of R-50; at 107.9 MHz the crystal term is 2.158 kHz and the… |
| `estimator_time_allocation` | 2.5 s | 1 a 2.9 s |  | propuesto | Time given to the estimator for the three captures of a scan, from the 4.1665 s left after the active captures with a 30 % margin (usable 2.9166 s); 2.5 s leaves 40 %. |
| `statistical_uncertainty_bound` | 0.015 dB | fijo |  | derivado | Statistical uncertainty of a channel power for a noise-like signal: relative standard deviation 1 / sqrt(M_eff x B_eff) with M_eff at least 2495 / 2 = 1247 independent segments (50 % overlap) and B_eff = 105 / 1.5 = 70 independent bins gives 0.00338, i.e. |
| `sample_scale` | 128 count | fijo |  | derivado | Each I and Q code is divided by 128 so that full scale of the 8-bit converter (codes -128 to +127) is magnitude 1; levels are in dBFS (full-scale unit: power of a complex sample with I = 1, Q = 0 is 0 dBFS). |

## Calibración de amplitud

| Parámetro | Valor | Rango | Crít. | Origen | Significado |
|---|---|---|---|---|---|
| `warmup_time` | 30 min | 10 a 120 min |  | propuesto | Time the node runs at the deployed gains before the measurements of the calibration, so the SDR and board have reached their operating temperature; the thermal behaviour of the SDR is not in a datasheet, so 30 min is an assumption confirmed by the drift check of the qualification test. |
| `noise_floor_scans` | 10 count | 5 a 60 count |  | propuesto | Scans taken with the antenna port terminated by 50 ohm to record the receiver noise floor per channel; 10 scans of 6 s average the statistics (0.015 dB per scan, «Estimador espectral») far below the channel-to-channel variation. |
| `calibration_point_count` | 24 count | fijo | sí | derivado | Frequencies at which the offset is measured, per step, at channel centres: step 1 channels 1, 11, 21, 31, 41, 51, 60 (7 points); step 2 channels 61, 71, 81, 91, 101, 111, 121, 131, 135 (9 points); step 3 channels 136, 141, 151, 161, 171, 181, 191, 199 (8 points); a point spacing of at most 1 MHz, with both ends of… |
| `repeats_per_point` | 5 count | 3 a 20 count |  | propuesto | Scans taken at each point; the offset uses their median and their spread is checked against `repeatability_max`. |
| `point_settle_time` | 30 s | 10 a 120 s |  | propuesto | Wait after the operator sets a frequency and level on the source before scans are counted; covers source settling and the end of the scan already running. |
| `sweep_level_min` | -100 dBm | -110 a -90 dBm |  | propuesto | Lowest level of the dynamic-range sweep (R-55), a level near the expected noise floor of the receiver (about -120 dBm thermal power in 256 kHz plus the receiver noise figure, which is not in a datasheet). |
| `sweep_level_max` | -20 dBm | -30 a -15 dBm | sí | derivado | Highest level of the sweep: the SDR maximum input power of -5 dBm less the headroom `input_headroom`; the sweep also stops at the first clipped capture. |
| `input_headroom` | 15 dB | 10 a 25 dB |  | propuesto | Margin kept below the -5 dBm limit when a source is connected, which covers the source level uncertainty and a setting error. |
| `sweep_step` | 5 dB | 1 a 10 dB |  | propuesto | Level step of the sweep: 5 dB gives 17 levels from -100 to -20 dBm and locates the compression onset to within 5 dB. |
| `compression_criterion` | 1 dB | 0.5 a 3 dB | sí | propuesto | A level is compressed when the measured power is lower than the input power plus the linear offset by this amount: the 1 dB compression convention. |
| `range_high_headroom` | 3 dB | 1 a 6 dB | sí | propuesto | Margin below the first level that is compressed or clipped; the upper end of the usable range is that level minus this margin. |
| `range_low_snr` | 10 dB | fijo |  | declarado | The lower end of the usable range is the lowest level that is at least 10 dB above the measured noise floor of the channel, the same margin R-06 uses for a Free release. |
| `reference_level_below_range_high` | 10 dB | 6 a 20 dB |  | propuesto | The level at which the offsets are measured is the upper end of the usable range minus this margin, so the reference tone is inside the linear region and well above the noise. |
| `reference_level_min` | -70 dBm | -80 a -60 dBm |  | propuesto | The reference level never falls below this value, so the signal stays at least 40 dB above the expected receiver noise floor. |
| `reference_level_max` | -30 dBm | -40 a -25 dBm |  | propuesto | The reference level never exceeds this value: 25 dB below the -5 dBm limit of the SDR input. |
| `reference_source_level_uncertainty_max` | 0.5 dB | 0.1 a 1 dB | sí | propuesto | Largest expanded uncertainty (k = 2) of the traceable source level the calibration accepts; it is a requirement on the external instrument, not a purchased item (calibration references are outside the cost of R-53). |
| `reference_source_frequency_uncertainty_max` | 1 ppm | 0.1 a 5 ppm |  | propuesto | Largest relative frequency uncertainty of the source: 1 ppm = 0.1 kHz at 100 MHz, small against the 2 kHz crystal term it must resolve. |
| `mismatch_uncertainty` | 0.3 dB | 0.1 a 0.6 dB |  | propuesto | Expanded uncertainty from the impedance mismatch between the source, the cable and the SDR port; the return loss of the SDR port is not in a datasheet, so 0.3 dB is an assumption checked in the qualification test. |
| `cable_loss_uncertainty_max` | 0.1 dB | 0.05 a 0.3 dB |  | propuesto | Largest expanded uncertainty of the loss of the cable and adapters between source and SDR port, known by measurement before use. |
| `interpolation_residual_max` | 0.5 dB | 0.2 a 1 dB | sí | propuesto | Largest difference accepted between the offset measured at an interior point and the offset interpolated from its two neighbours (leave-one-out); also the interpolation term of the uncertainty budget. |
| `repeatability_max` | 0.2 dB | 0.05 a 0.5 dB |  | propuesto | Largest spread (maximum minus minimum) of the 5 scans at one point accepted; larger spread means the point was disturbed. |
| `linearity_deviation_max` | 0.2 dB | 0.1 a 0.5 dB |  | propuesto | Largest deviation of the sweep from a straight line inside the usable range; also the linearity term of the uncertainty budget. |
| `drift_allowance` | 1 dB | 0.5 a 2 dB | sí | propuesto | Expanded uncertainty allowed for the change of the receiver gain between the calibration and the next verification; it equals the verification tolerance of «Verificación periódica», which flags a larger change. |
| `total_uncertainty_limit` | 2.5 dB | fijo | sí | derivado | Largest expanded uncertainty the calibration may carry so that el criterio de R-10 stays achievable: the limit 3 dB less the expanded uncertainty assumed for the independent reference (0.5 dB). |
| `snr_at_reference_min` | 40 dB | 30 a 60 dB |  | propuesto | Smallest ratio between the reference tone power and the noise floor of its channel for the offset to be accepted, so the noise adds under 0.001 dB. |
| `frequency_correction_limit` | 20 ppm | fijo | sí | declarado | Largest frequency error of the SDR crystal accepted; a larger one is out of the specified tolerance of the stock crystal. |
| `expanded_uncertainty_default` | 1.28 dB | 0 a 2.5 dB | sí | derivado | Expanded uncertainty (k = 2, half-width) of a calibrated channel power: root sum of squares of the expanded components of the budget: source 0.5, mismatch 0.3, cable 0.1, statistical 0.015, interpolation 0.5, drift 1.0, linearity 0.2 dB. |
| `expanded_uncertainty_dc_adjacent` | 1.37 dB | 0 a 2.5 dB |  | derivado | The same budget with the DC-adjacent term of «Estimador espectral» (0.5 dB) added, for channels 22, 23, 77, 78, 172, 173. |
| `calibration_record_max_size` | 65536 bytes | 16384 a 262144 bytes |  | propuesto | Largest size of one calibration record file: 64 KiB, about 10 times the expected record (24 offsets, 199 noise floors, budgets, identifiers). |
| `calibration_write_retries` | 3 count | 1 a 5 count |  | propuesto | Attempts to write the calibration record before it is declared not stored. |
| `calibration_write_retry_interval` | 1 s | 0.5 a 5 s |  | propuesto | Wait between write attempts. |
| `establish_attempts_before_stop` | 3 count | 1 a 5 count |  | propuesto | After 3 rejected establishments in a row the operator stops and checks the hardware instead of repeating. |

## Detector de ocupación

| Parámetro | Valor | Rango | Crít. | Origen | Significado |
|---|---|---|---|---|---|
| `occupied_threshold_excess` | 1.5 dB | 1.0 a 2.0 dB | sí | propuesto | A channel is a candidate for Occupied when its power is at least this much above its noise reference. |
| `free_threshold_excess` | 1.0 dB | 0.5 a 1.4 dB | sí | propuesto | A channel can be released Free only when its power is at most this much above its noise reference: 1.0 dB leaves 0.5 dB of Uncertain band below the occupied threshold (with the hysteresis) and a vacant channel (excess 0 dB, noise-reference uncertainty 0.50 dB) falls below it with probability 97.7 %. |
| `hysteresis` | 0.5 dB | 0 a 1.0 dB |  | propuesto | A channel that was Occupied in the previous scan stays Occupied while its excess is at least `occupied_threshold_excess` minus this value (1.0 dB), which equals `free_threshold_excess`, so the Free and the staying-Occupied regions never overlap. |
| `minimum_occupancy_scans` | 1 count | 1 a 3 count |  | propuesto | Scans a channel must look occupied before it is reported Occupied: 1 (no filtering), because el criterio de R-04 and el criterio de R-05 are judged per observation. |
| `noise_quantile_fraction` | 0.1 | 0.05 a 0.25 dimensionless | sí | propuesto | The noise reference of a step is the mean power of the lowest 10 % of the points of its calibrated spectrum, which are the points least affected by stations; the FM band has gaps between stations, so 10 % of the points are noise-dominated. |
| `noise_points_half_width` | 3.6 MHz | 3.0 a 3.8 MHz |  | derivado | Spectrum points within 3.6 MHz of the step centre are used for the noise reference, 90 % of the usable half-width of 4 MHz («Adquisición y barrido»), to stay clear of the analog filter roll-off at the band edges. |
| `noise_dc_exclusion_points` | 5 count | 3 a 10 count |  | propuesto | Points on each side of the LO excluded from the noise reference, 5 points = 48.8 kHz, beyond the DC mask of «Estimador espectral». |
| `noise_smoothing_scans` | 10 count | 3 a 60 count |  | propuesto | The noise reference of a step is the median of its estimates over the last 10 scans (60 s): fast enough to follow gain drift (hours) and slow enough to reject a passing transmitter. |
| `noise_shape_sigma` | 0.5 dB | 0.2 a 0.9 dB | sí | propuesto | Assumed standard deviation of the true vacant-channel power around the step noise reference caused by non-flat external noise and receiver response across the step; this is the dominant term of the noise-reference uncertainty and is checked by the qualification test on vacant channels. |
| `noise_reference_uncertainty` | 0.5 dB | 0.2 a 0.91 dB | sí | derivado | Standard uncertainty of the noise reference of a channel: root sum of squares of the statistical error of the mean of the lowest points (0.05 dB), the statistical error of the stored noise-floor shape (0.02 dB) and `noise_shape_sigma` (0.5 dB). |
| `noise_below_calibration_limit` | 3 dB | 1 a 6 dB |  | propuesto | A step noise reference more than 3 dB below the receiver noise floor stored at calibration cannot be right (the receiver floor is a lower bound): it signals a gain drift or an invalid calibration and makes the reference unreliable. |
| `noise_above_calibration_limit` | 30 dB | 15 a 40 dB |  | propuesto | A step noise reference more than 30 dB above the stored receiver floor is taken as a band in which the lowest points are not noise (interference or no gaps): the reference is unreliable and every channel of the step is Uncertain. |
| `release_margin` | 10 dB | fijo | sí | declarado | A channel is released Free only if the declared minimum received power is at least this far above the noise reference of the channel. |
| `adjacency_range_channels` | 2 count | fijo | sí | derivado | Windows of two channels overlap when their centres are less than 256.347 kHz apart: channels 1 and 2 apart (100 and 200 kHz) overlap, 3 apart (300 kHz) do not. |
| `inner_half_points` | 3 count | 2 a 4 count |  | propuesto | The inner band of a channel is the point nearest its centre plus 3 points each side (7 points = 68.4 kHz). |
| `flank_first_offset` | 5 count | 4 a 6 count |  | propuesto | The flanks of a channel start 5 points (48.8 kHz) from its centre point. |
| `flank_last_offset` | 10 count | 8 a 12 count |  | propuesto | The flanks end 10 points (97.7 kHz) from the centre point: 6 points on each side, 12 in all; the band edge guard of «Adquisición y barrido» keeps these points inside the usable band. |
| `own_carrier_ratio_min` | 0 dB | -1 a 3 dB | sí | propuesto | When a neighbour within `adjacency_range_channels` channels looks occupied, a channel is Occupied only if the mean power density of its inner band is at least this much above that of its flanks: a hump at the centre means a signal of its own; a valley means the energy belongs to the neighbours. |
| `detector_time_allocation` | 0.2 s | 0.05 a 1.0 s |  | propuesto | Time given to the detector per scan (sorting 3 x 726 points and classifying 199 channels). |
| `expected_false_alarm_probability` | 0.14 % | 0 a 5 % | sí | derivado | False-alarm probability of an isolated vacant channel: P(noise-reference error below -1.5 dB) = Q(1.5 / 0.503) = Q(2.98) = 0.14 %, below the 5 % of R-05 with a margin of 4.86 points. |
| `expected_detection_probability_snr0` | 99.87 % | 95 a 100 % | sí | derivado | Detection probability of an isolated occupied channel at SNR 0 dB: the excess is 10 log10(2) = 3.01 dB; P(noise-reference error below 3.01 - 1.5 = 1.51 dB) = Phi(1.51 / 0.503) = Phi(3.00) = 99.87 %, above the 95 % of R-04 with a margin of 4.87 points. |

## Verificación periódica

| Parámetro | Valor | Rango | Crít. | Origen | Significado |
|---|---|---|---|---|---|
| `verification_channel_count` | 6 count | 6 a 12 count | sí | propuesto | Channels measured at each verification: channels 16 and 46 (step 1), 76 and 126 (step 2), 146 and 186 (step 3), none of them a calibration point, so the check also tests the interpolation; two per step cover the three steps. |
| `verification_levels_per_channel` | 2 count | 1 a 3 count |  | propuesto | Two levels per channel: the reference level of the calibration and a lower level, so a gain error and a level-dependent error both show; 6 channels x 2 levels = 12 measurements. |
| `verification_level_offset` | 20 dB | 10 a 30 dB |  | propuesto | The lower verification level is the calibration reference level minus 20 dB, but not below the lower end of the usable range plus `range_low_snr` (10 dB). |
| `verification_tolerance` | 1.0 dB | 0.5 a 2.0 dB | sí | propuesto | Largest difference accepted between the calibrated power and the independent reference at a verification point: equal to the drift allowance `drift_allowance` of the uncertainty budget, so a passing verification keeps the budget valid; the combined uncertainty then stays at 1.28 dB, under the 2.5 dB limit. |
| `verification_measurement_uncertainty` | 0.59 dB | 0.2 a 1.0 dB | sí | derivado | Expanded uncertainty (k = 2) of one verification difference from the independent reference, cable and mismatch: sqrt(0.5^2 + 0.1^2 + 0.3^2) = 0.592 dB, using `independent_reference_uncertainty_max`, `cable_loss_uncertainty_max` and `mismatch_uncertainty`. |
| `verification_repeat_limit` | 1 count | 0 a 2 count |  | propuesto | An inconclusive verification (a difference above the tolerance that is not above tolerance plus the measurement uncertainty) is repeated once; a second inconclusive result counts as failed. |
| `verification_duration` | 39 min | 39 a 78 min |  | derivado | Duration of one verification: set-up 10 min + 12 measurements x 2 min (60 s operator, 30 s settle, 5 scans of 6 s) + record 5 min. |
| `verification_interval_min` | 345600 s | fijo | sí | derivado | Shortest verification interval the calibration record may declare (el intervalo de verificación y su margen bound, the value is declared at implementation): verifications may use at most 25 % (`verification_downtime_share_max`) of the 36 h unavailability that R-48 allows in 30 days = 540 min, with the 30 % time… |
| `verification_interval_max` | 3456000 s | fijo | sí | derivado | Longest verification interval the record may declare (el intervalo de verificación y su margen bound): 30 days, the length of the continuous run of R-48, so a run is never longer than one interval; no drift figure for the gain exists in a source, so a longer interval would rest on no evidence. |
| `expiry_margin_min` | 3600 s | fijo |  | propuesto | Shortest expiry margin the record may declare (el intervalo de verificación y su margen bound): 1 hour, so the calibration-not-demonstrated alert (R-38) is raised at least one hour before power values are withheld. |
| `expiry_margin_max` | 604800 s | fijo |  | propuesto | Longest expiry margin: 7 days, and always shorter than the declared interval; a longer margin would keep the node in 'expiring' for most of a short interval. |
| `verification_downtime_share_max` | 25 % | 10 a 50 % |  | propuesto | Share of the 36 h unavailability allowed by R-48 that verifications may use: 25 %; the rest is left to calibration, restarts and failures. |
| `independent_reference_uncertainty_max` | 0.5 dB | 0.1 a 1.0 dB | sí | propuesto | Largest expanded uncertainty (k = 2) of the independent reference accepted; a requirement on the external instrument, as `reference_source_level_uncertainty_max`; the 0.5 dB is the one `total_uncertainty_limit` already assumes. |
| `validation_record_max_size` | 65536 bytes | 16384 a 262144 bytes |  | propuesto | Largest size of one validation record file (12 measurements, identities, results): 64 KiB, about 20 times the expected record. |
> **Nota sobre `verification_interval_max`:** el valor aprobado es 3 456 000 s (40 días), pero su justificación dice «30 días, la duración de la corrida continua», que son 2 592 000 s. Es un error de cálculo del paquete aprobado; ver la sección 9.4 del documento principal. Hasta decidirlo, declare un intervalo de 30 días o menos.


## Comparador con asignaciones

| Parámetro | Valor | Rango | Crít. | Origen | Significado |
|---|---|---|---|---|---|
| `comparison_time_allocation` | 0.01 s | 0.001 a 0.1 s |  | propuesto | Time given to the comparison of 199 channels with the reference: table lookups and a four-way decision per channel, a few thousand operations. |
| `comparison_result_count` | 4 count | fijo | sí | declarado | The comparison result takes one of four values: consistent, unassigned-occupied, assigned-free, indeterminate. |

## Registros de escaneo y de salud

| Parámetro | Valor | Rango | Crít. | Origen | Significado |
|---|---|---|---|---|---|
| `evidence_label` | Screening evidence only: not a compliance determination | fijo | sí | propuesto | Fixed text carried by every scan header, health record, report and web view (R-32); the word 'compliance' appears only in this label, which denies a determination (R-33). |
| `stored_power_resolution` | 0.01 dB | 0.001 a 0.1 dB |  | propuesto | Power, excess and uncertainty are stored in dB with 2 decimals: finer than the 0.015 dB statistical term, so storage adds no visible error. |
| `records_per_scan` | 199 count | fijo | sí | declarado | One channel record per channel of the FM Technical Plan in every full-band scan (R-02, el criterio de R-02, el criterio de R-15). |
| `forbidden_wording` | compliant, non-compliant, noncompliant, compliance, non-compliance, violation, infringement, breach, illegal, unlawful, authorised, unauthorised | fijo | sí | propuesto | Words that no generated text (alert, record, report, view) may contain, except the exact label `evidence_label`; used by the inspection of el criterio de R-33 and by the self-check of the record builder. |
| `limit_comparison_rule` | within_limit when P + U <= L; outside_limit when P - U > L; indeterminate otherwise | fijo | sí | propuesto | Comparison of the calibrated power P with the configured limit L using the expanded uncertainty U (k = 2): a power whose uncertainty interval straddles the limit is indeterminate, never rounded into one side (R-14). |
| `channel_record_max_size` | 1024 bytes | 512 a 2048 bytes |  | propuesto | Largest size of one serialized channel record: 1 KiB, about 1.5 times the expected 650 bytes of JSON with the fields of `channel_record`. |
| `scan_header_max_size` | 4096 bytes | 2048 a 8192 bytes |  | propuesto | Largest size of one serialized scan header (3 acquisitions, location text up to 3 x 256 bytes, identifiers): 4 KiB. |
| `health_record_max_size` | 1024 bytes | 512 a 2048 bytes |  | propuesto | Largest size of one serialized health record: 1 KiB. |
| `record_build_time_allocation` | 0.15 s | 0.05 a 0.5 s |  | propuesto | Time given to build and serialize 199 channel records, the header and the health record (about 0.2 MB of JSON). |

## Historial en memoria

| Parámetro | Valor | Rango | Crít. | Origen | Significado |
|---|---|---|---|---|---|
| `history_window` | 744 h | 48 a 744 h | sí | derivado | Length of the volatile history: the longest value of 'silent on-air hours' the configuration accepts (720 h, `silent_hours_field_max` of «Configuración del sitio») plus 24 h of earlier duty cycle that the silence alert needs ('previously above 90 %'), which also covers the 24 h views and the 24 h drift check. |
| `bin_length` | 60 s | 10 a 300 s |  | propuesto | Time resolution of the stored history: one-minute bins of 10 scans; the views of R-41 and R-43 need no finer resolution and the memory stays small. |
| `bins_per_channel` | 44640 count | fijo |  | derivado | Bins held per channel: the window divided by the bin length. |
| `bin_record_size` | 24 bytes | fijo |  | derivado | Size of one bin: seven counters of 2 bytes (scans, released, occupied, free, uncertain, assigned-free, unassigned-occupied), mean and maximum released power as float32, one byte for the most frequent withheld reason and one pad byte: 14 + 8 + 2 = 24. |
| `scan_series_entry_size` | 28 bytes | fijo |  | derivado | Size of one entry of the per-scan series (UTC stamp 8, median noise floor 4, overflow count 4, dropped-frame count 4, records published 4, state flags 4). |
| `series_length` | 446400 count | fijo |  | derivado | Entries of the per-scan series: one per scan over the window at the scan period of 6 s. |
| `swap_space` | 0 MB | fijo | sí | derivado | No swap area (file, partition or compressed device backed by the storage medium) may exist, so memory pages holding history are never written to the disk (R-31). |
| `core_dump_limit` | 0 bytes | fijo | sí | derivado | Core dumps are disabled so a crash does not write the memory (and the history) to disk. |
| `history_memory_cap` | 512 MB | 256 a 1024 MB |  | propuesto | Upper bound of the memory the history may take: 512 MB, 2.3 times the 225.9 MB of the full window and 6.4 % of the 8 GB board. |
| `history_update_time` | 0.02 s | 0.005 a 0.2 s |  | propuesto | Time given to add a scan to the bins and the series (199 bin updates and one series entry). |
| `view_span_default` | 24 h | fijo | sí | declarado | Span of the time views: the last 24 hours. |

## Escritor de informes

| Parámetro | Valor | Rango | Crít. | Origen | Significado |
|---|---|---|---|---|---|
| `report_row_size` | 200 bytes | 150 a 300 bytes |  | propuesto | Average size of one channel row of the report in the comma-separated line format of `report_lines` (28 columns of about 7 characters); far below the 650 bytes of the JSON record, because the constant fields go in the scan line. |
| `segment_length` | 3600 s | 900 a 21600 s |  | propuesto | A new report segment file is opened every hour (600 scans, 25 MB): short enough that one corrupt file loses little, long enough to keep the number of files per 30 days at 720. |
| `flush_every_scans` | 1 count | fijo | sí | derivado | The report is flushed to the card after every scan, so a power loss costs at most the scan that was being built: all results produced before the interruption are in the file (R-73, el criterio de R-73). |
| `progress_update_interval` | 60 s | 10 a 300 s |  | propuesto | The progress file (last scan time and scan count) is rewritten every minute, so an interrupted run can be closed with an end time within one minute of the interruption. |
| `free_space_floor_fraction` | 0.2 | 0.1 a 0.3 dimensionless |  | derivado | Share of the card kept free: the 20 % storage planning margin. |
| `free_space_floor` | 12.8 GB | 6.4 a 19.2 GB |  | derivado | Free space below which the oldest closed report segments are deleted. |
| `report_retention_target` | 30 d | 30 a 68 d | sí | derivado | The package guarantees that at least the last 30 days of report are on the card before any rotation: the length of the continuous run of R-48; the card holds 68 days. |
| `scan_and_health_line_size` | 1800 bytes | 1000 a 3000 bytes |  | propuesto | Size of the scan line (stamp, gains and flags of three acquisitions, calibration, configuration hash) and the health line per scan: 1500 + 300 bytes. |
| `report_volume_per_day` | 599.04 MB | fijo |  | derivado | Report data written per day at the scan period of 6 s: 14,400 scans x (199 x 200 + 1800) bytes. |
| `report_write_time_allocation` | 0.05 s | 0.01 a 0.5 s |  | propuesto | Time given to write and flush about 41.6 KB per scan. |
| `write_retry_count` | 3 count | 1 a 5 count |  | propuesto | Attempts to write a scan before it is held in the pending buffer. |
| `write_retry_interval` | 1 s | 0.5 a 5 s |  | propuesto | Wait between write attempts. |
| `pending_scans_max` | 10 count | 2 a 60 count |  | propuesto | Scans held in memory when writing fails: 10 scans (60 s, 0.42 MB); this is report data not yet saved, not a second copy of the history, and it is dropped, never written elsewhere. |
| `free_space_check_interval` | 60 s | 10 a 600 s |  | propuesto | Free space is checked once a minute and at each segment change. |
| `os_and_software_size` | 10 GB | 6 a 16 GB |  | propuesto | Space taken by the operating system, the runtime and the package: an assumption (no figure in a datasheet); the free-space floor protects the report if it is larger. |
| `report_header_max_size` | 8192 bytes | 4096 a 16384 bytes |  | propuesto | Largest size of the report header file (run identity, location text, configuration, calibration and reference identifiers, execution time): 8 KiB. |

## Motor de alertas

| Parámetro | Valor | Rango | Crít. | Origen | Significado |
|---|---|---|---|---|---|
| `silent_prior_duty_threshold` | 90 % | fijo | sí | declarado | The duty cycle a station must have exceeded before its silence counts as an alert: R-34 says 'previously above 90% duty cycle'. |
| `prior_duty_window` | 24 h | 12 a 24 h | sí | propuesto | R-34 says 'previously' without a span. |
| `silence_credit_per_scan` | 6 s | fijo | sí | derivado | Each assigned-free scan credits one scan period of silence time and nothing else credits time, so an Uncertain scan adds exactly 0 s (R-35). |
| `active_scans_to_break_silence` | 3 count | 3 a 5 count | sí | propuesto | Occupied scans inside one 60 s bin (10 scans) needed to end a silent run. |
| `prior_duty_min_observation_share` | 50 % | 25 a 90 % | sí | propuesto | Share of the scans of the prior window that must be Occupied or Free (Uncertain are excluded from the duty cycle, as in «Detector de ocupación») for the prior duty cycle to be shown: 50 % of 14,400 scans = 7,200 observations. |
| `unexpected_persistence_scans` | 3 count | 2 a 10 count | sí | propuesto | Consecutive scans a channel must be Occupied and unassigned before the alert is raised. |
| `sensor_offline_scan_periods` | 3 count | fijo | sí | declarado | Scan periods without a health point after which the sensor-offline alert is raised; also the number of consecutive health points that clear it. |
| `sensor_offline_timeout` | 18 s | fijo | sí | derivado | Time without a health point after which the alert is raised. |
| `offline_check_interval` | 1 s | 0.5 a 6 s |  | propuesto | How often the watchdog compares the time since the last health point with `sensor_offline_timeout`; 1 s equals the time-status refresh `time_status_refresh`, so the alert is raised at most 19 s after the last health point (18 s + 1 s). |
| `alert_clear_count` | 10 count | 3 a 60 count |  | propuesto | Consecutive evaluations without the condition before a scan-based or drift alert is cleared (10 scans = 60 s; 10 minute-evaluations = 10 min for drift). |
| `drift_threshold` | 6 dB | fijo | sí | declarado | Shift of the median noise floor above which the drift alert is raised; strict comparison (more than 6 dB). |
| `drift_span` | 24 h | fijo | sí | declarado | Time between the two windows that are compared. |
| `drift_window` | 60 min | 10 a 120 min | sí | propuesto | Length of each of the two windows whose median noise floor is compared: 600 scans (60 x 60 / 6), long enough to average out the scan-to-scan variation so that the 6 dB threshold is applied to a steady level, short enough to keep the comparison local in time. |
| `drift_min_sample_share` | 50 % | 25 a 90 % |  | propuesto | Share of the scans of a window that must carry a median noise floor (not null): 50 % of 600 = 300 values. |
| `minute_evaluation_delay` | 10 s | 8 a 30 s |  | derivado | Wait after the end of a one-minute bin before the history alerts read it, so that the last scan of the bin is already in it: the last scan of a bin starts at the end of the bin, can last up to 7 s (scan_late of `health_record`) and the record build (0.15 s) and history update (0.02 s) follow: 7 + 0.17 = 7.17 s. |
| `calibration_withheld_reasons` | not_demonstrated, expired, config_mismatch, invalid | fijo | sí | derivado | The values of withheld_reason (`calibrated_channel_power`, copied into `channel_record`) that name the calibration, as opposed to the signal or the scan (clipped, scan_flagged, no_data, above_range). |
| `alert_event_ring` | 1000 count | 401 a 10000 count |  | propuesto | Alert events kept in memory (raised and cleared), newest first: 2.5 times the largest number of active alerts `max_active_alerts` = 401. |
| `alert_event_size` | 512 bytes | 512 a 1024 bytes |  | propuesto | Largest serialized alert event: the text (at most 256 bytes, `alert_text_max_bytes`) plus about 250 bytes of fields and evidence. |
| `alert_text_max_bytes` | 256 bytes | fijo |  | derivado | Longest alert text, the same limit as every free text of the package. |
| `alert_scan_evaluation_time` | 0.02 s | 0.005 a 0.2 s |  | propuesto | Time given to the per-scan work (health bookkeeping, calibration check, 199 unexpected-occupancy checks, text and publication): about 5,200 operations, microseconds at any sustained rate of one core. |
| `alert_minute_evaluation_time` | 0.2 s | 0.05 a 1.0 s |  | propuesto | Time given to the per-minute work (one bin read for up to 199 channels, the silence state machine, the two drift windows, and in the worst minute 199 prior-duty readings of 1,440 bins each: about 590,000 operations). |
| `alert_channel_state_size` | 48 bytes | fijo |  | derivado | State kept per channel: silence credit 4 B, last active bin end 8 B, run start 8 B, prior duty cycle 4 B, prior status 1 B, unexpected count 2 B, clear count 2 B, flags 1 B, ids of the two active alerts 16 B = 46 B, padded to 48 B. |
| `max_active_alerts` | 401 count | fijo |  | derivado | Most alerts that can be active at once: one silent and one unexpected-occupancy per channel plus the sensor-offline, calibration and drift alerts. |

## Reproducibilidad entre sitios

| Parámetro | Valor | Rango | Crít. | Origen | Significado |
|---|---|---|---|---|---|
| `cross_site_power_points` | 12 count | fijo | sí | derivado | Points at which the calibrated power of the two nodes is compared: the 12 measurements of one verification (6 channels x 2 levels, `verification_channel_count` x `verification_levels_per_channel`), at the same channels and nominal levels at both sites. |
| `coverage_factor` | 2 | fijo | sí | derivado | Coverage factor of the uncertainties that are combined: all the uncertainties of the package are expanded with k = 2 (`reference_source_level_uncertainty_max`, `expanded_uncertainty_default`, `verification_measurement_uncertainty`, `independent_reference_uncertainty_max`), so the root sum of squares of two of them… |
| `agreement_en_max` | 1 | fijo | sí | declarado | A point agrees when the difference between the two sites is within the combination of their reported uncertainties: En = \|D_A - D_B\| / sqrt(W_A^2 + W_B^2) is at most 1 (rule (1) of, approved by the person). |
| `power_agreement_min_points` | 10 count | 9 a 12 count | sí | propuesto | Points of `cross_site_power_points` that must agree. |
| `power_agreement_min_share` | 83.3 % | 75 a 100 % | sí | derivado | The threshold of el criterio de R-51 for the power comparison, in percent: 10 of 12 points. |
| `power_difference_hard_limit` | 6 dB | fijo | sí | derivado | No point may differ between the sites by more than 6 dB whatever the uncertainties: each site is within 3 dB of the true power (R-10), so two correct sites differ by at most 3 + 3 dB. |
| `combined_uncertainty_per_point` | 1.99 dB | fijo |  | derivado | Expanded combined uncertainty of the difference between the two sites at one point when both nodes report the default uncertainty: W = sqrt(1.28^2 + 0.59^2) = 1.409 dB for one site; sqrt(W_A^2 + W_B^2) = 1.993 dB. |
| `occupied_observations_min` | 20 count | fijo | sí | declarado | Ground-truth-occupied observations with SNR of at least 0 dB that each site's acceptance set must hold. |
| `acceptance_channels_min` | 10 count | fijo | sí | declarado | Distinct channels the occupied observations (and, by the same acceptance set, the vacant observations) must come from. |
| `acceptance_channel_share_max` | 20 % | fijo | sí | declarado | No channel may supply more than 20 % of the observations of the denominator, so one strong station cannot decide the result. |
| `vacant_observations_min` | 60 count | 40 a 200 count | sí | propuesto | Ground-truth-vacant observations (vacancy confirmed by an independent reference) that each site's acceptance set must hold: 5 % of 60 is 3, so up to 3 false alarms keep the observed false-alarm share at or below the 5 % of R-05. |
| `repeat_run_duration` | 72 h | 72 a 168 h |  | derivado | Length of the screening run at the repeat site: the same continuous 72 h at a site with a published FM station list that R-61 asks of the first site, so both sites are judged on a run of the same kind. |
| `acceptance_extension_max` | 2 count | 0 a 4 count |  | propuesto | Times the run may be extended when the acceptance set is too small (E-REP-005), each by `acceptance_extension_length`; after that the screening criterion is inconclusive and the comparison fails. |
| `acceptance_extension_length` | 24 h | 12 a 72 h |  | propuesto | Length of one extension of the run: one day, a full daily cycle of the stations. |
| `report_fields_required` | value, uncertainty, limit or recorded absence of one, comparison with the limit | fijo | sí | declarado | The four fields that every output of both reports must carry (rule (3) of): each is in the record of «Registros de escaneo y de salud» as power.value_dbm (or null with its reason), power.uncertainty_db with power.uncertainty_basis, limit.state with limit.limit_dbm, and limit.comparison. |
| `identical_items` | package sha256 and software_version; schema versions of `site_config` to `health_record`; `sample_rate`, `step_count` to `step3_centre_frequency`, `rf_amp_gain` to `clip_sample_count_threshold`, `fft_length` to `integration_bandwidth`, `occupied_threshold_excess` to `adjacency_range_channels` and `detector_time_allocation` values; the steps of `establish_amplitude_calibration` and `verify_amplitude_correction`; the listing of configuration in the calibration record; the independent-reference class (`reference_source_level_uncertainty_max`, `independent_reference_uncertainty_max`) | fijo | sí | propuesto | What must be identical at both sites so that a difference can only come from the site, the unit or the calibration: the package and its configuration schema, the acquisition and estimator settings, the detector thresholds and the two procedures. |
| `point_repeat_max` | 1 count | fijo |  | derivado | A point that is withheld, clipped or missing in one record is measured again once at that site; a second failure makes the comparison inconclusive (E-REP-004). |
| `comparison_record_max_size` | 65536 bytes | 16384 a 262144 bytes |  | derivado | Largest comparison record: 64 KiB, as the validation record (`validation_record_max_size`); the record holds 12 points, two identity blocks and the three results. |

## Supervisión y manejo de errores

| Parámetro | Valor | Rango | Crít. | Origen | Significado |
|---|---|---|---|---|---|
| `progress_tick_interval` | 1 s | 0.5 a 2 s |  | propuesto | Every supervised process raises a progress counter at least once per second from its main loop, busy or idle; a process whose loop is stuck stops raising it even if a helper thread is alive. |
| `hang_timeout` | 10 s | 5 a 30 s |  | propuesto | Time without a change of the progress counter after which a process is declared hung, killed and restarted: ten ticks, longer than the slowest legitimate pause of a main loop (a scan of up to 7 s, `health_record` scan_late). |
| `scan_progress_timeout` | 12 s | 8 a 18 s | sí | derivado | While the node is meant to be measuring, the measure process must publish a scan or a health record every scan period; with none for 12 s it is restarted. |
| `restart_delay_initial` | 5 s | 2 a 30 s |  | propuesto | Wait before the first restart of a process, so that the system can release the device (the SDR USB stream) and the port of the old process. |
| `restart_backoff_factor` | 2 | 1 a 4 dimensionless |  | propuesto | Factor by which the wait grows for each further restart inside the window: 5, 10, 20, 40, 60 s. |
| `restart_delay_max` | 60 s | 30 a 300 s |  | propuesto | Largest wait between restarts: the supervisor never gives up, so a node whose fault clears by itself (a USB cable, a full card) recovers within one minute of that. |
| `restart_limit_count` | 5 count | 3 a 10 count |  | propuesto | Restarts of one process inside the window `restart_limit_window` after which the process is declared in a restart loop: the condition is shown and counted; the restarts go on at `restart_delay_max`. |
| `restart_limit_window` | 600 s | 300 a 1800 s |  | propuesto | Window in which the restarts of a process are counted: 10 minutes, the time five restarts with the waits of `restart_delay_initial` to `restart_delay_max` take (5 + 10 + 20 + 40 + 60 = 135 s) plus their start times. |
| `restart_stable_time` | 600 s | 300 a 1800 s |  | derivado | A process that runs this long after a restart is considered healthy again: its wait goes back to `restart_delay_initial` and the restart-loop condition is cleared. |
| `reboot_after_loop` | 1800 s | 900 a 7200 s |  | propuesto | Time a process stays in a restart loop before the node itself is rebooted: a wedged USB controller or driver is cleared only by a reboot. |
| `reboot_limit_per_day` | 3 count | 1 a 6 count |  | propuesto | Most reboots ordered by the supervisor in 24 h; after that it only keeps restarting processes, so a faulty node cannot reboot all day and lose the history each time. |
| `hw_watchdog_timeout` | 15 s | 10 a 60 s |  | propuesto | The board hardware watchdog resets the node when the supervisor loop has not fed it for 15 s, which catches a frozen kernel or a stopped supervisor. |
| `hw_watchdog_feed_interval` | 5 s | 3 a 7 s |  | derivado | The supervisor loop feeds the hardware watchdog every 5 s, only when the loop itself ran, a third of the timeout. |
| `status_publish_interval` | 1 s | fijo |  | derivado | The supervisor publishes its status (liveness) once per progress tick. |
| `status_stale_after` | 5 s | 3 a 10 s |  | derivado | A consumer treats a supervisor status older than 5 s (five intervals) as 'supervisor not answering'. |
| `ipc_message_max` | 16 MB | 8 a 32 MB |  | derivado | Largest message between processes: the answer of the history process to the web service, at most 40,000 bins x 200 B = 8 MB (`history_bins_response` limit), doubled for margin. |
| `ipc_invalid_consecutive_limit` | 3 count | 2 a 10 count |  | derivado | Consecutive invalid messages from one producer after which that process is restarted: the same count as the flagged-scan limit `consecutive_flagged_scan_limit`. |
| `supervisor_log_retention` | 35 d | 31 a 90 d |  | derivado | Days of supervisor event files kept: the 30-day availability run of el criterio de R-48 plus 5 days to analyse it. |
| `supervisor_log_max_total` | 50 MB | 10 a 200 MB |  | propuesto | Upper bound of all supervisor event files together. |
| `supervisor_log_line_max` | 256 bytes | fijo |  | derivado | Longest event line: the same limit as every free text of the package. |
| `recovery_time_process` | 72 s | 40 a 150 s |  | propuesto | Time from the last complete scan before a process failure to the first complete scan after its restart: detection at most `scan_progress_timeout` = 12 s, restart wait `restart_delay_initial` = 5 s and a start of 55 s (open the SDR, load the configuration, the calibration record and the first scan). |
| `recovery_time_reboot` | 300 s | 120 a 600 s |  | propuesto | Time from the failure to the first complete scan after a reboot (watchdog reset or ordered reboot): hardware reset, boot of the operating system, the start sequence of `start_node`. |
| `fault_downtime_share_max` | 25 % | 10 a 40 % | sí | propuesto | Share of the 5 % unavailability that R-48 allows that is given to faults and their recovery (540 min of 2,160 min), the same share that «Verificación periódica» gives to verification (`verification_downtime_share_max`); the rest covers the calibration (el presupuesto de recursos) and keeps a reserve. |
| `assumed_process_restarts_per_30d` | 120 count | 0 a 600 count |  | propuesto | Planning figure, not a measurement: one restart per process per day for the four processes (4 x 30). |
| `assumed_reboots_per_30d` | 10 count | 0 a 90 count |  | propuesto | Planning figure, not a measurement: one reboot every three days (watchdog resets and ordered reboots). |
| `availability_gap_allowed` | 18 s | fijo | sí | declarado | A gap between complete scan records up to this length does not make the system unavailable: the system is counted available at a time when a complete full-band scan record exists within the preceding three scan periods (R-49), so an outage of D seconds counts D - 18 s. |
| `ipc_transport` | local Unix stream socket, one message = 4-byte big-endian length + UTF-8 JSON object of a schema | fijo |  | propuesto | The messages between the processes are the JSON schemas of the package over local stream sockets with a length prefix, so a reader always knows where a message ends and never reads a part of one. |
| `ipc_send_queue` | 10 count | 2 a 30 count | sí | derivado | Scan messages the measure process keeps for a consumer that is not reachable (10 scans = 60 s): it never blocks (R-57), reconnects every second, sends the queue when the consumer is back and drops the oldest message when the queue is full. |

## Servicio web

| Parámetro | Valor | Rango | Crít. | Origen | Significado |
|---|---|---|---|---|---|
| `web_port` | 8080 | 1024 a 65535 dimensionless |  | propuesto | TCP port of the web service on every network interface of the node: an unprivileged port, so the service runs without administrator rights, and a port people recognise for a web page. |
| `web_allowed_methods` | GET, HEAD | fijo | sí | declarado | The service offers read-only views and report download only: no method that changes anything is accepted. |
| `access_control_mechanisms` | 0 count | fijo | sí | declarado | Number of logins, roles, tokens, address filters or other means that restrict who may use the web view or the saved reports: none. |
| `web_concurrent_workers` | 8 count | 2 a 16 count |  | propuesto | Requests processed at the same time. |
| `web_request_queue_length` | 64 count | 8 a 256 count | sí | propuesto | Requests that may wait for a worker. |
| `web_queue_wait_limit` | 30 s | 5 a 60 s |  | propuesto | Longest wait of a queued request before E-WEB-005. |
| `web_request_max_bytes` | 8192 bytes | 2048 a 16384 bytes |  | propuesto | Largest request line plus headers accepted; a request has no body. |
| `stations_selected_max` | 10 count | 1 a 20 count |  | propuesto | Most stations a person can select in the 24 h power and duty-cycle view (R-43 says 'selected stations' without a number): ten keeps the answer at 10 x 288 = 2,880 bins and the chart readable. |
| `power_map_span_options` | 1, 6, 24 h | fijo |  | propuesto | Spans the person can choose for the view of channel power by frequency and time; the default is the 24 h of `view_span_default`. |
| `power_map_resolution_options` | 60, 300, 600 s | fijo |  | derivado | Bin length for the spans of `power_map_span_options` in the same order. |
| `stations_view_resolution` | 300 s | 60 a 600 s |  | propuesto | Bin length of the 24 h power and duty-cycle view of selected stations: 288 bins per station, 2,880 for the maximum of 10 stations, a multiple of `bin_length`. |
| `live_refresh_interval` | 6 s | fijo |  | derivado | The page asks again for the spectrum, the node status and the alerts once per scan, since nothing newer exists in between; a raised alert is on the screen at most one interval after the engine publishes it. |
| `history_refresh_interval` | 60 s | fijo |  | derivado | The page asks again for the power map and the station view once per minute: the history changes once per one-minute bin. |
| `cache_ttl_live` | 5 s | 1 a 6 s |  | propuesto | A live answer built for one client is reused for others for 5 s, below the scan period of 6 s, so every scan is shown and several clients cost one answer. |
| `cache_ttl_history` | 60 s | fijo |  | derivado | A history answer is reused for 60 s: the same query cannot return anything new inside one bin. |
| `spectrum_join_frequencies` | 94.0, 101.5 MHz | fijo |  | derivado | Frequencies at which the spectrum drawn passes from one step to the next: the middle of each overlap, so each part of the band is drawn from the step whose usable band is nearer. |
| `power_scale_range` | -130 to -5 dBm | fijo |  | derivado | Fixed colour and axis scale of the power views: the bounds a power value or limit may take in the configuration (`declared_min_power_floor`, `declared_min_power_ceiling`), so the colours mean the same on every day and on every node (R-51). |
| `response_time_limit` | 2 s | 0.5 a 10 s |  | propuesto | Longest time to build and send one answer, counted from the moment a worker takes the request. |
| `web_memory_cap` | 256 MB | 128 a 512 MB |  | propuesto | Upper bound of the web process memory: 1.3 times the 197 MB of el presupuesto de recursos, 3.2 % of the 8 GB, so a fault in the service cannot take the memory of the acquisition. |
| `web_cpu_cap_one_core` | 100 % | 50 a 200 % | sí | propuesto | The web process may use at most one of the four cores of the board (100 % of one core). |
| `web_scheduling_priority` | 10 | 5 a 19 dimensionless | sí | propuesto | Scheduling niceness of the web process (a higher number gets the processor later): 10 puts it behind the acquisition, the estimator and the detector. |
| `download_streams_max` | 2 count | 1 a 4 count |  | propuesto | Report downloads sent at the same time. |
| `download_rate_limit` | 20 MB/s | 5 a 50 MB/s |  | propuesto | Total rate of all report downloads: a segment of 24.96 MB takes 1.25 s and the card keeps capacity for the write of 41.6 KB per scan. |
| `static_assets_max_size` | 2 MB | 0.5 a 4 MB |  | propuesto | Largest total of the page, script and style files the service sends, all stored on the node: 2 MB. |
| `external_requests` | 0 count | fijo |  | propuesto | Requests a page makes to any address other than the node: none. |
| `alert_bar_max_inline` | 5 count | 1 a 20 count |  | propuesto | Active alerts written out in the bar at the top of every page; the rest are counted with a link to the alert page. |
| `retry_after` | 10 s | 5 a 60 s |  | propuesto | Value of the Retry-After header of a 503 answer: the page asks again after 10 s, which is long enough for the queue to drain. |

## Presupuesto de recursos

| Parámetro | Valor | Rango | Crít. | Origen | Significado |
|---|---|---|---|---|---|
| `ambient_design` | 40 degC | fijo | sí | declarado | Highest ambient temperature at which the node must meet all its requirements. |
| `board_operating_limit` | 70 degC | fijo | sí | declarado | Upper operating temperature of the board as the product brief states it; the brief does not say whether it is ambient or board temperature, so it is applied to the air around the board, the stricter reading. |
| `thermal_headroom` | 10 degC | 5 a 15 degC |  | propuesto | Planning headroom below the cited limit (the default of the package rules, shown to the person). |
| `internal_air_limit` | 60 degC | 55 a 65 degC | sí | derivado | Highest air temperature inside the enclosure at 40 degC ambient: the board limit less the headroom. |
| `internal_rise_allowed` | 20 degC | 15 a 25 degC | sí | derivado | Rise of the internal air over the ambient that the enclosure may allow. |
| `heat_inside_upper_bound` | 25 W | fijo | sí | derivado | The most heat that the board, the SDR and the fan can release inside the enclosure: everything they draw comes through the 5 V / 5 A output of the supply (the supply and its loss are outside the box, option O1). |
| `conductance_required_min` | 1.25 W/K | fijo | sí | derivado | Least heat conductance from the inside air to the ambient that keeps the rise within the allowance at the upper bound of the dissipation. |
| `enclosure_conductance_estimate` | 4.8 W/K | 1.25 a 8 W/K | sí | propuesto | Estimate, not a datasheet value (none is given): outer surface of the 300 x 400 x 210 mm box = 2 x (0.3 x 0.4 + 0.3 x 0.21 + 0.4 x 0.21) = 0.534 m2, times a combined convection and radiation coefficient of 9 W/(m2 K) assumed for still outdoor-indoor air = 4.8 W/K. |
| `soc_throttle_threshold` | 80 degC | fijo | sí | declarado | Temperature at which the processor begins to throttle, as the vendor article reports for the Active Cooler (open-air test, ambient not given). |
| `thermal_warning_threshold` | 70 degC | 65 a 75 degC |  | propuesto | Processor temperature, read from the operating system, at which the node flags a thermal condition: the operating limit of the board, 10 degC before the throttle threshold. |
| `thermal_warning_clear` | 65 degC | 60 a 70 degC |  | propuesto | Temperature below which the thermal condition is cleared: 5 degC of hysteresis, so a value near the threshold does not flap. |
| `thermal_read_interval` | 10 s | 5 a 60 s |  | propuesto | How often the supervisor reads the processor temperature: the temperature changes over minutes, so 10 s is far finer than needed and costs one file read. |
| `supply_output_power` | 25 W | fijo | sí | declarado | Output of the 5 V profile of the supply: 5.0 V at 5.0 A. |
| `supply_max_load` | 65 W | fijo |  | declarado | Maximum load of the 5 A version of the supply, rated for operating temperatures of 0 to 40 degC with natural convection; the node loads it to at most 20 W, 31 % of the rating, at the 40 degC of R-66. |
| `node_power_ceiling` | 20 W | 15 a 25 W | sí | derivado | Most power the board, the SDR and the fan may draw together: 80 % of the supply output (a margin of 20 %, as for the other resources). |
| `os_memory_reserve` | 1000 MB | 600 a 2000 MB |  | propuesto | Memory left to the operating system, its page cache and its services (the figure of the provisional budget el presupuesto de recursos). |
| `unit_runtime_base` | 50 MB | 20 a 100 MB |  | propuesto | Memory of the language runtime and libraries of each of the measure, store_alert and report units (the same assumption as the web process, el presupuesto de recursos). |
| `measure_memory_cap` | 256 MB | 128 a 512 MB | sí | propuesto | Memory limit of the measure unit: 2.4 times its demand of 108.2 MB, so a leak stops this unit and not the node. |
| `store_alert_memory_cap` | 768 MB | 400 a 1024 MB | sí | propuesto | Memory limit of the store_alert unit: the history takes up to its own cap `history_memory_cap` = 512 MB, the alert engine 0.53 MB and the runtime 50 MB: 563 MB, with 205 MB of margin. |
| `report_memory_cap` | 128 MB | 64 a 256 MB |  | propuesto | Memory limit of the report unit: 2.5 times its demand of 52.1 MB (the queue of 10 scans, 2.1 MB, and the runtime). |
| `supervisor_memory_cap` | 64 MB | 32 a 128 MB |  | propuesto | Memory limit of the supervisor unit and its message buffers: 2.1 times the 30.2 MB of el presupuesto de recursos. |
| `time_memory_cap` | 32 MB | 16 a 64 MB |  | propuesto | Memory limit of the time service (a standard NTP client, about 10 MB assumed). |
| `tmpfs_size` | 64 MB | 16 a 256 MB | sí | propuesto | Size of the memory-backed file system that holds every temporary file of the units, so no temporary file goes to the card (R-31); the logs there hold counts and codes only. |
| `cpu_utilization_limit` | 70 % | 50 a 80 % | sí | derivado | Highest sustained processor use of the whole node over its four cores: 100 % less the planning margin of 30 % for sustained compute. |
| `measure_cpu_quota` | 300 % | 200 a 400 % | sí | propuesto | Processor time the measure unit may take: three of the four cores; the web unit keeps at most one (`web_cpu_cap_one_core`) and the rest share what is left. |
| `store_alert_cpu_quota` | 100 % | 50 a 200 % |  | propuesto | Processor time of the store_alert unit: one core; its demand is below 0.01 core. |
| `report_cpu_quota` | 50 % | 25 a 100 % |  | propuesto | Processor time of the report unit: half a core; writing 41.6 KB per scan takes microseconds. |
| `supervisor_cpu_quota` | 25 % | 10 a 50 % |  | propuesto | Processor time of the supervisor: a quarter of a core; its demand is 0.25 Mop/s. |
| `assumed_cycles_per_operation` | 4 count | 1 a 16 count |  | propuesto | Planning assumption used only for the estimate of the load, not for a limit: the processor cycles one operation of the budget costs, with unvectorised code and memory waits. |
| `unit_scheduling_priorities` | measure 0, supervisor 0, time 0, store_alert 5, report 5, web 10 (`web_scheduling_priority`) | fijo | sí | propuesto | Niceness of each unit (a higher number gets the processor later): acquisition first, the supervisor and the time service on the same level so they are never starved, then the stores, then the web service. |
| `operating_system_requirements` | 64-bit Arm Linux with a service manager (systemd), control groups for memory and processor limits and niceness, a memory-backed temporary file system, an NTP client, the board hardware watchdog driver, and no swap; the board vendor's 64-bit Raspberry Pi OS Lite (Debian based) is the reference candidate | fijo | sí | propuesto | The software of the package relies on these system functions: unit restart, caps and priorities (`apply_resource_limits`), temporary files in memory (R-31), network time («Servicio de hora») and the hardware watchdog («Supervisión y manejo de errores»). |

## Presupuesto de tiempo

| Parámetro | Valor | Rango | Crít. | Origen | Significado |
|---|---|---|---|---|---|
| `chain_time_sum` | 4.9835 s | fijo | sí | derivado | Sequential worst-case sum of the processing stages of one scan, taken from the allocations of the modules: captures 1.8335 s (el presupuesto de recursos), estimator 2.5 s (`estimator_time_allocation`), detector 0.2 s (`detector_time_allocation`), comparator 0.01 s (`comparison_time_allocation`), record builder 0.15… |
| `chain_slack` | 1.0165 s | fijo | sí | derivado | Time left in one scan period after the sequential sum of the stages: the period less the sum. |
| `chain_share_of_period` | 83.1 % | fijo |  | derivado | Share of the scan period used by the sequential sum of the stages. |
| `estimator_backlog_max` | 0.3221 s | fijo | sí | derivado | Largest lag between the estimator and the incoming stream at the end of one capture: the estimator takes a third of its allocation per capture (2.5 / 3 = 0.8333 s) while one dwell lasts 0.5112 s, so 0.3221 s of frames wait in the ring buffer; the backlog is worked off before the next capture (the period leaves 4 s… |
| `backlog_share_of_ring` | 38.4 % | fijo | sí | derivado | Share of the ring buffer time (64 frames = 0.839 s, `ring_buffer_frames`) that the largest estimator backlog uses: 24.6 of the 64 frames. |
| `health_gap_max_normal` | 7 s | 6 a 7 s | sí | derivado | Longest gap between two consecutive health records while the node works normally: scans start every 6 s and a scan that lasts more than 7 s is flagged late (`scan_late_threshold`), so the health record of a scan appears within 7 s of its start and the gap stays at 7 s. |
| `offline_alert_latency_max` | 19 s | fijo | sí | derivado | Longest time from the last health point to the sensor-offline alert: the timeout plus one check interval. |
| `alert_on_screen_latency_max` | 25.1 s | fijo |  | derivado | Longest time from the condition of a sensor-offline alert to its presence on the screen: the alert latency, one refresh of the page and one answer. |
| `interval_limit` | 10 s | fijo | sí | declarado | Longest interval between consecutive full-band scan start timestamps over a run. |
| `interval_planned_max` | 7 s | 6 a 7 s | sí | derivado | Longest interval between scan starts that the design allows without a flag: the scan period of 6 s plus 1 s of lateness, the point at which a scan is flagged late (`scan_late_threshold`). |

## Fiabilidad y disponibilidad

| Parámetro | Valor | Rango | Crít. | Origen | Significado |
|---|---|---|---|---|---|
| `availability_allowance_30d` | 2160 min | fijo | sí | derivado | Unavailable time that R-48 allows in a continuous 30-day run: 5 % of 30 days. |
| `availability_threshold` | 95 % | fijo | sí | declarado | Least share of time counted as available over the run, by the definition of R-49. |
| `allocation_verification` | 540 min | fijo |  | derivado | Share of the allowance given to the periodic verification of the amplitude correction («Verificación periódica»): 25 % of 2,160 min; its worst case at the shortest interval is 312 min (el presupuesto de recursos). |
| `allocation_faults` | 540 min | 216 a 864 min |  | derivado | Share of the allowance given to faults and their recovery («Supervisión y manejo de errores»): 25 % of 2,160 min; the planned faults use 155 min (el presupuesto de recursos). |
| `allocation_calibration` | 118 min | fijo |  | derivado | Time of one establishment of the amplitude calibration («Calibración de amplitud»), counted once in the run in the worst case that it falls inside it. |
| `allocation_reserve` | 962 min | fijo |  | derivado | What is left of the allowance after the three allocations: kept as a reserve for events no module plans (a second calibration, an operator stop). |
| `planned_unavailability` | 585 min | fijo | sí | derivado | Planned counted unavailability over 30 days: verification at the shortest interval 312 min (el presupuesto de recursos), calibration 118 min (el presupuesto de recursos), faults 155 min (el presupuesto de recursos). |
| `planned_availability` | 98.6 % | fijo | sí | derivado | Availability the plan gives over 30 days: 1 minus the planned unavailability over 43,200 min. |
| `analysis_grid` | 6 s | fijo |  | derivado | Spacing of the time points at which availability is judged in the analysis of el criterio de R-49: one per scan period. |
| `analysis_points_30d` | 432000 count | fijo |  | derivado | Time points of a 30-day window on the grid of `analysis_grid`. |
| `unavailable_points_max` | 21600 count | fijo | sí | derivado | Most time points that may be counted unavailable in the window while the share stays at 95 %: 5 % of 432,000. |
| `field_run_min_duration` | 72 h | fijo | sí | declarado | Least duration of the continuous field run. |
| `field_run_planned_duration` | 76 h | 72 a 120 h |  | propuesto | Planned length of the field run: the 72 h of R-61 plus 4 h of reserve, so that the recovery of one process restart (72 s) or one reboot (300 s) and the set-up of the independent reference do not bring the counted continuous time below 72 h. |
| `field_run_gap_allowed` | 300 s | fijo | sí | derivado | Longest gap between two report runs (a run is closed as interrupted after a stop, E-RPT-005, and a new one starts) for the field run still to count as continuous: the recovery time of a reboot. |
| `reference_logging_min` | 6 h | fijo | sí | declarado | Least duration of the independent reference logging inside the field run; it also gives the ground truth for the acceptance sets of «Reproducibilidad entre sitios». |
| `site_noise_reliable_share_min` | 95 % | 80 a 99 % |  | propuesto | el criterio de R-61 asks for a site with at least the minimum vacant channels per capture; no input gives that number, and the detector needs vacant channels for its noise reference. |
| `power_cut_scans_at_risk` | 1 count | fijo | sí | derivado | Scans that a power cut can cost: only the scan being written, because the report is flushed after every scan (`flush_every_scans`); all scans completed before are in the file. |
| `power_cut_exposure` | 0.83 % | fijo |  | derivado | Share of the time in which a cut falls inside the write of a scan: the write allocation over the scan period. |
| `view_refill_time` | 24 h | fijo |  | derivado | Time after a restart of the store_alert unit before the 24 h views are complete again: the history starts empty and the views show from history_start_utc_us. |
| `drift_refill_time` | 25 h | fijo |  | derivado | Time after a restart of the store_alert unit before the noise-floor drift alert can be evaluated again: the two windows of 60 min 24 h apart. |
