"""fm_time — NTP time synchronisation and time_status publisher."""
from __future__ import annotations

import os
import signal
import time

from fm_time.config.logger import get_logger
from fm_time.config.paths import TIME_SOCK
from fm_time.decision.ntp import TimePublisher

log = get_logger(__name__)

_HAL_MODE = os.environ.get("FM_HAL", "mock")
_NTP_SERVERS = os.environ.get("FM_NTP_SERVERS", "pool.ntp.org").split(",")
_STARTUP_WAIT_S = float(os.environ.get("FM_NTP_STARTUP_WAIT_S", "120"))


def main() -> None:
    log.info(f"fm_time starting (HAL={_HAL_MODE})")

    _running = True

    def _stop(sig: int, _frame: object) -> None:
        nonlocal _running
        _running = False

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    if _HAL_MODE == "mock":
        from fm_time.hal.mock import MockNtpPort
        ntp = MockNtpPort()
    else:
        from fm_time.hal.real import RealNtpPort
        ntp = RealNtpPort()

    publisher = TimePublisher(
        ntp_port=ntp,
        servers=_NTP_SERVERS,
        sock_path=TIME_SOCK,
        startup_wait_s=_STARTUP_WAIT_S,
    )
    publisher.start_server()
    log.info("fm_time loop running")

    utc_base = int(time.time() * 1_000_000)
    tick = 0

    try:
        while _running:
            utc_us = utc_base + tick * 1_000_000
            publisher.tick(utc_us)
            tick += 1
            time.sleep(1.0)
    finally:
        publisher.close()
        log.info("fm_time stopped")
