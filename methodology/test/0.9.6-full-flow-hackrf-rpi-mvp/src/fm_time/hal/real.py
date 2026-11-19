"""Real NTP HAL — queries via ntplib."""
from __future__ import annotations

from fm_time.config.logger import get_logger
from fm_time.hal.port import NtpPort, NtpSample

log = get_logger(__name__)


class RealNtpPort(NtpPort):
    def query(self, server: str) -> NtpSample:
        try:
            import ntplib
            c = ntplib.NTPClient()
            resp = c.request(server, version=3, timeout=2)
            return NtpSample(
                offset_ms=resp.offset * 1000,
                delay_ms=resp.delay * 1000,
                source_id=server,
                leap=resp.leap,
            )
        except Exception as exc:
            log.debug(f"NTP query {server} failed: {exc}")
            return NtpSample(offset_ms=None, delay_ms=None, source_id=server)
