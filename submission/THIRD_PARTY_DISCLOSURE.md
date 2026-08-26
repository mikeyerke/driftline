# Driftline third-party dependency disclosure

Status: locked-environment engineering inventory, refreshed August 26, 2026.
This is not legal advice and does not replace the entrant's personal
ownership/rights attestation for the now-verified source archive.

## Reproducible inventory result

After `uv sync --locked --extra dev` and `npm ci`, run:

```bash
uv --directory backend run python ../scripts/verify_third_party_licenses.py
```

The current lockfiles resolve:

- 82 third-party Python distributions;
- 44 Node package-lock entries;
- 12 declared backend runtime/test dependencies; and
- 5 declared frontend build/runtime dependencies.

Every resolved package has license metadata, an OSI license classifier, or an
installed license file. `google-crc32c` is the only Python distribution without
license metadata; its installed distribution includes an Apache License 2.0
file, which the verifier reads. The current inventory contains MIT, Apache 2.0,
BSD, ISC, MPL 2.0, PSF 2.0, and compatible dual-license expressions. The gate
fails on missing license evidence and flags GPL, AGPL, SSPL, or BUSL families
for explicit review instead of silently accepting them.

## Direct application dependencies

Backend runtime:

- FastAPI — MIT
- Google ADK — Apache 2.0
- Google Cloud BigQuery, Firestore, Secret Manager, Storage, and Tasks clients —
  Apache 2.0
- python-dotenv — BSD 3-Clause
- Uvicorn — BSD 3-Clause

Backend test/tooling:

- pytest — MIT
- pytest-asyncio — Apache 2.0
- Ruff — MIT

Frontend build/runtime:

- React and React DOM — MIT
- Vite and `@vitejs/plugin-react` — MIT
- Lucide React — ISC

Exact versions and every transitive package remain pinned by
`backend/uv.lock` and `frontend/package-lock.json`; those lockfiles, installed
metadata, and license files are the authoritative machine inputs. This summary
must be regenerated and reviewed whenever either lockfile changes.

## Other material

- Driftline's own repository code is offered under the repository MIT license.
- Google Cloud hosted services and Gemini/Vertex AI are used under their
  applicable service terms; they are not redistributed dependencies.
- Public/synthetic demonstration evidence is labeled in the product and is not
  presented as proprietary customer data.
- The source archive's hash, contents, and contest-period member timestamps are
  verified in `submission/ORIGINALITY_PROVENANCE.md`; personal ownership/rights
  remain an entrant attestation.
