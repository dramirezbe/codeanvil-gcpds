# Run the FM occupancy prototype

This is a **Mock HAL preview (VL-1 ceiling)**. It does not use or validate an
RTL-SDR or Raspberry Pi. Run from this directory with Python 3.12+, `uv`, Node
and `pnpm` installed.

```bash
uv sync --frozen --no-dev
./run-demo SC-2
```

The launcher installs the locked dashboard dependencies, builds the UI, starts
the `fm_edge` package entry point and runs Vite. Open the local URL it prints
(normally <http://127.0.0.1:5173/>). The spectrum and waterfall should update,
and SC-2 should show three occupied channels. Press Ctrl-C to stop both
services.

For separate terminals, start the backend from this directory:

```bash
uv run --no-dev fm_edge --scene SC-2
```

Then start the UI from this directory in a second terminal:

```bash
pnpm install --frozen-lockfile
pnpm -C src/dashboard build
pnpm -C src/dashboard dev
```

The backend listens on WebSocket port 8765. `--scene` accepts SC-1 through
SC-6; `--updates 0` (the default) streams until stopped. `python
src/fm_edge/main.py` is not the package entry point because that path does not
put the parent package on Python's import path; use `uv run fm_edge` or
`uv run python -m fm_edge`.

Smoke evidence after the correction: `verification/fm_edge/test/test_entrypoint.py`
started the installed package and received one valid WebSocket update with
853 spectrum bins and 10 channel rows. The full Python suite passed (18
tests); the TypeScript dashboard built and its VL-0/VL-1 suites passed (6+4
tests). A manual `./run-demo SC-2` run returned HTTP 200 at Vite and a live
WebSocket message with the same shape. These are post-G2 correction checks;
the original G2 iteration 2 PASS belongs to commit `2b760da`.
