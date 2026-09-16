"""Command-line contract for the TDD Red-test guard."""

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = PROJECT_ROOT / "scripts" / "tdd_guard.py"


def run_guard(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["ARXEN_TDD_GUARD_ROOT"] = str(root)
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_records_and_verifies_red_test(tmp_path: Path) -> None:
    test_file = tmp_path / "tests" / "test_feature.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("def test_feature():\n    assert False\n", encoding="utf-8")

    recorded = run_guard(tmp_path, "record", str(test_file))
    verified = run_guard(tmp_path, "verify")

    assert recorded.returncode == 0, recorded.stderr
    assert "Recorded 1 Red test" in recorded.stdout
    assert verified.returncode == 0, verified.stderr
    assert "unchanged" in verified.stdout


def test_cli_verify_fails_after_red_test_changes(tmp_path: Path) -> None:
    test_file = tmp_path / "tests" / "test_feature.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("def test_feature():\n    assert False\n", encoding="utf-8")
    recorded = run_guard(tmp_path, "record", str(test_file))
    assert recorded.returncode == 0, recorded.stderr

    test_file.write_text("def test_feature():\n    assert True\n", encoding="utf-8")
    verified = run_guard(tmp_path, "verify")

    assert verified.returncode == 1
    assert "changed after the recorded Red" in verified.stderr
