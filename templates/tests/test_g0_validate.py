#!/usr/bin/env python3
"""Tests for the G0 deterministic validator (template skill scripts).

Two independent guarantees are covered here:

1. **Real fixtures** - the ANE edge-sensor SRS/HCS in
   ``methodology/test/T0_ANE-Lap2/just-edge/`` must pass with the exact
   expected error/warning counts.

2. **Reference templates** - the unfilled templates in ``templates/GT/`` must
   stay in sync with the validator. Every heading constant baked into the
   validator must still appear verbatim in the template, so a template edit
   that drops a required section fails loudly instead of silently drifting.

Plus one-defect-at-a-time unit tests proving each validation phase fires.

Runners - the suite is stdlib ``unittest`` at its core so the *skill* never
needs a venv. ``pytest`` is optional sugar and collects these classes natively:

    python3 -m unittest discover -s templates/tests -v     # zero dependencies
    python3 -m pytest templates/tests/ -v                  # after installing
                                                            # requirements.txt
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path
from typing import List, Tuple

_TESTS_DIR = Path(__file__).resolve().parent
_TEMPLATES = _TESTS_DIR.parent           # templates/
_REPO_ROOT = _TEMPLATES.parent           # repository root

SCRIPT = _TEMPLATES / "skills" / "G0_valid_req_and_GT" / "scripts" / "g0_validate.py"
TEMPLATE_SRS = _TEMPLATES / "GT" / "G0_SRS.md"
TEMPLATE_HCS = _TEMPLATES / "GT" / "G0_HCS.md"
FIXTURE_SRS = _REPO_ROOT / "methodology" / "test" / "T0_ANE-Lap2" / "just-edge" / "SRS.md"
FIXTURE_HCS = _REPO_ROOT / "methodology" / "test" / "T0_ANE-Lap2" / "just-edge" / "HCS.md"


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
    """Run the full validation pipeline on an in-memory markdown string.

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

MINIMAL_SRS = """# PROJECT: Test

## System Requirements Specification (SRS)

## Document Metadata

| Field | Value |
|-------|-------|
| **Document ID** | `SRS-TEST-001` |
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
| `REF-001` | Some doc | 2026 |

### 1.5 Document Overview

Overview.

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

## 3. Specific Requirements

**`ANAL-EMC-001` — Test requirement**

| Field | Value |
|-------|-------|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `TEST` |
| **Dependencies** | — |

**Description:**

The system SHALL do a thing.

**Acceptance Criteria:**

1. [ ] A thing happens.

## 4. External Interface Requirements

### 4.1 User Interfaces

Interfaces.

## 5. Non-Functional Requirements

### 5.1 Performance

Performance.

## 6. Traceability

| Requirement ID | Subsystem | Standard Ref | Test Case |
|----------------|-----------|--------------|-----------|
| `ANAL-EMC-001` | Test | — | TC-001 |
"""

MINIMAL_HCS = """# PROJECT: Test

## Hardware Constraints Specification (HCS)

## Document Metadata

| Field | Value |
|-------|-------|
| **Document ID** | `HCS-TEST-001` |
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

### 1.5 Hardware Inventory

| Component ID | Component Name | Role | Manufacturer | Part Number |
|--------------|----------------|------|--------------|-------------|
| `HW-SDR` | HackRF One | SDR receiver | Great Scott Gadgets | HackRF One |

## 2. System Hardware Architecture

### 2.1 Block Diagram

Diagram.

### 2.2 Bus and Interface Topology

| From | To | Bus/Protocol | Data Rate (theoretical) | Data Rate (sustained) |
|------|----|--------------|-------------------------|----------------------|
| HW-SDR | HW-CPU | USB 2.0 | 480 Mbps | 32 MB/s |

## 3. Hardware Constraints

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

## 4. Derived Constraints

Derived constraints.
"""


class TestMinimalFixtures(unittest.TestCase):
    """The synthetic baselines must validate clean, or every mutation test lies."""

    def test_minimal_srs_is_clean(self):
        doc_type, findings = check(MINIMAL_SRS)
        self.assertEqual(doc_type, "SRS")
        self.assertEqual(errors(findings), [], messages(findings))
        self.assertEqual(warnings(findings), [], messages(findings))

    def test_minimal_hcs_is_clean(self):
        doc_type, findings = check(MINIMAL_HCS)
        self.assertEqual(doc_type, "HCS")
        self.assertEqual(errors(findings), [], messages(findings))
        self.assertEqual(warnings(findings), [], messages(findings))


class TestRealSRSFixture(unittest.TestCase):
    """methodology/test/T0_ANE-Lap2/just-edge/SRS.md - the named real document."""

    @classmethod
    def setUpClass(cls):
        cls.doc_type, cls.findings = check_file(FIXTURE_SRS)
        cls.lines = FIXTURE_SRS.read_text(encoding="utf-8").splitlines()

    def test_fixture_exists(self):
        self.assertTrue(FIXTURE_SRS.is_file(), f"missing fixture {FIXTURE_SRS}")

    def test_detected_as_srs(self):
        self.assertEqual(self.doc_type, "SRS")

    def test_no_errors(self):
        self.assertEqual(errors(self.findings), [], messages(self.findings))

    def test_no_warnings(self):
        self.assertEqual(warnings(self.findings), [], messages(self.findings))

    def test_parses_all_43_requirement_blocks(self):
        blocks = g0.parse_blocks(self.lines, "SRS")
        self.assertEqual(len(blocks), 43)
        self.assertEqual(len({b.id for b in blocks}), 43, "requirement IDs must be unique")

    def test_all_sections_present(self):
        findings = g0.validate_sections(g0.parse_markdown(self.lines), "SRS")
        self.assertEqual(findings, [], messages(findings))

    def test_traceability_covers_every_requirement(self):
        sections = g0.parse_markdown(self.lines)
        blocks = g0.parse_blocks(self.lines, "SRS")
        trace = next(s for s in sections if s.title.startswith("6. Traceability"))
        traced = {g0.cell_text(row[0]) for row in g0._parse_first_column(trace.content)}
        missing = [b.id for b in blocks if b.id not in traced]
        self.assertEqual(missing, [], f"SRS §3 requirements absent from §6: {missing}")

    def test_every_description_uses_shall(self):
        for block in g0.parse_blocks(self.lines, "SRS"):
            self.assertTrue(
                block.has_description, f"{block.id} has no description"
            )
            self.assertRegex(
                block.description_text,
                r"\b(SHALL|SHOULD)\b",
                f"{block.id} description lacks SHALL/SHOULD",
            )


class TestRealHCSFixture(unittest.TestCase):
    """methodology/test/T0_ANE-Lap2/just-edge/HCS.md - the named real document."""

    @classmethod
    def setUpClass(cls):
        cls.doc_type, cls.findings = check_file(FIXTURE_HCS)
        cls.lines = FIXTURE_HCS.read_text(encoding="utf-8").splitlines()

    def test_fixture_exists(self):
        self.assertTrue(FIXTURE_HCS.is_file(), f"missing fixture {FIXTURE_HCS}")

    def test_detected_as_hcs(self):
        self.assertEqual(self.doc_type, "HCS")

    def test_no_errors(self):
        self.assertEqual(errors(self.findings), [], messages(self.findings))

    def test_exactly_five_warnings(self):
        self.assertEqual(len(warnings(self.findings)), 5, messages(self.findings))

    def test_all_warnings_are_source_ref_only(self):
        """The 5 known warnings are TBD/derived source refs - nothing else regressed."""
        for finding in warnings(self.findings):
            self.assertIn(
                "source ref", finding.message,
                f"unexpected warning kind: {finding.message}",
            )

    def test_parses_all_17_constraint_blocks(self):
        blocks = g0.parse_blocks(self.lines, "HCS")
        self.assertEqual(len(blocks), 17)
        self.assertEqual(len({b.id for b in blocks}), 17, "constraint IDs must be unique")

    def test_constraints_cited_in_derived_section_resolve(self):
        """§4 derived constraints cite §3 constraint IDs; they must all exist."""
        blocks = g0.parse_blocks(self.lines, "HCS")
        known = {b.id for b in blocks}
        for block in blocks:
            if block.id.startswith("HWC-DRV"):
                cited = g0._DEP_RE.findall(block.fields["Source ref"][0])
                for ref in cited:
                    self.assertIn(ref, known, f"{block.id} cites unknown {ref}")

    def test_every_component_exists_in_inventory(self):
        sections = g0.parse_markdown(self.lines)
        inventory = {
            g0.cell_text(row[0])
            for row in g0._parse_first_column(
                g0._section_content(sections, "### 1.5 Hardware Inventory")
            )
        }
        for block in g0.parse_blocks(self.lines, "HCS"):
            for comp in block.fields["Component"][0].replace("`", "").split(","):
                self.assertIn(comp.strip(), inventory, f"{block.id} orphan component")


class TestReferenceTemplates(unittest.TestCase):
    """templates/GT/ must stay in sync with the validator.

    If someone edits a template and drops a required heading, the sync test
    fails and names the exact heading that vanished.
    """

    @classmethod
    def setUpClass(cls):
        cls.srs_lines = TEMPLATE_SRS.read_text(encoding="utf-8").splitlines()
        cls.hcs_lines = TEMPLATE_HCS.read_text(encoding="utf-8").splitlines()
        cls.srs_sections = g0.parse_markdown(cls.srs_lines)
        cls.hcs_sections = g0.parse_markdown(cls.hcs_lines)

    def test_templates_exist(self):
        self.assertTrue(TEMPLATE_SRS.is_file(), f"missing {TEMPLATE_SRS}")
        self.assertTrue(TEMPLATE_HCS.is_file(), f"missing {TEMPLATE_HCS}")

    def test_srs_template_detected(self):
        self.assertEqual(g0.detect_doc_type(self.srs_sections), "SRS")

    def test_hcs_template_detected(self):
        self.assertEqual(g0.detect_doc_type(self.hcs_sections), "HCS")

    def test_every_srs_required_heading_is_in_the_template(self):
        """Sync guard: validator constants <-> template text."""
        text = TEMPLATE_SRS.read_text(encoding="utf-8")
        for heading in g0.SRS_REQUIRED:
            self.assertIn(
                heading, text,
                f"SRS template lost required heading {heading!r}; update "
                "templates/GT/G0_SRS.md or SRS_REQUIRED in g0_validate.py",
            )

    def test_every_hcs_required_heading_is_in_the_template(self):
        text = TEMPLATE_HCS.read_text(encoding="utf-8")
        for heading in g0.HCS_REQUIRED:
            self.assertIn(
                heading, text,
                f"HCS template lost required heading {heading!r}; update "
                "templates/GT/G0_HCS.md or HCS_REQUIRED in g0_validate.py",
            )

    def test_srs_template_has_no_missing_sections(self):
        findings = g0.validate_sections(self.srs_sections, "SRS")
        self.assertEqual(findings, [], messages(findings))

    def test_hcs_template_has_no_missing_sections(self):
        findings = g0.validate_sections(self.hcs_sections, "HCS")
        self.assertEqual(findings, [], messages(findings))

    def test_srs_template_fails_only_on_placeholders(self):
        """Unfilled template must FAIL (exit 1) but only via metadata placeholders
        and the illustrative block - never via missing structure."""
        _, findings = check(TEMPLATE_SRS.read_text(encoding="utf-8"))
        self.assertTrue(errors(findings), "unfilled template must not pass")
        for finding in errors(findings):
            self.assertNotIn(
                "missing required section", finding.message,
                f"template structure drifted: {finding.message}",
            )

    def test_hcs_template_fails_only_on_placeholders(self):
        _, findings = check(TEMPLATE_HCS.read_text(encoding="utf-8"))
        self.assertTrue(errors(findings), "unfilled template must not pass")
        for finding in errors(findings):
            self.assertNotIn(
                "missing required section", finding.message,
                f"template structure drifted: {finding.message}",
            )

    def test_templates_contain_exactly_one_example_block(self):
        self.assertEqual(len(g0.parse_blocks(self.srs_lines, "SRS")), 1)
        self.assertEqual(len(g0.parse_blocks(self.hcs_lines, "HCS")), 1)


class TestPhase1Sections(unittest.TestCase):
    def test_missing_section_reported(self):
        doc = MINIMAL_SRS.replace("### 1.4 References", "### 1.4 Bibliography")
        _, findings = check(doc)
        errs = errors(findings)
        self.assertTrue(any("missing required section" in f.message for f in errs),
                        messages(findings))
        self.assertTrue(any("1.4 References" in f.message for f in errs), messages(findings))

    def test_all_missing_sections_reported_individually(self):
        doc = MINIMAL_SRS.replace("## 6. Traceability", "## 6. Something Else")
        doc = doc.replace("### 2.1 Product Perspective", "### 2.1 Something Else")
        _, findings = check(doc)
        missing = [f for f in errors(findings) if "missing required section" in f.message]
        self.assertEqual(len(missing), 2, messages(findings))


class TestPhase2Metadata(unittest.TestCase):
    def test_placeholder_detected(self):
        doc = MINIMAL_SRS.replace("`SRS-TEST-001`", "`SRS-_ACRONYM_-_NNN_`")
        _, findings = check(doc)
        self.assertTrue(
            any("placeholder" in f.message for f in errors(findings)), messages(findings)
        )

    def test_underscore_placeholder_detected(self):
        doc = MINIMAL_SRS.replace("**Project** | Test Project", "**Project** | _full project name_")
        _, findings = check(doc)
        self.assertTrue(
            any("placeholder" in f.message and "Project" in f.message
                for f in errors(findings)), messages(findings)
        )

    def test_bad_semver_detected(self):
        doc = MINIMAL_SRS.replace("**Version** | 1.0.0", "**Version** | 1.0")
        _, findings = check(doc)
        self.assertTrue(
            any("SemVer" in f.message for f in errors(findings)), messages(findings)
        )

    def test_bad_classification_detected(self):
        doc = MINIMAL_SRS.replace("`INTERNAL`", "`SECRET`")
        _, findings = check(doc)
        self.assertTrue(
            any("Classification" in f.message for f in errors(findings)), messages(findings)
        )

    def test_missing_metadata_field_detected(self):
        doc = MINIMAL_SRS.replace("| **Organization** | Test Org |\n", "")
        _, findings = check(doc)
        self.assertTrue(
            any("metadata table missing required field 'Organization'" in f.message
                for f in errors(findings)), messages(findings)
        )


class TestPhase3SRSBlocks(unittest.TestCase):
    def test_bad_id_format_detected(self):
        doc = MINIMAL_SRS.replace("`ANAL-EMC-001`", "`ANAL-EMC-1`")
        _, findings = check(doc)
        self.assertTrue(
            any("does not match the required pattern" in f.message for f in errors(findings)),
            messages(findings),
        )

    def test_duplicate_id_detected(self):
        doc = MINIMAL_SRS.replace(
            "**Acceptance Criteria:**\n\n1. [ ] A thing happens.",
            "**Acceptance Criteria:**\n\n1. [ ] A thing happens.\n\n"
            "**`ANAL-EMC-001` — Second block**\n\n"
            "| Field | Value |\n|-------|-------|\n"
            "| **Type** | `FUNCTIONAL` |\n"
            "| **Priority** | `MUST` |\n"
            "| **Status** | `APPROVED` |\n"
            "| **Verification** | `TEST` |\n\n"
            "**Description:**\n\nThe system SHALL repeat.\n\n"
            "**Acceptance Criteria:**\n\n1. [ ] Repeats.",
        )
        _, findings = check(doc)
        self.assertTrue(
            any("duplicate block ID" in f.message for f in errors(findings)), messages(findings)
        )

    def test_long_title_detected(self):
        long_title = "A" * 130
        doc = MINIMAL_SRS.replace("— Test requirement", f"— {long_title}")
        _, findings = check(doc)
        self.assertTrue(
            any("block title is" in f.message for f in errors(findings)), messages(findings)
        )

    def test_missing_required_field_detected(self):
        doc = MINIMAL_SRS.replace("| **Verification** | `TEST` |\n", "")
        _, findings = check(doc)
        self.assertTrue(
            any("missing required field 'Verification'" in f.message for f in errors(findings)),
            messages(findings),
        )

    def test_invalid_enum_detected_with_expected_values(self):
        doc = MINIMAL_SRS.replace("`FUNCTIONAL`", "`SOMETIMES`")
        _, findings = check(doc)
        hit = [f for f in errors(findings) if "'Type'" in f.message]
        self.assertTrue(hit, messages(findings))
        self.assertIn("NON_FUNCTIONAL", hit[0].expected)

    def test_missing_description_detected(self):
        doc = MINIMAL_SRS.replace("**Description:**\n\nThe system SHALL do a thing.\n\n", "")
        _, findings = check(doc)
        self.assertTrue(
            any("missing '**Description:**'" in f.message for f in errors(findings)),
            messages(findings),
        )

    def test_description_without_shall_is_warning_not_error(self):
        doc = MINIMAL_SRS.replace("The system SHALL do a thing.", "The system does a thing.")
        _, findings = check(doc)
        self.assertTrue(
            any("SHALL/SHOULD" in f.message for f in warnings(findings)), messages(findings)
        )
        self.assertFalse(
            any("SHALL/SHOULD" in f.message for f in errors(findings)), messages(findings)
        )

    def test_missing_acceptance_criteria_detected(self):
        doc = MINIMAL_SRS.replace("**Acceptance Criteria:**\n\n1. [ ] A thing happens.", "")
        _, findings = check(doc)
        self.assertTrue(
            any("Acceptance Criteria" in f.message for f in errors(findings)), messages(findings)
        )

    def test_zero_numbered_criteria_detected(self):
        doc = MINIMAL_SRS.replace("1. [ ] A thing happens.", "Some prose instead.")
        _, findings = check(doc)
        self.assertTrue(
            any("no numbered items" in f.message for f in errors(findings)), messages(findings)
        )


class TestPhase3HCSBlocks(unittest.TestCase):
    def _hcs(self, **kw) -> str:
        doc = MINIMAL_HCS
        for old, new in kw.items():
            doc = doc.replace(old, new)
        return doc

    def test_range_missing_bounds_detected(self):
        doc = self._hcs(**{
            "| **Value min** | 1 MHz |\n| **Value max** | 6 GHz |\n": "",
        })
        _, findings = check(doc)
        msgs = messages(errors(findings))
        self.assertIn("Value min", msgs)
        self.assertIn("Value max", msgs)

    def test_non_range_missing_value_detected(self):
        doc = self._hcs(**{
            "`RANGE`": "`MAX`",
            "| **Value min** | 1 MHz |\n| **Value max** | 6 GHz |\n": "",
        })
        _, findings = check(doc)
        self.assertTrue(
            any("requires a non-empty 'Value'" in f.message for f in errors(findings)),
            messages(findings),
        )

    def test_orphan_component_detected(self):
        # Scope the edit to the Component field. A bare str.replace would also
        # rewrite the §1.5 inventory row and hide the orphan.
        doc = replace_field(MINIMAL_HCS, "Component", "`HW-SDR`", "`HW-GHOST`")
        self.assertIn("`HW-GHOST`", doc, "mutation did not apply")
        self.assertIn("| `HW-SDR` | HackRF One |", doc, "inventory row must stay intact")
        _, findings = check(doc)
        self.assertTrue(
            any("not listed in the §1.5 Hardware Inventory" in f.message
                for f in errors(findings)), messages(findings)
        )

    def test_unknown_source_ref_is_warning(self):
        doc = self._hcs(**{"`REF-DS-001` — Specifications": "_TBD — not selected yet_"})
        _, findings = check(doc)
        self.assertTrue(
            any("does not start with a known" in f.message for f in warnings(findings)),
            messages(findings),
        )
        self.assertFalse(
            any("Source ref" in f.message for f in errors(findings)), messages(findings)
        )

    def test_invalid_limit_type_enum_detected(self):
        doc = self._hcs(**{"`RANGE`": "`SOMETIMES`"})
        _, findings = check(doc)
        self.assertTrue(
            any("'Limit type'" in f.message for f in errors(findings)), messages(findings)
        )

    def test_multi_component_all_checked(self):
        """A block citing two components must validate BOTH against the inventory."""
        # Legitimately add HW-CPU to the inventory, then point the Component
        # field at both. Both edits are scoped so the inventory row for HW-SDR
        # is never rewritten into a bogus multi-value cell.
        two_parts = MINIMAL_HCS.replace(
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


class TestPhase4CrossRefs(unittest.TestCase):
    def test_unknown_dependency_detected(self):
        doc = MINIMAL_SRS.replace("**Dependencies** | —", "**Dependencies** | `ANAL-EMC-999`")
        _, findings = check(doc)
        self.assertTrue(
            any("does not exist in this document" in f.message for f in errors(findings)),
            messages(findings),
        )

    def test_traceability_gap_is_warning(self):
        doc = MINIMAL_SRS.replace("| `ANAL-EMC-001` | Test | — | TC-001 |", "")
        _, findings = check(doc)
        self.assertTrue(
            any("not listed in the §6 Traceability table" in f.message
                for f in warnings(findings)), messages(findings)
        )

    def test_circular_dependency_detected(self):
        second = (
            "\n**`ANAL-EMC-002` — Second requirement**\n\n"
            "| Field | Value |\n|-------|-------|\n"
            "| **Type** | `FUNCTIONAL` |\n"
            "| **Priority** | `MUST` |\n"
            "| **Status** | `APPROVED` |\n"
            "| **Verification** | `TEST` |\n"
            "| **Dependencies** | `ANAL-EMC-001` |\n\n"
            "**Description:**\n\nThe system SHALL cycle back.\n\n"
            "**Acceptance Criteria:**\n\n1. [ ] Cycles.\n"
        )
        doc = MINIMAL_SRS.replace(
            "**Dependencies** | —", "**Dependencies** | `ANAL-EMC-002`"
        ).replace("\n## 4. External Interface Requirements", second + "\n## 4. External Interface Requirements")
        doc = doc.replace(
            "| `ANAL-EMC-001` | Test | — | TC-001 |",
            "| `ANAL-EMC-001` | Test | — | TC-001 |\n| `ANAL-EMC-002` | Test | — | TC-002 |",
        )
        _, findings = check(doc)
        self.assertTrue(
            any("circular dependency" in f.message for f in errors(findings)), messages(findings)
        )

    def test_self_dependency_is_a_cycle(self):
        doc = MINIMAL_SRS.replace("**Dependencies** | —", "**Dependencies** | `ANAL-EMC-001`")
        _, findings = check(doc)
        self.assertTrue(
            any("circular dependency" in f.message for f in errors(findings)), messages(findings)
        )

    def test_acyclic_chain_passes(self):
        second = (
            "\n**`ANAL-EMC-002` — Second requirement**\n\n"
            "| Field | Value |\n|-------|-------|\n"
            "| **Type** | `FUNCTIONAL` |\n"
            "| **Priority** | `MUST` |\n"
            "| **Status** | `APPROVED` |\n"
            "| **Verification** | `TEST` |\n"
            "| **Dependencies** | `ANAL-EMC-001` |\n\n"
            "**Description:**\n\nThe system SHALL depend on the first.\n\n"
            "**Acceptance Criteria:**\n\n1. [ ] Depends.\n"
        )
        doc = MINIMAL_SRS.replace(
            "\n## 4. External Interface Requirements", second + "\n## 4. External Interface Requirements"
        ).replace(
            "| `ANAL-EMC-001` | Test | — | TC-001 |",
            "| `ANAL-EMC-001` | Test | — | TC-001 |\n| `ANAL-EMC-002` | Test | — | TC-002 |",
        )
        _, findings = check(doc)
        self.assertFalse(
            any("circular dependency" in f.message for f in findings), messages(findings)
        )


class TestCliExitCodes(unittest.TestCase):
    """End-to-end contract: 0 pass, 1 errors, 2 script error."""

    def _run(self, *args) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True, text=True, timeout=120,
        )

    def test_script_is_stdlib_only(self):
        """The skill must never acquire a venv requirement."""
        source = SCRIPT.read_text(encoding="utf-8")
        for banned in ("import pytest", "import requests", "import numpy", "import pandas"):
            self.assertNotIn(banned, source, f"{banned} would break the stdlib-only contract")

    def test_real_fixtures_exit_zero(self):
        result = self._run(str(FIXTURE_SRS), str(FIXTURE_HCS))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Result: PASS", result.stdout)
        self.assertEqual(result.stdout.count("G0 VALIDATION REPORT"), 2)

    def test_broken_document_exits_one(self):
        import tempfile, os
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as fh:
            fh.write(MINIMAL_SRS.replace("### 1.4 References", "### 1.4 Bibliography"))
            path = fh.name
        try:
            result = self._run(path)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("Result: FAIL", result.stdout)
        finally:
            os.unlink(path)

    def test_missing_file_exits_two(self):
        result = self._run("/nonexistent/g0_test_file.md")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    def test_undetectable_type_exits_two(self):
        import tempfile, os
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as fh:
            fh.write("# Just a title\n\nNo document type heading here.\n")
            path = fh.name
        try:
            result = self._run(path)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        finally:
            os.unlink(path)

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
            "validate_cross_refs", "format_report", "main",
        ):
            self.assertTrue(callable(getattr(g0, name, None)),
                            f"g0_validate.py no longer exposes {name}()")

    def test_documented_dataclasses_exist(self):
        self.assertTrue(hasattr(g0, "Finding"))
        self.assertTrue(hasattr(g0, "Block"))

    def test_required_section_constants_match_documented_lists(self):
        self.assertEqual(len(g0.SRS_REQUIRED), 15)
        self.assertEqual(len(g0.HCS_REQUIRED), 10)


if __name__ == "__main__":
    unittest.main(verbosity=2)
