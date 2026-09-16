; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Anunnaki: 3 mentions, traits: none
(entity Anunnaki :known false :spawnable false :classification "unknown" :mentions 3)
; Elder: 3 mentions, traits: none
(entity Elder :known false :spawnable false :classification "unknown" :mentions 3)
; Pazuzu: 4 mentions, traits: none
(entity Pazuzu :known true :spawnable true :classification "known_spawnable" :mentions 4)
; Zephyr: 4 mentions, traits: none
(entity Zephyr :known true :spawnable true :classification "known_spawnable" :mentions 4)

; ---- Speaker Inference ----
(speaker line:14 Zephyr :confidence 0.95)

; ---- Emotions ----
(emotion line:29 Zephyr hope :confidence 0.90)
(emotion line:32 Pazuzu uncertainty :confidence 0.90)
(emotion line:38 Elder hope :confidence 0.90)

; ---- Actions ----
(action line:22 speak :confidence 0.90)

; ---- Thoughts ----

