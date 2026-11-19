# Anexo B — Formatos de datos entre módulos

Cada formato lo produce un módulo y lo consumen otros. Todos son objetos JSON en UTF-8 salvo que se indique otra cosa. Un cambio **menor** agrega un campo opcional; un cambio **mayor** cambia el significado de un campo o su tabla de valores.

> Los nombres de parámetros, campos, estados y códigos de error se conservan en inglés porque son los identificadores que se implementan en el código y en los archivos. Las descripciones breves de estos anexos mantienen el texto técnico original.

## `time_status` (versión 1.0)

- **Produce:** el servicio de hora · **Consume:** el constructor de registros
- **Formato:** JSON object, UTF-8, one object per message; integers in decimal; text rendering of a stamp is ISO 8601 'YYYY-MM-DDThh:mm:ss.ffffffZ' (UTC, 6 fractional digits)
- **Límites:** at most 512 bytes per message; at most 1 message per `time_status_refresh` (1 s)
- **Compatibilidad:** Minor: add an optional field or a new enum value at the end. Major: remove, rename or change the unit or meaning of a field, or the epoch.
- **Retención:** n/a

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `utc_us` | int64 | us | 0 to 9223372036854775807 | sí | UTC time since 1970-01-01T00:00:00Z in microseconds, read from the node clock |
| `resolution_us` | int | us | 1 | sí | resolution of utc_us, equal to `timestamp_resolution` |
| `sync_state` | enum |  | synced \| unsynced \| stepped | sí | synced: offset <= `max_clock_offset` and age <= `max_sync_age`; unsynced: otherwise; stepped: a clock step above `clock_step_alarm_threshold` was seen since the last status |
| `offset_est_ms` | float | ms | -1000000 to 1000000, null when no source was ever reached | sí | estimated offset of the node clock against the network time source, signed |
| `last_sync_age_s` | float | s | 0 to 86400, null when never synced | sí | time since the last successful exchange |
| `source_id` | string |  | 0 to 255 bytes | sí | identifier of the network time source in use, empty when none |

## `site_config` (versión 1.1)

- **Produce:** la configuración del sitio · **Consume:** el servicio de adquisición
- **Formato:** JSON object in the file site-config.json, UTF-8, no byte-order mark, numbers in decimal; the station reference is a separate file (`station_assignment_reference`) named by `station_reference_file`
- **Límites:** file size at most `config_file_max_size` (1048576 bytes); at most `time_sources_max` time sources
- **Compatibilidad:** Minor: add an optional field. Major: remove or rename a field, change a unit, a range or the meaning of a field, or make an optional field required.
- **Retención:** n/a

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `schema_version` | string |  | MAJOR.MINOR, major 1 | sí | version of this schema |
| `node_id` | string |  | 1 to 64 characters in A-Z a-z 0-9 _ - | sí | identifier of the node; a new node uses a new value (R-52) |
| `location.country` | string |  | 1 to 256 bytes (`text_field_max_bytes`) | sí | country entered by the user (R-70) |
| `location.city` | string |  | 1 to 256 bytes (`text_field_max_bytes`) | sí | city entered by the user (R-70) |
| `location.place` | string |  | 1 to 256 bytes (`text_field_max_bytes`) | sí | place name or address entered by the user (R-70) |
| `run_mode` | enum |  | timed \| continuous | sí | timed: records are taken for record_time_min then the run stops; continuous: until stopped |
| `record_time_min` | int | min | `record_time_minimum` (10) to `record_time_maximum` (43200); required when run_mode is timed | no | time during which the records are taken (R-74) |
| `mapping_error_limit_khz` | float | kHz | `mapping_error_limit_minimum` (1) to `mapping_error_limit_maximum` (20); default `mapping_error_limit_default` (5) | no | limit of the channel-mapping error the user accepts (R-50, R-75) |
| `time_sources` | array of string |  | `time_sources_min` (1) to `time_sources_max` (4) entries, each 1 to 255 bytes | sí | network time sources of «Servicio de hora» |
| `declared_min_power_dbm.default` | float | dBm | `declared_min_power_floor` (-130) to `declared_min_power_ceiling` (-5) | no | declared minimum received power per channel, same for every channel without an override (la potencia mínima recibida declarada); absent means not configured |
| `declared_min_power_dbm.channels` | map channel number to float | dBm | keys 1 to 199; values `declared_min_power_floor` to `declared_min_power_ceiling` | no | per-channel overrides of the declared minimum received power (la potencia mínima recibida declarada) |
| `duty_cycle_interval_min` | int | min | 1 to 1440; default `duty_cycle_interval_default` (60) | no | declared reporting interval of the duty cycle and the Uncertain fraction (R-08) |
| `alert.silent_on_air_hours` | float | h | `silent_hours_field_min` (0.1) to `silent_hours_field_max` (720) | no | on-air hours that define a silent channel (las horas de silencio); absent means not configured |
| `station_reference_file` | string |  | path of 1 to 255 bytes | no | file holding the station-assignment reference (`station_assignment_reference`); absent means not configured |
| `received_power_limit_dbm.default` | float | dBm | `declared_min_power_floor` (-130) to `declared_min_power_ceiling` (-5) | no | limit that applies to the received channel power, same for every channel without an override (R-12, R-13); absent means no limit is configured |
| `received_power_limit_dbm.channels` | map channel number to float | dBm | keys 1 to 199; values `declared_min_power_floor` to `declared_min_power_ceiling` | no | per-channel overrides of the received-power limit |

## `station_assignment_reference` (versión 1.0)

- **Produce:** «Configuración del sitio» · **Consume:** el comparador de asignaciones
- **Formato:** JSON object in the file named by station_reference_file, UTF-8
- **Límites:** at most `station_entries_max` (199) entries; file size at most `config_file_max_size`
- **Compatibilidad:** Minor: add an optional field. Major: change the meaning of channel or remove a required field.
- **Retención:** n/a

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `schema_version` | string |  | MAJOR.MINOR, major 1 | sí | version of this schema |
| `reference_id` | string |  | 1 to 64 bytes | sí | identifier of the reference, recorded in every report |
| `reference_date` | string |  | ISO 8601 date YYYY-MM-DD | sí | date of the reference |
| `source` | string |  | 1 to 256 bytes (`text_field_max_bytes`) | sí | document or list the reference comes from |
| `entries[].channel` | int |  | 1 to 199, unique within the file | sí | channel number of the FM Technical Plan (centre 88.1 + 0.1 x (channel - 1) MHz) |
| `entries[].station` | string |  | 1 to 256 bytes (`text_field_max_bytes`) | sí | name of the station assigned to the channel; a channel with no entry is unassigned |

## `config_status` (versión 1.0)

- **Produce:** la configuración del sitio · **Consume:** el constructor de registros
- **Formato:** JSON object, UTF-8, one object per change of state and one per scan request
- **Límites:** at most 1024 bytes per message
- **Compatibilidad:** Minor: add an optional field or an enum value at the end. Major: remove or change the meaning of a field.
- **Retención:** n/a

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `config_state` | enum |  | valid \| missing \| rejected_kept_previous \| rejected_defaults | sí | result of the last load of site-config.json |
| `config_sha256` | string |  | 64 lowercase hex characters, empty when no file was read | sí | sha256 of the active configuration file; recorded with every report so the declared values (la potencia mínima recibida declarada, las horas de silencio) are recorded with their configuration |
| `loaded_utc_us` | int64 | us | 0 to 9223372036854775807 | sí | UTC stamp of the last load, same epoch as `time_status` |
| `station_reference_state` | enum |  | valid \| missing \| invalid | sí | state of the station-assignment reference |
| `reference_id` | string |  | 0 to 64 bytes | sí | reference_id of the loaded station reference, empty when none |
| `rejected_code` | string |  | empty or one of E-CFG-001 to E-CFG-004 | sí | code of the error that rejected the last load |

## `capture_block` (versión 1.0)

- **Produce:** el servicio de adquisición · **Consume:** el estimador espectral
- **Formato:** in-memory block: a fixed header followed by `frames_per_dwell` frames of interleaved signed 8-bit I then Q samples (one byte each, no byte order); the header is a JSON-compatible record of the fields below
- **Límites:** one block at most 39 x 262144 B = 10223616 B; 3 blocks per scan period
- **Compatibilidad:** Minor: add an optional header field. Major: change sample format, scaling, order of frames or the meaning or unit of a field.
- **Retención:** n/a

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `scan_id` | int64 | count | 0 to 9223372036854775807, increments by 1 per scan | sí | scan counter since service start |
| `step` | int | count | 1 to 3 | sí | step of the scan (`step_count`) |
| `centre_frequency_hz` | float64 | Hz | 90250000, 97750000 or 105250000 | sí | LO frequency requested (`step1_centre_frequency` to `step3_centre_frequency`) |
| `sample_rate_sps` | float64 | sps | `sample_rate` (10000000) | sí | complex sample rate |
| `frames` | int | count | `frames_per_dwell` (39) | sí | number of frames in the block |
| `scan_start_utc_us` | int64 | us | as `time_status` utc_us | sí | UTC stamp of the scan start, read once at the start of step 1 from `time_status` |
| `scan_start_sync_state` | enum |  | synced \| unsynced \| stepped | sí | sync_state of `time_status` at that read |
| `rf_amp_db` | float | dB | 0 to 14 | sí | front-end amplifier gain applied (R-23) |
| `lna_db` | float | dB | 0 to 40 | sí | first-stage gain applied (R-23) |
| `baseband_db` | float | dB | 0 to 40 | sí | baseband gain applied (R-23) |
| `agc_enabled` | bool |  | always false | sí | automatic gain control state (R-22, el criterio de R-22) |
| `clip_count` | int | count | 0 to 2 x 39 x 131072 | sí | number of I or Q samples at full scale (-128 or +127) |
| `clipped` | bool |  | true when clip_count >= `clip_sample_count_threshold` | sí | capture flagged clipped (R-24) |
| `dropped_frames` | int | count | 0 to 39 | sí | frames missing from the block (R-26) |
| `overflow_events` | int | count | 0 to 1000000 | sí | host buffer overflow or transfer error events during the capture (R-25) |
| `retune_failed` | bool |  | true when `retune_retry_max` attempts failed | sí | the step was not measured |
| `monotonic_ns` | int64 | ns | 0 to 9223372036854775807 | sí | monotonic clock at the start of the first used sample |

## `acquisition_counters` (versión 1.0)

- **Produce:** el servicio de adquisición · **Consume:** el constructor de registros
- **Formato:** JSON object, UTF-8, one per scan
- **Límites:** at most 512 bytes per message; 1 per scan period
- **Compatibilidad:** Minor: add an optional field. Major: remove or change the meaning of a field.
- **Retención:** n/a

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `scan_id` | int64 | count | as `capture_block` | sí | scan counter |
| `overflow_count` | int | count | 0 to 1000000 | sí | sum of overflow_events of the scan (R-27) |
| `dropped_frame_count` | int | count | 0 to 117 | sí | sum of dropped_frames of the scan (R-27) |
| `clipped_captures` | int | count | 0 to 3 | sí | number of captures flagged clipped |
| `retune_failures` | int | count | 0 to 3 | sí | number of steps not measured |
| `scan_late` | bool |  | true when the scan lasted more than `scan_late_threshold` | sí | scan flagged late |
| `scan_duration_s` | float | s | 0 to 60 | sí | wall time from scan start to the last capture end |
| `records_flag_scan` | bool |  | true when overflow_count or dropped_frame_count is above 0 | sí | every channel record of this scan is flagged and its power value withheld (R-25) |

## `channel_power_scan` (versión 1.0)

- **Produce:** el estimador espectral · **Consume:** el gestor de calibración
- **Formato:** JSON object per scan, UTF-8, header plus an array of 199 channel entries ordered by channel
- **Límites:** at most 199 channel entries; about 40 KB per scan; 1 per scan period
- **Compatibilidad:** Minor: add an optional field. Major: change the unit, the dB reference, the channel order or the meaning of a field.
- **Retención:** n/a

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `scan_id` | int64 | count | as `capture_block` | sí | scan counter |
| `scan_start_utc_us` | int64 | us | as `time_status` | sí | UTC stamp of the scan start copied from `capture_block` |
| `scan_start_sync_state` | enum |  | synced \| unsynced \| stepped | sí | copied from `capture_block` |
| `gains` | object | dB | rf_amp_db 0 to 14, lna_db 0 to 40, baseband_db 0 to 40 | sí | gain state of the scan, copied from `capture_block` |
| `bin_spacing_hz` | float64 | Hz | 2441.40625 | sí | `bin_spacing` |
| `integration_bandwidth_hz` | float64 | Hz | 256347 | sí | `integration_bandwidth`, recorded with every scan (el criterio de R-69) |
| `window` | string |  | Hann | sí | `window_family` |
| `fft_length` | int | count | 4096 | sí | `fft_length` |
| `segments` | int | count | 2495 per step | sí | `segments_per_capture` |
| `frequency_correction_ppm` | float | ppm | -100 to 100 | sí | correction applied from `estimator_control`; 0 when none |
| `channels[].channel` | int |  | 1 to 199 | sí | channel number |
| `channels[].step` | int |  | 1 to 3 | sí | step in which the channel was measured |
| `channels[].power_dbfs` | float | dBFS | -140 to 3, null when no_data or invalid | sí | uncalibrated channel power over the 105 bins, dB relative to full scale (sample scale `sample_scale`) |
| `channels[].bins_used` | int | count | 98 to 105 | sí | bins summed after the DC mask replacement (105 normally) |
| `channels[].dc_adjacent` | bool |  | true for channels 22, 23, 77, 78, 172, 173 when the DC bins fall in the window | sí | window contains the replaced DC bins; uncertainty `dc_adjacent_uncertainty` applies |
| `channels[].no_data` | bool |  | true when the step was not measured or the block is empty | sí | no power computed |
| `channels[].clipped` | bool |  | copied from `capture_block` of the step | sí | capture clipped |
| `channels[].scan_flagged` | bool |  | copied from `acquisition_counters` records_flag_scan | sí | overflow or dropped frame in the scan |
| `channels[].mapping_error_bound_khz` | float | kHz | 0 to 20 | sí | `mapping_rounding_error` + `frequency_estimate_error_bound` + `frequency_reference_tolerance_100mhz` x f / 100 MHz at the channel frequency |
| `channels[].mapping_limit_exceeded` | bool |  | true when the bound exceeds the limit of «Configuración del sitio» | sí | mapping error bound above the configured limit |

## `spectrum_snapshot` (versión 1.0)

- **Produce:** el estimador espectral · **Consume:** el gestor de calibración
- **Formato:** JSON object per scan: header and three arrays of 819 float32 values, UTF-8
- **Límites:** 3 x 819 x 4 B = 9828 B of values per scan
- **Compatibilidad:** Minor: add an optional field. Major: change point spacing, unit or order.
- **Retención:** n/a

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `scan_id` | int64 | count | as `capture_block` | sí | scan counter |
| `steps[].step` | int |  | 1 to 3 | sí | step |
| `steps[].first_frequency_hz` | float64 | Hz | 86250000 to 105250000 minus 4 MHz | sí | frequency of the first point: step centre - 4 MHz (usable band lower edge) |
| `steps[].point_spacing_hz` | float64 | Hz | 9765.625 | sí | 4 bins averaged: 4 x 2441.40625 Hz |
| `steps[].points_dbfs` | array of float32 | dBFS | 819 values, -140 to 3 | sí | uncalibrated averaged power per point, power of 4 bins summed and referred to a 9765.625 Hz width |

## `estimator_control` (versión 1.0)

- **Produce:** el gestor de calibración · **Consume:** el estimador espectral
- **Formato:** JSON object, UTF-8, sent at start-up and at every change of the calibration record
- **Límites:** at most 256 bytes; on change only
- **Compatibilidad:** Minor: add an optional field. Major: change the sign convention or the unit.
- **Retención:** n/a

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `frequency_correction_ppm` | float | ppm | -100 to 100 | sí | relative frequency error of the SDR reference found at calibration or verification (positive: actual frequency higher than nominal); 0 when none (R-56) |
| `frequency_reference_state` | enum |  | stock_uncorrected \| stock_corrected \| out_of_limit | sí | state of the frequency reference of the device (R-56, el criterio de R-56) |
| `calibration_record_id` | string |  | 0 to 64 bytes | sí | identifier of the calibration record that holds the correction |

## `calibration_record` (versión 1.0)

- **Produce:** el gestor de calibración · **Consume:** el constructor de registros
- **Formato:** JSON object in the file calibration/<record_id>.json, UTF-8; a companion file <record_id>.sha256 holds the sha256 of the JSON file; records are never overwritten or deleted by the node
- **Límites:** file at most `calibration_record_max_size` (65536 bytes)
- **Compatibilidad:** Minor: add an optional field. Major: change the meaning or unit of K, the sign convention, or remove a field.
- **Retención:** all records kept, none deleted by the node unbounded

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `record_id` | string |  | CAL-YYYYMMDD-hhmmss-nn, 1 to 64 bytes | sí | identifier of the calibration (el criterio de R-18) |
| `created_utc_us` | int64 | us | as `time_status` | sí | UTC stamp of the establishment |
| `operator` | string |  | 1 to 256 bytes | sí | person who established it |
| `device` | object |  | sdr_model, sdr_serial, board_id, software_version, each 1 to 128 bytes | sí | hardware and software the calibration belongs to (el criterio de R-18) |
| `configuration` | object |  | config_sha256 (64 hex) and the listing of sample_rate, step centres, gains, fft_length, window, integration_bins | sí | measurement configuration established with this calibration (R-58, el criterio de R-18) |
| `reference_plane` | string |  | 'SDR antenna port connector (SMA female)' | sí | plane at which the power in dBm is stated (R-09, el criterio de R-18) |
| `reference_source` | object |  | name, model, serial, calibration_date (ISO date), certificate_id, traceability_body, level_uncertainty_db_k2, frequency_uncertainty_ppm | sí | traceable source used (R-17, el criterio de R-17, el criterio de R-18) |
| `cable` | object | dB | loss_db, uncertainty_db at each calibration frequency | sí | loss between the source and the reference plane |
| `offsets` | array of {step int, channel int, frequency_hz float64, offset_db float, spread_db float} | dB | 24 entries (`calibration_point_count`) | sí | K = level at the plane in dBm minus power in dBFS, per calibration point |
| `noise_floor_dbfs` | array of 199 float | dBFS | -140 to 0 | sí | receiver noise floor per channel with the port terminated |
| `dynamic_range` | object | dBm | range_low_dbm, range_high_dbm, compression_level_dbm or null, clip_level_dbm or null, sweep table | sí | usable level range and compression behaviour at the deployed gains (R-55, el criterio de R-55) |
| `frequency_reference` | object | ppm | correction_ppm -20 to 20, state stock_uncorrected \| stock_corrected \| out_of_limit, uncertainty_hz | sí | frequency error of the SDR crystal (R-56) |
| `uncertainty` | object | dB | components, expanded_default_db, expanded_dc_adjacent_db, basis text | sí | budget of `expanded_uncertainty_default` and `expanded_uncertainty_dc_adjacent` with the measured interpolation residual (R-11) |
| `validity` | object | mixed | state valid \| expiring \| expired \| invalid \| rejected; verified_until_utc_us; verification_interval_s and expiry_margin_s declared by the operator within the bounds of «Verificación periódica»; last_verification_id | sí | validity state (R-18, el criterio de R-18) |
| `acceptance` | object |  | pass bool and the value of each criterion of `establish_amplitude_calibration` step 9 | sí | result of the acceptance rule |

## `calibrated_channel_power` (versión 1.0)

- **Produce:** el gestor de calibración · **Consume:** el detector de ocupación
- **Formato:** JSON object per scan, UTF-8, header plus an array of 199 channel entries ordered by channel
- **Límites:** 199 entries, about 45 KB per scan; 1 per scan period
- **Compatibilidad:** Minor: add an optional field or an enum value at the end. Major: change the unit, the reference plane or the meaning of a field.
- **Retención:** n/a

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `scan_id` | int64 | count | as `capture_block` | sí | scan counter |
| `scan_start_utc_us` | int64 | us | as `time_status` | sí | scan stamp |
| `calibration_state` | enum |  | valid \| expiring \| expired \| invalid \| none | sí | state of the active calibration at the scan |
| `calibration_record_id` | string |  | 0 to 64 bytes | sí | record used (el criterio de R-29) |
| `verified_until_utc_us` | int64 | us | as `time_status` or null | sí | end of the verification interval |
| `channels[].channel` | int |  | 1 to 199 | sí | channel |
| `channels[].power_dbm` | float | dBm | -140 to 0, null when withheld | sí | calibrated channel power at the reference plane |
| `channels[].uncertainty_db` | float | dB | 0 to 2.5 | sí | expanded half-width uncertainty (k = 2), `expanded_uncertainty_default` or `expanded_uncertainty_dc_adjacent` |
| `channels[].uncertainty_basis` | string |  | 'traceable source <certificate_id>; budget `expanded_uncertainty_default`' or the dc-adjacent form | sí | basis of the uncertainty (R-11, el criterio de R-11) |
| `channels[].withheld_reason` | enum |  | none \| not_demonstrated \| expired \| config_mismatch \| clipped \| scan_flagged \| no_data \| above_range \| invalid | sí | why power_dbm is null; none when released (R-21, R-24, R-25) |
| `channels[].near_noise_floor` | bool |  | true when below the lower end of the usable range | sí | power at or below the noise-limited end of the range, released with its flag |
| `channels[].dc_adjacent` | bool |  | copied from `channel_power_scan` | sí | `expanded_uncertainty_dc_adjacent` applies |
| `channels[].noise_floor_dbm` | float | dBm | -140 to -60 | sí | receiver noise floor of the channel with the offset applied (input of the detector) |

## `calibrated_spectrum` (versión 1.0)

- **Produce:** el gestor de calibración · **Consume:** el constructor de registros
- **Formato:** JSON object per scan: header and three arrays of 819 float32 values, UTF-8
- **Límites:** 9828 B of values per scan
- **Compatibilidad:** Minor: add an optional field. Major: change spacing, unit or order.
- **Retención:** n/a

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `scan_id` | int64 | count | as `capture_block` | sí | scan counter |
| `steps[].step` | int |  | 1 to 3 | sí | step |
| `steps[].first_frequency_hz` | float64 | Hz | as `spectrum_snapshot` | sí | frequency of the first point |
| `steps[].point_spacing_hz` | float64 | Hz | 9765.625 | sí | point spacing |
| `steps[].points_dbm` | array of float32 | dBm | 819 values, -140 to 0, null array when withheld | sí | calibrated power per point, offset of the nearest calibration frequency applied |
| `withheld_reason` | enum |  | as `calibrated_channel_power` | sí | reason the arrays are null |

## `occupancy_scan` (versión 1.0)

- **Produce:** el detector de ocupación · **Consume:** el comparador de asignaciones
- **Formato:** JSON object per scan, UTF-8, header plus an array of 199 channel entries ordered by channel
- **Límites:** 199 entries, about 70 KB per scan; 1 per scan period
- **Compatibilidad:** Minor: add an optional field or an enum value at the end. Major: change the meaning of a state, the unit or the rule that sets a reason.
- **Retención:** n/a

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `scan_id` | int64 | count | as `capture_block` | sí | scan counter |
| `scan_start_utc_us` | int64 | us | as `time_status` | sí | scan stamp |
| `calibration_state` | enum |  | as `calibrated_channel_power` | sí | copied from `calibrated_channel_power` |
| `noise_reference_dbm` | array of 3 object {step, noise_dbm float, reliable bool} | dBm | -140 to -40 | sí | noise reference of each step, in dBm per 256.347 kHz window |
| `noise_floor_median_dbm` | float | dBm | -140 to -40, null when no reference is reliable | sí | median over the 199 channels of the noise reference with the stored shape (input of the drift alert R-39) |
| `thresholds` | object | dB | occupied_excess_db 1.5, free_excess_db 1.0, hysteresis_db 0.5, release_margin_db 10 | sí | values in force (`occupied_threshold_excess` to `hysteresis`, `release_margin`) |
| `channels[].channel` | int |  | 1 to 199 | sí | channel |
| `channels[].state` | enum |  | Occupied \| Free \| Uncertain | sí | released occupancy state (R-03) |
| `channels[].reason` | enum |  | occupied_isolated \| occupied_own_carrier \| occupied_hysteresis \| free_released \| uncertain_between_thresholds \| uncertain_adjacent_leakage \| uncertain_not_configured \| uncertain_margin_below_10db \| uncertain_calibration \| uncertain_power_withheld \| uncertain_scan_flagged \| uncertain_no_data \| uncertain_noise_unreliable \| uncertain_input_invalid | sí | rule that gave the state |
| `channels[].validity` | enum |  | valid \| not_valid | sí | occupancy validity (R-07): not_valid when calibration, scan flags, data or noise reference are not valid |
| `channels[].power_dbm` | float | dBm | -140 to 0, null when withheld | sí | calibrated channel power copied from `calibrated_channel_power` (input of the state, R-30) |
| `channels[].excess_db` | float | dB | -20 to 100, null when not computed | sí | channel power minus its noise reference (dB, input of the state) |
| `channels[].noise_dbm` | float | dBm | -140 to -40, null when no reliable reference | sí | noise reference of the channel |
| `channels[].threshold_dbm` | float | dBm | -140 to -40, null when not computed | sí | detection threshold = noise reference + `occupied_threshold_excess` (R-59) |
| `channels[].declared_min_power_dbm` | float | dBm | -130 to -5, null when not configured | sí | declared minimum received power from `site_config` (la potencia mínima recibida declarada) |
| `channels[].release_margin_db` | float | dB | -100 to 100, null when not computed | sí | declared minimum power minus noise reference (R-06, el criterio de R-06) |
| `channels[].threshold_not_above_declared` | bool |  | true when threshold_dbm <= declared_min_power_dbm | sí | detection threshold did not exceed the declared minimum received power (R-59) |
| `channels[].own_carrier_ratio_db` | float | dB | -60 to 60, null when not computed | sí | inner band density over flank density (`own_carrier_ratio_min`), null when no neighbour looks occupied |

## `duty_cycle_report` (versión 1.0)

- **Produce:** el detector de ocupación · **Consume:** el comparador de asignaciones
- **Formato:** JSON object per closed interval, UTF-8, an array of 199 channel entries
- **Límites:** 199 entries, about 25 KB per interval; 1 per interval
- **Compatibilidad:** Minor: add an optional field. Major: change the formula or unit of a field.
- **Retención:** n/a

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `interval_start_utc_us` | int64 | us | a multiple of the interval length from 1970-01-01T00:00:00Z | sí | start of the declared reporting interval |
| `interval_min` | int | min | 1 to 1440 | sí | interval length from `site_config` (default `duty_cycle_interval_default`) |
| `partial` | bool |  | true when the node started or the interval length changed inside the interval | sí | interval shorter than declared |
| `time_flag` | bool |  | true when sync_state was unsynced or stepped during the interval | sí | stamps of the interval are not reliable (E-DET-004) |
| `channels[].channel` | int |  | 1 to 199 | sí | channel |
| `channels[].n_scans` | int | count | 0 to 14400 | sí | scans of the interval |
| `channels[].n_occupied` | int | count | 0 to 14400 | sí | scans with state Occupied |
| `channels[].n_free` | int | count | 0 to 14400 | sí | scans with state Free |
| `channels[].n_uncertain` | int | count | 0 to 14400 | sí | scans with state Uncertain |
| `channels[].duty_cycle` | float | % | 0 to 100, null when n_occupied + n_free is 0 | sí | 100 x n_occupied / (n_occupied + n_free) (R-08) |
| `channels[].uncertain_fraction` | float | % | 0 to 100 | sí | 100 x n_uncertain / n_scans (R-08) |

## `validation_record` (versión 1.0)

- **Produce:** el gestor de calibración · **Consume:** el constructor de registros
- **Formato:** JSON object in the file validation/<validation_id>.json, UTF-8; a companion file <validation_id>.sha256 holds its sha256; never overwritten or deleted by the node
- **Límites:** file at most `validation_record_max_size` (65536 bytes)
- **Compatibilidad:** Minor: add an optional field. Major: change the meaning of a result or the sign of a difference.
- **Retención:** all records kept, none deleted by the node unbounded

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `validation_id` | string |  | VAL-YYYYMMDD-hhmmss-nn, 1 to 64 bytes | sí | identifier of the verification |
| `created_utc_us` | int64 | us | as `time_status` | sí | UTC stamp of the verification |
| `operator` | string |  | 1 to 256 bytes | sí | person who carried it out |
| `calibration_record_id` | string |  | 1 to 64 bytes | sí | calibration verified |
| `independent_reference` | object |  | name, model, serial, calibration_date, certificate_id, traceability_body, traceability_chain_id, level_uncertainty_db_k2 (at most `independent_reference_uncertainty_max`) | sí | independent reference and its uncertainty (R-60, el criterio de R-60) |
| `independence` | object |  | serial_differs, certificate_differs, chain_differs, operator_attests_no_common_standard (all bool, all must be true) | sí | proof that the reference differs from the establishing reference (R-20, el criterio de R-20) |
| `measurements` | array of {channel int, level_dbm float, power_dbm float, difference_db float} | dB | `verification_channel_count` x `verification_levels_per_channel` = 12 entries | sí | calibrated power minus the reference level at the plane |
| `measurement_uncertainty_db` | float | dB | 0 to 2, `verification_measurement_uncertainty` | sí | expanded uncertainty of one difference |
| `frequency` | object | ppm | correction_ppm_now -100 to 100, within `frequency_correction_limit` or out_of_limit | sí | crystal frequency error measured at the verification (R-56) |
| `result` | enum |  | pass \| fail \| inconclusive | sí | verdict of `verify_amplitude_correction` |
| `validity_update` | object | mixed | state valid \| invalid, verified_until_utc_us or null | sí | new validity written to `calibration_validity` |

## `calibration_validity` (versión 1.0)

- **Produce:** el gestor de calibración · **Consume:** el motor de alertas
- **Formato:** JSON object in the file calibration/active.json, UTF-8, written atomically; one writer (el gestor de calibración)
- **Límites:** at most 1024 bytes
- **Compatibilidad:** Minor: add an optional field. Major: change the meaning of a state or a time.
- **Retención:** n/a

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `record_id` | string |  | 1 to 64 bytes | sí | active calibration record |
| `state` | enum |  | valid \| expiring \| expired \| invalid \| none | sí | as `calibrated_channel_power` calibration_state |
| `verified_until_utc_us` | int64 | us | as `time_status` or null | sí | last passing verification (or the establishment) plus verification_interval_s |
| `verification_interval_s` | int | s | `verification_interval_min` (345600) to `verification_interval_max` (3456000) | sí | declared verification interval (el intervalo de verificación y su margen) |
| `expiry_margin_s` | int | s | `expiry_margin_min` (3600) to `expiry_margin_max` (604800) and below the interval | sí | declared expiry margin (el intervalo de verificación y su margen, R-38) |
| `last_verification_id` | string |  | 0 to 64 bytes | sí | last verification |

## `assignment_comparison_scan` (versión 1.0)

- **Produce:** el comparador de asignaciones · **Consume:** el constructor de registros
- **Formato:** JSON object per scan, UTF-8, header plus an array of 199 channel entries ordered by channel; it carries the whole content of `occupancy_scan` for each channel so the record builder needs one input per channel
- **Límites:** 199 entries, about 90 KB per scan; 1 per scan period
- **Compatibilidad:** Minor: add an optional field. Major: change the meaning of a comparison value or the mapping table.
- **Retención:** n/a

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `scan_id` | int64 | count | as `capture_block` | sí | scan counter |
| `scan_start_utc_us` | int64 | us | as `time_status` | sí | scan stamp |
| `reference_state` | enum |  | valid \| missing \| invalid | sí | state of the station-assignment reference from `config_status` |
| `reference_id` | string |  | 0 to 64 bytes | sí | identifier of the reference used; recorded in every report (R-16, el criterio de R-16) |
| `reference_used` | bool |  | true when reference_state is valid | sí | the reference was used for this scan |
| `channels[].channel` | int |  | 1 to 199 | sí | channel |
| `channels[].occupancy` | object | mixed | the entry of `occupancy_scan` of the channel (state, reason, validity, power, excess, noise, threshold, declared minimum, margin, flags) | sí | released occupancy state with its inputs |
| `channels[].assigned` | bool |  | true, false, null when the reference is not valid | sí | the channel has an entry in the reference |
| `channels[].station` | string |  | 0 to 256 bytes, empty when unassigned or not valid | sí | station name of the entry |
| `channels[].comparison` | enum |  | consistent \| unassigned-occupied \| assigned-free \| indeterminate | sí | result of the comparison (R-15) |

## `scan_header` (versión 1.0)

- **Produce:** el constructor de registros · **Consume:** el historial en memoria
- **Formato:** JSON object per scan, UTF-8; the content that is constant for all channels of a scan, so channel records stay small
- **Límites:** at most `scan_header_max_size` (4096 bytes) per message; 1 per scan
- **Compatibilidad:** Minor: add an optional field. Major: remove or rename a field, change a unit or the meaning of a field.
- **Retención:** n/a

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `schema_version` | string |  | MAJOR.MINOR, major 1 | sí | version of this schema |
| `node_id` | string |  | as `site_config` | sí | identifier of the node |
| `scan_id` | int64 | count | as `capture_block` | sí | scan counter |
| `scan_start_utc_us` | int64 | us | as `time_status` | sí | UTC stamp of the scan start |
| `resolution_us` | int | us | 1 | sí | resolution of the stamp (`timestamp_resolution`), recorded with every scan (el criterio de R-28) |
| `sync_state` | enum |  | synced \| unsynced \| stepped | sí | time quality of the stamp |
| `evidence_label` | string |  | `evidence_label` | sí | screening-evidence label (R-32) |
| `acquisitions` | array of 3 objects {step, centre_frequency_hz, sample_rate_sps, rf_amp_db, lna_db, baseband_db, agc_enabled, clipped, clip_count, dropped_frames, overflow_events, retune_failed} | mixed | as `capture_block` | sí | gain settings and amplifier state of each acquisition with its flags (R-23, R-24, R-25) |
| `calibration` | object | mixed | record_id, state valid \| expiring \| expired \| invalid \| none, verified_until_utc_us | sí | calibration record in force (R-18, R-29) |
| `frequency_reference` | object | mixed | state stock_uncorrected \| stock_corrected \| out_of_limit, correction_ppm | sí | frequency-reference state of the device (R-56) |
| `estimator` | object | mixed | fft_length 4096, window Hann, bin_spacing_hz 2441.40625, integration_bandwidth_hz 256347, segments 2495 | sí | estimator configuration, including the integration bandwidth (el criterio de R-69) |
| `configuration` | object | mixed | config_sha256, config_state, reference_id, reference_state, location {country, city, place}, received_power_limit_state configured \| not_configured | sí | site configuration in force and the location entered by the user (R-70) |
| `thresholds` | object | dB | occupied_excess_db, free_excess_db, hysteresis_db, release_margin_db | sí | detector values in force |

## `channel_record` (versión 1.0)

- **Produce:** el constructor de registros · **Consume:** el historial en memoria
- **Formato:** JSON object per channel per scan, UTF-8; 199 per scan; serialized in memory by «Historial en memoria» and in the report file by «Escritor de informes»
- **Límites:** at most `channel_record_max_size` (1024 bytes) per record; 199 per scan
- **Compatibilidad:** Minor: add an optional field. Major: remove, rename or change the unit or meaning of a field, or the meaning of an enum value.
- **Retención:** n/a

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `scan_id` | int64 | count | as `capture_block` | sí | scan counter, joins the record to its scan header |
| `channel` | int |  | 1 to 199 | sí | channel number |
| `frequency_hz` | float64 | Hz | 88100000 to 107900000 | sí | channel centre 88.1 MHz + 0.1 MHz x (channel - 1) |
| `step` | int |  | 1 to 3 | sí | step of the acquisition, names the entry of acquisitions in the header (gain state, R-23) |
| `power` | object | mixed | value_dbm (-140 to 0 or null), uncertainty_db (0 to 2.5), uncertainty_basis (text), withheld_reason (as `calibrated_channel_power`), near_noise_floor, dc_adjacent, calibration_record_id, gain {rf_amp_db, lna_db, baseband_db} | sí | calibrated power at the SDR antenna port with its half-width uncertainty and basis (R-09, R-11) and the gain state and calibration record that produced it (R-29) |
| `limit` | object | mixed | state configured \| not_configured, limit_dbm (-130 to -5 or null), comparison within_limit \| outside_limit \| indeterminate \| not_configured \| unavailable | sí | limit that applies or the recorded absence of one, and the comparison (R-12, R-13, R-14) |
| `occupancy` | object | mixed | state, reason, validity (as `occupancy_scan`), detected bool, power_dbm, noise_dbm, excess_db, threshold_dbm, declared_min_power_dbm or null, release_margin_db or null, threshold_not_above_declared | sí | released occupancy state with every input of the decision (R-03, R-30, R-59) |
| `assignment` | object | mixed | assigned bool or null, station text, comparison consistent \| unassigned-occupied \| assigned-free \| indeterminate, reference_id | sí | comparison with the station-assignment reference (R-15) |
| `mapping` | object | kHz | error_bound_khz, limit_exceeded bool | sí | channel-mapping error bound and flag (R-50) |
| `screening_evidence` | bool |  | always true | sí | the record is screening evidence, not a compliance determination (R-32) |

## `health_record` (versión 1.0)

- **Produce:** el constructor de registros · **Consume:** el motor de alertas, el supervisor
- **Formato:** JSON object, one per full-band scan, UTF-8; also sent as a liveness message when no scan runs
- **Límites:** at most `health_record_max_size` (1024 bytes); 1 per scan period
- **Compatibilidad:** Minor: add an optional field. Major: remove or change the meaning of a count.
- **Retención:** n/a

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `scan_id` | int64 | count | as `capture_block`, null when no scan ran | sí | scan counter |
| `utc_us` | int64 | us | as `time_status` | sí | UTC stamp of the record |
| `node_id` | string |  | as `site_config` | sí | node |
| `overflow_count` | int | count | 0 to 1000000 | sí | receive-overflow count of the scan (R-27) |
| `dropped_frame_count` | int | count | 0 to 117 | sí | dropped-frame count of the scan (R-27) |
| `records_published` | int | count | 0 to 199 | sí | number of channel records published for the scan (R-27) |
| `clipped_captures` | int | count | 0 to 3 | sí | captures flagged clipped |
| `retune_failures` | int | count | 0 to 3 | sí | steps not measured |
| `scan_late` | bool |  | true when the scan lasted more than 7 s | sí | scan flagged late |
| `estimator_late` | bool |  | true when the estimator exceeded its allocation | sí | estimator flagged late |
| `calibration_state` | enum |  | valid \| expiring \| expired \| invalid \| none | sí | state of the active calibration |
| `config_state` | enum |  | valid \| missing \| rejected_kept_previous \| rejected_defaults | sí | state of the site configuration |
| `sync_state` | enum |  | synced \| unsynced \| stepped | sí | time quality |
| `noise_floor_median_dbm` | float | dBm | -140 to -40 or null | sí | median noise floor of the scan (input of the drift alert) |
| `inconsistent` | bool |  | true when the inputs of the scan disagree | sí | scan discarded (E-REC-002) |
| `screening_evidence` | bool |  | always true | sí | screening evidence label flag |

## `history_bins_response` (versión 1.0)

- **Produce:** el historial en memoria · **Consume:** el servicio web
- **Formato:** JSON object, UTF-8; the answer to a query with channels (1 to 199), from_utc_us, to_utc_us and resolution_s (a multiple of `bin_length`); read only
- **Límites:** response at most 40000 bins; 1 query at a time per client
- **Compatibilidad:** Minor: add an optional field. Major: change a unit, the meaning of a count or the bin definition.
- **Retención:** 744 h

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `history_start_utc_us` | int64 | us | as `time_status` | sí | time the history started (process start or clear): earlier time is not available |
| `bin_s` | int | s | 60 to 3600 | sí | length of the returned bins |
| `channels[].channel` | int |  | 1 to 199 | sí | channel |
| `channels[].bins[]` | array of {start_utc_us, mean_power_dbm or null, max_power_dbm or null, n_scans, n_released, n_occupied, n_free, n_uncertain, n_assigned_free, n_unassigned_occupied, withheld_reason} | mixed | at most 2000 bins per channel and 40000 in all | sí | aggregated history; power only from released values (R-45); a bin with no released value shows null and the most frequent withheld reason |

## `history_series_response` (versión 1.1)

- **Produce:** el historial en memoria · **Consume:** el motor de alertas
- **Formato:** JSON object, UTF-8; the per-scan series or the latest scan; read only; an optional time-range request (from_utc_us, to_utc_us) selects the series entries returned
- **Límites:** at most 446400 series entries without a range request and at most 20000 entries with one; one latest scan of about 0.23 MB
- **Compatibilidad:** Minor: add an optional field. Major: change a unit or the meaning of a field.
- **Retención:** 744 h

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `request.from_utc_us` | int64 | us | as `time_status` | no | added in v1.1: first UTC stamp wanted; absent means the start of the history |
| `request.to_utc_us` | int64 | us | as `time_status`, not before from_utc_us | no | added in v1.1: last UTC stamp wanted; absent means the latest scan; a range request returns at most 20000 entries (33.3 h of scans at 6 s) and the oldest are dropped first |
| `history_start_utc_us` | int64 | us | as `time_status` | sí | time the history started |
| `series[]` | array of {utc_us, noise_floor_median_dbm or null, overflow_count, dropped_frame_count, records_published, calibration_state, sync_state} | mixed | at most 446400 entries | sí | per-scan series for the drift alert, the node status and the sensor-offline alert |
| `latest_scan` | object | mixed | `scan_header` header, 199 `channel_record` records, `calibrated_spectrum` spectrum, `health_record` health of the latest scan, or null | sí | latest complete scan for the spectrum and status views (R-42, R-44) |

## `report_header` (versión 1.0)

- **Produce:** el escritor de informes · **Consume:** el servicio web
- **Formato:** JSON object in reports/<run_id>/header.json, UTF-8, written atomically (temporary file then rename); rewritten at the start and at the close of the run
- **Límites:** at most `report_header_max_size` (8192 bytes)
- **Compatibilidad:** Minor: add an optional field. Major: remove or rename a field, or change the meaning of a time or the unit of a field.
- **Retención:** 30 d

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `run_id` | string |  | RUN-YYYYMMDD-hhmmss-nn | sí | identifier of the screening run |
| `schema_version` | string |  | MAJOR.MINOR, major 1 | sí | version of the report format |
| `evidence_label` | string |  | `evidence_label` | sí | screening-evidence label (R-32) |
| `node_id` | string |  | as `site_config` | sí | node |
| `location` | object |  | country, city, place (text) or 'not configured' | sí | location information entered by the user (R-62, R-70) |
| `location_state` | enum |  | entered \| not_configured | sí | whether the user entered a location |
| `run_mode` | enum |  | timed \| continuous | sí | run mode from `site_config` |
| `planned_duration_min` | int | min | 10 to 43200 or null | sí | configured record time (R-74) |
| `run_start_utc_us` | int64 | us | as `time_status` | sí | UTC stamp of the first scan (date and time record, R-62) |
| `run_end_utc_us` | int64 | us | as `time_status` or null while the run is open | sí | UTC stamp of the end of the run |
| `execution_time_s` | float | s | 0 to 2592000 or null while open | sí | execution time of the run (R-62) |
| `interrupted` | bool |  | true when the run was closed after a power loss or crash | sí | run closed by recovery (end taken from the progress file) |
| `scans_saved` | int | count | 0 to 432000 | sí | scans written |
| `software_version` | string |  | 1 to 128 bytes | sí | software package version |
| `configuration` | object |  | config_sha256, reference_id, calibration_record_id | sí | configuration and calibration in force at the start |
| `segments` | array of {file, first_scan_id, last_scan_id, rows, sha256, state closed \| open \| incomplete \| corrupt \| deleted} | mixed | at most 432 segments per run | sí | manifest of the segment files with their checksums |

## `report_lines` (versión 1.0)

- **Produce:** el escritor de informes · **Consume:** el servicio web
- **Formato:** text file reports/<run_id>/scans-<YYYYMMDDThhmmZ>.csv, UTF-8, one line per record, comma separated, '.' decimal point, no quoting characters inside text (commas and line breaks in text are replaced by a space); the first line of a segment starts with # and names the columns of each line type; line types S (scan), C (channel), H (health)
- **Límites:** segment of 3600 s: 600 scans, about 25 MB; line at most 4096 bytes
- **Compatibilidad:** Minor: add a column at the end of a line type. Major: reorder or remove a column, or change a unit.
- **Retención:** 30 d

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `S line` | scan_id, utc_us, resolution_us, sync_state, calibration_record_id, calibration_state, rf_amp_db, lna_db, baseband_db for steps 1 to 3 (9 values), agc_enabled, clipped flags (3), clip counts (3), dropped frames (3), overflow events (3), config_sha256, reference_id, thresholds, evidence flag | mixed | about 1500 bytes | sí | constant data of the scan; the gain state and calibration record of each channel row are resolved through its step and scan_id (R-29) |
| `C line` | scan_id, channel, step, power_dbm, uncertainty_db, withheld_reason, near_noise_floor, dc_adjacent, limit_state, limit_dbm, limit_comparison, state, reason, validity, detected, excess_db, noise_dbm, threshold_dbm, declared_min_dbm, release_margin_db, threshold_not_above_declared, assigned, station_index, assignment_comparison, mapping_bound_khz, mapping_exceeded, evidence flag | mixed | about 200 bytes, 199 per scan | sí | one channel record (`channel_record`) with every input of the occupancy state (R-30, R-59); station names are in the station table of the header |
| `H line` | scan_id, overflow_count, dropped_frame_count, records_published, clipped_captures, retune_failures, scan_late, estimator_late, calibration_state, config_state, sync_state, noise_floor_median_dbm, inconsistent, evidence flag | mixed | about 300 bytes | sí | health record of the scan (R-27) |
| `duty-cycle file` | reports/<run_id>/intervals.csv, one line per channel and closed interval with the fields of `duty_cycle_report` | mixed | 199 lines per interval | sí | duty cycle and Uncertain fraction per interval (R-08) |

## `report_listing` (versión 1.0)

- **Produce:** el escritor de informes · **Consume:** el servicio web
- **Formato:** JSON object, UTF-8, built on request from the headers and manifests; read only
- **Límites:** at most 10000 file entries
- **Compatibilidad:** Minor: add an optional field. Major: change the meaning of a field.
- **Retención:** n/a

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `runs[].run_id` | string |  | RUN-... | sí | run |
| `runs[].run_start_utc_us` | int64 | us | as `time_status` | sí | start of the run |
| `runs[].run_end_utc_us` | int64 | us | as `time_status` or null | sí | end of the run, null while open |
| `runs[].files[]` | array of {path, bytes, sha256, state} | mixed | at most 10000 entries in all | sí | files available for download with their size and checksum |

## `storage_status` (versión 1.0)

- **Produce:** el escritor de informes · **Consume:** el motor de alertas, el supervisor
- **Formato:** JSON object, UTF-8, sent on every change of state and once per scan
- **Límites:** at most 512 bytes
- **Compatibilidad:** Minor: add an optional field or an enum value at the end. Major: change the meaning of a state or a unit.
- **Retención:** n/a

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `report_state` | enum |  | saving \| degraded \| stopped \| closed \| idle | sí | state of the report writer: degraded after a write failure, stopped when no space remains (`E-RPT-001`, `E-RPT-003`) |
| `history_state` | enum |  | running \| reduced \| restarted \| empty_start \| disk_guard_failed | sí | state of the history store reported by «Historial en memoria» (`E-HIS-001` to `E-HIS-004`) |
| `pending_scans` | int | count | 0 to 10 (`pending_scans_max`) | sí | scans held in the pending buffer |
| `free_space_gb` | float | GB | 0 to 64 | sí | free space on the card at the last check |
| `last_flush_utc_us` | int64 | us | as `time_status` or null | sí | UTC stamp of the last flushed scan |

## `alert_event` (versión 1.0)

- **Produce:** el motor de alertas · **Consume:** el servicio web
- **Formato:** JSON object, UTF-8; one object per alert raised or cleared
- **Límites:** at most `alert_event_size` (512 bytes) per event
- **Compatibilidad:** Minor: add an optional field or an optional evidence entry. Major: remove or re-type a field, change the meaning of a type or add a value to a closed enum that consumers must handle.
- **Retención:** 1000 count

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `alert_id` | int64 | count | 1 to 9223372036854775807, increasing since the engine start | sí | identifier of the alert; the same id appears in the raised and the cleared event |
| `type` | enum |  | channel_silent \| unexpected_occupancy \| sensor_offline \| calibration_not_demonstrated \| noise_floor_drift | sí | alert type (R-34, R-36, R-37, R-38, R-39); no type exists for received power (R-40) |
| `channel` | int or null |  | 1 to 199; null for sensor_offline, calibration_not_demonstrated and noise_floor_drift | sí | channel the alert is about |
| `state` | enum |  | raised \| cleared | sí | state of the alert at this event |
| `raised_utc_us` | int64 | us | as `time_status` | sí | UTC time the alert was raised |
| `raised_sync_state` | enum |  | synced \| unsynced \| stepped | sí | sync_state of `time_status` when it was raised (a stamp of an unsynced clock is not reliable) |
| `cleared_utc_us` | int64 or null | us | as `time_status`; null while raised | sí | UTC time the alert was cleared |
| `clear_reason` | enum |  | none \| condition_ended \| config_changed \| history_restarted | sí | why the alert was cleared; none while raised |
| `station` | text or null |  | 0 to 256 bytes, null for alerts without a station | sí | station assigned to the channel in the reference (silence alert) |
| `reference_id` | text or null |  | 1 to 64 bytes | sí | identifier of the station-assignment reference used (silence and unexpected-occupancy alerts) |
| `evidence` | object | mixed | channel_silent: {credit_hours 0 to 720 h, configured_hours 0.1 to 720 h, prior_duty_cycle 90 to 100 %, run_start_utc_us}; unexpected_occupancy: {consecutive_scans 3 to 255 count, scan_id, excess_db}; sensor_offline: {seconds_since_health_point 18 to 86400 s, last_health_utc_us or null}; calibration_not_demonstrated: {calibration_state, withheld_reasons list, verified_until_utc_us or null, expiry_margin_s or null}; noise_floor_drift: {shift_db above 6 dB, median_now_dbm, median_reference_dbm, window_min 60} | sí | the values that triggered the alert, so the person can re-check it; a power value appears only when it is released (R-45) |
| `text` | text |  | 1 to 256 bytes (`alert_text_max_bytes`); no word of `forbidden_wording` | sí | fixed-template sentence of the alert; it never states a regulatory finding (R-33) |
| `screening_evidence` | bool |  | always true | sí | the alert is screening evidence, not a determination (R-32, R-33) |

## `alert_status_response` (versión 1.1)

- **Produce:** el motor de alertas · **Consume:** el servicio web
- **Formato:** JSON object, UTF-8; the answer to a read request of the web service; read only
- **Límites:** response at most 0.52 MB (1000 events of 512 bytes plus the rules); 1 query at a time per client
- **Compatibilidad:** Minor: add an optional field. Major: remove or re-type a field or change the meaning of a status.
- **Retención:** 1000 count

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `sensor` | object {online bool, last_health_point_age_s float or null, last_health_utc_us int64 or null} | mixed | online false while a sensor_offline alert is active; age 0 to 86400 s from the monotonic timer of `watch_health_points`, null before the first health point | sí | added in v1.1: online status and last scan age for the node-status view (R-44); the age is that of the last health point, that is of the last measuring scan |
| `noise_floor_drift` | object {status, shift_db float or null, median_now_dbm float or null, median_reference_dbm float or null, evaluated_utc_us int64 or null} | mixed | status evaluating or insufficient_history; shift_db 0 to 100 dB; the dBm values -140 to -40 | sí | added in v1.1: the current drift value at every evaluation, with or without an alert, for the node-status view (R-44) |
| `engine_start_utc_us` | int64 | us | as `time_status` | sí | time the alert engine started; alerts before it were lost with the volatile memory |
| `evaluated_utc_us` | int64 or null | us | as `time_status`; null before the first scan | sí | time of the last per-scan evaluation |
| `rules[]` | array of {type, status, detail} | mixed | 5 entries; type as `alert_event`; status evaluating \| not_configured \| insufficient_history \| reference_unavailable \| input_missing; detail 0 to 256 bytes | sí | state of each rule, so a rule that cannot run is shown instead of looking quiet (R-34, R-39) |
| `active[]` | array of `alert_event` with state raised | mixed | at most 401 entries (`max_active_alerts`) | sí | alerts in force now (R-46 presentation is «Servicio web») |
| `recent[]` | array of `alert_event`, newest first | mixed | at most 1000 entries (`alert_event_ring`) | sí | raised and cleared events kept in memory |
| `events_dropped` | int | count | 0 to 2147483647 | sí | cleared events dropped from the ring since the engine start (`E-ALR-006`) |
| `late_evaluations` | int | count | 0 to 2147483647 | sí | evaluations that took longer than their allocation (`E-ALR-010`) |
| `screening_evidence` | bool |  | always true | sí | screening evidence label (R-32) |

## `cross_site_comparison` (versión 1.0)

- **Produce:** «Reproducibilidad entre sitios» · **Consume:** «Pruebas»
- **Formato:** JSON object in a file comparison/<comparison_id>.json, UTF-8, kept by the person who runs the repeat; the nodes neither read nor write it
- **Límites:** at most `comparison_record_max_size` (65536 bytes)
- **Compatibilidad:** Minor: add an optional field. Major: remove or re-type a field or change a criterion.
- **Retención:** n/a

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `comparison_id` | string |  | CMP-YYYYMMDD-nn, 1 to 64 bytes | sí | identifier of the comparison |
| `date` | string |  | ISO 8601 date YYYY-MM-DD | sí | date the comparison was made |
| `site_a` | object {node_id, location, package_sha256, config_sha256, calibration_record_id, validation_record_id, report_run_id} | mixed | texts 1 to 256 bytes; hashes 64 hex | sí | identity of the first site |
| `site_b` | object {node_id, location, package_sha256, config_sha256, calibration_record_id, validation_record_id, report_run_id} | mixed | as site_a | sí | identity of the repeat site |
| `identical_items` | object {pass, differences[]} | mixed | pass true or false; differences list of item names | sí | result of the check of `identical_items` (E-REP-001) |
| `points[]` | array of {channel, level_dbm_a, level_dbm_b, difference_db_a, difference_db_b, w_a_db, w_b_db, delta_db, en, agree} | mixed | `cross_site_power_points` = 12 entries; levels -130 to -5 dBm; differences and delta -10 to 10 dB; w 0 to 5 dB; en 0 to 100; agree true or false | sí | the comparison of the differences tables (`validation_record`) point by point |
| `power_summary` | object {agree_count, n_points, share_percent, max_abs_delta_db, hard_limit_exceeded, result} | mixed | agree_count 0 to 12; share 0 to 100 %; result pass or fail or inconclusive | sí | criterion (1) of the rule |
| `frequency` | object {state_a, correction_ppm_a, state_b, correction_ppm_b, within_limit_a, within_limit_b} | mixed | states as `calibration_record` frequency_reference; ppm -100 to 100; within_limit bool (`frequency_correction_limit` = 20 ppm) | sí | the frequency corrections of the two nodes, side by side |
| `screening` | object {site_a {n_occupied, n_occupied_channels, max_channel_share_percent, detection_percent, n_vacant, false_alarm_percent, result}, site_b {same}} | mixed | counts 0 to 10000000; percents 0 to 100; result pass or fail or inconclusive | sí | criterion (2) of the rule: each site against R-04 and R-05 with its own acceptance set |
| `reports` | object {fields_complete_a, fields_complete_b, missing_fields[]} | mixed | bool; list of field names of `report_fields_required` | sí | criterion (3) of the rule |
| `result` | enum |  | agree \| disagree \| inconclusive | sí | agree only when the three criteria pass; inconclusive when a criterion could not be evaluated (E-REP-002 to E-REP-005) |
| `approved_by` | string |  | 0 to 256 bytes | sí | the person who approves the result (la regla de reproducibilidad entre sitios) |

## `supervisor_status` (versión 1.0)

- **Produce:** el supervisor · **Consume:** el servicio web
- **Formato:** JSON object, UTF-8, length-prefixed (`ipc_transport`), published every `status_publish_interval` (1 s) and at every change of state; the same object is the liveness of the supervisor
- **Límites:** at most 2048 bytes
- **Compatibilidad:** Minor: add an optional field or an optional condition name. Major: remove or re-type a field or change the meaning of a node_state.
- **Retención:** n/a

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `liveness_seq` | int64 | count | increasing by 1 at every publication since the boot | sí | a consumer that sees no increase for `status_stale_after` (5 s) shows 'supervisor not answering' |
| `supervisor_utc_us` | int64 | us | as `time_status` | sí | UTC time of the publication |
| `sync_state` | enum |  | synced \| unsynced \| stepped | sí | time quality, as `time_status` |
| `boot_id` | string |  | 1 to 64 bytes | sí | identifier of this boot of the node |
| `node_boot_utc_us` | int64 | us | as `time_status` | sí | time of this boot |
| `unclean_boot` | bool |  | true when the previous stop left no clean-stop marker (E-SUP-006) | sí | the previous run ended without an orderly stop |
| `node_state` | enum |  | starting \| measuring \| measuring_degraded \| not_measuring | sí | state of the node derived by the rules of section 3 of «Supervisión y manejo de errores» |
| `power_released` | bool |  | true \| false | sí | false when the latest scan is flagged or calibration_state is expired, invalid or none: power values are withheld (R-21, R-24, R-25) |
| `processes[]` | array of {name, cmps, state, progress_age_s, restarts_last_24h, last_exit_reason, last_restart_utc_us} | mixed | 5 entries: measure, store_alert, report, web, time; state starting \| running \| restarting \| restart_loop \| stopped; progress_age_s 0 to 86400 s; restarts_last_24h 0 to 100000; last_exit_reason text 0 to 128 bytes; last_restart_utc_us as `time_status` or null | sí | state of each supervised process |
| `conditions[]` | array of {name, value, since_utc_us} | mixed | name in calibration_state \| config_state \| sync_state \| report_state \| history_state \| scan_flagged \| scan_late \| restart_loop \| reboot \| unclean_boot \| thermal; value text 0 to 64 bytes; since as `time_status` | sí | the conditions that make the node degraded, as read from `health_record`, `storage_status` and the process states |
| `reboots_last_24h` | int | count | 0 to 3 (`reboot_limit_per_day`) | sí | reboots ordered by the supervisor in 24 h |
| `hw_watchdog` | enum |  | active \| not_available | sí | whether the hardware watchdog is armed (confirmed by the qualification test) |
| `dropped_messages` | int | count | 0 to 2147483647 | sí | messages dropped by the producers when a consumer was not reachable (E-SUP-009) |
| `screening_evidence` | bool |  | always true | sí | screening evidence label (R-32) |

## `supervisor_log_line` (versión 1.0)

- **Produce:** el supervisor · **Consume:** «Pruebas»
- **Formato:** JSON lines, UTF-8, one object per line, files supervisor/events-<YYYYMMDD>.jsonl on the storage medium; counts and codes only, never a measurement or a record content (R-31)
- **Límites:** a line at most `supervisor_log_line_max` (256 bytes); all files at most `supervisor_log_max_total` (50 MB)
- **Compatibilidad:** Minor: add an optional field or an event name. Major: remove or re-type a field.
- **Retención:** 35 d

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `utc_us` | int64 | us | as `time_status` | sí | time of the event |
| `sync_state` | enum |  | synced \| unsynced \| stepped | sí | time quality |
| `boot_id` | string |  | 1 to 64 bytes | sí | boot the event belongs to |
| `event` | enum |  | boot \| clean_stop \| process_start \| process_exit \| process_hung \| restart \| restart_loop_enter \| restart_loop_exit \| reboot_ordered \| watchdog_reset_seen \| message_invalid \| messages_dropped \| guard_failed \| log_lines_dropped \| thermal_warning \| thermal_throttle \| thermal_cleared \| thermal_unreadable | sí | what happened; a restart is the recorded watchdog restart that el criterio de R-01 excludes |
| `process` | enum |  | supervisor \| measure \| store_alert \| report \| web \| time | sí | process concerned |
| `code` | string |  | E-SUP-001 to E-SUP-009 or a code of another module, 0 to 16 bytes | sí | error code that caused it |
| `detail` | text |  | 0 to 128 bytes | sí | exit status, signal or reason; no record content |

## `web_view_data` (versión 1.0)

- **Produce:** el servicio web · **Consume:** el servicio web
- **Formato:** JSON object, UTF-8, answer to a GET of /api/<view>; produced by the server part of el servicio web and read by the page script that el servicio web itself serves, which draws it; the person sees only the drawn page
- **Límites:** at most 6 MB per answer (28,656 bins of about 200 bytes); one answer per request
- **Compatibilidad:** Minor: add an optional field or an optional entry of data. Major: remove or re-type a field, change a unit, or change which values count as released.
- **Retención:** n/a

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `evidence_label` | string |  | exactly `evidence_label` | sí | screening-evidence label (R-32); the page shows it in a fixed header that cannot be hidden |
| `screening_evidence` | bool |  | always true | sí | the data are screening evidence, not a determination (R-32, R-33) |
| `view` | enum |  | power_map \| spectrum \| stations \| status \| alerts \| reports \| latest_scan | sí | which view the data are for |
| `data_state` | enum |  | ok \| no_data \| insufficient_history \| unavailable | sí | ok when data exist; no_data before the first scan; insufficient_history when the history is shorter than the span asked (history_start_utc_us says from when it exists); unavailable when a source cannot be read (E-WEB-006) |
| `generated_utc_us` | int64 | us | as `time_status` | sí | UTC time the answer was built; every time in a view is UTC |
| `sync_state` | enum |  | synced \| unsynced \| stepped | sí | time quality of the node at that moment; shown beside every time when not synced |
| `node` | object {node_id, location {country, city, place or null}, config_state, calibration_state} | mixed | node_id as `site_config`; texts up to 256 bytes; states as `health_record` | sí | identity and state of the node shown in the page header (R-70) |
| `alerts_summary` | object {active_count, by_type, rules[]} | mixed | active_count 0 to 401; rules as `alert_status_response` rules | sí | alert bar on every view (R-46): the number of active alerts per type and the status of every rule, so a rule that cannot run is visible |
| `history_start_utc_us` | int64 or null | us | as `time_status` | sí | time the history started (`history_bins_response`); earlier time is not available |
| `data` | object | mixed | power_map: {span_h, resolution_s, channels[] {channel, frequency_mhz, station or null, cells[] {start_utc_us, power_dbm or null, max_power_dbm or null, n_scans, n_occupied, n_free, n_uncertain, withheld_reason}}}; spectrum: {scan_id, scan_start_utc_us, points[] {frequency_hz, power_dbm}, markers[] {channel, frequency_mhz, station or null, state, reason, validity, power_dbm or null, uncertainty_db or null, withheld_reason, near_noise_floor, dc_adjacent}}; stations: {span_h, resolution_s, stations[] {channel, station, duty_cycle_percent or null, uncertain_fraction_percent, n_scans, bins[] {start_utc_us, mean_power_dbm or null, duty_cycle_percent or null, uncertain_fraction_percent}}}; status: {online, last_scan_age_s, noise_floor_drift {status, shift_db, median_now_dbm, median_reference_dbm}, overflow {latest, last_24h}, dropped_frames {latest, last_24h}, calibration_state, sync_state, config_state, reference_id, engine_start_utc_us, supervisor {node_state, power_released, processes[], conditions[], unclean_boot, reboots_last_24h, status_age_s}}; alerts: {active[] and recent[] of `alert_event`, rules[]}; reports: {runs[] of `report_listing` with the download path of each file}; latest_scan: {header, records[] of `channel_record` as released, health} | sí | view-specific content; a power value appears only when released; a value not released is null and the flags of the channel are given instead (R-45) |

## `web_request` (versión 1.0)

- **Produce:** el servicio web · **Consume:** el servicio web
- **Formato:** HTTP/1.1 GET or HEAD with a query string, ASCII, at most `web_request_max_bytes` bytes; sent by the page script that el servicio web serves or typed by the person; no body, no cookie, no credential
- **Límites:** request at most `web_request_max_bytes` (8192 bytes); at most `web_concurrent_workers` (8) requests processed at once and `web_request_queue_length` (64) waiting
- **Compatibilidad:** Minor: add an optional query parameter or an optional path. Major: remove a path, re-type a parameter or accept a method other than GET and HEAD.
- **Retención:** n/a

| Campo | Tipo | Unidad | Rango | Obligatorio | Significado |
|---|---|---|---|---|---|
| `method` | enum |  | GET \| HEAD (`web_allowed_methods`) | sí | any other method is refused (E-WEB-001) |
| `path` | string |  | /, /power, /spectrum, /stations, /status, /alerts, /reports, /api/power-map, /api/spectrum, /api/stations, /api/status, /api/alerts, /api/reports, /api/latest-scan, /reports/<run_id>/<file>, /static/<asset> | sí | page, data or file asked for; the pages show the four views of R-41 to R-44 and the alert and report pages |
| `span_h` | int | h | 1, 6 or 24 (`power_map_span_options`); default 24 (`view_span_default`); only /api/power-map | no | span of the power map; the resolution follows `power_map_resolution_options` |
| `stations` | list of text |  | 1 to 10 names (`stations_selected_max`), each equal to a station name of the reference (`station_assignment_reference`), separated by a vertical bar; only /api/stations | no | stations selected for the 24 h power and duty-cycle view; absent selects none and the page asks the person to choose (E-WEB-003 is not raised) |
| `channels` | list of int |  | 1 to 10 numbers (`stations_selected_max`), each 1 to 199; only /api/stations | no | channels selected instead of, or with, station names (a channel with no station is allowed) |
| `scope` | enum |  | bar \| all; only /api/alerts; default all | no | bar returns the active alerts and the rule status for the alert bar; all adds the recent events |
