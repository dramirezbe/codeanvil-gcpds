from pathlib import Path
import stat

import pytest

from vsil_hil_mcp import config, identity

MAC_A = "b8:27:eb:01:02:03"
MAC_B = "dc:a6:32:04:05:06"


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    return tmp_path


def test_mac_aliases_reuse_identity_keys_and_follow_connection_changes(home):
    first, row = identity.remember_device([MAC_A, MAC_B], "old-host", 22, "pi", "legacy_pi")
    second, changed = identity.remember_device([MAC_B], "new-host", 2222, "other-admin")
    assert second == first == "mac_b827eb010203"
    assert changed["key_identity"] == "legacy_pi"
    assert changed["mac_addresses"] == [MAC_A, MAC_B]
    assert changed["bootstrap_user"] == "other-admin"
    assert changed["endpoints"] == [{"host": "old-host", "port": 22}, {"host": "new-host", "port": 2222}]
    assert identity.local_key_identity(first) == "legacy_pi"
    assert stat.S_IMODE((identity.store_dir() / "devices.yaml").stat().st_mode) == 0o600
    assert not list(identity.store_dir().rglob("*_ed25519"))  # registry never creates keys


def test_second_pc_does_not_reuse_another_clients_private_key_mapping(home, monkeypatch, tmp_path):
    device_id, _ = identity.remember_device([MAC_A], "pi", 22, "admin", "legacy_pc1")
    monkeypatch.setenv("HOME", str(tmp_path / "second-pc"))
    assert identity.local_key_identity(device_id) == device_id
    _, row = identity.remember_device([MAC_A], "pi", 22, "admin")
    assert row["key_identity"] == device_id


def test_registry_never_replaces_established_keys(home):
    identity.remember_device([MAC_A], "pi", 22, "admin", "legacy")
    with pytest.raises(ValueError, match="refusing to replace"):
        identity.remember_device([MAC_A], "pi", 22, "admin", "other")


@pytest.mark.parametrize("raw", ["00:00:00:00:00:00", "ff:ff:ff:ff:ff:ff", "01:00:00:00:00:01", "bad", None])
def test_invalid_or_nonphysical_identity_not_enrolled(home, raw):
    with pytest.raises(ValueError):
        identity.remember_device([raw], "pi", 22, "admin")
    assert not identity.store_dir().exists()


def test_mac_format_normalization(home):
    assert identity.normalize_mac("B8-27-EB-01-02-03") == MAC_A
    assert identity.mac_device_id("B827EB010203") == "mac_b827eb010203"


def test_ambiguous_equipment_aliases_require_explicit_resolution(home):
    identity.remember_device([MAC_A], "pi", 22, "admin")
    identity.remember_device([MAC_B], "other", 22, "admin")
    with pytest.raises(ValueError, match="several equipment"):
        identity.remember_device([MAC_A, MAC_B], "pi", 22, "admin")


def test_target_key_identity_preserves_legacy_or_uses_local_mac_mapping(home):
    legacy = config.Target("old_alias", "pi", "hil", "/home/hil/ws")
    assert legacy.key_identity == "old_alias"
    device_id, _ = identity.remember_device([MAC_A], "pi", 22, "admin", "adopted_old_keys")
    target = config.Target(device_id, "pi", "codeanvil-agent", "/home/codeanvil-agent/projects/one", device_id=device_id)
    assert target.key_identity == "adopted_old_keys"


def test_public_target_metadata_has_identity_but_no_local_key_path(home):
    root = home / "project"
    (root / ".codeanvil").mkdir(parents=True)
    config.project_yaml(root).write_text("id: project-one\n")
    target = config._to_target("mac_b827eb010203", {
        "host": "pi", "user": "codeanvil-agent", "workspace": "/home/codeanvil-agent/projects/project-one",
        "device_id": "mac_b827eb010203", "mac_addresses": [MAC_A], "bootstrap_user": "admin",
        "deploy_root": "/home/codeanvil-agent/projects", "persistent_paths": ["data", "state/cache"],
    })
    config.register_target(root, target)
    assert config.load_targets(root)[target.name] == target
    text = config.project_yaml(root).read_text()
    assert "key_identity" not in text and str(identity.store_dir()) not in text


@pytest.mark.parametrize("paths", [["../outside"], ["/absolute"], ["data/*"], ["."], "state"])
def test_persistent_paths_confined_to_workspace(home, paths):
    with pytest.raises(config.ConfigError):
        config._to_target("pi", {"host": "pi", "user": "hil", "workspace": "/home/hil/ws", "persistent_paths": paths})
