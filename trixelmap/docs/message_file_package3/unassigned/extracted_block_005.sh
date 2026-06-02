cd /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/trixelmap

# Run the updated scanner
python3 vault_spatial_parser.py \
  --vault-dir /home/mytruelove/Downloads/obsidianburdenNov25 \
  --output-dir out/vault

# Verify the new "Mentioned" locations (Ironspire, Marsh, etc.)
grep -niE "star|needle|falcon|sundrift|ironspire|echo|tower|tide|caller|island|marsh|nephoretti" out/vault/location_spatial_report.md
