# Driftline originality and implementation provenance

Status: evidence record, refreshed August 26, 2026. This document separates
machine-verifiable implementation custody from the entrant attestation that
only Mike can make about material supplied before the repository existed.

## Machine-verifiable timeline

The official submission period began August 3, 2026 at 9:00 AM Pacific.

| Event | UTC timestamp | Evidence |
| --- | --- | --- |
| First repository commit | 2026-08-18 13:57:25Z | Git root commit `b7a45f1b456f8e5e8cb630574b6e829bd4f575c4` |
| Public GitHub repository created | 2026-08-18 13:57:39Z | GitHub repository metadata for `mikeyerke/driftline` |
| Dedicated Google Cloud project created | 2026-08-18 14:14:30.615Z | Project `driftline-hackathon-2026`, number `724959673622` |
| First successful Cloud Build | 2026-08-18 20:23:59Z | Build `38a33746-3dda-4b26-befc-0bd1d33363d4` |

The root commit added 43 files and 4,931 text lines. Its timestamp, repository
creation, isolated cloud-project creation, and first build are mutually
consistent implementation-custody anchors inside the contest window.

These timestamps do **not** independently prove when every idea, text passage,
image, or imported file was authored. They prove when the implementation
repository and deployment environment came into existence.

Run `./scripts/verify_contest_provenance.sh --external` to recheck the local Git,
public GitHub, Google Cloud project, and first-build evidence before submission.

## Pre-contest material boundary

Known from the project record:

- product ideation existed before implementation began; and
- a source package was supplied at build start.

Not established by the repository alone:

- whether that package contained concept/requirements material only;
- whether it contained implementation code, images, copy, or other assets;
- which exact current files, if any, derive from it; and
- what third-party rights or licenses applied to any such material.

## Entrant attestation required before submission

Mike must choose the factually correct branch after inspecting the source
package or otherwise confirming its contents:

### If the package contained ideation or requirements only

> Driftline's product concept and requirements were informed by pre-contest
> ideation and a source package containing no implementation code. The
> implementation repository, Google Cloud project, and deployment were created
> during the August 3–31, 2026 submission period, beginning August 18. The entry
> uses the open-source dependencies disclosed in the repository.

### If the package contained code, images, copy, or other implementation assets

Do not use a generic sentence. Enumerate each incorporated component, its
original date/source, ownership or license, and the current paths derived from
it. Confirm that the rules permit the incorporation before submitting.

Until one branch is verified, the Devpost originality answer is **prepared but
not final**. A root-commit date must never be used to imply facts about the
source package that the evidence does not prove.
