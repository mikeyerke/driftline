# Devpost form audit

Status: read-only audit, August 26, 2026. No Devpost account login, hackathon
registration, project creation, field entry, draft save, upload, or submission
was performed.

## Current authoritative observation

The public contest and authenticated-project URL were opened in both the Codex
browser and the connected Chrome profile. Both sessions were logged out of
Devpost. The project-management route displayed **Register for this hackathon**
and did not expose the submission form or its input constraints.

The public contest surface currently shows:

- deadline: August 31, 2026 at 7:00 PM CDT;
- public online contest;
- Taskmaster as one of the three mutually exclusive tracks;
- public YouTube or Vimeo video, four minutes maximum;
- hosted-project URL, description, repository, spin-up instructions,
  architecture diagram, Google technology selections, and testing instructions.

The rules and FAQ establish those requirements, but they do not prove the exact
live form labels, select options, character limits, upload constraints, or final
review rendering.

## Re-entry condition

After Mike signs in to Devpost in the connected Chrome profile, repeat the
read-only audit from:

`https://devpost.com/submit-to/30845-all-things-agentic-hackathon/manage/submissions`

Do not join the hackathon, create a project, enter or save fields, upload media,
accept terms, or submit without the separately authorized action. Merely reading
the authenticated form and its constraints remains distinct from registration
and publication.

## Fields still unverified from the actual form

- project-name and tagline character limits;
- whether description is one field or several prompted story fields;
- exact Google SDK/model/service selectors;
- architecture upload type and size limits;
- video URL validation behavior;
- testing-instruction length or privacy behavior;
- category and optional-prize controls;
- bonus-content and social-link fields;
- start-date format;
- originality/pre-existing-work questions;
- required entrant/eligibility/consent confirmations; and
- the final preview and submit boundary.

Until that authenticated read-only pass occurs, `devpost-submission.md` is a
rules-aligned prepared packet, not proof of exact form compatibility.
