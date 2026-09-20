; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Aerie: 5 mentions, traits: none
(entity Aerie :known false :spawnable false :classification "unknown" :mentions 5 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Forest: 5 mentions, traits: none
(entity Forest :known false :spawnable false :classification "unknown" :mentions 5 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Giant: 4 mentions, traits: none
(entity Giant :known false :spawnable false :classification "unknown" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Giants: 12 mentions, traits: none
(entity Giants :known true :spawnable false :classification "known_non_spawnable" :mentions 12 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Gruulith: 12 mentions, traits: none
(entity Gruulith :known false :spawnable false :classification "unknown" :mentions 12 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Korrhan: 13 mentions, traits: none
(entity Korrhan :known false :spawnable false :classification "unknown" :mentions 13 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Peaks: 7 mentions, traits: none
(entity Peaks :known false :spawnable false :classification "unknown" :mentions 7 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Singing: 7 mentions, traits: none
(entity Singing :known false :spawnable false :classification "unknown" :mentions 7 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Tidecallers: 5 mentions, traits: none
(entity Tidecallers :known false :spawnable false :classification "unknown" :mentions 5 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)

; ---- Scene Content Observations ----
(scene_object "ridge" :category "terrain_feature" :normalized_type "ridge" :mentions 1)
(scene_object "wall" :category "boundary" :normalized_type "wall" :mentions 1)

; ---- Speaker Inference ----
(speaker line:75 Korrhan :confidence 0.95)

; ---- Emotions ----
(emotion line:40 Aerie patience :confidence 0.90)
(emotion line:99 Giant fear :confidence 0.90)

; ---- Actions ----
(action line:54 attack :confidence 0.90)
(action line:86 approach :confidence 0.90)

; ---- Thoughts ----

