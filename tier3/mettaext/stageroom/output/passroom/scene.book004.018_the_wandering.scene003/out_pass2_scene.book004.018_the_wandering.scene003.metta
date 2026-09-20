; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Torrhen: 10 mentions, traits: patient
(entity Torrhen :known true :spawnable true :classification "known_spawnable" :mentions 10 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Zephyr: 8 mentions, traits: none
(entity Zephyr :known true :spawnable true :classification "known_spawnable" :mentions 8 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)

; ---- Speaker Inference ----
(speaker line:57 Torrhen :confidence 0.95)
(speaker line:59 Zephyr :confidence 0.95)

; ---- Emotions ----
(emotion line:32 Torrhen patience :confidence 0.90)
(emotion line:49 Torrhen wonder :confidence 0.90)

; ---- Actions ----
(action line:40 shaping :confidence 0.90)

; ---- Thoughts ----

; ---- Relationships ----
(relationship Torrhen Zephyr collaborate :confidence 0.70)
(relationship Torrhen Zephyr collaborate :confidence 0.70)

