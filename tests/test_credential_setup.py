"""MAC enrollment uses fake remote access and isolated controller key stores."""

from pathlib import Path
import subprocess

import pytest
import yaml

from codeanvil.CLI.commands import credential_setup as mod
from codeanvil.CLI.commands import hil_enrollment as enrollment

PROJECT = "019a73ea-1e23-7000-8000-000000000001"
OTHER_PROJECT = "019a73ea-1e23-7000-8000-000000000002"
MAC = "b8:27:eb:01:02:03"
WIFI = "dc:a6:32:04:05:06"
DEVICE = "mac_b827eb010203"


@pytest.fixture
def project_dir(tmp_path, monkeypatch):
    root = tmp_path / "project"
    (root / ".codeanvil").mkdir(parents=True)
    (root / ".codeanvil/project.yaml").write_text(f"id: {PROJECT}\nname: demo\n")
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.chdir(root)
    return root


def _data(root):
    return yaml.safe_load((root / ".codeanvil/project.yaml").read_text())


@pytest.fixture
def remote(project_dir, monkeypatch):
    state = {"authorized": False, "macs": [MAC, WIFI], "created": [], "bootstraps": [], "admin": []}
    def keys_access(host, port, rows):
        if not state["authorized"]:
            return None
        devices = enrollment.identity.read_devices()
        key_id = devices.get(DEVICE, {}).get("key_identity", DEVICE)
        paths = enrollment.identity.key_paths(key_id)
        if not paths["exec"].exists():
            return None
        return enrollment.Access(state["macs"], key_id, enrollment.AGENT_USER, paths["known_hosts"])
    def admin(host, port, user, password, known_hosts):
        state["admin"].append((host, port, user, password))
        known_hosts.write_text(f"{host} ssh-ed25519 public-host-key\n")
        return enrollment.Access(state["macs"], None, user, known_hosts, password)
    def keygen(argv, **kwargs):
        if argv[0] != "ssh-keygen":
            pytest.fail("unexpected real subprocess")
        if "-y" in argv:
            private = Path(argv[argv.index("-f") + 1])
            return subprocess.CompletedProcess(argv, 0, private.with_name(private.name + ".pub").read_text(), "")
        private = Path(argv[argv.index("-f") + 1])
        state["created"].append(str(private))
        private.write_text("private-client-key")
        private.with_name(private.name + ".pub").write_text(f"ssh-ed25519 AAAA{private.name} client\n")
        return subprocess.CompletedProcess(argv, 0, "", "")
    def bootstrap(access, host, port, keys, workspace, deploy_root, install_deploy, sudo_password=""):
        state["bootstraps"].append({"access": access, "workspace": workspace, "root": deploy_root, "deploy": install_deploy})
        state["authorized"] = True
    monkeypatch.setattr(enrollment, "discover_with_keys", keys_access)
    monkeypatch.setattr(enrollment, "discover_with_admin", admin)
    monkeypatch.setattr(enrollment.subprocess, "run", keygen)
    monkeypatch.setattr(enrollment, "bootstrap", bootstrap)
    monkeypatch.setattr(enrollment, "verify_access", lambda *args: None)
    return state


def test_first_enrollment_registers_public_mac_uuid_workspace(project_dir, remote):
    mod.cmd_credential_setup("pi", "raspberry.local", password="secret", port=2222)
    row = _data(project_dir)["targets"][0]
    assert row["device_id"] == row["name"] == DEVICE
    assert row["mac_addresses"] == [MAC, WIFI] and row["bootstrap_user"] == "pi"
    assert row["host"] == "raspberry.local" and row["port"] == 2222
    assert row["user"] == "codeanvil-agent"
    assert row["workspace"] == f"/home/codeanvil-agent/projects/{PROJECT}"
    assert row["deploy_root"] == "/home/codeanvil-agent/projects"
    assert len(remote["created"]) == 2 and len(remote["admin"]) == 1
    assert not any(field in row for field in ("exec_key", "deploy_key", "key_identity", "known_hosts"))
    assert "secret" not in (project_dir / ".codeanvil/project.yaml").read_text()


def test_other_project_changed_ip_admin_and_known_interface_reuse_without_prompts(project_dir, remote, monkeypatch):
    mod.cmd_credential_setup("pi", "first-host", password="secret")
    first_keys = list(remote["created"])
    other = project_dir.parent / "other-project"
    (other / ".codeanvil").mkdir(parents=True)
    (other / ".codeanvil/project.yaml").write_text(f"id: {OTHER_PROJECT}\n")
    monkeypatch.chdir(other)
    remote["macs"] = [WIFI]
    monkeypatch.setattr(mod.getpass, "getpass", lambda *args: pytest.fail("repeated admin prompt"))
    mod.cmd_credential_setup("another-admin", "different-ip", port=2222)
    assert remote["created"] == first_keys and len(remote["admin"]) == 1
    row = _data(other)["targets"][0]
    assert row["device_id"] == DEVICE and row["workspace"].endswith(OTHER_PROJECT)
    assert row["bootstrap_user"] == "another-admin"
    assert remote["bootstraps"][0]["workspace"] != remote["bootstraps"][1]["workspace"]


def test_new_pc_uses_own_keys_and_preserves_shared_device_identity(project_dir, remote, monkeypatch, tmp_path):
    mod.cmd_credential_setup("pi", "pi", password="secret")
    first_private = enrollment.identity.key_paths(DEVICE)["exec"]
    first_contents = first_private.read_bytes()
    monkeypatch.setenv("HOME", str(tmp_path / "second-pc"))
    remote["macs"] = [WIFI]  # shared MAC aliases identify the same equipment
    mod.cmd_credential_setup("admin2", "pi", password="other-secret")
    second_private = enrollment.identity.key_paths(DEVICE)["exec"]
    assert second_private != first_private and first_private.read_bytes() == first_contents
    assert len(remote["created"]) == 4 and _data(project_dir)["targets"][0]["device_id"] == DEVICE
    monkeypatch.setattr(mod.getpass, "getpass", lambda *args: pytest.fail("repeated admin prompt"))
    mod.cmd_credential_setup("admin2", "new-ip")
    assert len(remote["created"]) == 4 and len(remote["admin"]) == 2


def test_adopted_legacy_key_and_workspace_remain_untouched_until_project_enrollment(project_dir, remote, monkeypatch):
    keys = enrollment.identity.key_paths("old_alias")
    keys["dir"].mkdir(parents=True)
    for role in ("exec", "deploy"):
        keys[role].write_text("old-private")
        keys[role].with_name(keys[role].name + ".pub").write_text(f"ssh-ed25519 AAAA{role} old\n")
    keys["known_hosts"].write_text("pi ssh-ed25519 public-host-key\n")
    manifest = project_dir / ".codeanvil/project.yaml"
    data = _data(project_dir)
    data["targets"] = [{"name": "old_alias", "host": "pi", "user": "codeanvil-agent", "workspace": "/old/workspace"}]
    manifest.write_text(yaml.safe_dump(data))
    monkeypatch.setattr(enrollment, "discover_with_keys", lambda *args: enrollment.Access([MAC], "old_alias", enrollment.AGENT_USER, keys["known_hosts"]))
    monkeypatch.setattr(mod.getpass, "getpass", lambda *args: pytest.fail("legacy keys require no admin"))
    mod.cmd_credential_setup("pi", "pi")
    assert not remote["created"] and not remote["bootstraps"][0]["deploy"]
    assert all(keys[role].read_text() == "old-private" for role in ("exec", "deploy"))
    row = _data(project_dir)["targets"][0]
    assert row["name"] == "old_alias" and row["device_id"] == DEVICE
    assert enrollment.identity.local_key_identity(DEVICE) == "old_alias"


def test_missing_legacy_private_key_never_falls_back_to_fresh_admin_or_regenerates(project_dir, remote, monkeypatch):
    paths = enrollment.identity.key_paths("old_alias")
    paths["dir"].mkdir(parents=True)
    paths["deploy"].write_text("old-private")
    paths["exec"].with_name(paths["exec"].name + ".pub").write_text("ssh-ed25519 AAAAexec old\n")
    paths["known_hosts"].write_text("pi ssh-ed25519 pinned-host\n")
    manifest = project_dir / ".codeanvil/project.yaml"
    data = _data(project_dir)
    data["targets"] = [{"name": "old_alias", "host": "pi", "user": "codeanvil-agent", "workspace": "/old/workspace"}]
    manifest.write_text(yaml.safe_dump(data))
    before = manifest.read_bytes()
    monkeypatch.setattr(mod.getpass, "getpass", lambda *args: pytest.fail("admin prompted for missing legacy keys"))
    with pytest.raises(SystemExit):
        mod.cmd_credential_setup("pi", "pi")
    assert not remote["admin"] and not remote["created"] and not remote["bootstraps"]
    assert manifest.read_bytes() == before and not enrollment.identity.read_devices()


def test_legacy_cloned_declaration_without_local_key_store_can_enroll_new_client(project_dir, remote):
    manifest = project_dir / ".codeanvil/project.yaml"
    data = _data(project_dir)
    data["targets"] = [{"name": "old_alias", "host": "pi", "user": "codeanvil-agent", "workspace": "/old/workspace"}]
    manifest.write_text(yaml.safe_dump(data))
    mod.cmd_credential_setup("pi", "pi", password="secret")
    assert len(remote["admin"]) == 1 and len(remote["created"]) == 2
    targets = _data(project_dir)["targets"]
    assert len(targets) == 1  # unnamed MCP resolution still has one equipment
    assert targets[0]["name"] == "old_alias" and targets[0]["device_id"] == DEVICE
    assert targets[0]["workspace"] == f"/home/codeanvil-agent/projects/{PROJECT}"


def test_multiple_legacy_rows_at_authenticated_endpoint_stop_before_bootstrap(project_dir, remote):
    manifest = project_dir / ".codeanvil/project.yaml"
    data = _data(project_dir)
    data["targets"] = [{"name": name, "host": "pi", "port": 2222, "user": "codeanvil-agent", "workspace": "/old/workspace"}
                       for name in ("old_one", "old_two")]
    manifest.write_text(yaml.safe_dump(data))
    before = manifest.read_bytes()
    with pytest.raises(SystemExit):
        mod.cmd_credential_setup("pi", "pi", password="secret", port=2222)
    assert not remote["created"] and not remote["bootstraps"]
    assert manifest.read_bytes() == before and not enrollment.identity.read_devices()


def test_registered_keys_missing_entirely_never_regenerated(project_dir, remote):
    mod.cmd_credential_setup("pi", "pi", password="secret")
    paths = enrollment.identity.key_paths(DEVICE)
    paths["exec"].unlink()
    paths["exec"].with_name(paths["exec"].name + ".pub").unlink()
    before = list(remote["created"])
    with pytest.raises(SystemExit):
        mod.cmd_credential_setup("pi", "pi", password="secret")
    assert remote["created"] == before
    assert len(remote["admin"]) == 1  # refused before any new admin connection


def test_sudo_fallback_reuses_authenticated_host_pin(project_dir, remote, monkeypatch):
    mod.cmd_credential_setup("pi", "pi", password="secret")
    expected_pin = enrollment.identity.key_paths(DEVICE)["known_hosts"]
    original_admin, original_bootstrap = enrollment.discover_with_admin, enrollment.bootstrap
    admin_pins = []
    def admin(host, port, user, password, known_hosts):
        admin_pins.append(known_hosts)
        assert known_hosts == expected_pin
        return original_admin(host, port, user, password, known_hosts)
    def bootstrap(access, *args, **kwargs):
        if access.password is None:
            raise ValueError("sudo needs administrative enrollment")
        return original_bootstrap(access, *args, **kwargs)
    monkeypatch.setattr(enrollment, "discover_with_admin", admin)
    monkeypatch.setattr(enrollment, "bootstrap", bootstrap)
    mod.cmd_credential_setup("pi", "pi", password="secret")
    assert admin_pins == [expected_pin]


def test_known_endpoint_admin_path_preserves_pin_on_auth_failure(project_dir, remote, monkeypatch):
    mod.cmd_credential_setup("pi", "pi", password="secret")
    expected_pin = enrollment.identity.key_paths(DEVICE)["known_hosts"]
    before = (project_dir / ".codeanvil/project.yaml").read_bytes()
    monkeypatch.setattr(enrollment, "discover_with_keys", lambda *args: None)
    def host_rejected(host, port, user, password, known_hosts):
        assert known_hosts == expected_pin  # SSH checks this before password authentication
        raise ValueError("SSH host key verification failed")
    monkeypatch.setattr(enrollment, "discover_with_admin", host_rejected)
    with pytest.raises(SystemExit):
        mod.cmd_credential_setup("pi", "pi", password="secret")
    assert (project_dir / ".codeanvil/project.yaml").read_bytes() == before
    assert len(remote["created"]) == 2


def test_post_bootstrap_agent_verification_failure_leaves_mappings_unchanged(project_dir, remote, monkeypatch):
    def failed(*args):
        raise ValueError("dedicated SSH verification failed")
    monkeypatch.setattr(enrollment, "verify_access", failed)
    with pytest.raises(SystemExit):
        mod.cmd_credential_setup("pi", "pi", password="secret")
    assert not enrollment.identity.read_devices()
    assert "targets" not in _data(project_dir)
    assert len(remote["created"]) == 2  # retain keys for a diagnostic retry


def test_mac_discovery_failure_does_not_generate_keys_or_register(project_dir, remote, monkeypatch):
    def fail(*args, **kwargs):
        raise ValueError("no physical interface MAC")
    monkeypatch.setattr(enrollment, "discover_with_admin", fail)
    with pytest.raises(SystemExit):
        mod.cmd_credential_setup("pi", "pi", password="secret")
    assert not remote["created"] and "targets" not in _data(project_dir)


def test_bootstrap_failure_keeps_project_unregistered_and_reuses_created_keys(project_dir, remote, monkeypatch):
    original = enrollment.bootstrap
    def fail(*args, **kwargs):
        raise ValueError("bootstrap failed")
    monkeypatch.setattr(enrollment, "bootstrap", fail)
    with pytest.raises(SystemExit):
        mod.cmd_credential_setup("pi", "pi", password="secret")
    assert len(remote["created"]) == 2 and "targets" not in _data(project_dir)
    assert not enrollment.identity.read_devices()
    monkeypatch.setattr(enrollment, "bootstrap", original)
    mod.cmd_credential_setup("pi", "pi", password="secret")
    assert len(remote["created"]) == 2 and _data(project_dir)["targets"][0]["device_id"] == DEVICE


def test_missing_project_and_invalid_uuid_stop_before_remote(project_dir, remote, monkeypatch, tmp_path):
    (project_dir / ".codeanvil/project.yaml").write_text("id: invalid\n")
    with pytest.raises(SystemExit):
        mod.cmd_credential_setup("pi", "pi", password="secret")
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        mod.cmd_credential_setup("pi", "pi", password="secret")
    assert not remote["created"] and not remote["admin"]


def test_admin_prompts_only_for_initial_enrollment(project_dir, remote, monkeypatch):
    answers = iter(["password", "different-sudo"])
    monkeypatch.setattr(mod.getpass, "getpass", lambda *args: next(answers))
    mod.cmd_credential_setup("pi", "pi")
    assert remote["admin"][0][-1] == "password"
    monkeypatch.setattr(mod.getpass, "getpass", lambda *args: pytest.fail("unexpected repeat prompt"))
    mod.cmd_credential_setup("pi", "pi")
    assert len(remote["admin"]) == 1


@pytest.mark.parametrize("kwargs", [{"port": 0}, {"port": 65536}, {"port": True}, {"os_": "windows"}, {"user": "bad user"}])
def test_bad_request_stops_before_remote_or_prompt(project_dir, remote, monkeypatch, kwargs):
    monkeypatch.setattr(mod.getpass, "getpass", lambda *args: pytest.fail("prompt before validation"))
    request = {"user": "pi", "ip": "pi", **kwargs}
    with pytest.raises(SystemExit):
        mod.cmd_credential_setup(**request)
    assert not remote["created"] and not remote["admin"]


def test_cli_has_no_target_or_workspace_alias_picker():
    from codeanvil.CLI.parser import build_parser
    parser = build_parser()
    args = parser.parse_args(["credential-setup", "-u", "pi", "-i", "raspberry.local"])
    assert not hasattr(args, "target") and not hasattr(args, "workspace")
    with pytest.raises(SystemExit):
        parser.parse_args(["credential-setup", "-u", "pi", "-i", "pi", "--target", "alias"])
