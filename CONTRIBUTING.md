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
- **Calibration is OPTIONAL** — packs may declare a `calibration:` list on
  the pack YAML (see [Calibration](#calibration) below). The registry's
  `calibration` entry field stays `null` in v1; the builder summarizes any
  declared runs as `calibration_count` on the registry entry.

`added_at` is stamped automatically by the build script from the pack
directory's first commit date; reviewers do not edit it manually.

## Calibration

Calibration lets a pack advertise — or honestly report the absence of —
ground-truth fit data against a public benchmark. Calibration runs are
produced by `synthpanel pack calibrate` (see the
[synthpanel calibration docs](https://synthpanel.dev/docs/calibration)) and
declared on the pack YAML at the top level:

```yaml
calibration:
  - dataset: gss              # SynthBench-supported dataset id
    question: HAPPY           # question key within the dataset
    jsd: 0.18                 # Jensen-Shannon divergence vs human baseline
    n: 100                    # panel size
    samples_per_question: 15  # samples for stable JSD
    models: [...]             # panelist blend used for the run
    extractor: pick_one:auto-derived
    panelist_cost_usd: 0.6451
    calibrated_at: 2026-04-26T14:23:00Z
    synthpanel_version: 0.11.1
    methodology_url: https://synthpanel.dev/docs/calibration
```

Required per-entry fields: `dataset`, `question`, `jsd`, `n`,
`calibrated_at`. The remaining fields are recommended but optional; they
let downstream consumers sanity-check methodology drift. `calibration` is
itself OPTIONAL — a missing or `null` block means "uncalibrated," which is
a valid state.

### Which packs SHOULD calibrate

Representative packs that claim to model a real human population —
demographic axes (age, geography), broad consumer panels (e.g.
`general-consumer`), and ICP packs that map to a measurable real-world
profession or buyer cohort. If a reviewer can plausibly point at a public
dataset that overlaps the pack's domain (GSS, ANES, Eurobarometer, public
ATP waves), the pack belongs in this category and should accumulate
calibration runs over time.

### Which packs SHOULD NOT calibrate

Packs deliberately authored as **non-representative** instruments:

- ICP packs targeting a specific product's buyer set, where the goal is a
  designed slice rather than a population estimate.
- Narrow vertical packs (e.g. `legaltech-buyer`) where no public benchmark
  exists for the slice and a JSD against a mismatched baseline would be
  more misleading than informative.
- Stress-test or contrarian packs (`contrarian-stress`) authored as
  adversarial probes, not population samples.

For these, leave `calibration` absent. Don't fabricate runs against
unrelated benchmarks just to fill the field — the registry treats
"uncalibrated" as honest signal.

### Interpreting JSD

Jensen-Shannon divergence summarizes how far a panel's answer
distribution sits from the human baseline on a given question (0.0 =
identical, 1.0 = maximally separated). Treat the bands as rough guides,
not bright lines:

| JSD range   | Interpretation                                             |
|-------------|------------------------------------------------------------|
| `< 0.10`    | Strong fit. Panel tracks the human baseline closely.       |
| `0.10–0.30` | Useful fit. Reasonable for directional research.           |
| `0.30–0.50` | Weak fit. Use with care; document caveats in research.     |
| `> 0.50`    | Cautioned. Builder emits a warning; reviewer spot-check.   |

A high JSD does not auto-fail the pack — the validator emits a build
warning above 0.50 but accepts the entry. JSD outside `[0, 1]` is
rejected as malformed.

### What CI enforces

`scripts/build_registry.py` (run by the `registry-build` workflow):

1. Accepts `calibration: null` or an absent field as "uncalibrated."
2. Accepts a well-formed list of run entries.
3. Rejects malformed entries — missing required fields, non-numeric
   `jsd`, non-positive `n`, `jsd` outside `[0, 1]`.
4. Warns (does not reject) when any entry's `jsd > 0.5`.
5. Stamps each entry's `calibration_count` on the registry's
   `default.json` from the length of the pack's calibration list.

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
