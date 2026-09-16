; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Caelum: 1 mentions, traits: none
(entity Caelum :known false :spawnable false :classification "unknown" :mentions 1)
; Here: 3 mentions, traits: none
(entity Here :known false :spawnable false :classification "unknown" :mentions 3)
; Kronocht: 4 mentions, traits: none
(entity Kronocht :known false :spawnable false :classification "unknown" :mentions 4)
; Mika: 6 mentions, traits: none
(entity Mika :known true :spawnable true :classification "known_spawnable" :mentions 6)
; Path: 6 mentions, traits: none
(entity Path :known false :spawnable false :classification "unknown" :mentions 6)
; Thang: 1 mentions, traits: none
(entity Thang :known false :spawnable false :classification "unknown" :mentions 1)
; Tran: 12 mentions, traits: none
(entity Tran :known true :spawnable true :classification "known_spawnable" :mentions 12)
; Violet: 10 mentions, traits: none
(entity Violet :known false :spawnable false :classification "unknown" :mentions 10)
; Zaron: 6 mentions, traits: none
(entity Zaron :known false :spawnable false :classification "unknown" :mentions 6)

; ---- Speaker Inference ----
(speaker line:24 Kronocht :confidence 0.95)
(speaker line:38 Caelum :confidence 0.95)
(speaker line:47 Tran :confidence 0.95)
(speaker line:67 Thang :confidence 0.95)
(speaker line:80 Tran :confidence 0.95)

; ---- Emotions ----
(emotion line:91 Tran uncertainty :confidence 0.90)
(emotion line:108 Zaron uncertainty :confidence 0.90)

; ---- Actions ----
(action line:74 observe :confidence 0.90)
(action line:105 observe :confidence 0.90)

; ---- Thoughts ----
(thought line:16 Violet :confidence 0.90)
(thought line:17 Path :confidence 0.90)
(thought line:56 Path :confidence 0.90)
(thought line:85 Violet :confidence 0.90)
(thought line:89 Path :confidence 0.95)
(thought line:93 Tran :confidence 0.95)
(thought line:96 Path :confidence 0.95)
(thought line:99 Tran :confidence 0.95)
(thought line:102 Tran :confidence 0.95)

