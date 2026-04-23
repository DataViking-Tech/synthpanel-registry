# Contributing to synthpanel-registry

Thanks for proposing a pack for the SynthPanel registry. This repo is a thin,
curated index — every entry is human-reviewed against the same bar.

## Before you submit

1. **Publish your pack in a public GitHub repo.** The pack file should be
   named `synthpanel-pack.yaml` at the repo root. A git tag (e.g. `v0.1.0`)
   is recommended so the registry entry can pin a `ref`.
2. **Validate locally.** Run `synthpanel pack import gh:owner/repo --unverified`
   and confirm the pack loads and passes `validate_persona_pack`.
3. **Open a pack submission issue** using the
   [pack-submission template](.github/ISSUE_TEMPLATE/pack-submission.yml).
   This confirms author consent before a PR lands.

## Submitting an entry

Once the submission issue is accepted, open a PR that:

1. Adds `packs/<pack-id>.json` with the entry fields described in
   [`schema/default.schema.json`](schema/default.schema.json).
2. Appends the same entry to the `packs` array in `default.json`.
   (A `packs/*.json` → `default.json` build step will automate this in a
   later release; until then both files are edited by hand.)

The PR template checklist mirrors the six review criteria below — fill it in
so reviewers can verify at a glance.

## Review criteria

Every submission must meet all six of these before merge:

- Schema-valid against `schema/default.schema.json`
- Pack ID unique across `default.json`
- `author.github` is a public handle; `repo` is a public repo
- Pack YAML at `repo@ref:path` loads + passes `validate_persona_pack`
- No obvious prompt-injection payloads (reviewer spot-check, not automated)
- Calibration score NOT required in v1

On merge, the reviewer stamps `added_at` (today's date, `YYYY-MM-DD`).

## Removal and deprecation

Authors may request takedown or deprecation via the
[pack-removal issue template](.github/ISSUE_TEMPLATE/pack-removal.yml).
Removal is honoured on a best-effort basis and does not retroactively
invalidate users' local caches.

## Scope

- `kind: persona` entries only in v1. The schema reserves `instrument` for
  later but the review bar does not cover instrument-specific checks yet.
- Calibration fingerprints are reserved (`calibration: null`); do not
  populate that field.
- No sha256 checksum pinning in v1 — we trust git `@ref` tags.
