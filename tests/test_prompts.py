"""Tests for the interactive create prompts and folder-name derivation."""

from pathlib import Path

import pytest

from codeanvil.CLI import prompts


class _FakeTTY:
    def isatty(self) -> bool:
        return True


class _FakePipe:
    def isatty(self) -> bool:
        return False


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("My SDR Lab", "my_sdr_lab"),
        ("hello-world", "hello_world"),
        ("  spaces  ", "spaces"),
        ("UPPER", "upper"),
        ("foo__bar", "foo_bar"),
        ("Lab 2 -- final", "lab_2_final"),
        ("already_snake", "already_snake"),
    ],
)
def test_to_folder_name(raw, expected):
    assert prompts.to_folder_name(raw) == expected


@pytest.mark.parametrize("raw", ["", "   ", "***", "!!!"])
def test_to_folder_name_rejects_unusable_names(raw):
    with pytest.raises(ValueError):
        prompts.to_folder_name(raw)


def _patch_prompts(monkeypatch, *, project=None, folder=None, confirm=True):
    """Patch beaupy so `interactive_create` runs headless.

    `folder=None` accepts the derived default (returns `initial_value`).
    """
    seen = {}

    def fake_prompt(text, **kwargs):
        seen[text] = kwargs
        if text == "Project name":
            return project
        return kwargs.get("initial_value") if folder is None else folder

    monkeypatch.setattr(prompts.sys, "stdin", _FakeTTY())
    monkeypatch.setattr(prompts.beaupy, "prompt", fake_prompt)
    monkeypatch.setattr(prompts.beaupy, "confirm", lambda *args, **kwargs: confirm)
    return seen


def test_interactive_create_accepts_derived_folder(monkeypatch):
    seen = _patch_prompts(monkeypatch, project="My SDR Lab")

    assert prompts.interactive_create(Path("/tmp/workspace")) == ("My SDR Lab", "my_sdr_lab")
    assert seen["Folder name"]["initial_value"] == "my_sdr_lab"


def test_interactive_create_accepts_custom_folder(monkeypatch):
    _patch_prompts(monkeypatch, project="My SDR Lab", folder="  custom_dir  ")

    assert prompts.interactive_create(Path("/tmp")) == ("My SDR Lab", "custom_dir")


def test_interactive_create_confirm_no_cancels(monkeypatch):
    _patch_prompts(monkeypatch, project="My SDR Lab", confirm=False)

    assert prompts.interactive_create(Path("/tmp")) is None


def test_interactive_create_keyboard_interrupt_cancels(monkeypatch):
    monkeypatch.setattr(prompts.sys, "stdin", _FakeTTY())

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(prompts.beaupy, "prompt", interrupt)

    assert prompts.interactive_create(Path("/tmp")) is None


def test_interactive_create_abort_cancels(monkeypatch):
    class _FakeKey:
        key = "ctrl-c"
        key_codes = (3,)
        is_printable = False

    monkeypatch.setattr(prompts.sys, "stdin", _FakeTTY())

    def abort(*args, **kwargs):
        raise prompts.beaupy.Abort(_FakeKey())

    monkeypatch.setattr(prompts.beaupy, "prompt", abort)

    assert prompts.interactive_create(Path("/tmp")) is None


def test_interactive_create_requires_a_tty(monkeypatch):
    monkeypatch.setattr(prompts.sys, "stdin", _FakePipe())

    with pytest.raises(prompts.NotATTYError, match="--name"):
        prompts.interactive_create(Path("/tmp"))


def test_interactive_create_retries_unusable_project_name(monkeypatch):
    names = iter(["***", "Real Name"])

    monkeypatch.setattr(prompts.sys, "stdin", _FakeTTY())
    monkeypatch.setattr(
        prompts.beaupy,
        "prompt",
        lambda text, **kwargs: next(names) if text == "Project name" else kwargs["initial_value"],
    )
    monkeypatch.setattr(prompts.beaupy, "confirm", lambda *a, **k: True)

    assert prompts.interactive_create(Path("/tmp")) == ("Real Name", "real_name")


# --- prompt order, summary, and guard behaviour (S4, S11) -------------------

def test_prompt_order_and_confirmation_summary(monkeypatch, capsys):
    events = []

    def fake_prompt(text, **kwargs):
        events.append((text, kwargs.get("initial_value")))
        return "My SDR Lab" if text == "Project name" else kwargs["initial_value"]

    def fake_confirm(question, **kwargs):
        events.append((question, None))
        return True

    monkeypatch.setattr(prompts.sys, "stdin", _FakeTTY())
    monkeypatch.setattr(prompts.beaupy, "prompt", fake_prompt)
    monkeypatch.setattr(prompts.beaupy, "confirm", fake_confirm)

    assert prompts.interactive_create(Path("/tmp/ws")) == ("My SDR Lab", "my_sdr_lab")

    assert [event[0] for event in events][:2] == ["Project name", "Folder name"]
    assert events[1][1] == "my_sdr_lab"  # derived default shown in the folder prompt
    assert "Create project" in events[2][0]

    out = capsys.readouterr().out
    assert "CodeAnvil — create project" in out
    assert "Project: My SDR Lab" in out
    assert "Folder:  my_sdr_lab" in out


def test_ctrl_c_at_confirm_cancels(monkeypatch):
    monkeypatch.setattr(prompts.sys, "stdin", _FakeTTY())
    monkeypatch.setattr(
        prompts.beaupy,
        "prompt",
        lambda text, **kwargs: "My SDR Lab" if text == "Project name" else kwargs["initial_value"],
    )

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(prompts.beaupy, "confirm", interrupt)

    assert prompts.interactive_create(Path("/tmp")) is None


def test_non_tty_does_not_attempt_prompts(monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("prompt attempted without a TTY")

    monkeypatch.setattr(prompts.sys, "stdin", _FakePipe())
    monkeypatch.setattr(prompts.beaupy, "prompt", boom)
    monkeypatch.setattr(prompts.beaupy, "confirm", boom)

    with pytest.raises(prompts.NotATTYError, match="--name"):
        prompts.interactive_create(Path("/tmp"))
