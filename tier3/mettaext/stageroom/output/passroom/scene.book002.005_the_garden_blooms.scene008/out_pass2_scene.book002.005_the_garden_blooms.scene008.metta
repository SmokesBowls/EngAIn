; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Aeon: 3 mentions, traits: none
(entity Aeon :known false :spawnable false :classification "unknown" :mentions 3 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Anunnaki: 4 mentions, traits: none
(entity Anunnaki :known false :spawnable false :classification "unknown" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Coming: 3 mentions, traits: none
(entity Coming :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Elyraen: 0 mentions, traits: none
(entity Elyraen :known true :spawnable true :classification "known_spawnable" :mentions 0 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; First: 5 mentions, traits: none
(entity First :known false :spawnable false :classification "unknown" :mentions 5 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Garden: 9 mentions, traits: none
(entity Garden :known false :spawnable false :classification "unknown" :mentions 9 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Giant: 0 mentions, traits: none
(entity Giant :known false :spawnable false :classification "unknown" :mentions 0 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Giants: 3 mentions, traits: none
(entity Giants :known true :spawnable false :classification "known_non_spawnable" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Keepers: 3 mentions, traits: none
(entity Keepers :known false :spawnable false :classification "unknown" :mentions 3 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Nephoretti: 3 mentions, traits: none
(entity Nephoretti :known true :spawnable false :classification "known_non_spawnable" :mentions 3 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Senareth: 0 mentions, traits: none
(entity Senareth :known true :spawnable true :classification "known_spawnable" :mentions 0 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Seraneth: 4 mentions, traits: none
(entity Seraneth :known false :spawnable false :classification "unknown" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)

; ---- Scene Content Observations ----
(scene_object "valley" :category "terrain_feature" :normalized_type "valley" :mentions 5)

; ---- Speaker Inference ----

; ---- Emotions ----
(emotion line:29 Giants joy :confidence 0.90)
(emotion line:91 Garden fear :confidence 0.90)

; ---- Actions ----
(action line:29 gather :confidence 0.90)
(action line:93 observe :confidence 0.90)

; ---- Thoughts ----

; ---- Relationships ----
(relationship Giants Nephoretti collaborate :confidence 0.70)
(relationship Giants Nephoretti collaborate :confidence 0.70)

