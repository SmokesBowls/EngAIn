; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Anunnaki: 3 mentions, traits: none
(entity Anunnaki :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Book: 4 mentions, traits: none
(entity Book :known false :spawnable false :classification "unknown" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Giants: 3 mentions, traits: none
(entity Giants :known true :spawnable false :classification "known_non_spawnable" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Pazuzu: 8 mentions, traits: none
(entity Pazuzu :known true :spawnable true :classification "known_spawnable" :mentions 8 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Torhh: 7 mentions, traits: none
(entity Torhh :known true :spawnable true :classification "known_spawnable" :mentions 7 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)

; ---- Scene Content Observations ----
(scene_object "valley" :category "terrain_feature" :normalized_type "valley" :mentions 7)

; ---- Speaker Inference ----
(speaker line:32 Torhh :confidence 0.95)
(speaker line:34 Pazuzu :confidence 0.95)
(speaker line:38 Pazuzu :confidence 0.95)
(speaker line:42 Pazuzu :confidence 0.95)

; ---- Emotions ----
(emotion line:44 Torhh patience :confidence 0.90)

; ---- Actions ----
(action line:29 shaping :confidence 0.90)

; ---- Thoughts ----

