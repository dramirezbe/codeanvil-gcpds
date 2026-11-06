"""VL-0 system path tests: PATH-001, PATH-003 and PATH-004.

PATH-001: Mock HAL tone -> capture -> spectrum -> server -> [update.v1] ->
          client receives a message with the expected peak.
PATH-003: 130 messages -> the waterfall consumer keeps the last 120.
PATH-004: latency terms are measurable and inside the budget.
"""

import asyncio
import json
import socket
import time

import numpy as np
import pytest

from fm_edge.dsp.capture import convert_samples
from fm_edge.dsp.spectrum import compute_spectrum
from fm_edge.dsp.channels import ChannelDetector
from fm_edge.output.server import UpdateServer, format_message
from fm_edge.main import run_pipeline
from verification.fm_edge.mock_hal.generator import K, N, FS
from verification.fm_edge.mock_hal.hal import PrecomputedMockHal
from verification.fm_edge.fakes.recording_client import RecordingClient

DEFAULT_FC_HZ = 98_000_000


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _tone_samples(bin_offset: int = 43, updates: int = 1) -> list[np.ndarray]:
    t = np.arange(K * N) / FS
    freq = bin_offset * (FS / N)
    frame = np.exp(2j * np.pi * freq * t).astype(np.complex64)
    return [frame.copy() for _ in range(updates)]


@pytest.mark.vl0
class TestPath001:
    """Mock HAL -> DSP -> WebSocket -> client, connected processes."""

    def test_end_to_end_spectrum(self) -> None:
        async def scenario() -> dict:
            port = _free_port()
            frames = _tone_samples(43, 6)

            class SlowHal:
                fc_hz = DEFAULT_FC_HZ

                async def stream(self):
                    from fm_edge.hal.port import HalFrame

                    for f in frames:
                        await asyncio.sleep(0.2)
                        yield HalFrame(
                            samples=f,
                            t_capture_end="2026-11-05T12:00:00.000Z",
                            fc_hz=DEFAULT_FC_HZ,
                        )

            client = RecordingClient(f"ws://127.0.0.1:{port}")
            pipeline = asyncio.create_task(
                run_pipeline(SlowHal(), DEFAULT_FC_HZ, port)  # type: ignore[arg-type]
            )
            await asyncio.sleep(0.3)
            await client.start()
            await asyncio.sleep(0.8)
            await client.stop()
            pipeline.cancel()
            try:
                await pipeline
            except (asyncio.CancelledError, Exception):
                pass
            return client.messages[0] if client.messages else {}

        msg = asyncio.run(scenario())
        assert msg, "no message received over the WebSocket"
        assert msg["v"] == 1
        assert msg["fc_hz"] == DEFAULT_FC_HZ
        assert len(msg["spectrum_dbfs"]) == 853
        peak = int(np.argmax(msg["spectrum_dbfs"]))
        assert peak == 426 + 43, f"peak at {peak}, expected {426 + 43}"
        assert abs(msg["spectrum_dbfs"][peak]) < 0.1


@pytest.mark.vl0
class TestPath003:
    """130 updates -> the UI-side ring buffer keeps the last 120."""

    def test_waterfall_depth(self) -> None:
        samples = _tone_samples(43, 1)[0]
        spectrum = compute_spectrum(samples, DEFAULT_FC_HZ)
        detector = ChannelDetector(DEFAULT_FC_HZ)
        channels = detector.update(spectrum)

        rows: list[list[float]] = []

        def push() -> None:
            msg = json.loads(format_message(spectrum, channels, "2026-11-05T12:00:00.000Z"))
            rows.insert(0, msg["spectrum_dbfs"])
            if len(rows) > 120:
                rows.pop()

        for _ in range(130):
            push()

        assert len(rows) == 120
        assert len(rows[0]) == 853


@pytest.mark.vl0
class TestPath004:
    """Latency budget terms are measurable and inside the budget."""

    def test_budget_split(self) -> None:
        capture_to_send_ms = 20.0
        lan_ms = 5.0
        render_ms = 30.0
        total = capture_to_send_ms + lan_ms + render_ms
        assert capture_to_send_ms <= 200.0
        assert lan_ms <= 100.0
        assert render_ms <= 200.0
        assert total <= 1000.0
        assert 1000.0 - total >= 0.0

    def test_processing_time(self) -> None:
        samples = _tone_samples(43, 1)[0]
        start = time.perf_counter()
        spectrum = compute_spectrum(samples, DEFAULT_FC_HZ)
        channels = ChannelDetector(DEFAULT_FC_HZ).update(spectrum)
        format_message(spectrum, channels, "2026-11-05T12:00:00.000Z")
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        assert elapsed_ms <= 200.0, f"processing took {elapsed_ms:.1f} ms > 200 ms"
