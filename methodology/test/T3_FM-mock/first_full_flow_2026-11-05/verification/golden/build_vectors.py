"""Materialise the golden vectors and print their SHA-256 digests.

Run from the project root:  uv run python verification/golden/build_vectors.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from verification.fm_edge.mock_hal.generator import (
    K,
    N,
    FS,
    SAMPLES_PER_UPDATE,
    generate_update,
    scene_carriers,
)

HERE = Path(__file__).resolve().parent
FC_HZ = 98_000_000


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _tone(bin_offset: int) -> np.ndarray:
    t = np.arange(K * N) / FS
    freq = bin_offset * (FS / N)
    return np.exp(2j * np.pi * freq * t).astype(np.complex64)


def main() -> None:
    rows: list[tuple[str, str, str]] = []

    # GV-1: raw uint8 bytes.
    gv1 = bytes([255, 0, 127, 128])
    (HERE / "gv1.bin").write_bytes(gv1)
    rows.append(("GV-1", _digest(gv1), "gv1.bin (4 bytes)"))

    # GV-2: 64 x 1024 complex64 tone at +43 bins, amplitude 1.0, no noise.
    gv2 = _tone(43)
    gv2_bytes = gv2.tobytes()
    (HERE / "gv2.bin").write_bytes(gv2_bytes)
    rows.append(("GV-2", _digest(gv2_bytes), "gv2.bin (65536 complex64)"))

    # GV-3: the same generator with a tone at fc + 0.1 MHz (100 kHz, 42.67 bins).
    t = np.arange(K * N) / FS
    gv3 = np.exp(2j * np.pi * 100_000.0 * t).astype(np.complex64)
    gv3_bytes = gv3.tobytes()
    (HERE / "gv3.bin").write_bytes(gv3_bytes)
    rows.append(("GV-3", _digest(gv3_bytes), "gv3.bin (65536 complex64)"))

    # GV-4: SC-2 seed 1, one update, interleaved uint8.
    rng = np.random.default_rng(1)
    gv4 = generate_update(scene_carriers("SC-2", FC_HZ), FC_HZ, 0, rng)
    (HERE / "gv4.bin").write_bytes(gv4)
    rows.append(("GV-4", _digest(gv4), "gv4.bin (131072 uint8)"))

    # GV-5: one fixed Y8 message with n1 and n4 occupied.
    channels = []
    for n in range(10):
        occupied = n in (1, 4)
        channels.append(
            {
                "f_mhz": round(97.1 + 0.2 * n, 1),
                "power_dbfs": -20.0 if occupied else -60.0,
                "occupied": occupied,
                "occupancy": 1.0 if occupied else 0.0,
            }
        )
    message = {
        "v": 1,
        "t_capture_end": "2026-11-05T12:00:00.000Z",
        "fc_hz": FC_HZ,
        "bin_hz": 2343.75,
        "spectrum_dbfs": [-60.0] * 853,
        "floor_dbfs": -60.0,
        "channels": channels,
    }
    gv5 = json.dumps(message, separators=(",", ":")).encode()
    (HERE / "gv5.json").write_bytes(gv5)
    rows.append(("GV-5", _digest(gv5), "gv5.json"))

    for vid, digest, path in rows:
        print(f"| {vid} | {digest} | {path} |")


if __name__ == "__main__":
    main()
