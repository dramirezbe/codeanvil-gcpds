import pytest

from vsil_hil_mcp.classifier import ALLOW, PRIVILEGED, classify

WS = "/home/codeanvil-agent/workspace"


@pytest.mark.parametrize("cmd", [
    "uname -a", "cat /etc/sudoers", "dmesg | tail -n 20", "lsusb && free -m",
    "find /proc -name status", "sha256sum -c verification/manifest.sha256",
    "vcgencmd get_throttled", "SoapySDRUtil --find", "codeanvil --version",
    "/home/codeanvil-agent/.local/bin/codeanvil --version",
    f"cd {WS} && python3 verification/check_deployment.py --expected abc",
    f"cd {WS} && uv sync --frozen", f"cd {WS} && pytest verification/",
    f"cd {WS} && verification/run.sh vl0", f"cd {WS} && ./verification/run.sh vl1",
])
def test_automatic_diagnostics_and_workspace_runners(cmd):
    assert classify(cmd, WS) == ALLOW


@pytest.mark.parametrize("cmd", [
    "sudo reboot", "rm -rf /tmp/result", "touch marker", "chmod +x verification/run.sh",
    "cat > output.txt", "cat /proc/cpuinfo >> output", "ls; rm file", "ls &",
    "ls\nuname -a", "echo $(sudo id)", "ls `id`", "cat '${HOME}'", "bash -c ls",
    "env python3 script.py", "find . -delete", "find . -exec rm {} +", "find . -fprintf out x",
    "dmesg -c", "hostname newname", "find . -fls output", "python3 verification/check_deployment.py", f"cd /tmp && pytest",
    f"cd {WS} | python3 test.py", f"cd {WS} && verification/run.sh vl2",
    f"cd {WS} && verification/run.sh vl0 extra", "vcgencmd display_power 0",
    "", "ls &&", "ls || uname -a", "cat 'unterminated", "( uname -a )",
])
def test_mutations_expansions_and_unrecognized_commands_need_trusted(cmd):
    assert classify(cmd, WS) == PRIVILEGED
