; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Individual: 3 mentions, traits: analytical
(entity Individual :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Sage: 16 mentions, traits: analytical
(entity Sage :known false :spawnable false :classification "unknown" :mentions 16 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Torrhen: 16 mentions, traits: analytical
(entity Torrhen :known true :spawnable true :classification "known_spawnable" :mentions 16 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)

; ---- Speaker Inference ----
(speaker line:34 Torrhen :confidence 0.95)
(speaker line:37 Torrhen :confidence 0.95)
(speaker line:42 Torrhen :confidence 0.95)
(speaker line:50 Torrhen :confidence 0.95)
(speaker line:62 Torrhen :confidence 0.95)

; ---- Emotions ----

; ---- Actions ----
(action line:44 question :confidence 0.90)
(action line:61 approach :confidence 0.90)

; ---- Thoughts ----

; ---- Relationships ----
(relationship Torrhen Individual collaborate :confidence 0.70)

