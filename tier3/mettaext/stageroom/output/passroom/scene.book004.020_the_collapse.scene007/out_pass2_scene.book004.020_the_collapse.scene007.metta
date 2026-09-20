; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Sage: 10 mentions, traits: none
(entity Sage :known false :spawnable false :classification "unknown" :mentions 10 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Species: 3 mentions, traits: none
(entity Species :known false :spawnable false :classification "unknown" :mentions 3 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Torrhen: 10 mentions, traits: none
(entity Torrhen :known true :spawnable true :classification "known_spawnable" :mentions 10 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)

; ---- Speaker Inference ----
(speaker line:42 Torrhen :confidence 0.95)
(speaker line:54 Torrhen :confidence 0.95)
(speaker line:74 Torrhen :confidence 0.95)

; ---- Emotions ----
(emotion line:42 Torrhen anticipation :confidence 1.00)

; ---- Actions ----
(action line:34 gather :confidence 0.90)
(action line:40 observe :confidence 0.90)

; ---- Thoughts ----

