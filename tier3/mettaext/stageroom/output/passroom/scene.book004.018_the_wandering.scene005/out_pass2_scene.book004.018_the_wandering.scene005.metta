; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Nibiru: 5 mentions, traits: none
(entity Nibiru :known true :spawnable false :classification "known_non_spawnable" :mentions 5 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Torrhen: 11 mentions, traits: none
(entity Torrhen :known true :spawnable true :classification "known_spawnable" :mentions 11 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Zephyr: 10 mentions, traits: none
(entity Zephyr :known true :spawnable true :classification "known_spawnable" :mentions 10 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)

; ---- Speaker Inference ----
(speaker line:43 Torrhen :confidence 0.95)
(speaker line:50 Zephyr :confidence 0.95)
(speaker line:52 Torrhen :confidence 0.95)
(speaker line:60 Zephyr :confidence 0.95)
(speaker line:62 Torrhen :confidence 0.95)

; ---- Emotions ----
(emotion line:45 Torrhen uncertainty :confidence 0.90)

; ---- Actions ----
(action line:36 speak :confidence 0.90)

; ---- Thoughts ----

