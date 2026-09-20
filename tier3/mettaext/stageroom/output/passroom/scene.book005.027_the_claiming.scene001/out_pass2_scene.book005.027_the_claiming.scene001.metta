; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Aeon: 3 mentions, traits: none
(entity Aeon :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Anunnaki: 5 mentions, traits: none
(entity Anunnaki :known false :spawnable false :classification "unknown" :mentions 5 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Applicator: 4 mentions, traits: none
(entity Applicator :known false :spawnable false :classification "unknown" :mentions 4 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Dragon: 3 mentions, traits: none
(entity Dragon :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Geralt: 22 mentions, traits: none
(entity Geralt :known true :spawnable true :classification "known_spawnable" :mentions 22 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Keepers: 3 mentions, traits: none
(entity Keepers :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Mail: 3 mentions, traits: none
(entity Mail :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Nephoretti: 5 mentions, traits: none
(entity Nephoretti :known true :spawnable false :classification "known_non_spawnable" :mentions 5 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Oreck: 28 mentions, traits: none
(entity Oreck :known true :spawnable true :classification "known_spawnable" :mentions 28 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)

; ---- Scene Content Observations ----
(scene_object "ridge" :category "terrain_feature" :normalized_type "ridge" :mentions 1)
(scene_object "wall" :category "boundary" :normalized_type "wall" :mentions 1)

; ---- Speaker Inference ----
(speaker line:45 Geralt :confidence 0.95)
(speaker line:65 Geralt :confidence 0.95)
(speaker line:125 Oreck :confidence 0.95)
(speaker line:127 Geralt :confidence 0.95)
(speaker line:131 Oreck :confidence 0.95)
(speaker line:133 Geralt :confidence 0.95)
(speaker line:143 Oreck :confidence 0.95)
(speaker line:145 Geralt :confidence 0.95)
(speaker line:155 Oreck :confidence 0.95)

; ---- Emotions ----
(emotion line:71 Aeon fear :confidence 0.90)
(emotion line:101 Geralt anxiety :confidence 0.90)
(emotion line:161 Geralt joy :confidence 0.90)
(emotion line:171 Anunnaki caution :confidence 0.90)

; ---- Actions ----
(action line:35 approach :confidence 0.90)
(action line:83 shaping :confidence 0.90)
(action line:110 speak :confidence 0.90)
(action line:167 observe :confidence 0.90)

; ---- Thoughts ----

; ---- Relationships ----
(relationship Aeon Keepers collaborate :confidence 0.70)

