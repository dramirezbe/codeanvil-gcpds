"""Real HackRF One receiver backed by libhackrf's asynchronous RX stream."""
from __future__ import annotations

import ctypes
import ctypes.util
import queue
import time
from typing import Optional

from fm_measure.config.logger import get_logger
from fm_measure.hal.port import CaptureFrame, SdrConfig, SdrPort, SdrUnavailable

log = get_logger(__name__)

_HACKRF_SUCCESS = 0
_FRAME_BYTES = 131_072  # 65,536 interleaved complex int8 samples


class _HackRFTransfer(ctypes.Structure):
    _fields_ = [
        ("device", ctypes.c_void_p),
        ("buffer", ctypes.POINTER(ctypes.c_uint8)),
        ("buffer_length", ctypes.c_int),
        ("valid_length", ctypes.c_int),
        ("rx_ctx", ctypes.c_void_p),
        ("tx_ctx", ctypes.c_void_p),
    ]


_SampleCallback = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(_HackRFTransfer))


class RealSdrPort(SdrPort):
    """Capture real I/Q frames from a HackRF using libhackrf callbacks."""

    def __init__(self) -> None:
        self._lib = None
        self._device: Optional[ctypes.c_void_p] = None
        self._config: Optional[SdrConfig] = None
        self._frames: queue.Queue[CaptureFrame] = queue.Queue(maxsize=128)
        self._pending = bytearray()
        self._pending_overflow = False
        self._callback_error: Optional[str] = None
        self._streaming = False
        self._dropped_frames = 0
        self._overflow_events = 0
        # Keep the ctypes trampoline alive for the entire device lifetime.
        self._callback = _SampleCallback(self._on_transfer)

    @property
    def dropped_frames(self) -> int:
        return self._dropped_frames

    @property
    def overflow_events(self) -> int:
        return self._overflow_events

    def open(self) -> None:
        lib_name = ctypes.util.find_library("hackrf")
        if lib_name is None:
            raise SdrUnavailable("libhackrf not found on this host")

        try:
            lib = ctypes.CDLL(lib_name)
            self._bind_api(lib)
            rc = lib.hackrf_init()
            self._check("hackrf_init", rc)
            device = ctypes.c_void_p()
            rc = lib.hackrf_open(ctypes.byref(device))
            if rc != _HACKRF_SUCCESS:
                lib.hackrf_exit()
                self._check("hackrf_open", rc)
            self._lib = lib
            self._device = device
            log.info("RealSdrPort opened HackRF via %s", lib_name)
        except (OSError, AttributeError) as exc:
            raise SdrUnavailable(f"could not initialize libhackrf: {exc}") from exc

    @staticmethod
    def _bind_api(lib) -> None:
        lib.hackrf_init.restype = ctypes.c_int
        lib.hackrf_exit.restype = ctypes.c_int
        lib.hackrf_open.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
        lib.hackrf_open.restype = ctypes.c_int
        lib.hackrf_close.argtypes = [ctypes.c_void_p]
        lib.hackrf_close.restype = ctypes.c_int
        for name, argtypes in {
            "hackrf_set_freq": [ctypes.c_void_p, ctypes.c_uint64],
            "hackrf_set_sample_rate": [ctypes.c_void_p, ctypes.c_double],
            "hackrf_set_lna_gain": [ctypes.c_void_p, ctypes.c_uint32],
            "hackrf_set_vga_gain": [ctypes.c_void_p, ctypes.c_uint32],
            "hackrf_set_amp_enable": [ctypes.c_void_p, ctypes.c_uint8],
            "hackrf_set_antenna_enable": [ctypes.c_void_p, ctypes.c_uint8],
            "hackrf_set_baseband_filter_bandwidth": [ctypes.c_void_p, ctypes.c_uint32],
            "hackrf_start_rx": [ctypes.c_void_p, _SampleCallback, ctypes.c_void_p],
            "hackrf_stop_rx": [ctypes.c_void_p],
        }.items():
            fn = getattr(lib, name)
            fn.argtypes = argtypes
            fn.restype = ctypes.c_int

    @staticmethod
    def _check(operation: str, rc: int) -> None:
        if rc != _HACKRF_SUCCESS:
            raise SdrUnavailable(f"{operation} failed with libhackrf status {rc}")

    def info(self) -> dict:
        return {
            "model": "HackRF One",
            "serial": "unavailable",
            "sample_rate_hz": self._config.sample_rate_hz if self._config else None,
            "streaming": self._streaming,
        }

    def configure(self, config: SdrConfig) -> None:
        config.validate()
        if self._device is None or self._lib is None:
            raise SdrUnavailable("device not open")
        if self._streaming:
            raise SdrUnavailable("cannot retune while an RX capture is running")

        lib, dev = self._lib, self._device
        calls = (
            ("hackrf_set_freq", (dev, int(config.center_hz))),
            ("hackrf_set_sample_rate", (dev, config.sample_rate_hz)),
            ("hackrf_set_baseband_filter_bandwidth", (dev, int(config.baseband_filter_hz))),
            ("hackrf_set_lna_gain", (dev, config.lna_gain_db)),
            ("hackrf_set_vga_gain", (dev, config.bb_gain_db)),
            ("hackrf_set_amp_enable", (dev, int(config.rf_gain_db > 0))),
            ("hackrf_set_antenna_enable", (dev, int(config.antenna_power))),
        )
        for name, args in calls:
            try:
                rc = getattr(lib, name)(*args)
            except AttributeError as exc:
                raise SdrUnavailable(f"libhackrf does not provide {name}") from exc
            self._check(name, rc)

        self._config = config
        log.debug("HackRF tuned to %.3f MHz at %.3f MS/s", config.center_hz / 1e6, config.sample_rate_hz / 1e6)

    def _on_transfer(self, transfer_ptr) -> int:
        """Copy libhackrf's transient buffer and split it into fixed-size frames."""
        try:
            transfer = transfer_ptr.contents
            length = int(transfer.valid_length)
            if length < 0 or length > int(transfer.buffer_length):
                raise ValueError("libhackrf returned an invalid transfer length")
            if length == 0:
                return 0
            if not transfer.buffer:
                raise ValueError("libhackrf returned an empty sample buffer")

            self._pending.extend(ctypes.string_at(transfer.buffer, length))
            if length != int(transfer.buffer_length):
                self._pending_overflow = True
                self._overflow_events += 1

            while len(self._pending) >= _FRAME_BYTES:
                raw = bytes(self._pending[:_FRAME_BYTES])
                del self._pending[:_FRAME_BYTES]
                frame = CaptureFrame(
                    samples=raw,
                    clipped=(b"\x7f" in raw or b"\x80" in raw),
                    overflow=self._pending_overflow,
                )
                self._pending_overflow = False
                try:
                    self._frames.put_nowait(frame)
                except queue.Full:
                    self._dropped_frames += 1
                    self._overflow_events += 1
                    self._pending_overflow = True
            return 0
        except Exception as exc:
            # Exceptions must never cross the C callback boundary.
            self._callback_error = str(exc)
            return -1

    def read_frames(self, n: int, timeout_s: float = 2.0) -> list[CaptureFrame]:
        if n <= 0:
            return []
        if self._device is None or self._lib is None:
            raise SdrUnavailable("device not open")
        if self._config is None:
            raise SdrUnavailable("device not configured")
        if self._streaming:
            raise SdrUnavailable("an RX capture is already running")

        while True:
            try:
                self._frames.get_nowait()
            except queue.Empty:
                break
        self._pending.clear()
        self._pending_overflow = False
        self._callback_error = None
        self._dropped_frames = 0
        self._overflow_events = 0

        rc = self._lib.hackrf_start_rx(self._device, self._callback, None)
        self._check("hackrf_start_rx", rc)
        self._streaming = True
        deadline = time.monotonic() + max(0.0, timeout_s)
        frames: list[CaptureFrame] = []
        stop_error: Optional[str] = None
        try:
            while len(frames) < n:
                if self._callback_error:
                    raise SdrUnavailable(f"HackRF receive callback failed: {self._callback_error}")
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                try:
                    frames.append(self._frames.get(timeout=min(remaining, 0.1)))
                except queue.Empty:
                    continue
        finally:
            rc = self._lib.hackrf_stop_rx(self._device)
            self._streaming = False
            if rc != _HACKRF_SUCCESS:
                stop_error = f"hackrf_stop_rx failed with libhackrf status {rc}"
            self._pending.clear()

        if stop_error:
            raise SdrUnavailable(stop_error)
        if not frames:
            reason = f": {self._callback_error}" if self._callback_error else ""
            raise SdrUnavailable(f"HackRF returned no I/Q frames before timeout{reason}")
        if len(frames) < n:
            log.warning("HackRF capture timed out after %d/%d frames", len(frames), n)
        return frames

    def close(self) -> None:
        if self._device is not None and self._lib is not None:
            if self._streaming:
                self._lib.hackrf_stop_rx(self._device)
                self._streaming = False
            rc = self._lib.hackrf_close(self._device)
            if rc != _HACKRF_SUCCESS:
                log.warning("hackrf_close returned status %d", rc)
            rc = self._lib.hackrf_exit()
            if rc != _HACKRF_SUCCESS:
                log.warning("hackrf_exit returned status %d", rc)
        self._device = None
        self._lib = None
        self._config = None
        log.info("RealSdrPort closed")
