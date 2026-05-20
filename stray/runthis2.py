IN="03_Fist_contact.txt"
BASE="$(basename "$IN" .txt)"

# Pass 1
python3 pass1_explicit.py "$IN" || exit 1

# Confirm Pass1 output exists somewhere
echo "=== looking for Pass1 output ==="
find . -maxdepth 3 -type f \( -name "out_pass1_${BASE}.txt" -o -name "out_pass1_${BASE}.txt" \) -print
find . -maxdepth 3 -type f -name "out_pass1_${BASE}.txt" -print

# If Pass1 wrote it in the current dir, these will work:
python3 pass2_core.py "out_pass1_${BASE}.txt" || exit 1
python3 pass3_merge.py "out_pass1_${BASE}.txt" "out_pass2_${BASE}.metta" || exit 1
python3 pass4_zon_bridge.py "zonj_${BASE}.json" --era FirstAge --location Beach --output-dir out || exit 1

echo "DONE"
