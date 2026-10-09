## AI Production Pipeline for SDR-Based Spectrum Monitoring: A Circular, Iterative Architecture

The circular production pipeline transforms a static sensor array into a living measurement organism. The result is a self-correcting, ever-improving spectrum monitoring system that grows more accurate, efficient, and reliable over time. This pipeline is designed as a self-improving ecosystem; each stage feeds into the next, and the final stage loops back to refine the entire system.

The Production Pipeline embraces five core stages:

Stage 1: RF/DSP Development & Calibration Sandbox (The Sandbox) Purpose: Safe, collaborative space for building and testing DSP algorithms, calibration procedures, and measurement pipelines before field deployment.

 Signal Analysis Notebooks (GNU Radio Companion, Python/SciPy) for rapid DSP prototyping on captured I/Q datasets Hardware-in-the-Loop IDEs for production DSP code development targeting embedded host processors and SDR front-ends Version Control (Git) for DSP block diagrams, calibration coefficients, detection rules, and signal-processing configurations Containerization (Docker) for reproducible DSP environments across development workstations and embedded field targets

Output: Validated DSP blocks, calibrated measurement procedures, and feature prototypes. These outputs enter Stage 2 for array orchestration. Additionally, Stage 1 receives calibration drift reports, validation failures, and uncertainty anomalies from Stage 5 as prioritized inputs for the next development cycle.

Stage 2: Array Orchestration & Multi-Node Coordination (The Engine) Purpose: Coordinate distributed SDR nodes, measurement workflows, and multi-node data fusion.

 Array Orchestrator for scheduling wideband acquisitions and crossnode measurement campaigns Workflow Orchestrators (GNU Radio, Apache Airflow, custom DSP schedulers) for node-level pipeline control Multi-Node Coordination Systems with specialized roles (acquisition scheduler, calibration manager, timing supervisor, fusion arbiter) Data Routing Gateways for measurement metadata transport, local buffering during link outages, and fallback routing when nodes degrade

Output: Structured measurement decisions, capability-eligibility records, eligibility-gated decision records, array-wide task completion, synchronized observation epochs, and traceable chains linking node-level results to array-level regulatory conclusions. Formal compliance decisions shall be produced only after the regulatory context and measurand-specific decision rule have been resolved and the applicable regulatory-use gate has been passed.

Stage 3: Regulatory & Spectral Knowledge Base (The Knowledge Base) Purpose: Provide authoritative regulatory context, licensed station parameters, and historical spectral reference data to ground every measurement in validated information.

- Regulatory & Spectral Data Retrieval
  - Regulatory sources used for formal compliance shall carry an applicability record identifying jurisdiction, competent authority, service, station, effective date, source version, and source-precedence rule. A source shall not drive formal compliance logic until that record establishes its legal or normative role for the deployment.
- Historical spectrum embeddings for trend comparison and anomaly fingerprinting Knowledge Graphs for station relationships, propagation characteristics, array topology, and inter-node calibration histories

Output: Contextual regulatory grounding and versioned measurandspecific decision definitions, including the applicable rule type, limits or permitted region, reference quantities, rule parameters, and regulatory source needed for governed compliance evaluation.

Stage 4: Measurement Configuration & Policy Playbook (The Playbook) Purpose: Standardize and version-control measurement configurations, calibration profiles, and regulatory decision rules.

 Measurement Templates for reusable, parameterized channel plans, detection rules, and spectral analysis configurations Calibration Profile Versioning to track primary, secondary, and relative calibration states, coefficients, and validity periods across nodes A/B Testing to compare DSP algorithm variants against controlled reference signals or qualified datasets before fleet-wide deployment, using versioned acceptance criteria and rollback thresholds Policy Enforcement for safety rules (gain limits, overload prevention), metadata format constraints, capability-eligibility requirements, and measurand-specific regulatory decision-rule integrity

Output: Consistent, governed, and optimized measurement configurations deployable to the array with full traceability to regulatory rule sets and calibration states.

Stage 5: Metrological QA & Array Health Guardrails (The Guardrails)

Purpose: Measure RF and DSP performance, detect metrological drift, validate cross-node consistency, and enforce array health boundaries.

- Evaluation Metrics
  - Carrier-frequency error, calibrated power accuracy, occupied bandwidth containment
  - False occupancy rate, missed detection rate, cross-node consistency score
- Human-in-the-loop review of anomalous regulatory classifications Observability
  - Logging and tracing of sample-loss events, I/Q residuals, DC contamination, timing skew
  - Calibration validity monitoring, reference-lock state tracking, and drift detection
- Processing load, memory consumption, and ADC dynamic range utilization Alerting for real-time anomaly notification on threshold exceedances, node health degradation, and synchronization loss

Output: Performance reports, calibration drift logs, uncertainty scores, and health state classifications. These outputs are consumed by Stage 1 (RF/DSP Development & Calibration Sandbox) to initiate the next improvement cycle, closing the pipeline loop.

Regulatory Decision Authority and Dependency Contract The five stages form a circular production architecture, but they shall not be interpreted as a temporal sequence in which Stage 2 may issue a formal regulatory decision before Stages 3–5 have supplied the control information required by the governing SDR monitoring framework. For each measurand and decision cycle, the following dependencies shall be satisfied before formal decision execution:

- 1. Stage 3 shall provide the authoritative regulatory context and the measurandspecific decision definition, including the applicable rule type, limits or permitted region, reference quantities, and regulatory-source version.
- 2. Stage 4 shall bind that regulatory definition to the deployed measurement template, calibration profile, capability class, and versioned decision configuration.
- 3. Stage 5 shall provide the current metrological-validity and health information required to determine whether the measurement remains eligible for compliance use.
- 4. Stage 2 shall execute the measurement workflow, apply active Stage 4 calibration coefficients to raw I/Q data, and apply the Capability Eligibility & Regulatory-Use Gate before formal decision logic. Only a measurand

that passes this gate may be evaluated using the measurand-specific rule supplied through Stages 3 and 4; that rule shall explicitly define how the measured value and associated measurement uncertainty enter acceptance, rejection, and any indeterminate or guard-band outcome applicable to the rule. Screening-grade results may generate screening or review events but shall remain distinct from formal compliance determinations; unsupported measurands shall be blocked from regulatory decision processing.

Production Promotion and Rollback Gate A Stage 1 deployment candidate shall not enter governed Stage 2 production execution until a versioned promotion record confirms: (i) the Stage 1 validation package and candidate identifier; (ii) the active Controlled Source Specification Baseline and Stage 3 regulatory-rule version; (iii) the Stage 4 measurement template, calibration profile, capability state, acceptance criteria, and rollback thresholds; (iv) a valid Stage 5 metrological and node-health state; and (v) approval by the deployment authority identified in the Stage 4 policy record. Initial activation shall use the node subset or rollout scope authorized by that record. Stage 5 shall evaluate the configured post-deployment acceptance metrics over the defined evaluation interval. Exceedance of a rollback threshold, loss of calibration validity, invalidation of the regulatory baseline, or a safety/health gate failure shall suspend the candidate and restore the last approved compatible configuration. Promotion, rejection, rollback, and restoration events shall be preserved as versioned evidence records.

Inter-Stage Flow and Circular Closure The five stages operate as a closed system through governed handoffs. The numbered stage labels identify functional ownership rather than a mandatory chronological order for regulatory decision execution:

- 1. Stage 1 outputs (validated DSP blocks and calibrated procedures) become deployment candidates for Stage 2 execution under a versioned Stage 4 configuration.
- 2. Stage 3 supplies authoritative regulatory grounding and measurand-specific decision definitions to Stage 4 before those rules are activated in a production measurement configuration.
- 3. Stage 4 publishes the versioned measurement template, calibration profile, capability class, and decision configuration consumed by Stage 2; Stage 5 health and metrological-validity states provide the current eligibility constraints for that execution.
- 4. Stage 2 executes acquisitions, measurand estimation, capability-eligibility gating, and, only for eligible measurands, the configured formal decision logic. Its outputs are structured measurement results, eligibility records, decision records where authorized, and orchestration logs.

- 5. Stage 5 evaluates performance, uncertainty, drift, and cross-node consistency. Its outputs feed Stage 1 as prioritized validation or refactoring targets and may also constrain or downgrade Stage 4 configurations and Stage 2 execution, closing the circle.

The Feedback Loop: Key Mechanisms The circular architecture closes through Stage 5 outputs feeding into Stage 1. Four primary mechanisms drive this continuous refinement:

- 1. Calibration Drift Detection → Stage 5 identifies frequency-reference offset or gain bias beyond Tier 2 limits → Stage 1 executes recalibration experiments → Stage 4 updates calibration profile versions
- 2. Cross-Node Inconsistency → Stage 5 flags persistent disagreement beyond the uncertainty budget → Stage 1 investigates propagation-model or DSPalgorithm errors → Stage 3 updates knowledge graph or station records
- 3. Detection Rule Degradation → Stage 5 evaluates false occupancy and missed detection rates against qualified Ground-Truth Reference Records → Stage 1 prototypes and validates improved channel detection algorithms → Stage 4 evaluates the candidate against the Production Promotion and Rollback Gate → Stage 2 deploys only an approved update to the authorized rollout scope
- 4. Resource Optimization → Stage 5 analyzes ADC dynamic range utilization and processing load → Stage 1 prototypes efficient DSP implementations → Stage 4 simplifies measurement configurations

Ground-Truth Reference Contract False-occupancy and missed-detection metrics used for Stage 5 acceptance or feedback shall be computed only over observations associated with a qualified Ground-Truth Reference Record. The record shall identify the reference source and authority, the labeled signal or occupancy state, time and frequency bounds, alignment tolerances, confidence or review status, and the dataset or event-set version. Qualified sources may include controlled reference transmissions or signal-generator datasets with known truth, or independently reviewed observational labels whose provenance and uncertainty are recorded. Ambiguous or unresolved labels shall be excluded from quantitative acceptance metrics or reported separately as indeterminate. Stage 4 shall version the metric definition, minimum evaluation set, acceptance threshold, and evaluation interval; Stage 5 shall report the numerator, denominator, reference-record identifiers, and excluded/indeterminate cases with every falseoccupancy or missed-detection result used to trigger a production change.

Design Rationale for Circular Architecture

| Property                   | Mechanism                                                                                                                                                                   |               |                         |                |                                                                    |               |
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|-------------------------|----------------|--------------------------------------------------------------------|---------------|
| Iterative Refinement       | Detection algorithms and calibration profiles are updated in Stage 1 based on Stage 5 drift, false-occupancy, and consistency metrics                                       |               |                         |                |                                                                    |               |
| Failure Containment        | Tier 2/3 verification and cross-node consistency checks (Stage 5) are used to detect calibration and measurement failures                                                   |               |                         |                |                                                                    |               |
| Resource Management        | Stage 1 DSP configuration changes are evaluated against the processing load, storage, and backhaul bandwidth constraints identified in Stage 5 observability                |               |                         |                |                                                                    |               |
| Regulatory Traceability    | Stage 5 QA outputs together with Stage 4 configuration versioning support the traceability and evidence-retention requirements of the underlying monitoring framework       |               |                         |                |                                                                    |               |
| Controlled Stage Evolution | Node hardware, algorithms, and regulatory rule sets may originate as changes within their owning stages, but activation shall follow documented dependency-impact analysis, | revalidation, | and version updates for | every affected | downstream configuration, calibration state, uncertainty model, or | decision rule |

## Example Workflow in Action

- 1. RF engineer prototypes and validates a new channel detection algorithm against the qualified reference dataset defined for the candidate (Stage 1).
- 2. The applicable regulatory source, assigned frequencies, emission masks, and rule version are resolved for the intended deployment scope (Stage 3).
- 3. The candidate algorithm is bound to a versioned measurement template, calibration profile, capability class, decision configuration, acceptance criteria, and rollback thresholds (Stage 4).
- 4. Current metrological-validity and node-health states are confirmed, and the Production Promotion and Rollback Gate authorizes a controlled deployment only if all prerequisites are valid (Stages 4–5).
- 5. The array orchestrator deploys the approved candidate to the authorized node subset or fleet and records the activated configuration identifier (Stage 2).
- 6. Metrological QA evaluates false occupancy and missed detection only over observations carrying valid Ground-Truth Reference Records; any reported rate identifies the reference dataset, alignment criteria, and evaluation interval (Stage 5).
- 7. Stage 5 reports feed into Stage 1, triggering: Algorithm version 2.1 created in sandbox (Stage 1) with refined channel detection logic. Knowledge graph updated only when independently supported contextual or station evidence requires a Stage 3 revision. Calibration validity re-evaluated on failure cases; revised calibration coefficients are issued only when supported by calibration evidence and are activated through a new Stage 4 calibration-profile version.
- 8. The cycle repeats through the same promotion gate; performance improvement is accepted only when the versioned Stage 4 criteria are satisfied on qualified Stage 5 evaluation evidence.

Controlled Source Specification Baseline The term "SDR document," "monitoring framework," or "governing SDR monitoring framework" in this pipeline shall refer only to an instantiated and approved Controlled Source Specification Baseline. In this document the deployment-specific baseline is not instantiated; formal Stage 2 compliance execution therefore remains disabled until the Stage 4 baseline record specified here is populated and approved. Before Stage 2 formal compliance execution is enabled, Stage 4 shall bind a baseline record containing the source-document identifier, revision or version, effective date, cryptographic digest or equivalent integrity identifier, approval status, and the applicable section/appendix references used by this pipeline. Stage 3 shall bind regulatory-data records to the same baseline where those records supply implementation requirements. A change to the source specification shall create a new baseline version and trigger documented dependency-impact analysis before affected Stage 4 configurations or Stage 2 decisions are reactivated.

Mapping to SDR Document Architecture The circular pipeline maps directly onto the Controlled Source Specification Baseline as follows:

| Pipeline Stage          | SDR Document Reference                                                 |   | Core Function                                        |
|-------------------------|------------------------------------------------------------------------|---|------------------------------------------------------|
| Stage 1: Sandbox        | Sections 1 (Calibration Tiers), 2 (Functional Decomposition), Appendix | A | DSP/calibration development and validation           |
| Stage 2: Engine         | Sections 4 (Node-Level DSP), 5 (Array-Level Coordination)              |   | Array orchestration and multi-node fusion            |
| Stage 3: Knowledge Base | Section 3 (Measurands, Regulatory Data Source), Introduction           |   | Regulatory grounding and spectral context            |
| Stage 4: Playbook       | Section 3 (Classification, Metadata), Appendix B                       |   | Configuration governance and decision rules          |
| Stage 5: Guardrails     | Sections 1 (Integrity), 3 (Uncertainty), 5 (Health, Consistency)       |   | Metrological QA, drift detection, health enforcement |

Calibration Hierarchy Integration The three-tier calibration strategy defined in Section 1 of the SDR document is embedded within the pipeline loop:

 Tier 1 (Primary) is established and validated in Stage 1, version-controlled in Stage 4, and monitored for expiry in Stage 5. Tier 2 (Secondary) is executed as a scheduled Stage 2 workflow; results feed Stage 5 observability and trigger Stage 1 recalibration when limits are breached. Tier 3 (Relative) is maintained as a Stage 4 configuration artifact and verified by Stage 5 drift detection across the observation bandwidth.

Capability-Class Lifecycle In the Controlled Source Specification Baseline, four capability classes are defined: Unsupported→Screening-Grade → Conditional Compliance-Grade → Compliance-Grade, each step adding a layer of validation obligation on top of the last rather than being a wholly separate track.

The classes evolve through the pipeline:

- 1. A new measurand or algorithm enters the pipeline as Unsupported or Screening-Grade in Stage 1.
- 2. Stage 3 resolves the applicable Controlled Source Specification Baseline, regulatory context, and historical comparison data for the intended observation scope.
- 3. Stage 4 creates and versions the screening measurement template, calibration profile, capability state, and any regulatory decision definition needed for later qualification; formal compliance decision output remains disabled.
- 4. After the Production Promotion and Rollback Gate confirms the authorized screening rollout and current Stage 5 health/metrological-validity prerequisites, Stage 2 deploys the candidate to the approved node subset for controlled observation.
- 5. Stage 5 accumulates the uncertainty, repeatability, cross-node consistency, and health evidence required by the applicable Capability Qualification Record. A measurand may be promoted to Conditional Compliance-Grade only after that record is approved. Promotion from Conditional Compliance-Grade to Compliance-Grade requires that all measurand-specific preconditions in the Controlled Source Specification Baseline be implemented, independently validated, and recorded in the approved Capability Qualification Record and applicable calibration/validation records. If those source preconditions are absent, unresolved, or invalidated, the pipeline shall not authorize the promotion.
- 6. Promotion or demotion events are themselves logged as Stage 5 outputs, feeding back into Stage 1 to refine the validation protocol.

Capability Qualification and Promotion Contract Each capability-state transition shall be controlled by a versioned Capability Qualification Record. The record shall identify the measurand, current and proposed capability states, Controlled Source Specification Baseline, required evidence set, quantitative or categorical acceptance criteria, calibration and uncertainty prerequisites, validation method, validator identity and independence status, validation result, approving authority, approval timestamp, and resulting Stage 4 configuration version. The validation authority shall be organizationally or procedurally independent of the person or process that produced the candidate evidence to the extent required by the deployment's quality system. Stage 4 shall execute a promotion only when the record status is approved and every prerequisite remains valid; Stage 5 may trigger demotion or suspension when a prerequisite expires or fails. Every state transition shall be retained in the evidence archive.

Array-Level Decision Fusion as Cross-Stage Orchestration Distributed regulatory conclusions emerge from the coordinated execution of Stages 2 through 5. The array-level fusion rules defined in Section 5 of the monitoring framework are implemented as follows:

- 1. Eligibility arbitration (Stage 2): After each node-level measurand has passed the applicable Capability Eligibility & Regulatory-Use Gate, the orchestrator queries Stage 5 health and current calibration-validity states; the Stage 4 calibration-profile identifier is used only to identify the governing configuration when determining which otherwise eligible nodes may participate in array-level fusion on a per-measurand basis. Fusion eligibility shall not substitute for the preceding node-level regulatory-use gate.
- 2. Temporal alignment (Stage 2): The timing supervisor ensures observations are aligned to a common epoch before forwarding isolated channel results to Stage 3 for contextual retrieval.
- 3. Consistency evaluation (Stage 5): Cross-node consistency checks are executed as a Stage 5 evaluation-metric workflow, comparing carrier-frequency estimates, event times, and occupancy declarations after Stage 2 has corrected for known instrumental offsets.
- 4. Fusion rule execution (Stage 2): The fusion arbiter applies the documented decision rule—e.g., corroboration by at least two eligible nodes within a defined time window—using weights derived from Stage 4 calibration profiles and the real-time measurement uncertainty computed by Stage 2 using approved Stage 5 models.
- 5. Conclusion archiving (Stage 5): The fused decision, participating node list, consistency-check outcomes, and fusion weights are stored as an auditable evidence record with full traceability to the underlying Stage 1 DSP version, Stage 3 regulatory rule set, and Stage 4 configuration version.

Health-Driven Pipeline Degradation Stage 5 health supervision dynamically reconfigures the pipeline when nodes or the array enter degraded states:

Operational for Compliance Use. All five stages execute normally. Stage 4 permits compliance-grade measurement templates; Stage 2 includes the node in fusion pools.

Operational for Screening Only. Stage 5 flags the node. Stage 4 automatically downgrades its measurement templates to screening-grade; Stage 2 excludes the node from compliance fusion but retains it for situational awareness and evidence collection.

Degraded. Stage 5 triggers an alert. Stage 2 suspends all fusion involving the node; Stage 4 locks its configuration pending Stage 1 investigation.

Unavailable. Stage 2 removes the node from the orchestration schedule; Stage 5 continues to log absence events for trend analysis.

Uncertainty Propagation Through the Pipeline The GUM uncertainty framework is embedded at each measurement-relevant stage boundary, and each stage's contribution to or exclusion from the uncertainty budget is explicitly identified:

 Stage 1: Each uncertainty component is classified by its method of evaluation rather than by its physical source. Type A evaluation shall be used when the standard uncertainty is obtained by statistical analysis of measured quantity values under defined conditions; Type B evaluation shall be used when it is obtained by means other than Type A, including applicable calibration certificates, specifications, prior data, or documented scientific judgment. Algorithmic, hardware, timing, and environmental effects may therefore contribute through either category according to the evidence used to evaluate them. The evaluation method, source data, distribution or statistical model, sensitivity coefficient, and resulting standard uncertainty are attached to the applicable DSP block or calibration coefficient. Stage 2: Timing skew, sample-loss effects, and inter-node residual mismatch are quantified when they influence a reported measurand and are classified as Type A or Type B according to the evaluation method used. Their contributions, including applicable covariance terms where input quantities are correlated, are propagated into the node-level uncertainty budget. Stage 3: The regulatory decision reference applicable to each measurand is represented according to its governing mathematical form rather than as a universal scalar threshold. Depending on the measurand, the authoritative regulatory record may provide a one-sided limit, a two-sided tolerance interval, a permitted numerical range, a frequency-dependent limit or emission mask T(f), a relative reference, or a temporal or occupancy criterion. These regulatory decision parameters are maintained as authoritative decision inputs rather than measurement-error contributions to the GUM uncertainty budget. The regulatory-source version, retrieval timestamp, decision-rule type, and active parameters are logged as configuration metadata so the rule applied to each compliance determination can be reconstructed. Stage 4: Measurement template versioning captures which uncertainty contributions were active at the time of configuration deployment. Stage 5: Combined standard uncertainty uc(y) and expanded uncertainty U are validated from aggregated contributions; drift detection compares current uncertainty envelopes against the calibration record. Stage 2 computes real-time measurement uncertainty using Stage 5 approved uncertainty models.

Stage 5 outputs the uncertainty budget alongside performance reports, ensuring that Stage 1 receives not only what degraded, but with what confidence the degradation was detected.

Audit-Ready Evidence Archiving Every completed loop through the five stages shall produce a controlled evidence record. For formal compliance determinations, the repository shall provide append-only or write-once protection, authenticated access control, a cryptographic content digest for each retained artifact, an integrity-protected manifest, a trusted acquisition/record timestamp, and a retention identifier. Corrections or annotations shall create a new linked record without overwriting the preserved predecessor.

 Acquisition metadata (center frequency, sample rate, gain state, timestamp reference); DSP pipeline version, Stage 1 sandbox commit identifier, executable or container-image digest, and dependency/environment manifest required to reproduce the executed DSP path; Array orchestration log and Stage 2 node eligibility list; Regulatory rule set version, Controlled Source Specification Baseline identifier, and Stage 3 regulatory-data snapshot or immutable retrieval reference; Measurement configuration version, calibration profile identifiers, capability state, and Stage 4 policy enforcement checks; Estimated measurands, uncertainty budgets, decision outcomes, Stage 5 health states, fusion weights, and identifiers of any Ground-Truth Reference Records used for performance evaluation; For each formal decision, the raw I/Q interval or another lossless source artifact that documented replay validation has demonstrated to be sufficient to recompute every reported measurand and decision input. PSD estimates or spectrograms may be retained as supplementary evidence but shall not substitute for the required source artifact unless the documented replay validation explicitly demonstrates sufficiency.

A record satisfying these controls supports reconstruction of the executed measurement and decision path during technical or legal review. Reconstructability shall be demonstrated by replay or equivalent deterministic verification for each production DSP release before that release is authorized for formal compliance use.