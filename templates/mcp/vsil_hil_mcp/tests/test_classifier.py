import pytest

from vsil_hil_mcp.classifier import ALLOW, PRIVILEGED, classify


@pytest.mark.parametrize("cmd", [
    "uname -a", "cat /var/lib/database/live.sqlite", "stat data.db-wal", "ls /var/lib/mysql",
    "sudo apt-get install -y rtl-sdr", "sudo -n pip install package", "uv sync --frozen",
    "python3 verification/measure.py", "pytest verification/", "verification/run.sh vl2",
    "cd /tmp && pnpm add package", "node -e 'process.exit()'", "codeanvil init",
    "echo $(date -u)", "printf result > result.txt", "echo done >> logs/run.log",
    "ls\nuname -a", "find /proc -name status", "cat '${HOME}'", "bash -c 'echo hello'",
    "echo reboot", "printf systemctl", "rm temporary.txt", "rm -- -report.txt",
])
def test_ordinary_commands_scripts_and_sudo_are_automatic(cmd):
    assert classify(cmd) == ALLOW


@pytest.mark.parametrize("cmd", [
    "systemctl status ntp", "sudo systemctl restart service", "sudo -n reboot", "shutdown -h now",
    "poweroff", "/sbin/halt", "ls && sudo -u root /bin/rm -fr /tmp/run", "rm -r -f cache",
    "rm --force --recursive cache", "rm -vR cache", "sudo env MODE=lab rm -rf /tmp/run",
    "dd if=image of=/dev/sda", "mkfs.ext4 /dev/sda", "wipefs -a /dev/sda", "shred /dev/sda",
    "blkdiscard /dev/sda", "parted /dev/sda print", "fdisk /dev/sda", "mkswap /dev/sda",
    "sqlite3 data.db 'select 1'", "psql -c 'select 1'", "mysql --version", "redis-cli GET key",
    "rm data.db", "mv data.sqlite data.old", "cp backup.sqlite live.sqlite", "truncate -s0 live.db",
    "tee data.sqlite-wal", "printf value > data.db", "echo value >> data.sqlite3-shm",
    "cat result.txt > /var/lib/database/live", "echo go; systemctl stop app", "uname\nreboot",
])
def test_explicit_destructive_operations_use_trusted(cmd):
    assert classify(cmd) == PRIVILEGED


def test_router_does_not_pretend_to_interpret_python_or_sql():
    assert classify('python3 -c "run_destructive_script()"') == ALLOW
    assert classify('bash -c "rm -rf cache"') == ALLOW
    assert classify('sqlite3 data.sqlite "select 1"') == PRIVILEGED
    assert classify("python3 measure.py", "/legacy/workspace") == ALLOW
