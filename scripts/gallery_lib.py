"""Shared helpers for building index.html's video/still sections from
order/videos.txt and order/stills.txt. Both process_incoming.py and
process_removed.py call rebuild_index_html() after they touch the order
files, so index.html always reflects whatever order those two text files
list, regardless of file names."""

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_HTML = ROOT / "index.html"
GALLERY_DIR = ROOT / "assets" / "gallery"
STILLS_DIR = ROOT / "assets" / "stills"
ORDER_DIR = ROOT / "order"
VIDEOS_ORDER = ORDER_DIR / "videos.txt"
STILLS_ORDER = ORDER_DIR / "stills.txt"


def slugify(stem):
    s = re.sub(r"[_\s]+", "-", stem.strip().lower())
    s = re.sub(r"[^a-z0-9\-]", "", s)
    return re.sub(r"-+", "-", s).strip("-")


def titleize(stem):
    words = re.split(r"[_\-\s]+", stem.strip())
    return " ".join(w.capitalize() for w in words if w)


def ffprobe_is_portrait(mp4_path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height",
         "-of", "json", str(mp4_path)],
        capture_output=True, text=True, check=True,
    ).stdout
    stream = json.loads(out)["streams"][0]
    return stream["height"] > stream["width"]


def read_order(path):
    if not path.exists():
        return []
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            lines.append(line)
    return lines


def write_order(path, lines):
    ORDER_DIR.mkdir(exist_ok=True)
    path.write_text("\n".join(lines) + "\n" if lines else "", encoding="utf-8")


def append_to_order(path, entry):
    lines = read_order(path)
    lines.append(entry)
    write_order(path, lines)


def remove_from_order(path, predicate):
    lines = read_order(path)
    kept = [l for l in lines if not predicate(l)]
    write_order(path, kept)
    return len(kept) != len(lines)


def build_video_block(order_line):
    parts = order_line.split(",")
    slug = parts[0].strip()
    modifiers = [p.strip() for p in parts[1:]]

    mp4_path = GALLERY_DIR / f"{slug}.mp4"
    if not mp4_path.exists():
        return None

    title = titleize(slug)
    portrait = ffprobe_is_portrait(mp4_path)

    entry_classes = "gallery-entry" + ("".join(f" {m}" for m in modifiers))
    item_classes = "gallery-item" + (" portrait" if portrait else "") + " fade-in video-facade"

    return (
        f'  <div class="{entry_classes}">\n'
        f'    <p class="video-title">{title}</p>\n'
        f'    <div class="{item_classes}" data-src="assets/gallery/{slug}.mp4">\n'
        f'      <img class="v-thumb" src="assets/gallery/{slug}.jpg" alt="" loading="lazy">\n'
        '      <button class="v-play" aria-label="Play video"><svg viewBox="0 0 24 24" width="20" height="20"><polygon points="6,4 20,12 6,20" fill="currentColor"/></svg></button>\n'
        "    </div>\n"
        "  </div>"
    )


def build_still_block(name):
    path = STILLS_DIR / name
    if not path.exists():
        return None
    return f'    <img class="still fade-in" src="assets/stills/{name}" alt="" loading="lazy">'


def replace_between_markers(html, start_marker, end_marker, new_content):
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker), re.DOTALL
    )
    if not pattern.search(html):
        raise RuntimeError(f"Could not find markers {start_marker} / {end_marker} in index.html")
    replacement = f"{start_marker}\n{new_content}\n  {end_marker}"
    return pattern.sub(replacement, html, count=1)


def rebuild_index_html():
    html = INDEX_HTML.read_text(encoding="utf-8")

    video_lines = read_order(VIDEOS_ORDER)
    video_blocks = [b for b in (build_video_block(l) for l in video_lines) if b]
    html = replace_between_markers(
        html, "<!-- VIDEOS:START -->", "<!-- VIDEOS:END -->", "\n".join(video_blocks)
    )

    still_lines = read_order(STILLS_ORDER)
    still_blocks = [b for b in (build_still_block(n) for n in still_lines) if b]
    html = replace_between_markers(
        html, "<!-- STILLS:START -->", "<!-- STILLS:END -->", "\n".join(still_blocks)
    )

    INDEX_HTML.write_text(html, encoding="utf-8")
