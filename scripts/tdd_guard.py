"""Soft guardrail that freezes Red tests during implementation."""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any


class GuardError(RuntimeError):
    """Raised when the active Red-test snapshot is violated."""


STATE_VERSION = 1


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative_test_path(root: Path, path: Path) -> str:
    resolved_root = root.resolve()
    resolved_path = path.resolve()

    try:
        relative = resolved_path.relative_to(resolved_root)
    except ValueError as error:
        raise GuardError(f"{path} is outside the guard root") from error

    if not resolved_path.is_file():
        raise GuardError(f"{relative.as_posix()} is not an existing file")

    name = relative.name.lower()
    parts = {part.lower() for part in relative.parts}
    looks_like_test = (
        "tests" in parts
        or name.startswith("test_")
        or ".test." in name
        or ".spec." in name
    )
    if not looks_like_test:
        raise GuardError(f"{relative.as_posix()} does not look like a test file")

    return relative.as_posix()


def _load_state(state_file: Path) -> dict[str, Any]:
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GuardError(f"cannot read TDD guard state: {error}") from error

    if state.get("version") != STATE_VERSION or not isinstance(
        state.get("files"), dict
    ):
        raise GuardError("unsupported or invalid TDD guard state")
    return state


def record_guard(root: Path, state_file: Path, test_files: list[Path]) -> list[str]:
    """Record immutable hashes for tests that demonstrated a valid Red."""
    if not test_files:
        raise GuardError("record requires at least one Red test file")

    recorded: dict[str, str] = {}
    for path in test_files:
        relative = _relative_test_path(root, path)
        recorded[relative] = _sha256(path.resolve())

    state_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": STATE_VERSION, "files": dict(sorted(recorded.items()))}
    state_file.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return list(payload["files"])


def verify_guard(root: Path, state_file: Path) -> list[str]:
    """Verify recorded Red tests still match their snapshot."""
    if not state_file.exists():
        return []

    state = _load_state(state_file)
    recorded_files = state["files"]
    violations: list[str] = []

    for relative, expected_hash in sorted(recorded_files.items()):
        path = root.resolve() / relative
        if not path.is_file():
            violations.append(f"{relative} is missing after the recorded Red")
            continue
        if _sha256(path) != expected_hash:
            violations.append(f"{relative} changed after the recorded Red")

    if violations:
        raise GuardError("; ".join(violations))
    return list(sorted(recorded_files))


def clear_guard(state_file: Path) -> None:
    """Clear the active guard after Green and final verification."""
    state_file.unlink(missing_ok=True)


def _guard_root() -> Path:
    configured = os.environ.get("ARXEN_TDD_GUARD_ROOT", "").strip()
    return Path(configured).resolve() if configured else Path.cwd().resolve()


def _state_file(root: Path) -> Path:
    return root / ".artifacts" / "tdd-guard.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Freeze tests after a valid TDD Red until Green is demonstrated."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    record = subparsers.add_parser("record", help="Record hashes for Red test files")
    record.add_argument("test_files", nargs="+")
    subparsers.add_parser("verify", help="Verify recorded Red tests are unchanged")
    subparsers.add_parser("clear", help="Clear the active Red-test snapshot")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = _guard_root()
    state_file = _state_file(root)

    try:
        if args.command == "record":
            files = record_guard(root, state_file, [Path(p) for p in args.test_files])
            suffix = "" if len(files) == 1 else "s"
            print(f"Recorded {len(files)} Red test{suffix}: {', '.join(files)}")
            return 0
        if args.command == "verify":
            files = verify_guard(root, state_file)
            if not files:
                print("No active Red-test guard.")
            else:
                print(f"Verified {len(files)} recorded Red test(s) unchanged.")
            return 0

        clear_guard(state_file)
        print("Cleared Red-test guard.")
        return 0
    except GuardError as error:
        print(f"TDD guard violation: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
