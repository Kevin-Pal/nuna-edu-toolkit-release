#!/usr/bin/env bash
# Render the promo images via headless Chrome:
#   promo/social-poster.png   1080x1350 (@2x) — portrait poster for feed posts
#   site/assets/og-image.png  1200x630  (@2x) — link-preview card (Open Graph / Twitter)
# Requires Google Chrome. Override the binary with CHROME=... if needed.
#
#   bash tools/poster/build_poster.sh
#
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"

render() { # <html> <WxH> <out>
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --allow-file-access-from-files \
    --force-device-scale-factor=2 --window-size="$2" \
    --screenshot="$3" "file://$DIR/$1"
}

render poster.html 1080,1350 "$DIR/../../promo/social-poster.png"
render og.html     1200,630  "$DIR/../../site/assets/og-image.png"

echo "wrote promo/social-poster.png and site/assets/og-image.png"
