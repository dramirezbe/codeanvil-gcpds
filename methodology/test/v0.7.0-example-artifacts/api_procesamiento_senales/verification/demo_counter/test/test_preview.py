import json
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

import pytest

from demo_counter.hal.port import RuntimeMockHAL
from demo_counter.processing.value import identity
from verification.demo_counter.drivers.base import drive
from verification.demo_counter.mock_hal.source import samples
from verification.demo_counter.stubs.identity import identity_stub


@pytest.mark.vl0
def test_golden_and_stub():
    vectors = json.loads(Path('verification/golden/values.json').read_text())
    inputs = [row['input'] for row in vectors]
    expected = [row['expected'] for row in vectors]
    assert drive(identity, inputs) == expected
    assert drive(identity_stub, inputs) == expected


@pytest.mark.vl0
def test_runtime_hal():
    hal = RuntimeMockHAL()
    assert [hal.read() for _ in range(6)] == [0, 1, 2, 0, 1, 2]


@pytest.mark.vl0
def test_entrypoint():
    with socket.socket() as reserve:
        reserve.bind(('127.0.0.1', 0))
        port = reserve.getsockname()[1]
    process = subprocess.Popen([sys.executable, '-m', 'demo_counter', '--port', str(port)],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            if process.poll() is not None:
                pytest.fail('Package entry point exited before HTTP was available')
            try:
                with urlopen(f'http://127.0.0.1:{port}/', timeout=0.2) as response:
                    assert b'Synthetic UI fixture' in response.read()
                break
            except OSError:
                time.sleep(0.05)
        else:
            pytest.fail('HTTP entry point did not start')
        values = []
        for _ in range(3):
            with urlopen(f'http://127.0.0.1:{port}/api/value', timeout=1) as response:
                values.append(json.load(response)['value'])
        assert values == [0, 1, 2]
    finally:
        if process.poll() is None:
            process.send_signal(signal.SIGINT)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            pytest.fail('Entry point did not stop cleanly')
    assert process.returncode == 0


@pytest.mark.vl1
def test_synthetic_sequence():
    observed = drive(identity, samples(300))
    assert observed == [0, 1, 2] * 100
