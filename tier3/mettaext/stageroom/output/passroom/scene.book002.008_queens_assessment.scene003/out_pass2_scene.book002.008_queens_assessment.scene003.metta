; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Giant: 3 mentions, traits: none
(entity Giant :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Igigi: 3 mentions, traits: none
(entity Igigi :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Pazuzu: 7 mentions, traits: none
(entity Pazuzu :known true :spawnable true :classification "known_spawnable" :mentions 7 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Sundering: 7 mentions, traits: patient
(entity Sundering :known false :spawnable false :classification "unknown" :mentions 7 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Torhh: 10 mentions, traits: none
(entity Torhh :known true :spawnable true :classification "known_spawnable" :mentions 10 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)

; ---- Speaker Inference ----
(speaker line:35 Pazuzu :confidence 0.95)
(speaker line:42 Torhh :confidence 0.95)
(speaker line:44 Pazuzu :confidence 0.95)
(speaker line:46 Torhh :confidence 0.95)
(speaker line:48 Pazuzu :confidence 0.95)

; ---- Emotions ----
(emotion line:63 Sundering patience :confidence 0.90)

; ---- Actions ----
(action line:12 shaping :confidence 0.90)
(action line:24 shaping :confidence 0.90)

; ---- Thoughts ----

