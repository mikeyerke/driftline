# Driftline definition of done

Every capability must move through these states in order:

`implemented -> tested -> deployed -> live verified -> customer verified`

These states are not interchangeable:

- **Implemented:** code and unit/contract coverage exist locally.
- **Tested:** the complete local and hosted CI gates pass.
- **Deployed:** a named Cloud Run revision serves the exact candidate SHA.
- **Live verified:** direct production probes and the browser journey pass on
  that revision.
- **Customer verified:** a real operator or pilot supplies evidence beyond the
  isolated Driftline deployment.

## Release gate

For a code release, run all of the following against the same candidate:

```text
backend tests
Ruff
frontend production build
frontend contract checks
trace-to-eval gate
dependency/security checks
standalone image build
production verifier
live ADK/Gemini verifier
approval/undo browser or API journey
```

Documentation-only changes do not require a Cloud Run redeploy. They must still
not change a claim about the serving SHA. When a release is frozen, use one
candidate tag and one serving revision; avoid a chain of proof-only deploys.

## Product gate

The core story is complete only when one evidence-bound change reaches one real,
least-privilege downstream action and can be reversed. Prepared-only manifests,
counterfactual previews, and synthetic replays are useful support surfaces, not
substitutes for this gate.

## Evidence gate

Customer outcome fields remain `not_measured` until a real pilot records paired
baseline/Driftline values with an evidence reference. Deployment counts,
approval latency, source observations, and trace scores must never be relabeled
as customer ROI.

