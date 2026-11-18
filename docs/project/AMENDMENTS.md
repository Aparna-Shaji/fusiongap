# FusionGap · Amendments
Every change to scope, a requirement, a version pin, the protocol or a date after the plan was approved (2026-11-09). Append-only: a reversed amendment gets a new entry. PROTOCOL.md and PREDICTIONS.md are never edited after tag `prereg-v1`; deviations are disclosed here.

## AM-01 · 2026-11-14 · Week-1 schedule slip
- **What:** D1 went to the plan review; no project work on D2–D3 (2026-11-10/11); 16 h worked in week 1. Week-1 content moves to D7–D11. The harness gate (08) and the `prereg-v1` tag (gate 10) move to ~D10–D11 (2026-11-18/19) under gate 08's own "not green by D5" rule. Projections at 8.5 h/day from D7: K3 headline (gate 23) ~Thu 2026-12-17 · MVP (gate 25) ~Wed 2026-12-23 · v1.0.0 ~Wed 2026-12-30 · v1.1.0 Sat 2027-01-02 with reduced extensions (likely K2 Triton only).
- **Why:** time lost; gates are not softened to recover it.
- **Evidence:** STATUS-LOG D1–D6; week-1 actual 16 h.
- **DoD impact:** none on CORE. Quantization, first in the cut order, is expected to be cut at the D13 checkpoint (Sat 2026-11-21). No slack remains: another lost day cuts a strongly-expected item. Re-baseline at gate 06 if tasks run above 1.5× their time boxes.

## AM-02 · 2026-11-12 · Core release before extensions
- **What:** stages 27–31 (freeze, claims audit, hardening, acceptance, release) run directly after gate 25 → v1.0.0 by D46 (Thu 2026-12-24). Stage 26 extensions, blog post and talk follow → v1.1.0 by D55 (Sat 2027-01-02). Closure D55 afternoon; D56 rest.
- **Why:** in the approved order, an extension slip would delay the core release.
- **Evidence:** decision recorded 2026-11-12.
- **DoD impact:** none. CORE lines unchanged; strongly-expected lines ship in v1.1.0 or are cut by amendment.

## AM-03 · 2026-11-14 · D7 worked
- **What:** Sun 2026-11-15 (D7) is a working day, one-off catch-up. The rest-day rule is unchanged for every other week.
- **Why:** recover part of AM-01.
- **Evidence:** STATUS-LOG D7.
- **DoD impact:** none.

## AM-04 · 2026-11-15 · Technology-evaluation criteria fixed from the 2026-11-03 draft
- **What:** stage 03 scores candidates with the weights in the ADR-0001 draft dated 2026-11-03: compute-capability-7.5 evidence 40 · reproducibility (pinnable) 25 · ease of learning 20 · interview relevance 15. $0 cost and WSL2 support become pass/fail filters applied before scoring.
- **Why:** the weights were set before any spike evidence existed, as gate 03 requires; a hard constraint inside a weighted sum can be outweighed by high scores elsewhere.
- **Evidence:** draft file dated 2026-11-03, committed with ADR-0001 at stage 03.
- **DoD impact:** none.
