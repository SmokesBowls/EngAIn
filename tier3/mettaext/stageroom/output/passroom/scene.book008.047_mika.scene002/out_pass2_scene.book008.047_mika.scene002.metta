; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Geralt: 9 mentions, traits: none
(entity Geralt :known true :spawnable true :classification "known_spawnable" :mentions 9)
; Mika: 13 mentions, traits: none
(entity Mika :known true :spawnable true :classification "known_spawnable" :mentions 13)
; Month: 3 mentions, traits: none
(entity Month :known false :spawnable false :classification "unknown" :mentions 3)
; Zephyr: 5 mentions, traits: none
(entity Zephyr :known true :spawnable true :classification "known_spawnable" :mentions 5)

; ---- Speaker Inference ----
(speaker line:53 Mika :confidence 0.95)
(speaker line:82 Geralt :confidence 0.95)
(speaker line:129 Zephyr :confidence 0.95)
(speaker line:139 Zephyr :confidence 0.95)

; ---- Emotions ----
(emotion line:95 Month hope :confidence 0.90)

; ---- Actions ----
(action line:16 speak :confidence 0.90)
(action line:115 speak :confidence 0.90)

; ---- Thoughts ----

