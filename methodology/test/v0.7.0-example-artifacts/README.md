# CodeAnvil 0.7.0 example artifacts

Five portable project snapshots for UI tests, created with release **v0.7.0
(`2f08944`)**. Progress reports and human/verifier decisions are **synthetic**.
They are display fixtures, not genuine gate approvals or hardware validation.
The deterministic G0 checks, Python test logs and telemetry were actually run
when preparing the examples.

| Project | Fixture state | Reports | Runtime preview |
|---------|---------------|---------|-----------------|
| [laboratorio_espectro_rf](laboratorio_espectro_rf/) | Empty scaffold | None | None |
| [monitor_ocupacion_fm](monitor_ocupacion_fm/) | Through G0 | S0, G0 | None |
| [banco_telemetria_cots](banco_telemetria_cots/) | Through G1 | S0, G0, S1, G1 | None |
| [api_procesamiento_senales](api_procesamiento_senales/) | Through S2 | S0, G0, S1, G1, S2 | Mock counter, port 8853 |
| [panel_prototipo](panel_prototipo/) | Through G2 | S0, G0, S1, G1, S2, G2 | Mock counter, port 8854 |

The four progressed projects use cycle `01_ui_demo`. Their domain names are
launcher labels: the implemented example is only a local synthetic counter.
The empty project has no cycle, Ground Truth pair, source code or reports.

## What is preserved

Project identities, relative GT pointers, generated instructions, seven copied
0.7.0 skills, agent links/subagent definitions, GT, design/graph, cycle reports,
code, verification kit, lockfiles and recorded test/telemetry output are copied
unchanged from the prepared projects. The final sample includes
`.codeanvil/report/01_ui_demo/G2_artifacts/verified_prototype.md`.

Virtual environments, Python/test caches, Git internals, node_modules and local
`.env` files are excluded. Empty directories have `.gitkeep` files so the
scaffold survives a Git clone. These markers are archival additions, not
CodeAnvil-generated artifacts. Symlinks remain relative within each project.
The global SQLite DB and machine credentials are not part of the snapshots.

`ARCHIVE_MANIFEST.json` records expected profiles, exclusions, file SHA-256
digests, executable flags and symlink targets. To verify the stored payload:

```bash
python3 methodology/test/v0.7.0-example-artifacts/verify.py
```

## Use working copies after cloning

Keep these snapshots unchanged. From the repository root, with CodeAnvil 0.7.0
installed, copy the collection and register the working copies:

```bash
fixture_dir="$(mktemp -d)"
cp -a methodology/test/v0.7.0-example-artifacts/. "$fixture_dir/"
codeanvil init
for project in "$fixture_dir"/*/; do
    (cd "$project" && codeanvil sync)
done
```

`sync` preserves the captured UUIDs. If those UUIDs are already registered,
it moves their local DB paths to the working copies; it does not create
duplicate registrations. Open those copies in the development UI. The release
0.7.0 CLI itself does not include the later `ui` command.

For the final sample, using the same shell:

```bash
cd "$fixture_dir/panel_prototipo"
codeanvil status
uv sync --frozen --no-dev
uv run --no-dev demo_counter
```

Open `http://127.0.0.1:8854/`; the page shows repeating Mock HAL values 0, 1, 2.
Stop with Ctrl-C. To rerun its small automated checks instead:

```bash
uv sync --frozen
verification/run.sh vl0
verification/run.sh vl1
```

The captured results are 3 VL-0 tests and 1 VL-1 test passing. New runs produce
their own telemetry; they do not convert the synthetic G2 decision into an
actual human approval.
