
Hint: type caja to open the file manager

bash: /home/burdens/.openclaw/completions/openclaw.bash: No such file or directory
bash: /home/linuxbrew/.linuxbrew/bin/brew: No such file or directory
(base) burdens@pop-os:~$ curl -s -X POST http://localhost:8080/vault/link \
  -H "Content-Type: application/json" \
  -d "$(python3 - <<'PY'
import json
vault_root = "/home/burdens/obsidian/obsidianburdenNov25"
manifest_path = vault_root + "/vault.manifest.json"
with open(manifest_path, "r", encoding="utf-8") as f:
    manifest = json.load(f)
print(json.dumps({"vault_root": vault_root, "manifest": manifest}))
PY
)"
echo
{"status": "ok", "vault_id": "obsidianburdennov25", "vault_root": "/home/burdens/obsidian/obsidianburdenNov25", "files_found": 101, "scenes_extracted": 101, "scene_ids": ["scene.01_the_ethereal_vigil", "scene.02_molten_descent", "scene.03_fist_contact", "scene.04_the_convergence", "scene.05_the_garden_blooms", "scene.06_the_first_coming", "scene.07_the_needle_construction", "scene.08_queens_assesment", "scene.09_stalemate_departure_the_first_coming", "scene.100_the_final_breath", "scene.101_convergence_at_ironspire", "scene.102_the_hidden_resonance", "scene.103_convergence_on_mars", "scene.10_shadow_returns_second_coming", "scene.11_escalation_and_desperation", "scene.12_nephilim_summoning", "scene.14_convergence", "scene.15_betrayal", "scene.16_the_choice_third_coming", "scene.17_niburu_shadow", "scene.18_the_wandering", "scene.19_the_sacrafice", "scene.20_the_collapse", "scene.21_the_first_lesson", "scene.22_final_calculation", "scene.23_beyond_identity", "scene.24_the_first_spark", "scene.25_confined_freedom", "scene.26_dragonmail", "scene.27_the_claiming", "scene.28_ragnarok", "scene.29_bounty_hunter", "scene.30_ummade_army", "scene.31_the_crash_site", "scene.32_the_redo", "scene.33_the_march", "scene.34_the_250", "scene.35_sands_of_time", "scene.36_highland_giants", "scene.37_the_circle_of_progress", "scene.38_luminaire_keeper", "scene.39_jungle_fever", "scene.40_the_dragon_wars", "scene.41_the_tripartite_bond", "scene.42_the_verdant_crossing", "scene.43_the_badlands_crucible", "scene.44_the_mountains_shadow", "scene.45_the_hub_falls", "scene.46_not_like_this", "scene.47_mika", "scene.48_the_ledger_born", "scene.49_the_eastern_claim", "scene.50_the_scout", "scene.51_arrival_in_fire", "scene.52_entry_without_standing", "scene.53_the_twilight_city", "scene.54_tue_lunar_spire", "scene.55_the_anchors_forge", "scene.56_erasure_s_edge", "scene.57_enforced_enrollment", "scene.58_paradox_engine", "scene.59_eyes_of_eternity", "scene.60_echoes_of_the_cradle", "scene.61_the_hier", "scene.62_falcon_ridge_showdown", "scene.63_the_iron_hand", "scene.64_pass_through_shadow_and_flame", "scene.65_secrets_of_the_deep", "scene.66_the_first_tongue", "scene.67_the_shattered_mind", "scene.68_brotherhood_revealed", "scene.69_divergent_paths", "scene.71_spheres_truth", "scene.72_cosmic_teachers_arrive", "scene.73_flow_between_moments", "scene.74_stone_and_root", "scene.75_sunbound", "scene.76_anchor_points_of_time", "scene.77_lunar_inheritance", "scene.78_introducing_the_sage", "scene.79_the_queen_s_return", "scene.80_mages_awakening", "scene.81_the_whispers_between_worlds", "scene.82_mr_gpt_arrival", "scene.83_pyroclasts_burning_secrets", "scene.84_echoes_beneath_the_waves", "scene.85_earth_giants_and_diverging_paths", "scene.86_ancient_knowledge", "scene.87_sanctuary_to_storm", "scene.88_the_breath_of_life", "scene.89_shadows_of_umbrageous_fixed", "scene.90_the_white_mirror", "scene.91_echoes_of_the_culling_corrected", "scene.92_the_weight_of_memory", "scene.93_departure_and_determination", "scene.94_voices_between_worlds", "scene.95_chains_of_light", "scene.96_roots_of_change", "scene.97_violet_convergence", "scene.98_hearts_of_ash_and_fire", "scene.99_depths_of_memory"], "errors": [], "linked_at": "2026-03-05T03:20:01.183059Z", "scenes_registered": 101, "debug": {"chain": []}}
(base) burdens@pop-os:~$ curl -s http://localhost:8080/snapshot | python3 - <<'PY'
import sys, json
d=json.load(sys.stdin)
p=d.get("payload", d)
print("scene_id:", p.get("scene_id"))
print("entities:", len(p.get("bridge_entities", [])))
PY
Traceback (most recent call last):
  File "<stdin>", line 2, in <module>
  File "/home/burdens/miniconda3/lib/python3.13/json/__init__.py", line 298, in load
    return loads(fp.read(),
        cls=cls, object_hook=object_hook,
        parse_float=parse_float, parse_int=parse_int,
        parse_constant=parse_constant, object_pairs_hook=object_pairs_hook, **kw)
  File "/home/burdens/miniconda3/lib/python3.13/json/__init__.py", line 352, in loads
    return _default_decoder.decode(s)
           ~~~~~~~~~~~~~~~~~~~~~~~^^^
  File "/home/burdens/miniconda3/lib/python3.13/json/decoder.py", line 345, in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
               ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/burdens/miniconda3/lib/python3.13/json/decoder.py", line 363, in raw_decode
    raise JSONDecodeError("Expecting value", s, err.value) from None
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
(base) burdens@pop-os:~$ python3 - <<'PY' | curl -s -X POST http://localhost:8080/world/sync -H "Content-Type: application/json" -d @-
import json, subprocess
snap=json.loads(subprocess.check_output(["curl","-s","http://localhost:8080/snapshot"], text=True))
p=snap.get("payload", snap)
ents=p.get("bridge_entities", [])
eid=ents[0]["entity_id"]
pos=ents[0].get("transform", {}).get("position", {}) or {}
newpos={"x": float(pos.get("x",0.0))+1.0, "y": float(pos.get("y",0.0)), "z": float(pos.get("z",0.0))}
payload={"type":"world_sync","source":"cli","scene_id": p.get("scene_id",""), "entities": {eid: {"transform": {"position": newpos}}}}
print(json.dumps(payload))
PY
echo
{"type": "error", "message": "No vault linked or path invalid. Use /vault/link first.", "debug": {"chain": []}}
(base) burdens@pop-os:~$ curl -s http://localhost:8080/snapshot | python3 - <<'PY'
import sys, json
p=json.load(sys.stdin).get("payload", {})
e=p.get("bridge_entities", [])[0]
print(e.get("entity_id"), e.get("transform", {}).get("position", {}))
PY
Traceback (most recent call last):
  File "<stdin>", line 2, in <module>
  File "/home/burdens/miniconda3/lib/python3.13/json/__init__.py", line 298, in load
    return loads(fp.read(),
        cls=cls, object_hook=object_hook,
        parse_float=parse_float, parse_int=parse_int,
        parse_constant=parse_constant, object_pairs_hook=object_pairs_hook, **kw)
  File "/home/burdens/miniconda3/lib/python3.13/json/__init__.py", line 352, in loads
    return _default_decoder.decode(s)
           ~~~~~~~~~~~~~~~~~~~~~~~^^^
  File "/home/burdens/miniconda3/lib/python3.13/json/decoder.py", line 345, in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
               ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/burdens/miniconda3/lib/python3.13/json/decoder.py", line 363, in raw_decode
    raise JSONDecodeError("Expecting value", s, err.value) from None
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
(base) burdens@pop-os:~$ 
