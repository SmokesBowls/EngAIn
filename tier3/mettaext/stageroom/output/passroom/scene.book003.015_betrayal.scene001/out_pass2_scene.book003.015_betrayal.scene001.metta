; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Giant: 5 mentions, traits: none
(entity Giant :known false :spawnable false :classification "unknown" :mentions 5 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Giants: 7 mentions, traits: none
(entity Giants :known true :spawnable false :classification "known_non_spawnable" :mentions 7 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Korrhan: 1 mentions, traits: none
(entity Korrhan :known false :spawnable false :classification "unknown" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Nephilim: 3 mentions, traits: none
(entity Nephilim :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)

; ---- Speaker Inference ----
(speaker line:43 Korrhan :confidence 0.95)

; ---- Emotions ----
(emotion line:15 Giant vulnerability :confidence 0.90)
(emotion line:27 Giant vulnerability :confidence 0.90)

; ---- Actions ----

; ---- Thoughts ----

