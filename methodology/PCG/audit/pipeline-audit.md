# Audit: AI Production Pipeline for SDR-Based Spectrum Monitoring

Source: `00_ProductionPipelinePCG.md` (153 lines). Line references are given as **L##** and match the uploaded file.

**Bottom line.** The governance sections (Dependency Contract, Promotion Gate, Capability Qualification Contract, Ground-Truth Contract, Evidence Archiving) are careful and largely self-consistent. The problems come from three places: the narrative framing written before those sections (which still describes a simple 1→2→3→4→5→1 ring), concrete citations into a source specification the document says does not yet exist, and a few artifacts (uncertainty models, fusion rules, the Conditional Compliance-Grade class) that have no single owner or no defined behaviour. There are also many Markdown defects that make the document hard to read and, in two tables, change its meaning.

Severity key: **High** = a reader could implement the pipeline wrongly or a control could be bypassed. **Medium** = ambiguity or contradiction that needs a decision. **Low** = editorial / formatting.

---

## Part 1 — Functionality description

### 1.1 What the system is

A governed operating model for a network (array) of SDR sensor nodes that perform spectrum monitoring, including formal regulatory compliance determinations. It is organised as five functional stages that both run measurements and continuously improve the methods used to run them. Formal compliance output is deliberately **disabled** until a controlled source specification is instantiated and approved (L97).

### 1.2 The five stages

| Stage | Nickname | What it owns | Main outputs |
|---|---|---|---|
| 1. RF/DSP Development & Calibration Sandbox | Sandbox | Off-line R&D: prototyping DSP on captured I/Q, HIL development for embedded targets, Git versioning, Docker for reproducible environments (L7–9). Also characterises uncertainty components (Type A/B) and attaches them to each DSP block and calibration coefficient (L146). | Validated DSP blocks, calibrated measurement procedures, feature prototypes = *deployment candidates* (L11, L60). |
| 2. Array Orchestration & Multi-Node Coordination | Engine | Runtime execution: scheduling acquisitions, node-level workflows, role-based coordination (acquisition scheduler, calibration manager, timing supervisor, fusion arbiter), data routing with buffering/fallback (L13–15). Applies calibration coefficients to raw I/Q, runs the Capability Eligibility & Regulatory-Use Gate, computes real-time uncertainty, executes formal decision logic and multi-node fusion (L52, L128–131, L146). | Measurement results, eligibility records, decision records (only where authorised), synchronised epochs, orchestration logs (L17, L63). |
| 3. Regulatory & Spectral Knowledge Base | Knowledge Base | Authoritative regulatory context with an applicability record per source (jurisdiction, authority, version, precedence); historical spectrum embeddings; knowledge graphs of stations, propagation, topology and calibration history (L19–23). Represents each regulatory limit in its real mathematical form (one-sided, two-sided, mask T(f), occupancy criterion, etc.) (L146). | Versioned, measurand-specific decision definitions (rule type, limits, reference quantities, source) (L25). |
| 4. Measurement Configuration & Policy Playbook | Playbook | Configuration governance: parameterised measurement templates, calibration-profile versioning (primary/secondary/relative), A/B testing with acceptance criteria and rollback thresholds, policy enforcement (gain/overload limits, metadata, capability eligibility, decision-rule integrity) (L27–29). Holds the Controlled Source Specification Baseline record (L97) and executes capability promotions (L124). | Versioned, deployable configuration bundles traceable to rule sets and calibration states (L31). |
| 5. Metrological QA & Array Health Guardrails | Guardrails | Measures RF/DSP performance (frequency error, power accuracy, OBW, false occupancy, missed detection, cross-node consistency), observability (sample loss, I/Q residuals, DC, timing skew, reference lock, drift, load), alerting, and HITL review of anomalous classifications (L33–43). Validates combined/expanded uncertainty, approves uncertainty models, runs cross-node consistency checks during fusion, classifies node health, triggers demotions and rollbacks (L56, L124, L130, L134–146). | Performance reports, drift logs, uncertainty scores/budgets, health states (L45, L148). |

### 1.3 How the stages hand off

The document actually describes two flows that share the same stages.

**A. Decision-execution flow (per measurand, per decision cycle)** — L47–54, L58–65:

1. Stage 3 → Stage 4: regulatory decision definition for the measurand.
2. Stage 1 → Stage 4: validated DSP/calibration candidate.
3. Stage 4 binds rule + template + calibration profile + capability class into a versioned configuration and publishes it to Stage 2.
4. Stage 5 → Stage 2 (and Stage 4): current metrological-validity and health state, i.e. the eligibility constraints.
5. Stage 2 acquires, applies calibration, estimates the measurand and its uncertainty, applies the eligibility gate, then:
   - **Unsupported** measurands are blocked;
   - **Screening-Grade** results may raise screening/review events only;
   - eligible measurands go through the rule supplied via Stages 3 and 4, with uncertainty entering accept / reject / indeterminate / guard-band outcomes.
6. For array conclusions, fusion runs as Stage 2 eligibility arbitration → Stage 2 temporal alignment → Stage 5 consistency check → Stage 2 fusion rule → Stage 5 archiving (L126–132).

**B. Improvement flow (the loop)** — L56, L67–74, L88–95:

1. Stage 5 detects drift, cross-node inconsistency, detection degradation (measured only against qualified Ground-Truth Reference Records, L74) or resource pressure.
2. Stage 1 develops a fix (recalibration, new algorithm, efficient DSP).
3. Stage 4 versions the candidate with acceptance criteria and rollback thresholds; a Production Promotion record must confirm the validation package, baseline, rule version, Stage 4 bundle, a valid Stage 5 state and an approver (L56).
4. Stage 2 deploys to an authorised node subset.
5. Stage 5 evaluates post-deployment metrics; a breach triggers rollback to the last approved configuration.
6. Stage 5 results go back to Stage 1.

### 1.4 How the loop closes

The primary closure is **Stage 5 → Stage 1** (L45, L67). Stage 5 also closes two shorter loops directly: it can **downgrade or lock Stage 4 configurations** and **constrain Stage 2 execution** (L65, L134–142), and it can **demote or suspend capability states** (L124). Capability promotions/demotions are logged as Stage 5 outputs and fed back to Stage 1 to refine validation protocols (L122).

### 1.5 Supporting mechanisms

- **Capability-class lifecycle** (L113–124): Unsupported → Screening-Grade → Conditional Compliance-Grade → Compliance-Grade, each transition controlled by a versioned, independently validated Capability Qualification Record.
- **Health-driven degradation** (L134–142): four node states (Operational for Compliance, Operational for Screening Only, Degraded, Unavailable) each with defined effects on Stages 2 and 4.
- **Uncertainty propagation** (L144–148): GUM-based; Stage 1 characterises components, Stage 2 propagates them (with covariance) at runtime, Stage 3 limits are explicitly *not* uncertainty contributions, Stage 4 records which contributions were active, Stage 5 validates uc(y) and U.
- **Evidence archiving** (L150–154): append-only, digested, timestamped records sufficient to replay every formal decision from raw I/Q, with replay demonstrated for each DSP release before compliance use.

---

## Part 2 — Coherence and consistency audit

### Summary table

| # | Finding | Severity | Lines |
|---|---|---|---|
| F1 | Concrete citations into a baseline that "is not instantiated" | High | L69, L81, L97–113, L126 |
| F2 | Mapping table contradicts the Calibration Hierarchy section | Medium | L103, L107, L111 |
| F3 | Uncertainty model has no single owner and is outside the promotion gate | High | L50, L56, L84, L131, L146 |
| F4 | Calibration coefficients and their uncertainty come from two unlinked authorities | Medium | L52, L131, L146 |
| F5 | Fused (array-level) uncertainty is never defined | High | L54, L131, L146 |
| F6 | Stage 2 vs Stage 5 split on consistency and archiving is under-specified | Medium | L39, L70, L130–132, L146, L150 |
| F7 | Stage 3 used as a runtime service in fusion step 2, with no consumer of its answer | Medium | L61, L129, L146, L152 |
| F8 | "Unsupported" is a state, not a capability tier; entry rules bypass the qualification record | Medium | L54, L113, L117, L124 |
| F9 | Conditional Compliance-Grade is never defined | High | L54, L113, L121, L136–138 |
| F10 | Node health and capability class are conflated | Medium | L136–142, L124 |
| F11 | No recovery path out of Degraded / Unavailable | Medium | L140–142 |
| F12 | "Functional, not chronological" is contradicted by the opening and the stage Output lines | Medium | L3, L11, L17, L25, L31, L45, L58 |
| F13 | Three of four feedback mechanisms skip the Promotion Gate | High | L56, L69–72 |
| F14 | Promotion Gate evaluator is assigned to three different owners | Medium | L56, L71, L91 |
| F15 | Fusion decision rules are not in the Stage 4 binding | Medium | L50, L126, L131 |
| F16 | Title says "AI", content describes almost no AI | Low | L1, L23 |
| F17 | Terminology drift | Low | various |
| F18 | Ambiguous unit for "every completed loop" in archiving | Low | L150 |
| F19 | Broken Design Rationale table | Low (meaning lost) | L78–84 |
| F20 | Broken Mapping table | Low (meaning lost) | L101–107 |
| F21 | Run-together lists, broken list items, missing headings | Low | many |
| F22 | Hyphenation / typo defects | Low | L15, L25, L49, L70, L74 |

---

### F1. Forward references to a non-instantiated baseline — High

L97 states plainly: *"In this document the deployment-specific baseline is not instantiated."* Yet the document then describes that baseline's contents as fact:

- L99: the pipeline *"maps directly onto"* the baseline, with specific Sections and Appendices A/B (L101–107).
- L109: *"The three-tier calibration strategy defined in Section 1 of the SDR document."*
- L113: *"In the Controlled Source Specification Baseline, four capability classes are defined."*
- L126: *"The array-level fusion rules defined in Section 5 of the monitoring framework."*
- L69 and L81: *"Tier 2 limits"*, *"Tier 2/3 verification"*, which only exist if that Section 1 exists.

**Circular or just forward?** Not strictly circular: nothing is defined in terms of itself. But it is **incoherent in a weaker way**: the document presumes a specific structure (section numbers, appendix letters, a three-tier calibration scheme, four capability classes) for a document that L97 says can be *any* approved source, identified later by a Stage 4 record that itself must list *"the applicable section/appendix references used by this pipeline."* So the mapping is both hard-coded (L101–107) and deferred to a future record (L97). Whichever baseline is eventually approved may not have a Section 5 on array coordination.

There is also a practical gap. Formal compliance is disabled until the baseline exists, but **screening operation is not**. Screening still relies on things the document says come from the baseline: Tier 2 drift limits (L69), the capability classes (L117), and the fusion rules (L126). So the part of the system that is allowed to run today depends on undefined inputs.

**Fix.** Either (a) declare the tier scheme, capability classes and fusion-rule *structure* as requirements of this methodology (so the pipeline owns them and a baseline must conform), or (b) reword L99–113 and L126 as a template ("the baseline record shall map … e.g. Section X") and state which provisional values govern screening while no baseline is instantiated.

### F2. Mapping table contradicts the Calibration Hierarchy — Medium

The mapping table assigns baseline Section 1 (Calibration Tiers) to Stage 1 and Stage 5 only (L103, L107). The next section gives Tier 2 to **Stage 2** (*"executed as a scheduled Stage 2 workflow"*) and Tier 3 to **Stage 4** (*"maintained as a Stage 4 configuration artifact"*) (L111). Stage 2's row (L104) and Stage 4's row (L106) do not cite Section 1. Similarly L81 puts *"Tier 2/3 verification"* in Stage 5, while L111 puts Tier 2 *execution* in Stage 2. These can be reconciled (Stage 2 executes, Stage 5 verifies), but the table should say so.

### F3. The uncertainty model has no single owner and sits outside the promotion gate — High

Five stages touch uncertainty, but the *model* that turns raw contributions into a reported uncertainty is never placed in the governed configuration bundle:

- Stage 1 characterises components and attaches them to DSP blocks and coefficients (L146).
- Stage 2 *"computes real-time measurement uncertainty using Stage 5 approved uncertainty models"* (L146) and propagates node-level contributions with covariance.
- Stage 4 *"captures which uncertainty contributions were active"* (L146), i.e. a record, not the model.
- Stage 5 *"validates"* uc(y) and U (L146), *"outputs the uncertainty budget"* (L148), and approves the models (L146).

Meanwhile the Dependency Contract (L50) binds template, calibration profile, capability class and decision configuration, and the Promotion Gate (L56 (iii)) checks template, calibration profile, capability state, acceptance criteria and rollback thresholds. **The uncertainty model is in neither list.** L84 does list *"uncertainty model"* as something requiring revalidation, which confirms it is a distinct artifact, but no section says who versions it or how a new one is activated.

Because L54 makes the decision outcome depend on uncertainty (guard bands, indeterminate zones), a change to a Stage 5-approved model can change compliance outcomes without passing the Promotion Gate. That breaks the document's otherwise rigorous rule that everything affecting a decision is a versioned Stage 4 binding.

**Fix.** State that Stage 5 *approves* uncertainty models and Stage 4 *versions and publishes* them as part of the calibration profile or decision configuration. Add them to L50, to L56 (iii), and to the evidence list at L152.

### F4. Calibration coefficients and their uncertainty come from two unlinked authorities — Medium

The Dependency Contract (L52): Stage 2 *"shall apply active Stage 4 calibration coefficients."* The Uncertainty section (L146): Stage 2 uses *"Stage 5 approved uncertainty models."* Fusion (L131): weights come from *"Stage 4 calibration profiles and the real-time measurement uncertainty computed by Stage 2 using approved Stage 5 models."*

These are different artifacts, so the sentences do not contradict each other outright. **But they are not reconciled.** A calibration coefficient's uncertainty is part of its own definition (Stage 1 attaches it, L146). Nothing guarantees that the uncertainty model Stage 2 uses corresponds to the *same version* of the calibration profile Stage 2 applies. After a Stage 4 recalibration (L69), Stage 2 could pair new coefficients with an uncertainty model approved for the old ones.

There is also a small wording clash inside the fusion section. L128 says the calibration-profile identifier is *"used only to identify the governing configuration,"* while L131 derives fusion **weights** from the profile's contents. The "only" is scoped to eligibility arbitration, but it reads as a contradiction.

**Fix.** Same as F3: bind the uncertainty model to the calibration-profile version so Stage 2 receives a single, consistent bundle from Stage 4.

### F5. Fused (array-level) uncertainty is never defined — High

L54 requires that every rule define *"how the measured value and associated measurement uncertainty enter acceptance, rejection, and any indeterminate or guard-band outcome."* L146 defines only a **node-level** uncertainty budget. The fusion rule (L131) uses node uncertainties as weights, but the uncertainty of the **fused** result, which is what an array-level regulatory conclusion would be judged on, is never computed or assigned to any stage. Corroboration rules (*"at least two eligible nodes"*) are categorical and may not need one, but any fused numeric estimate (e.g. a fused frequency or power) would have no uncertainty to feed into L54's decision rule.

**Fix.** Add an array-level step to the Uncertainty section (owner: Stage 2 computes, Stage 5 validates), including treatment of correlated errors across nodes (shared reference, shared calibration source).

### F6. Stage 2 vs Stage 5 on consistency and archiving — Medium

Ownership is *mostly* divided as "Stage 2 does it, Stage 5 checks it," but the split is not stated as a principle and has three soft spots:

1. **Inter-node mismatch is measured twice.** Stage 2 quantifies *"inter-node residual mismatch"* for the uncertainty budget (L146) and corrects *"known instrumental offsets"* (L130). Stage 5 computes a *"cross-node consistency score"* (L39) and flags disagreement *"beyond the uncertainty budget"* (L70), a budget that already includes Stage 2's mismatch term. If the mismatch is absorbed into the budget, persistent inconsistency becomes harder to flag. The document should say whether Stage 5's test uses the budget with or without that term.
2. **The consistency check result is not consumed.** Fusion step 3 (L130) runs the Stage 5 check, but step 4 (L131) does not say what happens if it fails. Does the fusion arbiter exclude inconsistent nodes, mark the result indeterminate, or proceed?
3. **Archiving owner.** Fusion step 5 assigns *"Conclusion archiving"* to Stage 5 (L132), but Stage 5's purpose (L35) does not mention archiving, and the Audit-Ready Evidence Archiving section (L150–152) names no owner.

Stage 5 is also both an **offline QA function** (reports to Stage 1) and a **runtime participant** (eligibility input at L51, consistency check in the fusion path at L130, rollback trigger at L56). That dual role is fine, but L33–35 describe only the first. It would help to say so.

### F7. Stage 3 as a runtime query service — Medium

Fusion step 2 (L129): the timing supervisor aligns observations *"before forwarding isolated channel results to Stage 3 for contextual retrieval."* This is inconsistent with the rest of the document in two ways:

- **Wrong direction of flow.** Everywhere else Stage 3 feeds **Stage 4** at configuration time (L49, L61), and rules reach Stage 2 only *"through Stages 3 and 4"* (L54). L129 creates a runtime Stage 2 → Stage 3 call that bypasses the Stage 4 binding.
- **No return path.** The next step (L130) goes to Stage 5 and then back to Stage 2. Nothing says what Stage 3 returns, who uses it, or whether it can affect the decision.

The document is not entirely consistent that Stage 3 is config-time only, however. L146 logs a *"retrieval timestamp"* and L152 archives a *"Stage 3 regulatory-data snapshot or immutable retrieval reference,"* which implies some runtime retrieval. And Stage 3's knowledge graphs and historical embeddings (L23) look like they are meant for runtime anomaly fingerprinting.

**Fix.** Split Stage 3 explicitly into (a) **governed regulatory definitions**, delivered only via Stage 4 bindings and never queried live for decisions, and (b) **contextual/advisory lookups** (station identity, historical fingerprints) that may be queried at runtime but cannot change a formal decision. Then rewrite L129 to say which one it means and what consumes the result. "Isolated channel results" should also be defined.

### F8. Is "Unsupported" a class or an absence? — Medium

As a ladder, L113 is defensible: there are three *steps* between four states, and each step adds obligations. Unsupported is the floor. But Unsupported behaves like an **absence of capability**, not a grade:

- L54 says unsupported measurands *"shall be blocked from regulatory decision processing."* It produces nothing.
- L117 lets a new measurand *"enter … as Unsupported or Screening-Grade in Stage 1."* Entering directly at Screening-Grade skips any qualification step, while L124 says *"each capability-state transition shall be controlled by a versioned Capability Qualification Record."* Assigning an initial grade is effectively a transition from nothing, and it is uncontrolled. It also happens in Stage 1, while L119 and L124 place capability state under Stage 4 versioning.
- Criteria are given for Screening → Conditional and Conditional → Compliance (L121) but **not for Unsupported → Screening**.

**Fix.** Call Unsupported the default *state* (no capability) and list three *capability classes*, or keep four classes but define Unsupported → Screening entry criteria and require a Qualification Record for it. Move initial classification from Stage 1 to Stage 4.

### F9. Conditional Compliance-Grade is never defined — High

The class is named (L113, L121) but the document never says:

- what the **conditions** are, or who sets them;
- what it **permits** that Screening does not, or what it withholds compared with full Compliance-Grade. The gate at L54 handles only Screening and Unsupported. A Conditional measurand that passes the gate is treated the same as a Compliance-Grade one;
- how it behaves under **health degradation**. L136–138 mention only *"compliance-grade"* and *"screening-grade"* templates.

Since this class is the one that will actually issue the first formal determinations, its absence is the most consequential gap in the capability model.

### F10. Node health and capability class are conflated — Medium

L138: when a node becomes "Operational for Screening Only," *"Stage 4 automatically downgrades its measurement templates to screening-grade."* Capability class belongs to a **measurand** (L121, L124), but health belongs to a **node**. It is not clear whether a health downgrade changes the measurand's capability class (which would need a Qualification Record, L124) or only that node's template. The word "automatically" also sits awkwardly next to L124's requirement that Stage 4 execute transitions only on approved records. L124 allows Stage 5 to trigger demotion, so this is reconcilable, but the two mechanisms should be explicitly linked. L136's *"All five stages execute normally"* is a node-level statement about stages that are not per-node, which adds to the confusion.

### F11. No recovery path out of Degraded or Unavailable — Medium

Degraded locks the node's configuration *"pending Stage 1 investigation"* (L140). Unavailable removes it from the schedule (L142). Neither state says how a node returns to service: what evidence, which stage decides, and whether it must re-pass the Promotion Gate or re-qualify capabilities. Given how carefully promotion is controlled elsewhere, re-entry should be too.

### F12. "Functional ownership, not chronological order": is it upheld? — Medium

**Upheld in the governance sections, contradicted in the narrative.**

The Dependency Contract (L47–54) and the Inter-Stage Flow (L58–65) are consistent with the claim at L58. The real decision order is 3 → 4 → (5) → 2, and Stage 1 feeds Stage 4 rather than Stage 2. The Example Workflow (L88–95) follows that order (1, 3, 4, 4–5, 2, 5, 1). So far, coherent.

But earlier passages describe a sequential ring:

- L3: *"each stage feeds into the next, and the final stage loops back."* That is exactly a chronological 1→2→3→4→5→1 sequence.
- L11: Stage 1 outputs *"enter Stage 2 for array orchestration."* Per L60 they must go through Stage 4 first.
- The per-stage Output lines name only the 1→2 and 5→1 links. None of them shows 3→4, 4→2 or 5→2/4. Stage 2's outputs (L17) do not flow to Stage 3 at all in the contract.
- L126: *"Stages 2 through 5"* implies a range, though Stage 4 has no step in that fusion sequence.

Also, the circle is described as closing in one place (Stage 5 → Stage 1, L45, L67), while L65 adds direct Stage 5 → Stage 4 and Stage 5 → Stage 2 control paths. The real topology is a governed graph with one long improvement loop and two short control loops, not a single circle.

**Fix.** Rewrite L3 and the per-stage Output lines to match L58–65, and consider adding a diagram that shows the real edges.

### F13. Three of four feedback mechanisms skip the Promotion Gate — High

L56: *"A Stage 1 deployment candidate shall not enter governed Stage 2 production execution until a versioned promotion record confirms…"* Of the four feedback mechanisms (L69–72), only #3 (detection rule degradation) routes through the gate. The other three do not:

- #1 Calibration drift: Stage 1 recalibrates → *"Stage 4 updates calibration profile versions."* New coefficients are a Stage 1 output, and they reach production with no gate.
- #2 Cross-node inconsistency: Stage 1 → *"Stage 3 updates knowledge graph or station records."* L84 requires dependency-impact analysis, but the gate is not mentioned.
- #4 Resource optimisation: Stage 1 prototypes efficient DSP → *"Stage 4 simplifies measurement configurations."* That is a new DSP implementation entering production with no gate.

The Example Workflow (L94) correctly requires new calibration coefficients to go through *"a new Stage 4 calibration-profile version,"* and L95 routes the cycle *"through the same promotion gate."* So the intent is clear, but the mechanism list states otherwise.

**Fix.** Append "→ Production Promotion and Rollback Gate → Stage 2 deployment" to mechanisms #1 and #4, and "→ dependency-impact analysis → Stage 4 rebind" to #2.

### F14. Who runs the Promotion Gate? — Medium

- L56: a promotion *record* is required, approval is by the *"deployment authority identified in the Stage 4 policy record,"* and **Stage 5** evaluates post-deployment metrics.
- L71: **Stage 4** *"evaluates the candidate against the Production Promotion and Rollback Gate."*
- L91: the gate is run by **Stages 4–5**.

These are compatible (Stage 4 assembles and approves, Stage 5 supplies the health prerequisite and post-deployment evaluation), but no sentence says so. Rollback execution is also unowned: L56 says the candidate shall be *"suspend[ed]"* and the configuration *"restore[d]"* without naming who does it.

### F15. Fusion rules are not in the Stage 4 binding — Medium

L131 applies *"the documented decision rule"* for fusion (e.g. two-node corroboration), sourced from *"Section 5 of the monitoring framework"* (L126). The Dependency Contract binds only the **measurand-specific** decision definition (L49–50). Fusion rules, time windows and weighting schemes are not named as Stage 3 definitions, Stage 4 bindings or Promotion Gate items. A fusion rule change could therefore alter array-level conclusions outside the version control that governs node-level decisions.

### F16. "AI" in the title — Low

L1 is titled *"AI Production Pipeline,"* but the body describes conventional DSP, calibration, orchestration and QA. The only ML-like element is *"historical spectrum embeddings"* (L23). Detection algorithms (L71, L88) are not described as learned models, and there is nothing about training data, model drift or model validation. Either drop "AI" from the title or describe where learned components sit and how the Ground-Truth Contract (L74) governs their training as well as their evaluation. L3's *"self-correcting"* and *"living measurement organism"* framing also sits uneasily with a design in which every change requires human approval and promotion records.

### F17. Terminology drift — Low

- *Capability class* (L50, L62, L90) vs *capability state* (L56, L119, L124, L152). Pick one, or define class = the ladder rung and state = its current assignment.
- *SDR document* / *monitoring framework* / *governing SDR monitoring framework* / *Controlled Source Specification Baseline*. L97 declares these synonyms, but they appear before L97 (L47, L83) and continue after it (L109, L126). Using one term throughout would be clearer.
- *Decision definition* (Stage 3, L25) vs *decision rule* (Stage 4, L27) vs *decision configuration* (L50). L61–62 implies definition → configuration, but "rule" is used for both.
- Undefined abbreviations: GUM, PSD, ADC, DC, OBW (implied), I/Q. Most readers will know them, but a compliance document usually expands them once.

### F18. Unit of archiving — Low

L150: *"Every completed loop through the five stages shall produce a controlled evidence record."* "Loop" could mean an improvement cycle (weeks) or a decision cycle (seconds). The list that follows (L152) is clearly per formal decision. Say "every formal decision cycle, and every promotion/rollback event."

### F19. Broken Design Rationale table (L78–84) — Low, but meaning is lost

- The header row declares **7 columns**. Only the first two have headings, and five empty columns follow.
- Rows L80–83 fill two columns and leave five empty.
- Row L84 (*Controlled Stage Evolution*) has its sentence split across six cells: *"…documented dependency-impact analysis, | revalidation, | and version updates for | every affected | downstream configuration, calibration state, uncertainty model, or | decision rule |"*. Rendered, it reads as fragments in unlabelled columns. This sentence is also the only place the document lists the uncertainty model as a governed artifact (see F3), so the defect hides an important rule.

**Fix.** Collapse to a two-column table and rejoin the L84 sentence.

### F20. Broken Mapping table (L101–107) — Low, but meaning is lost

The table has an empty third column, and the Stage 1 row splits *"Appendix A"* into *"Appendix | A"* (L103). Rendered, Stage 1 appears to map to "Appendix" with an unlabelled "A" in a blank column. **Fix:** remove the empty column and rejoin "Appendix A."

### F21. Run-together lists and structural defects — Low

Bullet lists written as a single paragraph with no separators, so they render as one long sentence:

- **L9**: Stage 1 tools (Notebooks / HIL IDEs / Git / Docker).
- **L15**: Stage 2 tools (Array Orchestrator / Workflow Orchestrators / Multi-Node Coordination / Data Routing Gateways).
- **L23**: two Stage 3 items merged (*"…anomaly fingerprinting Knowledge Graphs for…"*).
- **L29**: Stage 4 tools (Templates / Calibration Profile Versioning / A/B Testing / Policy Enforcement).
- **L40–43**: Stage 5. *"Human-in-the-loop review … Observability"* fuses an item with the next sub-heading. *"Processing load, memory consumption…"* (an Observability sub-item) is promoted to top level and merged with the *"Alerting"* item.
- **L94**: Example step 7's three triggered actions run together.
- **L111**: Calibration Tiers 1/2/3.
- **L146**: all five Uncertainty-propagation stage paragraphs in one block.
- **L152**: the seven evidence-record items, separated only by semicolons.

Other structural issues:

- **L52–54**: Dependency Contract item 4 breaks mid-sentence (*"Only a measurand"* / blank line / *"that passes this gate…"*), so the gate rule renders as a separate paragraph outside the list.
- **L64**: a stray blank line inside the Inter-Stage Flow list, which splits it into two lists.
- Numbered items written as `- 1.`, `- 2.` (bullet + number) throughout (L49–52, L60–65, L69–72, L88–95, L117–122, L128–132), which renders as bullets with literal numbers.
- Only two real headings exist (L1 `##`, L86 `##`). Every other section title is run into its first sentence: *"Regulatory Decision Authority and Dependency Contract The five stages…"* (L47), and likewise L56, L58, L67, L74, L97, L99, L109, L113, L124, L126, L134, L144, L150. These should be `###` headings.
- Stage headers are inconsistent. Stages 1–4 put *"Purpose:"* on the header line (L7, L13, L19, L27), while Stage 5 splits it (L33–35).
- The four health states (L136–142) use sentence-style labels with no list or heading formatting.

### F22. Hyphenation and typo defects — Low

Missing hyphens, probably from line-wrap joins in the source: *"crossnode"* (L15), *"measurandspecific"* (L25, L49), *"DSPalgorithm"* (L70), *"falseoccupancy"* (L74). L113 is missing a space in *"Unsupported→Screening-Grade"*, while the other arrows are spaced.

---

## Recommended priority

1. **F3/F4/F5**: put the uncertainty model (node and fused) into the Stage 4 binding and the Promotion Gate. This is the one gap that lets decision-affecting changes bypass governance.
2. **F13/F15**: route every feedback mechanism and fusion-rule change through the Promotion Gate.
3. **F9/F8**: define Conditional Compliance-Grade and the Unsupported → Screening entry.
4. **F1/F2**: decide whether the tier scheme, capability classes and fusion structure are owned by this methodology or by the future baseline, and state what governs screening until the baseline exists.
5. **F7/F12/F6/F14**: clarify Stage 3's runtime role, rewrite the opening "ring" framing, and name owners for consistency outcomes, archiving and rollback.
6. **F19–F22**: formatting pass (mechanical; the two table fixes restore lost meaning).
