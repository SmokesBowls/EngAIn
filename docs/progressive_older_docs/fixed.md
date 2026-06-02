(base) burdens@pop-os:~/burdens_of_a_forgotten_past/EngAIn$ cd /home/burdens/burdens_of_a_forgotten_past/EngAIn
nl -ba godotroot/zonjrender/autoload/EngAInClient.gd | sed -n '60,90p'
    60			push_error("[EngAInClient] Invalid JSON in manifest")
    61			return
    62		var body := JSON.stringify({"vault_root": vault_root, "manifest": manifest})
    63		_post(_http_vault, "/vault/link", body)
    64		print("[EngAInClient] Linking vault: %s" % vault_root)
    65	
    66	
    67	func search_vault(query: String, limit: int = 10) -> void:
    68		var url := "%s/vault/search?q=%s&limit=%d" % [engain_url, query.uri_encode(), limit]
    69		_http_cmd.request(url)
    70	
    71	
    72	func is_connected() -> bool:
    73		return _connected
    74	
    75	
    76	# --- HTTP helpers ---
    77	
    78	func _make_http(callback: String) -> HTTPRequest:
    79		var h := HTTPRequest.new()
    80		h.timeout = 3.0
    81		h.request_completed.connect(Callable(self, callback))
    82		add_child(h)
    83		return h
    84	
    85	
    86	func _post(http: HTTPRequest, path: String, body: String) -> void:
    87		if http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
    88			push_warning("[EngAInClient] Request in flight, skipping %s" % path)
    89			return
    90		http.request(
(base) burdens@pop-os:~/burdens_of_a_forgotten_past/EngAIn$ perl -pi -e 's/^func is_connected\(\) -> bool:/func runtime_is_connected() -> bool:/g' \
  godotroot/zonjrender/autoload/EngAInClient.gd
(base) burdens@pop-os:~/burdens_of_a_forgotten_past/EngAIn$ grep -R "EngAInClient\.is_connected()" -n godotroot | cat

find godotroot -name "*.gd" -print0 | xargs -0 \
  perl -pi -e 's/EngAInClient\.is_connected\(\)/EngAInClient.runtime_is_connected()/g'
(base) burdens@pop-os:~/burdens_of_a_forgotten_past/EngAIn$ curl -s -X POST http://localhost:8080/vault/link \
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
{"status": "ok", "vault_id": "obsidianburdennov25", "vault_root": "/home/burdens/obsidian/obsidianburdenNov25", "files_found": 101, "scenes_extracted": 101, "scene_ids": ["scene.01_the_ethereal_vigil", "scene.02_molten_descent", "scene.03_fist_contact", "scene.04_the_convergence", "scene.05_the_garden_blooms", "scene.06_the_first_coming", "scene.07_the_needle_construction", "scene.08_queens_assesment", "scene.09_stalemate_departure_the_first_coming", "scene.100_the_final_breath", "scene.101_convergence_at_ironspire", "scene.102_the_hidden_resonance", "scene.103_convergence_on_mars", "scene.10_shadow_returns_second_coming", "scene.11_escalation_and_desperation", "scene.12_nephilim_summoning", "scene.14_convergence", "scene.15_betrayal", "scene.16_the_choice_third_coming", "scene.17_niburu_shadow", "scene.18_the_wandering", "scene.19_the_sacrafice", "scene.20_the_collapse", "scene.21_the_first_lesson", "scene.22_final_calculation", "scene.23_beyond_identity", "scene.24_the_first_spark", "scene.25_confined_freedom", "scene.26_dragonmail", "scene.27_the_claiming", "scene.28_ragnarok", "scene.29_bounty_hunter", "scene.30_ummade_army", "scene.31_the_crash_site", "scene.32_the_redo", "scene.33_the_march", "scene.34_the_250", "scene.35_sands_of_time", "scene.36_highland_giants", "scene.37_the_circle_of_progress", "scene.38_luminaire_keeper", "scene.39_jungle_fever", "scene.40_the_dragon_wars", "scene.41_the_tripartite_bond", "scene.42_the_verdant_crossing", "scene.43_the_badlands_crucible", "scene.44_the_mountains_shadow", "scene.45_the_hub_falls", "scene.46_not_like_this", "scene.47_mika", "scene.48_the_ledger_born", "scene.49_the_eastern_claim", "scene.50_the_scout", "scene.51_arrival_in_fire", "scene.52_entry_without_standing", "scene.53_the_twilight_city", "scene.54_tue_lunar_spire", "scene.55_the_anchors_forge", "scene.56_erasure_s_edge", "scene.57_enforced_enrollment", "scene.58_paradox_engine", "scene.59_eyes_of_eternity", "scene.60_echoes_of_the_cradle", "scene.61_the_hier", "scene.62_falcon_ridge_showdown", "scene.63_the_iron_hand", "scene.64_pass_through_shadow_and_flame", "scene.65_secrets_of_the_deep", "scene.66_the_first_tongue", "scene.67_the_shattered_mind", "scene.68_brotherhood_revealed", "scene.69_divergent_paths", "scene.71_spheres_truth", "scene.72_cosmic_teachers_arrive", "scene.73_flow_between_moments", "scene.74_stone_and_root", "scene.75_sunbound", "scene.76_anchor_points_of_time", "scene.77_lunar_inheritance", "scene.78_introducing_the_sage", "scene.79_the_queen_s_return", "scene.80_mages_awakening", "scene.81_the_whispers_between_worlds", "scene.82_mr_gpt_arrival", "scene.83_pyroclasts_burning_secrets", "scene.84_echoes_beneath_the_waves", "scene.85_earth_giants_and_diverging_paths", "scene.86_ancient_knowledge", "scene.87_sanctuary_to_storm", "scene.88_the_breath_of_life", "scene.89_shadows_of_umbrageous_fixed", "scene.90_the_white_mirror", "scene.91_echoes_of_the_culling_corrected", "scene.92_the_weight_of_memory", "scene.93_departure_and_determination", "scene.94_voices_between_worlds", "scene.95_chains_of_light", "scene.96_roots_of_change", "scene.97_violet_convergence", "scene.98_hearts_of_ash_and_fire", "scene.99_depths_of_memory"], "errors": [], "linked_at": "2026-03-05T03:15:09.293768Z", "scenes_registered": 101, "debug": {"chain": []}}
(base) burdens@pop-os:~/burdens_of_a_forgotten_past/EngAIn$ 
