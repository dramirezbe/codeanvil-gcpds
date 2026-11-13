# Anexo C — Procedimientos y algoritmos paso a paso

Cada procedimiento es una secuencia ordenada que el software (o la persona que opera el nodo) debe ejecutar. Los pasos citan los parámetros del Anexo A por su nombre.

> Los nombres de parámetros, campos, estados y códigos de error se conservan en inglés porque son los identificadores que se implementan en el código y en los archivos. Las descripciones breves de estos anexos mantienen el texto técnico original.

## `load_and_validate_site_config` — Configuración del sitio

- **Para qué:** read site-config.json and the station reference, check every field, publish the active configuration and its status
- **Quién lo ejecuta:** software
- **Cuándo:** service start; reload request; retry every `config_retry_interval` while the file is missing
- **Condiciones previas:** Industrial microSD SDCIT2/64GBSP storage readable; time status `time_status` available
- **Duración:** 1 s
- **Resultado:** `site_config`, `config_status`
- **Salidas por fallo:** `E-CFG-001`, `E-CFG-002`, `E-CFG-003`, `E-CFG-004`
- **Criterio de éxito:** all checks of steps 1 to 5 pass; otherwise the previous valid configuration stays active
- **Reproducibilidad:** n/a: not site-dependent

**Pasos**

1. check that the file exists and read its size — _esperado:_ file exists and size <= 1048576 bytes, else `E-CFG-001` or `E-CFG-004`
2. parse the file as JSON object — _esperado:_ valid JSON, else `E-CFG-002`
3. check schema_version major equals 1 and every required field of `site_config` is present — _esperado:_ all required fields present, else `E-CFG-002`
4. check each field range of `site_config` (location text <= 256 bytes, record_time_min >= 10 and <= 43200, mapping_error_limit_khz >= 1 and <= 20, declared power between -130 and -5 dBm, silent hours between 0.1 and 720, time sources between 1 and 4); the optional received power limit between -130 and -5 dBm — _esperado:_ every field inside its range, else `E-CFG-002`
5. if station_reference_file is present, read and check it against `station_assignment_reference`: channels unique, 1 to 199, at most 199 entries — _esperado:_ reference valid, else `E-CFG-003` (the reference alone is rejected)
6. compute sha256 of the configuration file and fill `config_status` — _esperado:_ config_sha256 filled
7. publish the new configuration as active and keep the previous valid one — _esperado:_ config_state valid

## `add_and_configure_another_node` — Configuración del sitio

- **Para qué:** show that another node is added and configured by data only (R-52, el criterio de R-52)
- **Quién lo ejecuta:** operator
- **Cuándo:** when another node is installed
- **Condiciones previas:** the same software package (same version and hash) installed on the new board; HackRF One to 36650 USB 2.0 Type A to Micro-B cable of the same references
- **Duración:** 30 min
- **Resultado:** `config_status`
- **Salidas por fallo:** `E-CFG-002`, `E-CFG-003`
- **Criterio de éxito:** config_state valid and installed files unchanged (0 lines rewritten, el criterio de R-52)
- **Reproducibilidad:** the same package hash and the same configuration schema on every node; compared by the package hash

**Pasos**

1. install the software package and compare the hash of the installed files with the package hash — _esperado:_ hashes equal
2. copy site-config.json from the package template and edit node_id, location, run_mode, time_sources and, if available, the declared minimum power and the silent hours — _esperado:_ file saved, no source file modified
3. provide the station-assignment reference file for the site and name it in station_reference_file — _esperado:_ file saved
4. start the service and read config_status — _esperado:_ config_state valid and station_reference_state valid
5. compare the hash of the installed files with the package hash again — _esperado:_ hashes equal: 0 lines of code rewritten

## `scan_cycle` — Adquisición y barrido

- **Para qué:** run one full-band scan of three stepped captures and publish the capture blocks and counters
- **Quién lo ejecuta:** software
- **Cuándo:** every `scan_period` (6 s) measured on the monotonic clock; the next scan starts at once when the previous one overran
- **Condiciones previas:** SDR opened, gains applied (`rf_amp_gain`, `lna_gain`, `baseband_gain`), site configuration valid or defaults, time status `time_status` available
- **Duración:** 1.8335 s
- **Resultado:** `capture_block`, `acquisition_counters`
- **Salidas por fallo:** `E-ACQ-001`, `E-ACQ-002`, `E-ACQ-003`, `E-ACQ-004`, `E-ACQ-005`
- **Criterio de éxito:** scan interval between starts at most `scan_period` + lateness, never above 10 s (el criterio de R-01)
- **Reproducibilidad:** the same `sample_rate`, `step1_centre_frequency` to `step3_centre_frequency` and `rf_amp_gain` to `baseband_gain` on every node; compared by the configuration listing of the calibration record («Calibración de amplitud»)

**Pasos**

1. read `time_status` once and keep utc_us and sync_state as scan_start — _esperado:_ scan start stamped
2. apply the fixed gains and confirm AGC is off — _esperado:_ agc_enabled false, gains recorded
3. for step s of 1 to 3: set the centre frequency (`step1_centre_frequency`, `step2_centre_frequency`, `step3_centre_frequency`) and wait `retune_settle`; retry up to `retune_retry_max` times at `retune_retry_interval` if the command fails — _esperado:_ tuned, or retune_failed true after the last retry
4. receive `frames_per_dwell` frames of `frame_samples` samples into the ring buffer of `ring_buffer_frames` frames, counting overflow events and frames received — _esperado:_ 39 frames received
5. count samples at full scale (-128 or +127) over the whole block and set clipped when the count reaches `clip_sample_count_threshold` — _esperado:_ clip_count and clipped set
6. set dropped_frames = `frames_per_dwell` - frames received and publish the block as `capture_block` to el estimador espectral — _esperado:_ block published
7. after step 3 publish `acquisition_counters` with the counts and scan_late when the scan lasted more than `scan_late_threshold` — _esperado:_ counters published

## `estimate_channel_power` — Estimador espectral

- **Para qué:** turn the three capture blocks of a scan into the integrated power of each of the 199 channels and a decimated spectrum
- **Quién lo ejecuta:** software
- **Cuándo:** each scan, when the three blocks of `capture_block` and the counters `acquisition_counters` of the scan are available
- **Condiciones previas:** `estimator_control` present (zero correction when absent); blocks not flagged no_data
- **Duración:** 2.5 s
- **Resultado:** `channel_power_scan`, `spectrum_snapshot`
- **Salidas por fallo:** `E-EST-001`, `E-EST-002`, `E-EST-003`, `E-EST-004`
- **Criterio de éxito:** none: a pure computation; results checked by the vector tests of the test spec
- **Reproducibilidad:** n/a: not site-dependent

**Pasos**

1. for each block check retune_failed and frames; an empty or retune-failed block sets no_data for its channels and ends the steps for that block — _esperado:_ no_data set or processing continues
2. convert each sample to complex float x = (I + jQ) / 128 and subtract the mean of the capture from I and from Q — _esperado:_ zero-mean complex samples
3. for segment m = 0 to 2494 take 4096 samples starting at m x 2048, multiply by the Hann window w[n] = 0.5 (1 - cos(2 pi n / 4096)), compute the 4096-point transform X[k] and the power P[k] = |X[k]|^2 / (4096 x sum(w^2)) with sum(w^2) = 1536 — _esperado:_ 2495 power spectra
4. average the 2495 spectra bin by bin — _esperado:_ one averaged power spectrum per step
5. replace the bins at offsets -3 to +3 from DC by the mean of the bins at offsets 4 to 6 and -6 to -4 — _esperado:_ DC spike suppressed
6. compute the true LO frequency f_true = f_nominal x (1 + c x 1e-6) with c from `estimator_control`; for each channel of the step find b = round((f_channel - f_true) / 2441.40625) and sum the averaged power over bins b-52 to b+52 — _esperado:_ linear channel power with 105 bins
7. convert to dBFS: power_dbfs = 10 log10(sum); set null when the sum is 0 or not finite — _esperado:_ power_dbfs or invalid (`E-EST-002`)
8. set dc_adjacent for channels whose window contains a replaced bin and compute mapping_error_bound = `mapping_rounding_error` + `frequency_estimate_error_bound` + `frequency_reference_tolerance_100mhz` x f / 100 MHz, compare with the limit of «Configuración del sitio» — _esperado:_ flags set
9. average groups of 4 bins of the usable band into 819 points per step and publish `channel_power_scan` and `spectrum_snapshot` to el gestor de calibración — _esperado:_ `channel_power_scan` and `spectrum_snapshot` published

## `establish_amplitude_calibration` — Calibración de amplitud

- **Para qué:** establish the amplitude correction from a traceable reference source at the reference plane, characterize the dynamic range, measure the crystal frequency error and write the calibration record
- **Quién lo ejecuta:** operator
- **Cuándo:** before the first measurement run, after any change of the measurement configuration (`sample_rate`, `step1_centre_frequency` to `step3_centre_frequency`, `rf_amp_gain` to `baseband_gain`, `fft_length` to `integration_bins`), after a hardware or software replacement, and when a verification fails
- **Condiciones previas:** node in its deployed configuration and enclosure; HackRF One to 36650 USB 2.0 Type A to Micro-B cable; the antenna cable disconnected at the SDR antenna port; external, not part of the node cost (R-53): a CW signal source for 88 to 108 MHz with a traceable level (expanded uncertainty at most `reference_source_level_uncertainty_max` and frequency uncertainty at most `reference_source_frequency_uncertainty_max`), a 50 ohm termination, a cable with measured loss; the reference source is different from the verification reference of «Verificación periódica» (R-20)
- **Duración:** 118 min
- **Resultado:** `calibration_record`, `estimator_control`
- **Salidas por fallo:** `E-CAL-003`, `E-CAL-004`, `E-CAL-005`
- **Criterio de éxito:** all five criteria of step 9 hold
- **Reproducibilidad:** the same procedure, step order and parameter set at every site; what is compared is the offsets table, the dynamic range and the frequency correction («Reproducibilidad entre sitios»)

**Pasos**

1. run the node for `warmup_time` with the antenna port terminated by the 50 ohm termination — _esperado:_ warm node, scans running
2. record the device identifiers, the software version, the configuration listing and its sha256, and the certificate data of the reference source (name, model, serial, calibration date, certificate id, traceability body, uncertainties); refuse to continue if any item is missing — _esperado:_ identity block complete (else `E-CAL-004`)
3. with the termination still connected record `noise_floor_scans` scans and store the mean power of each of the 199 channels in dBFS as the noise floor — _esperado:_ noise floor per channel
4. measure the loss of the cable and adapters at the calibration frequencies and write it with its uncertainty — _esperado:_ loss and uncertainty at most `cable_loss_uncertainty_max`
5. dynamic-range sweep at channel 100 (98.0 MHz, step 2): connect the source through the cable and set levels at the plane from `sweep_level_min` to `sweep_level_max` in steps of `sweep_step`; at each level wait `point_settle_time` and take `repeats_per_point` scans; stop at the first clipped scan — _esperado:_ sweep table: measured power in dBFS against level
6. from the sweep: fit the straight line (slope 1 dB per dB) to the levels inside the lower and middle part, mark the first level whose measured power is below the line by `compression_criterion` as the compression level and the first clipped level as the clip level; range_high = the lower of the two minus `range_high_headroom` (or `sweep_level_max` if neither is reached); range_low = the lowest level at least `range_low_snr` above the noise floor of the channel; reject if the deviation from the line inside the range exceeds `linearity_deviation_max` — _esperado:_ range_low, range_high, compression and clip levels
7. choose the reference level L_ref = range_high - `reference_level_below_range_high`, limited to `reference_level_min` and `reference_level_max` — _esperado:_ L_ref between -70 and -30 dBm
8. offsets: for each of the `calibration_point_count` = 24 calibration channels set the source to the channel centre at L_ref at the plane, wait `point_settle_time`, take `repeats_per_point` scans, take the median power of the channel in dBFS, compute K = L_ref - median and the spread; measure the tone frequency by the interpolation of «Estimador espectral» and compute the ppm error — _esperado:_ 24 offsets with spreads and 24 frequency errors
9. acceptance: all must hold: (a) spread at each point <= `repeatability_max`; (b) leave-one-out interpolation residual of the interior points <= `interpolation_residual_max`; (c) reference tone at least `snr_at_reference_min` above the noise floor of its channel; (d) median frequency error c within `frequency_correction_limit`; (e) total expanded uncertainty by the budget (`expanded_uncertainty_default`) <= `total_uncertainty_limit` — _esperado:_ pass or the list of failed criteria (`E-CAL-003`)
10. declare the verification interval and the expiry margin within the bounds of «Verificación periódica», write the record `calibration_record` with state valid and its sha256, activate it and send `estimator_control` with c and the frequency-reference state — _esperado:_ record file and checksum written, calibration active

## `apply_calibration_to_scan` — Calibración de amplitud

- **Para qué:** turn the channel powers in dBFS of a scan into calibrated powers in dBm with their uncertainty, and withhold them when the correction cannot be demonstrated
- **Quién lo ejecuta:** software
- **Cuándo:** each scan, when `channel_power_scan` and `spectrum_snapshot` of the scan are available
- **Condiciones previas:** active calibration record loaded or none
- **Duración:** 0.05 s
- **Resultado:** `calibrated_channel_power`, `calibrated_spectrum`
- **Salidas por fallo:** `E-CAL-001`, `E-CAL-002`, `E-CAL-006`
- **Criterio de éxito:** none: a pure computation; checked by the test spec
- **Reproducibilidad:** n/a: not site-dependent

**Pasos**

1. compare the sha256 of the current measurement configuration with that of the active record; on a difference do not start scans (the check is also made at each scan start) — _esperado:_ equal, else `E-CAL-001`
2. evaluate the validity state: valid before verified_until minus the expiry margin, expiring up to verified_until, expired after it; invalid after a failed verification; none without a record; when the node time is not synced after a restart the state is expired — _esperado:_ state set (expired, invalid and none: `E-CAL-002`)
3. for each channel compute K by linear interpolation of the offsets of its step against frequency (values held at the ends of the step) and power_dbm = power_dbfs + K — _esperado:_ calibrated power
4. set uncertainty_db to `expanded_uncertainty_default`, or `expanded_uncertainty_dc_adjacent` for dc_adjacent channels, and the basis text with the certificate id — _esperado:_ uncertainty and basis
5. withhold power_dbm (null) with its reason when the state is expired, invalid or none, the capture is clipped, the scan is flagged, there is no data, the power value is above range_high or invalid; set near_noise_floor when below range_low — _esperado:_ released or withheld with reason (`E-CAL-002`, `E-CAL-006`)
6. apply the same offsets to the points of the spectrum and publish `calibrated_channel_power` and `calibrated_spectrum` with the noise floor of each channel converted to dBm — _esperado:_ `calibrated_channel_power` and `calibrated_spectrum` published

## `classify_channels` — Detector de ocupación

- **Para qué:** release Occupied, Free or Uncertain for each channel of a scan with the inputs and flags that justify it
- **Quién lo ejecuta:** software
- **Cuándo:** each scan, when `calibrated_channel_power`, `calibrated_spectrum` and `acquisition_counters` of the scan are available
- **Condiciones previas:** `site_config` active (declared minimum power may be absent)
- **Duración:** 0.2 s
- **Resultado:** `occupancy_scan`
- **Salidas por fallo:** `E-DET-001`, `E-DET-002`, `E-DET-003`
- **Criterio de éxito:** none: a pure computation; checked by the vector tests of the test spec
- **Reproducibilidad:** n/a: not site-dependent

**Pasos**

1. check that `calibrated_channel_power` holds 199 channels; if not mark every channel Uncertain with reason uncertain_input_invalid (`E-DET-003`) — _esperado:_ 199 channels or `E-DET-003`
2. for each step take the points of `calibrated_spectrum` within `noise_points_half_width` of the step centre excluding `noise_dc_exclusion_points` points each side of the LO, take the lowest `noise_quantile_fraction` fraction by power, average their linear power, convert to a 256.347 kHz window (+14.19 dB) and keep the median of the last `noise_smoothing_scans` estimates — _esperado:_ noise reference of the step in dBm
3. check the reference against the stored receiver floor of the step: reliable when it lies between -`noise_below_calibration_limit` and +`noise_above_calibration_limit` dB of the median stored floor; otherwise mark the step unreliable (`E-DET-001`) — _esperado:_ reliable or unreliable
4. for each channel noise_k = step reference + (stored floor of the channel - median stored floor of its step); excess_k = power_dbm - noise_k; threshold_k = noise_k + `occupied_threshold_excess` — _esperado:_ noise, excess and threshold
5. if the calibration state is not valid or expiring, the scan is flagged, the capture clipped, the power withheld, no data, or the step unreliable: state Uncertain with the matching reason, validity not_valid, and go to step 9 — _esperado:_ Uncertain with reason, or continue
6. if excess_k >= `occupied_threshold_excess`, or the previous state was Occupied and excess_k >= `occupied_threshold_excess` - `hysteresis` (hysteresis): if no channel within `adjacency_range_channels` has excess >= `occupied_threshold_excess` the state is Occupied (occupied_isolated); otherwise compute own_carrier_ratio from the points of `calibrated_spectrum` around the channel (inner `inner_half_points` points each side, flanks `flank_first_offset` to `flank_last_offset` points) and the state is Occupied when it is >= `own_carrier_ratio_min` (occupied_own_carrier) and Uncertain (uncertain_adjacent_leakage) otherwise; Occupied must hold for `minimum_occupancy_scans` scans — _esperado:_ Occupied or Uncertain adjacent
7. otherwise, if excess_k <= `free_threshold_excess` test the Free release: the declared minimum power D_k from `site_config` must be configured (else Uncertain, uncertain_not_configured), D_k - noise_k must be >= `release_margin` (else uncertain_margin_below_10db) and threshold_k <= D_k; when all hold the state is Free (free_released) — _esperado:_ Free or Uncertain with reason
8. otherwise (`free_threshold_excess` < excess_k < `occupied_threshold_excess`) the state is Uncertain (uncertain_between_thresholds) — _esperado:_ Uncertain
9. fill power_dbm, excess_db, noise_dbm, threshold_dbm, declared minimum power, release margin, threshold_not_above_declared and own_carrier_ratio of each channel, set the median noise floor, publish `occupancy_scan`, and update the counters of `accumulate_duty_cycle` — _esperado:_ `occupancy_scan` published

## `accumulate_duty_cycle` — Detector de ocupación

- **Para qué:** count the states of each channel over the declared reporting interval and publish duty cycle and Uncertain fraction when the interval closes
- **Quién lo ejecuta:** software
- **Cuándo:** each scan result, and at each interval boundary aligned to UTC (a multiple of interval_min from 1970-01-01T00:00:00Z)
- **Condiciones previas:** `occupancy_scan` of the scan
- **Duración:** 0.01 s
- **Resultado:** `duty_cycle_report`
- **Salidas por fallo:** `E-DET-004`
- **Criterio de éxito:** none: a pure computation
- **Reproducibilidad:** n/a: not site-dependent

**Pasos**

1. add 1 to n_scans and to n_occupied, n_free or n_uncertain of each channel according to its state — _esperado:_ counters updated
2. when the scan stamp crosses an interval boundary close the interval: duty_cycle = 100 x n_occupied / (n_occupied + n_free), null when the denominator is 0; uncertain_fraction = 100 x n_uncertain / n_scans — _esperado:_ duty cycle and Uncertain fraction of each channel
3. set partial when the node started or the interval length changed inside the interval, and time_flag when the clock was unsynced or stepped; publish `duty_cycle_report` and reset the counters — _esperado:_ `duty_cycle_report` published

## `verify_amplitude_correction` — Verificación periódica

- **Para qué:** check the active amplitude correction against an independent reference, extend or end its validity, and write the validation record
- **Quién lo ejecuta:** operator
- **Cuándo:** at intervals not above the declared verification interval (el intervalo de verificación y su margen), at the latest before verified_until; also after a hardware replacement and after a drift alert
- **Condiciones previas:** an active calibration record; the antenna cable disconnected at the SDR antenna port; external (not part of the node cost): an independent reference source with traceability different from the establishing source and expanded uncertainty at most `independent_reference_uncertainty_max`, the 50 ohm termination, a cable with measured loss; node clock synced
- **Duración:** 39 min
- **Resultado:** `validation_record`, `calibration_validity`
- **Salidas por fallo:** `E-VER-001`, `E-VER-002`, `E-VER-003`, `E-VER-004`, `E-VER-005`, `E-VER-006`, `E-VER-007`
- **Criterio de éxito:** all 12 differences within `verification_tolerance` (1.0 dB) and the frequency correction within `frequency_correction_limit` (20 ppm)
- **Reproducibilidad:** the same channels, levels, tolerance and judgement at every site; what is compared is the differences table and the frequency correction («Reproducibilidad entre sitios»)

**Pasos**

1. record the identity of the independent reference (name, model, serial, calibration date, certificate id, traceability body, traceability chain id, uncertainty) and compare serial, certificate id and chain id with those of the establishing source; the operator attests that no calibration standard is common; refuse if any item is missing or equal — _esperado:_ serial, certificate and chain all differ (else `E-VER-001`, `E-VER-004`)
2. read the calibration reference level and the usable range from the active record and set the two verification levels: L_ref and L_ref - `verification_level_offset`, the lower not below range_low + `range_low_snr` — _esperado:_ two levels inside the usable range
3. connect the independent reference through the cable and, for each of the `verification_channel_count` = 6 channels (16, 46, 76, 126, 146, 186) and each level, set the channel centre frequency and level at the plane, wait `point_settle_time` and take `repeats_per_point` scans; take the median calibrated power and compute difference = power - level at the plane — _esperado:_ 12 differences
4. measure the tone frequency at each point with the estimator of «Estimador espectral» and compute the ppm error; the median is the new correction — _esperado:_ correction in ppm
5. judge: pass if every |difference| <= `verification_tolerance` and |correction| <= `frequency_correction_limit`; fail if any |difference| - `verification_measurement_uncertainty` > `verification_tolerance` or |correction| > `frequency_correction_limit`; otherwise inconclusive — _esperado:_ pass, fail or inconclusive
6. on inconclusive repeat steps 3 to 5 at most `verification_repeat_limit` times; a second inconclusive counts as fail — _esperado:_ final verdict
7. write the validation record `validation_record` with its sha256; on pass set verified_until = now + verification_interval_s, state valid, and send the new correction to «Estimador espectral» (`estimator_control`); on fail set state invalid; update calibration/active.json (`calibration_validity`) — _esperado:_ record and active state written

## `compare_with_reference` — Comparador con asignaciones

- **Para qué:** compare the released occupancy state of each channel with the station-assignment reference and record the result
- **Quién lo ejecuta:** software
- **Cuándo:** each scan, when `occupancy_scan` of the scan is available
- **Condiciones previas:** `config_status` and `station_assignment_reference` of «Configuración del sitio» available (the reference may be missing)
- **Duración:** 0.01 s
- **Resultado:** `assignment_comparison_scan`
- **Salidas por fallo:** `E-el componente`, `E-el componente`
- **Criterio de éxito:** none: a pure computation; checked by the vector tests of the test spec
- **Reproducibilidad:** n/a: not site-dependent (the reference is site data)

**Pasos**

1. check that `occupancy_scan` holds 199 channels and that the reference_state of `config_status` is valid; if `occupancy_scan` is invalid set every comparison to indeterminate (`E-el componente`); if the reference is missing or invalid set every comparison to indeterminate with assigned null (`E-el componente`) — _esperado:_ valid inputs or all indeterminate
2. for each channel look up the entry of the reference: assigned true with the station name when an entry exists, otherwise assigned false — _esperado:_ assigned flag and station
3. if the occupancy state is Uncertain the comparison is indeterminate; otherwise apply the table: assigned and Occupied -> consistent; unassigned and Free -> consistent; unassigned and Occupied -> unassigned-occupied; assigned and Free -> assigned-free — _esperado:_ one of four values
4. copy the occupancy entry of `occupancy_scan` into each channel and publish `assignment_comparison_scan` with the reference id and reference_used — _esperado:_ `assignment_comparison_scan` published

## `build_records` — Registros de escaneo y de salud

- **Para qué:** build the scan header, the 199 channel records and the health record of a scan from the outputs of the earlier modules and publish them
- **Quién lo ejecuta:** software
- **Cuándo:** each scan, when `assignment_comparison_scan` of the scan is available
- **Condiciones previas:** `time_status`, `config_status`, `capture_block`, `acquisition_counters`, `channel_power_scan`, `calibrated_channel_power`, `calibrated_spectrum`, `occupancy_scan`, `assignment_comparison_scan` of the same scan_id
- **Duración:** 0.15 s
- **Resultado:** `scan_header`, `channel_record`, `health_record`
- **Salidas por fallo:** `E-REC-001`, `E-REC-002`, `E-REC-003`, `E-REC-004`
- **Criterio de éxito:** none: a pure construction; checked by the schema tests of the test spec
- **Reproducibilidad:** n/a: not site-dependent

**Pasos**

1. check that scan_id is the same in all inputs and that `assignment_comparison_scan` holds 199 channels; on failure publish only the health record with records_published 0 (`E-REC-001`, `E-REC-002`) — _esperado:_ consistent inputs
2. fill the scan header: node and scan identifiers, UTC stamp with resolution and sync state, the three acquisitions with gains, flags and counts, calibration record and state, frequency-reference state, estimator configuration, site configuration with location, thresholds and the evidence label — _esperado:_ header within its size limit
3. for each channel fill the power object from `calibrated_channel_power` with the gain triple and calibration record id, the occupancy object from `occupancy_scan` with its inputs, the assignment object from `assignment_comparison_scan`, the mapping object from `channel_power_scan` and screening_evidence true — _esperado:_ record within its size limit
4. compute the limit comparison on the unrounded values: no configured limit gives not_configured with limit_dbm null; withheld power gives unavailable; otherwise within_limit when P + U <= L, outside_limit when P - U > L, indeterminate otherwise; then round stored values to `stored_power_resolution` — _esperado:_ limit object with a comparison
5. check every generated text against `forbidden_wording` (except the exact label); on a hit replace the text by a neutral one (`E-REC-004`) — _esperado:_ no forbidden word
6. fill the health record with the overflow, dropped-frame and published-record counts and the other fields of `health_record` — _esperado:_ health record
7. publish header, channel records and health record to el historial en memoria, el escritor de informes and el motor de alertas — _esperado:_ 199 records, 1 header, 1 health record published

## `update_history` — Historial en memoria

- **Para qué:** add each published scan to the minute bins and the per-scan series in memory and keep the latest scan, never writing monitoring records to disk
- **Quién lo ejecuta:** software
- **Cuándo:** each scan, when `scan_header`, `channel_record` and `health_record` of the scan are published
- **Condiciones previas:** start-up guard passed: no swap, core dumps disabled
- **Duración:** 0.02 s
- **Resultado:** `history_bins_response`, `history_series_response`
- **Salidas por fallo:** `E-HIS-001`, `E-HIS-002`, `E-HIS-003`, `E-HIS-004`
- **Criterio de éxito:** 0 monitoring records written to disk (el criterio de R-31)
- **Reproducibilidad:** n/a: not site-dependent

**Pasos**

1. at service start check that swap space is `swap_space` = 0 and the core dump limit is `core_dump_limit` = 0; otherwise refuse to start the history and the monitoring (`E-HIS-004`) — _esperado:_ guard passed
2. allocate the bins (`bins_per_channel` per channel of `bin_record_size` bytes) and the series (`series_length` of `scan_series_entry_size` bytes) within `history_memory_cap`; on failure shorten the window by halves until it fits (`E-HIS-001`) — _esperado:_ memory allocated
3. for each channel record find the bin of its scan start (floor(utc / `bin_length`)); add 1 to n_scans and to n_occupied, n_free or n_uncertain, to n_assigned_free or n_unassigned_occupied by the comparison, and, when the power is released, to n_released and to the running mean and maximum of the released power; remember the most frequent withheld reason — _esperado:_ bins updated
4. append the entry of the series (stamp, median noise floor, counts from the health record, states) and replace the latest scan — _esperado:_ series and latest scan updated
5. drop the bins and series entries older than `history_window` (ring buffers: the oldest slot is overwritten) — _esperado:_ memory constant
6. if the UTC stamp moves back by more than one bin or forward by more than the window, clear the history, set history_start_utc_us to the new time and record it (`E-HIS-002`) — _esperado:_ history continuous or restarted

## `report_run_lifecycle` — Escritor de informes

- **Para qué:** open, close and recover screening runs and manage the segment files of the report
- **Quién lo ejecuta:** software
- **Cuándo:** service start, first scan of a run, end of a timed run, segment change every `segment_length`, free-space check every `free_space_check_interval`
- **Condiciones previas:** Industrial microSD SDCIT2/64GBSP mounted read-write; configuration loaded (`site_config`, `config_status`)
- **Duración:** 0.05 s
- **Resultado:** `report_header`, `report_listing`
- **Salidas por fallo:** `E-RPT-002`, `E-RPT-003`, `E-RPT-004`, `E-RPT-005`, `E-RPT-006`
- **Criterio de éxito:** none: housekeeping; checked by the interruption test of el criterio de R-73 and the report inspection of el criterio de R-62
- **Reproducibilidad:** n/a: not site-dependent

**Pasos**

1. at start look for a run with no end time: close it with the end taken from progress.json, interrupted true, mark an unfinished segment incomplete and keep it (`E-RPT-005`, `E-RPT-004`) — _esperado:_ previous run closed
2. check the manifests: the sha256 of each closed segment must match; mark a mismatch corrupt (`E-RPT-004`) — _esperado:_ manifests verified
3. open a new run: run_id, header with the location (or 'not configured', `E-RPT-006`), run mode, planned duration, start stamp of the first scan, configuration and calibration identifiers, evidence label; write header.json atomically — _esperado:_ header written
4. every `segment_length` close the open segment: compute its sha256, write its manifest entry and open the next segment with the # column line — _esperado:_ segment closed, next opened
5. every `free_space_check_interval` compare the free space with `free_space_floor`; if lower delete the oldest closed segments of the oldest runs until free space is `free_space_floor` plus one segment, keeping header and manifest with state deleted (`E-RPT-002`); if no closed segment remains stop writing (`E-RPT-003`) — _esperado:_ free space at or above the floor
6. for a timed run, when the run has lasted record_time_min from its start, close the run: end stamp, execution time, last segment closed, header rewritten; the acquisition then stops taking records — _esperado:_ run closed with execution time

## `write_scan_to_report` — Escritor de informes

- **Para qué:** append the records of a scan to the open segment and flush it to the card
- **Quién lo ejecuta:** software
- **Cuándo:** each scan, when `scan_header`, `channel_record` and `health_record` of the scan are published
- **Condiciones previas:** an open run and segment (`report_run_lifecycle`)
- **Duración:** 0.05 s
- **Resultado:** `report_lines`
- **Salidas por fallo:** `E-RPT-001`
- **Criterio de éxito:** every scan published before an interruption is in the file (el criterio de R-73)
- **Reproducibilidad:** n/a: not site-dependent

**Pasos**

1. build the S line, the 199 C lines and the H line of the scan in the format `report_lines`; replace commas and line breaks in texts by a space — _esperado:_ about 41.6 KB of lines
2. append the lines to the open segment and flush to the card (`flush_every_scans` = after every scan) — _esperado:_ scan on the card
3. on a write error retry `write_retry_count` times at `write_retry_interval`; if it still fails keep the scan in the pending buffer of `pending_scans_max` scans and try again after the next scan (`E-RPT-001`) — _esperado:_ written or pending
4. append the interval lines of `duty_cycle_report` to intervals.csv when an interval closes and rewrite progress.json every `progress_update_interval` — _esperado:_ intervals and progress written

## `evaluate_scan_alerts` — Motor de alertas

- **Para qué:** on every scan, update the health bookkeeping, check the calibration state and the unassigned-occupied channels, and raise or clear the sensor-offline recovery, calibration-not-demonstrated and unexpected-occupancy alerts
- **Quién lo ejecuta:** software
- **Cuándo:** each scan, when `channel_record` (199 records) and `health_record` of the scan are published by el constructor de registros
- **Condiciones previas:** engine started; `site_config` and `config_status` readable
- **Duración:** 0.02 s
- **Resultado:** `alert_event`, `alert_status_response`
- **Salidas por fallo:** `E-ALR-004`, `E-ALR-005`, `E-ALR-006`, `E-ALR-008`
- **Criterio de éxito:** unexpected-occupancy alert raised for an occupied unassigned channel at the third consecutive scan: 0 not raised (el criterio de R-36 <= 0 count); calibration-not-demonstrated alert raised on the first scan with an expired verification interval: 0 not raised (el criterio de R-38 <= 0 count)
- **Reproducibilidad:** n/a: not site-dependent

**Pasos**

1. read `health_record`; when records_published is at least 1 and inconsistent is false, count a health point: restart the monotonic timer of `watch_health_points` and add 1 to the run of consecutive health points; otherwise set that run to 0 and, if `channel_record` is missing, skip steps 3 and 4 (`E-ALR-004`) — _esperado:_ health point counted or scan skipped
2. when the run of consecutive health points reaches `sensor_offline_scan_periods` = 3 and a sensor-offline alert is active, clear it with clear_reason condition_ended — _esperado:_ sensor-offline alert cleared after 3 points
3. calibration check: condition holds when calibration_state of `health_record` is not valid, or any of the 199 records of `channel_record` has a power.withheld_reason in `calibration_withheld_reasons`; when it holds and no calibration alert is active raise calibration_not_demonstrated with the state, the reasons found, verified_until_utc_us and expiry_margin_s of `calibration_validity`; when it does not hold add 1 to the clear count and clear the active alert at `alert_clear_count` consecutive scans; when it holds reset the clear count — _esperado:_ calibration alert raised on the first scan with the condition
4. unexpected-occupancy check (skipped while the reference is unavailable, `E-ALR-005`): for each channel 1 to 199 read assignment.comparison of `channel_record`; when it is unassigned-occupied add 1 to the persistence count and set the clear count to 0, otherwise set the persistence count to 0 and add 1 to the clear count; raise unexpected_occupancy for the channel when the persistence count reaches `unexpected_persistence_scans` = 3 and none is active; clear the active alert when the clear count reaches `alert_clear_count` — _esperado:_ unexpected-occupancy alert raised at the third consecutive scan
5. build the text of every new event from its fixed template, check it against `forbidden_wording` and `alert_text_max_bytes` (`E-ALR-008`) and stamp it with the UTC time and sync_state of `time_status` — _esperado:_ text without a forbidden word
6. append the events to the ring (`E-ALR-006`), update the active list and publish `alert_status_response`; no step reads power.value_dbm or limit.comparison, so no alert is raised from the received power (R-40) — _esperado:_ events and status published

## `evaluate_history_alerts` — Motor de alertas

- **Para qué:** every minute, update the silence state of each assigned channel from the closed one-minute bin and evaluate the channel-silent and noise-floor-drift alerts from the history
- **Quién lo ejecuta:** software
- **Cuándo:** every 60 s at the end of a one-minute bin plus `minute_evaluation_delay` = 10 s (every closed bin not yet processed, `E-ALR-010`)
- **Condiciones previas:** engine started; history store running
- **Duración:** 0.2 s
- **Resultado:** `alert_event`, `alert_status_response`
- **Salidas por fallo:** `E-ALR-001`, `E-ALR-002`, `E-ALR-003`, `E-ALR-005`, `E-ALR-006`, `E-ALR-007`, `E-ALR-008`, `E-ALR-010`
- **Criterio de éxito:** channel-silent alert raised when the credit reaches the declared hours and the prior duty cycle is above 90 %: 0 not raised (el criterio de R-34 <= 0 count); Uncertain observations counted toward silence: 0 (el criterio de R-35 <= 0 count); noise-floor-drift alert raised when the median shifts by more than 6 dB over 24 h: 0 not raised (el criterio de R-39 <= 0 count)
- **Reproducibilidad:** n/a: not site-dependent

**Pasos**

1. read the hours H of alert.silent_on_air_hours from `site_config` (absent: `E-ALR-001`) and the reference state from `config_status`; when reference_id changed since the last tick reset every silence credit and prior status; when H changed, clear any active silent alert whose credit is below the new H with clear_reason config_changed — _esperado:_ H known or rule not configured
2. read the closed bin of every channel that has an entry in `station_assignment_reference` from `history_bins_response` (channels listed, from and to equal to the bin start, resolution 60 s); when history_start_utc_us changed apply `E-ALR-007` — _esperado:_ 199 bins at most
3. for each channel: if n_occupied is at least `active_scans_to_break_silence` = 3 the bin is active: set the credit to 0, set the last active end to the end of the bin, set the prior status to pending and clear an active channel_silent alert (condition_ended); otherwise, if n_assigned_free is at least 1, add n_assigned_free x `silence_credit_per_scan` (6 s) to the credit; a bin with only Uncertain, consistent or no scans changes nothing (R-35) — _esperado:_ credit counts assigned-free scans only
4. for a channel whose prior status is pending and that just received credit (start of a run): read its bins from the last active end minus `prior_duty_window` = 24 h to the last active end (1440 bins at most); when the history covers the window and Occupied plus Free scans are at least `prior_duty_min_observation_share` of the scans, compute D = 100 x sum n_occupied / (sum n_occupied + sum n_free) and set the status busy when D is above `silent_prior_duty_threshold` = 90, else not_busy; otherwise set insufficient_history (`E-ALR-002`) — _esperado:_ prior status decided once per run
5. drift (every tick): request `history_series_response` for the window [t - `drift_window`, t) and for [t - `drift_span` - `drift_window`, t - `drift_span`), with t the end of the processed bin; each window needs at least `drift_min_sample_share` = 300 non-null median noise floors and the history must reach the older window (`E-ALR-003`); M_now and M_ref are the medians of the two windows (mean of the two middle values for an even count); the shift is |M_now - M_ref|; when it is above `drift_threshold` = 6 dB and no drift alert is active raise noise_floor_drift; when it is not above 6 dB add 1 to the clear count and clear the active alert at `alert_clear_count` consecutive evaluations; at every evaluation publish M_now, M_ref and the shift in `alert_status_response` noise_floor_drift (status insufficient_history and null values when it cannot be evaluated) — _esperado:_ drift alert raised when the shift is above 6 dB
6. for each channel with H configured, prior status busy, credit at least H x 3600 s and no active alert: raise channel_silent with the credit, H, the prior duty cycle, the station and the reference_id — _esperado:_ silence alert raised once per run
7. build the texts (fixed templates, `E-ALR-008`), stamp the events, append them to the ring (`E-ALR-006`), update the active list and publish `alert_status_response` — _esperado:_ events and status published

## `watch_health_points` — Motor de alertas

- **Para qué:** raise the sensor-offline alert when no health point has arrived for three scan periods, using a monotonic clock that does not depend on time synchronisation
- **Quién lo ejecuta:** software
- **Cuándo:** every `offline_check_interval` = 1 s
- **Condiciones previas:** engine started
- **Duración:** 0.001 s
- **Resultado:** `alert_event`, `alert_status_response`
- **Salidas por fallo:** `E-ALR-006`
- **Criterio de éxito:** sensor-offline alert raised when no health record arrives for three scan periods: 0 not raised (el criterio de R-37 <= 0 count)
- **Reproducibilidad:** n/a: not site-dependent

**Pasos**

1. compute the elapsed time since the last health point counted by `evaluate_scan_alerts` (or since the engine start when none has arrived) with the monotonic clock and publish it as sensor.last_health_point_age_s of `alert_status_response`, with sensor.online false while a sensor_offline alert is active — _esperado:_ elapsed seconds
2. when the elapsed time is at least `sensor_offline_timeout` = 18 s and no sensor_offline alert is active, raise it with seconds_since_health_point, last_health_utc_us (null when none) and the UTC time and sync_state of `time_status`; publish `alert_status_response` — _esperado:_ sensor-offline alert raised at most 19 s after the last health point

## `repeat_at_another_site` — Reproducibilidad entre sitios

- **Para qué:** build, configure, calibrate and run a second node at another site with the same package so that its results can be compared with those of the first
- **Quién lo ejecuta:** operator
- **Cuándo:** when the person orders the repeat (once per reproducibility check)
- **Condiciones previas:** the first site has a valid calibration, a passed verification (`validation_record`) and a saved 72 h report; the same hardware cards (HackRF One to 36650 USB 2.0 Type A to Micro-B cable) are available for site B
- **Duración:** 76 h
- **Resultado:** `cross_site_comparison`
- **Salidas por fallo:** `E-REP-001`, `E-REP-002`, `E-REP-003`, `E-REP-005`
- **Criterio de éxito:** none: a pure action; its results are judged by `compare_two_sites`
- **Reproducibilidad:** the same package, configuration schema, estimator and detector parameters and the same two procedures at both sites (`identical_items`); what differs on purpose is the site, the units, the references and the ground truth

**Pasos**

1. build the second node from the same characteristic cards and install the package with the same sha256; create a new node_id and the configuration of site B (location and station reference of site B) by `add_and_configure_another_node`; list the configuration of both nodes (`scan_cycle` listing) and check every item of `identical_items` (E-REP-001) — _esperado:_ identical items confirmed
2. establish the amplitude calibration at site B with its own traceable source (`establish_amplitude_calibration`) and verify it with its own independent reference (`verify_amplitude_correction`) at the same 6 channels and the same 2 nominal levels as the first site; the reference of site B has a level uncertainty of at most `independent_reference_uncertainty_max` (E-REP-003); the validation result must be pass (E-REP-002) — _esperado:_ calibration and validation records of site B valid
3. run the screening at site B for `repeat_run_duration` = 72 h in the deployment configuration, with the acceptance set of el criterio de R-04 and el criterio de R-05 annotated against an independent reference; extend by `acceptance_extension_length` = 24 h at most `acceptance_extension_max` = 2 times when the set is too small (E-REP-005); save the report — _esperado:_ report B and its acceptance set
4. collect from site A its latest valid calibration record, its latest passed validation record, its saved report and its acceptance set; confirm that the two validation records are both valid on the day of the comparison — _esperado:_ inputs of both sites collected

## `compare_two_sites` — Reproducibilidad entre sitios

- **Para qué:** apply the agreement rule of to the records of the two sites and write the comparison record
- **Quién lo ejecuta:** operator
- **Cuándo:** after `repeat_at_another_site` has delivered the inputs of both sites
- **Condiciones previas:** inputs of `repeat_at_another_site` step 4 available
- **Duración:** 2 h
- **Resultado:** `cross_site_comparison`
- **Salidas por fallo:** `E-REP-001`, `E-REP-002`, `E-REP-003`, `E-REP-004`, `E-REP-005`, `E-REP-006`
- **Criterio de éxito:** agreement of power points at least 83.3 % (10 of 12) with none above 6 dB, both sites meeting R-04 and R-05 and both reports complete (el criterio de R-51 threshold of la regla de reproducibilidad entre sitios)
- **Reproducibilidad:** the rule is applied identically to any pair of sites: same quantities, same coverage factor k = 2, same threshold; the comparison uses only the records of the two nodes and the acceptance sets

**Pasos**

1. confirm the identical items of `identical_items` once more from the two records and the two configuration listings; a difference is E-REP-001 — _esperado:_ identical_items.pass true
2. check both validation records: result pass, independence flags all true, reference uncertainty at most `independent_reference_uncertainty_max`, same channels and nominal levels (E-REP-002, E-REP-003) — _esperado:_ records fit for comparison
3. for each of the `cross_site_power_points` = 12 points compute D = difference_db of the record (calibrated power minus the reference level) for each site, W = sqrt(U^2 + u^2) with U the uncertainty_db of the calibrated channel power and u the measurement_uncertainty_db of the record, delta = D_A - D_B, En = |delta| / sqrt(W_A^2 + W_B^2); the point agrees when En <= `agreement_en_max` = 1; a missing point is measured again once (E-REP-004); count the agreeing points and the largest |delta| — _esperado:_ 12 points with En and agree
4. power criterion: pass when the agreeing points are at least `power_agreement_min_points` = 10 (share at least `power_agreement_min_share` = 83.3 %) and no |delta| is above `power_difference_hard_limit` = 6 dB; criterion (2): for each site compute the detection share on its occupied observations and the false-alarm share on its vacant observations and check the sample sizes (E-REP-005): pass when detection is at least 95 % and false alarm at most 5 % — _esperado:_ criteria (1) and (2) decided
5. criterion (3): inspect 100 % of the channel lines of the report of each site for the fields of `report_fields_required`; any missing field is E-REP-006; write the two frequency corrections and their states side by side (each must be within `frequency_correction_limit` = 20 ppm; the two values are not compared with each other, because two crystals differ) — _esperado:_ criterion (3) decided and corrections recorded
6. write `cross_site_comparison`: result agree when the three criteria pass, disagree when one fails, inconclusive when one could not be evaluated; the person approves it (la regla de reproducibilidad entre sitios) — _esperado:_ comparison record written and approved

## `start_node` — Supervisión y manejo de errores

- **Para qué:** start the node after power-up or reboot in an order that readies every consumer before its producer, and recover from an unclean stop
- **Quién lo ejecuta:** software
- **Cuándo:** operating system boot (the service manager starts the supervisor)
- **Condiciones previas:** mains power; storage medium readable
- **Duración:** 300 s
- **Resultado:** `supervisor_status`, `supervisor_log_line`
- **Salidas por fallo:** `E-SUP-006`, `E-SUP-008`
- **Criterio de éxito:** after a power cut and return, the first complete scan record is published within 300 s and the interrupted run is marked (el criterio de R-48 availability, el criterio de R-73)
- **Reproducibilidad:** n/a: not site-dependent

**Pasos**

1. read the marker supervisor/clean-stop: present means a clean stop, delete it; absent after an earlier run means an unclean stop (E-SUP-006); create a new boot_id; restore reboots_last_24h by counting the reboot_ordered events of the last 24 h in the supervisor log, so the limit `reboot_limit_per_day` holds across reboots; write the event boot — _esperado:_ boot kind known
2. arm the hardware watchdog with `hw_watchdog_timeout` and start publishing `supervisor_status` with node_state starting every `status_publish_interval` — _esperado:_ liveness published, watchdog armed
3. start the time service el servicio de hora and do not wait for it: a scan is never withheld because of time («Servicio de hora»); it waits for synchronisation at most `startup_sync_wait` = 120 s only to state sync_state — _esperado:_ time service running
4. read the site configuration («Configuración del sitio»; E-CFG codes) and run the start guard of the history store (no swap, no core dumps, E-HIS-004); when the guard fails start only the report writer and the web service, write guard_failed and keep node_state not_measuring — _esperado:_ configuration read, guard passed or measuring refused
5. apply the limits of `apply_resource_limits` of «Presupuesto de recursos» (memory caps, processor quotas, niceness, memory-backed temporary files) and start the processes in this order: report, store_alert, web, measure; start each when the previous one publishes its first progress count; the measure process is last so every consumer is ready (`ipc_send_queue` queues the rest) — _esperado:_ four processes started
6. set node_state measuring when the first complete scan record has been published, measuring_degraded when it carries a condition of section 3 — _esperado:_ first scan published within `recovery_time_process` (72 s) of the failure that caused the start, or `recovery_time_reboot` (300 s) after a reboot

## `supervise_processes` — Supervisión y manejo de errores

- **Para qué:** watch the five units, restart a failed one with a growing wait, escalate a loop to a reboot, derive the node state and publish it
- **Quién lo ejecuta:** software
- **Cuándo:** every `progress_tick_interval` = 1 s
- **Condiciones previas:** `start_node` step 2 done
- **Duración:** 0.01 s
- **Resultado:** `supervisor_status`, `supervisor_log_line`
- **Salidas por fallo:** `E-SUP-001`, `E-SUP-002`, `E-SUP-003`, `E-SUP-004`, `E-SUP-007`, `E-SUP-008`
- **Criterio de éxito:** a killed measure process is restarted and the first complete scan appears within 72 s; a stopped node raises the sensor-offline alert (el criterio de R-37) and is counted unavailable only after 18 s without a complete scan (el criterio de R-48)
- **Reproducibilidad:** n/a: not site-dependent

**Pasos**

1. read the exit status of every process; a non-zero exit, a signal or an exit within `restart_delay_initial` of the start is E-SUP-001 — _esperado:_ exits known
2. read the progress counter of every process and the time since the last scan or health record of the measure process: no change for `hang_timeout` = 10 s, or no scan for `scan_progress_timeout` = 12 s while the node is meant to measure, is E-SUP-002; kill the process — _esperado:_ hung processes found
3. restart a failed process after min(`restart_delay_initial` x `restart_backoff_factor`^(k - 1), `restart_delay_max`) where k is its restarts inside `restart_limit_window`; at `restart_limit_count` = 5 restarts set restart_loop (E-SUP-003); after `reboot_after_loop` = 1800 s in the loop, order a reboot unless `reboot_limit_per_day` = 3 reboots were ordered in 24 h (E-SUP-004); a process that ran `restart_stable_time` = 600 s is healthy again and its k restarts at 0 — _esperado:_ restart ladder applied
4. run `monitor_temperature` of «Presupuesto de recursos» every 10 s (processor temperature, condition thermal); derive node_state and power_released from the process states, the latest health record (calibration_state, config_state, sync_state, scan_late, flagged scan, records_published) and the storage status (report_state, history_state) by the rules of section 3 — _esperado:_ node_state and conditions
5. publish `supervisor_status` and write the events of this tick to the supervisor log (E-SUP-008 when the write fails) — _esperado:_ status published, events logged
6. feed the hardware watchdog every `hw_watchdog_feed_interval` = 5 s, only when this loop ran — _esperado:_ watchdog fed

## `stop_node` — Supervisión y manejo de errores

- **Para qué:** stop the node in an orderly way so that the report run is closed and the next start is clean
- **Quién lo ejecuta:** software
- **Cuándo:** an ordered stop or reboot (operator command or E-SUP-004)
- **Condiciones previas:** supervisor running
- **Duración:** 40 s
- **Resultado:** `supervisor_log_line`
- **Salidas por fallo:** `E-SUP-008`
- **Criterio de éxito:** after an ordered stop the next boot finds the marker and unclean_boot is false
- **Reproducibilidad:** n/a: not site-dependent

**Pasos**

1. stop the measure process first, then store_alert, web and report in this order, each with a wait of at most `hang_timeout` = 10 s before it is killed — _esperado:_ processes stopped
2. let the report writer close the open run and segment («Escritor de informes»), then write the event clean_stop and create the marker supervisor/clean-stop — _esperado:_ run closed, marker written
3. stop the hardware watchdog feed only after the power-off or reboot command is given — _esperado:_ node stopped

## `serve_view_request` — Servicio web

- **Para qué:** answer one GET or HEAD for a page, a static file or a data view, using only read access to the other components and releasing only released values
- **Quién lo ejecuta:** software
- **Cuándo:** each HTTP request on port `web_port`
- **Condiciones previas:** service started with the limits `web_memory_cap` to `web_scheduling_priority`; sources readable
- **Duración:** 0.1 s
- **Resultado:** `web_view_data`
- **Salidas por fallo:** `E-WEB-001`, `E-WEB-002`, `E-WEB-003`, `E-WEB-004`, `E-WEB-005`, `E-WEB-006`, `E-WEB-007`, `E-WEB-009`
- **Criterio de éxito:** every answer carries the evidence label: share of records, reports and dashboards identified as screening evidence at least 100 % (el criterio de R-32); unreleased power values drawn: 0 (el criterio de R-45); users or roles denied: 0 (el criterio de R-67)
- **Reproducibilidad:** n/a: not site-dependent

**Pasos**

1. check the request: size at most `web_request_max_bytes` and no body (E-WEB-004); method in `web_allowed_methods` (E-WEB-001); path in `web_request` and free of '..' or an encoded separator (E-WEB-002); parameters inside `web_request` (E-WEB-003) — _esperado:_ request valid
2. admission: take a worker when fewer than `web_concurrent_workers` are busy, else wait in the queue; refuse with 503 when `web_request_queue_length` requests wait or the wait passes `web_queue_wait_limit` (E-WEB-005); no identity, address or role is read — _esperado:_ worker taken or request refused without regard to who asks
3. look for a cached answer of the same path and parameters younger than `cache_ttl_live` (live views) or `cache_ttl_history` (history views); the alert answer is never cached; otherwise read the sources: `history_bins_response` bins for the map and the station view (resolution `power_map_resolution_options` or `stations_view_resolution`), `history_series_response` latest scan and series (range request of 24 h) for the spectrum and the status, `alert_status_response` for alerts, status, drift and online state, `supervisor_status` for the node state and the processes, `report_listing` for the report list, `site_config`, `station_assignment_reference` and `config_status` for the node, the stations and the reference; a failed read is E-WEB-006 — _esperado:_ source data read
4. apply the release rule to every value: a power value enters the answer only when power.withheld_reason is none, otherwise null plus the withheld_reason and flags; an Occupied or Free state only with validity valid, otherwise Uncertain with its reason (E-WEB-009); aggregate bins give counts of Occupied, Free and Uncertain scans and never one converted state — _esperado:_ only released values in the answer
5. build the view content: power map cells for 199 channels; spectrum points joined at `spectrum_join_frequencies` with the 199 markers of channel centre 88.1 + 0.1 x (n - 1) MHz; for each selected station the duty cycle 100 x sum n_occupied / (sum n_occupied + sum n_free) over 24 h (null when the sum is 0), the share of Uncertain scans and the bins; the status quantities from `alert_status_response` and the latest health record; wrap the content in `web_view_data` with the evidence label `evidence_label`, the node, the location, sync_state, history_start_utc_us and alerts_summary — _esperado:_ `web_view_data` answer
6. serialize and send with Content-Type, the header X-Screening-Evidence: true and Cache-Control no-store for alerts or max-age equal to the cache time for the others; stop and free the worker at `response_time_limit` (E-WEB-007); store the answer in the cache — _esperado:_ answer sent within 2 s

## `serve_report_file` — Servicio web

- **Para qué:** send a saved screening report file to any user, unchanged
- **Quién lo ejecuta:** software
- **Cuándo:** GET or HEAD of /reports/<run_id>/<file>
- **Condiciones previas:** `serve_view_request` steps 1 and 2 passed; `report_listing` readable
- **Duración:** 1.25 s
- **Resultado:** `web_view_data`
- **Salidas por fallo:** `E-WEB-002`, `E-WEB-008`
- **Criterio de éxito:** every saved report file listed is downloadable by every user: users or roles denied access to the saved screening reports: 0 (el criterio de R-67)
- **Reproducibilidad:** n/a: not site-dependent

**Pasos**

1. look up the run and the file in `report_listing`; a file not in the listing, or a name with '..' or a separator, is E-WEB-002 and the file system is not touched — _esperado:_ file found in the listing
2. check the file exists and, for a closed file, that its size and sha256 equal the listing (E-WEB-008); for an open file record its size now — _esperado:_ file consistent with the listing
3. take a download stream when fewer than `download_streams_max` are busy, else wait in the request queue; send the bytes unchanged at a total rate of at most `download_rate_limit` with the headers Content-Type, Content-Length, ETag equal to the sha256, X-Report-State and X-Screening-Evidence: true — _esperado:_ file sent unchanged

## `refresh_page` — Servicio web

- **Para qué:** keep the page current: ask again at the refresh interval, draw only what the answer holds, show the alert bar and the label
- **Quién lo ejecuta:** software
- **Cuándo:** page load and then every `live_refresh_interval` (spectrum, status, alerts) or `history_refresh_interval` (power map, stations, reports) seconds
- **Condiciones previas:** the page script served by el servicio web is running in the browser of the user
- **Duración:** 0.5 s
- **Resultado:** `web_request`
- **Salidas por fallo:** `E-WEB-005`, `E-WEB-006`, `E-WEB-007`
- **Criterio de éxito:** the four views and the raised alerts are available in the browser: views demonstrated at least 1 each (el criterio de R-41, el criterio de R-42, el criterio de R-43, el criterio de R-44, el criterio de R-46)
- **Reproducibilidad:** n/a: not site-dependent

**Pasos**

1. ask /api/alerts?scope=bar every `live_refresh_interval` on every page, and the data of the page view at its interval; make no request to any address but the node (`external_requests`) — _esperado:_ answers received
2. show the fixed header with the label `evidence_label`, the node identifier, the location text, the UTC time of the answer and sync_state (flagged when not synced), and the alert bar: the number of active alerts and the text of up to `alert_bar_max_inline` = 5 of them with their raised time, or 'no active alert' plus every rule whose status is not evaluating — _esperado:_ header and alert bar drawn
3. draw the view from the answer: the power colour scale is fixed at `power_scale_range`; a null power is drawn as a hatched cell or a gap with its withheld_reason in the tooltip, never as zero or as the last value; counts of Occupied, Free and Uncertain are drawn as shares, not as one state; when data_state is not ok write what it is (no_data, insufficient_history from history_start_utc_us, unavailable) instead of an empty chart — _esperado:_ only released values drawn; states written when no data
4. on 503 wait `retry_after` and ask again and show 'busy, retrying'; on any other failure show the code and keep the last good drawing marked 'not current' with its time — _esperado:_ page never shows stale data as current

## `monitor_temperature` — Presupuesto de recursos

- **Para qué:** read the processor temperature and flag a thermal condition without changing what the node measures
- **Quién lo ejecuta:** software
- **Cuándo:** every `thermal_read_interval` = 10 s, from the supervisor loop
- **Condiciones previas:** supervisor running («Supervisión y manejo de errores»)
- **Duración:** 0.001 s
- **Resultado:** `supervisor_status`, `supervisor_log_line`
- **Salidas por fallo:** `E-RES-002`, `E-RES-003`, `E-RES-004`
- **Criterio de éxito:** none: a flag only; the temperature limit is verified by the chamber test (el criterio de R-66)
- **Reproducibilidad:** n/a: not site-dependent

**Pasos**

1. read the processor temperature from the operating system (the thermal zone of the board) and the throttle flag; an unreadable value is E-RES-004 — _esperado:_ temperature known or event written
2. compare with the thresholds: at or above `thermal_warning_threshold` = 70 degC set the condition thermal and write thermal_warning (E-RES-002); at or above `soc_throttle_threshold` = 80 degC, or a throttle flag, write thermal_throttle (E-RES-003); at or below `thermal_warning_clear` = 65 degC clear the condition and write thermal_cleared — _esperado:_ condition set or cleared

## `apply_resource_limits` — Presupuesto de recursos

- **Para qué:** set the memory, processor and priority limits of every unit and the memory-backed temporary storage before the units start
- **Quién lo ejecuta:** software
- **Cuándo:** at boot, in `start_node` step 5 before each unit is started
- **Condiciones previas:** the operating system is up
- **Duración:** 1 s
- **Resultado:** `supervisor_log_line`
- **Salidas por fallo:** `E-RES-001`
- **Criterio de éxito:** no monitoring record on the card outside the report (el criterio de R-31); no overflow or dropped frame in a continuous run (el criterio de R-57)
- **Reproducibilidad:** n/a: not site-dependent

**Pasos**

1. confirm that no swap area exists (`swap_space`), that core dumps are off (`core_dump_limit`) and mount the memory-backed file system of size `tmpfs_size` for every temporary file — _esperado:_ no swap, no core dump, temporary files in memory
2. start each unit with its memory cap (measure `measure_memory_cap`, store_alert `store_alert_memory_cap`, report `report_memory_cap`, supervisor `supervisor_memory_cap`, time `time_memory_cap`, web `web_memory_cap`), its processor quota (measure `measure_cpu_quota`, store_alert `store_alert_cpu_quota`, report `report_cpu_quota`, supervisor `supervisor_cpu_quota`, web `web_cpu_cap_one_core`) and its niceness of `unit_scheduling_priorities` (web `web_scheduling_priority`) — _esperado:_ limits applied to the five units and the web unit

## `compute_availability` — Fiabilidad y disponibilidad

- **Para qué:** judge the availability of a continuous 30-day run by the definition of R-49 from the saved reports and the supervisor log
- **Quién lo ejecuta:** operator
- **Cuándo:** after a 30-day continuous run (el criterio de R-48, el criterio de R-49)
- **Condiciones previas:** the saved report and the supervisor log of the run are available
- **Duración:** 4 h
- **Resultado:** 
- **Salidas por fallo:** 
- **Criterio de éxito:** share of time points counted as available at least 95 % over the 30-day window (el criterio de R-48, el criterio de R-49)
- **Reproducibilidad:** n/a: the same rule at every site

**Pasos**

1. list the time points of the window every `analysis_grid` = 6 s (`analysis_points_30d` = 432,000 points) and, for each, look in the saved report for a complete full-band scan record (199 channel lines and a health line with records_published 199) whose scan time is within the preceding `availability_gap_allowed` = 18 s — _esperado:_ each point marked available or unavailable
2. count the unavailable points and compute the share available = 100 x (432,000 - unavailable) / 432,000 — _esperado:_ share available
3. explain every run of unavailable points from the supervisor log (restart, reboot, verification, calibration) and report the share of channel records in each validity state (calibration state valid, expiring, expired, invalid, none and occupancy validity) with the result — _esperado:_ causes listed, validity shares reported
4. pass when the share is at least `availability_threshold` = 95 % (at most `unavailable_points_max` = 21,600 unavailable points, 36 h) — _esperado:_ el criterio de R-48 and el criterio de R-49 decided

## `run_field_validation` — Fiabilidad y disponibilidad

- **Para qué:** run the continuous 72 h field validation at a site with a published FM station list with an independent reference logging
- **Quién lo ejecuta:** operator
- **Cuándo:** when the person orders the field validation (R-61)
- **Condiciones previas:** the node is calibrated and verified («Calibración de amplitud», «Verificación periódica»); the site has a published FM station list; the independent reference is installed
- **Duración:** 76 h
- **Resultado:** 
- **Salidas por fallo:** `E-RPT-005`, `E-SUP-001`
- **Criterio de éxito:** duration of the continuous field run at least 72 h with independent reference logging for at least 6 h (el criterio de R-61)
- **Reproducibilidad:** the same run is the first-site run of «Reproducibilidad entre sitios» (`repeat_run_duration`); the same duration and configuration at a repeat site

**Pasos**

1. check the site: the published station list is entered as the reference of the configuration («Configuración del sitio») and the noise reference is reliable in at least `site_noise_reliable_share_min` = 95 % of the scans of the first hour — _esperado:_ site fit
2. start the screening run in the deployment configuration and the independent reference logging; keep the logging for at least `reference_logging_min` = 6 h inside the run — _esperado:_ run and logging started
3. keep the run for `field_run_planned_duration` = 76 h planned; an interruption is recovered by the supervisor («Supervisión y manejo de errores») and the report starts a new run (E-RPT-005); the field run counts as continuous while the gap between two runs is at most `field_run_gap_allowed` = 300 s — _esperado:_ continuous time accumulated
4. end the run when the continuous time is at least `field_run_min_duration` = 72 h and the logging at least 6 h; save the reports, the logging and the supervisor log as the evidence of el criterio de R-61 — _esperado:_ el criterio de R-61 evidence saved
