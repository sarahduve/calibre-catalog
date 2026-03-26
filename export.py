#!/usr/bin/env python3
"""Export Calibre library to a static HTML catalog."""

import json
import os
import subprocess
import sys
from pathlib import Path

# ============================================================
# CONFIGURE THIS: path to your Calibre library
# ============================================================
CALIBRE_LIBRARY_PATH = "/path/to/your/Calibre Library"
# Common macOS default: os.path.expanduser("~/Calibre Library")
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = PROJECT_DIR / "template.html"
OUTPUT_DIR = PROJECT_DIR / "docs"
OUTPUT_PATH = OUTPUT_DIR / "index.html"

FIELDS = "title,authors,formats,tags,series,series_index"


def export_books() -> list[dict]:
    """Run calibredb and return parsed book data."""
    library = os.path.expanduser(CALIBRE_LIBRARY_PATH)
    if not os.path.isdir(library):
        print(f"Error: Calibre library not found at {library}", file=sys.stderr)
        print("Update CALIBRE_LIBRARY_PATH in export.py", file=sys.stderr)
        sys.exit(1)

    result = subprocess.run(
        [
            "calibredb", "list",
            "--fields", FIELDS,
            "--for-machine",
            "--library-path", library,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"calibredb failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    raw_books = json.loads(result.stdout)
    books = []
    for b in raw_books:
        formats = []
        for fmt_path in (b.get("formats") or []):
            ext = os.path.splitext(fmt_path)[1].lstrip(".").upper()
            if ext:
                formats.append(ext)

        books.append({
            "title": b.get("title", "Untitled"),
            "authors": b.get("authors", "Unknown"),
            "formats": sorted(set(formats)),
            "tags": sorted(b.get("tags", []) or []),
            "series": b.get("series") or "",
            "series_index": b.get("series_index"),
        })

    books.sort(key=lambda x: x["title"].lower())
    return books


def build_html(books: list[dict]) -> None:
    """Inject book data into template and write to docs/."""
    template = TEMPLATE_PATH.read_text()
    html = template.replace("__BOOKS_DATA__", json.dumps(books))
    OUTPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_PATH.write_text(html)
    print(f"Wrote {len(books)} books to {OUTPUT_PATH}")


def git_commit_and_push() -> None:
    """Commit the updated catalog and push if a remote exists."""
    os.chdir(PROJECT_DIR)
    # Stage the output
    subprocess.run(["git", "add", "docs/index.html"], check=True)

    # Check if there are changes to commit
    diff = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if diff.returncode == 0:
        print("No changes to commit.")
        return

    subprocess.run(
        ["git", "commit", "-m", "Update library catalog"],
        check=True,
    )

    # Push if remote exists
    remote = subprocess.run(
        ["git", "remote"],
        capture_output=True,
        text=True,
    )
    if remote.stdout.strip():
        subprocess.run(["git", "push"], check=True)
        print("Pushed to remote.")
    else:
        print("No remote configured — skipping push.")


def main() -> None:
    books = export_books()
    build_html(books)
    git_commit_and_push()


if __name__ == "__main__":
    main()
