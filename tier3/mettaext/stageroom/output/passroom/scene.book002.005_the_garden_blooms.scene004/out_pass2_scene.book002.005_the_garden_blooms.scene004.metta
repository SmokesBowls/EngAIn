; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Elyraen: 1 mentions, traits: none
(entity Elyraen :known true :spawnable true :classification "known_spawnable" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Giants: 4 mentions, traits: none
(entity Giants :known true :spawnable false :classification "known_non_spawnable" :mentions 4 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Nephoretti: 2 mentions, traits: none
(entity Nephoretti :known true :spawnable false :classification "known_non_spawnable" :mentions 2 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)

; ---- Scene Content Observations ----
(scene_object "valley" :category "terrain_feature" :normalized_type "valley" :mentions 3)

; ---- Speaker Inference ----
(speaker line:44 Elyraen :confidence 0.95)

; ---- Emotions ----

; ---- Actions ----
(action line:12 vrill_energy :confidence 0.90)
(action line:23 vrill_energy :confidence 0.90)
(action line:37 shaping :confidence 0.90)

; ---- Thoughts ----

