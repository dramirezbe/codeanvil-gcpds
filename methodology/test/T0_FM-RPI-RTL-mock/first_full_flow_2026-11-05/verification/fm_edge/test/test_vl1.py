"""VL-1 scene tests for SVC-001 fm_edge.

Fed by the Mock HAL synthetic generator; each test measures the occupied
flags and occupancy against the Build Package B.3 expected result.
"""

import json

import numpy as np
import pytest

from fm_edge.dsp.capture import convert_samples
from fm_edge.dsp.spectrum import compute_spectrum
from fm_edge.dsp.channels import ChannelDetector
from verification.fm_edge.mock_hal.generator import (
    generate_update,
    scene_carriers,
    SAMPLES_PER_UPDATE,
)

DEFAULT_FC_HZ = 98_000_000
UPDATES = 120


def _run_scene(scene: str, seed: int = 1) -> list[list[bool]]:
    """Run a full 60 s scene and return the occupied flags per update."""
    carriers = scene_carriers(scene, DEFAULT_FC_HZ)
    rng = np.random.default_rng(seed)
    detector = ChannelDetector(DEFAULT_FC_HZ)
    history: list[list[bool]] = []
    for i in range(UPDATES):
        raw = generate_update(carriers, DEFAULT_FC_HZ, i, rng)
        samples = convert_samples(raw)
        spectrum = compute_spectrum(samples, DEFAULT_FC_HZ)
        result = detector.update(spectrum)
        history.append([ch.occupied for ch in result.channels])
    return history


def _occupancy(history: list[list[bool]], channel: int) -> float:
    return sum(1 for flags in history if flags[channel]) / len(history)


@pytest.mark.vl1
class TestScenes:
    """B.3 labelled scenes: expected occupancy per channel."""

    def test_sc1_noise_only(self) -> None:
        history = _run_scene("SC-1", seed=1)
        for n in range(10):
            assert _occupancy(history, n) <= 0.05, f"channel {n} above 0.05"

    def test_sc2_three_stations(self) -> None:
        history = _run_scene("SC-2", seed=1)
        for n in range(10):
            occ = _occupancy(history, n)
            if n in (1, 4, 8):
                assert occ >= 0.95, f"ON channel {n} occupancy {occ:.2f} < 0.95"
            else:
                assert occ <= 0.05, f"OFF channel {n} occupancy {occ:.2f} > 0.05"

    def test_sc3_adjacent_stations(self) -> None:
        history = _run_scene("SC-3", seed=1)
        for n in range(10):
            occ = _occupancy(history, n)
            if n in (4, 5):
                assert occ >= 0.95, f"ON channel {n} occupancy {occ:.2f} < 0.95"
            else:
                assert occ <= 0.05, f"OFF channel {n} occupancy {occ:.2f} > 0.05"

    def test_sc4_near_threshold(self) -> None:
        history = _run_scene("SC-4", seed=1)
        assert _occupancy(history, 2) >= 0.95, "n2 below 0.95"
        for n in range(10):
            if n != 2:
                assert _occupancy(history, n) <= 0.05, f"channel {n} above 0.05"

    def test_sc5_intermittent(self) -> None:
        history = _run_scene("SC-5", seed=1)
        for i in range(60):
            assert history[i][6] is True, f"n6 should be occupied at update {i + 1}"
        for i in range(60, 120):
            assert history[i][6] is False, f"n6 should be free at update {i + 1}"
        occ = _occupancy(history, 6)
        assert abs(occ - 0.50) <= 0.02, f"n6 occupancy {occ:.3f}, expected 0.50 ± 0.02"
        for n in range(10):
            if n != 6:
                assert _occupancy(history, n) <= 0.05, f"channel {n} above 0.05"

    def test_sc6_busy_slice(self) -> None:
        history = _run_scene("SC-6", seed=1)
        for n in range(10):
            occ = _occupancy(history, n)
            if n <= 7:
                assert occ >= 0.95, f"ON channel {n} occupancy {occ:.2f} < 0.95"
            else:
                assert occ <= 0.05, f"OFF channel {n} occupancy {occ:.2f} > 0.05"
