#!/usr/bin/env python3
"""Tests for the G0 deterministic validator (template skill scripts).

Two independent guarantees are covered here:

1. **Real fixtures** - the ANE edge-sensor StRS/SyRS pair in
   ``methodology/test/T0_ANE-Lap2/just-edge/`` must pass with the exact
   expected error/warning counts, and the G0 gate must accept the pair.

2. **Reference templates** - the unfilled templates in ``templates/GT/`` must
   stay in sync with the validator. Every heading constant baked into the
   validator must still appear verbatim in the template, so a template edit
   that drops a required section fails loudly instead of silently drifting.

Plus one-defect-at-a-time unit tests proving each validation phase fires,
including the G0-X cross-document rules.

Runners - the suite is stdlib ``unittest`` at its core so the *skill* never
needs a venv. ``pytest`` is optional sugar and collects these classes natively:

    python3 -m unittest discover -s templates/tests -v     # zero dependencies
    python3 -m pytest templates/tests/ -v                  # after installing
                                                            # requirements.txt
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import List, Tuple

_TESTS_DIR = Path(__file__).resolve().parent
_TEMPLATES = _TESTS_DIR.parent           # templates/
_REPO_ROOT = _TEMPLATES.parent           # repository root

SCRIPT = _TEMPLATES / "skills" / "G0_valid_req_and_GT" / "scripts" / "g0_validate.py"
TEMPLATE_STRS = _TEMPLATES / "GT" / "G0_StRS.md"
TEMPLATE_SYRS = _TEMPLATES / "GT" / "G0_SyRS.md"
FIXTURE_STRS = (
    _REPO_ROOT / "methodology" / "test" / "T0_ANE-Lap2" / "just-edge" / "StRS.md"
)
FIXTURE_SYRS = (
    _REPO_ROOT / "methodology" / "test" / "T0_ANE-Lap2" / "just-edge" / "SyRS.md"
)

# Expected shape of the migrated real fixtures (pinned; see T8).
FIXTURE_STRS_BLOCK_COUNT = 64   # 43 STK + 17 HWC + 4 NRM
FIXTURE_STRS_STK_COUNT = 43
FIXTURE_STRS_HWC_COUNT = 17
FIXTURE_STRS_NRM_COUNT = 4
FIXTURE_SYRS_BLOCK_COUNT = 27
FIXTURE_STRS_SOURCE_REF_WARNINGS = 5  # known TBD/derived Source ref cells


def _load_validator():
    """Import g0_validate.py directly from its path without touching sys.path.

    The module must be registered in sys.modules before exec_module: Python
    3.13+ dataclasses resolve string annotations via sys.modules[cls.__module__],
    which raises AttributeError if the entry is missing.
    """
    spec = importlib.util.spec_from_file_location("g0_validate", SCRIPT)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load validator at {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["g0_validate"] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop("g0_validate", None)
        raise
    return module


g0 = _load_validator()


def check(text: str) -> Tuple[str, List]:
    """Run the full single-document validation pipeline on a markdown string.

    Mirrors ``validate_file`` but skips disk I/O, so unit tests stay fast and
    self-contained. Returns ``(doc_type, findings)``.
    """
    lines = text.splitlines()
    sections = g0.parse_markdown(lines)
    doc_type = g0.detect_doc_type(sections)
    if doc_type is None:
        return "", []

    findings = []
    findings += g0.validate_sections(sections, doc_type)
    findings += g0.validate_metadata(sections)
    blocks = g0.parse_blocks(lines, doc_type)
    findings += g0.validate_blocks(blocks, doc_type)
    findings += g0.validate_cross_refs(blocks, sections, doc_type)
    return doc_type, findings


def check_pair(strs_text: str, syrs_text: str) -> Tuple[List, List, List]:
    """Validate both documents and run the G0-X cross-document rules.

    Returns ``(strs_findings, syrs_findings, g0x_findings)``.
    """
    _, strs_findings = check(strs_text)
    _, syrs_findings = check(syrs_text)
    strs_blocks = g0.parse_blocks(strs_text.splitlines(), "StRS")
    syrs_blocks = g0.parse_blocks(syrs_text.splitlines(), "SyRS")
    g0x = g0.validate_cross_document(strs_blocks, syrs_blocks)
    return strs_findings, syrs_findings, g0x


def check_file(path: Path) -> Tuple[str, List]:
    """Validate a real file on disk through the same pipeline."""
    return check(path.read_text(encoding="utf-8"))


def errors(findings) -> List:
    return [f for f in findings if f.severity == "ERROR"]


def warnings(findings) -> List:
    return [f for f in findings if f.severity == "WARNING"]


def messages(findings) -> str:
    return " | ".join(f.message for f in findings)


def replace_field(text: str, field: str, old: str, new: str) -> str:
    """Replace ``old`` with ``new`` only inside the table row keyed by ``field``.

    A naive ``str.replace`` would also rewrite the same token wherever else it
    appears (for example a component ID that is both an inventory row and a
    constraint's Component value), silently turning an "orphan" test into a
    passing one. Scoping the edit to the keyed row keeps the mutation honest.
    """
    marker = f"**{field}**"
    out = []
    for line in text.split("\n"):
        if marker in line and old in line:
            out.append(line.replace(old, new))
        else:
            out.append(line)
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Minimal documents that validate clean. Each unit test mutates ONE thing.
# ---------------------------------------------------------------------------

MINIMAL_STRS = """# PROJECT: Test

## Stakeholder Requirements Specification (StRS)

## Document Metadata

| Field | Value |
|-------|-------|
| **Document ID** | `STRS-TEST-001` |
| **Project** | Test Project |
| **Organization** | Test Org |
| **Version** | 1.0.0 |
| **Classification** | `INTERNAL` |

## 1. Introduction

### 1.1 Purpose

Purpose.

### 1.2 Scope

Scope.

### 1.3 Definitions, Acronyms, and Abbreviations

| Term | Definition |
|------|------------|
| X | Y |

### 1.4 References

| Ref ID | Document | Version |
|--------|----------|---------|
| `REF-DS-001` | HackRF Datasheet | Rev 2024 |

### 1.5 Document Overview

Overview.

### 1.6 Hardware Inventory

| Component ID | Component Name | Role | Manufacturer | Part Number |
|--------------|----------------|------|--------------|-------------|
| `HW-SDR` | HackRF One | SDR receiver | Great Scott Gadgets | HackRF One |

## 2. Overall System Description

### 2.1 Product Perspective

Perspective.

### 2.2 Product Functions

Functions.

### 2.3 User Characteristics

| User Type | Description | Technical Level |
|-----------|-------------|-----------------|
| Engineer | Operates it | `EXPERT` |

### 2.4 Constraints

Constraints.

### 2.5 Assumptions and Dependencies

Assumptions.

### 2.6 Block Diagram

Diagram.

### 2.7 Bus and Interface Topology

| From | To | Bus/Protocol | Data Rate (theoretical) | Data Rate (sustained) |
|------|----|--------------|-------------------------|----------------------|
| HW-SDR | HW-CPU | USB 2.0 | 480 Mbps | 32 MB/s |

## 3. Specific Requirements

**`STK-ANAL-001` — Test stakeholder requirement**

| Field | Value |
|-------|-------|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `TEST` |
| **Dependencies** | — |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**

The system SHALL do a thing.

**Acceptance Criteria:**

1. [ ] A thing happens.

**`NRM-STD-001` — Cited normative obligation**

| Field | Value |
|-------|-------|
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Standard(s)** | ITU-R SM.1537 |
| **Clause** | §5.2 |
| **Compliance** | `COMPLIANT` |

**Description:**

The system SHALL respect the cited obligation.

**Acceptance Criteria:**

1. [ ] Obligation respected.

**`HWC-SDR-001` — Frequency range**

| Field | Value |
|-------|-------|
| **Component** | `HW-SDR` |
| **Parameter** | Operating frequency range |
| **Limit type** | `RANGE` |
| **Value min** | 1 MHz |
| **Value max** | 6 GHz |
| **Source** | `DATASHEET` |
| **Source ref** | `REF-DS-001` — Specifications |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

## 4. External Interface Requirements

### 4.1 User Interfaces

Interfaces.

## 5. Non-Functional Requirements

### 5.1 Performance

Performance.

## 6. Traceability

| Block ID | Subsystem | Standard(s) | Compliance | Test Case |
|----------|-----------|-------------|------------|-----------|
| `STK-ANAL-001` | Test | — | NOT_APPLICABLE | TC-001 |
| `NRM-STD-001` | Test | ITU-R SM.1537 | COMPLIANT | TC-002 |
| `HWC-SDR-001` | Test | — | NOT_APPLICABLE | TC-003 |
"""

MINIMAL_SYRS = """# PROJECT: Test

## System Requirements Specification (SyRS)

## Document Metadata

| Field | Value |
|-------|-------|
| **Document ID** | `SYRS-TEST-001` |
| **Project** | Test Project |
| **Organization** | Test Org |
| **Version** | 1.0.0 |
| **Classification** | `INTERNAL` |

## 1. Introduction

### 1.1 Purpose

Purpose.

### 1.2 Scope

Scope.

### 1.3 Definitions, Acronyms, and Abbreviations

| Term | Definition |
|------|------------|
| X | Y |

### 1.4 References

| Ref ID | Document | Version |
|--------|----------|---------|
| `REF-001` | IEEE/ISO/IEC 29148:2018 | 2018 |

### 1.5 Document Overview

Overview.

## 2. Measurement Framework

### 2.1 Measurand Catalog

| Measurand ID | Quantity | Unit |
|--------------|----------|------|
| M-001 | Field strength | dBµV/m |

### 2.2 Method Selection and Rationale

Selected methods.

### 2.3 Normative-to-Method Mapping

| Standard(s) | Clause | Measurand | Method |
|-------------|--------|-----------|--------|
| ITU-R SM.1537 | §5.2 | M-001 | Spectrum survey |

## 3. System Requirements

**`SYS-ANAL-001` — Field strength measurement**

| Field | Value |
|-------|-------|
| **Type** | `MEASUREMENT` |
| **Parameter** | Field strength |
| **Method** | Spectrum survey per ITU-R SM.1537 |
| **Traces to** | `STK-ANAL-001` |
| **Standard(s)** | ITU-R SM.1537 |

**Acceptance Criteria:**

1. [ ] Measurement completes within the sweep time.

## 4. Correction Chains

Correction chains.

## 5. Uncertainty Budgets

Uncertainty budgets.

## 6. Field Measurement Protocols

Protocols.

## 7. Traceability

| Specification ID | Traces to | Test Case |
|------------------|-----------|-----------|
| `SYS-ANAL-001` | `STK-ANAL-001` | TC-001 |
"""

# A second fully-valid STK block for duplicate / dependency tests.
STK_BLOCK_002 = """
**`STK-ANAL-002` — Second stakeholder requirement**

| Field | Value |
|-------|-------|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `TEST` |
| **Dependencies** | — |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**

The system SHALL cycle.

**Acceptance Criteria:**

1. [ ] Cycles.
"""


class TestMinimalFixtures(unittest.TestCase):
    """The synthetic baselines must validate clean, or every mutation test lies."""

    def test_minimal_strs_is_clean(self):
        doc_type, findings = check(MINIMAL_STRS)
        self.assertEqual(doc_type, "StRS")
        self.assertEqual(errors(findings), [], messages(findings))
        self.assertEqual(warnings(findings), [], messages(findings))

    def test_minimal_syrs_is_clean(self):
        doc_type, findings = check(MINIMAL_SYRS)
        self.assertEqual(doc_type, "SyRS")
        self.assertEqual(errors(findings), [], messages(findings))
        self.assertEqual(warnings(findings), [], messages(findings))

    def test_minimal_pair_is_clean(self):
        strs_f, syrs_f, g0x = check_pair(MINIMAL_STRS, MINIMAL_SYRS)
        self.assertEqual(errors(strs_f), [], messages(strs_f))
        self.assertEqual(errors(syrs_f), [], messages(syrs_f))
        self.assertEqual(errors(g0x), [], messages(g0x))
        self.assertEqual(warnings(g0x), [], messages(g0x))


class TestRealStrsFixture(unittest.TestCase):
    """methodology/test/T0_ANE-Lap2/just-edge/StRS.md - the named real document."""

    @classmethod
    def setUpClass(cls):
        cls.doc_type, cls.findings = check_file(FIXTURE_STRS)
        cls.lines = FIXTURE_STRS.read_text(encoding="utf-8").splitlines()

    def test_fixture_exists(self):
        self.assertTrue(FIXTURE_STRS.is_file(), f"missing fixture {FIXTURE_STRS}")

    def test_detected_as_strs(self):
        self.assertEqual(self.doc_type, "StRS")

    def test_no_errors(self):
        self.assertEqual(errors(self.findings), [], messages(self.findings))

    def test_exactly_known_source_ref_warnings(self):
        """The 5 known TBD/derived Source ref cells - nothing else regressed."""
        found = warnings(self.findings)
        self.assertEqual(
            len(found), FIXTURE_STRS_SOURCE_REF_WARNINGS, messages(found)
        )
        for finding in found:
            self.assertIn(
                "source ref", finding.message,
                f"unexpected warning kind: {finding.message}",
            )

    def test_parses_all_blocks(self):
        blocks = g0.parse_blocks(self.lines, "StRS")
        self.assertEqual(len(blocks), FIXTURE_STRS_BLOCK_COUNT)
        self.assertEqual(
            len({b.id for b in blocks}), FIXTURE_STRS_BLOCK_COUNT,
            "block IDs must be unique",
        )

    def test_block_kind_counts(self):
        blocks = g0.parse_blocks(self.lines, "StRS")
        kinds = [g0.strs_block_kind(b.id) for b in blocks]
        self.assertEqual(kinds.count("STK"), FIXTURE_STRS_STK_COUNT)
        self.assertEqual(kinds.count("HWC"), FIXTURE_STRS_HWC_COUNT)
        self.assertEqual(kinds.count("NRM"), FIXTURE_STRS_NRM_COUNT)

    def test_all_sections_present(self):
        findings = g0.validate_sections(g0.parse_markdown(self.lines), "StRS")
        self.assertEqual(findings, [], messages(findings))

    def test_traceability_covers_every_section_3_block(self):
        sections = g0.parse_markdown(self.lines)
        blocks = g0.parse_blocks(self.lines, "StRS")
        trace = next(s for s in sections if s.title.startswith("6. Traceability"))
        traced = {value for value, _ in g0._parse_first_column(trace.content)}
        missing = [b.id for b in blocks if b.id not in traced]
        self.assertEqual(missing, [], f"StRS §3 blocks absent from §6: {missing}")

    def test_every_stk_and_nrm_description_uses_shall(self):
        for block in g0.parse_blocks(self.lines, "StRS"):
            kind = g0.strs_block_kind(block.id)
            if kind not in ("STK", "NRM"):
                continue
            self.assertTrue(block.has_description, f"{block.id} has no description")
            self.assertRegex(
                block.description_text,
                r"\b(SHALL|SHOULD)\b",
                f"{block.id} description lacks SHALL/SHOULD",
            )

    def test_derived_constraints_cite_existing_blocks(self):
        """§3.18 derived constraints cite HWC IDs via Source ref; they must exist."""
        blocks = g0.parse_blocks(self.lines, "StRS")
        known = {b.id for b in blocks}
        for block in blocks:
            if block.id.startswith("HWC-DRV"):
                cited = g0._DEP_RE.findall(block.fields["Source ref"][0])
                self.assertTrue(cited, f"{block.id} cites no block IDs")
                for ref in cited:
                    self.assertIn(ref, known, f"{block.id} cites unknown {ref}")


class TestRealSyrsFixture(unittest.TestCase):
    """methodology/test/T0_ANE-Lap2/just-edge/SyRS.md - the named real document."""

    @classmethod
    def setUpClass(cls):
        cls.doc_type, cls.findings = check_file(FIXTURE_SYRS)
        cls.lines = FIXTURE_SYRS.read_text(encoding="utf-8").splitlines()

    def test_fixture_exists(self):
        self.assertTrue(FIXTURE_SYRS.is_file(), f"missing fixture {FIXTURE_SYRS}")

    def test_detected_as_syrs(self):
        self.assertEqual(self.doc_type, "SyRS")

    def test_no_errors(self):
        self.assertEqual(errors(self.findings), [], messages(self.findings))

    def test_no_warnings(self):
        self.assertEqual(warnings(self.findings), [], messages(self.findings))

    def test_parses_all_sys_blocks(self):
        blocks = g0.parse_blocks(self.lines, "SyRS")
        self.assertEqual(len(blocks), FIXTURE_SYRS_BLOCK_COUNT)
        self.assertEqual(
            len({b.id for b in blocks}), FIXTURE_SYRS_BLOCK_COUNT,
            "specification IDs must be unique",
        )

    def test_all_sections_present(self):
        findings = g0.validate_sections(g0.parse_markdown(self.lines), "SyRS")
        self.assertEqual(findings, [], messages(findings))

    def test_every_sys_block_cites_a_standard(self):
        for block in g0.parse_blocks(self.lines, "SyRS"):
            self.assertIn("Standard(s)", block.fields, f"{block.id} has no Standard(s) row")
            self.assertFalse(
                g0.is_unset(block.fields["Standard(s)"][0]),
                f"{block.id} Standard(s) is unset",
            )


class TestRealFixturePair(unittest.TestCase):
    """The migrated T0 pair must pass the full G0 gate end to end."""

    def test_real_fixture_pair_exits_zero(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(FIXTURE_STRS), str(FIXTURE_SYRS)],
            capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.count("Result: PASS"), 3, result.stdout)
        self.assertIn("G0-X CROSS-DOCUMENT REPORT", result.stdout)
        self.assertNotIn("G0 GATE REPORT", result.stdout)


class TestReferenceTemplates(unittest.TestCase):
    """templates/GT/ must stay in sync with the validator.

    If someone edits a template and drops a required heading, the sync test
    fails and names the exact heading that vanished.
    """

    @classmethod
    def setUpClass(cls):
        cls.strs_lines = TEMPLATE_STRS.read_text(encoding="utf-8").splitlines()
        cls.syrs_lines = TEMPLATE_SYRS.read_text(encoding="utf-8").splitlines()
        cls.strs_sections = g0.parse_markdown(cls.strs_lines)
        cls.syrs_sections = g0.parse_markdown(cls.syrs_lines)

    def test_templates_exist(self):
        self.assertTrue(TEMPLATE_STRS.is_file(), f"missing {TEMPLATE_STRS}")
        self.assertTrue(TEMPLATE_SYRS.is_file(), f"missing {TEMPLATE_SYRS}")

    def test_strs_template_detected(self):
        self.assertEqual(g0.detect_doc_type(self.strs_sections), "StRS")

    def test_syrs_template_detected(self):
        self.assertEqual(g0.detect_doc_type(self.syrs_sections), "SyRS")

    def test_every_strs_required_heading_is_in_the_template(self):
        """Sync guard: validator constants <-> template text."""
        text = TEMPLATE_STRS.read_text(encoding="utf-8")
        for heading in g0.STRS_REQUIRED:
            self.assertIn(
                heading, text,
                f"StRS template lost required heading {heading!r}; update "
                "templates/GT/G0_StRS.md or STRS_REQUIRED in g0_validate.py",
            )

    def test_every_syrs_required_heading_is_in_the_template(self):
        text = TEMPLATE_SYRS.read_text(encoding="utf-8")
        for heading in g0.SYRS_REQUIRED:
            self.assertIn(
                heading, text,
                f"SyRS template lost required heading {heading!r}; update "
                "templates/GT/G0_SyRS.md or SYRS_REQUIRED in g0_validate.py",
            )

    def test_strs_template_has_no_missing_sections(self):
        findings = g0.validate_sections(self.strs_sections, "StRS")
        self.assertEqual(findings, [], messages(findings))

    def test_syrs_template_has_no_missing_sections(self):
        findings = g0.validate_sections(self.syrs_sections, "SyRS")
        self.assertEqual(findings, [], messages(findings))

    def test_strs_template_fails_only_on_placeholders(self):
        """Unfilled template must FAIL (exit 1) but only via metadata placeholders
        and the illustrative blocks - never via missing structure."""
        _, findings = check(TEMPLATE_STRS.read_text(encoding="utf-8"))
        self.assertTrue(errors(findings), "unfilled template must not pass")
        for finding in errors(findings):
            self.assertNotIn(
                "missing required section", finding.message,
                f"template structure drifted: {finding.message}",
            )

    def test_syrs_template_fails_only_on_placeholders(self):
        _, findings = check(TEMPLATE_SYRS.read_text(encoding="utf-8"))
        self.assertTrue(errors(findings), "unfilled template must not pass")
        for finding in errors(findings):
            self.assertNotIn(
                "missing required section", finding.message,
                f"template structure drifted: {finding.message}",
            )

    def test_strs_template_has_one_example_block_per_kind(self):
        """§3 carries one concrete example per block kind (plus the generic
        format sketch, which the parser also captures)."""
        blocks = g0.parse_blocks(self.strs_lines, "StRS")
        kinds = {
            g0.strs_block_kind(b.id)
            for b in blocks
            if g0.strs_block_kind(b.id) is not None
        }
        self.assertEqual(kinds, {"NRM", "STK", "HWC"}, f"blocks: {[b.id for b in blocks]}")

    def test_syrs_template_has_one_example_sys_block(self):
        blocks = g0.parse_blocks(self.syrs_lines, "SyRS")
        self.assertEqual(len(blocks), 1, [b.id for b in blocks])


class TestPhase1Sections(unittest.TestCase):
    def test_missing_section_reported(self):
        doc = MINIMAL_STRS.replace("### 1.4 References", "### 1.4 Bibliography")
        _, findings = check(doc)
        errs = errors(findings)
        self.assertTrue(any("missing required section" in f.message for f in errs),
                        messages(findings))
        self.assertTrue(any("1.4 References" in f.message for f in errs), messages(findings))

    def test_all_missing_sections_reported_individually(self):
        doc = MINIMAL_STRS.replace("## 6. Traceability", "## 6. Something Else")
        doc = doc.replace("### 2.1 Product Perspective", "### 2.1 Something Else")
        _, findings = check(doc)
        missing = [f for f in errors(findings) if "missing required section" in f.message]
        self.assertEqual(len(missing), 2, messages(findings))

    def test_syrs_missing_section_reported(self):
        doc = MINIMAL_SYRS.replace("## 5. Uncertainty Budgets", "## 5. Budgets")
        _, findings = check(doc)
        self.assertTrue(
            any("5. Uncertainty Budgets" in f.message for f in errors(findings)),
            messages(findings),
        )


class TestPhase2Metadata(unittest.TestCase):
    def test_placeholder_detected(self):
        doc = MINIMAL_STRS.replace("`STRS-TEST-001`", "`STRS-_ACRONYM_-_NNN_`")
        _, findings = check(doc)
        self.assertTrue(
            any("placeholder" in f.message for f in errors(findings)), messages(findings)
        )

    def test_underscore_placeholder_detected(self):
        doc = MINIMAL_STRS.replace(
            "**Project** | Test Project", "**Project** | _full project name_"
        )
        _, findings = check(doc)
        self.assertTrue(
            any("placeholder" in f.message and "Project" in f.message
                for f in errors(findings)), messages(findings)
        )

    def test_bad_semver_detected(self):
        doc = MINIMAL_STRS.replace("**Version** | 1.0.0", "**Version** | 1.0")
        _, findings = check(doc)
        self.assertTrue(
            any("SemVer" in f.message for f in errors(findings)), messages(findings)
        )

    def test_bad_classification_detected(self):
        doc = MINIMAL_STRS.replace("`INTERNAL`", "`SECRET`")
        _, findings = check(doc)
        self.assertTrue(
            any("Classification" in f.message for f in errors(findings)), messages(findings)
        )

    def test_missing_metadata_field_detected(self):
        doc = MINIMAL_STRS.replace("| **Organization** | Test Org |\n", "")
        _, findings = check(doc)
        self.assertTrue(
            any("metadata table missing required field 'Organization'" in f.message
                for f in errors(findings)), messages(findings)
        )


class TestPhase3StkBlocks(unittest.TestCase):
    """STK- stakeholder requirements: the old SRS field rules plus compliance."""

    def test_bad_id_format_detected(self):
        doc = MINIMAL_STRS.replace("`STK-ANAL-001`", "`STK-ANAL-1`")
        _, findings = check(doc)
        self.assertTrue(
            any("does not match the required pattern" in f.message for f in errors(findings)),
            messages(findings),
        )

    def test_duplicate_id_detected(self):
        doc = MINIMAL_STRS.replace(
            "\n## 4. External Interface Requirements",
            STK_BLOCK_002.replace("STK-ANAL-002", "STK-ANAL-001")
            + "\n## 4. External Interface Requirements",
        )
        _, findings = check(doc)
        self.assertTrue(
            any("duplicate block ID" in f.message for f in errors(findings)), messages(findings)
        )

    def test_long_title_detected(self):
        long_title = "A" * 130
        doc = MINIMAL_STRS.replace("— Test stakeholder requirement", f"— {long_title}")
        _, findings = check(doc)
        self.assertTrue(
            any("block title is" in f.message for f in errors(findings)), messages(findings)
        )

    def test_missing_required_field_detected(self):
        doc = MINIMAL_STRS.replace("| **Verification** | `TEST` |\n", "", 1)
        _, findings = check(doc)
        self.assertTrue(
            any("missing required field 'Verification'" in f.message for f in errors(findings)),
            messages(findings),
        )

    def test_missing_compliance_field_detected(self):
        doc = MINIMAL_STRS.replace("| **Compliance** | `NOT_APPLICABLE` |\n", "", 1)
        _, findings = check(doc)
        self.assertTrue(
            any("missing required field 'Compliance'" in f.message for f in errors(findings)),
            messages(findings),
        )

    def test_missing_standard_presence_row_detected(self):
        """STK blocks must carry Standard(s)/Clause rows (em dash allowed)."""
        doc = MINIMAL_STRS.replace("| **Standard(s)** | — |\n", "", 1)
        _, findings = check(doc)
        self.assertTrue(
            any("missing required field 'Standard(s)'" in f.message
                for f in errors(findings)), messages(findings)
        )

    def test_invalid_enum_detected_with_expected_values(self):
        doc = MINIMAL_STRS.replace("`FUNCTIONAL`", "`SOMETIMES`")
        _, findings = check(doc)
        hit = [f for f in errors(findings) if "'Type'" in f.message]
        self.assertTrue(hit, messages(findings))
        self.assertIn("NON_FUNCTIONAL", hit[0].expected)

    def test_invalid_compliance_enum_detected(self):
        doc = MINIMAL_STRS.replace("`NOT_APPLICABLE`", "`SORT_OF`", 1)
        _, findings = check(doc)
        hit = [f for f in errors(findings) if "'Compliance'" in f.message]
        self.assertTrue(hit, messages(findings))
        self.assertIn("COMPLIANT", hit[0].expected)

    def test_missing_description_detected(self):
        doc = MINIMAL_STRS.replace(
            "**Description:**\n\nThe system SHALL do a thing.\n\n", ""
        )
        _, findings = check(doc)
        self.assertTrue(
            any("missing '**Description:**'" in f.message for f in errors(findings)),
            messages(findings),
        )

    def test_description_without_shall_is_warning_not_error(self):
        doc = MINIMAL_STRS.replace("The system SHALL do a thing.", "The system does a thing.")
        _, findings = check(doc)
        self.assertTrue(
            any("SHALL/SHOULD" in f.message for f in warnings(findings)), messages(findings)
        )
        self.assertFalse(
            any("SHALL/SHOULD" in f.message for f in errors(findings)), messages(findings)
        )

    def test_missing_acceptance_criteria_detected(self):
        doc = MINIMAL_STRS.replace("**Acceptance Criteria:**\n\n1. [ ] A thing happens.", "")
        _, findings = check(doc)
        self.assertTrue(
            any("Acceptance Criteria" in f.message for f in errors(findings)), messages(findings)
        )

    def test_zero_numbered_criteria_detected(self):
        doc = MINIMAL_STRS.replace("1. [ ] A thing happens.", "Some prose instead.")
        _, findings = check(doc)
        self.assertTrue(
            any("no numbered items" in f.message for f in errors(findings)), messages(findings)
        )


class TestPhase3NrmBlocks(unittest.TestCase):
    """NRM- normative obligations: always cite a concrete source."""

    def test_unset_standard_detected(self):
        doc = MINIMAL_STRS.replace("| **Standard(s)** | ITU-R SM.1537 |", "| **Standard(s)** | — |")
        _, findings = check(doc)
        self.assertTrue(
            any(f.block_id == "NRM-STD-001" and "Standard(s)" in f.message
                for f in errors(findings)), messages(findings)
        )

    def test_missing_clause_detected(self):
        doc = MINIMAL_STRS.replace("| **Clause** | §5.2 |\n", "")
        _, findings = check(doc)
        self.assertTrue(
            any(f.block_id == "NRM-STD-001" and "Clause" in f.message
                for f in errors(findings)), messages(findings)
        )

    def test_missing_acceptance_criteria_detected(self):
        doc = MINIMAL_STRS.replace("**Acceptance Criteria:**\n\n1. [ ] Obligation respected.", "")
        _, findings = check(doc)
        self.assertTrue(
            any(f.block_id == "NRM-STD-001" and "Acceptance Criteria" in f.message
                for f in errors(findings)), messages(findings)
        )

    def test_nrm_does_not_require_type_or_verification(self):
        """Absence of Type/Verification on an NRM block is not an error."""
        _, findings = check(MINIMAL_STRS)
        for finding in errors(findings):
            self.assertNotEqual(finding.block_id, "NRM-STD-001", messages([finding]))


class TestPhase3HwcBlocks(unittest.TestCase):
    """HWC- COTS constraints: the hardware-constraint field rules plus compliance."""

    def _strs(self, **kw) -> str:
        doc = MINIMAL_STRS
        for old, new in kw.items():
            doc = doc.replace(old, new)
        return doc

    def test_range_missing_bounds_detected(self):
        doc = self._strs(**{
            "| **Value min** | 1 MHz |\n| **Value max** | 6 GHz |\n": "",
        })
        _, findings = check(doc)
        msgs = messages(errors(findings))
        self.assertIn("Value min", msgs)
        self.assertIn("Value max", msgs)

    def test_non_range_missing_value_detected(self):
        doc = self._strs(**{
            "`RANGE`": "`MAX`",
            "| **Value min** | 1 MHz |\n| **Value max** | 6 GHz |\n": "",
        })
        _, findings = check(doc)
        self.assertTrue(
            any("requires a non-empty 'Value'" in f.message for f in errors(findings)),
            messages(findings)
        )

    def test_orphan_component_detected(self):
        # Scope the edit to the Component field. A bare str.replace would also
        # rewrite the §1.6 inventory row and hide the orphan.
        doc = replace_field(MINIMAL_STRS, "Component", "`HW-SDR`", "`HW-GHOST`")
        self.assertIn("`HW-GHOST`", doc, "mutation did not apply")
        self.assertIn("| `HW-SDR` | HackRF One |", doc, "inventory row must stay intact")
        _, findings = check(doc)
        self.assertTrue(
            any("not listed in the §1.6 Hardware Inventory" in f.message
                for f in errors(findings)), messages(findings)
        )

    def test_unknown_source_ref_is_warning(self):
        doc = self._strs(**{"`REF-DS-001` — Specifications": "_TBD — not selected yet_"})
        _, findings = check(doc)
        self.assertTrue(
            any("does not start with a known" in f.message for f in warnings(findings)),
            messages(findings)
        )
        self.assertFalse(
            any("Source ref" in f.message for f in errors(findings)), messages(findings)
        )

    def test_invalid_limit_type_enum_detected(self):
        doc = self._strs(**{"`RANGE`": "`SOMETIMES`"})
        _, findings = check(doc)
        self.assertTrue(
            any("'Limit type'" in f.message for f in errors(findings)), messages(findings)
        )

    def test_multi_component_all_checked(self):
        """A block citing two components must validate BOTH against the inventory."""
        # Legitimately add HW-CPU to the inventory, then point the Component
        # field at both. Both edits are scoped so the inventory row for HW-SDR
        # is never rewritten into a bogus multi-value cell.
        two_parts = MINIMAL_STRS.replace(
            "| `HW-SDR` | HackRF One | SDR receiver | Great Scott Gadgets | HackRF One |",
            "| `HW-SDR` | HackRF One | SDR receiver | Great Scott Gadgets | HackRF One |\n"
            "| `HW-CPU` | Raspberry Pi 4B | Processing | RPi Foundation | RPi 4B |",
        )
        doc = replace_field(two_parts, "Component", "`HW-SDR`", "`HW-SDR`, `HW-CPU`")
        self.assertIn("| `HW-SDR` | HackRF One |", doc, "inventory row must stay intact")
        _, findings = check(doc)
        self.assertEqual(errors(findings), [], messages(findings))

        # Now cite a component that is absent from the inventory: only the
        # second one may be flagged, proving both are checked.
        bad = replace_field(two_parts, "Component", "`HW-SDR`", "`HW-SDR`, `HW-MISSING`")
        _, findings = check(bad)
        flagged = [f for f in errors(findings) if "not listed" in f.message]
        self.assertEqual(len(flagged), 1, messages(findings))
        self.assertIn("HW-MISSING", flagged[0].message)


class TestPhase3SysBlocks(unittest.TestCase):
    """SYS- SyRS specifications: structural MVP."""

    def _syrs(self, **kw) -> str:
        doc = MINIMAL_SYRS
        for old, new in kw.items():
            doc = doc.replace(old, new)
        return doc

    def test_bad_id_format_detected(self):
        doc = self._syrs(**{"`SYS-ANAL-001`": "`SYS-ANAL-1`"})
        _, findings = check(doc)
        self.assertTrue(
            any("does not match the required pattern" in f.message for f in errors(findings)),
            messages(findings),
        )

    def test_duplicate_id_detected(self):
        block = MINIMAL_SYRS.split("## 3. System Requirements")[1].split("## 4.")[0]
        doc = self._syrs(**{
            "\n## 4. Correction Chains": block + "\n## 4. Correction Chains",
        })
        _, findings = check(doc)
        self.assertTrue(
            any("duplicate block ID" in f.message for f in errors(findings)), messages(findings)
        )

    def test_long_title_detected(self):
        doc = self._syrs(**{"— Field strength measurement": "— " + "A" * 130})
        _, findings = check(doc)
        self.assertTrue(
            any("block title is" in f.message for f in errors(findings)), messages(findings)
        )

    def test_missing_required_fields_detected_individually(self):
        for field in ("Type", "Parameter", "Method", "Traces to"):
            # Drop the whole row so the key disappears entirely.
            out = [
                line for line in MINIMAL_SYRS.split("\n")
                if f"**{field}**" not in line
            ]
            _, findings = check("\n".join(out))
            self.assertTrue(
                any(f"missing required field '{field}'" in f.message
                    for f in errors(findings)),
                f"field {field}: {messages(findings)}",
            )

    def test_missing_acceptance_criteria_detected(self):
        doc = self._syrs(**{"**Acceptance Criteria:**\n\n1. [ ] Measurement completes within the sweep time.": ""})
        _, findings = check(doc)
        self.assertTrue(
            any("Acceptance Criteria" in f.message for f in errors(findings)),
            messages(findings),
        )

    def test_zero_numbered_criteria_detected(self):
        doc = self._syrs(**{"1. [ ] Measurement completes within the sweep time.": "Prose."})
        _, findings = check(doc)
        self.assertTrue(
            any("no numbered items" in f.message for f in errors(findings)), messages(findings)
        )

    def test_sys_block_needs_no_description(self):
        """SyRS MVP has no SHALL/description rule - absence is not an error."""
        _, findings = check(MINIMAL_SYRS)
        for finding in errors(findings):
            self.assertNotIn("Description", finding.message, messages([finding]))


class TestPhase4CrossRefs(unittest.TestCase):
    """Intra-document cross-checks (StRS)."""

    def test_unknown_dependency_detected(self):
        doc = replace_field(MINIMAL_STRS, "Dependencies", "—", "`STK-ANAL-999`")
        _, findings = check(doc)
        self.assertTrue(
            any("does not exist in this document" in f.message for f in errors(findings)),
            messages(findings),
        )

    def test_traceability_gap_is_warning(self):
        doc = MINIMAL_STRS.replace("| `STK-ANAL-001` | Test | — | NOT_APPLICABLE | TC-001 |\n", "")
        _, findings = check(doc)
        self.assertTrue(
            any("not listed in the §6 Traceability table" in f.message
                for f in warnings(findings)), messages(findings)
        )

    def test_circular_dependency_detected(self):
        second = STK_BLOCK_002.replace(
            "| **Dependencies** | — |", "| **Dependencies** | `STK-ANAL-001` |"
        )
        doc = replace_field(
            MINIMAL_STRS, "Dependencies", "—", "`STK-ANAL-002`"
        ).replace(
            "\n## 4. External Interface Requirements",
            second + "\n## 4. External Interface Requirements",
        )
        _, findings = check(doc)
        self.assertTrue(
            any("circular dependency" in f.message for f in errors(findings)), messages(findings)
        )

    def test_self_dependency_is_a_cycle(self):
        doc = replace_field(MINIMAL_STRS, "Dependencies", "—", "`STK-ANAL-001`")
        _, findings = check(doc)
        self.assertTrue(
            any("circular dependency" in f.message for f in errors(findings)), messages(findings)
        )

    def test_acyclic_chain_passes(self):
        second = STK_BLOCK_002.replace(
            "| **Dependencies** | — |", "| **Dependencies** | `STK-ANAL-001` |"
        )
        doc = MINIMAL_STRS.replace(
            "\n## 4. External Interface Requirements",
            second + "\n## 4. External Interface Requirements",
        )
        _, findings = check(doc)
        self.assertFalse(
            any("circular dependency" in f.message for f in findings), messages(findings)
        )


class TestCrossDocument(unittest.TestCase):
    """G0-X: StRS + SyRS pair consistency rules."""

    def test_clean_pair_passes(self):
        _, _, g0x = check_pair(MINIMAL_STRS, MINIMAL_SYRS)
        self.assertEqual(errors(g0x), [], messages(g0x))

    def test_uncovered_stk_reported(self):
        """Point the only SYS block at the NRM block: the STK loses coverage."""
        doc = self._syrs_replace({"`STK-ANAL-001`": "`NRM-STD-001`"})
        _, _, g0x = check_pair(MINIMAL_STRS, doc)
        hit = [f for f in errors(g0x) if "no SyRS specification" in f.message]
        self.assertEqual(len(hit), 1, messages(g0x))
        self.assertIn("STK-ANAL-001", hit[0].block_id)
        self.assertEqual(hit[0].doc, "StRS")

    def test_traces_to_without_id_token_reported(self):
        doc = self._syrs_replace({"`STK-ANAL-001`": "some prose without an ID"})
        _, _, g0x = check_pair(MINIMAL_STRS, doc)
        hit = [f for f in errors(g0x) if "does not reference any StRS block ID" in f.message]
        self.assertEqual(len(hit), 1, messages(g0x))
        self.assertEqual(hit[0].doc, "SyRS")

    def test_traces_to_unknown_target_reported(self):
        doc = self._syrs_replace({"`STK-ANAL-001`": "`STK-ANAL-999`"})
        _, _, g0x = check_pair(MINIMAL_STRS, doc)
        hit = [f for f in errors(g0x) if "does not exist in the StRS" in f.message]
        self.assertEqual(len(hit), 1, messages(g0x))
        self.assertIn("STK-ANAL-999", hit[0].message)

    def test_shared_namespace_collision_reported(self):
        doc = self._syrs_replace({"`SYS-ANAL-001`": "`STK-ANAL-001`"})
        _, _, g0x = check_pair(MINIMAL_STRS, doc)
        hit = [f for f in errors(g0x) if "collides with a StRS block ID" in f.message]
        self.assertEqual(len(hit), 1, messages(g0x))

    def test_sys_without_standard_reported(self):
        doc = MINIMAL_SYRS.replace("| **Standard(s)** | ITU-R SM.1537 |\n", "")
        _, _, g0x = check_pair(MINIMAL_STRS, doc)
        hit = [f for f in errors(g0x) if "no normative source cited" in f.message]
        self.assertEqual(len(hit), 1, messages(g0x))
        self.assertEqual(hit[0].doc, "SyRS")

    def test_multi_trace_covers_each_target(self):
        """A comma-separated Traces to cell covers every named STK."""
        strs = MINIMAL_STRS.replace(
            "\n## 4. External Interface Requirements",
            STK_BLOCK_002 + "\n## 4. External Interface Requirements",
        ).replace(
            "| `HWC-SDR-001` | Test | — | NOT_APPLICABLE | TC-003 |",
            "| `HWC-SDR-001` | Test | — | NOT_APPLICABLE | TC-003 |\n"
            "| `STK-ANAL-002` | Test | — | NOT_APPLICABLE | TC-004 |",
        )
        syrs = self._syrs_replace({
            "`STK-ANAL-001`": "`STK-ANAL-001`, `STK-ANAL-002`",
        })
        strs_f, syrs_f, g0x = check_pair(strs, syrs)
        self.assertEqual(errors(strs_f), [], messages(strs_f))
        self.assertEqual(errors(syrs_f), [], messages(syrs_f))
        self.assertEqual(errors(g0x), [], messages(g0x))

    @staticmethod
    def _syrs_replace(pairs) -> str:
        doc = MINIMAL_SYRS
        for old, new in pairs.items():
            doc = doc.replace(old, new)
        return doc


class TestCliExitCodes(unittest.TestCase):
    """End-to-end contract: 0 pass, 1 errors/gate, 2 script error."""

    def _run(self, *args) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True, text=True, timeout=120,
        )

    def _temp_md(self, text: str) -> str:
        handle = tempfile.NamedTemporaryFile(
            "w", suffix=".md", delete=False, encoding="utf-8"
        )
        handle.write(text)
        handle.close()
        self.addCleanup(os.unlink, handle.name)
        return handle.name

    def test_script_is_stdlib_only(self):
        """The skill must never acquire a venv requirement."""
        source = SCRIPT.read_text(encoding="utf-8")
        for banned in ("import pytest", "import requests", "import numpy", "import pandas"):
            self.assertNotIn(banned, source, f"{banned} would break the stdlib-only contract")

    def test_clean_pair_exits_zero(self):
        strs_path = self._temp_md(MINIMAL_STRS)
        syrs_path = self._temp_md(MINIMAL_SYRS)
        result = self._run(strs_path, syrs_path)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.count("Result: PASS"), 3, result.stdout)
        self.assertIn("G0-X CROSS-DOCUMENT REPORT", result.stdout)

    def test_strs_alone_fails_the_gate(self):
        strs_path = self._temp_md(MINIMAL_STRS)
        result = self._run(strs_path)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("G0 GATE REPORT", result.stdout)
        self.assertIn("requires a SyRS document", result.stdout)
        self.assertIn("Result: PASS", result.stdout)  # the StRS itself is clean

    def test_syrs_alone_fails_the_gate(self):
        syrs_path = self._temp_md(MINIMAL_SYRS)
        result = self._run(syrs_path)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("G0 GATE REPORT", result.stdout)
        self.assertIn("requires a StRS document", result.stdout)

    def test_broken_document_exits_one(self):
        broken = self._temp_md(
            MINIMAL_STRS.replace("### 1.4 References", "### 1.4 Bibliography")
        )
        result = self._run(broken)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("Result: FAIL", result.stdout)

    def test_missing_file_exits_two(self):
        result = self._run("/nonexistent/g0_test_file.md")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    def test_undetectable_type_exits_two(self):
        path = self._temp_md("# Just a title\n\nNo document type heading here.\n")
        result = self._run(path)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    def test_no_arguments_exits_two(self):
        result = self._run()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)


class TestValidatorPublicApi(unittest.TestCase):
    """The functions documented in references/RULES.md must actually exist,
    so the reference doc cannot drift away from the code."""

    def test_documented_pipeline_functions_exist(self):
        for name in (
            "parse_markdown", "detect_doc_type", "validate_sections",
            "validate_metadata", "parse_blocks", "validate_blocks",
            "validate_cross_refs", "validate_cross_document",
            "format_report", "format_cross_document_report",
            "format_gate_report", "strs_block_kind", "main",
        ):
            self.assertTrue(callable(getattr(g0, name, None)),
                            f"g0_validate.py no longer exposes {name}()")

    def test_documented_dataclasses_exist(self):
        self.assertTrue(hasattr(g0, "Finding"))
        self.assertTrue(hasattr(g0, "Block"))

    def test_required_section_constants_match_documented_lists(self):
        self.assertEqual(len(g0.STRS_REQUIRED), 18)
        self.assertEqual(len(g0.SYRS_REQUIRED), 15)

    def test_finding_carries_optional_doc_field(self):
        finding = g0.Finding(
            severity="ERROR", line=1, block_id="", message="x", doc="SyRS"
        )
        self.assertEqual(finding.doc, "SyRS")


if __name__ == "__main__":
    unittest.main(verbosity=2)
