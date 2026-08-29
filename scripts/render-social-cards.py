#!/usr/bin/env python3
"""Render an Open Graph card (1200x630 PNG) for every page, and wire it into front matter.

Why this exists: without og:image, a link to this site posted anywhere renders as bare
text with no preview. tabi already emits og:image / twitter:image from a
`social_media_card` setting; it just needs an image to point at.

Design constraints, same as the rest of this repo:
  - No CI dependency. Cards are committed artefacts, reviewable in a diff, so the
    deploy pipeline stays hermetic. Run this locally after adding or retitling a post.
  - No network at any point. The card HTML uses locally installed fonts only; a remote
    webfont would render as a fallback on this machine and silently differently on
    another.
  - Idempotent. Re-running regenerates the PNGs and leaves front matter alone if the
    key is already present, so it is safe to run on the whole tree at any time.

Usage:  python3 scripts/render-social-cards.py [--force]
        --force  rewrite cards even if the PNG is newer than its source
"""

import argparse
import html
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
OUT_DIR = ROOT / "static" / "social_cards"
SITE = "linuxgroot.net"

# Matches the TOML front matter block Zola uses (+++ delimited).
FRONT_MATTER = re.compile(r"\A\+\+\+\n(.*?)\n\+\+\+\n", re.DOTALL)

CARD_HTML = """<!doctype html>
<meta charset="utf-8">
<style>
  /* Local font stack only. Nothing is fetched. */
  html, body {{ margin: 0; padding: 0; }}
  body {{
    width: 1200px; height: 630px; box-sizing: border-box;
    padding: 76px 84px;
    display: flex; flex-direction: column; justify-content: space-between;
    background: #fbfbfa; color: #16161a;
    font-family: "Noto Sans", "DejaVu Sans", "Liberation Sans", sans-serif;
    -webkit-font-smoothing: antialiased;
  }}
  .kicker {{
    font-size: 25px; letter-spacing: .16em; text-transform: uppercase;
    color: #6b6b73; font-weight: 600;
  }}
  h1 {{
    font-size: {title_size}px; line-height: 1.13; font-weight: 700;
    margin: 0; letter-spacing: -0.022em; max-width: 20ch;
  }}
  p {{
    font-size: 30px; line-height: 1.42; color: #4a4a52;
    margin: 26px 0 0; max-width: 44ch;
  }}
  footer {{
    display: flex; align-items: center; gap: 18px;
    border-top: 2px solid #e0e0dd; padding-top: 26px;
    font-size: 26px; color: #6b6b73;
  }}
  .site {{ color: #16161a; font-weight: 700; }}
  /* The root-prompt mark, inline so the card stays a single self-contained
     render with no asset to fetch. */
  .mark {{ width: 46px; height: 46px; flex: 0 0 auto; color: #2c6e49; }}
</style>
<div class="kicker">{kicker}</div>
<div>
  <h1>{title}</h1>
  {description}
</div>
<footer><svg class="mark" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><path d="M13 5 L10 27 M23 5 L20 27 M5 12 L27 12 M4 20 L26 20" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round"/></svg><span class="site">{site}</span><span>{tagline}</span></footer>
"""


def parse_front_matter(path: pathlib.Path):
    text = path.read_text(encoding="utf-8")
    m = FRONT_MATTER.match(text)
    if not m:
        return None, text
    try:
        return tomllib.loads(m.group(1)), text
    except tomllib.TOMLDecodeError as exc:
        print(f"  skip {path.relative_to(ROOT)}: unparseable front matter ({exc})")
        return None, text


def card_name(path: pathlib.Path) -> str:
    """Stable slug from the content path, so a card maps to exactly one page."""
    rel = path.relative_to(CONTENT)
    parts = list(rel.parts)
    if parts[-1] in ("index.md", "_index.md"):
        parts.pop()
    else:
        parts[-1] = parts[-1][:-3]
    return "-".join(parts) if parts else "index"


def truncate(text: str, limit: int) -> str:
    """Trim to fit the card, preferring a clean sentence end over an ellipsis.

    A card that stops mid-clause reads as broken rather than abridged, and the
    description is the only prose a reader sees before deciding to click.
    """
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    head = text[:limit]
    # Prefer the last sentence boundary, but only if it keeps enough of the text
    # to still say something.
    cut = max(head.rfind(". "), head.rfind("? "), head.rfind("! "))
    if cut >= limit * 0.55:
        return head[: cut + 1]
    return head.rsplit(" ", 1)[0] + "…"


def card_kicker(path: pathlib.Path, fm: dict) -> str:
    """The small label above the title: what kind of page this is."""
    rel = path.relative_to(CONTENT)
    is_section = rel.name == "_index.md"
    if fm.get("extra", {}).get("series"):
        return "Series"
    if rel.parts[0] == "pages":
        return "Reference"
    if rel.parts[0] == "blog" and not is_section:
        return "Post"
    return SITE


def render(chromium: str, title: str, description: str, kicker: str, out: pathlib.Path):
    # Long titles need to step down or they overflow the 630px box.
    n = len(title)
    title_size = 82 if n <= 34 else 72 if n <= 48 else 62 if n <= 64 else 54
    desc_html = f"<p>{html.escape(truncate(description, 150))}</p>" if description else ""
    doc = CARD_HTML.format(
        title=html.escape(truncate(title, 90)),
        description=desc_html,
        kicker=html.escape(kicker),
        site=SITE,
        tagline="Linux, HPC and AI infrastructure",
        title_size=title_size,
    )
    with tempfile.TemporaryDirectory() as tmp:
        src = pathlib.Path(tmp) / "card.html"
        src.write_text(doc, encoding="utf-8")
        subprocess.run(
            [chromium, "--headless", "--no-sandbox", "--disable-gpu",
             "--hide-scrollbars", "--force-device-scale-factor=1",
             "--default-background-color=FFFBFBFA",
             "--virtual-time-budget=2000",
             "--window-size=1200,630",
             f"--screenshot={out}", f"file://{src}"],
            check=True, capture_output=True,
        )


def ensure_front_matter_key(path: pathlib.Path, raw: str, fm: dict, value: str) -> bool:
    """Add social_media_card to [extra] if absent. Returns True if the file changed."""
    if "social_media_card" in fm.get("extra", {}):
        return False
    m = FRONT_MATTER.match(raw)
    block = m.group(1)
    if re.search(r"^\[extra\]\s*$", block, re.MULTILINE):
        # Insert directly under the existing [extra] header, which keeps it before any
        # [extra.*] sub-table. Sub-tables capture every key below them (see the CSP
        # incident in config.toml), so position matters even here.
        new_block = re.sub(r"^(\[extra\]\s*)$",
                           rf'\1\nsocial_media_card = "{value}"',
                           block, count=1, flags=re.MULTILINE)
    else:
        new_block = block.rstrip() + f'\n\n[extra]\nsocial_media_card = "{value}"'
    path.write_text(raw.replace(m.group(1), new_block, 1), encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="rewrite cards even if current")
    args = ap.parse_args()

    chromium = next((p for p in ("chromium-browser", "chromium", "google-chrome")
                     if shutil.which(p)), None)
    if not chromium:
        print("FAIL: no chromium on PATH", file=sys.stderr)
        return 1
    print(f"using browser: {shutil.which(chromium)}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    made = wired = 0
    for path in sorted(CONTENT.rglob("*.md")):
        fm, raw = parse_front_matter(path)
        if fm is None or not fm.get("title") or fm.get("draft") or fm.get("render") is False:
            continue

        name = card_name(path)
        out = OUT_DIR / f"{name}.png"
        kicker = card_kicker(path, fm)

        if args.force or not out.exists() or out.stat().st_mtime < path.stat().st_mtime:
            render(chromium, fm["title"], fm.get("description", ""), kicker, out)
            made += 1
            print(f"  rendered {out.relative_to(ROOT)}")

        if ensure_front_matter_key(path, raw, fm, f"/social_cards/{name}.png"):
            wired += 1
            print(f"  wired    {path.relative_to(ROOT)}")

    print(f"OK: {made} card(s) rendered, {wired} page(s) wired")
    return 0


if __name__ == "__main__":
    sys.exit(main())
