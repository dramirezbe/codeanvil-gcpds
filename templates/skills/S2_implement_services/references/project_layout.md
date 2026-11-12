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
├── deployment_manifest.json # remote PIL or any VL-2: final input hashes
├── check_deployment.py     # remote PIL or any VL-2: stdlib, read-only G2 preflight
├── golden/
│   ├── manifest.md        # one row per vector: id, SHA-256, generation parameters,
│   │                      #   simulated condition, expected output
│   └── <vector files>
├── telemetry/             # one JSONL file per run, written by `codeanvil telemetry`
│   └── <run-id>/          # conditional VL-2: immutable measurement.json, telemetry and captures
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
package-manager command. Non-login SSH does not load shell startup files; do not rely on the
host's PATH or send an environment-expanding shell command through the auto MCP door.

1. starts the telemetry collector in the background:
   `codeanvil telemetry --pid $$ --output verification/telemetry/<level>-<timestamp>.jsonl &`,
   with the design §1.7 `--interval`, and `--counters` when the HAL or services expose counters;
   add `--fsync` only when the design requests durable per-sample writes (default off);
2. runs `uv run pytest -m <level>` when a Python service exists;
3. runs `pnpm -r --filter "./verification/*" test:<level>` when a TS service exists;
4. stops the companion and attaches its readings to the run output;
5. exits non-zero if any run failed.

The companion degrades on a disk write failure; its successful exit is not evidence of a valid
run. Attach only this run's JSONL file and report missing, empty or corrupt evidence as
`unavailable`, never as a zero or an in-envelope measurement. A reader may skip a torn final
line with an explicit warning, never corruption before the tail.

In `mock+real` with all lab prerequisites supplied, add `verification/run.sh vl2 --run-id <id>`.
The operator command checks the approved protocol/oracle and explicit authorization, creates a
new output directory exclusively, checks deployment identity, records the actual HAL probe,
rejects unsupported device configuration, captures telemetry and raw device data, applies the
declared correction chain and writes `measurement.json` with capture SHA-256 hashes. Always stop
the device and telemetry on error; preserve partial failed evidence without overwriting it.
Test the orchestration and failure paths with a fake device API; fake results never count as
real VL-2 evidence. G2's `references/machine_evidence.md` and `measurement.schema.json` define
the capture contract and scalar interval limitation. No declared oracle means no VL-2 run.

On the target, captures are under `verification/telemetry/<run-id>/`. Each `fetch_evidence` call
returns `local_path`, a new host snapshot under `verification/telemetry/<target>/fetch-<unique>/`.
Read the selected `<run-id>/measurement.json` inside that returned directory; older remote runs
may also be present in the snapshot and are not fresh evidence. Local captures stay under
`verification/telemetry/<run-id>/`. Preserve per-run relative paths inside each record.

## Deployment identity (remote PIL or any VL-2)

S2 creates the manifest and checker for remote PIL or any planned VL-2 capture, including local
PC-to-device HIL with no remote target. Local VL-0/VL-1 alone do not need them. Local VL-2 uses
target name `local`, the host CodeAnvil version and the same expected manifest digest checks;
it needs no MCP or deployment sync. They are verification infrastructure, not delivered service
dependencies. The manifest records the clean delivered git
revision, its selected input roots, and sorted project-relative paths with SHA-256 hashes and
executable bits. Include all service code, kit tests and vectors, the checker itself, lockfiles,
root manifests and runnable entry-point/configuration files. Exclude only declared outputs and
volatile caches: `verification/telemetry/`, the manifest itself, `.venv`, `__pycache__`, `*.pyc`,
and tooling state (`.git`, `.codeanvil`, agent configuration). Never exclude executable inputs
just to make a preflight pass. Record exclusions explicitly; secrets are not deployed inputs.

`python3 verification/check_deployment.py --expected <manifest-SHA256>` uses only the stdlib,
reads the manifest and selected roots, prints the identity and exits 0 only when the manifest's
own hash equals `--expected` and every input matches. Reject missing, changed or additional files
within the selected roots, unsafe paths, and symlinks escaping the workspace. For allowed internal
symlinks record and check both the link target and the resolved input digest. Do not rewrite the
manifest, install dependencies, deploy or run tests in this preflight. Its expected digest comes
from the host `test_run.md`, not from the remote manifest it is checking.

S2 tests this checker with an altered input before delivery. G2 repeats it before and after the
recorded level commands. Any mismatch returns to S2; the verifier never calls `code_sync` to
make a changed deployment look like the approved one. Keep test outputs outside the selected
input roots or explicitly excluded, so executing the kit does not change its own baseline.

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
