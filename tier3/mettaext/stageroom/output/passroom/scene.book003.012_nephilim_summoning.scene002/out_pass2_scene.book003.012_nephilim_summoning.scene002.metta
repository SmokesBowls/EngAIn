; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Aeon: 8 mentions, traits: none
(entity Aeon :known false :spawnable false :classification "unknown" :mentions 8 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Communion: 4 mentions, traits: none
(entity Communion :known false :spawnable false :classification "unknown" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Giant: 6 mentions, traits: none
(entity Giant :known false :spawnable false :classification "unknown" :mentions 6 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Giants: 7 mentions, traits: none
(entity Giants :known true :spawnable false :classification "known_non_spawnable" :mentions 7 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Igigi: 3 mentions, traits: none
(entity Igigi :known false :spawnable false :classification "unknown" :mentions 3 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Keepers: 10 mentions, traits: none
(entity Keepers :known false :spawnable false :classification "unknown" :mentions 10 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Korrhan: 2 mentions, traits: none
(entity Korrhan :known false :spawnable false :classification "unknown" :mentions 2 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Nephilim: 13 mentions, traits: none
(entity Nephilim :known false :spawnable false :classification "unknown" :mentions 13 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Pazuzu: 1 mentions, traits: none
(entity Pazuzu :known true :spawnable true :classification "known_spawnable" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Saresh: 0 mentions, traits: none
(entity Saresh :known false :spawnable false :classification "unknown" :mentions 0 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Torhh: 1 mentions, traits: none
(entity Torhh :known true :spawnable true :classification "known_spawnable" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Torrhen: 7 mentions, traits: none
(entity Torrhen :known true :spawnable true :classification "known_spawnable" :mentions 7 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Veil: 4 mentions, traits: none
(entity Veil :known true :spawnable false :classification "known_non_spawnable" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)

; ---- Scene Content Observations ----
(scene_object "valley" :category "terrain_feature" :normalized_type "valley" :mentions 3)

; ---- Speaker Inference ----
(speaker line:53 Torhh :confidence 0.95)
(speaker line:98 Korrhan :confidence 0.95)
(speaker line:124 Korrhan :confidence 0.95)

; ---- Emotions ----
(emotion line:45 Giant patience :confidence 0.90)
(emotion line:115 Nephilim vulnerability :confidence 0.90)
(emotion line:140 Giant exhaustion :confidence 0.90)
(emotion line:140 Giant fear :confidence 0.90)
(emotion line:142 Giant hope :confidence 0.90)

; ---- Actions ----
(action line:77 vrill_energy :confidence 0.90)

; ---- Thoughts ----

; ---- Relationships ----
(relationship Communion Torhh collaborate :confidence 0.70)

