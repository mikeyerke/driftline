# PM utility research refresh — 2026-08-25

## The product job

Driftline is for the moment when a product manager has already made or inherited
a commitment, new evidence no longer agrees with it, and the team needs a
defensible response before the next launch, rollout, pricing, or packaging
milestone.

It is not a roadmap, feedback repository, analytics dashboard, or generic AI
copilot. It closes one decision loop:

1. assemble the minimum relevant evidence;
2. make the material disagreement visible;
3. compare ship, segment, rollback, and defer;
4. record a human-approved, reversible experiment;
5. monitor the guardrail and preserve what the outcome taught the team.

## Research signals

- Atlassian's 2025 State of Teams research surveyed 12,000 knowledge workers and
  200 executives and found that leaders and teams spend 25% of their time
  searching for answers. Product implication: Driftline should assemble a
  decision packet, not ask a PM to maintain another dashboard.
  Source: https://www.atlassian.com/blog/state-of-teams-2025
- Atlassian reports that teams aligned to goals are 6.4x more likely to produce
  high-quality work, 2.2x more likely to focus on what matters, and 4.9x more
  likely to meet deadlines. Product implication: every decision needs the
  current commitment, why-now, measurable success, and owner handoff in one
  record.
  Source: https://www.atlassian.com/blog/innovation/goal-alignment
- Productboard's 2025 Product Ops survey reports only 15% full integration with
  Sales and Customer Success, while 28% name better feedback loops as the
  biggest customer-facing opportunity. Product implication: customer, support,
  usage, strategy, and feasibility evidence must remain visibly connected.
  Source: https://www.productboard.com/blog/the-state-of-product-ops-in-2025/
- Productboard's product-leadership survey reports a confidence/execution gap:
  most executives feel confident in their product strategy, yet fewer than half
  consistently achieve their goals. Product implication: a recommendation is
  insufficient; Driftline must attach guardrails, rollback, autonomous
  measurement, and a learning receipt.
  Source: https://www.productboard.com/ebook/product-leadership-trends-and-insights/
- Product-Led Alliance and ProductPlan's 2026 survey of nearly 250 product
  professionals lists becoming more outcome-focused, limited bandwidth,
  strategy alignment, and responsible AI adoption among the leading concerns.
  Product implication: automation should remove evidence and monitoring work
  while keeping authority with a named PM.
  Source: https://www.productledalliance.com/product-management-statistics/

## Changes derived from the research

### First-screen clarity

The first viewport now states the audience, the triggering problem, the four
bounded responses, the outputs, and the no-sign-in demo path. The old
"Decision Twin" label no longer carries the burden of explaining the product.

### Decision memory

The council now receives a bounded precedent retrieved by BigQuery vector
search over four normalized decision-shape features: upside, downside,
cross-segment conflict, and reversibility. Precedents are explicitly
non-authoritative and cannot replace current evidence. The public seed records
are labelled synthetic fixtures; no customer history is implied.

### Closed-loop proof

The existing human approval, Cloud Tasks monitor, generation-based reopening,
and learning receipt remain the core differentiator. The new first screen
explains that loop in PM language rather than infrastructure language.

### Sign-in recovery

Google Identity Services requires the exact site origin to be registered on the
OAuth web client. The production client already authorizes the Cloud Run origin,
while the Firebase hosting origin produced `origin_mismatch`. The UI now routes
sign-in to the authorized first-party Cloud Run origin before loading Google
Identity Services. This removes the broken path without weakening token or
tenant validation. The Firebase origin should still be added to the OAuth
client later for a seamless same-origin experience.

Google setup reference:
https://developers.google.com/identity/gsi/web/guides/get-google-api-clientid

BigQuery vector-search reference:
https://docs.cloud.google.com/bigquery/docs/vector-search

## Google-native architecture, without tech-for-tech's-sake

- Google ADK: five role-isolated positions plus a separate synthesis turn.
- Gemini on Vertex AI: schema-bound analysis with current evidence and bounded
  precedent context.
- BigQuery: privacy-floored aggregate metrics and exact, byte-capped vector
  precedent retrieval.
- Firestore: append-only, generation-aware decision state and audit history.
- Cloud Tasks: durable post-approval measurement without a second PM click.
- Cloud Run: isolated runtime and the authorized Google operator sign-in origin.

The strongest technical story is not the number of Google services. It is that
each service owns one necessary part of a trustworthy product-decision loop.
