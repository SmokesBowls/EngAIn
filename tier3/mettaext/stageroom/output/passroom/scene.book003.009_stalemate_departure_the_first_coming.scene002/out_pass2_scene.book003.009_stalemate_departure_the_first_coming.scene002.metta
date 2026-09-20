; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Anunnaki: 8 mentions, traits: none
(entity Anunnaki :known false :spawnable false :classification "unknown" :mentions 8 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Giant: 5 mentions, traits: none
(entity Giant :known false :spawnable false :classification "unknown" :mentions 5 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Needle: 4 mentions, traits: none
(entity Needle :known false :spawnable false :classification "unknown" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Pazuzu: 20 mentions, traits: none
(entity Pazuzu :known true :spawnable true :classification "known_spawnable" :mentions 20 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Torhh: 14 mentions, traits: none
(entity Torhh :known true :spawnable true :classification "known_spawnable" :mentions 14 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)

; ---- Speaker Inference ----
(speaker line:41 Pazuzu :confidence 0.95)
(speaker line:43 Torhh :confidence 0.95)
(speaker line:50 Pazuzu :confidence 0.95)
(speaker line:66 Torhh :confidence 0.95)
(speaker line:79 Pazuzu :confidence 0.95)
(speaker line:81 Torhh :confidence 0.95)

; ---- Emotions ----
(emotion line:56 Pazuzu hope :confidence 0.90)
(emotion line:64 Pazuzu hope :confidence 0.90)
(emotion line:95 Pazuzu hope :confidence 0.90)

; ---- Actions ----
(action line:29 observe :confidence 0.90)
(action line:31 question :confidence 0.90)
(action line:39 shaping :confidence 0.90)

; ---- Thoughts ----

; ---- Relationships ----
(relationship Pazuzu Giant trust :confidence 0.70)

