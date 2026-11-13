#!/usr/bin/env python3
"""IQ golden vector generator.

Usage:
    uv run verification/golden/generate.py [--scenario gv001] [--out-dir verification/golden/]
"""
from __future__ import annotations

import argparse
import pathlib
import sys

import numpy as np

SAMPLE_RATE = 10_000_000
FRAME_SIZE = 131_072
FRAMES = 39
AMPLITUDE = 0.5


def _rng(seed: int = 1) -> np.random.Generator:
    return np.random.default_rng(seed)


def _tone_iq(offset_hz: float, amplitude: float, rng: np.random.Generator) -> np.ndarray:
    n = FRAME_SIZE
    t = np.arange(n, dtype=np.float64) / SAMPLE_RATE
    sigma = amplitude / (10 ** (30.0 / 20))
    I = amplitude * np.cos(2 * np.pi * offset_hz * t) + rng.standard_normal(n) * sigma
    Q = amplitude * np.sin(2 * np.pi * offset_hz * t) + rng.standard_normal(n) * sigma
    iq = np.empty(2 * n, dtype=np.float32)
    iq[0::2] = I
    iq[1::2] = Q
    return np.clip(iq, -1.0, 1.0)


def generate_gv001(out_dir: pathlib.Path) -> None:
    rng = _rng(1)
    frames = [_tone_iq(1_000_000, AMPLITUDE, rng) for _ in range(FRAMES)]
    arr = np.array(frames, dtype=np.float32)
    np.save(out_dir / "gv001_tone.npy", arr)
    print(f"gv001: {arr.shape} → {out_dir / 'gv001_tone.npy'}")


def generate_gv003(out_dir: pathlib.Path) -> None:
    rng = _rng(1)
    sigma = AMPLITUDE / (10 ** (30.0 / 20))
    frames = [rng.standard_normal(FRAME_SIZE * 2).astype(np.float32) * sigma for _ in range(FRAMES)]
    arr = np.array(frames, dtype=np.float32)
    np.save(out_dir / "gv003_noise.npy", arr)
    print(f"gv003: {arr.shape} → {out_dir / 'gv003_noise.npy'}")


def generate_gv004(out_dir: pathlib.Path) -> None:
    rng = _rng(1)
    frames = []
    for _ in range(FRAMES):
        amp1 = 0.3 * AMPLITUDE
        amp2 = 0.03 * AMPLITUDE  # -20 dB
        sigma = amp1 / (10 ** (30.0 / 20))
        n = FRAME_SIZE
        t = np.arange(n, dtype=np.float64) / SAMPLE_RATE
        I = amp1 * np.cos(2 * np.pi * 1_000_000 * t) + amp2 * np.cos(2 * np.pi * 3_000_000 * t) + rng.standard_normal(n) * sigma
        Q = amp1 * np.sin(2 * np.pi * 1_000_000 * t) + amp2 * np.sin(2 * np.pi * 3_000_000 * t) + rng.standard_normal(n) * sigma
        iq = np.empty(2 * n, dtype=np.float32)
        iq[0::2] = I
        iq[1::2] = Q
        frames.append(np.clip(iq, -1.0, 1.0))
    arr = np.array(frames, dtype=np.float32)
    np.save(out_dir / "gv004_two_tones.npy", arr)
    print(f"gv004: {arr.shape} → {out_dir / 'gv004_two_tones.npy'}")


def generate_gv005(out_dir: pathlib.Path) -> None:
    arr = np.ones((1, FRAME_SIZE * 2), dtype=np.float32)
    np.save(out_dir / "gv005_clipped.npy", arr)
    print(f"gv005: {arr.shape} → {out_dir / 'gv005_clipped.npy'}")


def generate_gv006(out_dir: pathlib.Path) -> None:
    rng = _rng(1)
    frames = [_tone_iq(1_000_000, AMPLITUDE, rng) for _ in range(FRAMES - 1)]
    arr = np.array(frames, dtype=np.float32)
    np.save(out_dir / "gv006_dropped.npy", arr)
    print(f"gv006: {arr.shape} ({FRAMES-1} frames) → {out_dir / 'gv006_dropped.npy'}")


def main() -> None:
    p = argparse.ArgumentParser(description="Generate IQ golden vectors")
    p.add_argument("--scenario", default="all", choices=["all", "gv001", "gv003", "gv004", "gv005", "gv006"])
    p.add_argument("--out-dir", default="verification/golden", type=pathlib.Path)
    args = p.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    generators = {
        "gv001": generate_gv001,
        "gv003": generate_gv003,
        "gv004": generate_gv004,
        "gv005": generate_gv005,
        "gv006": generate_gv006,
    }

    if args.scenario == "all":
        for gen in generators.values():
            gen(args.out_dir)
    else:
        generators[args.scenario](args.out_dir)


if __name__ == "__main__":
    main()
