"""Inline the data files into one self-contained HTML page.

Usage: python3 -I scripts/bundle.py index.html dist/proof-sheet.html
"""

import pathlib
import sys

src = pathlib.Path(sys.argv[1])
html = src.read_text()
for name in ("breads.js", "schedule.js"):
    data = (src.parent / "data" / name).read_text()
    html = html.replace(f'<script src="data/{name}"></script>', f"<script>\n{data}\n</script>")
out = pathlib.Path(sys.argv[2])
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(html)
