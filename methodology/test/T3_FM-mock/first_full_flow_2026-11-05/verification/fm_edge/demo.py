"""Live demo: run the real SVC-001 pipeline on the Mock HAL.

Kit-only entry point (never shipped). It streams the chosen labelled scene over
the WebSocket the dashboard listens to, and prints the channel table to the
terminal so the run is visible without a browser.

Usage:
    PYTHONPATH=.:src uv run python verification/fm_edge/demo.py --scene SC-2
    PYTHONPATH=.:src uv run python verification/fm_edge/demo.py --scene SC-5 --fast
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone

import numpy as np

from fm_edge.config.logger import get_logger
from fm_edge.dsp.capture import convert_samples
from fm_edge.dsp.channels import ChannelDetector
from fm_edge.dsp.spectrum import compute_spectrum
from fm_edge.hal.port import HalFrame
from fm_edge.main import DEFAULT_FC_HZ, DEFAULT_PORT, run_pipeline
from verification.fm_edge.mock_hal.generator import generate_update, scene_carriers

log = get_logger(__name__)


class DemoHal:
    """Mock HAL that paces updates and prints the channel table as it goes."""

    def __init__(
        self,
        scene: str,
        fc_hz: int = DEFAULT_FC_HZ,
        seed: int = 1,
        updates: int = 120,
        period_s: float = 0.5,
    ) -> None:
        self.fc_hz = fc_hz
        self.carriers = scene_carriers(scene, fc_hz)
        self.scene = scene
        self.seed = seed
        self.updates = updates
        self.period_s = period_s

    async def stream(self):
        rng = np.random.default_rng(self.seed)
        detector = ChannelDetector(self.fc_hz)
        for i in range(self.updates):
            await asyncio.sleep(self.period_s)
            raw = generate_update(self.carriers, self.fc_hz, i, rng)
            samples = convert_samples(raw)
            spectrum = compute_spectrum(samples, self.fc_hz)
            channels = detector.update(spectrum)
            _print_table(i + 1, spectrum, channels)
            yield HalFrame(
                samples=samples,
                t_capture_end=datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                fc_hz=self.fc_hz,
            )


def _print_table(update: int, spectrum, channels) -> None:
    cells = []
    for n, ch in enumerate(channels.channels):
        mark = "ON " if ch.occupied else "off"
        cells.append(f"n{n}:{mark} {ch.power_dbfs:6.1f}dB {ch.occupancy * 100:5.1f}%")
    print(f"[{update:3d}] floor={spectrum.floor_dbfs:6.1f} " + " | ".join(cells), flush=True)


async def _run_demo(args: argparse.Namespace) -> None:
    hal = DemoHal(
        scene=args.scene,
        fc_hz=args.fc_hz,
        seed=args.seed,
        updates=args.updates,
        period_s=0.02 if args.fast else 0.5,
    )
    print(f"scene {args.scene} · fc {args.fc_hz} Hz · WebSocket ws://0.0.0.0:{args.port}")
    print("dashboard: run `pnpm dev` in src/dashboard and open http://localhost:5173")
    await run_pipeline(hal, args.fc_hz, args.port)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SVC-001 on the Mock HAL")
    parser.add_argument("--scene", default="SC-2", help="SC-1 … SC-6")
    parser.add_argument("--fc-hz", type=int, default=DEFAULT_FC_HZ)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--updates", type=int, default=120)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--fast", action="store_true", help="20 updates/s instead of 2")
    args = parser.parse_args()
    log.info("demo starting: %s", args.scene)
    asyncio.run(_run_demo(args))


if __name__ == "__main__":
    main()
