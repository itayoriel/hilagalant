#!/usr/bin/env python3
"""Given a list of deleted file paths (one per line, on stdin or as argv),
remove them from the order files, clean up any paired file (e.g. deleting
a video's .mp4 also removes its .jpg poster, and vice versa), and rebuild
index.html from whatever the order files say is left."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gallery_lib as lib


def get_deleted_paths():
    if len(sys.argv) > 1:
        raw = "\n".join(sys.argv[1:])
    else:
        raw = sys.stdin.read()
    raw = raw.lstrip("﻿")
    return [line.strip() for line in raw.splitlines() if line.strip()]


def handle_gallery_deletion(rel_path):
    p = Path(rel_path)
    slug = p.stem
    other_ext = ".jpg" if p.suffix == ".mp4" else ".mp4"
    other = lib.GALLERY_DIR / f"{slug}{other_ext}"
    if other.exists():
        other.unlink()
        print(f"Also removed paired file: {other.relative_to(lib.ROOT)}")

    changed = lib.remove_from_order(
        lib.VIDEOS_ORDER, lambda line: line.split(",")[0].strip() == slug
    )
    if changed:
        print(f"Removed from order/videos.txt: {slug}")


def handle_stills_deletion(rel_path):
    name = Path(rel_path).name
    changed = lib.remove_from_order(lib.STILLS_ORDER, lambda line: line.strip() == name)
    if changed:
        print(f"Removed from order/stills.txt: {name}")


def main():
    deleted = get_deleted_paths()
    if not deleted:
        print("No deleted files passed in.")
        return

    for rel_path in deleted:
        norm = rel_path.replace("\\", "/")
        if norm.startswith("assets/gallery/"):
            handle_gallery_deletion(norm)
        elif norm.startswith("assets/stills/"):
            handle_stills_deletion(norm)

    lib.rebuild_index_html()


if __name__ == "__main__":
    main()
