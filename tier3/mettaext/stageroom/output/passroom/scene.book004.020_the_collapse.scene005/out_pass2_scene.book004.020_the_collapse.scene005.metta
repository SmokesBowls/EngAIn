; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Anunnaki: 17 mentions, traits: none
(entity Anunnaki :known false :spawnable false :classification "unknown" :mentions 17 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Individual: 3 mentions, traits: none
(entity Individual :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Sage: 11 mentions, traits: none
(entity Sage :known false :spawnable false :classification "unknown" :mentions 11 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Seven: 3 mentions, traits: none
(entity Seven :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Synthesis: 4 mentions, traits: none
(entity Synthesis :known false :spawnable false :classification "unknown" :mentions 4 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Torrhen: 10 mentions, traits: none
(entity Torrhen :known true :spawnable true :classification "known_spawnable" :mentions 10 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)

; ---- Speaker Inference ----
(speaker line:38 Torrhen :confidence 0.95)
(speaker line:43 Torrhen :confidence 0.95)
(speaker line:48 Torrhen :confidence 0.95)
(speaker line:66 Torrhen :confidence 0.95)
(speaker line:81 Torrhen :confidence 0.95)
(speaker line:90 Torrhen :confidence 0.95)

; ---- Emotions ----
(emotion line:66 Torrhen joy :confidence 0.90)
(emotion line:74 Anunnaki uncertainty :confidence 1.00)
(emotion line:82 Anunnaki hope :confidence 0.90)
(emotion line:82 Anunnaki uncertainty :confidence 0.90)
(emotion line:82 Anunnaki wonder :confidence 0.90)

; ---- Actions ----
(action line:36 approach :confidence 0.90)
(action line:47 approach :confidence 0.90)
(action line:78 speak :confidence 0.90)

; ---- Thoughts ----

; ---- Relationships ----
(relationship Sage Torrhen collaborate :confidence 0.70)

