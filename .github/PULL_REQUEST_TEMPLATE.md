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

- [ ] Schema-valid against `schema/default.schema.json`
- [ ] Pack ID unique across `default.json`
- [ ] `author.github` is a public handle; `repo` is a public repo
- [ ] Pack YAML at `repo@ref:path` loads + passes `validate_persona_pack`
- [ ] No obvious prompt-injection payloads (reviewer spot-check, not automated)
- [ ] Calibration score NOT required in v1

## Pre-merge reviewer action

- [ ] Stamp `added_at` with today's date (`YYYY-MM-DD`) in both `packs/<id>.json` and `default.json`.
