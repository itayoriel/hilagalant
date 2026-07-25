#!/usr/bin/env python3
"""Process new files dropped into assets/incoming/gallery or assets/incoming/stills:
compress them, insert them into index.html, and remove the raw upload."""

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_HTML = ROOT / "index.html"
GALLERY_INCOMING = ROOT / "assets" / "incoming" / "gallery"
STILLS_INCOMING = ROOT / "assets" / "incoming" / "stills"
GALLERY_DIR = ROOT / "assets" / "gallery"
STILLS_DIR = ROOT / "assets" / "stills"

VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".avi", ".mkv"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".webp"}

VIDEO_ENCODE_ARGS = [
    "-vf", "scale=720:-2,fps=30",
    "-c:v", "libx264", "-profile:v", "baseline", "-level", "3.1",
    "-preset", "slow", "-crf", "24",
    "-g", "60", "-keyint_min", "60", "-sc_threshold", "0",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "128k",
    "-movflags", "+faststart",
]


def slugify(stem):
    s = re.sub(r"[_\s]+", "-", stem.strip().lower())
    s = re.sub(r"[^a-z0-9\-]", "", s)
    return re.sub(r"-+", "-", s).strip("-")


def titleize(stem):
    words = re.split(r"[_\-\s]+", stem.strip())
    return " ".join(w.capitalize() for w in words if w)


def ffprobe_dimensions(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    stream = json.loads(out)["streams"][0]
    return stream["width"], stream["height"]


def unique_slug(base_slug):
    slug = base_slug
    i = 2
    while (GALLERY_DIR / f"{slug}.mp4").exists():
        slug = f"{base_slug}-{i}"
        i += 1
    return slug


def process_videos():
    if not GALLERY_INCOMING.exists():
        return []
    entries = []
    for src in sorted(GALLERY_INCOMING.iterdir()):
        if src.suffix.lower() not in VIDEO_EXTS:
            continue
        base_slug = slugify(src.stem)
        slug = unique_slug(base_slug)
        title = titleize(src.stem)
        width, height = ffprobe_dimensions(src)
        portrait = height > width

        out_mp4 = GALLERY_DIR / f"{slug}.mp4"
        out_jpg = GALLERY_DIR / f"{slug}.jpg"

        subprocess.run(
            ["ffmpeg", "-y", "-i", str(src), *VIDEO_ENCODE_ARGS, str(out_mp4)],
            check=True,
        )
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(out_mp4), "-ss", "00:00:01",
             "-vframes", "1", "-vf", "scale=480:-2", str(out_jpg)],
            check=True,
        )

        src.unlink()
        entries.append({"slug": slug, "title": title, "portrait": portrait})
        print(f"Processed video: {src.name} -> {slug} ({'portrait' if portrait else 'landscape'})")
    return entries


def next_still_number():
    existing = sorted(STILLS_DIR.glob("still-*.jpg"))
    nums = []
    for p in existing:
        m = re.match(r"still-(\d+)\.jpg", p.name)
        if m:
            nums.append(int(m.group(1)))
    return (max(nums) + 1) if nums else 1


def process_stills():
    if not STILLS_INCOMING.exists():
        return []
    entries = []
    n = next_still_number()
    for src in sorted(STILLS_INCOMING.iterdir()):
        if src.suffix.lower() not in IMAGE_EXTS:
            continue
        name = f"still-{n:02d}.jpg"
        out_jpg = STILLS_DIR / name

        subprocess.run(
            ["ffmpeg", "-y", "-i", str(src),
             "-vf", "scale='if(gt(iw,ih),1600,-2)':'if(gt(iw,ih),-2,1600)'",
             "-q:v", "4", str(out_jpg)],
            check=True,
        )

        src.unlink()
        entries.append({"name": name})
        print(f"Processed still: {src.name} -> {name}")
        n += 1
    return entries


def insert_video_entries(entries):
    if not entries:
        return
    html = INDEX_HTML.read_text(encoding="utf-8")
    blocks = []
    for e in entries:
        portrait_class = " portrait" if e["portrait"] else ""
        blocks.append(
            '  <div class="gallery-entry">\n'
            f'    <p class="video-title">{e["title"]}</p>\n'
            f'    <div class="gallery-item{portrait_class} fade-in video-facade" data-src="assets/gallery/{e["slug"]}.mp4">\n'
            f'      <img class="v-thumb" src="assets/gallery/{e["slug"]}.jpg" alt="" loading="lazy">\n'
            '      <button class="v-play" aria-label="Play video"><svg viewBox="0 0 24 24" width="20" height="20"><polygon points="6,4 20,12 6,20" fill="currentColor"/></svg></button>\n'
            "    </div>\n"
            "  </div>\n"
        )
    anchor = '</section>\n\n<section class="stills"'
    replacement = "".join(blocks) + anchor
    if anchor not in html:
        raise RuntimeError("Could not find gallery section anchor in index.html")
    html = html.replace(anchor, replacement, 1)
    INDEX_HTML.write_text(html, encoding="utf-8")


def insert_still_entries(entries):
    if not entries:
        return
    html = INDEX_HTML.read_text(encoding="utf-8")
    lines = "".join(
        f'    <img class="still fade-in" src="assets/stills/{e["name"]}" alt="" loading="lazy">\n'
        for e in entries
    )
    anchor = '  </div>\n</section>\n\n<div class="lightbox"'
    replacement = lines + anchor
    if anchor not in html:
        raise RuntimeError("Could not find stills grid anchor in index.html")
    html = html.replace(anchor, replacement, 1)
    INDEX_HTML.write_text(html, encoding="utf-8")


def main():
    video_entries = process_videos()
    still_entries = process_stills()
    insert_video_entries(video_entries)
    insert_still_entries(still_entries)
    if not video_entries and not still_entries:
        print("No new files found in assets/incoming/.")


if __name__ == "__main__":
    main()
