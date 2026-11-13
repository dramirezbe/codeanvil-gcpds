# Anexo E — Plan de pruebas

Cada requisito tiene al menos una prueba de aceptación (P-nnn). Además hay pruebas de calificación del hardware, de procedimiento, unitarias y de integración. «Umbral» es el valor que la prueba debe cumplir; «casos» son los ejemplos mínimos que deben ejecutarse (nominal, error y borde).

**Importante:** las pruebas de calificación de hardware no se han ejecutado todavía; no hay ningún resultado medido en este documento.

> Los nombres de parámetros, campos, estados y códigos de error se conservan en inglés porque son los identificadores que se implementan en el código y en los archivos. Las descripciones breves de estos anexos mantienen el texto técnico original.

## Pruebas de aceptación (74)

### P-001 · requisito R-01 · ensayo

- **Mide:** interval between consecutive full-band scan start timestamps (maximum over the run) <= 10 s
- **Condición:** over a declared run in the deployment configuration; an interval interrupted by a recorded watchdog restart is excluded
- **Procedimiento:** `scan_cycle`
- **Datos de prueba:** intervals = difference of consecutive scan_start_utc_us over the whole run; expected maximum = 6 s (monotonic schedule), planned limit 7 s
- **Falla si:** the next scan is scheduled from the end of the previous scan (6 + about 5 s = 11 s) instead of from the monotonic schedule
- _nominal:_ 72 h run in the deployment configuration (6 s scan period `scan_period`); take scan_start_utc_us of `scan_header` for every scan → maximum start-to-start interval 6 s plus timer jitter, at most 7 s (`interval_planned_max`), which is <= 10 s
- _error:_ kill the measure process once (E-SUP-001); scans stop until the first scan after the restart (72 s, `recovery_time_process`) → the interval across the restart is excluded only because the supervisor log (`supervisor_log_line`) holds a restart event for it; without that line it counts and the test fails
- _edge:_ delay the start of one scan by 3.9 s (6 + 3.9 = 9.9 s) and then by 4.1 s (10.1 s) → 9.9 s passes (<= 10); 10.1 s fails

### P-002 · requisito R-02 · inspección

- **Mide:** share of full-band scans that carry a record for every channel of the FM Technical Plan >= 100 %
- **Condición:** capture and scan plan declared for the deployment configuration; channels 1 to 199
- **Procedimiento:** `scan_cycle`
- **Datos de prueba:** for each scan_id count C lines and compare the channel numbers with 1..199 and frequency 88.1 + 0.1 x (n - 1) MHz; expected 199 distinct channels
- **Falla si:** a channel at the end of a step (60 or 135) is dropped, or a step boundary shifts a channel by one
- _nominal:_ inspect the saved report of a 1 h segment (600 scans) → every scan has 199 C lines, channels 1 to 199, 88.1 to 107.9 MHz at 100 kHz steps: 100 %
- _error:_ inject a retune failure in step 2 (E-ACQ-003) for one scan → the scan still has 199 C lines; the channels of the step are present with the flag and state Uncertain, not missing: 100 %
- _edge:_ scan with a failed process restart in the middle (health record only, E-REC-001) → a scan with no records is not a full-band scan (health line only); every full-band scan has 199 lines

### P-003 · requisito R-03 · inspección

- **Mide:** share of channel-scan records that carry a released state of Occupied, Free or Uncertain >= 100 %
- **Condición:** saved screening reports of the validation set and of the field run
- **Procedimiento:** `classify_channels`
- **Datos de prueba:** count lines whose state is not one of the three values or is empty; expected 0 of 119,400 lines in 600 scans
- **Falla si:** a withheld channel is written with an empty state or with Free by default
- _nominal:_ inspect all C lines of a 1 h segment → every line has state in {Occupied, Free, Uncertain} with a reason and validity: 100 %
- _error:_ throttle the host so one scan has an overflow (E-ACQ-002) → all 199 records of the scan carry state Uncertain with reason uncertain_scan_flagged: still a released state, 100 %
- _edge:_ scan with every channel withheld (calibration expired) → all 199 are Uncertain with reason uncertain_calibration; none is blank or null

### P-004 · requisito R-04 · ensayo

- **Mide:** detection probability on ground-truth-occupied observations with SNR at least 0 dB >= 95 %
- **Condición:** acceptance set only, at least 20 observations from at least 10 distinct channels, no channel above 20% of the denominator, independent reference
- **Procedimiento:** `classify_channels`
- **Datos de prueba:** SNR = 10 log10((P_signal - P_noise)/P_noise) with the injected carrier at noise + 3.01 dB (excess 3.01 dB, SNR 0 dB) on 10 channels, 2 observations each; the detector threshold is 1.5 dB excess (`occupied_threshold_excess`)
- **Falla si:** the occupied threshold applied in dB of power instead of dB over the noise reference, or the noise reference biased by +1.5 dB so that an SNR-0 carrier is missed
- _nominal:_ acceptance set of at least 20 occupied observations with SNR >= 0 dB from at least 10 channels, none above 20 % of the denominator, annotated with an independent reference → detection share >= 95 %; the expected detection is 99.87 % (`expected_detection_probability_snr0`), so 20 of 20 (19 of 20 is still 95 %)
- _error:_ same set with a scan flagged for overflow among the observations (E-ACQ-002) → flagged scans give Uncertain, not Occupied; they count as not detected: the share falls; the set must be replaced or enlarged (E-REP-005 rules)
- _edge:_ exactly 20 observations with 19 detected, then 18 detected → 19 of 20 = 95 % passes (>= 95); 18 of 20 = 90 % fails

### P-005 · requisito R-05 · ensayo

- **Mide:** false-alarm probability on ground-truth-vacant observations <= 5 %
- **Condición:** same acceptance set; vacancy confirmed by an independent reference
- **Procedimiento:** `classify_channels`
- **Datos de prueba:** terminated input at the SDR port with the noise floor of the receiver; vacant means no signal above the noise reference by 1.5 dB confirmed by the reference
- **Falla si:** the false-alarm threshold set 1 dB too low (0.5 dB excess), giving more than 5 % false alarms
- _nominal:_ acceptance set with at least 60 vacant observations confirmed by an independent reference from at least 10 channels → false-alarm share <= 5 %: at most 3 of 60; the expected is 0.14 % (`expected_false_alarm_probability`)
- _error:_ inject a strong adjacent carrier beside a vacant channel (adjacent leakage) → the vacant channel is released Uncertain (uncertain_adjacent_leakage), not Occupied: not a false alarm
- _edge:_ 60 vacant observations with 3 false alarms and then 4 → 3 of 60 = 5 % passes (<= 5); 4 of 60 = 6.7 % fails

### P-006 · requisito R-06 · inspección

- **Mide:** smallest margin between the required received power and the verified noise level in records released as Free >= 10 dB
- **Condición:** saved screening reports of the validation set and of the field run; one violating record fails
- **Datos de prueba:** D_k - N_k computed from declared_min_power_dbm and noise_dbm of the record: for N = -100 dBm and D = -90 dBm margin 10.0 dB
- **Falla si:** the margin tested as > 10 instead of >= 10, or tested against the threshold instead of the declared minimum
- _nominal:_ inspect every record released as Free in a 72 h report → smallest release_margin_db >= 10 dB (`release_margin`)
- _error:_ configure a declared minimum received power 8 dB above the noise reference → the channel is not released Free: state Uncertain with reason uncertain_margin_below_10db (a reason code of `occupancy_scan`, not an error)
- _edge:_ declared minimum exactly 10.0 dB above the noise reference, then 9.9 dB → 10.0 dB releases Free (>= 10); 9.9 dB does not

### P-007 · requisito R-07 · inspección

- **Mide:** share of channel-scan records without a valid occupancy validity or without a Free-release that are released as Free <= 0 %
- **Condición:** saved screening reports of the validation set and of the field run
- **Datos de prueba:** count records with state Free and (validity not_valid or reason not free_released); expected 0
- **Falla si:** Free released by default when the declared minimum is absent
- _nominal:_ inspect all records of a 72 h report → records with validity not valid or without a Free release that are Free: 0 %
- _error:_ expired calibration (calibration_state expired) → all records Uncertain with reason uncertain_calibration; none Free (E-CAL-002)
- _edge:_ declared minimum not configured (uncertain_not_configured) → no channel is Free until the minimum is declared: 0 % violations

### P-008 · requisito R-08 · inspección

- **Mide:** share of channels with a duty cycle and an Uncertain fraction reported for each reporting interval >= 100 %
- **Condición:** intervals in which at least one scan is Occupied or Free
- **Procedimiento:** `accumulate_duty_cycle`
- **Datos de prueba:** duty = 100 x n_occupied / (n_occupied + n_free); example n_occ 600, n_free 400, n_unc 200 of 1200 scans: duty 60 %, uncertain 16.7 %
- **Falla si:** Uncertain scans counted in the denominator of the duty cycle, or an interval without a line for a channel
- _nominal:_ declared reporting interval 60 min (`duty_cycle_interval_default`); inspect the intervals file of a 72 h report → each interval has 199 entries each with duty_cycle and uncertain_fraction: 100 %
- _error:_ time unsynced for part of an interval (E-TIME-001) → the interval is flagged time_flag true (E-DET-004) but still reports both values
- _edge:_ an interval in which a channel has no Occupied or Free scan → duty_cycle is null and uncertain_fraction is 100; the entry is present

### P-009 · requisito R-59 · inspección

- **Mide:** share of Free records showing the release conditions >= 100 %
- **Condición:** saved screening reports of the validation set and of the 72 h field run
- **Datos de prueba:** required fields of a Free C line: detected false, validity valid, release_margin_db, declared_min_power_dbm, threshold_dbm
- **Falla si:** a Free line missing the declared minimum or the margin
- _nominal:_ inspect every Free record in a 72 h report → each shows no detection, validity valid, release margin >= 10 dB and the declared minimum: 100 %
- _error:_ drop the field release_margin_db from a record at the writer (fault injection) → the record is rejected by the schema check (E-SUP-005 or E-REC) and flagged; no Free record without the fields is saved
- _edge:_ release margin exactly 10.0 dB → the margin is written with two decimals (`stored_power_resolution` 0.01 dB): 10.00

### P-010 · requisito R-09 · inspección

- **Mide:** share of channel-scan records carrying a calibrated power in dBm at the receiver reference plane >= 100 %
- **Condición:** saved screening reports; integration bandwidth as in R-69
- **Datos de prueba:** inject a known level of -60 dBm at the port; expected reading -60 dBm within the stated uncertainty 1.28 dB
- **Falla si:** power written in dBFS or referred to another plane
- _nominal:_ inspect all C lines of a calibrated 72 h report → every line carries power in dBm (null with a reason when withheld) referred to the SDR antenna port connector: 100 %
- _error:_ scan with an uncalibrated state (calibration none) → power null with withheld_reason not_demonstrated; the unit and plane are still declared in the header
- _edge:_ power at the top of the range (-5 dBm) and bottom (-130 dBm) → values within -140 to 0 dBm are written; none in dBFS

### P-011 · requisito R-10 · ensayo

- **Mide:** absolute difference between the reported channel power and a qualified independent reference <= 3 dB
- **Condición:** at least 10 distinct channels; each difference with its expanded uncertainty subtracted from the limit; an inconclusive channel prevents acceptance
- **Procedimiento:** `verify_amplitude_correction`
- **Datos de prueba:** reference levels from the calibration reference level and 20 dB below at channels 16, 46, 76, 126, 146, 186 plus 4 more channels not calibration points; expected difference within 1.72 dB
- **Falla si:** the expanded uncertainty is not subtracted from the 3 dB limit, or interpolation between calibration points is wrong
- _nominal:_ at least 10 distinct channels, a qualified independent reference level applied (verification points 12 over 6 channels, plus 4 extra channels), difference |P_node - P_ref| per channel → each |difference| + expanded uncertainty 1.28 dB (k = 2) <= 3 dB, i.e. |difference| <= 1.72 dB
- _error:_ gain error injected: +2 dB offset in the correction table → |difference| 2 dB + 1.28 dB = 3.28 dB > 3: the verification fails (`verify_amplitude_correction`) and the state becomes invalid (E-VER-002)
- _edge:_ difference 1.72 dB and then 1.80 dB → 1.72 + 1.28 = 3.00 passes; 1.80 + 1.28 = 3.08 fails; an inconclusive channel prevents acceptance

### P-012 · requisito R-11 · inspección

- **Mide:** share of power values reported with a half-width uncertainty in dB and its basis >= 100 %
- **Condición:** saved screening reports
- **Datos de prueba:** count lines with power not null and (uncertainty_db null or basis empty); expected 0
- **Falla si:** the uncertainty written as a full width (2.56 dB) instead of the half-width
- _nominal:_ inspect all power values of a 72 h report → each has uncertainty_db (half-width, 1.28 dB default, 1.37 dB DC-adjacent) and uncertainty_basis text: 100 %
- _error:_ channel 22 (DC-adjacent) → uncertainty 1.37 dB with the basis naming the DC spike
- _edge:_ power value near the noise floor (near_noise_floor true) → uncertainty and basis are still present; flag set

### P-013 · requisito R-12 · inspección

- **Mide:** share of outputs delivered with value, uncertainty, limit or recorded absence, and comparison >= 100 %
- **Condición:** saved screening reports
- **Datos de prueba:** fields per C line: power.value_dbm, power.uncertainty_db, limit.state, limit.limit_dbm, limit.comparison
- **Falla si:** limit field omitted when not configured
- _nominal:_ inspect all outputs of a 72 h report → each output has value, uncertainty, limit or recorded absence, comparison: 100 %
- _error:_ no limit configured → limit.state not_configured, comparison not_configured, never within_limit
- _edge:_ limit configured at -5 dBm (the upper bound) and a power just below → comparison within_limit with the limit value written

### P-014 · requisito R-13 · inspección

- **Mide:** share of records without a limit that present the comparison as within the limit <= 0 %
- **Condición:** saved screening reports while no limit is configured
- **Datos de prueba:** count lines with limit.state not_configured and comparison within_limit; expected 0
- **Falla si:** absence of a limit treated as unlimited, giving within_limit
- _nominal:_ run with no received-power limit configured and inspect the report → records presenting comparison within_limit: 0 %
- _error:_ limit file rejected (E-CFG-002) and node runs with defaults → comparison not_configured on every record
- _edge:_ limit configured then removed during the run → after removal records carry not_configured, none within_limit

### P-015 · requisito R-14 · inspección

- **Mide:** number of comparison states converted from indeterminate, not configured or unavailable to within or outside the limit <= 0 count
- **Condición:** saved screening reports over the validation set and field run
- **Datos de prueba:** vector of 30 channel records with the five comparison values; expected output equal to input for the three non-definite values
- **Falla si:** rounding, averaging or defaulting a non-definite state to a definite one
- _nominal:_ feed records with comparison indeterminate, not_configured and unavailable through the pipeline → none is converted to within_limit or outside_limit: 0
- _error:_ inject an unreadable reference (E-CFG-003) → assignment comparison indeterminate on all 199 channels; no state converted
- _edge:_ a bin of 10 scans with 5 Occupied and 5 Uncertain in a view → the view shows counts; no averaged or majority state is produced

### P-016 · requisito R-15 · inspección

- **Mide:** share of channel-scan records carrying an occupancy comparison result >= 100 %
- **Condición:** site with a station-assignment reference loaded
- **Procedimiento:** `compare_with_reference`
- **Datos de prueba:** truth table of occupancy x assignment: Occupied+assigned consistent, Occupied+unassigned unassigned-occupied, Free+assigned assigned-free, Free+unassigned consistent, Uncertain indeterminate
- **Falla si:** Uncertain mapped to assigned-free, feeding the silence alert
- _nominal:_ inspect all C lines of a 72 h report → every line carries assignment.comparison in {consistent, unassigned-occupied, assigned-free, indeterminate}: 100 %
- _error:_ station reference missing (E-CFG-001/E-CFG-003) → comparison indeterminate on all lines, none blank
- _edge:_ Uncertain occupancy on an assigned channel → comparison indeterminate, never assigned-free

### P-017 · requisito R-16 · demostración

- **Mide:** a station-assignment reference of the site is loaded and used by the comparison >= 1 count
- **Condición:** site configuration with at least one loaded reference
- **Procedimiento:** `load_and_validate_site_config`
- **Datos de prueba:** reference_id REF-TEST-01, 199 entries channel n station STN-n; expected reference_used equal in the report header
- **Falla si:** the comparator uses a built-in list instead of the loaded reference
- _nominal:_ load a valid station-assignment reference (`station_assignment_reference`) with 199 entries through the site configuration → `config_status` reports station_reference_state valid and reference_id; every record's assignment.reference_id equals it: demonstrated, count 1
- _error:_ load a reference with a duplicate channel (E-CFG-003) → the reference is rejected, the comparison is indeterminate everywhere, the previous valid reference is kept if any
- _edge:_ reference with 0 entries, then with 199 entries (`station_entries_max` maximum) → 0 entries: every channel unassigned, comparison defined; 199 entries accepted; 200 entries rejected

### P-018 · requisito R-17 · inspección

- **Mide:** share of power measurements carrying a correction established against a traceable reference >= 100 %
- **Condición:** calibration record names the source, its calibration date and its uncertainty
- **Procedimiento:** `apply_calibration_to_scan`
- **Datos de prueba:** join each C line calibration_record_id with `calibration_record` reference_source fields; expected all non-empty
- **Falla si:** power released with a correction from an untraceable or unnamed source
- _nominal:_ inspect every power measurement of a calibrated 72 h report → each carries calibration_record_id of a record whose reference source has a certificate_id and traceability_body: 100 %
- _error:_ start with calibration none → power withheld, no power measurement is released uncorrected
- _edge:_ record with a reference calibration_date older than its certificate validity → the establishment is refused (E-CAL-004 family); no record is created

### P-019 · requisito R-18 · inspección

- **Mide:** share of calibrations whose record holds the identifier, configuration, reference plane, reference source and validity state >= 100 %
- **Condición:** calibration records
- **Procedimiento:** `establish_amplitude_calibration`
- **Datos de prueba:** required keys of `calibration_record`: record_id, device, configuration, reference_plane, reference_source, validity; expected present and the sha256 file equal to the hash of the JSON
- **Falla si:** a record without the reference plane or overwritten by a later one
- _nominal:_ inspect every calibration record created in a test session → each holds record_id, device and configuration, reference_plane, reference_source and validity state: 100 %
- _error:_ power failure while the record is written (E-CAL-005) → the previous calibration is kept; no partial record exists (companion sha256 absent or invalid is rejected)
- _edge:_ two records created in the same second → record_id differs by the -nn suffix; neither overwrites the other

### P-020 · requisito R-19 · ensayo

- **Mide:** longest time between two passing verifications of the amplitude correction <= 3456000 s (valor que se declara en la implementación, dentro de los límites del anexo A)
- **Condición:** bound is the declared verification interval, deferred through el intervalo de verificación y su margen
- **Procedimiento:** `verify_amplitude_correction`
- **Datos de prueba:** verification times from the validation records: t1, t2...; expected max(t_{i+1} - t_i) <= declared interval
- **Falla si:** the interval measured from the start of a verification instead of its passing result, or bounds not enforced
- _nominal:_ declare verification interval 7 d (604,800 s) and margin 1 d in the calibration record; run 30 days → longest time between two passing verifications <= 604,800 s and inside the bounds 345,600 to 3,456,000 s
- _error:_ declare an interval of 50 d (4,320,000 s) → the record is rejected: above `verification_interval_max` (E-VER-006)
- _edge:_ interval 345,600 s (4 d), then 345,599 s → 345,600 s accepted; 345,599 s rejected; the interval at the upper bound 3,456,000 s accepted

### P-021 · requisito R-20 · inspección

- **Mide:** number of verifications in which the verification reference coincides with the reference that established the correction <= 0 count
- **Condición:** calibration and validation records
- **Procedimiento:** `verify_amplitude_correction`
- **Datos de prueba:** independence = serial_differs and certificate_differs and chain_differs and operator attestation, all true
- **Falla si:** independence judged by model name only
- _nominal:_ verify with an independent reference whose serial, certificate and traceability chain differ from the establishing source → verifications where the reference coincides with the establishing one: 0
- _error:_ use the same instrument for establishment and verification → independence flags false: the verification is refused (E-VER-001); validity unchanged
- _edge:_ same model, different serial, same certificate → certificate_differs false: refused

### P-022 · requisito R-60 · inspección

- **Mide:** share of validation records that identify the independent reference and its uncertainty >= 100 %
- **Condición:** validation records
- **Procedimiento:** `verify_amplitude_correction`
- **Datos de prueba:** independent_reference.level_uncertainty_db_k2 <= 0.5
- **Falla si:** uncertainty not recorded or the 0.5 dB limit not enforced
- _nominal:_ inspect every validation record → each identifies the independent reference (name, model, serial, certificate, traceability) and its uncertainty at most 0.5 dB (`independent_reference_uncertainty_max`): 100 %
- _error:_ reference with level uncertainty 0.8 dB → record refused (E-VER-001/E-VER-004); no validation record created
- _edge:_ uncertainty exactly 0.5 dB → accepted; 0.51 dB refused

### P-023 · requisito R-21 · ensayo

- **Mide:** number of power values released while the active correction cannot be demonstrated <= 0 count
- **Condición:** fault injection: expired verification, drifted correction
- **Procedimiento:** `apply_calibration_to_scan`
- **Datos de prueba:** released power values counted in scans whose calibration_state is expired, invalid or none; expected 0
- **Falla si:** state read once per hour instead of per scan, so a scan after the expiry is released
- _nominal:_ set verified_until to the past (expired state) during a run → zero power values released after the expiry instant; records withheld_reason expired; occupancy Uncertain
- _error:_ drift the correction by 1.6 dB so the verification fails (invalid) → calibration_state invalid; power withheld on all channels (E-VER-002, E-CAL-002)
- _edge:_ scan starting 1 s before verified_until and one starting 1 s after → before: state expiring, power released with the alert; after: expired, power withheld

### P-024 · requisito R-22 · inspección

- **Mide:** number of acquisitions made with automatic gain control enabled <= 0 count
- **Condición:** configuration record of each acquisition
- **Procedimiento:** `scan_cycle`
- **Datos de prueba:** count blocks with agc_enabled true; expected 0 of 3 blocks x 14,400 scans per day
- **Falla si:** the default gain mode of the driver left on at start-up
- _nominal:_ inspect acquisition records (`capture_block`/`acquisition_counters`) of a 72 h run → agc_enabled false in every block: 0 acquisitions with AGC
- _error:_ driver reports AGC on after a restart → the acquisition sets AGC off before capture; if it cannot, the scan is flagged (E-ACQ-001 family) and no power is released
- _edge:_ first scan after a process restart → agc_enabled false in the first block

### P-025 · requisito R-23 · inspección

- **Mide:** share of acquisitions whose record holds the gain settings and the amplifier state >= 100 %
- **Condición:** saved screening reports
- **Procedimiento:** `scan_cycle`
- **Datos de prueba:** 9 gain values per S line (3 steps x 3 stages); expected 0, 16, 16 for each step
- **Falla si:** gain omitted when it is zero
- _nominal:_ inspect S lines of a 72 h report → each acquisition has rf_amp_db, lna_db, baseband_db (0, 16, 16 dB, `rf_amp_gain` to `baseband_gain`) and the amplifier state: 100 %
- _error:_ gain command fails on one step (E-ACQ-003) → the S line records the gains actually applied and the retune_failed flag
- _edge:_ step 1 with 0 dB RF amplifier → rf_amp_db written 0, not omitted

### P-026 · requisito R-24 · ensayo

- **Mide:** number of power values released from a capture with a full-scale sample <= 0 count
- **Condición:** fault injection with a full-scale signal
- **Procedimiento:** `scan_cycle`
- **Datos de prueba:** signal: 10 Msps, I = 127 for 1 sample inside 39 frames of noise; expected clipped flag true for the step
- **Falla si:** clipping threshold set to a count above 1 or applied to the average
- _nominal:_ inject a full-scale sine (I or Q sample at +127/-128) in step 2 only → channels 77 to 135 of the scan: power null, withheld_reason clipped, occupancy Uncertain; other steps unaffected: 0 power values released from the clipped capture
- _error:_ full-scale signal in all three steps → all 199 channels withheld clipped (E-ACQ-001)
- _edge:_ one sample at full scale in a capture of 5,111,200 samples → still flagged (clip threshold 1 sample, `clip_sample_count_threshold`)

### P-027 · requisito R-25 · ensayo

- **Mide:** number of power values released, and of occupancy states released other than Uncertain, in scans with an overflow or a dropped frame <= 0 count
- **Condición:** fault injection: throttled host, paused subscriber
- **Procedimiento:** `scan_cycle`
- **Datos de prueba:** pause length t_p added to the estimator; overflow when 0.3221 + t_p > 0.8389, i.e. t_p > 0.5168 s
- **Falla si:** only the capture with the overflow is flagged instead of the whole scan
- _nominal:_ pause the subscriber for 1 s during a capture so the ring buffer (0.839 s) overflows → all 199 records of the scan flagged, power null, occupancy Uncertain: 0 power values and 0 non-Uncertain states released
- _error:_ throttled host (CPU limited) causing dropped frames → as above; after 3 consecutive flagged scans the supervisor restarts the measure process (E-SUP-001)
- _edge:_ pause of 0.5 s (below the buffer time 0.839 s minus the backlog 0.32 s = 0.52 s) and of 0.6 s → 0.5 s: no overflow, scan normal; 0.6 s: overflow, scan flagged

### P-028 · requisito R-26 · ensayo

- **Mide:** share of injected frame losses counted as dropped frames >= 100 %
- **Condición:** fault injection: paused subscriber
- **Procedimiento:** `scan_cycle`
- **Datos de prueba:** frame counter gap between consecutive frames (13.1072 ms); lost = gap - 1; expected equal to the injected number
- **Falla si:** consecutive lost frames counted as one
- _nominal:_ pause the subscriber to lose exactly 10 frames, repeat for 20 injections of 1 to 20 frames → dropped_frame_count in the health record equals the injected count in every injection: 100 %
- _error:_ inject losses in two captures of the same scan → the counts add (e.g. 3 + 4 = 7) and the scan is flagged
- _edge:_ loss of exactly 1 frame; loss of 117 frames (3 x 39) → 1 and 117 counted; the health range is 0 to 117

### P-029 · requisito R-27 · inspección

- **Mide:** share of full-band scans with a health record holding the three counts >= 100 %
- **Condición:** saved screening reports over the field run
- **Procedimiento:** `build_records`
- **Datos de prueba:** one H line per scan_id; expected 14,400 H lines per day, each with the three counts
- **Falla si:** health record skipped for a failed scan
- _nominal:_ inspect H lines of a 72 h report → each scan has overflow_count, dropped_frame_count and records_published: 100 %
- _error:_ scan fails (E-REC-001) → health record still written with records_published 0 and the counts that exist
- _edge:_ scan with 0 overflow and 0 dropped → fields written as 0, not omitted

### P-030 · requisito R-28 · inspección

- **Mide:** resolution of the scan timestamp <= 1 ms
- **Condición:** saved screening reports, UTC
- **Datos de prueba:** stamp value in microseconds since 1970; expected integer microseconds
- **Falla si:** timestamp truncated to seconds or to 10 ms
- _nominal:_ inspect the resolution of utc_us (`timestamp_resolution` = 1 us) in `scan_header` of a run → resolution_us 1 <= 1 ms (1000 us)
- _error:_ time service unsynced (E-TIME-001) → the stamp keeps 1 us resolution; sync_state unsynced is recorded; the scan is not withheld
- _edge:_ two scans started 6,000,000 us apart → stamps differ by 6,000,000 +/- jitter, never rounded to ms

### P-031 · requisito R-29 · inspección

- **Mide:** share of calibrated power records that name the gain state and the calibration record >= 100 %
- **Condición:** saved screening reports; calibration record resolvable from persistent data
- **Procedimiento:** `apply_calibration_to_scan`
- **Datos de prueba:** join C lines with S lines on scan_id: expected calibration_record_id and 9 gain values present
- **Falla si:** gain state stored only in the header, not per scan
- _nominal:_ inspect calibrated power records of a 72 h report → each names the gain state (gains and agc flag in the S line) and the calibration_record_id: 100 %
- _error:_ configuration differs from the record (config_mismatch) → power withheld (E-CAL-001), the record id still named in the line
- _edge:_ calibration replaced during the run → lines before and after carry different record ids

### P-032 · requisito R-30 · inspección

- **Mide:** share of released Free states that can be re-checked from the stored inputs >= 100 %
- **Condición:** saved screening reports of the validation set and of the field run
- **Datos de prueba:** from the line: power, noise, declared_min, threshold; recompute excess = power - noise and margin = declared_min - noise
- **Falla si:** report keeps the state but drops the inputs
- _nominal:_ pick 100 Free states from a 72 h report and re-check each from the stored inputs → all 100 re-derive Free: excess <= 1.0 dB, margin >= 10 dB, threshold <= declared minimum: 100 %
- _error:_ a report line with the noise_dbm field removed (fault injection) → the re-check fails; the line is a defect (the writer must keep every input, «Escritor de informes»)
- _edge:_ excess exactly 1.0 dB → re-checks as Free (<= 1.0)

### P-033 · requisito R-31 · inspección

- **Mide:** real-time monitoring records saved to disk outside the screening report <= 0 count
- **Condición:** disk of the node after a field run
- **Procedimiento:** `apply_resource_limits`
- **Datos de prueba:** list of files on the card: reports/, calibration/, validation/, supervisor/, config/ only; expected no file with channel records outside reports/
- **Falla si:** history swapped to the card or a core dump holding records
- _nominal:_ inspect the card after a 72 h field run (files, swap, core files, temporary files, logs) → real-time monitoring records outside the report: 0
- _error:_ start with a swap area active (E-HIS-004) → monitoring is refused; nothing is written; node_state not_measuring
- _edge:_ process crash during a run → no core file is written (limit 0) and the history is not on the card

### P-034 · requisito R-55 · ensayo

- **Mide:** number of deployed gain configurations with a documented dynamic range and compression characterization >= 1 count
- **Condición:** bench characterization at the deployed gain configuration
- **Procedimiento:** `establish_amplitude_calibration`
- **Datos de prueba:** sweep -100 to -20 dBm in 5 dB steps (`sweep_level_min`, `sweep_level_max`, `sweep_step`); expected range_low at 10 dB over the noise floor
- **Falla si:** sweep uses another gain configuration than the deployed one
- _nominal:_ establish the dynamic range for the deployed gain configuration (0, 16, 16 dB) with the sweep of `establish_amplitude_calibration` → one record with range_low, range_high, compression and clip levels: count 1
- _error:_ sweep source fails mid-sweep → the acceptance criteria fail (E-CAL-003) and the previous calibration is kept
- _edge:_ compression criterion 1 dB (`compression_criterion`) reached at the highest level → compression_level_dbm recorded; range_high set 3 dB below (`range_high_headroom`)

### P-035 · requisito R-56 · inspección

- **Mide:** share of devices with a recorded frequency-reference state >= 100 %
- **Condición:** device records
- **Datos de prueba:** correction_ppm from a reference tone at 100.000 MHz measured at 100.001 MHz = 10 ppm
- **Falla si:** state missing when no correction is applied
- _nominal:_ inspect the calibration record and the report header of each device → frequency_reference.state present (stock_uncorrected, stock_corrected or out_of_limit): 100 %
- _error:_ correction above 20 ppm → state out_of_limit; the establishment fails its acceptance criteria (E-CAL-003)
- _edge:_ correction exactly 20 ppm → state within limit (stock_corrected)

### P-036 · requisito R-57 · ensayo

- **Mide:** sample loss and host-buffer overrun events in a continuous run at the deployed sample rate <= 0 count
- **Condición:** 60 s bench run and the field run, as in the bench bring-up
- **Procedimiento:** `apply_resource_limits`
- **Datos de prueba:** overflow_count and dropped_frame_count summed over all H lines of the run; expected 0
- **Falla si:** web or report work on the same priority as the acquisition
- _nominal:_ 60 s bench run and the 72 h field run at 10 Msps with 8 web clients at the refresh rates → overflow count 0 and dropped-frame count 0
- _error:_ web burst of 80 clients (queue 64) → 503 answers to some; acquisition counts stay 0 because the web unit is capped at one core and niceness 10
- _edge:_ estimator delayed by 0.5 s per capture, then 0.6 s → 0.5 s: no event; 0.6 s: an overflow event is counted (expected failure of the test)

### P-037 · requisito R-58 · inspección

- **Mide:** number of scans run with a configuration different from the one of the active calibration record <= 0 count
- **Condición:** configuration record of each scan
- **Procedimiento:** `apply_calibration_to_scan`
- **Datos de prueba:** compare config_sha256 of the scan header with the one in `calibration_record`; expected equal for every scan that releases power
- **Falla si:** only the sample rate is compared, not the gains or step centres
- _nominal:_ change a gain setting in the configuration after calibration, then start a scan → scan not run (or records withheld config_mismatch): scans with a configuration different from the record: 0
- _error:_ configuration file edited by hand while running → the scan is flagged config_mismatch (E-CAL-001) and power withheld; a malformed file is rejected (E-CFG-002) and the previous valid configuration kept
- _edge:_ identical configuration reloaded → config_sha256 equal: scans continue

### P-038 · requisito R-32 · inspección

- **Mide:** share of records, reports and dashboards identified as screening evidence >= 100 %
- **Condición:** dashboard panels and exported reports
- **Procedimiento:** `serve_view_request`
- **Datos de prueba:** count of responses without the header X-Screening-Evidence true or the field evidence_label; expected 0
- **Falla si:** label omitted on JSON answers or on the alert page
- _nominal:_ inspect every page header, API answer, downloaded report and a record file → each carries the label 'Screening evidence only: not a compliance determination' or screening_evidence true: 100 %
- _error:_ page request while the history is unavailable (E-WEB-006) → the error page still shows the label
- _edge:_ a cached answer served from the cache → carries the label and X-Screening-Evidence true

### P-039 · requisito R-33 · inspección

- **Mide:** number of alerts, records or reports stating compliance or non-compliance <= 0 count
- **Condición:** all alert texts and report templates
- **Procedimiento:** `build_records`
- **Datos de prueba:** search every generated text for the 12 words of `forbidden_wording` case-insensitively; expected 0 hits outside the label
- **Falla si:** station name copied into an alert text without the wording check
- _nominal:_ inspect every alert text, record text and report text of a test session with all alert types raised → none contains a word of `forbidden_wording` (compliant, non-compliant, violation, illegal,...): 0
- _error:_ a station named 'Illegal Radio' in the reference → the text replaces the name by its channel number (E-ALR-008 / E-REC-004); the word does not appear
- _edge:_ the exact label text contains 'compliance' → allowed only inside the label that denies a determination

### P-040 · requisito R-47 · demostración

- **Mide:** share of the listed evidence items available to personnel >= 100 %
- **Condición:** measurements, records, quality indicators, uncertainty, alerts
- **Procedimiento:** `serve_view_request`
- **Datos de prueba:** checklist of 5 items with the route that gives each: /api/latest-scan, /reports, /alerts
- **Falla si:** uncertainty shown only in the saved report and not in the views
- _nominal:_ review a session with the views, /api/latest-scan, a raised alert and a report download → the five evidence items (calibrated measurements, monitoring records, quality indicators, uncertainty, alerts) are reachable: 5 of 5, 100 %
- _error:_ alert engine stopped (E-WEB-006) → alerts show data unavailable; the other four items remain reachable
- _edge:_ a withheld power value → the view shows validity and flags in place of the value (item quality indicators)

### P-041 · requisito R-34 · ensayo

- **Mide:** number of channel-silent alerts not raised when the silence condition holds <= declared hours H between 0.1 h and 720 h (valor que se declara en la implementación, dentro de los límites del anexo A)
- **Condición:** replayed or simulated assignment-free station; threshold hours deferred through las horas de silencio
- **Procedimiento:** `evaluate_history_alerts`
- **Datos de prueba:** credit = 6 s x assigned-free scans; alert when credit >= H x 3,600 s and D_prior > 90 % with at least 7,200 Occupied+Free scans in the prior 24 h
- **Falla si:** duty cycle compared with >= 90, or the prior window read after the run start, or the hours counted as elapsed time
- _nominal:_ declare H = 2 h; replay a station with prior duty cycle 94.2 % for 24 h (13,000 Occupied, 800 Free scans) then 1,200 assigned-free scans (120 full bins) → one channel_silent alert raised when the credit reaches 7,200 s: not-raised count 0
- _error:_ same replay with silent hours absent from the configuration (E-ALR-001) → no alert is raised and the rule shows not_configured; after H is declared the alert is raised at once
- _edge:_ prior duty cycle exactly 90.0 % (12,600 Occupied, 1,400 Free) then 90.1 % → 90.0 %: no alert (not above 90); 90.1 %: alert raised; and H = 0.1 h and 720 h accepted, 0.09 h rejected

### P-042 · requisito R-35 · ensayo

- **Mide:** number of Uncertain observations counted toward silence <= 0 count
- **Condición:** simulated Uncertain observations
- **Procedimiento:** `evaluate_history_alerts`
- **Datos de prueba:** credit_s = 6 x n_assigned_free per bin; assert credit does not increase when n_uncertain increases
- **Falla si:** a bin credited 60 s when it has any assigned-free scan
- _nominal:_ bins with 5 assigned-free and 5 Uncertain scans each, repeated 240 times → credit per bin 30 s (5 x 6 s); alert only at 4 h for H = 2 h; Uncertain observations counted toward silence: 0
- _error:_ bins with 10 Uncertain scans (reference lost, E-CFG-003) → credit 0 s for every bin; the run is not extended and not reset
- _edge:_ a bin with 1 assigned-free and 9 Uncertain scans → credit 6 s only; never 60 s

### P-043 · requisito R-36 · ensayo

- **Mide:** number of unexpected-occupancy alerts not raised for an occupied unassigned channel <= 0 count
- **Condición:** replayed signal on an unassigned channel
- **Procedimiento:** `evaluate_scan_alerts`
- **Datos de prueba:** persistence count increments on unassigned-occupied, resets on any other value; raise at 3
- **Falla si:** persistence counter not reset by a non-matching scan, raising on 2 non-consecutive scans
- _nominal:_ replay a stable signal on an unassigned channel (Occupied, unassigned-occupied) for 3 consecutive scans → one unexpected_occupancy alert raised at the third scan, 12 s after the first: not-raised count 0
- _error:_ station reference missing (E-CFG-003) → comparison indeterminate: no alert, rule shows reference_unavailable (E-ALR-005)
- _edge:_ signal present in 2 scans then absent → no alert (persistence 3 not reached); with 3 scans an alert

### P-044 · requisito R-37 · ensayo

- **Mide:** number of sensor-offline alerts not raised when no health record arrives for three scan periods <= 0 count
- **Condición:** node stopped for more than three scan periods
- **Procedimiento:** `watch_health_points`
- **Datos de prueba:** monotonic timer restarted at each health point; alert when timer >= 18 s (`sensor_offline_timeout`)
- **Falla si:** timer measured in UTC (a clock step shifts it) or the alert needing 3 missed records instead of 18 s
- _nominal:_ stop the node (kill the measure process and prevent restart) for 30 s → sensor_offline alert raised at most 19 s after the last health point: not-raised count 0
- _error:_ measure process alive but every scan fails (records_published 0, E-REC-001) → after 3 periods without a health point (records_published >= 1) the alert is raised
- _edge:_ no health record for 17 s, then one arrives; and no health record for 18 s → 17 s: no alert; 18 s: alert at the next 1 s check

### P-045 · requisito R-38 · ensayo

- **Mide:** number of calibration-not-demonstrated alerts not raised when the condition holds <= 0 count
- **Condición:** expired verification interval
- **Procedimiento:** `evaluate_scan_alerts`
- **Datos de prueba:** condition = calibration_state not valid or any withheld_reason in {not_demonstrated, expired, config_mismatch, invalid}
- **Falla si:** clipped counted as calibration reason, or the margin ignored so the alert comes only at expiry
- _nominal:_ set verified_until so that the verification interval expires: state expiring then expired → calibration_not_demonstrated alert raised on the first scan with expiring: not-raised count 0
- _error:_ inject a record with withheld_reason expired in one channel → alert raised; a record with only clipped does not raise it
- _edge:_ scan 1 s before verified_until minus the declared margin and 1 s after → before: no alert; after: alert

### P-046 · requisito R-39 · ensayo

- **Mide:** number of noise-floor-drift alerts not raised when the median shifts by more than 6 dB over 24 h <= 0 count
- **Condición:** simulated noise-floor shift
- **Procedimiento:** `evaluate_history_alerts`
- **Datos de prueba:** shift = |median of last 60 min - median of the same 60 min 24 h earlier|; windows of 600 scans each, at least 300 non-null
- **Falla si:** max minus min inside 24 h used, or comparison made with >= 6, or windows shorter than 300 values
- _nominal:_ hold the median noise floor at -98.0 dBm for 25 h, then step to -91.5 dBm for 60 min → shift 6.5 dB > 6: noise_floor_drift alert raised: not-raised count 0
- _error:_ history store restarted 10 h before the step (E-HIS-003) → rule shows insufficient_history until 25 h of data; no alert, no false alert
- _edge:_ step of exactly 6.0 dB, then 6.1 dB → 6.0 dB: no alert (not above 6); 6.1 dB: alert

### P-047 · requisito R-40 · inspección

- **Mide:** number of alerts raised from received channel power while no limit is configured <= 0 count
- **Condición:** alert rule set
- **Procedimiento:** `evaluate_scan_alerts`
- **Datos de prueba:** static check: the five rule conditions reference only comparison, withheld_reason, bin counts, noise_floor_median, calibration_state, health counters
- **Falla si:** a sixth rule reads power.value_dbm
- _nominal:_ inspect the alert rule set and replay a strong channel power with no limit configured → alerts raised from received channel power: 0 (the five types read no power value)
- _error:_ limit configuration rejected (E-CFG-002) and a power above any plausible limit → still 0 power alerts
- _edge:_ limit configured at -130 dBm and a power of -20 dBm → still 0 alerts from power (outside_limit appears in the record only)

### P-048 · requisito R-41 · demostración

- **Mide:** the web view of channel power by frequency and time is available >= 1 count
- **Condición:** field run data
- **Procedimiento:** `refresh_page`
- **Datos de prueba:** GET /api/power-map?span_h=24; expected 144 cells per channel x 199
- **Falla si:** map drawn from a finer bin that exceeds 40,000 bins and is refused
- _nominal:_ open /power with field-run data in a browser → the map of channel power by frequency and time is shown for 24 h at 600 s: count 1
- _error:_ history empty after a restart (E-HIS-003) → data_state no_data or insufficient_history is written; no empty chart
- _edge:_ span 1 h, 6 h and 24 h → bins 11,940, 14,328 and 28,656; the 24 h span at 300 s is not offered

### P-049 · requisito R-42 · demostración

- **Mide:** the web view of the current power spectrum with channel markers is available >= 1 count
- **Condición:** field run data
- **Procedimiento:** `refresh_page`
- **Datos de prueba:** 2,457 points at 9,765.625 Hz; markers at 88.1 + 0.1 x (n - 1) MHz
- **Falla si:** steps overlapped so a band edge appears twice
- _nominal:_ open /spectrum with a calibrated scan → the line of 3 joined steps with 199 channel markers is drawn: count 1
- _error:_ scan flagged (E-ACQ-002) → line not drawn; markers show Uncertain with flags
- _edge:_ the join frequencies 94.0 and 101.5 MHz → no gap and no overlap at the joins; channel 100 marker at 98.0 MHz

### P-050 · requisito R-43 · demostración

- **Mide:** the web view of power and duty cycle of selected stations over 24 h is available >= 1 count
- **Condición:** field run data
- **Procedimiento:** `refresh_page`
- **Datos de prueba:** 288 bins of 300 s per station; duty = 100 x sum n_occ / (sum n_occ + sum n_free)
- **Falla si:** duty cycle computed with Uncertain scans in the denominator
- _nominal:_ select 10 stations in /stations with 24 h of data → power and duty cycle over 24 h drawn for each: count 1
- _error:_ select 11 stations (E-WEB-003) → 400 with the parameter name; no partial chart
- _edge:_ a station with no Occupied or Free scan in 24 h → duty cycle null, Uncertain share 100 %

### P-051 · requisito R-44 · demostración

- **Mide:** the web view of node status shows the five listed quantities >= 5 count
- **Condición:** field run data
- **Procedimiento:** `refresh_page`
- **Datos de prueba:** fields: sensor.online, sensor.last_health_point_age_s, noise_floor_drift.shift_db, overflow.latest/last_24h, dropped_frames.latest/last_24h
- **Falla si:** drift shown only while an alert is active
- _nominal:_ open /status while measuring → online status, last scan age, noise-floor drift, overflow count and dropped-frame count shown: 5
- _error:_ alert engine stopped (E-WEB-006) → the drift and online fields show unavailable; the counts from the history remain: the count falls and the failure is visible
- _edge:_ no scan for 20 s → online false, last scan age highlighted from 18 s, the sensor-offline alert listed

### P-052 · requisito R-45 · inspección

- **Mide:** number of unreleased power values drawn in the power and occupancy views <= 0 count
- **Condición:** records with a power value retained and not released
- **Procedimiento:** `serve_view_request`
- **Datos de prueba:** vector of 20 records: 10 released, 10 withheld with non-null power; expected 10 drawn
- **Falla si:** withheld values drawn in a lighter colour instead of omitted
- _nominal:_ feed records with power retained but withheld_reason clipped through the views → unreleased power values drawn: 0; the cell shows reason and flags
- _error:_ a source record with a power value and withheld_reason expired (E-WEB-009) → the value is dropped and counted; the answer has null
- _edge:_ state Free with validity not_valid → drawn as Uncertain with its reason

### P-053 · requisito R-46 · demostración

- **Mide:** the web view shows the raised alerts >= 1 count
- **Condición:** a raised alert
- **Procedimiento:** `refresh_page`
- **Datos de prueba:** alert bar from GET /api/alerts?scope=bar every 6 s; not cached
- **Falla si:** alert answer cached for 5 s so the alert appears late
- _nominal:_ raise a sensor_offline alert and watch /status → the alert is shown within 6 s of its publication in the bar: count 1
- _error:_ web busy (E-WEB-005) → the page retries after 10 s and shows 'busy, retrying'; the alert appears at the next answer
- _edge:_ 6 active alerts → 5 written out, the sixth counted with a link

### P-054 · requisito R-48 · ensayo

- **Mide:** available time over a continuous run >= 95 %
- **Condición:** 30-day run; the 72 h field run does not verify availability; mains supply continuous, as guaranteed by the user
- **Procedimiento:** `compute_availability`
- **Datos de prueba:** 432,000 points every 6 s; available if a complete scan record lies in the preceding 18 s
- **Falla si:** outage counted from the failure instead of from the 19th second, or restarts not counted
- _nominal:_ 30-day continuous run with the planned faults (120 restarts, 10 reboots) → share available >= 95 %; planned 98.6 %
- _error:_ a loop of one process for 30 minutes followed by a reboot (E-SUP-003, E-SUP-004) → the outage counted minus 18 s; the share stays above 95 %
- _edge:_ 21,600 unavailable points and 21,601 → exactly 95.000 % passes; 21,601 fails

### P-055 · requisito R-49 · análisis

- **Mide:** share of time points counted as available using the definition of the requirement >= 95 %
- **Condición:** 30-day window; share of records in each validity state reported with the result
- **Procedimiento:** `compute_availability`
- **Datos de prueba:** a scan record is complete when it has 199 C lines and a health line with records_published 199
- **Falla si:** a flagged scan not counted as a record (it is a complete record with flags)
- _nominal:_ analyse the same 30-day window by the definition of R-49 → share of time points counted available >= 95 %, with the share of records in each validity state reported
- _error:_ a window with a missing day of report (card replaced) → those points count unavailable; the result is reported as it is
- _edge:_ a gap of exactly 18 s and of 19 s between complete scans → 18 s: all points available; 19 s: one point unavailable

### P-056 · requisito R-50 · ensayo

- **Mide:** channel-mapping error plus the expanded uncertainty of the source frequency <= 5 kHz
- **Condición:** continuous-wave tones at the centre of at least five channels, including the lowest and the highest, with at least one channel for each capture; default configuration
- **Procedimiento:** `estimate_channel_power`
- **Datos de prueba:** error = rounding 1.2207 kHz + interpolation 0.2441 kHz + crystal 2.0 kHz (`frequency_estimate_error_bound` to `mapping_error_bound_100mhz`) plus the source uncertainty
- **Falla si:** the crystal term not corrected or the source uncertainty omitted
- _nominal:_ tone at 100.000 MHz with the frequency correction applied → mapping error 3.4648 kHz plus source frequency uncertainty 1 ppm x 100 MHz = 0.1 kHz: 3.56 kHz <= 5 kHz
- _error:_ correction above 20 ppm (out_of_limit) → calibration invalid; mapping limit exceeded flag (E-EST-004)
- _edge:_ tone at 107.9 MHz → bound 3.6228 kHz plus 0.1079 kHz = 3.73 kHz <= 5 kHz

### P-057 · requisito R-51 · ensayo

- **Mide:** agreement of measurement and screening results between the first site and another site >= 83.3 %
- **Condición:** procedure and agreement rule deferred through la regla de reproducibilidad entre sitios
- **Procedimiento:** `compare_two_sites`
- **Datos de prueba:** En = |D_A - D_B| / sqrt(W_A^2 + W_B^2) with W = sqrt(1.28^2 + 0.59^2); combined limit 1.993 dB
- **Falla si:** En computed with the reported powers at different nominal levels or with k = 1 uncertainties
- _nominal:_ repeat at a second site (`repeat_at_another_site`) and compare the 12 verification points → 10 or more of 12 points with En <= 1 (>= 83.3 %), none above 6 dB, both sites meet 95 % detection and 5 % false alarm, both reports complete
- _error:_ a differing package hash between the sites (E-REP-001) → comparison refused, result inconclusive
- _edge:_ 10 agreeing points and 9 agreeing points → 10 of 12 (83.3 %) passes; 9 of 12 (75 %) fails; a point at 6.5 dB fails whatever the count

### P-058 · requisito R-52 · demostración

- **Mide:** lines of code rewritten to add and configure another node <= 0 count
- **Condición:** another node added and configured by configuration only
- **Procedimiento:** `add_and_configure_another_node`
- **Datos de prueba:** diff of the package files of node 1 and node 2: expected no difference; configuration listing differs only in the declared fields
- **Falla si:** a site-specific constant compiled into the code
- _nominal:_ add and configure a second node from the package and a new configuration file (node_id, location, reference, time sources) → lines of code rewritten: 0; the same package sha256 runs on both nodes
- _error:_ configuration with a required field missing (E-CFG-002) → rejected with a message naming the field; no code change is needed to correct it
- _edge:_ configuration with 4 time sources (maximum `time_sources_max`) and with 5 → 4 accepted; 5 rejected by the schema

### P-059 · requisito R-53 · inspección

- **Mide:** cost of one complete monitoring node, without calibration references or licences <= 3200 USD
- **Condición:** prices at the date of the acceptance review; dollars read as US dollars
- **Datos de prueba:** table of item, source URL, date, price in USD, quantity; total = sum(price x quantity)
- **Falla si:** a required item (supply cord, mounting parts) left out of the sum
- _nominal:_ sum the list prices of HackRF One to 36650 USB 2.0 Type A to Micro-B cable, the cabling, the card and the assembly parts at the purchase date, without calibration references or licences → total <= 3,200 USD
- _error:_ a card whose price is not found at the date → the total is marked unverified and the test fails until the price is documented
- _edge:_ total of exactly 3,200 USD and of 3,201 USD → 3,200 passes; 3,201 fails

### P-060 · requisito R-54 · inspección

- **Mide:** monitoring nodes whose receiver is not a HackRF One <= 0 count
- **Condición:** delivered node
- **Datos de prueba:** sdr_model of `calibration_record` device equals 'HackRF One' for every node
- **Falla si:** the model not recorded in the calibration record
- _nominal:_ inspect each node of the test set (device record in `calibration_record`) → nodes whose receiver is not a HackRF One: 0
- _error:_ an attempt to start with another SDR model in the configuration → the calibration device record names the model; a node with another model is not accepted as the reference node
- _edge:_ a HackRF One clone with a different serial format → accepted only if the model reads HackRF One

### P-061 · requisito R-61 · ensayo

- **Mide:** duration of the continuous field run >= 72 h
- **Condición:** site with a published FM station list and at least the minimum vacant channels per capture; independent reference logging for at least 6 h of it
- **Procedimiento:** `run_field_validation`
- **Datos de prueba:** continuous time = sum of run durations joined by gaps of at most 300 s; expected >= 72 h and logging >= 6 h
- **Falla si:** any restart ending the field run, or a gap of an hour accepted
- _nominal:_ continuous field run planned 76 h at a site with a published FM station list and the reference logging for 6 h → duration of the continuous run >= 72 h
- _error:_ a reboot at hour 30 (E-SUP-004 or power cut) → the report run is closed as interrupted and a new one starts within 300 s: the run still counts as continuous
- _edge:_ a gap of 300 s and of 301 s between two runs → 300 s: continuous; 301 s: the continuous time ends

### P-062 · requisito R-62 · inspección

- **Mide:** share of the four content items (screening results, date and time records, execution time, location information) present in the saved screening report >= 100 %
- **Condición:** screening report saved after a run
- **Procedimiento:** `report_run_lifecycle`
- **Datos de prueba:** header.json fields: location, run_start_utc_us, run_end_utc_us, execution_time_s; plus C/S/H lines
- **Falla si:** execution_time missing for an interrupted run
- _nominal:_ inspect the saved report of a completed run → the four items (results, date and time, execution time, location) are present: 100 %
- _error:_ location not configured (E-RPT-006) → location_state not_configured is written; the report is saved; the item is present as stated
- _edge:_ run interrupted by a power cut → the next start closes it with end time from progress.json and execution_time (E-RPT-005)

### P-063 · requisito R-63 · demostración

- **Mide:** share of acceptance runs in which the node is powered from the mains supply >= 100 %
- **Condición:** acceptance runs in the field on a 120 V and 60 Hz supply
- **Datos de prueba:** record of the supply type in each acceptance run log; expected 'mains supply 85 to 264 V'
- **Falla si:** an acceptance run on a battery or bench supply counted
- _nominal:_ run every acceptance run with the node on the mains supply through the 5 V / 5 A supply → runs powered from the mains: 100 %
- _error:_ supply output below 4.75 V (under-voltage) → the run is not counted as acceptance and is repeated on the mains supply
- _edge:_ mains at 85 V and at 264 V (supply input range) → the node runs in both; the run counts

### P-064 · requisito R-64 · demostración

- **Mide:** installation types (indoor, outdoor) in which the node meets its requirements >= 2 count
- **Condición:** one field run in each installation type
- **Datos de prueba:** acceptance checklist per installation type with the result of el criterio de R-01, el criterio de R-57, el criterio de R-65, el criterio de R-66
- **Falla si:** only the indoor installation tested
- _nominal:_ run the acceptance set in an indoor installation and in an outdoor installation (enclosure on a mast or wall, out of direct sun) → installation types in which the node meets its requirements: 2
- _error:_ outdoor rain during the run → no ingress (el criterio de R-65) and the requirements are met; a failure counts the type as not met
- _edge:_ outdoor at 40 degC ambient → all requirements met (el criterio de R-66); in direct sun is outside the package assumption

### P-065 · requisito R-65 · ensayo

- **Mide:** dust and water ingress into the enclosure <= 0 count
- **Condición:** dust and rain exposure whose severity is set by la severidad de exposición al polvo y la lluvia
- **Datos de prueba:** jet: nozzle 6.3 mm, 12.5 l/min, 3 m distance, 1 min per m2 of surface (IP65 water test); dust: 8 h in the dust chamber
- **Falla si:** the box tested empty without the cable entries of the real installation
- _nominal:_ test the assembled enclosure with its cable entries: dust test and water jet test of the IP protection class (IP65 of) → dust and water ingress observed: 0
- _error:_ a cable entry left open or loosened → ingress observed; the test fails and the assembly is corrected
- _edge:_ jet at the cable entries and the lid seam from several angles → no water inside after the test

### P-066 · requisito R-66 · ensayo

- **Mide:** highest ambient temperature at which the node meets all its requirements >= 40 degC
- **Condición:** node running at the stated ambient temperature
- **Procedimiento:** `monitor_temperature`
- **Datos de prueba:** temperature logged at the board, the SDR, the card and the inside air each 10 s; derived rise expected about 5.2 degC at 25 W (estimate)
- **Falla si:** the test run with the enclosure lid open or without the supply load
- _nominal:_ node at full load in a chamber at 40 degC ambient for at least 6 h after settling → internal air <= 60 degC, processor below 80 degC, no throttling, all requirements met: highest ambient >= 40 degC
- _error:_ fan removed from the cooler → processor reaches 70 degC then 80 degC: thermal conditions flagged (E-RES-002, E-RES-003); the test fails at 40 degC
- _edge:_ ambient 40 degC and 41 degC → 40 degC required; 41 degC recorded as margin

### P-067 · requisito R-67 · demostración

- **Mide:** users or roles denied access to the web view or to the saved screening reports <= 0 count
- **Condición:** users of the network to which the node is connected
- **Procedimiento:** `serve_view_request`
- **Datos de prueba:** the refusal rule reads only queue length and wait time; verified by sending the same request from 5 different addresses
- **Falla si:** an address list or a token check in front of the service
- _nominal:_ users on several machines of the network open the views and download a saved report with no login → users or roles denied: 0
- _error:_ 80 clients at the same moment (E-WEB-005) → some get 503 with Retry-After by queue length only; none is denied by identity; they succeed on retry
- _edge:_ a request with a role header or a cookie → ignored; the same answer for everyone

### P-068 · requisito R-69 · inspección

- **Mide:** integration bandwidth used for the channel power >= 256 kHz
- **Condición:** configuration record of the calibration and of each scan
- **Procedimiento:** `estimate_channel_power`
- **Datos de prueba:** bandwidth = bins x 2,441.40625 Hz = 105 x 2,441.40625 = 256,347 Hz
- **Falla si:** the window equivalent noise bandwidth used instead of the integration width
- _nominal:_ inspect the estimator configuration and the header of a report → integration bandwidth 256.347 kHz (105 bins of 2,441.40625 Hz) >= 256 kHz
- _error:_ configuration with 100 bins (244 kHz) → rejected: below 256 kHz; the estimator does not start with it
- _edge:_ 105 bins and 104 bins → 105 bins = 256.347 kHz passes; 104 bins = 253.9 kHz fails

### P-069 · requisito R-72 · demostración

- **Mide:** share of acceptance runs in which the node is powered from a 60 Hz mains supply >= 100 %
- **Condición:** acceptance runs in the field
- **Datos de prueba:** log of the supply frequency in each acceptance run; expected 60 Hz
- **Falla si:** the frequency not recorded in the run log
- _nominal:_ run every acceptance run on a 60 Hz mains supply → runs on 60 Hz mains: 100 %
- _error:_ a 50 Hz run → not counted as acceptance for R-72; the supply accepts 47 to 63 Hz and the node works, but the run is repeated at 60 Hz
- _edge:_ mains at 59 Hz and 61 Hz → node runs; the run is counted only at the nominal 60 Hz of the declared condition

### P-070 · requisito R-70 · inspección

- **Mide:** share of saved screening reports that carry the location entered by the user >= 100 %
- **Condición:** location entered before the run
- **Procedimiento:** `report_run_lifecycle`
- **Datos de prueba:** header.json location.country, city, place equal to the configuration values
- **Falla si:** location written only in the first segment, not in the header of a later run
- _nominal:_ enter country, city and place before a run and inspect the saved report → the location appears in 100 % of the reports
- _error:_ location not entered (E-RPT-006) → report carries not configured and location_state not_configured; still counted as stated
- _edge:_ location texts of 256 bytes and of 300 bytes → 256 accepted; 300 rejected by the schema (E-CFG-002)

### P-071 · requisito R-71 · inspección

- **Mide:** GPS receivers in the node <= 0 count
- **Condición:** delivered node
- **Datos de prueba:** list of devices on the USB bus and processes; expected only the SDR
- **Falla si:** a GPS fallback for time
- _nominal:_ inspect the bill of materials and the USB devices of the node → GPS receivers: 0; time comes from the network
- _error:_ a USB GPS dongle plugged in → the node ignores it: no module reads a GPS signal («Servicio de hora»)
- _edge:_ no network time reachable → sync_state unsynced and the scans continue, no GPS fallback

### P-072 · requisito R-73 · ensayo

- **Mide:** share of the results produced before an interruption that are in the saved screening report >= 100 %
- **Condición:** power removed from the node in the middle of a run
- **Procedimiento:** `write_scan_to_report`
- **Datos de prueba:** compare the scan_ids written (the ids the node published) with the ids in the file; expected equal up to the last completed flush
- **Falla si:** flush every 10 scans (loss of up to 9 scans) or the file not closed at the next start
- _nominal:_ remove the power in the middle of a 1 h run at a random moment and restart → every result whose write completed is in the report; at most 1 scan lost (the one being written): 100 % of the produced results
- _error:_ power cut during the write of a scan (0.83 % of the time) → that scan is missing; all earlier scans present; the run is closed interrupted (E-RPT-005)
- _edge:_ cut exactly after the flush of a scan → that scan is present

### P-073 · requisito R-74 · ensayo

- **Mide:** shortest time for taking records that the system accepts when the user configures it >= 10 min
- **Condición:** attempt to configure a shorter time is rejected
- **Procedimiento:** `load_and_validate_site_config`
- **Datos de prueba:** record_time_minutes in the configuration compared with the bounds 10 and 43,200
- **Falla si:** the minimum applied in seconds or hours
- _nominal:_ configure the time for taking records at 10 min and at 12 h (720 min) → both accepted; the run takes records for the configured time
- _error:_ configure 9 min → rejected below `record_time_minimum` = 10 min (E-CFG-002)
- _edge:_ exactly 10 min and 9.9 min → 10 accepted; 9.9 rejected; 43,200 min (`record_time_maximum`) accepted, 43,201 rejected

### P-074 · requisito R-75 · ensayo

- **Mide:** highest mapping-error limit that the system accepts from the user <= 20 kHz
- **Condición:** attempt to set a larger limit is rejected
- **Procedimiento:** `load_and_validate_site_config`
- **Datos de prueba:** mapping_error_limit_khz compared with 1 and 20
- **Falla si:** the limit applied in Hz instead of kHz
- _nominal:_ configure a mapping-error limit of 5 kHz (default) and 20 kHz → both accepted
- _error:_ configure 25 kHz → rejected above `mapping_error_limit_maximum` = 20 kHz (E-CFG-002)
- _edge:_ exactly 20 kHz and 20.1 kHz → 20 accepted; 20.1 rejected; 1 kHz (`mapping_error_limit_minimum`) accepted, 0.9 kHz rejected

## Pruebas de calificación de hardware (21)

### P-075 · requisito R-57 · ensayo

- **Mide:** overflow events and dropped frames in a sustained capture at 10 Msps (20 MB/s) <= 0 count
- **Condición:** 1 h on the board with the SDR on its USB cable, all other modules running
- **Datos de prueba:** frames expected in 1 h of continuous capture = 3,600 s / 13.1072 ms = 274,658; measured frame counter gap = 0
- **Falla si:** a USB link that cannot sustain 20 MB/s (the rate is not cited)
- _nominal:_ capture 10 Msps for 1 h → overflow 0, dropped frames 0, sustained throughput >= 20 MB/s
- _error:_ shorten the ring buffer to 16 frames (`ring_buffer_frames` minimum) → overflows appear: shows the margin of the 64 frames

### P-076 · requisito R-24 · ensayo

- **Mide:** time of the full-scale check on one capture <= 0.05 s
- **Condición:** measured on the board over 72 h inside the compute qualification run
- **Datos de prueba:** 2 comparisons per complex sample x 5,111,200 = 10.2 Mop per capture
- **Falla si:** a check that scans samples twice or in an interpreted loop
- _nominal:_ check 5,111,200 complex samples → time <= 0.05 s (the budget is 0.02 Gop/s over the scan)
- _error:_ capture with a full-scale sample → flag raised in the same time

### P-077 · requisito R-57 · ensayo

- **Mide:** time of the estimator for the three captures of a scan on the board <= 2.5 s
- **Condición:** three recorded captures of 39 frames while the detector and the web service run (8 clients)
- **Datos de prueba:** operations per scan = 3 captures x 2,495 segments x 270,336 flop = 2.023 Gflop
- **Falla si:** an estimator that exceeds its allocation and builds a backlog beyond the 0.8389 s ring buffer
- _nominal:_ estimate 3 captures → <= 2.5 s (`estimator_time_allocation`)
- _error:_ estimator takes 3.0 s → estimator_late flag (E-EST-003); scan flagged late

### P-078 · requisito R-04 · ensayo

- **Mide:** time of the detector for 199 channels <= 0.2 s
- **Condición:** measured on the board inside the compute qualification run
- **Datos de prueba:** about 40,600 operations per scan (el presupuesto de recursos)
- **Falla si:** a detector that sorts all 2,457 points per channel
- _nominal:_ classify 199 channels of one scan → <= 0.2 s (`detector_time_allocation`)
- _error:_ a scan of 199 channels all Uncertain → same bound

### P-079 · requisito R-73 · ensayo

- **Mide:** write and flush latency of one scan to the report on the card <= 0.05 s
- **Condición:** 41.6 KB per scan, 72 h on the deployed card, with two downloads at 20 MB/s running for 1 h of it
- **Datos de prueba:** latency per scan = time of flush completion minus time of publication
- **Falla si:** downloads starving the write so scans queue beyond 10 (E-RPT-001)
- _nominal:_ write 14,400 scans a day for 3 days → 99.9th percentile <= 0.05 s; maximum below 1 s
- _error:_ fill the card to the free-space floor (12.8 GB) → rotation of old segments (E-RPT-002), latency unchanged

### P-080 · requisito R-34 · ensayo

- **Mide:** time of the per-scan and per-minute alert evaluation <= 0.22 s
- **Condición:** measured in the compute qualification run (`alert_scan_evaluation_time` + `alert_minute_evaluation_time`)
- **Datos de prueba:** about 5,194 operations per scan and 17,045 per minute (el presupuesto de recursos)
- **Falla si:** the history read for the prior duty repeated every minute for every channel
- _nominal:_ evaluate a scan and a minute tick with 199 assigned channels → <= 0.02 s and <= 0.2 s
- _error:_ 199 prior-duty readings of 1,440 bins in one minute → <= 0.2 s (worst minute)

### P-081 · requisito R-57 · ensayo

- **Mide:** overflow and dropped-frame events with 8 web clients at the refresh rates <= 0 count
- **Condición:** 1 h with 8 clients asking the 24 h map every 60 s and the spectrum, status and alerts every 6 s; web unit capped at one core
- **Datos de prueba:** answers of 5.73 MB (28,656 bins); load 0.00094 Gop/s estimated
- **Falla si:** the web unit sharing priority with the acquisition
- _nominal:_ 8 clients → events 0; web process at most 100 % of one core
- _error:_ 80 clients → 503 to some; events 0

### P-082 · requisito R-67 · ensayo

- **Mide:** response time of the 24 h power map under 8 clients <= 2 s
- **Condición:** measured in the compute qualification run
- **Datos de prueba:** estimate 0.078 s at an assumed 0.1 Gop/s; the measured effective rate replaces the assumption
- **Falla si:** an answer built by scanning all 744 h of bins
- _nominal:_ 24 h map, 28,656 bins → <= 2 s (`response_time_limit`)
- _error:_ answer exceeding 2 s → 504 and the worker freed (E-WEB-007)

### P-083 · requisito R-48 · ensayo

- **Mide:** processor use of the supervisor <= 25 %
- **Condición:** 72 h, supervisor quota `supervisor_cpu_quota` = 25 % of one core
- **Datos de prueba:** about 250 operations per second (el presupuesto de recursos)
- **Falla si:** a supervisor loop that blocks on the log write and misses the watchdog feed
- _nominal:_ supervise 5 units for 72 h → use far below 25 %; watchdog fed every 5 s
- _error:_ supervisor starved by a busy unit → hardware watchdog resets the node (E-SUP-007) and the event is logged

### P-084 · requisito R-57 · ensayo

- **Mide:** processor use of the whole node averaged over each 5 minutes of a 72 h run <= 70 %
- **Condición:** deployed rate 10 Msps, all units, 8 web clients, plus overflow and dropped-frame counts 0
- **Datos de prueba:** estimate 0.833 Gop/s x 4 cycles = 3.33 of 9.6 Gcycles/s = 34.7 % (assumed 4 cycles per operation)
- **Falla si:** a real cost per operation above the assumed 4 cycles
- _nominal:_ 72 h run → every 5-minute average <= 70 %
- _error:_ raise the load with a second estimator copy → use above 70 % flags the remedy ladder; overflow counts still read

### P-085 · requisito R-66 · ensayo

- **Mide:** air temperature inside the enclosure and processor temperature at 40 degC ambient <= 60 degC
- **Condición:** full load in a chamber at 40 degC for at least 6 h after settling; processor below 80 degC, no throttling, no overflow
- **Datos de prueba:** rise = 25 W / 4.8 W/K = 5.2 degC estimated; the measured conductance replaces the estimate
- **Falla si:** enclosure conductance below the 1.25 W/K needed
- _nominal:_ chamber at 40 degC, full load → inside air <= 60 degC (expected about 45 degC), processor < 80 degC
- _error:_ cooler fan stopped → thermal conditions flagged at 70 and 80 degC (E-RES-002, E-RES-003); test fails

### P-086 · requisito R-72 · ensayo

- **Mide:** supply power of the board, the SDR and the fan <= 20 W
- **Condición:** full load and start-up, measured at the 5 V output of the supply
- **Datos de prueba:** P = V x I from a power meter on the supply output; the antenna port adds 3.3 V x 0.05 A = 0.165 W
- **Falla si:** a start-up peak that trips the supply or under-voltages the board
- _nominal:_ full load for 1 h → <= 20 W (4 A at 5 V)
- _error:_ SDR antenna port power enabled at 50 mA, start-up peak → <= 20 W also at the peak

### P-087 · requisito R-01 · ensayo

- **Mide:** duration of the processing chain of one scan <= 6 s
- **Condición:** over 72 h on the board with all units running
- **Datos de prueba:** stage times per scan from the logs: captures 1.8335, estimator <= 2.5, detector <= 0.2, record builder <= 0.15, others <= 0.3
- **Falla si:** stages that do not overlap and a chain above the period (tight row el presupuesto de recursos)
- _nominal:_ chain from scan start to the report write → maximum <= 6 s; nominal about 3.5 s
- _error:_ chain longer than 7 s → scan_late flag (E-ACQ-005); the remedy ladder applies

### P-088 · requisito R-24 · ensayo

- **Mide:** strongest channel level at the SDR antenna port <= -5 dBm
- **Condición:** deployed antenna and cable at the site before the 72 h run
- **Datos de prueba:** level = field level + antenna gain 2 dBi - cable loss up to 1.8 dB
- **Falla si:** a strong local station damaging or clipping the input
- _nominal:_ measure the strongest channel with the calibrated node → level at or below -5 dBm minus the margin the front-end allows
- _error:_ level above -5 dBm → the antenna is attenuated or moved: the SDR input limit of -5 dBm would be exceeded (damage above)

### P-089 · requisito R-04 · ensayo

- **Mide:** detection of an SNR 0 dB carrier without an external low-noise amplifier >= 95 %
- **Condición:** 20 occupied observations at SNR 0 dB from 10 channels with the receiver noise figure and ADC quantization noise at the deployed gains
- **Datos de prueba:** excess 3.01 dB over a noise reference with uncertainty 0.503 dB: detection 99.87 % expected
- **Falla si:** a quantization-noise floor that the detector takes as a clean noise reference
- _nominal:_ carrier at noise + 3.01 dB → 19 of 20 detected
- _error:_ noise floor within 6 dB of the ADC quantization floor → noise reference flagged unreliable (uncertain_noise_unreliable) and the channels Uncertain, not false Free

### P-090 · requisito R-50 · ensayo

- **Mide:** channel-mapping error plus source frequency uncertainty at 40 degC <= 5 kHz
- **Condición:** frequency correction measured at 25 degC and at 40 degC with the reference tone at 100 MHz
- **Datos de prueba:** error = 1.2207 + 0.2441 + crystal term (up to 2.0 kHz) + 0.1 kHz source = 3.56 kHz
- **Falla si:** a crystal that drifts beyond the tolerance over temperature
- _nominal:_ correction at 25 degC and 40 degC → drift between them within the 2 kHz crystal term at 100 MHz (20 ppm)
- _error:_ correction above 20 ppm at 40 degC → state out_of_limit and the calibration invalid

### P-091 · requisito R-04 · ensayo

- **Mide:** detection and false alarm of a weak channel beside a strong one >= 95 %
- **Condición:** carrier on channel k and a carrier 20 dB stronger on channel k+1 (overlap of 64 of 105 bins)
- **Datos de prueba:** R_k = 10 log10(inner 7 points / flank 12 points) >= `own_carrier_ratio_min` = 0 dB
- **Falla si:** leakage of the neighbour read as the own carrier
- _nominal:_ isolated carrier SNR 0 dB → detected (own-carrier ratio >= 0 dB)
- _error:_ vacant channel beside the strong carrier → not Occupied: Uncertain (uncertain_adjacent_leakage)

### P-092 · requisito R-55 · ensayo

- **Mide:** gain step sizes and range of the baseband stage >= 1 count
- **Condición:** measure the gain of the deployed configuration (0, 16, 16 dB) with the calibration source at several levels
- **Datos de prueba:** levels -100 to -20 dBm in 5 dB steps (`sweep_level_min` to `sweep_step`)
- **Falla si:** an assumed gain used when the real step differs
- _nominal:_ sweep with the calibration source → gains within the documented values; dynamic range recorded (el criterio de R-55)
- _error:_ a gain step different from the setting → the calibration record carries the measured value; a mismatch with the setting makes the configuration undeployable

### P-093 · requisito R-65 · ensayo

- **Mide:** water and dust ingress at the cable entries and mounting parts <= 0 count
- **Condición:** assembled enclosure with the cable entries and mast adapter actually used
- **Datos de prueba:** as el criterio de R-65: jet 6.3 mm nozzle 12.5 l/min at 3 m
- **Falla si:** parts without a read datasheet value leaving an opening
- _nominal:_ IP65 jet and dust test of the assembly → no ingress
- _error:_ entry without a gland → ingress observed; the entry must be fitted

### P-094 · requisito R-53 · análisis

- **Mide:** cost of one complete node with dated prices <= 3200 USD
- **Condición:** price of every item taken from a dated source at the purchase date
- **Datos de prueba:** sum of price x quantity with source date
- **Falla si:** undated listings used for the cost check
- _nominal:_ dated price list → total <= 3,200 USD
- _error:_ an undated price → the total is unverified

### P-095 · requisito R-65 · inspección

- **Mide:** the meaning of the IP65 class (IEC 60529) used by the test >= 1 count
- **Condición:** snapshot of the IP65 definition (dust-tight, water jets) attached to the test record
- **Datos de prueba:** IP6X dust-tight; IPX5 water jet of 12.5 l/min at 3 m
- **Falla si:** a test written against an unverified reading of IP65
- _nominal:_ definition attached → the test of el criterio de R-65 uses it
- _error:_ definition missing → the test is not accepted

## Pruebas de procedimiento (6)

### P-096 · requisito R-10 · ensayo

- **Mide:** offsets table, dynamic range and expanded uncertainty of an establishment <= 2.5 dB
- **Condición:** expanded uncertainty of the calibrated channel power at most `total_uncertainty_limit` and the acceptance criteria of `establish_amplitude_calibration` step 9 met
- **Procedimiento:** `establish_amplitude_calibration`
- **Datos de prueba:** expanded = sqrt(0.5^2 + 0.3^2 + 0.1^2 + 0.015^2 + 0.5^2 + 1.0^2 + 0.2^2) = sqrt(1.6402) = 1.281 dB
- **Falla si:** a component of the budget missing from the root sum of squares
- _nominal:_ establish with a traceable source of 0.5 dB (k = 2) at 24 points → uncertainty 1.28 dB <= 2.5 dB; record written with sha256
- _error:_ source uncertainty 0.8 dB → refused (E-CAL-004); no record
- _edge:_ interpolation residual 0.5 dB and 0.51 dB → 0.5 accepted; 0.51 fails the criteria (E-CAL-003)

### P-097 · requisito R-19 · ensayo

- **Mide:** largest difference of a verification against the tolerance <= 1.0 dB
- **Condición:** 12 points (6 channels x 2 levels), tolerance `verification_tolerance` plus measurement uncertainty 0.59 dB (k = 2)
- **Procedimiento:** `verify_amplitude_correction`
- **Datos de prueba:** pass if |d| <= 1.0; fail if |d| > 1.0 + 0.59 = 1.59; between is inconclusive
- **Falla si:** inconclusive treated as pass
- _nominal:_ all 12 differences within 1.0 dB → result pass; verified_until set; state valid
- _error:_ one difference 1.7 dB → fail: above 1.0 + 0.59 (E-VER-002), state invalid
- _edge:_ one difference 1.4 dB → inconclusive (above 1.0 and not above 1.59): repeat once (E-VER-003)

### P-098 · requisito R-51 · ensayo

- **Mide:** agreement of the power points between two sites >= 83.3 %
- **Condición:** 10 of 12 points with En <= 1 and none above 6 dB; both screening criteria and the report criterion pass
- **Procedimiento:** `compare_two_sites`
- **Datos de prueba:** En(i) = |D_A - D_B| / 1.993 dB for default uncertainties
- **Falla si:** hard limit applied as 6 dB per site instead of between sites
- _nominal:_ 12 points: 11 agree → pass (91.7 %)
- _error:_ a record with independence flags false (E-REP-002) → inconclusive, verification repeated
- _edge:_ 10 agree, then 9 agree; one point at 6.0 dB and at 6.01 dB → 10 passes, 9 fails; 6.0 dB passes the hard limit and 6.01 dB fails it

### P-099 · requisito R-48 · ensayo

- **Mide:** time from the failure of a process to its first complete scan after the restart <= 72 s
- **Condición:** kill the measure process; kill store_alert, report and web in turn
- **Procedimiento:** `supervise_processes`
- **Datos de prueba:** waits 5 x 2^(k-1) capped at 60 s; loop at the fifth restart in 600 s; reboot after 1,800 s in the loop
- **Falla si:** the reboot count kept only in memory
- _nominal:_ kill the measure process → first complete scan <= 72 s, counted outage 54 s
- _error:_ five kills in 10 minutes → restart_loop shown; waits 5, 10, 20, 40, 60 s (E-SUP-003)
- _edge:_ three reboots ordered within 24 h, then a fourth request after a reboot → no fourth reboot: the count is restored from the supervisor log

### P-100 · requisito R-73 · ensayo

- **Mide:** time from a power return to the first complete scan and state of the interrupted run <= 300 s
- **Condición:** power removed during a run and restored
- **Procedimiento:** `start_node`
- **Datos de prueba:** marker supervisor/clean-stop absent means unclean; the previous run is closed with the end time of progress.json
- **Falla si:** the interrupted run left open or the start waiting for time synchronisation
- _nominal:_ cut and restore the power → first complete scan <= 300 s; unclean_boot true
- _error:_ swap area active at start (E-HIS-004) → only report and web start; node_state not_measuring with the reason
- _edge:_ first start with no earlier file → not an unclean boot

### P-101 · requisito R-49 · análisis

- **Mide:** share of time points counted available >= 95 %
- **Condición:** synthetic reports of a 30-day window
- **Procedimiento:** `compute_availability`
- **Datos de prueba:** 432,000 points every 6 s; an outage of D s counts D - 18 s
- **Falla si:** outages counted in full from the failure
- _nominal:_ report with 3 outages of 72 s → share 99.99 %
- _error:_ report missing for one day → those 14,400 points unavailable
- _edge:_ 21,600 unavailable points and 21,601 → exactly 95.000 % passes; 21,601 fails

## Pruebas de integración (33)

### P-120 · requisito R-28 · ensayo

- **Mide:** conforming and non-conforming record of `time_status` time_status = 1 count
- **Condición:** boundary el servicio de hora to el constructor de registros, schema version 1.0
- **Datos de prueba:** record built from the field table of `time_status` with values at the range ends
- **Falla si:** a consumer that accepts a record of `time_status` with utc_us missing or out of range
- _nominal:_ a record with every required field of `time_status` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field utc_us removed → rejected by the consumer with the code E-TIME-001; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-121 · requisito R-52 · ensayo

- **Mide:** conforming and non-conforming record of `site_config` site_config = 1 count
- **Condición:** boundary la configuración del sitio to el servicio de adquisición, schema version 1.1
- **Datos de prueba:** record built from the field table of `site_config` with values at the range ends
- **Falla si:** a consumer that accepts a record of `site_config` with schema_version missing or out of range
- _nominal:_ a record with every required field of `site_config` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field schema_version removed → rejected by the consumer with the code E-CFG-002; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-122 · requisito R-16 · ensayo

- **Mide:** conforming and non-conforming record of `station_assignment_reference` station_assignment_reference = 1 count
- **Condición:** boundary «Configuración del sitio» to el comparador de asignaciones, schema version 1.0
- **Datos de prueba:** record built from the field table of `station_assignment_reference` with values at the range ends
- **Falla si:** a consumer that accepts a record of `station_assignment_reference` with schema_version missing or out of range
- _nominal:_ a record with every required field of `station_assignment_reference` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field schema_version removed → rejected by the consumer with the code E-CFG-003; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-123 · requisito R-52 · ensayo

- **Mide:** conforming and non-conforming record of `config_status` config_status = 1 count
- **Condición:** boundary la configuración del sitio to el constructor de registros, schema version 1.0
- **Datos de prueba:** record built from the field table of `config_status` with values at the range ends
- **Falla si:** a consumer that accepts a record of `config_status` with config_state missing or out of range
- _nominal:_ a record with every required field of `config_status` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field config_state removed → rejected by the consumer with the code E-SUP-005; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-124 · requisito R-22 · ensayo

- **Mide:** conforming and non-conforming record of `capture_block` capture_block = 1 count
- **Condición:** boundary el servicio de adquisición to el estimador espectral, schema version 1.0
- **Datos de prueba:** record built from the field table of `capture_block` with values at the range ends
- **Falla si:** a consumer that accepts a record of `capture_block` with scan_id missing or out of range
- _nominal:_ a record with every required field of `capture_block` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field scan_id removed → rejected by the consumer with the code E-SUP-005; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-125 · requisito R-25 · ensayo

- **Mide:** conforming and non-conforming record of `acquisition_counters` acquisition_counters = 1 count
- **Condición:** boundary el servicio de adquisición to el constructor de registros, schema version 1.0
- **Datos de prueba:** record built from the field table of `acquisition_counters` with values at the range ends
- **Falla si:** a consumer that accepts a record of `acquisition_counters` with scan_id missing or out of range
- _nominal:_ a record with every required field of `acquisition_counters` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field scan_id removed → rejected by the consumer with the code E-SUP-005; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-126 · requisito R-09 · ensayo

- **Mide:** conforming and non-conforming record of `channel_power_scan` channel_power_scan = 1 count
- **Condición:** boundary el estimador espectral to el gestor de calibración, schema version 1.0
- **Datos de prueba:** record built from the field table of `channel_power_scan` with values at the range ends
- **Falla si:** a consumer that accepts a record of `channel_power_scan` with scan_id missing or out of range
- _nominal:_ a record with every required field of `channel_power_scan` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field scan_id removed → rejected by the consumer with the code E-SUP-005; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-127 · requisito R-42 · ensayo

- **Mide:** conforming and non-conforming record of `spectrum_snapshot` spectrum_snapshot = 1 count
- **Condición:** boundary el estimador espectral to el gestor de calibración, schema version 1.0
- **Datos de prueba:** record built from the field table of `spectrum_snapshot` with values at the range ends
- **Falla si:** a consumer that accepts a record of `spectrum_snapshot` with scan_id missing or out of range
- _nominal:_ a record with every required field of `spectrum_snapshot` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field scan_id removed → rejected by the consumer with the code E-SUP-005; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-128 · requisito R-56 · ensayo

- **Mide:** conforming and non-conforming record of `estimator_control` estimator_control = 1 count
- **Condición:** boundary el gestor de calibración to el estimador espectral, schema version 1.0
- **Datos de prueba:** record built from the field table of `estimator_control` with values at the range ends
- **Falla si:** a consumer that accepts a record of `estimator_control` with frequency_correction_ppm missing or out of range
- _nominal:_ a record with every required field of `estimator_control` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field frequency_correction_ppm removed → rejected by the consumer with the code E-SUP-005; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-129 · requisito R-17 · ensayo

- **Mide:** conforming and non-conforming record of `calibration_record` calibration_record = 1 count
- **Condición:** boundary el gestor de calibración to el constructor de registros, schema version 1.0
- **Datos de prueba:** record built from the field table of `calibration_record` with values at the range ends
- **Falla si:** a consumer that accepts a record of `calibration_record` with record_id missing or out of range
- _nominal:_ a record with every required field of `calibration_record` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field record_id removed → rejected by the consumer with the code E-CAL-005; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-130 · requisito R-09 · ensayo

- **Mide:** conforming and non-conforming record of `calibrated_channel_power` calibrated_channel_power = 1 count
- **Condición:** boundary el gestor de calibración to el detector de ocupación, schema version 1.0
- **Datos de prueba:** record built from the field table of `calibrated_channel_power` with values at the range ends
- **Falla si:** a consumer that accepts a record of `calibrated_channel_power` with scan_id missing or out of range
- _nominal:_ a record with every required field of `calibrated_channel_power` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field scan_id removed → rejected by the consumer with the code E-SUP-005; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-131 · requisito R-42 · ensayo

- **Mide:** conforming and non-conforming record of `calibrated_spectrum` calibrated_spectrum = 1 count
- **Condición:** boundary el gestor de calibración to el constructor de registros, schema version 1.0
- **Datos de prueba:** record built from the field table of `calibrated_spectrum` with values at the range ends
- **Falla si:** a consumer that accepts a record of `calibrated_spectrum` with scan_id missing or out of range
- _nominal:_ a record with every required field of `calibrated_spectrum` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field scan_id removed → rejected by the consumer with the code E-SUP-005; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-132 · requisito R-03 · ensayo

- **Mide:** conforming and non-conforming record of `occupancy_scan` occupancy_scan = 1 count
- **Condición:** boundary el detector de ocupación to el comparador de asignaciones, schema version 1.0
- **Datos de prueba:** record built from the field table of `occupancy_scan` with values at the range ends
- **Falla si:** a consumer that accepts a record of `occupancy_scan` with scan_id missing or out of range
- _nominal:_ a record with every required field of `occupancy_scan` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field scan_id removed → rejected by the consumer with the code E-SUP-005; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-133 · requisito R-08 · ensayo

- **Mide:** conforming and non-conforming record of `duty_cycle_report` duty_cycle_report = 1 count
- **Condición:** boundary el detector de ocupación to el comparador de asignaciones, schema version 1.0
- **Datos de prueba:** record built from the field table of `duty_cycle_report` with values at the range ends
- **Falla si:** a consumer that accepts a record of `duty_cycle_report` with interval_start_utc_us missing or out of range
- _nominal:_ a record with every required field of `duty_cycle_report` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field interval_start_utc_us removed → rejected by the consumer with the code E-SUP-005; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-134 · requisito R-19 · ensayo

- **Mide:** conforming and non-conforming record of `validation_record` validation_record = 1 count
- **Condición:** boundary el gestor de calibración to el constructor de registros, schema version 1.0
- **Datos de prueba:** record built from the field table of `validation_record` with values at the range ends
- **Falla si:** a consumer that accepts a record of `validation_record` with validation_id missing or out of range
- _nominal:_ a record with every required field of `validation_record` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field validation_id removed → rejected by the consumer with the code E-VER-005; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-135 · requisito R-19 · ensayo

- **Mide:** conforming and non-conforming record of `calibration_validity` calibration_validity = 1 count
- **Condición:** boundary el gestor de calibración to el motor de alertas, schema version 1.0
- **Datos de prueba:** record built from the field table of `calibration_validity` with values at the range ends
- **Falla si:** a consumer that accepts a record of `calibration_validity` with record_id missing or out of range
- _nominal:_ a record with every required field of `calibration_validity` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field record_id removed → rejected by the consumer with the code E-SUP-005; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-136 · requisito R-15 · ensayo

- **Mide:** conforming and non-conforming record of `assignment_comparison_scan` assignment_comparison_scan = 1 count
- **Condición:** boundary el comparador de asignaciones to el constructor de registros, schema version 1.0
- **Datos de prueba:** record built from the field table of `assignment_comparison_scan` with values at the range ends
- **Falla si:** a consumer that accepts a record of `assignment_comparison_scan` with scan_id missing or out of range
- _nominal:_ a record with every required field of `assignment_comparison_scan` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field scan_id removed → rejected by the consumer with the code E-SUP-005; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-137 · requisito R-23 · ensayo

- **Mide:** conforming and non-conforming record of `scan_header` scan_header = 1 count
- **Condición:** boundary el constructor de registros to el historial en memoria, schema version 1.0
- **Datos de prueba:** record built from the field table of `scan_header` with values at the range ends
- **Falla si:** a consumer that accepts a record of `scan_header` with schema_version missing or out of range
- _nominal:_ a record with every required field of `scan_header` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field schema_version removed → rejected by the consumer with the code E-SUP-005; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-138 · requisito R-11 · ensayo

- **Mide:** conforming and non-conforming record of `channel_record` channel_record = 1 count
- **Condición:** boundary el constructor de registros to el historial en memoria, schema version 1.0
- **Datos de prueba:** record built from the field table of `channel_record` with values at the range ends
- **Falla si:** a consumer that accepts a record of `channel_record` with scan_id missing or out of range
- _nominal:_ a record with every required field of `channel_record` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field scan_id removed → rejected by the consumer with the code E-SUP-005; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-139 · requisito R-27 · ensayo

- **Mide:** conforming and non-conforming record of `health_record` health_record = 1 count
- **Condición:** boundary el constructor de registros to el motor de alertas, schema version 1.0
- **Datos de prueba:** record built from the field table of `health_record` with values at the range ends
- **Falla si:** a consumer that accepts a record of `health_record` with scan_id missing or out of range
- _nominal:_ a record with every required field of `health_record` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field scan_id removed → rejected by the consumer with the code E-SUP-005; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-140 · requisito R-41 · ensayo

- **Mide:** conforming and non-conforming record of `history_bins_response` history_bins_response = 1 count
- **Condición:** boundary el historial en memoria to el servicio web, schema version 1.0
- **Datos de prueba:** record built from the field table of `history_bins_response` with values at the range ends
- **Falla si:** a consumer that accepts a record of `history_bins_response` with history_start_utc_us missing or out of range
- _nominal:_ a record with every required field of `history_bins_response` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field history_start_utc_us removed → rejected by the consumer with the code E-SUP-005; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-141 · requisito R-39 · ensayo

- **Mide:** conforming and non-conforming record of `history_series_response` history_series_response = 1 count
- **Condición:** boundary el historial en memoria to el motor de alertas, schema version 1.1
- **Datos de prueba:** record built from the field table of `history_series_response` with values at the range ends
- **Falla si:** a consumer that accepts a record of `history_series_response` with history_start_utc_us missing or out of range
- _nominal:_ a record with every required field of `history_series_response` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field history_start_utc_us removed → rejected by the consumer with the code E-SUP-005; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-142 · requisito R-62 · ensayo

- **Mide:** conforming and non-conforming record of `report_header` report_header = 1 count
- **Condición:** boundary el escritor de informes to el servicio web, schema version 1.0
- **Datos de prueba:** record built from the field table of `report_header` with values at the range ends
- **Falla si:** a consumer that accepts a record of `report_header` with run_id missing or out of range
- _nominal:_ a record with every required field of `report_header` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field run_id removed → rejected by the consumer with the code E-RPT-004; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-143 · requisito R-62 · ensayo

- **Mide:** conforming and non-conforming record of `report_lines` report_lines = 1 count
- **Condición:** boundary el escritor de informes to el servicio web, schema version 1.0
- **Datos de prueba:** record built from the field table of `report_lines` with values at the range ends
- **Falla si:** a consumer that accepts a record of `report_lines` with S line missing or out of range
- _nominal:_ a record with every required field of `report_lines` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field S line removed → rejected by the consumer with the code E-RPT-004; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-144 · requisito R-62 · ensayo

- **Mide:** conforming and non-conforming record of `report_listing` report_listing = 1 count
- **Condición:** boundary el escritor de informes to el servicio web, schema version 1.0
- **Datos de prueba:** record built from the field table of `report_listing` with values at the range ends
- **Falla si:** a consumer that accepts a record of `report_listing` with runs[].run_id missing or out of range
- _nominal:_ a record with every required field of `report_listing` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field runs[].run_id removed → rejected by the consumer with the code E-WEB-006; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-145 · requisito R-73 · ensayo

- **Mide:** conforming and non-conforming record of `storage_status` storage_status = 1 count
- **Condición:** boundary el escritor de informes to el motor de alertas, schema version 1.0
- **Datos de prueba:** record built from the field table of `storage_status` with values at the range ends
- **Falla si:** a consumer that accepts a record of `storage_status` with report_state missing or out of range
- _nominal:_ a record with every required field of `storage_status` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field report_state removed → rejected by the consumer with the code E-SUP-005; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-146 · requisito R-33 · ensayo

- **Mide:** conforming and non-conforming record of `alert_event` alert_event = 1 count
- **Condición:** boundary el motor de alertas to el servicio web, schema version 1.0
- **Datos de prueba:** record built from the field table of `alert_event` with values at the range ends
- **Falla si:** a consumer that accepts a record of `alert_event` with alert_id missing or out of range
- _nominal:_ a record with every required field of `alert_event` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field alert_id removed → rejected by the consumer with the code E-SUP-005; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-147 · requisito R-34 · ensayo

- **Mide:** conforming and non-conforming record of `alert_status_response` alert_status_response = 1 count
- **Condición:** boundary el motor de alertas to el servicio web, schema version 1.1
- **Datos de prueba:** record built from the field table of `alert_status_response` with values at the range ends
- **Falla si:** a consumer that accepts a record of `alert_status_response` with sensor missing or out of range
- _nominal:_ a record with every required field of `alert_status_response` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field sensor removed → rejected by the consumer with the code E-SUP-005; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-148 · requisito R-32 · ensayo

- **Mide:** conforming and non-conforming record of `web_view_data` web_view_data = 1 count
- **Condición:** boundary el servicio web to el servicio web, schema version 1.0
- **Datos de prueba:** record built from the field table of `web_view_data` with values at the range ends
- **Falla si:** a consumer that accepts a record of `web_view_data` with evidence_label missing or out of range
- _nominal:_ a record with every required field of `web_view_data` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field evidence_label removed → rejected by the consumer with the code E-WEB-006; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-149 · requisito R-41 · ensayo

- **Mide:** conforming and non-conforming record of `web_request` web_request = 1 count
- **Condición:** boundary el servicio web to el servicio web, schema version 1.0
- **Datos de prueba:** record built from the field table of `web_request` with values at the range ends
- **Falla si:** a consumer that accepts a record of `web_request` with method missing or out of range
- _nominal:_ a record with every required field of `web_request` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field method removed → rejected by the consumer with the code E-WEB-003; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-150 · requisito R-37 · ensayo

- **Mide:** conforming and non-conforming record of `supervisor_status` supervisor_status = 1 count
- **Condición:** boundary el supervisor to el servicio web, schema version 1.0
- **Datos de prueba:** record built from the field table of `supervisor_status` with values at the range ends
- **Falla si:** a consumer that accepts a record of `supervisor_status` with liveness_seq missing or out of range
- _nominal:_ a record with every required field of `supervisor_status` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field liveness_seq removed → rejected by the consumer with the code E-SUP-005; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-151 · requisito R-48 · ensayo

- **Mide:** conforming and non-conforming record of `supervisor_log_line` supervisor_log_line = 1 count
- **Condición:** boundary el supervisor to «Pruebas», schema version 1.0
- **Datos de prueba:** record built from the field table of `supervisor_log_line` with values at the range ends
- **Falla si:** a consumer that accepts a record of `supervisor_log_line` with utc_us missing or out of range
- _nominal:_ a record with every required field of `supervisor_log_line` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field utc_us removed → rejected by the consumer with the code E-SUP-008; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

### P-152 · requisito R-51 · ensayo

- **Mide:** conforming and non-conforming record of `cross_site_comparison` cross_site_comparison = 1 count
- **Condición:** boundary «Reproducibilidad entre sitios» to «Pruebas», schema version 1.0
- **Datos de prueba:** record built from the field table of `cross_site_comparison` with values at the range ends
- **Falla si:** a consumer that accepts a record of `cross_site_comparison` with comparison_id missing or out of range
- _nominal:_ a record with every required field of `cross_site_comparison` inside its range → accepted by the consumer unchanged
- _error:_ the same record with the required field comparison_id removed → rejected by the consumer with the code E-REP-001; no partial record is used
- _edge:_ a field at the end of its stated range, and one just outside it → the first accepted, the second rejected with the same code

## Pruebas de unitaria (22)

### P-102 · requisito R-74 · ensayo

- **Mide:** configuration file size rejected above the limit <= 1048576 bytes
- **Condición:** worked check of «Configuración del sitio»
- **Datos de prueba:** 199 x 400 + 4,096 = 83,696 bytes; about 13 times below the limit
- **Falla si:** limit applied in KB instead of bytes
- _nominal:_ configuration of 79,600 bytes (199 stations) plus 4 KiB → accepted
- _error:_ file of 1,048,577 bytes → rejected (E-CFG-004)
- _edge:_ 1,048,576 bytes → accepted

### P-103 · requisito R-28 · ensayo

- **Mide:** clock offset limit for the synced state <= 50 ms
- **Condición:** worked check of «Servicio de hora»
- **Datos de prueba:** stamp resolution 1 us; `max_clock_offset` 50 ms; `max_sync_age` 3,600 s
- **Falla si:** offset compared in seconds
- _nominal:_ estimated offset 20 ms, sync age 100 s → sync_state synced
- _error:_ offset 51 ms → unsynced (E-TIME-001)
- _edge:_ offset 50 ms and sync age 3,600 s → synced; 3,601 s unsynced

### P-104 · requisito R-02 · ensayo

- **Mide:** channels of each step = 199 count
- **Condición:** worked check of «Adquisición y barrido»
- **Datos de prueba:** frame = 131,072 samples at 10 Msps = 13.1072 ms; dwell 39 frames = 0.5112 s; 3 x 0.5112 + 3 x 0.1 = 1.8336 s
- **Falla si:** a channel measured in two steps or none
- _nominal:_ steps with centres 90.25, 97.75, 105.25 MHz → channels 1 to 60, 61 to 135, 136 to 199: 60 + 75 + 64 = 199
- _error:_ retune fails on step 2 (E-ACQ-003) → 75 channels flagged Uncertain; 199 records still produced
- _edge:_ channels 60/61 and 135/136 → each assigned to exactly one step

### P-105 · requisito R-69 · ensayo

- **Mide:** integration bandwidth >= 256 kHz
- **Condición:** worked check of «Estimador espectral»
- **Datos de prueba:** 10,000,000 / 4,096 = 2,441.40625 Hz; 105 x 2,441.40625 = 256,347 Hz; segments 2,495
- **Falla si:** Hann ENBW used as width
- _nominal:_ FFT 4,096 at 10 Msps → bin spacing 2,441.40625 Hz; 105 bins = 256.347 kHz
- _error:_ a channel power zero (E-EST-002) → channel flagged invalid, not released
- _edge:_ 104 bins → 253.9 kHz fails

### P-106 · requisito R-11 · ensayo

- **Mide:** expanded uncertainty of the default channel <= 2.5 dB
- **Condición:** worked check of «Calibración de amplitud»
- **Datos de prueba:** sqrt(0.25 + 0.09 + 0.01 + 0.000225 + 0.25 + 1.0 + 0.04) = sqrt(1.640225) = 1.2807 dB
- **Falla si:** half-width reported as a full width
- _nominal:_ budget of 7 components → 1.281 dB, written as 1.28
- _error:_ DC-adjacent channel 22 → 1.37 dB
- _edge:_ interpolation residual 0.5 dB → component present in the sum

### P-107 · requisito R-19 · ensayo

- **Mide:** duration of one verification <= 39 min
- **Condición:** worked check of «Verificación periódica»
- **Datos de prueba:** downtime at the 4-day interval over 30 days: ceil(30 / 4) = 8 x 39 = 312 min
- **Falla si:** repeat counted twice
- _nominal:_ 6 channels x 2 levels → 12 measurements; 10 + 12 x 2 + 5 = 39 min
- _error:_ one inconclusive repeat → 78 min, the range maximum
- _edge:_ interval 345,600 s and 3,456,000 s → accepted; one below or above rejected (E-VER-006)

### P-108 · requisito R-05 · ensayo

- **Mide:** expected false-alarm probability <= 5 %
- **Condición:** worked check of «Detector de ocupación»
- **Datos de prueba:** thresholds 1.5 / 1.0 dB, hysteresis 0.5 dB, release margin 10 dB
- **Falla si:** hysteresis applied on the wrong side
- _nominal:_ vacant channel, noise reference error N(0, 0.503 dB), threshold 1.5 dB → Q(1.5 / 0.503) = Q(2.98) = 0.14 %
- _error:_ noise reference unreliable (E-DET-001) → channels Uncertain, none Occupied
- _edge:_ excess 1.5 dB and 1.49 dB → 1.5 Occupied; 1.49 not Occupied (hysteresis 0.5 dB)

### P-109 · requisito R-15 · ensayo

- **Mide:** comparison results = 4 count
- **Condición:** worked check of «Comparador con asignaciones»
- **Datos de prueba:** Occupied + unassigned = unassigned-occupied; Free + assigned = assigned-free
- **Falla si:** Uncertain mapped to assigned-free
- _nominal:_ Occupied + assigned; Free + unassigned → consistent for both
- _error:_ reference missing (E-el componente) → indeterminate for all 199
- _edge:_ Uncertain on an assigned channel → indeterminate

### P-110 · requisito R-27 · ensayo

- **Mide:** size of one scan message <= 208896 bytes
- **Condición:** worked check of «Registros de escaneo y de salud»
- **Datos de prueba:** 4,096 + 203,776 + 1,024 = 208,896
- **Falla si:** a record of 199 channels dropped silently when one is oversize
- _nominal:_ header 4,096 + 199 x 1,024 + health 1,024 → 208,896 bytes
- _error:_ record above 1,024 bytes (E-REC-003) → free texts shortened to 256 bytes
- _edge:_ a text of 256 and of 257 bytes → 256 kept; 257 shortened

### P-111 · requisito R-62 · ensayo

- **Mide:** report volume per day <= 599.04 MB
- **Condición:** worked check of «Escritor de informes»
- **Datos de prueba:** 41,600 B x 14,400 = 599,040,000 B; segment of 600 scans = 24.96 MB
- **Falla si:** flush every segment instead of every scan
- _nominal:_ 14,400 scans x (199 x 200 + 1,800) bytes → 599.04 MB
- _error:_ write fails (E-RPT-001) → 3 retries at 1 s, then up to 10 scans pending
- _edge:_ free space exactly 12.8 GB → rotation of the oldest closed segment (E-RPT-002)

### P-112 · requisito R-31 · ensayo

- **Mide:** history memory <= 512 MB
- **Condición:** worked check of «Historial en memoria»
- **Datos de prueba:** 213,200,640 + 12,499,200 + 218,724 = 225,918,564 B
- **Falla si:** raw records kept for 744 h
- _nominal:_ 44,640 bins x 199 x 24 B + 446,400 x 28 B + 0.22 MB → 225.9 MB
- _error:_ allocation above the cap (E-HIS-001) → window halved down to 48 h
- _edge:_ UTC stamp moves back by 2 bins (E-HIS-002) → history cleared and restarted

### P-113 · requisito R-35 · ensayo

- **Mide:** credit for 2 declared hours = 7200 s
- **Condición:** worked check of «Motor de alertas»
- **Datos de prueba:** credit = 6 s x n_assigned_free; unexpected occupancy raised at the 3rd consecutive scan
- **Falla si:** Uncertain scans credited
- _nominal:_ 1,200 assigned-free scans x 6 s → 7,200 s = 2 h
- _error:_ reference lost (E-ALR-005) → rules frozen, nothing cleared
- _edge:_ a bin with 3 and with 2 Occupied scans → 3 ends the run, 2 does not

### P-114 · requisito R-41 · ensayo

- **Mide:** bins of the 24 h map <= 40000 count
- **Condición:** worked check of «Servicio web»
- **Datos de prueba:** 144 x 199 = 28,656; 300 s would give 57,312, refused
- **Falla si:** a finer bin that exceeds the cap
- _nominal:_ 24 h at 600 s x 199 channels → 28,656 bins
- _error:_ method DELETE (E-WEB-001) → 405 and nothing changed
- _edge:_ 11 stations selected → 400 (E-WEB-003)

### P-115 · requisito R-48 · ensayo

- **Mide:** restart wait of the fifth restart <= 60 s
- **Condición:** worked check of «Supervisión y manejo de errores»
- **Datos de prueba:** min(5 x 2^(k-1), 60)
- **Falla si:** cap not applied
- _nominal:_ restarts k = 1 to 5 → waits 5, 10, 20, 40, 60 s
- _error:_ invalid message three times in a row (E-SUP-005) → producer restarted
- _edge:_ a process that ran 600 s → wait back to 5 s

### P-116 · requisito R-51 · ensayo

- **Mide:** combined uncertainty of a point <= 1.99 dB
- **Condición:** worked check of «Reproducibilidad entre sitios»
- **Datos de prueba:** sqrt(2 x 1.9865) = 1.993
- **Falla si:** k = 1 and k = 2 values mixed
- _nominal:_ W = sqrt(1.28^2 + 0.59^2) → 1.409 dB per site; combined 1.993 dB
- _error:_ reference uncertainty 0.8 dB (E-REP-003) → comparison refused
- _edge:_ delta 1.99 dB and 2.00 dB → 1.99 agrees; 2.00 does not (En 1.0035)

### P-117 · requisito R-57 · ensayo

- **Mide:** estimator backlog against the ring buffer <= 0.8389 s
- **Condición:** worked check of «Presupuesto de tiempo»
- **Datos de prueba:** ring buffer 64 x 13.1072 ms = 0.8389 s; chain 4.9835 s of 6 s
- **Falla si:** backlog computed over the whole scan instead of one capture
- _nominal:_ 2.5 / 3 - 0.5112 → 0.3221 s (38.4 %)
- _error:_ stall of 0.6 s on top → 0.9221 s: overflow (E-ACQ-002)
- _edge:_ stall of 0.5168 s → exactly at the limit

### P-118 · requisito R-66 · ensayo

- **Mide:** rise of the internal air <= 20 degC
- **Condición:** worked check of «Presupuesto de recursos»
- **Datos de prueba:** allowed rise 60 - 40 = 20 degC; need 25 / 20 = 1.25 W/K; memory sum 1,737.9 MB
- **Falla si:** warning threshold without hysteresis
- _nominal:_ 25 W / 4.8 W/K → 5.2 degC
- _error:_ processor 70 degC (E-RES-002) → condition thermal, node keeps measuring
- _edge:_ processor 65 degC after 70 → condition cleared

### P-119 · requisito R-48 · ensayo

- **Mide:** unavailable time points <= 21600 count
- **Condición:** worked check of «Fiabilidad y disponibilidad»
- **Datos de prueba:** planned 312 + 118 + 155 = 585 min of 2,160
- **Falla si:** availability counted from the failure instant
- _nominal:_ allowed 5 % of 432,000 → 21,600 points = 36 h
- _error:_ reboot not restoring its count → fourth reboot in 24 h refused
- _edge:_ gap of 18 s and 19 s → 18 s no point; 19 s one point

### P-153 · requisito R-06 · ensayo

- **Mide:** LNA gain setting accepted by the acquisition <= 40 dB
- **Condición:** gain settings of the deployed configuration and of the configuration check
- **Datos de prueba:** steps of 8 dB from 0 to 40 dB: 0, 8, 16, 24, 32, 40
- **Falla si:** a setting above the SDR limit sent to the device
- _nominal:_ LNA gain 16 dB (`lna_gain`) → accepted
- _error:_ LNA gain 48 dB → configuration refused; the node does not start measuring with it
- _edge:_ LNA gain 40 dB and 41 dB → 40 accepted; 41 refused

### P-154 · requisito R-07 · ensayo

- **Mide:** RF amplifier gain setting accepted by the acquisition <= 14 dB
- **Condición:** gain settings of the deployed configuration and of the configuration check
- **Datos de prueba:** amplifier states 0 and 14 dB (fixed step)
- **Falla si:** the amplifier switched on at a value other than the two the device has
- _nominal:_ RF amplifier 0 dB (`rf_amp_gain`, amplifier off) → accepted
- _error:_ RF amplifier 20 dB → configuration refused
- _edge:_ 14 dB and 15 dB → 14 accepted; 15 refused

### P-155 · requisito R-08 · ensayo

- **Mide:** integration width against the necessary bandwidth of a stereophonic emission >= 256 kHz
- **Condición:** estimator configuration (FFT 4,096 at 10 Msps, 105 bins)
- **Datos de prueba:** width = 105 x 2,441.40625 Hz = 256,347 Hz
- **Falla si:** an integration width narrower than the emission, losing power at the band edges
- _nominal:_ 105 bins of 2,441.40625 Hz → 256.347 kHz covers the 256 kHz emission
- _error:_ 104 bins → 253.9 kHz: estimator configuration refused
- _edge:_ a stereo carrier of 256 kHz centred in the window → all of its power inside the integration width

### P-156 · requisito R-09 · ensayo

- **Mide:** slow variation of a received signal over a day that the detector must tolerate <= 10 dB
- **Condición:** a fixed carrier whose level varies by +/- 10 dB over 24 h on a channel, noise reference unchanged
- **Datos de prueba:** excess(t) = 10 + 10 sin(2 pi t / 86,400 s) dB; thresholds 1.5 and 1.0 dB
- **Falla si:** a noise reference that follows the signal fading and hides a weak carrier
- _nominal:_ carrier 10 dB above the noise at the start, varying slowly to 0 dB and back to 20 dB → state decided at each scan on the current excess; duty cycle counts scans; no state forced by the trend
- _error:_ the carrier fades to 1.2 dB above the noise → Uncertain between the thresholds (uncertain_between_thresholds), never Free
- _edge:_ variation of exactly 10 dB and of 12 dB → both handled by the same per-scan rule; the noise reference does not follow the signal
