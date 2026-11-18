# Changelog

## 0.9.1 — unreleased

- Seed Codex sandbox login from auth.json as well as installation_id, honoring an inherited CODEX_HOME.
- Keep the copied authentication files private and temporary while preserving global-settings isolation.

## 0.9.0 — 2026-11-17

- Close scope-specific verification, immutable plan, rework and mandatory delta-review contracts.
- Eight-node V-SIL v4 chain with per-module plans, slice cadence and fresh implementation contexts.
- Plan micro-gate, scoped verification and system-only Verified Prototype.
- Custody checks report inputs and golden vectors; authorized interface-neutral deltas preserve evidence.
- Living GT/design delta-sync and source-preserving feedback routes.
- Breaking methodology change: start a new v4 scaffold/cycle; no migration command.
- UI remains v3-only until a dedicated follow-up. Published before T0 full-flow acceptance by owner authorization.

Validation before release: 742 automated tests passed, 40 skipped; full T0 v4 execution and
human gate acceptance remain pending.

## 0.7.5 — Simple red-button deletion confirmation

Replaces typed-name UI confirmation with a direct question, Cancel and a red Delete button. Keeps explicit file-removal selection and existing identity/path safeguards.

Validation: 606 Python tests passed, 1 skipped; 30 frontend tests passed; frontend and distributions built.

## 0.7.4 — Project deletion in CLI and UI

Shared guarded project deletion, the delete CLI command, explicit file-removal option, and a dedicated UI confirmation dialog. Directory identity is revalidated before removal.

Validation: 606 Python tests passed, 1 skipped; 30 frontend tests passed; frontend and distributions built.

## 0.7.3 — Matching light and dark dependency graphs

S1 delivers dark and light graphs from one offline renderer; backups preserve both, and the UI follows its active theme. Removes the duplicate launcher return control.

Validation: 557 Python tests passed, 1 skipped; 22 frontend tests passed; frontend and distributions built.

## 0.7.2 — Clearer project navigation and creation

Contextual launcher navigation, readable home-relative paths, user context, Documents/Documentos defaults, CLI-derived folder suggestions and a local Anvil favicon.

Validation: 550 Python tests passed, 1 skipped; 19 frontend tests passed; frontend and distributions built.

## 0.7.1 — Self-contained graphical workspace

Project creation/import, cycle and report browsing, safe artifact views, shared report state, local fonts and a complete global UI install. Includes the pending HIL packaging, setup and synchronization fixes already on main.

Validation: 537 Python tests passed, 1 skipped; 11 frontend tests passed; frontend and distributions built.
