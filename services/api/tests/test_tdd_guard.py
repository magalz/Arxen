"""Soft TDD guardrail for freezing tests after a valid Red."""

from pathlib import Path

import pytest
from scripts.tdd_guard import GuardError, clear_guard, record_guard, verify_guard


def make_test_file(
    root: Path, content: str = "def test_rule():\n    assert False\n"
) -> Path:
    path = root / "tests" / "test_rule.py"
    path.parent.mkdir(parents=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_record_and_verify_unchanged_red_test(tmp_path: Path) -> None:
    test_file = make_test_file(tmp_path)
    state_file = tmp_path / ".artifacts" / "tdd-guard.json"

    record_guard(tmp_path, state_file, [test_file])

    assert verify_guard(tmp_path, state_file) == ["tests/test_rule.py"]


def test_verify_rejects_test_changed_after_red(tmp_path: Path) -> None:
    test_file = make_test_file(tmp_path)
    state_file = tmp_path / ".artifacts" / "tdd-guard.json"
    record_guard(tmp_path, state_file, [test_file])

    test_file.write_text("def test_rule():\n    assert True\n", encoding="utf-8")

    with pytest.raises(GuardError, match="changed after the recorded Red"):
        verify_guard(tmp_path, state_file)


def test_record_rejects_non_test_file(tmp_path: Path) -> None:
    source_file = tmp_path / "src" / "feature.py"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("value = 1\n", encoding="utf-8")
    state_file = tmp_path / ".artifacts" / "tdd-guard.json"

    with pytest.raises(GuardError, match="does not look like a test file"):
        record_guard(tmp_path, state_file, [source_file])


def test_clear_removes_active_guard(tmp_path: Path) -> None:
    test_file = make_test_file(tmp_path)
    state_file = tmp_path / ".artifacts" / "tdd-guard.json"
    record_guard(tmp_path, state_file, [test_file])

    clear_guard(state_file)

    assert not state_file.exists()
    assert verify_guard(tmp_path, state_file) == []
