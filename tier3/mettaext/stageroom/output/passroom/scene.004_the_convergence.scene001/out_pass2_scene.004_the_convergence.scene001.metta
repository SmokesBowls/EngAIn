; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Giant: 3 mentions, traits: creative
(entity Giant :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Mountain: 4 mentions, traits: creative
(entity Mountain :known false :spawnable false :classification "unknown" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Senareth: 3 mentions, traits: creative
(entity Senareth :known true :spawnable true :classification "known_spawnable" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Torhh: 3 mentions, traits: creative
(entity Torhh :known true :spawnable true :classification "known_spawnable" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)

; ---- Speaker Inference ----

; ---- Emotions ----
(emotion line:13 Giant fear :confidence 0.90)

; ---- Actions ----
(action line:13 shaping :confidence 0.90)
(action line:13 submission :confidence 0.90)

; ---- Thoughts ----

; ---- Relationships ----
(relationship Giant Mountain trust :confidence 0.70)

