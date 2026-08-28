#!/usr/bin/env bash
# Verify security invariants in the BUILT artifact (public/), not the config.
# Exists because every security bug this project has had built successfully:
# the config said one thing and the emitted site said another. Run after `zola build`;
# CI runs it before deploy and fails the pipeline on drift.
set -euo pipefail
cd "$(dirname "$0")/.."
fail() { echo "FAIL: $1" >&2; exit 1; }

[ -f public/index.html ] || fail "public/index.html missing — build first"

# 1. CSP is emitted and matches the intended policy exactly.
csp=$(grep -o 'default-src[^"]*' public/index.html | head -1) || fail "no CSP meta tag emitted"
echo "CSP: $csp"
case "$csp" in *"https://*"*) fail "img-src wildcard (https://*) leaked into CSP — the extra.hcard ordering bug is back";; esac
case "$csp" in *unsafe-inline*) fail "unsafe-inline in CSP";; esac
case "$csp" in *"img-src 'self' data:"*) ;; *) fail "img-src is not exactly 'self' data:";; esac
case "$csp" in *"style-src 'self'"*) ;; *) fail "style-src is not 'self'";; esac

# 2. Class-based highlighting: zero inline style ATTRIBUTES in rendered posts.
# Match style= only inside a tag (after < and before >), so prose or code spans that
# merely mention the string do not trip the gate.
if grep -rlqE '<[a-zA-Z][^>]*[[:space:]]style=' public/blog/*/index.html 2>/dev/null; then
  fail "inline style= attribute in a post — highlighting fell back to inline mode"
fi

# 3. HTTP-header policies shipped for Workers to serve.
[ -f public/_headers ] || fail "public/_headers missing"
grep -q 'X-Frame-Options: DENY' public/_headers || fail "_headers lost X-Frame-Options"
grep -q 'X-Content-Type-Options: nosniff' public/_headers || fail "_headers lost nosniff"

# 4. Identity: the built site must never contain the owner's real identity.
if grep -rilq -e 'ray bitton' -e 'raybit10' public/; then
  fail "identity-bearing string in built output"
fi

echo "OK: all build invariants hold"
