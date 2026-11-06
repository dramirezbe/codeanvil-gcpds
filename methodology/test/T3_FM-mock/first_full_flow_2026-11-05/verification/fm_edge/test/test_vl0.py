"""VL-0 golden vector tests for SVC-001 fm_edge.

Every input is loaded from ``verification/golden/``; expected values come from
the design's §3 vectors and ``verification/golden/manifest.md``.
"""

import json
from pathlib import Path

import numpy as np
import pytest

from fm_edge.dsp.capture import convert_samples
from fm_edge.dsp.spectrum import compute_spectrum, validate_fc, SpectrumResult
from fm_edge.dsp.channels import ChannelDetector, ChannelState, ChannelResult
from fm_edge.output.server import format_message

GOLDEN = Path(__file__).resolve().parents[2] / "golden"
DEFAULT_FC_HZ = 98_000_000


def _load_vector(name: str) -> bytes:
    return (GOLDEN / name).read_bytes()


@pytest.mark.vl0
class TestGV1:
    """GV-1: uint8 bytes [255, 0, 127, 128] -> complex64."""

    def test_sample_conversion(self) -> None:
        raw = _load_vector("gv1.bin")
        assert raw == bytes([255, 0, 127, 128])
        result = convert_samples(raw)
        assert len(result) == 2
        expected = np.array(
            [1.0 - 1.0j, (127 - 127.5) / 127.5 + 1j * (128 - 127.5) / 127.5],
            dtype=np.complex128,
        )
        np.testing.assert_allclose(result, expected, atol=1e-6)


@pytest.mark.vl0
class TestGV2:
    """GV-2: pure tone at +43 bins, amplitude 1.0, no noise."""

    def test_spectrum_peak(self) -> None:
        samples = np.frombuffer(_load_vector("gv2.bin"), dtype=np.complex64)
        result = compute_spectrum(samples, DEFAULT_FC_HZ)
        assert len(result.bins_dbfs) == 853
        peak_idx = int(np.argmax(result.bins_dbfs))
        assert peak_idx == 469, f"Peak at {peak_idx}, expected 469"
        assert abs(result.bins_dbfs[peak_idx] - 0.0) < 0.1, (
            f"Peak value {result.bins_dbfs[peak_idx]:.2f} dBFS, expected 0.0 ± 0.1"
        )


@pytest.mark.vl0
class TestGV3:
    """GV-3: tone at fc + 0.1 MHz -> highest channel power is n=5."""

    def test_channel_identification(self) -> None:
        samples = np.frombuffer(_load_vector("gv3.bin"), dtype=np.complex64)
        spectrum = compute_spectrum(samples, DEFAULT_FC_HZ)
        detector = ChannelDetector(DEFAULT_FC_HZ)
        result = detector.update(spectrum)
        powers = [ch.power_dbfs for ch in result.channels]
        max_ch = int(np.argmax(powers))
        assert max_ch == 5, f"Highest power channel is {max_ch}, expected 5"


@pytest.mark.vl0
class TestGV4:
    """GV-4: SC-2 seed 1, one update -> detection flags."""

    def test_detection_flags(self) -> None:
        raw = _load_vector("gv4.bin")
        samples = convert_samples(raw)
        spectrum = compute_spectrum(samples, DEFAULT_FC_HZ)
        detector = ChannelDetector(DEFAULT_FC_HZ)
        result = detector.update(spectrum)
        flags = [ch.occupied for ch in result.channels]
        expected = [False, True, False, False, True, False, False, False, True, False]
        assert flags == expected, f"Got {flags}, expected {expected}"


@pytest.mark.vl0
class TestGV5Producer:
    """GV-5 producer side: message format matches the fixed vector."""

    def test_message_format(self) -> None:
        fixed = json.loads(_load_vector("gv5.json"))
        bins = np.array(fixed["spectrum_dbfs"], dtype=np.float64)
        spectrum = SpectrumResult(
            bins_dbfs=bins,
            floor_dbfs=fixed["floor_dbfs"],
            fc_hz=fixed["fc_hz"],
            bin_hz=fixed["bin_hz"],
        )
        detector = ChannelDetector(DEFAULT_FC_HZ)
        base = detector.update(spectrum)
        chans = list(base.channels)
        for idx, ch in enumerate(fixed["channels"]):
            chans[idx] = ChannelState(
                f_mhz=ch["f_mhz"],
                power_dbfs=ch["power_dbfs"],
                occupied=ch["occupied"],
                occupancy=ch["occupancy"],
            )
        channels = ChannelResult(channels=chans)
        msg_str = format_message(spectrum, channels, fixed["t_capture_end"])
        msg = json.loads(msg_str)

        assert msg["v"] == 1
        assert msg["fc_hz"] == fixed["fc_hz"]
        assert msg["bin_hz"] == fixed["bin_hz"]
        assert msg["t_capture_end"] == fixed["t_capture_end"]
        assert len(msg["spectrum_dbfs"]) == 853
        assert len(msg["channels"]) == 10
        assert msg["channels"][1]["occupied"] is True
        assert msg["channels"][4]["occupied"] is True
        assert msg["channels"][0]["occupied"] is False
        occupied = [c["occupied"] for c in msg["channels"]]
        assert occupied == [c["occupied"] for c in fixed["channels"]]


@pytest.mark.vl0
class TestDCValidation:
    """DC spike placement: fc validation."""

    def test_valid_fc(self) -> None:
        assert validate_fc(98_000_000) is True
        assert validate_fc(89_000_000) is True
        assert validate_fc(107_000_000) is True

    def test_invalid_fc(self) -> None:
        assert validate_fc(88_000_000) is False
        assert validate_fc(108_000_000) is False
        assert validate_fc(98_100_000) is False
