; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Applicator: 1 mentions, traits: none
(entity Applicator :known false :spawnable false :classification "unknown" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Ethereal: 3 mentions, traits: none
(entity Ethereal :known true :spawnable false :classification "known_non_spawnable" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Geralt: 11 mentions, traits: none
(entity Geralt :known true :spawnable true :classification "known_spawnable" :mentions 11 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Immediately: 4 mentions, traits: none
(entity Immediately :known false :spawnable false :classification "unknown" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Oreck: 1 mentions, traits: none
(entity Oreck :known true :spawnable true :classification "known_spawnable" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)

; ---- Speaker Inference ----
(speaker line:85 Geralt :confidence 0.95)
(speaker line:94 Geralt :confidence 0.95)

; ---- Emotions ----
(emotion line:12 Geralt uncertainty :confidence 0.90)
(emotion line:15 Geralt uncertainty :confidence 0.90)
(emotion line:24 Geralt uncertainty :confidence 0.90)
(emotion line:27 Geralt uncertainty :confidence 0.90)
(emotion line:69 Geralt fear :confidence 0.90)

; ---- Actions ----
(action line:32 shaping :confidence 0.90)
(action line:92 speak :confidence 0.90)

; ---- Thoughts ----

