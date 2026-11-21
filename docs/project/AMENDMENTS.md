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

## AM-05 · 2026-11-18 · Hours-based plan replaces the day calendar
- **What:** progress is counted in project hours against each stage's time box, not in calendar days. The D1–D56 calendar is retired; worked days are numbered WD (WD0 = 2026-11-09 plan review · WD1 = 11-12 · WD2 = 11-13 · WD3 = 11-14 · WD4 = 11-15 · WD5 = 11-18). Planning rate: 8.5 h/day of project work x 6 days = 51 h/week, plus 1.5 h/day on the parallel career track. Targets: v1.0.0 (core) Sat 2027-01-02 · v1.1.0 (full) Sat 2027-01-09 · MVP gate (25) ~ Mon 2026-12-28. Every gate and every time box is unchanged. The seven hard checkpoints keep their content gates and lose their calendar NO-GO branches. A task that runs above 1.5x its box goes to the next weekly review for a decision. Each weekly review records hours worked and the forecast (remaining boxed hours / measured hours per week) in STATUS-LOG. Tripwire: if the v1.0.0 forecast passes Sun 2027-02-28, a scope-or-date decision is taken at that review. The tripwire is armed from the review of Sat 2026-12-05 and uses the mean of the two most recently completed weeks, so that it fires on a trend and not on a single week.
- **Why:** day length varied from 2 h to 8.5 h, so a calendar day measured nothing, and the hard checkpoints were firing cuts on dates rather than on evidence. Hours against boxes measure the work, and the weekly forecast converts them back into a date without hiding the gap. Builder's ruling 2026-11-18: the 51 h/week rate is kept and no item is cut from the plan, so the tripwire is the only automatic brake and its date is therefore set deliberately rather than left at a default.
- **Evidence:** measured hours — week 1 (11-09 to 11-15) ~ 20 h, of which the plan review, a 67-minute toolchain download, a /tmp failure and a duplicate-folder rework were one-off costs; 11-16/17 no project work; 11-18 ~ 3 h. Stage 01 ran ~ 7 h against a 1.5 h box (~ 4.7x, finding RV-22). Plan boxes ~ 382 h total, ~ 376 h remaining, ~ 330 h to v1.0.0.
- **DoD impact:** none. No CORE line and no strongly-expected line changes. Supersedes the AM-01 projections and the calendar and release dates in charter section 3. AM-02 keeps its ordering decision (core release before extensions) and loses its dates.

## AM-06 * 2026-11-21 * AM-04 evidence corrected; forecast week defined; stage-box ruling and a governance allowance
- **What:** three items, all from the weekly review of 2026-11-21. (1) **AM-04's evidence is corrected.** AM-04 records the 2026-11-03 draft as "committed with ADR-0001 at stage 03". The draft was in fact committed *after* ADR-0001 (`52d385e`), under gate-03 condition C5, in commit `7747d1a` on 2026-11-21, and its original bytes were verified recoverable from the committed file after the commit. AM-04's weights and filters are unchanged; AM-04 attributes only the four weights to the draft, and the $0-cost and WSL2 filters are AM-04's own. (2) **The weekly forecast divides by the most recently completed Monday-to-Sunday week**, with the week in progress recorded as partial information only. AM-05 fixed the formula but not the week, and a Saturday review that divides by the week in progress omits that week's last two days at every review. (3) **Stage 03 ran above 1.5x its 1.5 h box; the AM-05 decision is that no time box is re-estimated.** The overrun is recorded as gate-condition discharge and document rework, not as box error: stage 02 closed inside its 2 h box on comparable work and is the control case. In its place, unboxed project governance - condition discharge, change requests, decision records, register and log maintenance, session wrap and the weekly review itself - is given a measured allowance and counted separately from stage boxes.
- **Why:** (1) this file is append-only, so a stale evidence line is corrected by a new entry and never by editing the old one. (2) and (3) the review found that the plan's forecast counts only boxed hours and therefore assumes unboxed governance drops to zero; on measured numbers the v1.0.0 forecast is ~2027-03-13 on boxed hours alone and ~2027-04-20 to ~2027-06-09 once the allowance is applied. Reversal trigger for (3): if stage 05 or 06 also exceeds 1.5x its box while carrying no gate conditions and no rework, the document boxes are re-estimated at that review.
- **Evidence:** commit `7747d1a`; `gitleaks detect` on 2026-11-21 - 23 commits scanned, no leaks, exit 0; plan boxes re-summed 2026-11-21 = 382 h total and 330 h to v1.0.0, agreeing with AM-05's own figure, less 9.5 h closed = 320.5 h remaining; hours mapping to a stage box ~16.2 h of ~38.5 h logged, from stage 01 ~7 h against 1.5 h (AM-05), stage 02 ~1.7 h against 2 h, stage 03 ~3 h or more against 1.5 h, spikes 4A and 4B ~4.5 h on estimate.
- **DoD impact:** none. No CORE line and no strongly-expected line changes. The tripwire date and its arming review (2026-12-05) are unchanged.
