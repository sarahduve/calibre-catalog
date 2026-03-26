# Calibre Catalog

A mobile-first, searchable catalog of your Calibre ebook library. Exports your
library to a static site you can check from your phone.

## Setup

### Prerequisites

- Python 3
- [Calibre](https://calibre-ebook.com/) installed (provides the `calibredb` CLI)
- Optional: Node.js (for PageCrypt password protection)

### Configure

Edit `export.py` and set `CALIBRE_LIBRARY_PATH` to your Calibre library location:

```python
# ============================================================
# CONFIGURE THIS: path to your Calibre library
# ============================================================
CALIBRE_LIBRARY_PATH = "/path/to/your/Calibre Library"
```

The default macOS path is `~/Calibre Library`.

### Export your library

```bash
python3 export.py
```

This generates `docs/index.html` with your full library embedded.

### Optional: password-protect the page

```bash
npx pagecrypt docs/index.html docs/index.html YOUR_PASSWORD
```

### Deploy

Push to GitHub and enable GitHub Pages from the `docs/` folder in repo settings.

### Preview with sample data

To see the site without Calibre installed:

```bash
python3 -c "
from pathlib import Path
t = Path('template.html').read_text()
d = Path('sample_books.json').read_text()
Path('docs').mkdir(exist_ok=True)
Path('docs/index.html').write_text(t.replace('__BOOKS_DATA__', d))
"
open docs/index.html
```

### Keep it updated

Run `python3 export.py` whenever you add new books. The script commits and
pushes automatically. Or set up a launch agent to run it on a schedule — see
`launchd.example.plist`.
