; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Elyraen: 1 mentions, traits: none
(entity Elyraen :known true :spawnable true :classification "known_spawnable" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Giants: 6 mentions, traits: none
(entity Giants :known true :spawnable false :classification "known_non_spawnable" :mentions 6 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Nephoretti: 4 mentions, traits: none
(entity Nephoretti :known true :spawnable false :classification "known_non_spawnable" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Senareth: 1 mentions, traits: none
(entity Senareth :known true :spawnable true :classification "known_spawnable" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Vairis: 1 mentions, traits: pragmatic
(entity Vairis :known true :spawnable true :classification "known_spawnable" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)

; ---- Scene Content Observations ----
(scene_object "settlement" :category "settlement" :normalized_type "settlement" :mentions 2)

; ---- Speaker Inference ----
(speaker line:52 Vairis :confidence 0.95)
(speaker line:54 Senareth :confidence 0.95)
(speaker line:61 Elyraen :confidence 0.95)

; ---- Emotions ----

; ---- Actions ----
(action line:56 gather :confidence 0.90)
(action line:57 approach :confidence 0.90)
(action line:57 shaping :confidence 0.90)
(action line:57 submission :confidence 0.90)

; ---- Thoughts ----

