# Slice Deltas

Changes to the planned module slicing, registered through G3 FEEDBACK (module defect, slice complete) or
RFD-accepted requirement changes. Deltas are immutable records; they inform re-planning but do not directly
edit the BACKLOG.md.

## Per-Slice Decisions

### Slice 01

| Issue | Verdict | Verdict from | Action | Date |
|-------|---------|--------------|--------|------|
| {{problem detected}} | module defect / slice complete / GT defect | {{G3 / S3 / ...}} | {{re-plan / next slice / RFD}} | {{date}} |

---

## RFD-Accepted Changes

Requirement changes accepted by Build Package author through RFD (outside the chain).

| Change | Verdict | Date | Impact |
|--------|---------|------|--------|
| {{SYS-nnn tolerance adjusted}} | Accepted | {{date}} | {{affects slice-NN}} |
| {{New module SUB-NNN/name added}} | Accepted | {{date}} | {{inserted into BACKLOG}} |

---

**Instructions:**

1. Record every G3 FEEDBACK verdict (module defect, slice complete) in the per-slice table.
2. Record every RFD-accepted change in the RFD-Accepted table.
3. Deltas inform the next S2 planning pass but do not modify BACKLOG.md directly.
4. When a delta is resolved (re-plan complete, next slice planned), mark its action as complete with date.
