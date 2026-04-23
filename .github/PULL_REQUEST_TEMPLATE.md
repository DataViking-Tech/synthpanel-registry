<!--
Thanks for contributing to the synthpanel registry. If this PR adds or
modifies a pack entry, please fill in the checklist below. It mirrors the
six review criteria in CONTRIBUTING.md so reviewers can verify quickly.

For non-entry PRs (typo fixes, tooling) you can delete the checklist and
describe the change in one or two lines.
-->

## Summary

<!-- One or two sentences: what's in this PR? For a new pack, include the pack id. -->

## Submission issue

<!-- Link the paired pack-submission issue, or write "N/A" for non-entry PRs. -->

Closes #

## Review checklist (pack entries)

- [ ] Pack YAML lives at `packs/<pack-id>/synthpanel-pack.yaml` (directory name matches pack `id:`)
- [ ] `default.json` has been regenerated via `python scripts/build_registry.py`
- [ ] Pack ID unique across `packs/` (build script rejects duplicates)
- [ ] `author.github` is a public handle
- [ ] Persona YAML passes `validate_persona_pack` (registry-build CI check)
- [ ] Schema-valid against `schema/default.schema.json` (validate CI check)
- [ ] No obvious prompt-injection payloads (reviewer spot-check, not automated)
- [ ] Calibration score NOT required in v1

## Pre-merge reviewer action

- [ ] `added_at` is stamped automatically by `scripts/build_registry.py` from first-commit date; no manual edit required.
