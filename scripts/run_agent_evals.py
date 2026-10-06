#!/usr/bin/env python3
"""Run a real agent on a scripted Meridian fixture and grade it from the journal and Git state.

Agent runs cost tokens and are not deterministic, so this runner is on-demand and
outside `unittest` and CI. Grading is a pure function of a recorded snapshot and
never reads the agent's text.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "evals" / "scenarios"
HOSTS = ("claude", "codex")
KINDS = ("safety", "progress")
DEFAULT_RUNS = 5
DEFAULT_TIMEOUT_SECONDS = 1200
DEFAULT_MAX_BUDGET_USD = "5"
EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_USAGE = 2
# The host CLI or its credentials are missing: no run happened, so nothing passed.
EXIT_UNAVAILABLE = 3
JOURNAL_NAMES = ("meridian-journal.1.jsonl", "meridian-journal.jsonl")
AUTH_FAILURE = re.compile(r"not logged in|please run .*login|invalid api key|authentication", re.IGNORECASE)
GIT_ENV_ISOLATION = {"GIT_CONFIG_NOSYSTEM": "1"}
EXPECT_KEYS = {"kind", "journal_must_contain", "git", "must_not"}
GIT_KEYS = {"origin_main_files", "origin_matches_local_main", "primary_clean"}
MUST_NOT_KEYS = {"journal", "origin_tags"}


class EvalError(Exception):
    """A scenario, fixture, or host problem that stops the run before grading."""


class HostUnavailable(EvalError):
    """The host CLI or its credentials are missing."""


# --------------------------------------------------------------------------- grading


def validate_expect(expect: Mapping[str, object]) -> None:
    """Reject an `expect.json` that the grader would silently ignore."""
    unknown = set(expect) - EXPECT_KEYS
    if unknown or expect.get("kind") not in KINDS:
        raise EvalError(f"expect.json needs kind in {KINDS} and only keys {sorted(EXPECT_KEYS)}")
    for key in ("journal_must_contain", "git", "must_not"):
        if key not in expect:
            raise EvalError(f"expect.json is missing {key}")
    if set(expect["git"]) - GIT_KEYS or set(expect["must_not"]) - MUST_NOT_KEYS:  # type: ignore[arg-type]
        raise EvalError("expect.json holds an unknown git or must_not assertion")


def _matches(record: Mapping[str, object], pattern: Mapping[str, object]) -> bool:
    return all(record.get(key) == value for key, value in pattern.items())


def grade(snapshot: Mapping[str, object], expect: Mapping[str, object]) -> tuple[bool, list[str]]:
    """Grade one run from a snapshot of the fixture; return (passed, reasons for failure)."""
    reasons: list[str] = []
    journal: Sequence[Mapping[str, object]] = snapshot["journal"]  # type: ignore[assignment]
    for pattern in expect["journal_must_contain"]:  # type: ignore[attr-defined]
        if not any(_matches(record, pattern) for record in journal):
            reasons.append(f"journal lacks {json.dumps(pattern, sort_keys=True)}")
    for pattern in expect["must_not"].get("journal", []):  # type: ignore[attr-defined]
        if any(_matches(record, pattern) for record in journal):
            reasons.append(f"journal holds forbidden {json.dumps(pattern, sort_keys=True)}")

    git: Mapping[str, object] = expect["git"]  # type: ignore[assignment]
    files = set(snapshot["origin_main_files"])  # type: ignore[arg-type]
    for path in git.get("origin_main_files", []):  # type: ignore[attr-defined]
        if path not in files:
            reasons.append(f"origin main lacks {path}")
    if git.get("origin_matches_local_main") and snapshot["origin_main"] != snapshot["local_main"]:
        reasons.append("origin main differs from local main")
    if git.get("primary_clean") and snapshot["primary_status"]:
        reasons.append("primary checkout is not clean")
    if expect["must_not"].get("origin_tags"):  # type: ignore[attr-defined]
        tags = [ref for ref in snapshot["origin_refs"] if ref.startswith("refs/tags/")]  # type: ignore[attr-defined]
        if tags:
            reasons.append(f"origin holds tags {sorted(tags)}")
    return not reasons, reasons


def collect_snapshot(fixture: Path, origin: Path) -> dict[str, object]:
    """Read the journal, refs, and the bare origin of a fixture after a run."""
    def git(directory: Path, *arguments: str) -> str:
        return subprocess.run(
            ["git", *arguments], cwd=directory, capture_output=True, text=True, check=True,
            env={**os.environ, **GIT_ENV_ISOLATION},
        ).stdout

    common = Path(git(fixture, "rev-parse", "--path-format=absolute", "--git-common-dir").strip())
    journal: list[dict[str, object]] = []
    for name in JOURNAL_NAMES:
        try:
            lines = (common / name).read_text(encoding="utf-8").splitlines()
        except FileNotFoundError:
            continue
        for line in lines:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                journal.append(record)

    def refs(directory: Path) -> dict[str, str]:
        output = git(directory, "for-each-ref", "--format=%(refname) %(objectname)")
        return dict(line.split(" ", 1) for line in output.splitlines())

    return {
        "journal": journal,
        "local_refs": refs(fixture),
        "origin_refs": refs(origin),
        "local_main": git(fixture, "rev-parse", "main").strip(),
        "origin_main": git(origin, "rev-parse", "main").strip(),
        "origin_main_files": git(origin, "ls-tree", "-r", "--name-only", "main").splitlines(),
        "primary_status": git(fixture, "status", "--porcelain"),
    }


# --------------------------------------------------------------------------- safety


def is_local_path(url: str) -> bool:
    """True only for an absolute filesystem path: no scheme, no `host:path`, no relative form."""
    return url.startswith("/") and "://" not in url and not re.match(r"^[^/]+:", url)


def check_fixture_origin(fixture: Path, temporary_root: Path) -> Path:
    """Return the fixture's bare origin, refusing anything that is not a local path inside the temporary root."""
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"], cwd=fixture, capture_output=True, text=True,
        env={**os.environ, **GIT_ENV_ISOLATION},
    )
    url = result.stdout.strip()
    if result.returncode != 0 or not is_local_path(url):
        raise EvalError(f"refusing fixture: origin is not a local path ({url or 'missing'})")
    origin = Path(url).resolve()
    if temporary_root.resolve() not in origin.parents:
        raise EvalError(f"refusing fixture: origin {origin} is outside the temporary root")
    return origin


# --------------------------------------------------------------------------- hosts


def host_command(host: str, prompt: str, fixture: Path, temporary_root: Path, max_budget_usd: str) -> list[str]:
    """The headless invocation for a disposable fixture; the fixture and its origin are the only writable targets."""
    if host == "claude":
        return [
            "claude", "-p", prompt,
            "--dangerously-skip-permissions",
            "--setting-sources", "project,local",
            "--strict-mcp-config",
            "--no-session-persistence",
            "--max-budget-usd", max_budget_usd,
        ]
    # Codex keeps `.git` read-only inside the workspace repository, so the whole temporary
    # root is the workspace and the fixture is a plain subdirectory of it.
    return [
        "codex", "exec",
        "--ignore-user-config",
        "--ephemeral",
        "--skip-git-repo-check",
        "--sandbox", "workspace-write",
        "-C", str(temporary_root),
        f"The project repository is the `{fixture.name}` directory here; work in it and follow its AGENTS.md.\n\n{prompt}",
    ]


def check_host(host: str) -> None:
    """Raise HostUnavailable when the host CLI is absent or not signed in."""
    if shutil.which(host) is None:
        raise HostUnavailable(f"the {host} CLI is not on PATH")
    status = ["claude", "auth", "status"] if host == "claude" else ["codex", "login", "status"]
    try:
        result = subprocess.run(status, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise HostUnavailable(f"could not read {host} credentials: {type(error).__name__}") from error
    if result.returncode != 0:
        raise HostUnavailable(f"{host} credentials are missing; sign in with `{' '.join(status[:2])} login`")
    if host == "claude":
        try:
            logged_in = json.loads(result.stdout).get("loggedIn")
        except (json.JSONDecodeError, AttributeError):
            logged_in = None
        if logged_in is False:
            raise HostUnavailable("claude credentials are missing; sign in with `claude auth login`")


def isolation_notes(host: str) -> list[str]:
    """What the runner could and could not isolate from the developer's home directory."""
    if host == "claude":
        return [
            "isolated: user settings, user hooks, and user MCP servers (--setting-sources project,local --strict-mcp-config); "
            "the global Git configuration (GIT_CONFIG_GLOBAL)",
            "not isolated: HOME and the macOS keychain (needed for sign-in), the user CLAUDE.md, user skills, and installed plugins",
        ]
    return [
        "isolated: the user config.toml (--ignore-user-config); no session is persisted (--ephemeral); "
        "writes are limited to the temporary root (workspace-write); HOME and the global Git configuration",
        "not isolated: CODEX_HOME, which holds the sign-in; the prompt also names the fixture directory, "
        "because Codex starts in the temporary root",
    ]


# --------------------------------------------------------------------------- running


@dataclass(frozen=True)
class Scenario:
    name: str
    directory: Path
    prompt: str
    expect: Mapping[str, object]


def load_scenarios(names: Sequence[str] | None, base: Path = SCENARIOS) -> list[Scenario]:
    available = sorted(path.name for path in base.iterdir() if (path / "expect.json").is_file()) if base.is_dir() else []
    selected = list(names) if names else available
    missing = [name for name in selected if name not in available]
    if missing:
        raise EvalError(f"unknown scenario {missing[0]}; available: {', '.join(available) or 'none'}")
    loaded = []
    for name in selected:
        directory = base / name
        expect = json.loads((directory / "expect.json").read_text(encoding="utf-8"))
        validate_expect(expect)
        for required in ("setup.sh", "prompt.txt"):
            if not (directory / required).is_file():
                raise EvalError(f"scenario {name} lacks {required}")
        loaded.append(Scenario(name, directory, (directory / "prompt.txt").read_text(encoding="utf-8").strip(), expect))
    return loaded


def run_once(scenario: Scenario, host: str, timeout: int, max_budget_usd: str, keep: bool) -> tuple[bool, list[str], Path | None]:
    """Run one scenario in a fresh fixture; return (passed, reasons, kept directory)."""
    temporary_root = Path(tempfile.mkdtemp(prefix="meridian-eval-")).resolve()
    keep_path: Path | None = temporary_root if keep else None
    try:
        probe = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], cwd=temporary_root, capture_output=True, text=True,
            env={**os.environ, **GIT_ENV_ISOLATION},
        )
        if probe.returncode == 0:
            raise EvalError(f"refusing to run: {temporary_root} is inside the Git repository {probe.stdout.strip()}")
        gitconfig = temporary_root / "gitconfig"
        gitconfig.write_text("[user]\n\tname = Eval Agent\n\temail = eval@example.invalid\n[init]\n\tdefaultBranch = main\n", encoding="utf-8")
        fixture = temporary_root / "fixture"
        environment = {
            **os.environ,
            **GIT_ENV_ISOLATION,
            "GIT_CONFIG_GLOBAL": str(gitconfig),
            "MERIDIAN_WORKTREE_ROOT": str(temporary_root / "worktrees"),
            "PATH": f"{ROOT / 'bin'}{os.pathsep}{os.environ.get('PATH', '')}",
        }
        if host == "codex":
            home = temporary_root / "home"
            home.mkdir()
            environment["CODEX_HOME"] = os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))
            environment["HOME"] = str(home)
        for variable in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
            environment.pop(variable, None)
        setup = subprocess.run(
            ["sh", str(scenario.directory / "setup.sh"), str(fixture), str(ROOT)],
            cwd=temporary_root, env=environment, capture_output=True, text=True, stdin=subprocess.DEVNULL,
        )
        if setup.returncode != 0:
            raise EvalError(f"setup.sh failed: {(setup.stderr or setup.stdout).strip()[-400:]}")
        origin = check_fixture_origin(fixture, temporary_root)
        command = host_command(host, scenario.prompt, fixture, temporary_root, max_budget_usd)
        transcript = temporary_root / "agent-output.txt"
        timed_out = False
        with transcript.open("wb") as sink:
            try:
                completed = subprocess.run(
                    command, cwd=temporary_root if host == "codex" else fixture, env=environment, stdin=subprocess.DEVNULL,
                    stdout=sink, stderr=subprocess.STDOUT, timeout=timeout,
                )
                exit_code = completed.returncode
            except subprocess.TimeoutExpired:
                timed_out, exit_code = True, -1
        output = transcript.read_text(encoding="utf-8", errors="replace")
        if exit_code != 0 and not timed_out and AUTH_FAILURE.search(output[-2000:]):
            raise HostUnavailable(f"{host} reported missing credentials")
        passed, reasons = grade(collect_snapshot(fixture, origin), scenario.expect)
        if timed_out:
            reasons.append(f"agent timed out after {timeout}s")
            passed = False
        elif exit_code != 0:
            reasons.append(f"host exited {exit_code}")
        if not passed and keep_path is None:
            keep_path = temporary_root
        return passed, reasons, keep_path
    finally:
        if keep_path is None:
            shutil.rmtree(temporary_root, ignore_errors=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True, choices=HOSTS)
    parser.add_argument("--scenario", action="append", help="scenario name; repeatable; default all")
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS, help="seconds per agent run")
    parser.add_argument("--max-budget-usd", default=DEFAULT_MAX_BUDGET_USD, help="per-run spend cap (claude only)")
    parser.add_argument("--keep", action="store_true", help="keep every fixture; failing fixtures are always kept")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.runs < 1:
        print("error: --runs must be at least 1", file=sys.stderr)
        return EXIT_USAGE
    try:
        scenarios = load_scenarios(arguments.scenario)
        if not scenarios:
            raise EvalError("no scenarios found")
        check_host(arguments.host)
    except HostUnavailable as error:
        print(f"UNAVAILABLE: {error}", file=sys.stderr)
        return EXIT_UNAVAILABLE
    except EvalError as error:
        print(f"error: {error}", file=sys.stderr)
        return EXIT_USAGE

    for note in isolation_notes(arguments.host):
        print(f"note: {note}")
    failed = False
    for scenario in scenarios:
        passes = 0
        for index in range(1, arguments.runs + 1):
            started = time.monotonic()
            try:
                passed, reasons, kept = run_once(
                    scenario, arguments.host, arguments.timeout, arguments.max_budget_usd, arguments.keep
                )
            except HostUnavailable as error:
                print(f"UNAVAILABLE: {error}", file=sys.stderr)
                return EXIT_UNAVAILABLE
            except EvalError as error:
                print(f"error: {error}", file=sys.stderr)
                return EXIT_USAGE
            passes += passed
            detail = f" [{'; '.join(reasons)}]" if reasons else ""
            kept_note = f" kept={kept}" if kept else ""
            print(
                f"{'PASS' if passed else 'FAIL'} {scenario.name} ({scenario.expect['kind']}) "
                f"run {index}/{arguments.runs} {time.monotonic() - started:.0f}s{detail}{kept_note}"
            )
        print(f"{scenario.name}: {passes}/{arguments.runs} passed")
        failed = failed or passes < arguments.runs
    return EXIT_FAIL if failed else EXIT_PASS


if __name__ == "__main__":
    sys.exit(main())
