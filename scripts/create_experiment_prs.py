#!/usr/bin/env python3
"""Create independent experiment PRs with staggered CI starts."""

import argparse
import datetime
from pathlib import Path
import subprocess
import sys
import time
import uuid


def run(*args: str, cwd: Path) -> str:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(
            f"Command failed: {' '.join(args)}\n{result.stdout}{result.stderr}"
        )
    return result.stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=4, help="Number of PRs (default: 4)")
    parser.add_argument(
        "--interval", type=float, default=20, help="Seconds between PRs (default: 20)"
    )
    args = parser.parse_args()
    if args.count < 1 or not 0 <= args.interval < float("inf"):
        parser.error("count must be positive and interval must be finite and nonnegative")

    root = Path(run("git", "rev-parse", "--show-toplevel", cwd=Path(__file__).parent))

    def git(*arguments: str) -> str:
        return run("git", *arguments, cwd=root)

    def tracked_changes() -> str:
        return git("status", "--porcelain", "--untracked-files=no")

    if tracked_changes():
        raise RuntimeError("Commit or stash tracked file changes before running this script.")
    run("gh", "auth", "status", cwd=root)
    git("fetch", "origin", "main")
    git("switch", "main")
    git("merge", "--ff-only", "origin/main")
    base = git("rev-parse", "main")
    if base != git("rev-parse", "origin/main"):
        raise RuntimeError("Local main has unpublished commits; synchronize it first.")

    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S")
    batch = f"{timestamp}-{uuid.uuid4().hex[:6]}"
    previous_commit = None
    previous_open = None
    try:
        for index in range(1, args.count + 1):
            branch = f"experiment/chute-staggered-{batch}-{index}"
            git("switch", "-c", branch, base)
            filename = f"chute-experiment-{batch}-{index}.txt"
            with (root / filename).open("x") as file:
                file.write(
                    f"Chute staggered CI experiment\nBatch: {batch}\n"
                    f"PR: {index} of {args.count}\nIndependent base: {base}\n"
                )
            git("add", "--", filename)
            if previous_commit is not None:
                time.sleep(max(0, previous_commit + args.interval - time.monotonic()))
            previous_commit = time.monotonic()
            git("commit", "-m", f"Add Chute experiment {batch} ({index}/{args.count})")
            if git("rev-parse", "HEAD^") != base:
                raise RuntimeError(f"Unexpected parent commit on {branch}")
            git("push", "-u", "origin", branch)
            if previous_open is not None:
                time.sleep(max(0, previous_open + args.interval - time.monotonic()))
            previous_open = time.monotonic()
            url = run(
                "gh", "pr", "create", "--base", "main", "--head", branch,
                "--title", f"Chute experiment {batch}: staggered CI {index}/{args.count}",
                "--body",
                f"Independent experiment {index} of {args.count}, based on main commit "
                f"`{base}`.\n\nAdds a separate text file. PR openings are spaced "
                f"approximately {args.interval:g} seconds apart to observe CI progress "
                "and Chute behavior.",
                cwd=root,
            )
            print(f"[{index}/{args.count}] {url}", flush=True)
            git("switch", "main")
    finally:
        if not tracked_changes():
            git("switch", "main")
        else:
            print("Leaving the current branch in place to preserve uncommitted changes.", file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, KeyboardInterrupt) as error:
        print(f"Stopped: {error or 'interrupted'}", file=sys.stderr)
        sys.exit(1)
