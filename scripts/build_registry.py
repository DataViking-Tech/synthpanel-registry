#!/usr/bin/env python3
"""Build default.json from packs/*/synthpanel-pack.yaml.

Walks every `packs/<id>/synthpanel-pack.yaml`, validates each pack against
synthpanel's persona-pack schema (via `synth_panel.mcp.data.validate_persona_pack`),
and emits a registry index matching `schema/default.schema.json`.

Output is deterministic: stable sort by id, canonical JSON (2-space indent,
sorted keys, trailing newline). `generated_at` is pinned to the newest
commit touching `packs/`, and each entry's `added_at` comes from the pack
directory's first commit — so two runs on the same checkout produce
byte-identical output, and unrelated edits (docs, scripts, workflows) do
not mark `default.json` stale.

Usage:
    python scripts/build_registry.py           # write default.json
    python scripts/build_registry.py --check   # verify default.json is fresh
"""

from __future__ import annotations

import argparse
import datetime as _dt
import difflib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKS_DIR = REPO_ROOT / "packs"
OUTPUT = REPO_ROOT / "default.json"
REGISTRY_REPO = "DataViking-Tech/synthpanel-registry"
SCHEMA_VERSION = 1

CALIBRATION_REQUIRED_FIELDS = ("dataset", "question", "jsd", "n", "calibrated_at")
# Soft ceiling above which we surface a CI warning. Packs that calibrate poorly
# are still valid — JSD > 0.5 means "almost orthogonal to the human baseline,"
# which is worth a sanity check from the author but does not fail the build.
CALIBRATION_JSD_WARN = 0.5


class PackError(ValueError):
    """Raised when a pack is malformed. Message names the pack dir."""


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _first_commit_date(path: Path) -> str:
    """Return the YYYY-MM-DD of the earliest commit that added `path`.

    Uses committer-date so it survives rebases onto a fresh mainline. Requires
    a full-depth checkout (the CI job sets `fetch-depth: 0`).
    """
    rel = path.relative_to(REPO_ROOT).as_posix()
    out = _git("log", "--diff-filter=A", "--follow", "--format=%cs", "--", rel).strip()
    dates = [line for line in out.splitlines() if line.strip()]
    if not dates:
        raise PackError(
            f"{rel}: no git history found; CI must checkout with fetch-depth: 0"
        )
    return dates[-1]


def _packs_generated_at() -> str:
    """Committer date of the newest commit touching `packs/`, as UTC ISO8601.

    Pinned to pack history (not HEAD) so regenerating after an unrelated
    script or docs change doesn't mark default.json stale. A new/edited
    pack bumps this; everything else leaves it alone.
    """
    raw = _git("log", "-1", "--format=%cI", "--", "packs").strip()
    if not raw:
        raise PackError("no git history for packs/; CI must checkout with fetch-depth: 0")
    dt = datetime.fromisoformat(raw).astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise PackError(f"{path.parent.name}: pack yaml must be a mapping at top level")
    return data


def _normalize_author(raw: Any, pack_name: str) -> dict[str, str]:
    """Coerce pack `author` (string handle or {github: ...}) to schema shape."""
    if isinstance(raw, str):
        handle = raw.strip()
    elif isinstance(raw, dict):
        handle = str(raw.get("github", "")).strip()
    else:
        raise PackError(f"{pack_name}: author must be a string or a mapping with 'github'")
    if not handle:
        raise PackError(f"{pack_name}: author.github is empty")
    return {"github": handle}


def _normalize_description(raw: Any, pack_name: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise PackError(f"{pack_name}: description must be a non-empty string")
    return " ".join(raw.split())


def _validate_calibration(raw: Any, pack_id: str) -> list[dict[str, Any]]:
    """Validate a pack's optional `calibration:` block and return the entries.

    Accepted shapes:
      * field absent or `null` → uncalibrated, returns []
      * list of mappings, each carrying at minimum
        (dataset, question, jsd, n, calibrated_at)

    Raises PackError on malformed entries. Emits a stderr warning (not an
    error) when an entry's jsd > 0.5 — bad fits are still valid registry
    entries, but the author probably wants to know.
    """
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise PackError(
            f"{pack_id}: calibration must be a list of run entries (or null/absent)"
        )
    out: list[dict[str, Any]] = []
    for idx, entry in enumerate(raw):
        if not isinstance(entry, dict):
            raise PackError(
                f"{pack_id}: calibration[{idx}] must be a mapping"
            )
        missing = [k for k in CALIBRATION_REQUIRED_FIELDS if entry.get(k) in (None, "")]
        if missing:
            raise PackError(
                f"{pack_id}: calibration[{idx}] missing required field(s): "
                f"{', '.join(missing)}"
            )
        jsd_raw = entry["jsd"]
        if not isinstance(jsd_raw, (int, float)) or isinstance(jsd_raw, bool):
            raise PackError(
                f"{pack_id}: calibration[{idx}].jsd must be a number, got {type(jsd_raw).__name__}"
            )
        jsd = float(jsd_raw)
        if not 0.0 <= jsd <= 1.0:
            raise PackError(
                f"{pack_id}: calibration[{idx}].jsd must be within [0, 1], got {jsd}"
            )
        n_raw = entry["n"]
        if not isinstance(n_raw, int) or isinstance(n_raw, bool) or n_raw <= 0:
            raise PackError(
                f"{pack_id}: calibration[{idx}].n must be a positive integer"
            )
        if not isinstance(entry["dataset"], str) or not entry["dataset"].strip():
            raise PackError(f"{pack_id}: calibration[{idx}].dataset must be a non-empty string")
        if not isinstance(entry["question"], str) or not entry["question"].strip():
            raise PackError(f"{pack_id}: calibration[{idx}].question must be a non-empty string")
        ts = entry["calibrated_at"]
        # PyYAML auto-coerces unquoted ISO 8601 to datetime/date; accept either.
        if isinstance(ts, (_dt.datetime, _dt.date)):
            pass
        elif isinstance(ts, str) and ts.strip():
            pass
        else:
            raise PackError(
                f"{pack_id}: calibration[{idx}].calibrated_at must be an ISO 8601 timestamp"
            )
        if jsd > CALIBRATION_JSD_WARN:
            print(
                f"warning: {pack_id}: calibration[{idx}] jsd={jsd:.3f} exceeds "
                f"{CALIBRATION_JSD_WARN} (poor fit vs human baseline) — "
                f"dataset={entry['dataset']} question={entry['question']}",
                file=sys.stderr,
            )
        out.append(entry)
    return out


def _validate_and_build_entry(pack_dir: Path) -> dict[str, Any]:
    """Validate one pack directory and return its default.json entry."""
    # Import here so a missing dep yields a clear error path, not an import-time crash.
    from synth_panel.mcp.data import PackValidationError, validate_persona_pack

    yaml_path = pack_dir / "synthpanel-pack.yaml"
    if not yaml_path.is_file():
        raise PackError(f"{pack_dir.name}: missing synthpanel-pack.yaml")

    data = _load_yaml(yaml_path)
    pack_id = str(data.get("id", "")).strip()
    if not pack_id:
        raise PackError(f"{pack_dir.name}: pack yaml missing required field 'id'")
    if pack_id != pack_dir.name:
        raise PackError(
            f"{pack_dir.name}: pack id {pack_id!r} does not match directory name"
        )

    personas = data.get("personas")
    if personas is None:
        raise PackError(f"{pack_id}: pack yaml missing required field 'personas'")
    try:
        validate_persona_pack(personas)
    except PackValidationError as exc:
        raise PackError(f"{pack_id}: invalid persona pack — {exc}") from exc

    calibrations = _validate_calibration(data.get("calibration"), pack_id)

    entry: dict[str, Any] = {
        "id": pack_id,
        "kind": "persona",
        "name": str(data["name"]).strip() if data.get("name") else pack_id,
        "description": _normalize_description(data.get("description"), pack_id),
        "repo": REGISTRY_REPO,
        "path": f"packs/{pack_id}/synthpanel-pack.yaml",
        "author": _normalize_author(data.get("author"), pack_id),
        "added_at": _first_commit_date(pack_dir),
        "calibration": None,
    }
    version = data.get("version")
    if version not in (None, ""):
        entry["version"] = str(version)
    if calibrations:
        entry["calibration_count"] = len(calibrations)
    return entry


def build() -> dict[str, Any]:
    if not PACKS_DIR.is_dir():
        raise PackError(f"packs directory not found at {PACKS_DIR}")

    entries: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for pack_dir in sorted(p for p in PACKS_DIR.iterdir() if p.is_dir()):
        entry = _validate_and_build_entry(pack_dir)
        if entry["id"] in seen_ids:
            raise PackError(f"{entry['id']}: duplicate pack id across packs/")
        seen_ids.add(entry["id"])
        entries.append(entry)

    entries.sort(key=lambda e: e["id"])
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _packs_generated_at(),
        "packs": entries,
    }


def render(manifest: dict[str, Any]) -> str:
    """Canonical JSON: 2-space indent, sorted keys, trailing newline."""
    return json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def cmd_check() -> int:
    fresh = render(build())
    if not OUTPUT.is_file():
        print(f"error: {OUTPUT.name} is missing; run scripts/build_registry.py", file=sys.stderr)
        return 1
    existing = OUTPUT.read_text(encoding="utf-8")
    if existing == fresh:
        return 0
    print(f"error: {OUTPUT.name} is stale; run scripts/build_registry.py to regenerate", file=sys.stderr)
    diff = difflib.unified_diff(
        existing.splitlines(keepends=True),
        fresh.splitlines(keepends=True),
        fromfile=f"{OUTPUT.name} (on disk)",
        tofile=f"{OUTPUT.name} (expected)",
        n=3,
    )
    sys.stderr.writelines(diff)
    return 1


def cmd_write() -> int:
    OUTPUT.write_text(render(build()), encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(REPO_ROOT)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate packs, rebuild in-memory, and fail if default.json is stale",
    )
    args = parser.parse_args(argv)
    try:
        return cmd_check() if args.check else cmd_write()
    except PackError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as exc:
        print(f"error: git command failed: {exc.stderr.strip() or exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
