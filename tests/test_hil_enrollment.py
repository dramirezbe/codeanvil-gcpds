"""Enrollment transport fakes; never connect to hardware or install packages."""

import argparse
import grp
import os
from pathlib import Path
import pwd
import shlex
import shutil
import subprocess

import pytest

from codeanvil.CLI.commands import hil_enrollment as mod

MAC = "b8:27:eb:01:02:03"


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    return tmp_path


def _existing(key_id):
    paths = mod.identity.key_paths(key_id)
    paths["dir"].mkdir(parents=True, exist_ok=True)
    for role in ("exec", "deploy"):
        paths[role].write_text(f"private-{key_id}-{role}")
        paths[role].with_name(paths[role].name + ".pub").write_text(f"ssh-ed25519 AAAA{role}{key_id} old\n")
    return paths


def test_key_first_discovery_reuses_equipment_when_endpoint_or_admin_changes(home, monkeypatch):
    name, _ = mod.identity.remember_device([MAC], "old-host", 22, "pi", "legacy")
    _existing("legacy")
    calls = []
    def run(argv, **kwargs):
        calls.append(argv)
        return argparse.Namespace(returncode=0, stdout=MAC + "\n", stderr="")
    monkeypatch.setattr(mod.subprocess, "run", run)
    access = mod.discover_with_keys("new-host", 2222, [])
    assert access.key_identity == "legacy" and access.password is None
    assert calls[0][0] == "ssh" and "BatchMode=yes" in calls[0]
    assert calls[0][calls[0].index("-p") + 1] == "2222"
    assert calls[0][-2] == "codeanvil-agent@new-host"


def test_legacy_key_authenticated_discovery_needs_no_registry_or_password(home, monkeypatch):
    paths = _existing("old_alias")
    before = paths["exec"].read_bytes()
    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: argparse.Namespace(returncode=0, stdout=MAC, stderr=""))
    access = mod.discover_with_keys("pi", 22, [])
    assert access.key_identity == "old_alias"
    assert paths["exec"].read_bytes() == before


def test_known_equipment_mismatch_and_host_key_changes_never_fall_through(home, monkeypatch):
    mod.identity.remember_device([MAC], "pi", 22, "admin", "known")
    _existing("known")
    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: argparse.Namespace(returncode=0, stdout="dc:a6:32:00:00:01", stderr=""))
    with pytest.raises(ValueError, match="different equipment"):
        mod.discover_with_keys("pi", 22, [])
    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: argparse.Namespace(returncode=255, stdout="", stderr="Host key verification failed"))
    with pytest.raises(ValueError, match="host authentication changed"):
        mod.discover_with_keys("pi", 22, [])


def test_admin_mac_discovery_password_stays_outside_argv(home, monkeypatch):
    calls = []
    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        return argparse.Namespace(returncode=0, stdout=MAC + "\n00:00:00:00:00:00\n", stderr="")
    monkeypatch.setattr(mod.subprocess, "run", run)
    access = mod.discover_with_admin("pi", 22, "pi", "secret", home / "known_hosts")
    assert access.macs == [MAC] and "secret" not in repr(access)
    argv, kwargs = calls[0]
    assert "secret" not in " ".join(argv)
    assert kwargs["env"]["SSHPASS"] == "secret"
    assert "PubkeyAuthentication=no" in argv


def test_missing_mac_creates_no_keys(home, monkeypatch):
    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: argparse.Namespace(returncode=0, stdout="", stderr=""))
    with pytest.raises(ValueError, match="no physical interface"):
        mod.discover_with_admin("pi", 22, "pi", "secret", home / "known_hosts")
    assert not mod.identity.store_dir().exists()


def test_missing_private_key_is_never_regenerated(home, monkeypatch):
    paths = _existing("legacy")
    paths["deploy"].unlink()
    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: pytest.fail("regenerated a missing private key"))
    with pytest.raises(ValueError, match="refusing regeneration"):
        mod.ensure_keys("legacy")


def test_existing_public_private_mismatch_is_not_replaced(home, monkeypatch):
    paths = _existing("legacy")
    before = paths["deploy"].with_name(paths["deploy"].name + ".pub").read_bytes()
    monkeypatch.setattr(mod.subprocess, "run", lambda *args, **kwargs: argparse.Namespace(returncode=0, stdout="ssh-ed25519 AAAAdifferent", stderr=""))
    with pytest.raises(ValueError, match="key mismatch"):
        mod.ensure_keys("legacy")
    assert paths["deploy"].with_name(paths["deploy"].name + ".pub").read_bytes() == before


def test_post_bootstrap_verification_uses_selected_key_pin_and_mac(home, monkeypatch):
    paths = _existing("selected")
    calls = []
    def run(argv, **kwargs):
        calls.append(argv)
        return argparse.Namespace(returncode=0, stdout=MAC, stderr="")
    monkeypatch.setattr(mod.subprocess, "run", run)
    mod.verify_access("new-ip", 2222, "selected", [MAC])
    argv, = calls
    assert "BatchMode=yes" in argv
    assert f"UserKnownHostsFile={paths['known_hosts']}" in argv
    assert argv[argv.index("-i") + 1] == str(paths["exec"])
    assert argv[-2] == "codeanvil-agent@new-ip"
    with pytest.raises(ValueError, match="verification failed"):
        mod.verify_access("new-ip", 2222, "selected", ["dc:a6:32:00:00:01"])


def test_real_local_key_pair_survives_repeat_and_public_key_recovery(home):
    if shutil.which("ssh-keygen") is None:
        pytest.skip("local ssh-keygen unavailable")
    paths = mod.ensure_keys("local_test")
    private_before = {role: paths[role].read_bytes() for role in ("exec", "deploy")}
    public = paths["exec"].with_name(paths["exec"].name + ".pub")
    expected_public = public.read_text().split()[:2]
    public.unlink()
    mod.ensure_keys("local_test")
    assert public.read_text().split()[:2] == expected_public
    assert all(paths[role].read_bytes() == private_before[role] for role in ("exec", "deploy"))


def _authorized_block(home, deploy_pub, exec_pub, install_deploy):
    script = (mod.TEMPLATES_DIR / "mcp/vsil_hil_mcp/scripts/enroll_equipment.sh").read_text()
    block = script[script.index("# Preserve every other"):script.index("# Existing trusted lab policy")]
    variables = {"HIL_HOME": str(home), "HIL_AGENT_USER": pwd.getpwuid(os.getuid()).pw_name,
                 "HIL_GROUP": grp.getgrgid(os.getgid()).gr_name, "HIL_DEPLOY_ROOT": "/home/codeanvil-agent/projects",
                 "HIL_DEPLOY_PUB": deploy_pub, "HIL_EXEC_PUB": exec_pub,
                 "HIL_INSTALL_DEPLOY": install_deploy, "RRSYNC": "/usr/bin/rrsync"}
    header = "set -euo pipefail\n" + "\n".join(f"{k}={shlex.quote(v)}" for k, v in variables.items()) + "\n"
    result = subprocess.run(["bash", "-c", header + block], capture_output=True, text=True, timeout=5)
    assert result.returncode == 0, result.stderr
    return (home / ".ssh/authorized_keys").read_text().splitlines()


def test_two_controllers_append_idempotently_without_invalidating_old_keys(home):
    old = 'command="rrsync -wo /old/workspace",restrict ssh-ed25519 AAAAlegacy old'
    (home / ".ssh").mkdir()
    (home / ".ssh/authorized_keys").write_text(old + "\n")
    for _ in range(2):
        _authorized_block(home, "ssh-ed25519 AAAAdeploy1 client1", "ssh-ed25519 AAAAexec1 client1", "yes")
        lines = _authorized_block(home, "ssh-ed25519 AAAAdeploy2 client2", "ssh-ed25519 AAAAexec2 client2", "yes")
    assert lines.count(old) == 1 and len(lines) == 5
    assert sum("AAAAdeploy1 " in line for line in lines) == 1
    assert sum("AAAAdeploy2 " in line for line in lines) == 1
    assert sum("AAAAexec1 " in line for line in lines) == 1
    assert sum("AAAAexec2 " in line for line in lines) == 1


def test_legacy_adoption_keeps_deploy_confinement_byte_for_byte(home):
    old = 'command="rrsync -wo /old/workspace",restrict ssh-ed25519 AAAAlegacy old'
    (home / ".ssh").mkdir()
    (home / ".ssh/authorized_keys").write_text(old + "\n")
    lines = _authorized_block(home, "ssh-ed25519 AAAAlegacy old", "ssh-ed25519 AAAAexec old", "no")
    assert old in lines and len(lines) == 2
