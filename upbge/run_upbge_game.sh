#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BLEND="${HERE}/one_path.blend"

if [[ ! -f "${BLEND}" ]]; then
  echo "ERROR: Blend not found: ${BLEND}" >&2
  exit 2
fi

# You can set UPBGE_BIN=/absolute/path/to/upbge/blender to override.
if [[ -z "${UPBGE_BIN:-}" ]]; then
  CANDIDATES=(
    "${HERE}/applications/"upbge-*-linux-x64"/blender"
    "${HERE}/../applications/"upbge-*-linux-x64"/blender"
    "${HERE}/../../applications/"upbge-*-linux-x64"/blender"
  )
  for c in "${CANDIDATES[@]}"; do
    if [[ -x "$c" ]]; then
      UPBGE_BIN="$c"
      break
    fi
  done
fi

if [[ -z "${UPBGE_BIN:-}" ]]; then
  if command -v blender >/dev/null 2>&1; then
    UPBGE_BIN="$(command -v blender)"
  fi
fi

if [[ -z "${UPBGE_BIN:-}" ]]; then
  echo "ERROR: Could not find UPBGE blender binary." >&2
  echo "Set UPBGE_BIN=/absolute/path/to/upbge/blender and re-run." >&2
  exit 3
fi

echo "Launching: ${UPBGE_BIN}"
echo "Blend:     ${BLEND}"
echo ""
echo "In UPBGE: click the 3D Viewport, then press P to start the game."
echo "While running: press F5 to send a ping to EngAIn (/cmd)."
echo ""

exec "${UPBGE_BIN}" "${BLEND}"
