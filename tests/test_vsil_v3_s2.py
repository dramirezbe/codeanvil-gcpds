"""T6 — S2 implements the services, builds the verification kit and ships the loggers (D2, D8, D10)."""

import logging
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from codeanvil.CLI.commands.create import cmd_create
from codeanvil.config.logger import ColoredFormatter
from codeanvil.config.time import format_timestamp
from test_create import TEMPLATES_DIR, _scaffold_skill, _skill_text, db_path  # noqa: F401  (fixture)

SKILL = "S2_implement_services"
_TIMESTAMP = re.compile(r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}\] ")
_FIXED_CREATED = datetime(2026, 11, 5, 19, 30, 15, 123000, tzinfo=timezone.utc).timestamp()


def test_s2_skill_checks_its_prerequisites():
    text = _skill_text(SKILL)

    assert "Cycle closed by RFD. Continue in cycle" in text
    assert "Cycle suspended by RFD. Run the RFD skill." in text
    assert "G1 must pass first. Run the G1 skill." in text
    assert "S1 must rework first. Run the S1 skill." in text
    assert "Based on: G1 iteration" in text
    assert 'gate: "S2"' in text


def test_s2_skill_builds_with_the_design_toolchain_and_layout():
    text = _skill_text(SKILL)

    for needle in ("Toolchain", "project_layout.md", "logger.py", "logger.ts",
                   "get_logger(__name__)", "src/<package>/", "--no-dev"):
        assert needle in text


def test_s2_skill_builds_the_kit_and_proves_the_vl0_floor():
    text = _skill_text(SKILL)

    assert "verification/run.sh vl0" in text
    assert "verification/run.sh vl1" in text
    assert "verification/golden/manifest.md" in text
    assert "VL-1" in text
    assert "S2 complete. Run the G2 skill." in text


def test_s2_skill_routes_defects_and_infeasibility():
    text = _skill_text(SKILL)

    assert "Verdict: design defect" in text
    assert "Verdict: module defect" in text
    assert "Possible infeasibility" in text
    assert "ML integration is future work. Remove design §1.5 for this round." in text
    assert "Resume" in text


def test_s2_skill_never_runs_the_rfd_skill():
    text = _skill_text(SKILL).lower()

    assert "never runs the rfd skill" in text
    for line in text.splitlines():
        if "run the rfd skill" in line:
            # Only the returned prerequisite line may name it; S2 itself never runs RFD.
            assert "cycle suspended by rfd. run the rfd skill." in line or "never" in line


def test_project_layout_names_the_d2_trees():
    path = TEMPLATES_DIR / "skills" / SKILL / "references" / "project_layout.md"
    text = path.read_text(encoding="utf-8")

    for needle in ("pyproject.toml", "uv.lock", "__main__.py", "pnpm-workspace.yaml",
                   "verification/run.sh"):
        assert needle in text


# --- references/logger.py ------------------------------------------------------


def _scaffolded_reference(tmp_path, name: str) -> Path:
    cmd_create(None, tmp_path, project_name="Proj")
    path = _scaffold_skill(tmp_path, SKILL, "references", name)
    assert path.is_file(), f"codeanvil create did not ship references/{name}"
    return path


def _service_config(tmp_path, logger_src: Path, suffix: str, runtime: str) -> Path:
    """A scratch service holding the logger as config/logger.<suffix>."""
    root = tmp_path / "svc"
    config = root / "config"
    config.mkdir(parents=True)
    shutil.copy(logger_src, config / f"logger.{suffix}")
    (config / f"runtime.{suffix}").write_text(runtime, encoding="utf-8")
    return root


_PY_DRIVER = r"""
import logging, sys
sys.path.insert(0, sys.argv[1])
from config.logger import ColoredFormatter, get_logger
record = logging.LogRecord("svc.mod", logging.INFO, "mod.py", 1, "hello world", None, None, func="func")
record.created = float(sys.argv[2])
record.msecs = 123.0
print(ColoredFormatter(use_color=sys.argv[3] == "1").format(record))
if len(sys.argv) > 4:
    def run():
        get_logger("svc.live").warning("from stderr")
    run()
"""


def _run_python_logger(root: Path, color: bool, env_extra: dict | None = None,
                       live: bool = False) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k not in ("NO_COLOR", "FORCE_COLOR")}
    env.update(env_extra or {})
    args = [sys.executable, "-I", "-c", _PY_DRIVER, str(root), str(_FIXED_CREATED), "1" if color else "0"]
    if live:
        args.append("live")
    return subprocess.run(args, capture_output=True, text=True, env=env, check=True)


def _codeanvil_line(color: bool) -> str:
    record = logging.LogRecord("svc.mod", logging.INFO, "mod.py", 1, "hello world", None, None, func="func")
    record.created = _FIXED_CREATED
    record.msecs = 123.0
    return ColoredFormatter(use_color=color).format(record)


def test_reference_logger_py_has_no_codeanvil_dependency(tmp_path, db_path):
    path = _scaffolded_reference(tmp_path, "logger.py")
    assert "codeanvil" not in path.read_text(encoding="utf-8").lower()


def test_reference_logger_py_matches_codeanvil_format(tmp_path, db_path):
    root = _service_config(tmp_path, _scaffolded_reference(tmp_path, "logger.py"), "py",
                           'TIMEZONE = "America/Bogota"\n')

    line = _run_python_logger(root, color=False).stdout.strip()

    expected_ts = format_timestamp(datetime.fromtimestamp(_FIXED_CREATED, tz=timezone.utc),
                                   tz_name="America/Bogota")
    assert line == f"[{expected_ts}] INFO svc.mod.func hello world"
    assert _TIMESTAMP.sub("", line) == _TIMESTAMP.sub("", _codeanvil_line(color=False))


def test_reference_logger_py_uses_the_same_ansi_codes(tmp_path, db_path):
    root = _service_config(tmp_path, _scaffolded_reference(tmp_path, "logger.py"), "py",
                           'TIMEZONE = "America/Bogota"\n')

    line = _run_python_logger(root, color=True).stdout.strip()
    assert _TIMESTAMP.sub("", line) == _TIMESTAMP.sub("", _codeanvil_line(color=True))

    live = _run_python_logger(root, color=True, env_extra={"FORCE_COLOR": "1"}, live=True).stderr
    assert "\033[33mWARNING\033[0m \033[2msvc.live\033[0m.run from stderr" in live
    plain = _run_python_logger(root, color=True, env_extra={"NO_COLOR": "1", "FORCE_COLOR": "1"},
                               live=True).stderr
    assert "] WARNING svc.live.run from stderr" in plain


def test_reference_logger_py_falls_back_to_utc(tmp_path, db_path):
    root = _service_config(tmp_path, _scaffolded_reference(tmp_path, "logger.py"), "py",
                           'TIMEZONE = "Not/AZone"\n')

    line = _run_python_logger(root, color=False).stdout.strip()

    expected_ts = format_timestamp(datetime.fromtimestamp(_FIXED_CREATED, tz=timezone.utc), tz_name="UTC")
    assert line.startswith(f"[{expected_ts}] ")


# --- references/logger.ts ------------------------------------------------------


_TS_DRIVER = """import { getLogger } from "./config/logger.ts";

function func(): void {
  getLogger("svc.mod").info("hello world");
  getLogger("svc.mod").warn("careful");
}
func();
"""


def _run_node_logger(root: Path, env_extra: dict) -> str:
    (root / "package.json").write_text('{"type": "module"}\n', encoding="utf-8")
    (root / "main.ts").write_text(_TS_DRIVER, encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k not in ("NO_COLOR", "FORCE_COLOR")}
    env.update(env_extra)
    result = subprocess.run(["node", "--experimental-strip-types", "--no-warnings", "main.ts"],
                            cwd=root, capture_output=True, text=True, env=env, check=True)
    return result.stderr


def test_reference_logger_ts_has_no_codeanvil_dependency(tmp_path, db_path):
    path = _scaffolded_reference(tmp_path, "logger.ts")
    assert "codeanvil" not in path.read_text(encoding="utf-8").lower()


@pytest.mark.skipif(shutil.which("node") is None, reason="Node is not installed")
def test_reference_logger_ts_matches_the_python_line(tmp_path, db_path):
    root = _service_config(tmp_path, _scaffolded_reference(tmp_path, "logger.ts"), "ts",
                           'export const TIMEZONE = "America/Bogota";\n')

    plain = _run_node_logger(root, {"NO_COLOR": "1"}).splitlines()
    assert _TIMESTAMP.match(plain[0])
    assert _TIMESTAMP.sub("", plain[0]) == "INFO svc.mod.func hello world"
    assert _TIMESTAMP.sub("", plain[1]) == "WARNING svc.mod.func careful"

    colored = _run_node_logger(root, {"FORCE_COLOR": "1"}).splitlines()
    assert _TIMESTAMP.sub("", colored[0]) == _TIMESTAMP.sub("", _codeanvil_line(color=True))
    assert _TIMESTAMP.sub("", colored[1]) == "\033[33mWARNING\033[0m \033[2msvc.mod\033[0m.func careful"


# --- review fixes (2026-11-05) ----------------------------------------------

def _layout_text() -> str:
    from codeanvil.config.paths import TEMPLATES_DIR
    path = TEMPLATES_DIR / "skills" / "S2_implement_services" / "references" / "project_layout.md"
    return path.read_text(encoding="utf-8")


def test_layout_kit_imports_do_not_collide_with_the_service_package():
    text = _layout_text()

    assert 'pythonpath = ["src", "."]' in text
    assert 'pythonpath = ["src", "verification"]' not in text
    assert "verification.<package>.mock_hal" in text


def test_layout_tsconfig_declares_the_console_types():
    text = _layout_text()

    assert '"lib"' in text and '"DOM"' in text
    assert "@types/node" in text


def test_s2_skill_backs_up_before_overwriting_the_test_run():
    text = " ".join(_skill_text("S2_implement_services").split())

    assert "codeanvil backup S2" in text
    assert "If it exits nonzero, stop and show its message; write no iteration." in text


# --- design-defect rework from the G1 impact map (2026-11-06) --------------

def test_s2_skill_uses_the_g1_impact_map_for_design_defect_rework():
    text = " ".join(_skill_text("S2_implement_services").split())

    assert "latest PASS iteration's impact map" in text
    assert "Rework, design defect" in text
    assert "revise the affected contract and its stub first" in text
    assert "Preserve every module the impact map does not name" in text


# --- pause schedule and module subagents (2026-11-06, WU-L4/L5) -------------


def _section(title: str) -> str:
    text = _skill_text(SKILL)
    start = text.index(f"## {title}")
    return " ".join(text[start:text.index("\n## ", start + 1)].split())


def test_s2_pause_schedule_offers_the_three_options_and_the_extra_pause():
    section = _section("Pause Schedule")

    assert "Per layer and module" in section
    assert "Per layer (recommended)" in section
    assert "Per service" in section
    assert "one pause after cross-service integration and before the `PATH-*` tests" in section


def test_s2_pause_schedule_asks_every_iteration_with_the_native_question_tool():
    section = _section("Pause Schedule")

    assert "`AskUserQuestion`" in section
    assert "native question tool" in section
    assert "start of **every** iteration" in section
    assert "ask the same question in chat and wait for the reply" in section
    assert "never assume or default an answer" in section


def test_s2_pause_schedule_records_checkpoints_not_verdicts():
    section = _section("Pause Schedule")

    assert "checkpoint line" in section
    assert "never as a gate verdict" in section
    for answer in ("`continue`", "`rework`", "`stop`"):
        assert answer in section
    assert "write no iteration" in section
    assert "Resume, do not restart" in section


def test_s2_module_subagents_are_optional_and_bounded():
    section = _section("Module Subagents")

    assert "S2 works without subagents" in section
    assert "one module at a time" in section
    assert "unit, bottom-up and sandwich tests" in section
    assert "Default concurrency is 1" in section
    assert "their files do not overlap" in section


# --- locked telemetry collector (2026-11-06, WU-L6) -------------------------


def test_s2_skill_copies_the_locked_telemetry_collector():
    text = " ".join(_skill_text(SKILL).split())

    assert "telemetry_collector.py" in text
    assert "verification/telemetry/" in text
    assert "never edit them" in text


def test_layout_names_the_locked_telemetry_collector():
    text = _layout_text()

    assert "telemetry_collector.py (locked)" in text
    assert "psutil" in text
    assert "--counters" in text
