#!/usr/bin/env python3
"""Download cost of env/requirements.lock on this machine.

ENVIRONMENT.md section 3 step 1 makes a disk budget a precondition of the 5D
rebuild, and finding F45 records that it had never been computed. The lock
carries a hash for every platform's file of every pin; exactly one file per pin
installs here. This script identifies that file and sums its size, using
PyPI's JSON API, which reports each file's size without downloading it.

It never guesses. Where the platform filter leaves more than one candidate the
total is reported as a range; where it leaves none the package is reported as a
failure and excluded. A narrow range is as useful as a number; a silent wrong
number is not.

The lock's hashes are used as an ASSERTION, not a filter. A lock built with
--generate-hashes already holds every file's hash for that version, so the
intersection adds nothing - but a mismatch means the lock is stale or the index
changed, which is finding F55. Both directions are reported.

Usage, from the repository root:
    python3 scripts/env/budget.py env/requirements.lock
    python3 scripts/env/budget.py env/requirements.lock --only torch,mdurl
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request

PIN_RE = re.compile(r"^(?P<name>[A-Za-z0-9._-]+)==(?P<ver>[^ \\]+)")
HASH_RE = re.compile(r"--hash=sha256:([0-9a-f]{64})")

# Architectures and platforms this machine is not. Checked before anything else.
EXCLUDE = (
    "win32", "win_amd64", "win_arm64", "macosx", "musllinux",
    "aarch64", "s390x", "ppc64", "i686", "armv7", "riscv", "loongarch",
    "android", "ios",
)


def normalise(name: str) -> str:
    """PEP 503 name normalisation, so jaraco.classes and jaraco_classes agree."""
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_lock(path: str) -> dict:
    pins: dict[str, dict] = {}
    current = None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            m = PIN_RE.match(line)
            if m:
                current = normalise(m.group("name"))
                pins[current] = {
                    "name": m.group("name"),
                    "version": m.group("ver").strip(),
                    "hashes": set(),
                }
                continue
            h = HASH_RE.search(line)
            if h and current:
                pins[current]["hashes"].add(h.group(1))
    return pins


def is_candidate(filename: str) -> bool:
    low = filename.lower()
    if not low.endswith(".whl"):
        return False
    if any(s in low for s in EXCLUDE):
        return False
    if "-none-any.whl" in low:
        return True                      # pure python, no platform tag
    if "x86_64" not in low or "manylinux" not in low:
        return False
    if "-py3-none-" in low or "-py2.py3-none-" in low:
        return True                      # pure python, platform-tagged
    if "-cp314-cp314-" in low:
        return True                      # this interpreter, not freethreaded
    m = re.search(r"-cp(\d{2,3})-abi3-", low)
    if m and int(m.group(1)) <= 314:
        return True                      # stable ABI built for 3.14 or earlier
    return False


def fetch(name: str, version: str, timeout: int = 30) -> dict:
    url = f"https://pypi.org/pypi/{name}/{version}/json"
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "fusiongap-budget/1.0"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def human(n: int) -> str:
    return f"{n / 1024 / 1024:.1f} MiB / {n / 1000 / 1000:.1f} MB"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("lock")
    ap.add_argument("--only", default="", help="comma-separated package names")
    args = ap.parse_args()

    pins = parse_lock(args.lock)
    if args.only:
        wanted = {normalise(x) for x in args.only.split(",") if x}
        pins = {k: v for k, v in pins.items() if k in wanted}
        missing = wanted - set(pins)
        if missing:
            print(f"NOT IN LOCK: {sorted(missing)}", file=sys.stderr)

    print(f"packages read from lock: {len(pins)}")
    print(f"{'package':28} {'files':>5} {'chosen size':>14}  file / note")
    print("-" * 110)

    total_min = total_max = 0
    exact = ambiguous = failed = 0
    problems: list[str] = []

    for key in sorted(pins):
        pin = pins[key]
        try:
            data = fetch(pin["name"], pin["version"])
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            failed += 1
            problems.append(f"FETCH FAILED  {key}=={pin['version']}  {exc}")
            print(f"{key:28} {'-':>5} {'FETCH FAILED':>14}  {exc}")
            continue

        files = data.get("urls", [])
        pypi_hashes = {f["digests"]["sha256"] for f in files}
        only_pypi = pypi_hashes - pin["hashes"]
        only_lock = pin["hashes"] - pypi_hashes
        if only_pypi or only_lock:
            problems.append(
                f"HASH MISMATCH {key}: {len(only_pypi)} on PyPI not in lock, "
                f"{len(only_lock)} in lock not on PyPI"
            )

        cands = [f for f in files if is_candidate(f["filename"])]
        if not cands:
            failed += 1
            names = ", ".join(f["filename"] for f in files[:4])
            problems.append(f"NO CANDIDATE  {key}=={pin['version']}  of {len(files)} files")
            print(f"{key:28} {len(files):>5} {'NO CANDIDATE':>14}  {names}")
            continue

        sizes = sorted(f["size"] for f in cands)
        total_min += sizes[0]
        total_max += sizes[-1]
        if len(cands) == 1:
            exact += 1
            print(f"{key:28} {len(files):>5} {sizes[0]:>14,}  {cands[0]['filename']}")
        else:
            ambiguous += 1
            problems.append(
                f"AMBIGUOUS     {key}: {len(cands)} candidates, "
                f"{sizes[0]:,}..{sizes[-1]:,} bytes"
            )
            print(f"{key:28} {len(files):>5} {sizes[0]:>14,}  AMBIGUOUS x{len(cands)} "
                  f"(max {sizes[-1]:,}) e.g. {cands[0]['filename']}")

    print("-" * 110)
    print(f"exact: {exact}   ambiguous: {ambiguous}   failed: {failed}")
    print(f"TOTAL MIN  {total_min:>14,} bytes   {human(total_min)}")
    print(f"TOTAL MAX  {total_max:>14,} bytes   {human(total_max)}")
    spread = total_max - total_min
    print(f"SPREAD     {spread:>14,} bytes   {human(spread)}")
    if problems:
        print("\nproblems, every one of them:")
        for p in problems:
            print(f"  {p}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
