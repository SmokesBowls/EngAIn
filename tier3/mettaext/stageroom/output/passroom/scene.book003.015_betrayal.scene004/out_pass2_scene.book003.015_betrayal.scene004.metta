; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; After: 4 mentions, traits: none
(entity After :known false :spawnable false :classification "unknown" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Anunnaki: 5 mentions, traits: none
(entity Anunnaki :known false :spawnable false :classification "unknown" :mentions 5 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Giant: 8 mentions, traits: none
(entity Giant :known false :spawnable false :classification "unknown" :mentions 8 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Giants: 6 mentions, traits: none
(entity Giants :known true :spawnable false :classification "known_non_spawnable" :mentions 6 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Needle: 7 mentions, traits: none
(entity Needle :known false :spawnable false :classification "unknown" :mentions 7 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Pazuzu: 6 mentions, traits: none
(entity Pazuzu :known true :spawnable true :classification "known_spawnable" :mentions 6 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Queen: 3 mentions, traits: patient
(entity Queen :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Saresh: 1 mentions, traits: none
(entity Saresh :known false :spawnable false :classification "unknown" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Tidecaller: 3 mentions, traits: none
(entity Tidecaller :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Torhh: 4 mentions, traits: none
(entity Torhh :known true :spawnable true :classification "known_spawnable" :mentions 4 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)

; ---- Speaker Inference ----
(speaker line:39 Pazuzu :confidence 0.95)
(speaker line:51 Pazuzu :confidence 0.95)
(speaker line:55 Pazuzu :confidence 0.95)

; ---- Emotions ----
(emotion line:43 Queen patience :confidence 0.90)
(emotion line:45 Torhh patience :confidence 1.00)
(emotion line:47 Giant vulnerability :confidence 0.90)

; ---- Actions ----
(action line:47 retreat :confidence 0.90)
(action line:64 vrill_energy :confidence 0.90)

; ---- Thoughts ----

; ---- Relationships ----
(relationship Giant Torhh trust :confidence 0.70)
(relationship Giant Needle trust :confidence 0.70)
(relationship Giant Torhh trust :confidence 0.70)
(relationship Giant Needle trust :confidence 0.70)
(relationship Tidecaller Giant collaborate :confidence 0.70)
(relationship Giant Giants trust :confidence 0.70)
(relationship Giant Giants trust :confidence 0.70)

