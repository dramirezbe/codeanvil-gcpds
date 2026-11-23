# AGENTS.md — Tutor review

Cross-cutting review of generated project instructions, using the same procedure
as a skill review. AGENTS is not an additional methodology stage.

| Path | Contents |
|------|----------|
| [raw/](raw/) | Original audit text and four SVGs supplied in `raw-AGENTSmd/`; moved without editing their bytes. |
| [RAW_MANIFEST.sha256](RAW_MANIFEST.sha256) | Checksums recorded when organising the supplied artifacts. |
| [EXPLAIN.md](EXPLAIN.md) | Spanish triage of all eleven findings, contextual evidence and corrections. |
| [corrected/](corrected/) | Reserved for tutor `PATCHES.md` and our subsequent `ANALYSIS.md`. No patches were supplied. |

The audit names its target `SKILL_pre_david.md` and instrument `Navaja_(6).md`.
Neither original file was supplied. We therefore cannot establish byte-for-byte
identity with the audited target or inspect the instrument itself. The contrast
uses the [source template](../../../../templates/AGENTS/TEMPLATE_AGENT.md), skills,
CLI, scaffold and tests at baseline `2af198d532986ffef70da40c20e140e228a3584d`.

Result: **5 valid execution-contract defects**, **1 partially valid recovery
limitation**, and **5 findings not established as defects because the external
audit lacked context**. No fundamental methodology concept error was established.
The five defects were corrected in `e44d7c000b69ebe807b0f42653ebff53d5437fc5`.
This completes initial triage and our own fixes, not a tutor patch review or an
end-to-end acceptance of the methodology.

Verify the preserved inputs from this directory with `sha256sum -c RAW_MANIFEST.sha256`.
The local Git attributes preserve original line endings and whitespace in `raw/`;
normal formatting checks still apply to the analysis and corrections.
