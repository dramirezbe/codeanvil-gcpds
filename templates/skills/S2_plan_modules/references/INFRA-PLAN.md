# Slice 0 — Infrastructure plan

## Per-subsystem bases
{{Logging, control/error lifecycle, Mock HAL, base API and production paths.}}

## Toolchain
{{Exact SDD toolchain, root manifests, install and verification commands.}}

## Verification kit
{{SDD §1.3.4: VL, generator, golden vectors, oracle, tolerance, command and telemetry.}}

## Module stubs
{{All module identities and interface-complete stub paths; no behavior invented.}}

## Top-down integration
{{Bases call stubs; copy the exact cross-subsystem placeholder schema and concrete fixture
values or a deterministic generation recipe, with expected receiver output. Include valid,
invalid-version and error-path observations; do not abbreviate required arrays.}}

## Acceptance
{{verification/run.sh vl0; all placeholders load before any module implementation.
Base/stub startup and placeholder handshakes are the slice-0 smoke; no final root-command
smoke, future module criteria or final PATH-* acceptance is claimed here.}}

## Parent Context set

{{Exact design/GT sections or files, base APIs, kit and shared artifacts needed for this scope.
The S3 parent may read full SDD/GT for infrastructure/integration; this does not expand any
module implementor's isolated Context set. Include inputs, commands and expected outcomes
for every shared task so G2 can review completeness and execution sufficiency.}}

## Ordered delivery tasks

| Order | Files or inputs | Creation task and command | Expected output or observable result |
|-------|-----------------|---------------------------|--------------------------------------|
{{Populate manifests/install, base APIs, registry/stubs, fake peers/handshake, telemetry and
runner tasks in dependency order. Name actual paths, commands, exit contract and saved artifacts.
These are S3 creation tasks; S2 writes the plan, not the runner or implementation code.}}
