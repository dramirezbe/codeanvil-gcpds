# Project layout — locked reference for S2

Build exactly these trees in the project root, outside `.codeanvil/`. One rule for every language:
**each service is `src/<package>/`**, where `<package>` is the package name of its design
`Toolchain` entry (`SVC-xxx: <package> · <language> · <package manager> · <test runner>`). Root
manifests exist only for the toolchains in use. Layer folders (`dsp/`, `decision/`, `output/`, …)
are the design's functional layers, one per layer.

## Python service (uv · pytest)

```
src/<package>/
├── __init__.py
├── __main__.py            # from <package>.main import main; main()
├── main.py                # base: orchestration and routing, def main() -> None
├── config/
│   ├── __init__.py
│   ├── logger.py          # copied unchanged from references/logger.py
│   ├── paths.py           # every filesystem path resolved here
│   └── runtime.py         # TIMEZONE = "America/Bogota" and other runtime constants
├── hal/
│   ├── __init__.py
│   ├── port.py            # the HAL port the base and modules depend on
│   └── real.py            # Real HW HAL, mock+real only
├── <layer>/               # one subpackage per functional layer, each with __init__.py
└── lib/                   # shared helpers of this service
```

## TypeScript service (pnpm · vitest)

A pnpm package with **no nested `src/`**.

```
src/<package>/
├── package.json           # "type": "module", no dependency on any verification/ package
├── tsconfig.json          # strict, "allowImportingTsExtensions" or "rewriteRelativeImportExtensions";
│                          #   "lib" with "DOM" for a UI, "types": ["node"] + @types/node (dev) for Node
├── main.ts                # base entry; a UI uses main.tsx + index.html + vite.config.ts
├── config/
│   ├── logger.ts          # copied unchanged from references/logger.ts
│   └── runtime.ts         # export const TIMEZONE = "America/Bogota";
├── hal/                   # the HAL port, plus the Real HW HAL in mock+real
├── <layer>/               # one folder per functional layer
└── lib/
```

## Root manifests

```
pyproject.toml             # Python services exist
uv.lock
package.json               # TypeScript services exist: "private": true, "packageManager": "pnpm@<version>"
pnpm-workspace.yaml        # packages: ["src/*", "verification/*"] (TS services and TS kits only)
pnpm-lock.yaml
.env.example               # committed; .env is git-ignored
cmd/                       # install and deploy scripts, only when the design deploys to a host
daemon/                    # systemd units, only when the design deploys to a host
run-demo                   # multi-service preview launcher when design §0.5 names one
```

`pyproject.toml`, one for all Python services:

```toml
[project]
name = "<project>"
requires-python = ">=3.12"
dependencies = []                 # runtime dependencies of the services only

[project.scripts]
<package> = "<package>.main:main" # one entry per Python service

[dependency-groups]
dev = ["pytest"]                  # plus every kit dependency; never in [project] dependencies

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/<package>"]      # listed explicitly, one per Python service; never verification/

[tool.pytest.ini_options]
testpaths = ["verification"]
pythonpath = ["src", "."]
markers = ["vl0: VL-0 floor test", "vl1: VL-1 metric test"]
```

Kit code is imported from the project root, never as a top-level package: `verification/<package>/`
has the same name as `src/<package>/` and would be shadowed by it. Write
`from verification.<package>.mock_hal import ...` and `from <package>.hal.port import ...`.

No `sys.path` bootstrap. Deploy with `uv sync --frozen --no-dev`, start with `uv run <package>`.
The telemetry collector ships with CodeAnvil itself and is invoked as `codeanvil telemetry`; it is
not copied into the project, and the kit's dev group never lists `psutil`. `run.sh` starts it in the
background with `--pid $$`, so it measures `run.sh` and every process `run.sh` starts, never the collector itself.
The `<package>.main:main` function must instantiate a runtime HAL and run the service; logging
startup instructions without starting the loop is not a working entry point. In `mock-only`, the
runtime Mock HAL required for a preview lives in the package or a shipped demo bundle, while the
independent vectors and test drivers stay under `verification/`.
A uv workspace is allowed only when two Python services deploy to different hosts with conflicting
dependencies, and only as a recorded design decision.

## Verification kit (never shipped)

```
verification/
├── run.sh                 # verification/run.sh vl0 | verification/run.sh vl1
├── golden/
│   ├── manifest.md        # one row per vector: id, SHA-256, generation parameters,
│   │                      #   simulated condition, expected output
│   └── <vector files>
├── telemetry/             # one JSONL file per run, written by `codeanvil telemetry`
│   └── <cycle>_<iteration>_<timestamp>/ # measurement.json v2, named telemetry and script outputs
└── <package>/             # one folder per service, in that service's language
    ├── mock_hal/          # VL-0 vectors and the VL-1 synthetic generator
    ├── stubs/             # one stub per contract of a module not built yet
    ├── fakes/             # one fake peer per service-to-service contract
    ├── drivers/           # bottom-up drivers through the base
    └── test/              # pytest (Python) or vitest (TS); markers or scripts vl0 and vl1
```

A TS kit `verification/<package>/` is a private pnpm package with vitest and the scripts
`test:vl0` and `test:vl1`. In `mock+real` the kit also holds the fake device API that the Real HW
HAL's VL-0 tests use.

`verification/run.sh <vl0|vl1>`:

Set `export PATH="$HOME/.local/bin:$PATH"` inside `run.sh` before starting the collector or any
package-manager command. Non-login SSH does not load shell startup files, so set the target's
PATH explicitly rather than relying on the host's environment.

1. starts the telemetry collector in the background:
   `codeanvil telemetry --pid $$ --output verification/telemetry/<run_id>/<run_id>.jsonl &`,
   with the design §1.7 `--interval`, and `--counters` when the HAL or services expose counters;
   add `--fsync` only when the design requests durable per-sample writes (default off);
2. runs `uv run pytest -m <level>` when a Python service exists;
3. runs `pnpm -r --filter "./verification/*" test:<level>` when a TS service exists;
4. stops the companion and attaches its readings to the run output;
5. exits non-zero if any run failed.

The run ID is `<cycle>_<iteration>_<codeanvil now --machine>`: the current S2/G2 iteration,
not a new HIL counter. A retry gets another timestamp. Use fresh outputs without overwriting.
The companion degrades on disk failure; exit 0 does not certify telemetry coverage. Investigate
missing/partial telemetry, notify the parent and decide whether affected measures need repeating
or unaffected evidence can continue. Never turn a missing reading into zero. A reader may skip
only a torn final JSONL line with notice; earlier corruption needs diagnosis.

In `mock+real`, `verification/run.sh vl2` uses the Real HW HAL and measurement scripts appropriate
to the GT, writes `measurement.json` v2 and script/capture outputs beside telemetry, and stops the
device/companion on errors. Test orchestration/failure paths with a fake API, but never claim
those fake results as real hardware evidence. This skill's locked `references/machine_evidence.md`
and `measurement.schema.json` describe the small record. Functional tests need no universal
oracle, file hashes or calibration budget; satisfy lab inputs when the GT/conclusion needs them.

Before remote updates/deployment or local HW tests, the parent shows the clean, pushed candidate
and planned operations and waits for explicit `continue`. After review the agent updates tool,
app and dependencies from their own published refs, synchronizes clocks before measurement and
uses monotonic durations while acquiring. No deployment manifest or per-file checker is built.
`code_sync` exports only the published Git candidate and preserves target databases/state; do not
send ignored host source. Read-only inventory may precede review, actual device tests may not.

`fetch_evidence` returns `local_path`, a fresh host snapshot of remote telemetry. Select this
run's files within it; older remote runs may also be present. Local runs read their local output.
The existing S2 pause schedule, `Checkpoint:` narrative and append-only report format remain;
no partial iteration or extra HITL state represents an operational stop.

Never shipped: no service imports or depends on anything under `verification/`. Python kit
dependencies live only in the dev group and the wheel holds no `verification/` file; no service
`package.json` lists a kit package.

## Conventions inside each service

- Type hints everywhere; Google-style docstrings in Python, TSDoc in TypeScript.
- `.env.example` committed, `.env` ignored; paths resolved in `config/paths.py` (Python) or one
  `config/` module (TS).
- Every module logs through its service logger: `log = get_logger(__name__)` in Python,
  `const log = getLogger("<package>.<module>")` in TypeScript. No `print`, no bare `console.log`.
- No file, import, dependency or string refers to the tool that scaffolded the project.

## Mixed example (`fm_edge` Python + `dashboard` TypeScript)

Toolchain: `SVC-001: fm_edge · Python 3.12 · uv · pytest; SVC-002: dashboard · TypeScript · pnpm · vitest`.

```
pyproject.toml   uv.lock   package.json   pnpm-workspace.yaml   pnpm-lock.yaml   .env.example
cmd/   daemon/
src/
├── fm_edge/       __init__.py __main__.py main.py config/ hal/ dsp/ decision/ output/ lib/
└── dashboard/     package.json tsconfig.json main.tsx index.html vite.config.ts config/ hal/ views/ lib/
verification/
├── run.sh   golden/manifest.md   telemetry/
├── fm_edge/       mock_hal/ stubs/ fakes/ drivers/ test/
└── dashboard/     package.json mock_hal/ stubs/ fakes/ drivers/ test/
```
