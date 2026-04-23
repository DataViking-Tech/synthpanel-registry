# synthpanel-registry

Curated index of community-authored packs for [SynthPanel](https://github.com/DataViking-Tech/SynthPanel),
a lightweight LLM-agnostic research harness for synthetic focus groups.

## What this is

A thin, human-reviewed catalog. The root `default.json` is the manifest
SynthPanel fetches at runtime to power `pack search` and `pack import gh:...`.
There is no runtime here — only JSON, a schema, and a PR workflow.

## How discovery works

1. A pack author publishes a `synthpanel-pack.yaml` in a public GitHub repo.
2. They open a submission issue, then a PR adding a `packs/<pack-id>.json`
   entry to this repo (see [CONTRIBUTING.md](CONTRIBUTING.md)).
3. A reviewer checks the six criteria in CONTRIBUTING, stamps `added_at`,
   and merges.
4. SynthPanel clients fetch
   `https://raw.githubusercontent.com/DataViking-Tech/synthpanel-registry/main/default.json`
   (cached 24h) to surface the pack via `synthpanel pack search` and to
   resolve registered `gh:owner/repo` imports.

## Manifest shape

See [`schema/default.schema.json`](schema/default.schema.json) for the
authoritative JSON Schema. Validation runs in CI on every PR.

## Removal

Authors may request takedown via the [pack removal issue
template](.github/ISSUE_TEMPLATE/pack-removal.yml).
