#!/usr/bin/env bash
# scripts/hooks/attribution_guard.sh
#
# Mechanises POLICY-ATTRIBUTION.md section 3 so its steps cannot be skipped.
# Decision D-42: every artefact of this project is authored by Aparna Shaji and
# by nobody else. This script stops a breach; the checks in section 7 only
# detect one, at the next weekly review, after it is already public.
#
# Modes:
#   message <file>   Tier 0 + Tier 1 + Tier 2 over a commit message file
#   diff             Tier 0 + Tier 1 + Tier 2 over the staged diff
#
# Tier 1 BLOCKs. Tier 2 prints for review and does not block: an unreviewed
# REVIEW hit is the problem, not the hit itself (section 3).
#
# Tier 2 on the message goes beyond section 3, which scopes the review tier to
# the staged diff only. The message is the surface where attribution is most
# often requested, and a credit such as "written with Claude's help" is not a
# Tier 1 form (finding F64).
#
# THIS FILE EXCLUDES ITSELF from the diff scan. Its ATTR line contains the
# literal forbidden forms, so without the exclusion the guard blocks its own
# commit and every future edit to it. The trade-off is explicit: a change to
# this file is not attribution-scanned by this file. It is scanned by review,
# and section 7's audit still checks every commit's message and identity.
# The exclusion is a single exact path and is proved to be scoped to it.
#
# The ATTR pattern is COPIED VERBATIM from POLICY-ATTRIBUTION.md section 3. It
# was repaired twice (F46, F48) and proved against planted attribution on
# 2026-11-25. Do not edit it here. Edit the policy, re-prove it, then copy.

set -u

ATTR='(co-authored-by:|claude-session:|generated with [[]?claude|@anthropic[.]com|(authored|generated|written) by (claude|anthropic))'
MENTION='(claude|anthropic)'
SELF='scripts/hooks/attribution_guard.sh'

guard_message() {
  local msgfile="$1"
  if [ -z "$msgfile" ] || [ ! -s "$msgfile" ]; then
    echo "attribution-guard: TIER 0 FAIL - message file missing or empty: '${msgfile}'" >&2
    return 1
  fi
  if grep -nEi "$ATTR" "$msgfile"; then
    echo "attribution-guard: BLOCK - attribution form in commit message (D-42)" >&2
    return 1
  fi
  echo "attribution-guard: message - no attribution form"
  if grep -nEi "$MENTION" "$msgfile"; then
    echo "attribution-guard: REVIEW - account for each line above in one sentence (not a block)"
  else
    echo "attribution-guard: message - no vendor-name mentions"
  fi
  return 0
}

guard_diff() {
  if git diff --cached --quiet; then
    echo "attribution-guard: TIER 0 FAIL - nothing staged" >&2
    return 1
  fi
  local staged
  staged="$(git --no-pager diff --cached -- . ":(exclude)$SELF" | grep -v '^+++')"
  if printf '%s\n' "$staged" | grep -nEi "^[+].*$ATTR"; then
    echo "attribution-guard: BLOCK - attribution form in staged diff (D-42)" >&2
    return 1
  fi
  echo "attribution-guard: diff - no attribution form"
  if printf '%s\n' "$staged" | grep -nEi "^[+].*$MENTION"; then
    echo "attribution-guard: REVIEW - account for each line above in one sentence (not a block)"
  else
    echo "attribution-guard: diff - no vendor-name mentions"
  fi
  return 0
}

case "${1:-}" in
  message) guard_message "${2:-}"; exit $? ;;
  diff)    guard_diff;             exit $? ;;
  *)
    echo "attribution-guard: usage: $0 {message <file>|diff}" >&2
    exit 2
    ;;
esac
