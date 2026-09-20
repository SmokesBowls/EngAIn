; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Anunnaki: 11 mentions, traits: none
(entity Anunnaki :known false :spawnable false :classification "unknown" :mentions 11 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Applicator: 3 mentions, traits: none
(entity Applicator :known false :spawnable false :classification "unknown" :mentions 3 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Dawn: 3 mentions, traits: none
(entity Dawn :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Dren: 1 mentions, traits: none
(entity Dren :known false :spawnable false :classification "unknown" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Geralt: 18 mentions, traits: none
(entity Geralt :known true :spawnable true :classification "known_spawnable" :mentions 18 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Guards: 1 mentions, traits: none
(entity Guards :known false :spawnable false :classification "unknown" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Mika: 9 mentions, traits: none
(entity Mika :known true :spawnable true :classification "known_spawnable" :mentions 9 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Oreck: 8 mentions, traits: none
(entity Oreck :known true :spawnable true :classification "known_spawnable" :mentions 8 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Overseer: 9 mentions, traits: none
(entity Overseer :known false :spawnable false :classification "unknown" :mentions 9 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Strike: 0 mentions, traits: none
(entity Strike :known false :spawnable false :classification "unknown" :mentions 0 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Team: 0 mentions, traits: none
(entity Team :known false :spawnable false :classification "unknown" :mentions 0 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Zaron: 5 mentions, traits: none
(entity Zaron :known false :spawnable false :classification "unknown" :mentions 5 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)

; ---- Scene Content Observations ----
(scene_object "gate" :category "boundary" :normalized_type "gate" :mentions 10)
(scene_object "wall" :category "boundary" :normalized_type "wall" :mentions 6)

; ---- Speaker Inference ----
(speaker line:75 Oreck :confidence 0.95)
(speaker line:84 Oreck :confidence 0.95)
(speaker line:130 Geralt :confidence 0.95)

; ---- Emotions ----
(emotion line:33 Anunnaki vulnerability :confidence 0.90)
(emotion line:105 Zaron anticipation :confidence 0.90)
(emotion line:107 Zaron wonder :confidence 0.90)
(emotion line:162 Guards hope :confidence 0.90)

; ---- Actions ----
(action line:94 attack :confidence 0.90)
(action line:105 speak :confidence 0.90)
(action line:134 retreat :confidence 0.90)
(action line:136 speak :confidence 0.90)
(action line:158 attack :confidence 0.90)
(action line:160 attack :confidence 0.90)
(action line:162 observe :confidence 0.90)
(action line:165 attack :confidence 0.90)
(action line:171 attack :confidence 0.90)
(action line:183 attack :confidence 0.90)

; ---- Thoughts ----

; ---- Relationships ----
(relationship Geralt Applicator trust :confidence 0.70)

