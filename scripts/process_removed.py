#!/usr/bin/env python3
"""Given a list of deleted file paths (one per line, on stdin or as argv),
remove their matching entries from index.html and clean up any paired file
(e.g. deleting a video's .mp4 also removes its .jpg poster, and vice versa)."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_HTML = ROOT / "index.html"


def get_deleted_paths():
    if len(sys.argv) > 1:
        raw = "\n".join(sys.argv[1:])
    else:
        raw = sys.stdin.read()
    raw = raw.lstrip("﻿")
    return [line.strip() for line in raw.splitlines() if line.strip()]


def handle_gallery_deletion(html, rel_path):
    p = Path(rel_path)
    slug = p.stem
    other_ext = ".jpg" if p.suffix == ".mp4" else ".mp4"
    other = ROOT / "assets" / "gallery" / f"{slug}{other_ext}"
    if other.exists():
        other.unlink()
        print(f"Also removed paired file: {other.relative_to(ROOT)}")

    pattern = re.compile(
        r'[ \t]*<div class="gallery-entry[^"]*">\s*'
        r'<p class="video-title">[^<]*</p>\s*'
        rf'<div class="gallery-item[^"]*" data-src="assets/gallery/{re.escape(slug)}\.mp4">.*?'
        r"</div>\s*</div>\n?",
        re.DOTALL,
    )
    new_html, count = pattern.subn("", html)
    if count:
        print(f"Removed gallery entry for: {slug}")
    return new_html


def handle_stills_deletion(html, rel_path):
    name = Path(rel_path).name
    pattern = re.compile(
        rf'[ \t]*<img class="still fade-in" src="assets/stills/{re.escape(name)}"[^>]*>\n?'
    )
    new_html, count = pattern.subn("", html)
    if count:
        print(f"Removed still entry for: {name}")
    return new_html


def main():
    deleted = get_deleted_paths()
    if not deleted:
        print("No deleted files passed in.")
        return

    html = INDEX_HTML.read_text(encoding="utf-8")
    for rel_path in deleted:
        norm = rel_path.replace("\\", "/")
        if norm.startswith("assets/gallery/"):
            html = handle_gallery_deletion(html, norm)
        elif norm.startswith("assets/stills/"):
            html = handle_stills_deletion(html, norm)

    INDEX_HTML.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
