#!/usr/bin/env python3
"""Process new files dropped into assets/incoming/gallery or assets/incoming/stills:
compress them, append them to the order files, and rebuild index.html."""

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gallery_lib as lib

GALLERY_INCOMING = lib.ROOT / "assets" / "incoming" / "gallery"
STILLS_INCOMING = lib.ROOT / "assets" / "incoming" / "stills"

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


def unique_slug(base_slug):
    slug = base_slug
    i = 2
    while (lib.GALLERY_DIR / f"{slug}.mp4").exists():
        slug = f"{base_slug}-{i}"
        i += 1
    return slug


def process_videos():
    if not GALLERY_INCOMING.exists():
        return
    for src in sorted(GALLERY_INCOMING.iterdir()):
        if src.suffix.lower() not in VIDEO_EXTS:
            continue
        slug = unique_slug(lib.slugify(src.stem))

        out_mp4 = lib.GALLERY_DIR / f"{slug}.mp4"
        out_jpg = lib.GALLERY_DIR / f"{slug}.jpg"

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
        lib.append_to_order(lib.VIDEOS_ORDER, slug)
        print(f"Added video: {src.name} -> {slug}")


def next_still_number():
    existing = sorted(lib.STILLS_DIR.glob("still-*.jpg"))
    nums = []
    for p in existing:
        m = re.match(r"still-(\d+)\.jpg", p.name)
        if m:
            nums.append(int(m.group(1)))
    return (max(nums) + 1) if nums else 1


def process_stills():
    if not STILLS_INCOMING.exists():
        return
    n = next_still_number()
    for src in sorted(STILLS_INCOMING.iterdir()):
        if src.suffix.lower() not in IMAGE_EXTS:
            continue
        name = f"still-{n:02d}.jpg"
        out_jpg = lib.STILLS_DIR / name

        subprocess.run(
            ["ffmpeg", "-y", "-i", str(src),
             "-vf", "scale='if(gt(iw,ih),1600,-2)':'if(gt(iw,ih),-2,1600)'",
             "-q:v", "4", str(out_jpg)],
            check=True,
        )

        src.unlink()
        lib.append_to_order(lib.STILLS_ORDER, name)
        print(f"Added still: {src.name} -> {name}")
        n += 1


def main():
    process_videos()
    process_stills()
    lib.rebuild_index_html()


if __name__ == "__main__":
    main()
