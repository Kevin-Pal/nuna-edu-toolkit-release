#!/usr/bin/env bash
# Render the social-media poster to promo/social-poster.png (1080x1350, @2x = 2160x2700).
# Requires Google Chrome (headless). Override the binary with CHROME=... if needed.
#
#   bash tools/poster/build_poster.sh
#
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="$DIR/../../promo/social-poster.png"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"

"$CHROME" --headless=new --disable-gpu --hide-scrollbars --allow-file-access-from-files \
  --force-device-scale-factor=2 --window-size=1080,1350 \
  --screenshot="$OUT" "file://$DIR/poster.html"

echo "wrote $OUT"
