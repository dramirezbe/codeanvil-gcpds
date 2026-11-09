# Test fixtures

Reference inputs owned by the test suite. These files exist **only** to drive the
tests and are decoupled from `methodology/test/` so that editing or deleting a
methodology test case never breaks the code tests.

| File | Used by | Role |
|------|---------|------|
| `StRS.md` | `templates/tests/test_g0_validate.py`, `tests/test_vsil_v3_s0.py`, `tests/test_create.py` | A valid, passing Stakeholder Requirements Specification (64 blocks: 43 STK + 17 HWC + 4 NRM). The G0 validator must accept it with the pinned error/warning counts. |
| `SyRS.md` | same | The matching System Requirements Specification. |

The pair is the ANE edge-sensor example that previously lived under
`methodology/test/T0_ANE-Lap2/just-edge/`. It was moved here when that methodology
test case was retired, because tests must not read product/methodology data. The
counts asserted in `test_g0_validate.py` (`FIXTURE_STRS_BLOCK_COUNT`, etc.) are
pinned to this content; change the fixture and update those constants together.
