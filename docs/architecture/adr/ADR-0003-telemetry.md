# ADR-0003 — Telemetry source and sampling method

Status: accepted 2026-11-28 (stage 5B review)
Date: 2026-11-23
Owner stage: 04 → frozen at 05

## Context
Brief §9 makes clocks and temperature part of measurement hygiene: a timing number is only
admissible if the state of the card while it was produced is on record. Risk R7 recorded the
exposure before any evidence existed — telemetry might be unreadable under WSL2, and the
clocks might not be lockable. Both halves turned out to matter, and in opposite directions:
the telemetry is readable, and the clocks are **not** lockable, which turns clock state from
something to control into something to measure. How that measurement is taken is therefore a
decision, and it gates every timing number this project is allowed to report.

**On decision identifiers.** `D-nn` and `CR-nn` refer to entries in the project's state
file, which is working memory and is not part of this repository. They are secondary
references. Everything load-bearing here rests on the evidence paths named below.

## Decision
Six parts.

1. **Source.** WSL `nvidia-smi`, one CSV query per sample. Not `nvidia-smi.exe` through
   Windows interop, and not pynvml.
2. **A separate process.** The sampler never runs inside the process under measurement.
3. **Rate.** `-lms 400`, which delivers **2.37 Hz measured**. The requested delay is not the
   interval: `nvidia-smi -lms N` gives N milliseconds *plus* the query's own time, so the
   rate is a measured property and is recorded per capture, never assumed from the flag.
4. **Fields, ten per sample:** `timestamp`, `clocks.sm`, `clocks.mem`, `power.draw`,
   `enforced.power.limit`, `temperature.gpu`, `utilization.gpu`, `utilization.memory`,
   `memory.used`, `clocks_event_reasons.active`. **Six of them — SM clock, memory clock,
   temperature, power draw, the event-reason flags and `enforced.power.limit` — must never
   read `N/A` in a capture that is used.** The sixth was added on 2026-11-28 (F87). It is the
   field D-39 pins, the field reversal trigger 4 reads, and the field the invalidity rule in
   Consequences rests on - load-bearing in three places and protected in none. The failure is
   silent in the direction that matters: a load window reading `N/A` throughout yields a
   distinct set of exactly one member, so trigger 4 does not fire and the run reads as valid
   with no ceiling recorded at all.
5. **Windows are cut from the load generator's own printed timestamps**, never inferred from
   the telemetry itself. This is not a style preference; see Evidence.
6. **Observations are printed and never become pass criteria.** Cool-down behaviour and the
   post-warm-up window are reported by the grader as observations, below the verdict.

**What this telemetry may not be used for**, stated here so no later stage has to rediscover
it: the Clocks Event Reasons *duration* counters increment with wall-clock time regardless of
throttling and are a clock, not a throttle meter. The *active* flags are usable for liveness
and for detecting that the card left idle. **Neither attributes a slowdown to a cause.** Any
throttle attribution in this project rests on power draw against the enforced ceiling plus
clock variance under sustained load, not on those counters.

Checkable: `spikes/4C/grade_4c.py` is the criterion as executable code, with exit 0 for pass,
1 for a failing result and 2 for malformed input.

## Evidence
`results/env/run2_4C_loaded.csv`, `run2_4C_load_log.txt`, `run2_4C_perf_during.txt` and
`run2_4C_power_after.txt`, graded by `spikes/4C/grade_4c.py`, exit 0 on 2026-11-21.
TECH-STACK cell 10 records the result: a **43.6 s window at 2.37 Hz, maximum gap 0.47 s, no
`N/A`, idle median 300 MHz**. Cell 10 is DECIDED + VERIFIED on that evidence.

**Run 1 failed, and the failure is why part 5 exists.** Run 1 of 2026-11-21 failed clause 2
because the grader took the idle reference as "every sample before the window", which swept
in the cuBLAS warm-up burst and put a 1380 MHz sample into the idle baseline. That was a
**grader defect, not a telemetry result**: the instrument was wrong, and the measurement it
rejected was sound. Cutting both windows from the load generator's own timestamps, with
one-second margins to trim transition samples, is the fix. The criterion itself never changed.

**The criterion it grades was itself replaced before the run it judged** (CR-10, recorded as
amendment AM-07). The original clause asked the SM clock to change "by more than the
read-to-read spread of the idle samples", and the idle spread measured 0 MHz across 83
samples on two separate baselines — so the clause reduced to "changes by more than 0 MHz",
which a rounding artefact satisfies. A criterion that cannot fail would have licensed the
entire measurement programme on no evidence. The replacement requires a doubling of the idle
median plus corroboration from a second field, and it was committed before the run it judges.

**Clock locking was attempted and refused.** Verification item V3 is NO: four mechanisms were
tried and all four refused, two of them while reporting success. `nvidia-smi -ac` and `-lmc`
exit 0 and print "All done" while setting nothing, and `-rgc` fails with "Unknown Error", so
there is no reset path either. Clock state is therefore a measured covariate, not a
controlled variable.

**The enforced ceiling, measured twice. The primary evidence is 4L** -
`results/env/4L_balance.csv`, `4L_balance.txt`, `4L_high-performance.csv` and
`4L_high-performance.txt` (2026-11-24), produced by the committed instrument
`spikes/4L/sample_power.py`: 140 samples per arm, 280 in total, the ceiling reading 30.00 W on
every single sample, with zero disagreements between the two power-limit forms. That run is
reproducible from this repository. The reading below is not, and the distinction was missing
from this record until 2026-11-28 (F85).

**The earlier reading, 2026-11-23** (`results/env/4K_power_under_load.txt` - **produced by an
uncommitted command and therefore NOT regenerable, finding F32; retained because it is the only
record of the idle movement described two paragraphs below**): 40 samples across idle, 25 s of
sustained
100 % utilisation, and idle again. The ceiling read **30.00 W on every sample**, idle and
loaded alike. Power draw under load was 28.1–29.1 W, which is 94–97 % of the cap, with the SM
clock oscillating between 945 and 1050 MHz against a 1515 MHz device maximum — the signature
of a card held at its power limit by clock modulation. The loaded median was **1005 MHz,
reproducing 2026-11-21's independent median exactly**, on a different workload two days apart.

**The same file shows why the ceiling is sampled rather than read once.** Earlier on
2026-11-23 the idle ceiling moved between 50 W and 30 W within a single twenty-second window
with the mains adapter untouched, and `nvidia-smi -pl` is refused even as root, so it cannot
be held from inside WSL. Under load it did not move. The rule that follows is in Consequences.

## Alternatives rejected
| Alternative | Why it lost |
|---|---|
| `nvidia-smi.exe` through Windows interop | A second path to the same data, with Windows process-start cost inside the sampling loop and a different clock domain for its timestamps. Never needed: the WSL binary returns every field required |
| pynvml in-process | Puts the sampler inside the process under measurement, which is the perturbation risk RV-06 exists to guard against, in exchange for nothing this project needs |
| Sampling inside the timed region | Same objection, sharper: the thing being measured would be paying for its own measurement |
| Locking the clocks and measuring without telemetry | The ideal, and impossible here: V3 is NO on four mechanisms, two of which reported success while doing nothing. Designing around a lock that does not exist would have produced numbers with no record of the state that produced them |

## Consequences
- **Easier:** one tool, already installed, no dependency, no privilege, works under WSL2, and
  the capture is a plain CSV that any later stage can re-grade.
- **Harder:** at 2.37 Hz a sample arrives every ~420 ms, so a timed region shorter than about
  a second has no telemetry of its own. Telemetry therefore describes a **group** of repeats,
  not an individual repeat, and the report must say so wherever it pairs a timing with a
  clock.
- **Harder:** clocks cannot be locked, so run-to-run clock variation is a covariate that is
  measured and reported rather than removed. The 1005 MHz median reproducing across two days
  is evidence that it is stable enough to work with, not evidence that it is fixed.
- **Harder:** the enforced power ceiling is read, not set. It held under load on the only
  occasion it has been measured under load, and it moved at idle on the same day.
- **Must do, all at stage 08 unless stated:**
  - The harness records the set of distinct `enforced.power.limit` values seen **in a run's
    load window**, never across the whole capture. The scope is load-bearing, and leaving it
    out was finding F86. This record documents above that the ceiling moves between 50 W and
    30 W at idle and does not move under load; every capture contains idle windows, because
    they are the negative control that proves the load ran. A whole-capture set would therefore
    mark a capture invalid for a documented, harmless idle wobble - firing on the control
    instead of on the measurement. A **load-window** set with more than one member is
    **invalid, not adjusted**. **Enforced from 5C by `scripts/env/capture.py`**, which computes
    that set over the load window only; stage 08's harness inherits it rather than inventing
    it. `spikes/4C/grade_4c.py` prints its set over the whole capture - that is an observation
    and must not be read as this criterion.
  - A run's ceiling is comparable only to a roofline denominator measured under the same
    ceiling. Stage 07 records the ceiling with the ceilings it measures.
  - Oracle O7 at 8D checks that sampling does not disturb the timed region (RV-06).
  - The harness verifies the return to idle before the next group rather than sleeping a fixed
    interval. The grader's cool-down block already measures this; it becomes a check.

## Fallback
If any of the six required fields begins reading `N/A` under load, fall back to a spin-kernel
clock probe around each group (oracle O2, stage 8D), and disclose temperature as unavailable
rather than estimating it. Record the change as a dated amendment. The fallback deliberately
loses a field instead of inventing one.

## Reversal trigger
Looked for in every committed capture, and at 8D.
1. Any of the six required fields reads `N/A` in a capture that is used.
2. The measured rate falls below 2 Hz, or the maximum inter-sample gap exceeds 0.75 s.
3. Oracle O7 shows the sampler perturbs the timed region beyond its stated tolerance.
4. A run's `enforced.power.limit` set has more than one member.
