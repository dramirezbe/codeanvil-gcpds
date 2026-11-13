"""Mock NTP HAL — scripted sequence, no network."""
from fm_time.config.logger import get_logger
from fm_time.hal.port import NtpPort, NtpSample

log = get_logger(__name__)


class MockNtpPort(NtpPort):
    _sequence = [
        NtpSample(offset_ms=12.0, delay_ms=5.0, source_id="mock-ntp"),
        NtpSample(offset_ms=49.0, delay_ms=5.0, source_id="mock-ntp"),
        NtpSample(offset_ms=60.0, delay_ms=5.0, source_id="mock-ntp"),  # unsynced > 50 ms
        NtpSample(offset_ms=250.0, delay_ms=5.0, source_id="mock-ntp"),  # stepped
        NtpSample(offset_ms=None, delay_ms=None, source_id=""),
    ]

    def __init__(self) -> None:
        self._idx = 0

    def query(self, server: str) -> NtpSample:
        sample = self._sequence[self._idx % len(self._sequence)]
        self._idx += 1
        return sample
