; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Eduhauana: 6 mentions, traits: none
(entity Eduhauana :known false :spawnable false :classification "unknown" :mentions 6 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Giant: 4 mentions, traits: none
(entity Giant :known false :spawnable false :classification "unknown" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Giants: 10 mentions, traits: none
(entity Giants :known true :spawnable false :classification "known_non_spawnable" :mentions 10 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Igigi: 8 mentions, traits: none
(entity Igigi :known false :spawnable false :classification "unknown" :mentions 8 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Ishara: 5 mentions, traits: none
(entity Ishara :known false :spawnable false :classification "unknown" :mentions 5 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Pazuzu: 10 mentions, traits: analytical
(entity Pazuzu :known true :spawnable true :classification "known_spawnable" :mentions 10 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Queen: 8 mentions, traits: none
(entity Queen :known false :spawnable false :classification "unknown" :mentions 8 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Sundering: 3 mentions, traits: none
(entity Sundering :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)

; ---- Speaker Inference ----
(speaker line:79 Ishara :confidence 0.95)
(speaker line:81 Pazuzu :confidence 0.95)

; ---- Emotions ----

; ---- Actions ----
(action line:48 observe :confidence 0.90)
(action line:111 observe :confidence 0.90)

; ---- Thoughts ----

; ---- Relationships ----
(relationship Giant Giants trust :confidence 0.70)
(relationship Giant Giants trust :confidence 0.70)

