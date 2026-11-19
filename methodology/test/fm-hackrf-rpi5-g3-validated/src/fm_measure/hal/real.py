"""Real HW HAL for fm_measure — HackRF One via libhackrf.

This HAL is exercised only at VL-2 on the enrolled Raspberry Pi 5 target.
VL-0 and VL-1 always use MockSdrPort from hal/mock.py.
"""
from __future__ import annotations

import ctypes
import ctypes.util
import time
from typing import Optional

from fm_measure.config.logger import get_logger
from fm_measure.hal.port import CaptureFrame, CaptureMeta, SdrConfig, SdrPort, SdrUnavailable

log = get_logger(__name__)

_HACKRF_SUCCESS = 0


class RealSdrPort(SdrPort):
    """HackRF One driver through libhackrf."""

    def __init__(self) -> None:
        self._lib = None
        self._device = None
        self._config: Optional[SdrConfig] = None

    def open(self) -> None:
        lib_name = ctypes.util.find_library("hackrf")
        if lib_name is None:
            raise SdrUnavailable("libhackrf not found on this host")
        try:
            self._lib = ctypes.CDLL(lib_name)
            rc = self._lib.hackrf_init()
            if rc != _HACKRF_SUCCESS:
                raise SdrUnavailable(f"hackrf_init failed: {rc}")
            dev = ctypes.c_void_p()
            rc = self._lib.hackrf_open(ctypes.byref(dev))
            if rc != _HACKRF_SUCCESS:
                raise SdrUnavailable(f"hackrf_open failed: {rc}")
            self._device = dev
            log.info("RealSdrPort.open succeeded")
        except OSError as exc:
            raise SdrUnavailable(str(exc)) from exc

    def info(self) -> dict:
        return {"model": "HackRF One", "serial": "real"}

    def configure(self, config: SdrConfig) -> None:
        config.validate()
        if self._device is None:
            raise SdrUnavailable("device not open")
        lib = self._lib
        dev = self._device
        lib.hackrf_set_freq(dev, ctypes.c_uint64(int(config.center_hz)))
        lib.hackrf_set_sample_rate(dev, ctypes.c_double(config.sample_rate_hz))
        lib.hackrf_set_lna_gain(dev, ctypes.c_uint32(config.lna_gain_db))
        lib.hackrf_set_vga_gain(dev, ctypes.c_uint32(config.bb_gain_db))
        lib.hackrf_set_amp_enable(dev, ctypes.c_uint8(1 if config.rf_gain_db > 0 else 0))
        self._config = config
        log.debug(f"RealSdrPort.configure center={config.center_hz:.0f} Hz")

    def read_frames(self, n: int, timeout_s: float = 2.0) -> list[CaptureFrame]:
        # Synchronous capture via libhackrf streaming callback — VL-2 only.
        raise NotImplementedError("RealSdrPort.read_frames is implemented at VL-2 only")

    def close(self) -> None:
        if self._device is not None and self._lib is not None:
            self._lib.hackrf_close(self._device)
            self._lib.hackrf_exit()
        self._device = None
        log.info("RealSdrPort.close")
