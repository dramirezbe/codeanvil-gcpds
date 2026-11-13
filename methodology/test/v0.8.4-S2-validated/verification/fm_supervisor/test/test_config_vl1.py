"""VL-1 tests for SUB-006/config."""
import json
import pytest
from pathlib import Path
from fm_supervisor.decision.config import ConfigPublisher, _load_config, SiteConfig


def _write_config(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "site-config.json"
    p.write_text(json.dumps(data))
    return p


VALID = {
    "station_id": "COL-001",
    "station_name": "Bogota Test",
    "latitude_deg": 4.711,
    "longitude_deg": -74.072,
    "ntp_sources": ["pool.ntp.org"],
    "scan_start_mhz": 87.5,
    "scan_end_mhz": 108.0,
    "step_mhz": 8.0,
    "lna_gain_db": 0,
    "rf_gain_db": 0,
    "bb_gain_db": 0,
}


@pytest.mark.vl1
def test_valid_config_loads(tmp_path):
    p = _write_config(tmp_path, VALID)
    cfg, sha = _load_config(p)
    assert cfg.station_id == "COL-001"
    assert len(sha) == 64


@pytest.mark.vl1
def test_missing_field_rejected(tmp_path):
    bad = {k: v for k, v in VALID.items() if k != "ntp_sources"}
    p = _write_config(tmp_path, bad)
    with pytest.raises(ValueError, match="ntp_sources"):
        _load_config(p)


@pytest.mark.vl1
def test_bad_latitude_rejected(tmp_path):
    bad = dict(VALID, latitude_deg=91.0)
    p = _write_config(tmp_path, bad)
    with pytest.raises(ValueError, match="latitude_deg"):
        _load_config(p)


@pytest.mark.vl1
def test_empty_ntp_rejected(tmp_path):
    bad = dict(VALID, ntp_sources=[])
    p = _write_config(tmp_path, bad)
    with pytest.raises(ValueError, match="ntp_sources"):
        _load_config(p)


@pytest.mark.vl1
def test_keep_last_valid_on_reject(tmp_path, monkeypatch):
    p = _write_config(tmp_path, VALID)
    pub = ConfigPublisher(config_path=p)
    assert pub.load() is True
    old = pub.current
    assert old is not None

    # Write a broken config
    p.write_text("{bad json")
    assert pub.load() is False
    # Still the old config
    assert pub.current is old


@pytest.mark.vl1
def test_sha256_changes_on_different_content(tmp_path):
    p1 = tmp_path / "a.json"
    p2 = tmp_path / "b.json"
    cfg2 = dict(VALID, station_name="Other")
    p1.write_text(json.dumps(VALID))
    p2.write_text(json.dumps(cfg2))
    _, sha1 = _load_config(p1)
    _, sha2 = _load_config(p2)
    assert sha1 != sha2
