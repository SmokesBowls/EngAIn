; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Path: 4 mentions, traits: none
(entity Path :known false :spawnable false :classification "unknown" :mentions 4)
; Thang: 2 mentions, traits: none
(entity Thang :known false :spawnable false :classification "unknown" :mentions 2)
; Tran: 10 mentions, traits: none
(entity Tran :known true :spawnable true :classification "known_spawnable" :mentions 10)
; Violet: 7 mentions, traits: none
(entity Violet :known false :spawnable false :classification "unknown" :mentions 7)
; Zaron: 6 mentions, traits: none
(entity Zaron :known false :spawnable false :classification "unknown" :mentions 6)

; ---- Speaker Inference ----
(speaker line:50 Tran :confidence 0.95)
(speaker line:89 Thang :confidence 0.95)
(speaker line:107 Thang :confidence 0.95)

; ---- Emotions ----
(emotion line:16 Path uncertainty :confidence 0.90)
(emotion line:46 Tran fear :confidence 0.90)
(emotion line:47 Tran curiosity :confidence 0.90)
(emotion line:47 Tran fear :confidence 0.90)
(emotion line:47 Tran hope :confidence 0.90)
(emotion line:86 they gentleness :confidence 0.90)

; ---- Actions ----
(action line:65 speak :confidence 0.90)
(action line:100 approach :confidence 0.90)

; ---- Thoughts ----
(thought line:11 Path :confidence 0.90)
(thought line:33 Tran :confidence 0.90)
(thought line:58 Violet :confidence 0.90)
(thought line:84 they :confidence 0.90)

