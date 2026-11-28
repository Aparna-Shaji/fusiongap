#!/usr/bin/env python3
"""scripts/maintenance/5b_adr_fixes.py - stage 5B's blocking fix pass, 2026-11-28.

Applies the thirteen findings that block a status flip, plus the six flips.
Non-blocking findings (F88, F89, F90, F92, F93, F84, F94, F95, F96, F97, F99,
F100, F101, F102, F44) and ADR-0001's owed fourth column are NOT here: they are
the second pass, a condition on opening stage 07.

GUARD, designed rather than incidental (F67). For every edit:
  - the target text must occur EXACTLY ONCE in its file
  - the replacement text must be ABSENT
  - nothing is written to disk unless all nineteen edits satisfy both
A second run fails loudly at the first edit rather than silently doing nothing.

Run from the repository root:  python3 scripts/maintenance/5b_adr_fixes.py
Exit 0 = all applied.  1 = nothing applied, with the failing edits named.
"""
import sys
from pathlib import Path

ADR = Path("docs/architecture/adr")
A1 = ADR / "ADR-0001-env-pins.md"
A2 = ADR / "ADR-0002-triton-sm75.md"
A3 = ADR / "ADR-0003-telemetry.md"
A4 = ADR / "ADR-0004-distribution.md"
A5 = ADR / "ADR-0005-ci-scope.md"
A6 = ADR / "ADR-0006-one-repo.md"

EDITS = []


def edit(finding, path, old, new):
    EDITS.append({"id": finding, "path": path, "old": old, "new": new})


# ---------------------------------------------------------------------------
# ADR-0002 - F74: a gate-03 finding cited as bare F1 (R-E namespace rule)
# ---------------------------------------------------------------------------
edit("F74", A2,
     "finding F1's fix required both and only one was applied on 2026-11-23.",
     "finding C4-F1's fix required both and only one was applied on 2026-11-23.")

# ---------------------------------------------------------------------------
# ADR-0002 - F72: a tolerance bar frozen with no derivation
# ---------------------------------------------------------------------------
edit("F72", A2,
     "For fp32 the two are identical by construction, because nothing is cast.",
     """For fp32 the two are identical by construction, because nothing is cast.

**None of the four bars carries a derivation, and that is now recorded rather than left
implicit.** The cited evidence `results/env/4J_tl_dot.txt` is seventeen lines and prints both
bars as bare numbers. The fp16 full-pipeline bar of `2.0e-02` admits a measured error of
`2.427e-04`, roughly 82x inside it, so it cannot fail on anything short of a gross defect -
which is the same objection the paragraph below raises about the bar it replaced.
`[VERIFY: how - derive all four bars at stage 17, from the unit in the last place of each dtype
and the reduction depth K = 64, before K1's and K3's tolerances inherit them under the two-bar
rule in Consequences.]` Until then these are working bars, not derived ones, and no tolerance
claim in this project rests on them.""")

# ---------------------------------------------------------------------------
# ADR-0002 - F71: a Fallback condition no finite test can establish
# ---------------------------------------------------------------------------
edit("F71", A2,
     """If no pair runs on this GPU at all, the charter's exception applies: the Triton arm is dropped
through this record, by amendment, with the failure reproduced and committed — and the
re-charter at stage 01 must address losing B2 at the same time, because the same failure takes
both.""",
     """If the pinned pair stops running on this GPU, the charter's exception becomes available - but
only through a finite test. "If no pair runs on this GPU at all" quantifies over every
torch/Triton release that exists or will exist, and no experiment establishes it, so as
originally written the charter's one escape hatch for a never-cut item was gated on an
unopenable door (F71). The decidable form: the pinned pair fails spikes 4B and 4J on this GPU,
**and** the two adjacent torch releases either side of the pin, each re-resolved with its own
declared Triton, fail the same two spikes. Five pairs, a bounded afternoon, a reproducible
negative. If that test comes back all-fail the Triton arm is dropped through this record, by
amendment, with every failure reproduced and committed - and the re-charter at stage 01 must
address losing B2 at the same time, because the same failure takes both. The branch is dormant:
a pair runs (Decision part 1), and R1 is retired on two machines.""")

# ---------------------------------------------------------------------------
# ADR-0002 - F70 (HIGH) + F29 + F73: triggers read the current environment as a
# proxy for each run's versions, and two are scoped to stages that cannot run them
# ---------------------------------------------------------------------------
edit("F70+F29+F73", A2,
     """Looked for at 5C, at 5D, and in every run's metadata thereafter.
1. `.venv/bin/python -m pip show triton` reports anything other than 3.9.0.
2. The installed torch's declared Triton requirement no longer names 3.9.
3. `TRITON_DEFAULT_FP_FUSION` is unset, or set to anything but 1, in a recorded run.
4. A Triton kernel passes under `TRITON_INTERPRET=1` and fails on the GPU, or the reverse.""",
     """Looked for at 5C, at 5D, and in every run's metadata thereafter. **Triggers 1 and 2 are
pre-run guards on the current environment; triggers 3 to 5 are read from a run's own recorded
metadata.** That distinction is load-bearing and was missing until 2026-11-28 (F70). A check
that reads the *current* environment cannot speak about a run taken weeks earlier: a historical
run compiled by a different Triton stays silent, and a later environment change fires against
runs that were valid when they were taken. Both directions fail, and they fail in opposite
ways.

1. **Pre-run guard, read before each measurement session.** `.venv/bin/python -m pip show
   triton` reports anything other than 3.9.0.
2. **Pre-run guard, read before each measurement session.** The installed torch's declared
   Triton requirement no longer names 3.9.
3. **From run metadata.** A run's own recorded Triton version is anything other than 3.9.0, or
   its recorded torch version is not the pinned pair's. This is the trigger that makes the
   Consequences claim above - that both arms share a compiler, so a difference between them is
   this project's finding rather than a version artefact - checkable after the fact. Without
   the version in run metadata that claim is unfalsifiable, which is how it stood until
   2026-11-28.
4. **From run metadata, for runs taken on or after 2026-11-23.** `TRITON_DEFAULT_FP_FUSION` is
   unset, or set to anything but 1. The scope matters twice (F29). Earlier runs - 4B and 4C
   among them - predate the pin, so an unset variable there is not evidence of drift. And in
   Triton 3.9.0 unset reads as ENABLED, arithmetically identical to 1, so an unset variable in
   a 3.9.0 run is a **recording** defect and not an arithmetic one. It becomes an arithmetic
   one at 3.10, which is the version bump this trigger exists to catch.
5. **From 5D onward, not before.** A Triton kernel passes under `TRITON_INTERPRET=1` and fails
   on the GPU, or the reverse. This cannot be looked for at 5C (F73): `TRITON_INTERPRET=1`
   imports numpy at `@jit` decoration time, and this record states twice that numpy is not
   installed. It installs at 5D (RV-36).""")

# ---------------------------------------------------------------------------
# ADR-0003 - F85 (HIGH): the power-ceiling evidence is an unreproducible file
# ---------------------------------------------------------------------------
edit("F85", A3,
     """**The enforced ceiling, measured across a load transition on 2026-11-23**
(`results/env/4K_power_under_load.txt`): 40 samples across idle, 25 s of sustained""",
     """**The enforced ceiling, measured twice. The primary evidence is 4L** -
`results/env/4L_balance.csv`, `4L_balance.txt`, `4L_high-performance.csv` and
`4L_high-performance.txt` (2026-11-24), produced by the committed instrument
`spikes/4L/sample_power.py`: 140 samples per arm, 280 in total, the ceiling reading 30.00 W on
every single sample, with zero disagreements between the two power-limit forms. That run is
reproducible from this repository. The reading below is not, and the distinction was missing
from this record until 2026-11-28 (F85).

**The earlier reading, 2026-11-23** (`results/env/4K_power_under_load.txt` - **produced by an
uncommitted command and therefore NOT regenerable, finding F32; retained because it is the only
record of the idle movement described two paragraphs below**): 40 samples across idle, 25 s of
sustained""")

# ---------------------------------------------------------------------------
# ADR-0003 - F86 (HIGH): the D-39 clause drops the under-load scoping
# ---------------------------------------------------------------------------
edit("F86", A3,
     """  - The harness records the set of distinct `enforced.power.limit` values seen in each run.
    The grader already prints that set; from stage 08 a run whose set has more than one member
    is **invalid, not adjusted**.""",
     """  - The harness records the set of distinct `enforced.power.limit` values seen **in a run's
    load window**, never across the whole capture. The scope is load-bearing, and leaving it
    out was finding F86. This record documents above that the ceiling moves between 50 W and
    30 W at idle and does not move under load; every capture contains idle windows, because
    they are the negative control that proves the load ran. A whole-capture set would therefore
    mark a capture invalid for a documented, harmless idle wobble - firing on the control
    instead of on the measurement. A **load-window** set with more than one member is
    **invalid, not adjusted**. **Enforced from 5C by `scripts/env/capture.py`**, which computes
    that set over the load window only; stage 08's harness inherits it rather than inventing
    it. `spikes/4C/grade_4c.py` prints its set over the whole capture - that is an observation
    and must not be read as this criterion.""")

# ---------------------------------------------------------------------------
# ADR-0003 - F87: the field D-39 depends on is unprotected from N/A
# ---------------------------------------------------------------------------
edit("F87a", A3,
     """   `memory.used`, `clocks_event_reasons.active`. Five of them — SM clock, memory clock,
   temperature, power draw and the event-reason flags — must never read `N/A` in a capture
   that is used.""",
     """   `memory.used`, `clocks_event_reasons.active`. **Six of them — SM clock, memory clock,
   temperature, power draw, the event-reason flags and `enforced.power.limit` — must never
   read `N/A` in a capture that is used.** The sixth was added on 2026-11-28 (F87). It is the
   field D-39 pins, the field reversal trigger 4 reads, and the field the invalidity rule in
   Consequences rests on - load-bearing in three places and protected in none. The failure is
   silent in the direction that matters: a load window reading `N/A` throughout yields a
   distinct set of exactly one member, so trigger 4 does not fire and the run reads as valid
   with no ceiling recorded at all.""")

edit("F87b", A3,
     "If any of the five required fields begins reading `N/A` under load, fall back to a spin-kernel",
     "If any of the six required fields begins reading `N/A` under load, fall back to a spin-kernel")

edit("F87c", A3,
     "1. Any of the five required fields reads `N/A` in a capture that is used.",
     "1. Any of the six required fields reads `N/A` in a capture that is used.")

# ---------------------------------------------------------------------------
# ADR-0004 - F91 (HIGH): a premise measured false on 2026-11-26
# ---------------------------------------------------------------------------
edit("F91", A4,
     """  The spike demonstrates the failure. Finding F15 makes it harder than it looks: this
  project's torch reports distribution metadata version `2.15.0`, which on a public index does
  not by itself name the CUDA build in use here, so a declared dependency on torch must reckon
  with which index resolves it.""",
     """  The spike demonstrates the failure. The index question that once made this harder was
  measured and settled on 2026-11-26, and the premise recorded here until 2026-11-28 was false
  for this project (F91): for linux x86_64, `torch==2.15.0` is published on PyPI and on
  **neither** PyTorch index, so the version string does discriminate, and D-45 pins PyPI as
  this project's sole index. There is no "which index resolves it" left to reckon with.
  Evidence: `env/requirements.in`'s header and ADR-0001's torch row. What remains hard is the
  half no index pin fixes - nothing ships pre-built, so a missing or wrong declared dependency
  is silent until import, exactly as arm 2 demonstrated.""")

# ---------------------------------------------------------------------------
# ADR-0004 - F75: a reversal trigger true of the spike and false of the package
# ---------------------------------------------------------------------------
edit("F75", A4,
     """3. A clean-environment `pip install fusiongap` followed by `import fusiongap` raises
   `ModuleNotFoundError` — the failure arm 2 reproduced on 2026-11-23.""",
     """3. A clean-environment `pip install fusiongap` followed by `import fusiongap` raises
   `ModuleNotFoundError`, where `fusiongap` is **the published wheel built by stage 15's
   packaging configuration with its declared dependencies installed**. Looked for from stage 15
   onward, and again at 27C and 31. The qualifier is the whole trigger (F75): arm 2 above was
   `fusiongap_spiked`, a 1780-byte spike declaring no dependencies at all, and it failed in
   exactly this way on 2026-11-23 - so without the qualifier this clause reads as already
   satisfied by a throwaway, and will be false of the real package. It was true of the artefact
   that demonstrated the risk and silent about the artefact it governs. The spike's failure
   stays in Evidence and Consequences, where it is the reason stage 15's "must do" exists.""")

# ---------------------------------------------------------------------------
# ADR-0001 - F98 (HIGH): the Decision section and the pin table disagree
# ---------------------------------------------------------------------------
edit("F98", A1,
     """2. **Dependency pinning.** `pip-tools >= 7.5.3`. `pip-compile --generate-hashes` produces
   `env/requirements.lock`; installation is always
   `pip install --require-hashes -r env/requirements.lock`. The 7.5.3 floor is not cosmetic
   and it is load-bearing: the stage-03 rubric did not decide this on its own - `../TECH-STACK.md`
   section 1 carries the scores and says so - so this option won on a tie-break, and the floor
   is what makes it credible. Three claims support
   the floor. None has been confirmed against this machine, and each carries its check:
   (a) that release declares Python 3.14 support
   [VERIFY at 5C: read the pip-tools changelog entry for 7.5.3 and its declared
   Requires-Python];
   (b) it is compatible with pip 26 - the installed pip is 26.3, measured 2026-11-23
   [VERIFY at 5C: `pip-compile --version` runs and resolves under that pip];
   (c) it fixes a defect where `pip-compile` dropped index-URL options while looking up
   hashes, which broke resolution for packages available only from an extra index — which is
   exactly how torch is published
   [VERIFY at 5C: the generated lock carries the index URL for the torch entry].
   If any of the three is wrong the floor is wrong, and after gate 05 that costs a dated
   amendment and a re-resolve inside stage 05's two-hour box.""",
     """2. **Dependency pinning.** `pip-tools`, pinned at **7.7.0 exactly, not a floor**.
   `pip-compile --generate-hashes` produces `env/requirements.lock`; installation is always
   `pip install --require-hashes -r env/requirements.lock`. The stage-03 rubric did not decide
   this on its own - `../TECH-STACK.md` section 1 carries the scores and says so - so this
   option won on a tie-break, and what made it credible was an open floor plus three claims.
   **All three have since been answered, and this part is restated rather than left as its
   2026-11-19 snapshot, because the pin table below was rewritten on 2026-11-26 and the two
   halves of this record then disagreed about the pin, its form and its justification (F98).**
   What the floor was, and what became of it:
   (a) *that 7.5.3 declares Python 3.14 support* - **moot**: 7.5.3 is not the pin. What 7.7.0
   declares is in the pip-tools row below.
   (b) *that it is compatible with pip 26* - **answered NO for 7.5.3.** It crashed on this
   machine's pip 26.3 before any network access; the traceback is in the pip-tools row. The
   surface check that had marked this verified cannot fail for an incompatibility - that is
   finding F57, and it is why the row now carries a functional check beside the surface one.
   (c) *that it fixes a defect affecting packages available only from an extra index, "which is
   exactly how torch is published"* - **the premise is false for this project.** D-45, measured
   2026-11-26: for linux x86_64 `torch==2.15.0` is published on PyPI and on neither PyTorch
   index, and PyPI is this project's sole index. There is no extra index here, so that defect
   could never have applied. Its check - that the generated lock carries the index URL for the
   torch entry - was answered **no** and ruled acceptable: the lock records no index (F59), and
   the index is documented in `env/requirements.in`'s header and in the torch row below.
   **Why the open floor was nonetheless the right form.** It is what allowed 7.7.0 to be
   adopted on evidence, without a change request, when 7.5.3 proved unusable on this machine.
   An exact pin written on 2026-11-19 would have forced an amendment on 2026-11-26 to repair a
   defect the pin itself introduced. The floor is closed now because the resolve has run and
   the lock exists; from here pip-tools moves only with pip, to which it is coupled (RV-40).""")

# ---------------------------------------------------------------------------
# ADR-0006 - F50 + F51, ruled on 2026-11-27 to be fixed as one
# ---------------------------------------------------------------------------
edit("F50+F51a", A6,
     """If packaging from a mixed repository proves impossible at 4F, publish from a generated
subtree rather than splitting the history — history is what makes the dated
pre-registration worth anything, and it cannot be split without losing that.""",
     """**Condition, re-scoped on 2026-11-28 (F51).** This was written against 4F, which ran on
2026-11-22 and is closed. A fallback whose condition can only be evaluated at a closed stage
can never be taken. It is read from **stage 15 onward at every wheel build, and again at 27C
and 31** - the stages that write the packaging configuration and build the published artefact.
The condition: a wheel built by stage 15's configuration contains any path outside the
allowlist in this record's reversal trigger, and no change to that configuration removes it.

**First action, not only an outcome (F50).** This previously named a destination and no step,
so under time pressure there was nothing to do first. The order is:
1. Record the offending paths from `unzip -l` on the built wheel, so the fallback is taken
   against evidence rather than against a suspicion.
2. Generate a publish-only subtree containing `src/fusiongap/` alone, via `git subtree split`
   into a throwaway branch that is never pushed.
3. Build the wheel from that subtree and check it against the same allowlist.
4. Record a dated amendment naming the paths from step 1 and the subtree commit.

**The history is never split.** History is what makes the dated pre-registration worth
anything, and it cannot be split without losing that - which is why the subtree is generated
per release and discarded, never maintained as a second line of development.""")

edit("F50+F51b", A6,
     "Looked for at 4F, and written as an **allowlist** rather than as a list of directories to",
     """Looked for at 4F (done, 2026-11-22), from stage 15 onward at every wheel build, and again at
27C and 31. Written as an **allowlist** rather than as a list of directories to""")

# ---------------------------------------------------------------------------
# Six status flips. A second run fails here first, which is the guard working.
# ---------------------------------------------------------------------------
for name, path in (("ADR-0001", A1), ("ADR-0002", A2), ("ADR-0003", A3),
                   ("ADR-0004", A4), ("ADR-0005", A5), ("ADR-0006", A6)):
    edit("flip " + name, path,
         "Status: proposed",
         "Status: accepted 2026-11-28 (stage 5B review)")


# ---------------------------------------------------------------------------
def main():
    if not ADR.is_dir():
        print("FATAL: run this from the repository root; %s not found" % ADR)
        return 1

    texts, problems, applied = {}, [], []

    for e in EDITS:
        p = e["path"]
        if p not in texts:
            if not p.exists():
                problems.append("%s: file not found: %s" % (e["id"], p))
                continue
            texts[p] = p.read_text(encoding="utf-8")
        body = texts[p]

        if e["new"] in body:
            problems.append("%s: ALREADY APPLIED - replacement text already in %s"
                            % (e["id"], p.name))
            continue
        n = body.count(e["old"])
        if n != 1:
            head = e["old"].split("\n")[0][:72]
            problems.append("%s: target occurs %d times in %s (need exactly 1)\n"
                            "        first line of target: %s"
                            % (e["id"], n, p.name, head))
            continue

        texts[p] = body.replace(e["old"], e["new"], 1)
        applied.append("%s  ->  %s" % (e["id"], p.name))

    if problems:
        print("NOTHING WRITTEN. %d of %d edits could not be applied:\n"
              % (len(problems), len(EDITS)))
        for pr in problems:
            print("  " + pr)
        print("\n%d edits would have applied cleanly." % len(applied))
        return 1

    for p, body in texts.items():
        p.write_text(body, encoding="utf-8")

    print("ALL %d EDITS APPLIED\n" % len(applied))
    for a in applied:
        print("  " + a)
    print("\nfiles written: %d" % len(texts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
