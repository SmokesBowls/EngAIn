; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Pythagoras: 11 mentions, traits: none
(entity Pythagoras :known false :spawnable false :classification "unknown" :mentions 11 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Sage: 17 mentions, traits: none
(entity Sage :known false :spawnable false :classification "unknown" :mentions 17 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Torrhen: 15 mentions, traits: none
(entity Torrhen :known true :spawnable true :classification "known_spawnable" :mentions 15 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)

; ---- Speaker Inference ----
(speaker line:36 Torrhen :confidence 0.95)
(speaker line:40 Torrhen :confidence 0.95)
(speaker line:48 Torrhen :confidence 0.95)
(speaker line:56 Torrhen :confidence 0.95)
(speaker line:62 Pythagoras :confidence 0.95)
(speaker line:64 Torrhen :confidence 0.95)
(speaker line:76 Torrhen :confidence 0.95)

; ---- Emotions ----
(emotion line:59 Pythagoras curiosity :confidence 0.90)

; ---- Actions ----
(action line:40 approach :confidence 0.90)
(action line:59 approach :confidence 0.90)
(action line:59 observe :confidence 0.90)
(action line:69 speak :confidence 0.90)
(action line:78 approach :confidence 0.90)

; ---- Thoughts ----

; ---- Relationships ----
(relationship Sage Torrhen collaborate :confidence 0.70)
(relationship Sage Torrhen collaborate :confidence 0.70)

