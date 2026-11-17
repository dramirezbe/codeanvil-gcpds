# G2 Plan Review Checklist

A human-facing checklist for reviewing each module in the slice plan. Use this during G2 review to systematically
validate all 6 checks.

## Slice: {{slice_id}}

| Module | G2.1 Present | G2.2 Order | G2.3 VL-2 Ready | G2.4 Test Entry | G2.5 Contracts | G2.6 Boundary | Findings |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|---------|
| {{module_id}} | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | (open or advisory) |

---

## Per-Module Details

For modules with open findings, record the issue and resolution:

### {{module_id}}

- **Issue:** {{what failed}}
- **Check(s):** {{G2.N}}
- **Resolution:** {{how to fix, or escalation}}
- **Verdict:** {{open / advisory / resolved}}

---

## Cross-Slice Dependencies

List any modules in later slices that depend on contracts produced by this slice:

| Later Module | Depends On | Status |
|--------------|-----------|--------|
| {{later_module_id}} | {{contract}} | ✓ available / ⚠️ deferred / ✗ missing |

---

## Open Findings Summary

| Check | Count | Severity | Blocking? |
|-------|-------|----------|-----------|
| G2.1 | — | — | — |
| G2.2 | — | — | — |
| G2.3 | — | — | — |
| G2.4 | — | — | — |
| G2.5 | — | — | — |
| G2.6 | — | — | — |

---

## Recommendation

- [ ] **PASS:** All checks passed. Recommend S3 proceed.
- [ ] **FEEDBACK, plan defect:** Replan and S2 re-enters.
- [ ] **FEEDBACK, infra defect:** Infrastructure incomplete; defer or escalate.
- [ ] **FEEDBACK, GT defect:** Requirement or design issue; consider RFD.
