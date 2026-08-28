#!/usr/bin/env bash
# Render Mermaid sources in diagrams/ to static SVG in static/diagrams/.
#
# Why build-time rather than in the browser:
#   The theme can load mermaid.js client-side, but doing so makes it inject <style>
#   elements at runtime, so the theme relaxes the page CSP to style-src 'unsafe-inline'
#   on every page that enables it. Measured, not assumed (2026-08-28). This site treats
#   that CSP as a hard invariant, and scripts/verify-build.sh now fails the build if any
#   page carries 'unsafe-inline'.
#   Rendering here instead keeps the source of truth as plain text in git, ships a ~10 KB
#   SVG instead of 2.5 MB of JavaScript, renders with JS disabled, and costs the page
#   nothing at runtime.
#
# This is intentionally NOT part of CI. The SVGs are committed artefacts, reviewable in
# a diff, so the deploy pipeline stays hermetic and free of an npm dependency.
# Run it locally after editing a .mmd, then commit both files.
#
# Requires: node/npx, and a Chromium on the host (used via PUPPETEER_EXECUTABLE_PATH so
# puppeteer does not download a second browser).
set -euo pipefail
cd "$(dirname "$0")/.."

MERMAID_VERSION="11.4.2"   # pinned, like every other tool in this repo
SRC_DIR="diagrams"
OUT_DIR="static/diagrams"

[ -d "$SRC_DIR" ] || { echo "no $SRC_DIR/ directory; nothing to render"; exit 0; }
mkdir -p "$OUT_DIR"

chromium=$(command -v chromium-browser || command -v chromium || command -v google-chrome || true)
if [ -n "$chromium" ]; then
    export PUPPETEER_EXECUTABLE_PATH="$chromium"
    echo "using browser: $chromium"
fi

# Neutral rendering: the site skin is monochrome and the diagram is displayed through
# the theme's invertible_image shortcode, which inverts it for dark mode. A diagram with
# baked-in colour would invert into something unpleasant.
cat > "$(dirname "$0")/../.mermaid-config.json" <<'CONF'
{
  "theme": "neutral",
  "themeVariables": {
    "fontFamily": "ui-sans-serif, system-ui, sans-serif",
    "fontSize": "16px"
  },
  "htmlLabels": false,
  "flowchart": { "curve": "basis", "useMaxWidth": true, "htmlLabels": false }
}
CONF

shopt -s nullglob
count=0
for src in "$SRC_DIR"/*.mmd; do
    out="$OUT_DIR/$(basename "${src%.mmd}").svg"
    echo "rendering $src -> $out"
    npx -y "@mermaid-js/mermaid-cli@${MERMAID_VERSION}" \
        --input "$src" --output "$out" \
        --configFile .mermaid-config.json \
        --backgroundColor transparent \
        --quiet
    count=$((count + 1))
done
rm -f .mermaid-config.json

[ "$count" -gt 0 ] || { echo "no .mmd files found in $SRC_DIR/"; exit 0; }

# Two things must hold in the output, and neither is visible from a zero exit code.
#
# 1. No fetchable external reference. XML namespace URIs (www.w3.org) are declarations,
#    not subresources, so they are excluded; anything else would be fetched at render
#    time and silently blocked by img-src 'self'.
if grep -oE '(xlink:href|href|src)="https?://[^"]*|url\(https?://[^)]*|@import' "$OUT_DIR"/*.svg 2>/dev/null \
   | grep -v 'www\.w3\.org' | grep -q .; then
    grep -loE '(xlink:href|href|src)="https?://[^"]*|url\(https?://[^)]*|@import' "$OUT_DIR"/*.svg >&2
    echo "FAIL: rendered SVG contains an external reference" >&2
    exit 1
fi
#
# 2. No <foreignObject>. Mermaid's default label mode wraps text in embedded XHTML, and
#    browsers do not render foreign content in an SVG loaded through <img> -- the diagram
#    appears with every label blank. htmlLabels:false above emits native <text> instead.
#    This check exists because the failure is entirely silent: valid SVG, correct size,
#    no console error, no text.
if grep -l 'foreignObject' "$OUT_DIR"/*.svg 2>/dev/null | grep -q .; then
    grep -l 'foreignObject' "$OUT_DIR"/*.svg >&2
    echo "FAIL: SVG uses foreignObject labels, which render blank inside <img>" >&2
    exit 1
fi

echo "OK: rendered $count diagram(s) to $OUT_DIR/"
