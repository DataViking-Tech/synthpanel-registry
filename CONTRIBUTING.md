# Contributing to synthpanel-registry

Thanks for proposing a pack for the SynthPanel registry. This repo is a thin,
curated index — every entry is human-reviewed against the same bar.

## How packs are hosted

Packs live **in this repo** under `packs/<pack-id>/synthpanel-pack.yaml`, one
directory per pack. The directory name must match the pack's top-level `id:`
field. The root `default.json` is a generated manifest built from those
directories by `scripts/build_registry.py`.

(External-repo hosting may return in a later release; v1 keeps everything in
one curated tree so the review bar is uniform and auditable.)

## Before you submit

1. **Write your pack YAML.** Put it at `packs/<pack-id>/synthpanel-pack.yaml`.
   See the seed packs in `packs/` for examples. Required top-level fields:
   `id`, `version`, `description`, `author`, `personas`.
2. **Validate locally** by regenerating the manifest:
   ```
   pip install pyyaml jsonschema synthpanel
   python scripts/build_registry.py
   ```
   The script validates every pack against synthpanel's `validate_persona_pack`
   and rewrites `default.json` deterministically.
3. **Open a pack submission issue** using the
   [pack-submission template](.github/ISSUE_TEMPLATE/pack-submission.yml).
   This confirms author consent before a PR lands.

## Submitting the PR

Once the submission issue is accepted, open a PR that:

1. Adds `packs/<pack-id>/synthpanel-pack.yaml`.
2. Commits the regenerated `default.json` (produced by running
   `python scripts/build_registry.py`).

CI runs `python scripts/build_registry.py --check` on every PR. The PR fails
if any pack is invalid or if `default.json` is stale relative to the
`packs/` tree.

The PR template checklist mirrors the review criteria below — fill it in so
reviewers can verify at a glance.

## Review criteria

Every submission must meet all of these before merge:

- **Schema-valid** against `schema/default.schema.json` (enforced by the
  `validate` workflow).
- **Passes `validate_persona_pack`** on the pack's `personas:` list (enforced
  by the `registry-build` workflow via `scripts/build_registry.py --check`).
- **Pack ID unique** across `packs/` (directory names are the source of truth;
  the build script rejects duplicates).
- **`author.github` is a public GitHub handle.**
- **No obvious prompt-injection payloads** in persona text (reviewer
  spot-check, not automated).
- **Calibration score NOT required in v1** — the `calibration` field is
  always emitted as `null`.

`added_at` is stamped automatically by the build script from the pack
directory's first commit date; reviewers do not edit it manually.

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
- No sha256 checksum pinning in v1 — pack content is committed directly to
  this repo and reviewed in-band.
