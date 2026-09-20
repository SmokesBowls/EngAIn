; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Aeon: 3 mentions, traits: none
(entity Aeon :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Anunnaki: 7 mentions, traits: none
(entity Anunnaki :known false :spawnable false :classification "unknown" :mentions 7 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Applicator: 4 mentions, traits: none
(entity Applicator :known false :spawnable false :classification "unknown" :mentions 4 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Every: 3 mentions, traits: none
(entity Every :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Geralt: 21 mentions, traits: none
(entity Geralt :known true :spawnable true :classification "known_spawnable" :mentions 21 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Keepers: 3 mentions, traits: none
(entity Keepers :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Nephoretti: 7 mentions, traits: none
(entity Nephoretti :known true :spawnable false :classification "known_non_spawnable" :mentions 7 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Oreck: 18 mentions, traits: none
(entity Oreck :known true :spawnable true :classification "known_spawnable" :mentions 18 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Zaron: 3 mentions, traits: none
(entity Zaron :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)

; ---- Scene Content Observations ----
(scene_object "wall" :category "boundary" :normalized_type "wall" :mentions 3)

; ---- Speaker Inference ----
(speaker line:52 Oreck :confidence 0.95)
(speaker line:64 Geralt :confidence 0.95)
(speaker line:74 Geralt :confidence 0.95)
(speaker line:86 Geralt :confidence 0.95)
(speaker line:90 Geralt :confidence 0.95)
(speaker line:133 Oreck :confidence 0.95)
(speaker line:159 Geralt :confidence 0.95)

; ---- Emotions ----
(emotion line:68 Oreck vulnerability :confidence 0.90)
(emotion line:150 Anunnaki patience :confidence 0.90)

; ---- Actions ----
(action line:68 attack :confidence 0.90)
(action line:119 speak :confidence 0.90)
(action line:128 observe :confidence 0.90)
(action line:148 speak :confidence 0.90)
(action line:164 speak :confidence 0.90)
(action line:192 speak :confidence 0.90)

; ---- Thoughts ----

