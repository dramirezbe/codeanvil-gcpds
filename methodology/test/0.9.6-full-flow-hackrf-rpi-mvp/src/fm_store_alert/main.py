"""fm_store_alert — history ring buffer, alert evaluation, history/alert sockets."""
from __future__ import annotations

import os
import signal
import socket
import time

from fm_store_alert.config.logger import get_logger
from fm_store_alert.config.paths import HISTORY_SOCK, ALERTS_SOCK
from fm_store_alert.lib.framing import send_msg, recv_msg
from fm_store_alert.output.history import HistoryStore
from fm_store_alert.output.alerts import AlertEngine

log = get_logger(__name__)

_HAL_MODE = os.environ.get("FM_HAL", "mock")


def main() -> None:
    log.info(f"fm_store_alert starting (HAL={_HAL_MODE})")

    _running = True

    def _stop(sig: int, _frame: object) -> None:
        nonlocal _running
        _running = False

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    if _HAL_MODE == "mock":
        from fm_store_alert.hal.mock import MockStoreDataPort
        port = MockStoreDataPort(default_scans=5)
    else:
        from fm_store_alert.hal.real import RealStoreDataPort
        port = RealStoreDataPort()

    history = HistoryStore()
    alerts = AlertEngine()

    log.info("fm_store_alert loop running")

    while _running:
        try:
            scan = port.next_scan_record(timeout_s=10.0)
        except StopIteration:
            log.info("mock scan sequence exhausted")
            break
        except Exception as exc:
            log.warning(f"scan receive error: {exc}")
            time.sleep(1.0)
            continue

        history.ingest(scan)
        cal_state = scan.get("calibration_state", "unavailable")
        sync_state = scan.get("scan_start_sync_state", "unsynced")
        utc_us = scan.get("scan_start_utc_us", int(time.time() * 1_000_000))

        events = alerts.evaluate(
            channels=scan.get("channels", []),
            cal_state=cal_state,
            sync_state=sync_state,
            utc_us=utc_us,
        )
        for evt in events:
            log.info(f"alert {evt.state}: {evt.rule} ch={evt.channel} {evt.reason}")

    log.info("fm_store_alert stopped")
