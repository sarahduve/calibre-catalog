#!/usr/bin/env python3
"""Export Calibre library to a static HTML catalog."""

import json
import os
import subprocess
import sys
from pathlib import Path

# ============================================================
# CONFIGURE THESE before first use
# ============================================================
CALIBRE_LIBRARY_PATH = "~/Calibre Library"
CALIBRE_CONTENT_SERVER = "http://localhost:8080"

CALIBREDB = "/Applications/calibre.app/Contents/MacOS/calibredb"
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = PROJECT_DIR / "template.html"
OUTPUT_DIR = PROJECT_DIR / "docs"
OUTPUT_PATH = OUTPUT_DIR / "index.html"

FIELDS = "title,pubdate,authors,formats,tags,series,series_index"


def export_books() -> list[dict]:
    """Run calibredb and return parsed book data.

    Tries the content server first (works when Calibre is open),
    then falls back to the library path (works when Calibre is closed).
    """
    # Try content server first
    result = subprocess.run(
        [
            CALIBREDB, "list",
            "--fields", FIELDS,
            "--for-machine",
            "--with-library", CALIBRE_CONTENT_SERVER,
        ],
        capture_output=True,
        text=True,
    )

    # Fall back to file path
    if result.returncode != 0:
        print(f"Content server failed: {result.stderr.strip()}", file=sys.stderr)
        print("Trying library path directly.")
        library = os.path.expanduser(CALIBRE_LIBRARY_PATH)
        if not os.path.isdir(library):
            print(f"Error: Calibre library not found at {library}", file=sys.stderr)
            print("Update CALIBRE_LIBRARY_PATH in export.py", file=sys.stderr)
            sys.exit(1)

        result = subprocess.run(
            [
                CALIBREDB, "list",
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
        for fmt in (b.get("formats") or []):
            # Content server returns bare names like "EPUB";
            # file path access returns full paths like "/path/to/book.epub"
            ext = os.path.splitext(fmt)[1]
            if ext:
                formats.append(ext.lstrip(".").upper())
            else:
                formats.append(fmt.upper())

        books.append({
            "title": b.get("title", "Untitled"),
            "authors": b.get("authors", "Unknown"),
            "published": b.get("pubdate") or b.get("published") or "",
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


def encrypt_html() -> None:
    """Encrypt the output HTML with pagecrypt if a password is set."""
    password = os.environ.get("PAGECRYPT_PASSWORD")
    if not password:
        print("PAGECRYPT_PASSWORD not set — skipping encryption.", file=sys.stderr)
        return

    subprocess.run(
        ["npx", "pagecrypt", str(OUTPUT_PATH), str(OUTPUT_PATH), password],
        check=True,
    )
    print("Encrypted docs/index.html with pagecrypt.")


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
    encrypt_html()
    git_commit_and_push()


if __name__ == "__main__":
    main()
