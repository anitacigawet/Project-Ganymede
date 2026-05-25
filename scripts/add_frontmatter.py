#!/usr/bin/env python3
"""Add YAML frontmatter to every markdown file under docs/.

Idempotent: skips any file that already has a frontmatter block at line 1.

Run from the Project Ganymede repo root:

    python scripts/add_frontmatter.py [--dry-run]

Frontmatter shape, per the canvas viewer specification:

    ---
    title: "<H1 text>"
    type: "<hub | cluster-head | concept | architecture-component | protocol | history-record>"
    status: "<core | active | speculative | draft | archived>"
    tags: ["<tag>", ...]
    color_id: "<1-6 cluster color index>"
    ---
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

DOCS_DIR = Path("docs")


# Folder → metadata mapping. Keys are POSIX-style paths relative to docs/.
# Most-specific keys are listed first; the lookup picks the longest matching prefix.
FOLDER_MAP: dict[str, dict] = {
    "concepts/Mirror_Protocol": {
        "type": "concept",
        "status": "archived",
        "tags": ["mirror-protocol", "historical"],
        "color_id": "5",
    },
    "concepts": {
        "type": "concept",
        "status": "active",
        "tags": ["concepts"],
        "color_id": "5",
    },
    "protocols": {
        "type": "protocol",
        "status": "active",
        "tags": ["protocols", "operational"],
        "color_id": "6",
    },
    "foundations": {
        "type": "concept",
        "status": "core",
        "tags": ["foundations", "9d-framework"],
        "color_id": "4",
    },
    "experiments/pathways": {
        "type": "concept",
        "status": "active",
        "tags": ["pathway", "experiments"],
        "color_id": "3",
    },
    "experiments/runs/Powell_Cleanroom": {
        "type": "history-record",
        "status": "active",
        "tags": ["run", "experiments", "powell-cleanroom"],
        "color_id": "1",
    },
    "experiments/runs/polymarket": {
        "type": "history-record",
        "status": "active",
        "tags": ["run", "experiments", "polymarket"],
        "color_id": "1",
    },
    "experiments/runs": {
        "type": "history-record",
        "status": "active",
        "tags": ["run", "experiments"],
        "color_id": "1",
    },
    "experiments/scripts": {
        "type": "architecture-component",
        "status": "archived",
        "tags": ["scripts", "experiments", "archived"],
        "color_id": "1",
    },
    "experiments": {
        "type": "concept",
        "status": "active",
        "tags": ["experiments", "methodology"],
        "color_id": "3",
    },
    "integration/examples": {
        "type": "architecture-component",
        "status": "active",
        "tags": ["integration", "examples"],
        "color_id": "2",
    },
    "integration": {
        "type": "architecture-component",
        "status": "active",
        "tags": ["integration", "api"],
        "color_id": "2",
    },
    "history": {
        "type": "history-record",
        "status": "active",
        "tags": ["history", "chronological"],
        "color_id": "6",
    },
    "learnings": {
        "type": "history-record",
        "status": "active",
        "tags": ["learnings", "operational"],
        "color_id": "6",
    },
    "visions": {
        "type": "concept",
        "status": "speculative",
        "tags": ["visions", "productisation"],
        "color_id": "3",
    },
    "brainstorming": {
        "type": "concept",
        "status": "speculative",
        "tags": ["brainstorming"],
        "color_id": "1",
    },
}

TOP_LEVEL_OVERRIDES: dict[str, dict] = {
    "README.md": {
        "type": "hub",
        "status": "active",
        "tags": ["hub"],
        "color_id": "4",
    },
    "OVERVIEW.md": {
        "type": "hub",
        "status": "active",
        "tags": ["hub", "overview"],
        "color_id": "4",
    },
    "GLOSSARY.md": {
        "type": "concept",
        "status": "active",
        "tags": ["glossary", "vocabulary"],
        "color_id": "4",
    },
    "Project_In_My_Words.md": {
        "type": "concept",
        "status": "active",
        "tags": ["personal-voice", "explanation"],
        "color_id": "4",
    },
}


def has_frontmatter(content: str) -> bool:
    return content.startswith("---\n") or content.startswith("---\r\n")


def extract_title(content: str, filename: str) -> str:
    m = re.search(r"^#\s+(.+?)\s*$", content, re.MULTILINE)
    if m:
        return m.group(1).strip()
    # Fallback: filename without extension, underscores → spaces.
    return filename.replace("_", " ").rsplit(".", 1)[0]


def get_metadata(rel_path: Path) -> dict:
    name = rel_path.name
    parent_posix = rel_path.parent.as_posix()

    # Top-level files (relative parent is "." or "").
    if parent_posix in (".", ""):
        if name in TOP_LEVEL_OVERRIDES:
            return dict(TOP_LEVEL_OVERRIDES[name])
        # Unknown top-level file.
        return {
            "type": "hub",
            "status": "active",
            "tags": [name.rsplit(".", 1)[0]],
            "color_id": "4",
        }

    # Match the longest folder prefix in FOLDER_MAP.
    best_key = None
    best_len = -1
    for key in FOLDER_MAP:
        # Match either exact folder or prefix-with-/ to avoid matching "concepts" against "concepts_extra".
        if parent_posix == key or parent_posix.startswith(key + "/"):
            if len(key) > best_len:
                best_key = key
                best_len = len(key)

    if best_key is not None:
        meta = dict(FOLDER_MAP[best_key])
        # Preserve list semantics for tags.
        meta["tags"] = list(meta["tags"])
    else:
        # Generic fallback.
        meta = {
            "type": "concept",
            "status": "active",
            "tags": [],
            "color_id": "5",
        }

    # Folder README.md files are cluster heads regardless of folder.
    if name == "README.md":
        meta["type"] = "cluster-head"
        meta["tags"].append("cluster-head")

    return meta


def yaml_string_value(value: str) -> str:
    # Escape backslashes and double-quotes so the generated YAML stays valid.
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def make_frontmatter(meta: dict, title: str) -> str:
    tags = meta.get("tags", []) or []
    tag_str = "[" + ", ".join(yaml_string_value(t) for t in tags) + "]"
    return (
        "---\n"
        f"title: {yaml_string_value(title)}\n"
        f"type: {yaml_string_value(meta['type'])}\n"
        f"status: {yaml_string_value(meta['status'])}\n"
        f"tags: {tag_str}\n"
        f"color_id: {yaml_string_value(meta['color_id'])}\n"
        "---\n\n"
    )


def process_file(path: Path, dry_run: bool = False) -> str:
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = path.read_text(encoding="utf-8", errors="replace")

    if has_frontmatter(content):
        return f"SKIP (has frontmatter): {path}"

    rel = path.relative_to(DOCS_DIR)
    meta = get_metadata(rel)
    title = extract_title(content, path.name)
    fm = make_frontmatter(meta, title)

    new_content = fm + content
    if not dry_run:
        path.write_text(new_content, encoding="utf-8", newline="\n")
    return (
        f"ADDED: {path} | title={title!r} "
        f"type={meta['type']} status={meta['status']} color={meta['color_id']}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change without writing any files.",
    )
    args = parser.parse_args()

    if not DOCS_DIR.is_dir():
        raise SystemExit(
            f"docs/ not found in {Path.cwd()} — run from the Project Ganymede repo root"
        )

    paths = sorted(DOCS_DIR.rglob("*.md"))
    skipped = added = 0
    for p in paths:
        line = process_file(p, args.dry_run)
        print(line)
        if line.startswith("SKIP"):
            skipped += 1
        else:
            added += 1

    print(
        f"\nProcessed {len(paths)} files (dry-run={args.dry_run}). "
        f"Added: {added}. Skipped: {skipped}."
    )


if __name__ == "__main__":
    main()
