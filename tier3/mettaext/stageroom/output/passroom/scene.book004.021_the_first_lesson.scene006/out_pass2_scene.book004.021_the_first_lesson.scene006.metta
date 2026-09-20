; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; First: 8 mentions, traits: none
(entity First :known false :spawnable false :classification "unknown" :mentions 8 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Keen: 5 mentions, traits: none
(entity Keen :known false :spawnable false :classification "unknown" :mentions 5 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Sage: 10 mentions, traits: analytical
(entity Sage :known false :spawnable false :classification "unknown" :mentions 10 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Torrhen: 11 mentions, traits: none
(entity Torrhen :known true :spawnable true :classification "known_spawnable" :mentions 11 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Tran: 5 mentions, traits: compassionate
(entity Tran :known true :spawnable true :classification "known_spawnable" :mentions 5 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Year: 5 mentions, traits: none
(entity Year :known false :spawnable false :classification "unknown" :mentions 5 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)

; ---- Speaker Inference ----
(speaker line:34 Torrhen :confidence 0.95)
(speaker line:48 Torrhen :confidence 0.95)
(speaker line:54 Torrhen :confidence 0.95)
(speaker line:60 Torrhen :confidence 0.95)
(speaker line:71 Torrhen :confidence 0.95)

; ---- Emotions ----
(emotion line:62 Sage anticipation :confidence 1.00)
(emotion line:65 Tran gentleness :confidence 0.90)

; ---- Actions ----
(action line:59 speak :confidence 0.90)
(action line:70 observe :confidence 0.90)
(action line:72 gather :confidence 0.90)

; ---- Thoughts ----
(thought line:42 Sage :confidence 0.95)

