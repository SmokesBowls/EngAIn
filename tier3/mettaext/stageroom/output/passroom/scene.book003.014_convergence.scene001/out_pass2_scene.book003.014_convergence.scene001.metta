; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Aeon: 3 mentions, traits: none
(entity Aeon :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Desert: 0 mentions, traits: none
(entity Desert :known false :spawnable false :classification "unknown" :mentions 0 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Forest: 2 mentions, traits: none
(entity Forest :known false :spawnable false :classification "unknown" :mentions 2 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Giant: 7 mentions, traits: none
(entity Giant :known false :spawnable false :classification "unknown" :mentions 7 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Giants: 7 mentions, traits: none
(entity Giants :known true :spawnable false :classification "known_non_spawnable" :mentions 7 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Highland: 2 mentions, traits: none
(entity Highland :known false :spawnable false :classification "unknown" :mentions 2 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Igigi: 5 mentions, traits: none
(entity Igigi :known false :spawnable false :classification "unknown" :mentions 5 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Keepers: 3 mentions, traits: none
(entity Keepers :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Korrhan: 3 mentions, traits: none
(entity Korrhan :known false :spawnable false :classification "unknown" :mentions 3 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Mountain: 3 mentions, traits: none
(entity Mountain :known false :spawnable false :classification "unknown" :mentions 3 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Nephilim: 7 mentions, traits: none
(entity Nephilim :known false :spawnable false :classification "unknown" :mentions 7 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Pazuzu: 5 mentions, traits: none
(entity Pazuzu :known true :spawnable true :classification "known_spawnable" :mentions 5 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Saresh: 0 mentions, traits: none
(entity Saresh :known false :spawnable false :classification "unknown" :mentions 0 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Subterranean: 2 mentions, traits: none
(entity Subterranean :known false :spawnable false :classification "unknown" :mentions 2 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Tidecallers: 3 mentions, traits: none
(entity Tidecallers :known false :spawnable false :classification "unknown" :mentions 3 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Torhh: 1 mentions, traits: none
(entity Torhh :known true :spawnable true :classification "known_spawnable" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)

; ---- Scene Content Observations ----
(scene_object "valley" :category "terrain_feature" :normalized_type "valley" :mentions 6)

; ---- Speaker Inference ----
(speaker line:58 Torhh :confidence 0.95)
(speaker line:86 Pazuzu :confidence 0.95)

; ---- Emotions ----
(emotion line:75 Giant patience :confidence 0.90)
(emotion line:112 Giant anger :confidence 0.90)

; ---- Actions ----
(action line:34 gather :confidence 0.90)
(action line:109 vrill_energy :confidence 0.90)

; ---- Thoughts ----

; ---- Relationships ----
(relationship Aeon Keepers collaborate :confidence 0.70)

