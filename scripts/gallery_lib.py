"""Shared helpers for building index.html from the data files:
order/videos.txt, order/stills.txt (display order) and content/site.json
(hero text, about text, custom video titles). Everything between the
<!-- X:START --> / <!-- X:END --> markers in index.html is generated."""

import hashlib
import html as html_lib
import json
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_HTML = ROOT / "index.html"
GALLERY_DIR = ROOT / "assets" / "gallery"
STILLS_DIR = ROOT / "assets" / "stills"
ORDER_DIR = ROOT / "order"
VIDEOS_ORDER = ORDER_DIR / "videos.txt"
STILLS_ORDER = ORDER_DIR / "stills.txt"
SITE_JSON = ROOT / "content" / "site.json"
STYLES_JSON = ROOT / "edit" / "styles.json"

PLAY_BUTTON = (
    '<button class="v-play" aria-label="Play video"><svg viewBox="0 0 24 24" '
    'width="20" height="20"><polygon points="6,4 20,12 6,20" fill="currentColor"/></svg></button>'
)


def slugify(stem):
    s = re.sub(r"[_\s]+", "-", stem.strip().lower())
    s = re.sub(r"[^a-z0-9\-]", "", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or f"item-{int(time.time() * 1000)}"


def titleize(stem):
    words = re.split(r"[_\-\s]+", stem.strip())
    return " ".join(w.capitalize() for w in words if w)


def esc(text):
    return html_lib.escape(text, quote=False)


def ffprobe_is_portrait(mp4_path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height",
         "-of", "json", str(mp4_path)],
        capture_output=True, text=True, check=True,
    ).stdout
    stream = json.loads(out)["streams"][0]
    return stream["height"] > stream["width"]


def ffprobe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    return float(json.loads(out)["format"].get("duration") or 0)


def image_brightness(path):
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-vf", "signalstats,metadata=print:file=-", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stdout
    m = re.search(r"lavfi\.signalstats\.YAVG=([\d.]+)", out)
    return float(m.group(1)) if m else 0.0


def make_poster(mp4_path, jpg_path, min_brightness=40):
    """Pick a cover frame that isn't black (clips often open with a fade from black)."""
    duration = ffprobe_duration(mp4_path)
    best = None
    for fraction in (0.2, 0.35, 0.5, 0.65):
        candidate = jpg_path.with_name(f"{jpg_path.stem}.cand{int(fraction * 100)}.jpg")
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-ss", f"{duration * fraction:.2f}", "-i", str(mp4_path),
             "-vf", "thumbnail=45,scale=480:-2", "-frames:v", "1", "-update", "1", str(candidate)],
            check=True,
        )
        brightness = image_brightness(candidate)
        if best is None or brightness > best[0]:
            if best:
                best[1].unlink(missing_ok=True)
            best = (brightness, candidate)
        else:
            candidate.unlink(missing_ok=True)
        if brightness >= min_brightness:
            break
    best[1].replace(jpg_path)


def make_poster_at(mp4_path, jpg_path, seconds):
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-ss", f"{max(0.0, seconds):.2f}", "-i", str(mp4_path),
         "-frames:v", "1", "-vf", "scale=480:-2", "-q:v", "3", "-update", "1", str(jpg_path)],
        check=True,
    )


def apply_chosen_covers(site):
    for slug, seconds in (site.get("covers") or {}).items():
        mp4_path = GALLERY_DIR / f"{slug}.mp4"
        if isinstance(seconds, (int, float)) and mp4_path.exists():
            make_poster_at(mp4_path, GALLERY_DIR / f"{slug}.jpg", float(seconds))


def read_order(path):
    if not path.exists():
        return []
    return [l.strip() for l in path.read_text(encoding="utf-8-sig").splitlines() if l.strip()]


def write_order(path, lines):
    ORDER_DIR.mkdir(exist_ok=True)
    path.write_text("\n".join(lines) + "\n" if lines else "", encoding="utf-8")


def order_key(line):
    return line.split(",")[0].strip()


def append_to_order(path, entry):
    lines = read_order(path)
    if order_key(entry) not in {order_key(l) for l in lines}:
        lines.append(entry)
        write_order(path, lines)


def remove_from_order(path, predicate):
    lines = read_order(path)
    kept = [l for l in lines if not predicate(l)]
    write_order(path, kept)
    return len(kept) != len(lines)


def load_site():
    if not SITE_JSON.exists():
        return {}
    return json.loads(SITE_JSON.read_text(encoding="utf-8-sig"))


def build_video_block(order_line, titles):
    parts = order_line.split(",")
    slug = parts[0].strip()
    modifiers = [p.strip() for p in parts[1:] if p.strip()]

    mp4_path = GALLERY_DIR / f"{slug}.mp4"
    if not mp4_path.exists():
        return None

    title = titles.get(slug) or titleize(slug)
    portrait = ffprobe_is_portrait(mp4_path)
    jpg_path = GALLERY_DIR / f"{slug}.jpg"
    version = hashlib.md5(jpg_path.read_bytes()).hexdigest()[:8] if jpg_path.exists() else "0"

    entry_classes = "gallery-entry" + "".join(f" {m}" for m in modifiers)
    item_classes = "gallery-item" + (" portrait" if portrait else "") + " fade-in video-facade"

    return (
        f'  <div class="{entry_classes}">\n'
        f'    <p class="video-title">{esc(title)}</p>\n'
        f'    <div class="{item_classes}" data-src="assets/gallery/{slug}.mp4">\n'
        f'      <img class="v-thumb" src="assets/gallery/{slug}.jpg?v={version}" alt="" loading="lazy">\n'
        f"      {PLAY_BUTTON}\n"
        "    </div>\n"
        "  </div>"
    )


def build_still_block(name):
    if not (STILLS_DIR / name).exists():
        return None
    return f'    <img class="still fade-in" src="assets/stills/{name}" alt="" loading="lazy">'


def build_hero_block(site):
    lines = [f'    <p class="role">{esc(r)}</p>' for r in site.get("roles", [])]
    if site.get("tagline"):
        lines.append(f'    <p class="tagline">{esc(site["tagline"])}</p>')
    return "\n".join(lines)


def build_about_block(site):
    about = [esc(l) for l in site.get("about", []) if l.strip()]
    if not about:
        return ""
    return '  <p class="about-text" dir="rtl" lang="he">' + "<br>\n    ".join(about) + "</p>"


def build_styles_block(site):
    cfg = json.loads(STYLES_JSON.read_text(encoding="utf-8"))
    rules, used_fonts = [], set()
    for key, style in (site.get("styles") or {}).items():
        target = cfg["targets"].get(key)
        if not target or not isinstance(style, dict):
            continue
        decls = []
        font = style.get("font")
        if font in cfg["fonts"]:
            decls.append(f"font-family: '{font}', sans-serif")
            used_fonts.add(font)
        size = style.get("size")
        if isinstance(size, (int, float)) and 8 <= size <= 160:
            px = int(size)
            decls.append(f"font-size: min({px}px, {target['maxVw']}vw)" if target.get("maxVw") else f"font-size: {px}px")
        color = style.get("color")
        if isinstance(color, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", color):
            decls.append(f"color: {color}")
        if decls:
            rules.append(f"  {target['selector']} {{ {'; '.join(decls)}; }}")

    lines = []
    if used_fonts:
        families = "&".join(
            f"family={f.replace(' ', '+')}:wght@{cfg['fonts'][f]}" for f in sorted(used_fonts)
        )
        lines.append(f'<link href="https://fonts.googleapis.com/css2?{families}&display=swap" rel="stylesheet">')
    if rules:
        lines.append("<style>\n" + "\n".join(rules) + "\n</style>")
    return "\n".join(lines)


def replace_between_markers(html, name, new_content):
    pattern = re.compile(
        rf"(<!-- {name}:START -->).*?\n([ \t]*)(<!-- {name}:END -->)", re.DOTALL
    )
    m = pattern.search(html)
    if not m:
        raise RuntimeError(f"Could not find {name} markers in index.html")
    body = f"\n{new_content}" if new_content else ""
    replacement = f"{m.group(1)}{body}\n{m.group(2)}{m.group(3)}"
    return html[:m.start()] + replacement + html[m.end():]


def rebuild_index_html():
    html = INDEX_HTML.read_text(encoding="utf-8")
    site = load_site()
    titles = site.get("titles", {})
    apply_chosen_covers(site)

    videos = [b for b in (build_video_block(l, titles) for l in read_order(VIDEOS_ORDER)) if b]
    html = replace_between_markers(html, "VIDEOS", "\n".join(videos))

    stills = [b for b in (build_still_block(n) for n in read_order(STILLS_ORDER)) if b]
    html = replace_between_markers(html, "STILLS", "\n".join(stills))

    if site:
        html = replace_between_markers(html, "HERO", build_hero_block(site))
        html = replace_between_markers(html, "ABOUT", build_about_block(site))
        html = replace_between_markers(html, "STYLES", build_styles_block(site))

    INDEX_HTML.write_text(html, encoding="utf-8")
