# Local custom-intake audit — 2026-08-25

Status: local verification only. Not deployed or published.

## Why this pass existed

The production public lane accepted a PM's own decision and honestly labeled the context as unverified, but its approved experiment used placeholder language for the metric and stop rule. That was sufficient for a safe demo and insufficient for a credible real-PM pilot.

## Production observation before the local change

Using non-sensitive synthetic context, the live custom intake completed:

1. Opened **Use my decision**.
2. Accepted a new platform-dependency decision rather than the showcase fixture.
3. Created a generation-one brief with five council positions and three competing responses.
4. Labeled every supplied input **PM-provided · unverified** and reported **0 of 3 checks corroborated**.
5. Required a named human before approval.
6. Refused to generate a synthetic outcome for the PM-provided case.

The resulting operating contract still used `decision_success_metric`, a generic success condition, and a generic risk condition. This was the identified pilot blocker.

## Local change

The intake now requires the PM to define before generation:

- affected segment;
- accountable action owner;
- primary outcome metric, unit, baseline, direction, and success threshold;
- risk metric, baseline, direction, and stop threshold; and
- review window.

The approved experiment preserves those exact values and displays them in the
learning receipt and owner follow-through. PM-provided decisions remain
ineligible for synthetic outcomes.

The local candidate also makes the Taskmaster action explicit without
pretending to mutate a customer system. A named approval creates one bounded
internal allocation record tied to the exact evidence hash, synthesis hash,
decision generation, and target segment. Its contract is deliberately narrow:

- action type: `internal_allocation`;
- scope: Driftline decision state only;
- external writes: none;
- active after approval;
- completed when the measured outcome validates the plan; and
- automatically rolled back before the case reopens when a guardrail
  invalidates the plan.

The allocation lifecycle is appended to the case event history. This is a real,
reversible state transition, not a Jira or customer-system side-effect claim.

## Verification evidence

- Targeted decision/API tests: 199 passed.
- Complete backend suite: 425 passed, with two dependency deprecation warnings.
- Frontend production build: passed.
- Frontend literal contract: passed.
- Python static checks on changed backend and tests: passed.
- Desktop browser journey: intake → generated brief → named approval → authored contract receipt passed.
- Mobile browser check: full intake rendered at 390 × 844 without clipped fields or horizontal overflow.
- Mobile rollback check: the generation-one allocation visibly changed from
  active to rolled back, generation two selected the rollback response, the
  approver field cleared, and the next approval remained disabled.
- Manual/local outcome fallback now converges with the Cloud Tasks path: after
  reopen it applies the returned case, clears the stale approver, and uses the
  generation-two selected option. This fixes a browser-found state mismatch in
  which generation one remained selected after a local fallback outcome.
- Browser diagnostics: no application-origin errors; visible errors were emitted only by the installed Grammarly extension.

Synthetic browser inputs used for verification:

- Decision: single-provider launch versus delay for failover.
- Segment: Seed-to-Series-A B2B SaaS teams.
- Primary metric: Workflow completion rate; baseline 38%; success at least 45%.
- Risk metric: Failed workflow rate; baseline 3%; stop at least 8%.
- Owner: Taylor, Product Lead.
- Review window: seven days.

## Custody

This change exists only in the isolated worktree. No commit, push, pull request, merge, deployment, event registration, external message, or submission was performed.
