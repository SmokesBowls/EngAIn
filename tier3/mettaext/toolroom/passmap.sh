#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
METTAEXT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
STAGEROOM="$METTAEXT_ROOT/stageroom"

BLD=$'\033[1m'
RST=$'\033[0m'
CYN=$'\033[36m'

print_header() {
  echo
  echo "EngAIn Pass Map  –  imprint · output · catcher"
  echo "$(date '+%Y-%m-%d %H:%M')   mettaext: $METTAEXT_ROOT"
  echo "──────────────────────────────────────────────────────────────────────────────"
  echo
}

row() {
  local pass="$1"
  local reads="$2"
  local writes="$3"
  local caught_by="$4"
  printf "%-13s %-23s %-21s %s\n" "$pass" "$reads" "$writes" "$caught_by"
}

print_summary() {
  print_header

  echo "── CHAPTERROOM  (ABC = scene provider)"
  echo
  printf "%-13s %-23s %-21s %s\n" "PASS" "READS" "WRITES" "CAUGHT BY"
  echo "──────────────────────────────────────────────────────────────────────────────"
  row "passA" "<chapter>.txt"    "out_passA_*.json"           "Pass B"
  row "passB" "out_passA_*.json" "out_passB_*.json"           "Pass C"
  row "passC" "out_passB_*.json" "scene_NNN.txt + index.json" "Pass 1 × N"

  echo
  echo "── PASSROOM  (1–5 = scene compiler)"
  echo
  printf "%-13s %-23s %-21s %s\n" "PASS" "READS" "WRITES" "CAUGHT BY"
  echo "──────────────────────────────────────────────────────────────────────────────"
  row "pass1" "scene_NNN.txt"       "out_pass1_*.txt"             "Pass 2"
  row "pass2" "out_pass1_*.txt"     "out_pass2_*.metta"           "Pass 3"
  row "pass3" "pass1 + pass2"       "zonj_*.json"                 "Pass 4"
  row "pass4" "zonj_*.json"         "*.zon + *.zonj.json"         "Pass 5"
  row "pass5" "*.zonj.json"         "scene.*.json + scene_index"  "EngAInOS / vault"

  echo
  echo "Run  ./passmap.sh <passX>       for full detail on one pass"
  echo "Run  ./passmap.sh --live        to see actual stageroom file counts"
  echo
}

print_detail() {
  local pass="$1"
  print_header

  case "$pass" in
    passA|a|A)
      echo "passA — Chapter Intake"
      echo "  Code     : $METTAEXT_ROOT/chapterroom/passA_chapter_intake.py"
      echo "  Reads    : stageroom/input/chapters/<chapter>.txt"
      echo "  Writes   : stageroom/output/chapterroom/out_passA_<chapter>.json"
      echo "  Contract : engain.chapter_intake_manifest.v1"
      echo "  Caught by: Pass B"
      ;;
    passB|b|B)
      echo "passB — Scene Boundary Provider"
      echo "  Code     : $METTAEXT_ROOT/chapterroom/passB_scene_boundary_provider.py"
      echo "  Reads    : stageroom/output/chapterroom/out_passA_*.json"
      echo "  Writes   : stageroom/output/chapterroom/out_passB_*.json"
      echo "  Contract : engain.scene_boundary_proposal.v1"
      echo "  Caught by: Pass C"
      ;;
    passC|c|C)
      echo "passC — Scene Packet Writer"
      echo "  Code     : $METTAEXT_ROOT/chapterroom/passC_scene_packet_writer.py"
      echo "  Reads    : stageroom/output/chapterroom/out_passB_*.json"
      echo "  Writes   : stageroom/output/chapterroom/scene_packets/<chapter>/scene_*.txt"
      echo "  Index    : stageroom/output/chapterroom/scene_packets/<chapter>/scene_packets_index.json"
      echo "  Contract : engain.scene_provider_packet.v1"
      echo "  Caught by: Pass 1, once per scene packet"
      ;;
    pass1|1)
      echo "pass1 — Explicit Extraction"
      echo "  Code     : $METTAEXT_ROOT/passroom/pass1_explicit.py"
      echo "  Reads    : scene packet .txt from Pass C"
      echo "  Writes   : stageroom/output/passroom/<scene>/out_pass1_<stem>.txt"
      echo "  Caught by: Pass 2"
      ;;
    pass2|2)
      echo "pass2 — Enhanced MeTTa Inference"
      echo "  Code     : $METTAEXT_ROOT/passroom/pass2_enhanced.py"
      echo "  Reads    : out_pass1_*.txt"
      echo "  Writes   : stageroom/output/passroom/<scene>/out_pass2_<stem>.metta"
      echo "  Caught by: Pass 3"
      ;;
    pass3|3)
      echo "pass3 — ZONJ Merge"
      echo "  Code     : $METTAEXT_ROOT/passroom/pass3_merge.py"
      echo "  Reads    : out_pass1_*.txt + out_pass2_*.metta"
      echo "  Writes   : stageroom/output/passroom/<scene>/zonj_<stem>.json"
      echo "  Caught by: Pass 4"
      ;;
    pass4|4)
      echo "pass4 — ZON Bridge"
      echo "  Code     : $METTAEXT_ROOT/passroom/pass4_zon_bridge.py"
      echo "  Reads    : zonj_<stem>.json"
      echo "  Writes   : stageroom/output/passroom/<scene>/<stem>.zon"
      echo "           : stageroom/output/passroom/<scene>/<stem>.zonj.json"
      echo "  Caught by: Pass 5"
      ;;
    pass5|5)
      echo "pass5 — Game Scene Bridge"
      echo "  Code     : $METTAEXT_ROOT/passroom/pass5_game_bridge.py"
      echo "  Reads    : <stem>.zonj.json"
      echo "  Writes   : stageroom/output/passroom/<scene>/game_scenes/scene.*.json"
      echo "           : stageroom/output/passroom/<scene>/game_scenes/scene_index.json"
      echo "  Caught by: EngAInOS / scene loader / vault bridge"
      ;;
    *)
      echo "UNKNOWN_PASS=$pass"
      echo "Known passes: passA passB passC pass1 pass2 pass3 pass4 pass5"
      exit 1
      ;;
  esac

  echo
}

count_files() {
  local dir="$1"
  local name="$2"

  if [[ ! -d "$dir" ]]; then
    echo "[none]"
    return 0
  fi

  local count
  count="$(find "$dir" -type f -name "$name" 2>/dev/null | wc -l | tr -d ' ')"

  if [[ "$count" == "0" ]]; then
    echo "[none]"
  else
    echo "$count"
  fi
}

print_live() {
  print_summary

  local ch_out="$STAGEROOM/output/chapterroom"
  local pr_out="$STAGEROOM/output/passroom"

  echo "${BLD}${CYN}── Live stageroom file counts ──────────────────────────────────────────${RST}"

  printf "  %-35s" "PassA manifests (out_passA_*.json)"
  count_files "$ch_out" "out_passA_*.json"
  echo

  printf "  %-35s" "PassB proposals (out_passB_*.json)"
  count_files "$ch_out" "out_passB_*.json"
  echo

  printf "  %-35s" "PassC scene packets (.txt)"
  count_files "$ch_out/scene_packets" "scene.*.txt"
  echo

  printf "  %-35s" "PassC packet indexes"
  count_files "$ch_out/scene_packets" "scene_packets_index.json"
  echo

  printf "  %-35s" "Pass1 outputs (out_pass1_*.txt)"
  count_files "$pr_out" "out_pass1_*.txt"
  echo

  printf "  %-35s" "Pass2 outputs (out_pass2_*.metta)"
  count_files "$pr_out" "out_pass2_*.metta"
  echo

  printf "  %-35s" "Pass3 ZONJ files (zonj_*.json)"
  count_files "$pr_out" "zonj_*.json"
  echo

  printf "  %-35s" "Pass4 ZON files (*.zon)"
  count_files "$pr_out" "*.zon"
  echo

  printf "  %-35s" "Pass4 canonical ZONJ (*.zonj.json)"
  count_files "$pr_out" "*.zonj.json"
  echo

  printf "  %-35s" "Pass5 game scenes (scene.*.json)"
  count_files "$pr_out" "scene.*.json"
  echo

  printf "  %-35s" "Pass5 scene indexes"
  count_files "$pr_out" "scene_index.json"
  echo

  echo
}

main() {
  if [[ "${1:-}" == "--live" ]]; then
    print_live
    exit 0
  fi

  if [[ -n "${1:-}" ]]; then
    print_detail "$1"
    exit 0
  fi

  print_summary
  exit 0
}

main "$@"
