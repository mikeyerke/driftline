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
ineligible for synthetic outcomes. When the review window closes, the PM can
instead attach the actual primary and risk values with a non-confidential source
label. Both observations remain explicitly **PM-provided · unverified**.

The two-metric evaluator is fail-closed:

- a success value alone does not complete the action without a current safe
  risk observation;
- a safe risk value alone does not complete the action without a successful
  primary outcome;
- the two observations may arrive in either order;
- a breached risk metric rolls the action back and reopens the decision; and
- a mismatched segment, metric, or unit remains inconclusive.

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

- Targeted decision/API tests: 204 passed.
- Complete backend suite: 433 passed, with two dependency deprecation warnings.
- Frontend production build: passed.
- Frontend literal contract: passed.
- First-viewport desktop check: at 1453 × 670, the primary workflow CTA is
  fully visible at y=531–581 with zero horizontal overflow. The production
  layout placed that CTA below the same browser's fold; the candidate moves the
  action directly beneath the value proposition.
- First-viewport phone check: at 390 × 844, the primary CTA is fully visible
  at y=730–780 with document and body widths exactly 390 pixels.
- Python static checks on changed backend and tests: passed.
- Persistence boundary tests: 17 passed, including expired-read and
  expired-compare-and-set rejection.
- Desktop browser journey: intake → generated brief → named approval → authored contract receipt passed.
- Mobile browser check: full intake rendered at 390 × 844 without clipped fields or horizontal overflow.
- Mobile rollback check: the generation-one allocation visibly changed from
  active to rolled back, generation two selected the rollback response, the
  approver field cleared, and the next approval remained disabled.
- Manual/local outcome fallback now converges with the Cloud Tasks path: after
  reopen it applies the returned case, clears the stale approver, and uses the
  generation-two selected option. This fixes a browser-found state mismatch in
  which generation one remained selected after a local fallback outcome.
- Real-measurement browser journey: PM intake → approval → primary value 46% →
  risk value 9% → automatic action rollback → generation-two reopen passed.
- Phone-width result: the complete reopened journey rendered at 390 × 844 with
  document and body scroll widths both exactly 390 pixels.
- Return-link journey: a newly created PM case wrote its opaque case ID into the
  URL, restored in a fresh browser tab, retained the approval state after a
  second fresh-tab load, and exposed the real-measurement form. The capability
  disclosure warns that anyone with the link can view the non-confidential case.
- Firestore cases already carry the deployment retention TTL. The candidate now
  also rejects an expired or malformed TTL at the read and compare-and-set
  boundaries instead of depending on eventually consistent TTL deletion.
- Restored follow-up at 390 × 844 also held document and body scroll widths at
  exactly 390 pixels.
- Continuous pinned-case rehearsal: first action → council → evidence detail →
  three option comparisons → named approval → autonomous outcome → generation
  two completed in 7.5 seconds locally with deliberate inspection pauses. The
  action rolled back, the next human name cleared, rollback became the selected
  recommendation, and the browser logged no warning or error.
- Monitor enqueue failure is now explicit. The approval response reports
  `monitor_status: fallback_required` when Cloud Tasks cannot accept the task;
  the UI exposes the bounded demo fallback in about 0.3 seconds and never
  claims that the autonomous monitor is active. A successfully accepted monitor
  reports `scheduled`; PM-provided cases report `not_applicable`.
- Clicking that explicitly disclosed fallback completed the measured rollback
  and generation-two reopen in 3.1 seconds; rollback was checked and recommended,
  the internal action was rolled back, the approver cleared, and browser logs
  remained clean.
- Browser diagnostics: no application-origin errors; visible errors were emitted only by the installed Grammarly extension.

Synthetic browser inputs used for verification:

- Decision: single-provider launch versus delay for failover.
- Segment: Seed-to-Series-A B2B SaaS teams.
- Primary metric: Workflow completion rate; baseline 38%; success at least 45%.
- Risk metric: Failed workflow rate; baseline 3%; stop at least 8%.
- Owner: Taylor, Product Lead.
- Review window: seven days.

## Custody

This change exists only on the isolated local branch. Local commits were
created for custody, but no push, pull request, merge, deployment, event
registration, external message, or submission was performed.
