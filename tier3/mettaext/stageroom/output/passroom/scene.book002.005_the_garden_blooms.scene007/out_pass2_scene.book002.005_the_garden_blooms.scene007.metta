; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Aeon: 4 mentions, traits: analytical
(entity Aeon :known false :spawnable false :classification "unknown" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Contact: 3 mentions, traits: none
(entity Contact :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Elyraen: 1 mentions, traits: analytical
(entity Elyraen :known true :spawnable true :classification "known_spawnable" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Festival: 3 mentions, traits: none
(entity Festival :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; First: 3 mentions, traits: none
(entity First :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Giant: 2 mentions, traits: none
(entity Giant :known false :spawnable false :classification "unknown" :mentions 2 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Giants: 10 mentions, traits: none
(entity Giants :known true :spawnable false :classification "known_non_spawnable" :mentions 10 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Keepers: 4 mentions, traits: analytical
(entity Keepers :known false :spawnable false :classification "unknown" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Nephoretti: 7 mentions, traits: none
(entity Nephoretti :known true :spawnable false :classification "known_non_spawnable" :mentions 7 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Senareth: 1 mentions, traits: none
(entity Senareth :known true :spawnable true :classification "known_spawnable" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Seraneth: 1 mentions, traits: none
(entity Seraneth :known false :spawnable false :classification "unknown" :mentions 1 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)

; ---- Scene Content Observations ----
(scene_object "valley" :category "terrain_feature" :normalized_type "valley" :mentions 1)

; ---- Speaker Inference ----
(speaker line:53 Elyraen :confidence 0.95)
(speaker line:55 Seraneth :confidence 0.95)

; ---- Emotions ----
(emotion line:65 Festival fear :confidence 0.90)
(emotion line:66 Festival fear :confidence 0.90)

; ---- Actions ----
(action line:60 respond :confidence 0.90)
(action line:65 flee :confidence 0.90)
(action line:66 gather :confidence 0.90)

; ---- Thoughts ----

; ---- Relationships ----
(relationship Giants Nephoretti collaborate :confidence 0.70)

