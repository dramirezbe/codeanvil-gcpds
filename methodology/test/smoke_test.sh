#!/usr/bin/env bash
# smoke_test.sh — Automated end-to-end smoke test for CodeAnvil
#
# Validates: install → scaffold → GT copy → G0 → custody-chain → tamper detection
# Uses claude -p (print mode) with sandboxed settings.
#
# Prerequisites:
#   - codeanvil installed and initialized (codeanvil init)
#   - claude CLI available
#   - Run from the CodeAnvil repo root
#
# Usage: bash methodology/test/smoke_test.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PROJECT_DIR="/tmp/smoke-test"
CLAUDE_FLAGS=(--setting-sources "project" --dangerously-skip-permissions --verbose -p)

pass() { echo -e "\033[32m  PASS\033[0m $1"; }
fail() { echo -e "\033[31m  FAIL\033[0m $1"; FAILURES=$((FAILURES + 1)); }
step() { echo -e "\n\033[1m[$1/$TOTAL] $2\033[0m"; }

FAILURES=0
TOTAL=7

# ── Step 1: Scaffold ─────────────────────────────────────────────────
step 1 "Scaffold project and copy T0 GT files"

rm -rf "$PROJECT_DIR"
codeanvil init 2>/dev/null || true
codeanvil create smoke-test -p /tmp 2>&1 | tail -1

# Copy T0 GT files
cp "$REPO_ROOT/methodology/test/T0_ANE-Lap2/just-edge/SRS.md" "$PROJECT_DIR/GT/G0_SRS.md"
cp "$REPO_ROOT/methodology/test/T0_ANE-Lap2/just-edge/HCS.md" "$PROJECT_DIR/GT/G0_HCS.md"

# Set HMAC key for custody-chain
export PROVENANCE_HMAC_KEY="smoke-test-key-2026"

# Verify scaffold
[[ -f "$PROJECT_DIR/AGENTS.md" ]]                          && pass "AGENTS.md exists"           || fail "AGENTS.md missing"
[[ -L "$PROJECT_DIR/CLAUDE.md" ]]                          && pass "CLAUDE.md is symlink"       || fail "CLAUDE.md not a symlink"
[[ -d "$PROJECT_DIR/.agents/skills/G0_valid_req_and_GT" ]] && pass "G0 skill present"           || fail "G0 skill missing"
[[ -d "$PROJECT_DIR/.agents/skills/custody-chain" ]]       && pass "custody-chain skill present" || fail "custody-chain skill missing"
[[ -f "$PROJECT_DIR/GT/G0_SRS.md" ]]                       && pass "GT/G0_SRS.md copied"        || fail "GT/G0_SRS.md missing"
[[ -f "$PROJECT_DIR/GT/G0_HCS.md" ]]                       && pass "GT/G0_HCS.md copied"        || fail "GT/G0_HCS.md missing"

# ── Step 2: Context check ────────────────────────────────────────────
step 2 "Context check — does Claude know it's in a user project?"

CONTEXT_OUT=$(cd "$PROJECT_DIR" && claude "${CLAUDE_FLAGS[@]}" \
  "What project is this? What skills are available? What gate should run first? Answer in under 100 words.")

echo "$CONTEXT_OUT" | head -20
echo "$CONTEXT_OUT" | grep -qi "G0\|gate.*0\|first.*gate\|validation" \
  && pass "Claude identifies G0 as first gate" \
  || fail "Claude did not identify G0 as first gate"

# ── Step 3: Run G0 ───────────────────────────────────────────────────
step 3 "Run G0 validation"

G0_OUT=$(cd "$PROJECT_DIR" && claude "${CLAUDE_FLAGS[@]}" \
  "Run G0 validation on GT/G0_SRS.md and GT/G0_HCS.md. Use the g0_validate.py script from the G0 skill. Report the exit code and verdict.")

echo "$G0_OUT" | tail -30
echo "$G0_OUT" | grep -qi "G0.*PASS\|PASS.*G0\|exit.*code.*0\|0 error" \
  && pass "G0 validation passed" \
  || fail "G0 validation did not pass"

# ── Step 4: Seal GT ──────────────────────────────────────────────────
step 4 "Seal GT files with custody-chain"

SEAL_OUT=$(cd "$PROJECT_DIR" && claude "${CLAUDE_FLAGS[@]}" \
  "Load the custody-chain skill. Seal the GT files: run source_snapshot.py snapshot with --root . --include 'GT/**' --out .codeanvil/custody/snapshot.json. Then record custody for GT/G0_SRS.md and GT/G0_HCS.md (action created, actor smoke-test, role tester). Then verify the ledger. PROVENANCE_HMAC_KEY is set.")

echo "$SEAL_OUT" | tail -30
[[ -f "$PROJECT_DIR/.codeanvil/custody/snapshot.json" ]] \
  && pass "Snapshot created" \
  || fail "Snapshot not created"
[[ -f "$PROJECT_DIR/.codeanvil/custody/custody.jsonl" ]] \
  && pass "Custody ledger created" \
  || fail "Custody ledger not created"

# ── Step 5: Verify GT unchanged ──────────────────────────────────────
step 5 "Verify GT integrity (should PASS)"

VERIFY_OUT=$(cd "$PROJECT_DIR" && claude "${CLAUDE_FLAGS[@]}" \
  "Run source_snapshot.py verify with --root . --snapshot .codeanvil/custody/snapshot.json --strict. Report the status.")

echo "$VERIFY_OUT" | tail -15
echo "$VERIFY_OUT" | grep -qi "PASS\|intact\|no.*finding\|verified" \
  && pass "GT verification passed" \
  || fail "GT verification did not pass"

# ── Step 6: Tamper detection ─────────────────────────────────────────
step 6 "Tamper GT and detect"

echo "# TAMPERED BY SMOKE TEST" >> "$PROJECT_DIR/GT/G0_SRS.md"

TAMPER_OUT=$(cd "$PROJECT_DIR" && claude "${CLAUDE_FLAGS[@]}" \
  "Run source_snapshot.py verify with --root . --snapshot .codeanvil/custody/snapshot.json --strict. Report any integrity violations found.")

echo "$TAMPER_OUT" | tail -20
echo "$TAMPER_OUT" | grep -qi "FAIL\|DIGEST_CHANGED\|LENGTH_CHANGED\|tamper\|mismatch\|changed" \
  && pass "Tamper detected" \
  || fail "Tamper not detected"

# ── Step 7: Custody history ──────────────────────────────────────────
step 7 "Custody history for GT/G0_SRS.md"

HIST_OUT=$(cd "$PROJECT_DIR" && claude "${CLAUDE_FLAGS[@]}" \
  "Show custody history for GT/G0_SRS.md using custody_ledger.py history.")

echo "$HIST_OUT" | tail -10
echo "$HIST_OUT" | grep -qi "created\|smoke-test\|history\|seq" \
  && pass "Custody history shown" \
  || fail "Custody history not found"

# ── Summary ──────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════"
if [[ $FAILURES -eq 0 ]]; then
  echo -e "\033[32m  ALL CHECKS PASSED\033[0m"
else
  echo -e "\033[31m  $FAILURES CHECK(S) FAILED\033[0m"
fi
echo "════════════════════════════════════════"

# Cleanup
rm -rf "$PROJECT_DIR"
unset PROVENANCE_HMAC_KEY

exit "$FAILURES"
