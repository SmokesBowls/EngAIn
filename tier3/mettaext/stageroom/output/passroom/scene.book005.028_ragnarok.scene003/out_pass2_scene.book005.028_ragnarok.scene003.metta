; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Anunnaki: 6 mentions, traits: none
(entity Anunnaki :known false :spawnable false :classification "unknown" :mentions 6 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Applicator: 3 mentions, traits: none
(entity Applicator :known false :spawnable false :classification "unknown" :mentions 3 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Days: 4 mentions, traits: none
(entity Days :known false :spawnable false :classification "unknown" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Dren: 1 mentions, traits: none
(entity Dren :known false :spawnable false :classification "unknown" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Geralt: 12 mentions, traits: none
(entity Geralt :known true :spawnable true :classification "known_spawnable" :mentions 12 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Mika: 7 mentions, traits: none
(entity Mika :known true :spawnable true :classification "known_spawnable" :mentions 7 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; None: 3 mentions, traits: none
(entity None :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Oreck: 6 mentions, traits: none
(entity Oreck :known true :spawnable true :classification "known_spawnable" :mentions 6 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Same: 4 mentions, traits: none
(entity Same :known false :spawnable false :classification "unknown" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Strike: 2 mentions, traits: none
(entity Strike :known false :spawnable false :classification "unknown" :mentions 2 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Team: 2 mentions, traits: none
(entity Team :known false :spawnable false :classification "unknown" :mentions 2 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Tomorrow: 3 mentions, traits: none
(entity Tomorrow :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Volunteers: 0 mentions, traits: none
(entity Volunteers :known false :spawnable false :classification "unknown" :mentions 0 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Zaron: 2 mentions, traits: none
(entity Zaron :known false :spawnable false :classification "unknown" :mentions 2 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)

; ---- Scene Content Observations ----
(scene_object "gate" :category "boundary" :normalized_type "gate" :mentions 3)
(scene_object "wall" :category "boundary" :normalized_type "wall" :mentions 1)

; ---- Speaker Inference ----
(speaker line:50 Geralt :confidence 0.95)
(speaker line:61 Geralt :confidence 0.95)
(speaker line:83 Geralt :confidence 0.95)
(speaker line:89 Geralt :confidence 0.95)
(speaker line:107 Geralt :confidence 0.95)

; ---- Emotions ----
(emotion line:33 Anunnaki vulnerability :confidence 1.00)
(emotion line:99 None uncertainty :confidence 0.90)
(emotion line:146 Tomorrow fear :confidence 0.90)

; ---- Actions ----
(action line:69 attack :confidence 0.90)
(action line:79 approach :confidence 0.90)
(action line:95 retreat :confidence 0.90)
(action line:142 attack :confidence 0.90)

; ---- Thoughts ----

