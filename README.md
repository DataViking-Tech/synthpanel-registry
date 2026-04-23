# synthpanel-registry

Curated index of community-authored packs for [SynthPanel](https://github.com/DataViking-Tech/SynthPanel),
a lightweight LLM-agnostic research harness for synthetic focus groups.

## What this is

A thin, human-reviewed catalog. The root `default.json` is the manifest
SynthPanel fetches at runtime to power `pack search` and `pack import gh:...`.
There is no runtime here — only JSON, a schema, and a PR workflow.

## How discovery works

1. A pack author drops a `synthpanel-pack.yaml` under
   `packs/<pack-id>/` in this repo (see [CONTRIBUTING.md](CONTRIBUTING.md)).
2. They open a submission issue, then a PR adding the pack directory and
   the regenerated `default.json`.
3. A reviewer checks the submission criteria in CONTRIBUTING and merges.
   `added_at` is stamped automatically from the pack directory's first
   commit by `scripts/build_registry.py`.
4. SynthPanel clients fetch
   `https://raw.githubusercontent.com/DataViking-Tech/synthpanel-registry/main/default.json`
   (cached 24h) to surface the pack via `synthpanel pack search` and to
   resolve registered `gh:owner/repo` imports.

## Manifest shape

See [`schema/default.schema.json`](schema/default.schema.json) for the
authoritative JSON Schema. Validation runs in CI on every PR.

## Adding a pack

1. Drop your pack YAML at `packs/<pack-id>/synthpanel-pack.yaml` (one
   directory per pack; the directory name must equal the pack's `id:`).
2. Regenerate the registry index locally:
   ```
   pip install pyyaml jsonschema synthpanel
   python scripts/build_registry.py
   ```
   The script walks every `packs/*/synthpanel-pack.yaml`, validates it
   against synthpanel's persona-pack schema, and rewrites `default.json`
   deterministically (stable sort, canonical JSON).
3. Commit both the new pack and the regenerated `default.json` in your PR.

CI runs `python scripts/build_registry.py --check` on every PR. Any pack
that fails persona-pack validation or any PR whose `default.json` is stale
relative to its `packs/` tree will fail the `registry-build` status check.

## Removal

Authors may request takedown via the [pack removal issue
template](.github/ISSUE_TEMPLATE/pack-removal.yml).
