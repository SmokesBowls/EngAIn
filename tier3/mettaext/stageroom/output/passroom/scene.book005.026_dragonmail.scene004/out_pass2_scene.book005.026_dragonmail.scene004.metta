; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Aeon: 13 mentions, traits: none
(entity Aeon :known false :spawnable false :classification "unknown" :mentions 13 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Anunnaki: 9 mentions, traits: none
(entity Anunnaki :known false :spawnable false :classification "unknown" :mentions 9 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Applicator: 7 mentions, traits: none
(entity Applicator :known false :spawnable false :classification "unknown" :mentions 7 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Dragon: 4 mentions, traits: none
(entity Dragon :known false :spawnable false :classification "unknown" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Ethereal: 3 mentions, traits: none
(entity Ethereal :known true :spawnable false :classification "known_non_spawnable" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Geralt: 17 mentions, traits: none
(entity Geralt :known true :spawnable true :classification "known_spawnable" :mentions 17 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Immediately: 4 mentions, traits: none
(entity Immediately :known false :spawnable false :classification "unknown" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Keeper: 12 mentions, traits: none
(entity Keeper :known false :spawnable false :classification "unknown" :mentions 12 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Keepers: 7 mentions, traits: none
(entity Keepers :known false :spawnable false :classification "unknown" :mentions 7 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Library: 10 mentions, traits: none
(entity Library :known false :spawnable false :classification "unknown" :mentions 10 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Mail: 4 mentions, traits: none
(entity Mail :known false :spawnable false :classification "unknown" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Nephoretti: 4 mentions, traits: none
(entity Nephoretti :known true :spawnable false :classification "known_non_spawnable" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Tiamat: 4 mentions, traits: none
(entity Tiamat :known true :spawnable false :classification "known_non_spawnable" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Zaron: 21 mentions, traits: none
(entity Zaron :known false :spawnable false :classification "unknown" :mentions 21 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)

; ---- Speaker Inference ----
(speaker line:71 Zaron :confidence 0.95)
(speaker line:114 Zaron :confidence 0.95)
(speaker line:172 Zaron :confidence 0.95)

; ---- Emotions ----
(emotion line:63 Keeper anger :confidence 0.90)
(emotion line:108 Zaron wonder :confidence 0.90)
(emotion line:143 Zaron fear :confidence 0.90)
(emotion line:143 Zaron vulnerability :confidence 0.90)
(emotion line:151 Geralt uncertainty :confidence 0.90)
(emotion line:188 Geralt uncertainty :confidence 0.90)
(emotion line:250 Aeon fear :confidence 0.90)

; ---- Actions ----
(action line:59 observe :confidence 0.90)
(action line:69 shaping :confidence 0.90)
(action line:135 gather :confidence 0.90)

; ---- Thoughts ----

; ---- Relationships ----
(relationship Aeon Keeper collaborate :confidence 0.70)
(relationship Aeon Keeper collaborate :confidence 0.70)

