; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Torrhen: 12 mentions, traits: none
(entity Torrhen :known true :spawnable true :classification "known_spawnable" :mentions 12 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Zephyr: 14 mentions, traits: none
(entity Zephyr :known true :spawnable true :classification "known_spawnable" :mentions 14 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)

; ---- Speaker Inference ----
(speaker line:33 Torrhen :confidence 0.95)
(speaker line:43 Torrhen :confidence 0.95)
(speaker line:53 Torrhen :confidence 0.95)
(speaker line:55 Zephyr :confidence 0.95)

; ---- Emotions ----

; ---- Actions ----
(action line:41 shaping :confidence 0.90)

; ---- Thoughts ----

; ---- Relationships ----
(relationship Torrhen Zephyr collaborate :confidence 0.70)
(relationship Torrhen Zephyr collaborate :confidence 0.70)

