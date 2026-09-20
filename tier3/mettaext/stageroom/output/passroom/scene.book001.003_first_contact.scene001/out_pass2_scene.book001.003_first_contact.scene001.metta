; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Elyraen: 2 mentions, traits: patient
(entity Elyraen :known true :spawnable true :classification "known_spawnable" :mentions 2 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Giants: 3 mentions, traits: none
(entity Giants :known true :spawnable false :classification "known_non_spawnable" :mentions 3 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Nephoretti: 6 mentions, traits: none
(entity Nephoretti :known true :spawnable false :classification "known_non_spawnable" :mentions 6 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Olythae: 1 mentions, traits: none
(entity Olythae :known true :spawnable true :classification "known_spawnable" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Pelagor: 0 mentions, traits: none
(entity Pelagor :known true :spawnable true :classification "known_spawnable" :mentions 0 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Senareth: 9 mentions, traits: none
(entity Senareth :known true :spawnable true :classification "known_spawnable" :mentions 9 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Tomorrow: 3 mentions, traits: none
(entity Tomorrow :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Torhh: 1 mentions, traits: none
(entity Torhh :known true :spawnable true :classification "known_spawnable" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Vairis: 1 mentions, traits: none
(entity Vairis :known true :spawnable true :classification "known_spawnable" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; someone: 1 mentions, traits: none
(entity someone :known true :spawnable false :classification "known_non_spawnable" :mentions 1 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)

; ---- Scene Content Observations ----
(scene_object "wall" :category "boundary" :normalized_type "wall" :mentions 1)

; ---- Speaker Inference ----
(speaker line:48 Vairis :confidence 0.95)
(speaker line:50 Elyraen :confidence 0.95)
(speaker line:52 Olythae :confidence 0.95)
(speaker line:66 Senareth :confidence 0.95)
(speaker line:68 someone :confidence 0.95)
(speaker line:70 Elyraen :confidence 0.95)
(speaker line:76 Senareth :confidence 0.95)

; ---- Emotions ----
(emotion line:12 Nephoretti vulnerability :confidence 0.90)
(emotion line:22 Nephoretti vulnerability :confidence 0.90)
(emotion line:36 Torhh curiosity :confidence 0.90)
(emotion line:56 Nephoretti uncertainty :confidence 1.00)
(emotion line:57 Nephoretti fear :confidence 0.90)
(emotion line:58 Nephoretti caution :confidence 0.90)
(emotion line:58 Nephoretti curiosity :confidence 0.90)
(emotion line:72 Senareth gratitude :confidence 0.90)
(emotion line:73 Elyraen patience :confidence 0.90)

; ---- Actions ----
(action line:35 retreat :confidence 0.90)
(action line:36 retreat :confidence 0.90)
(action line:37 observe :confidence 0.90)
(action line:39 huddle :confidence 0.90)
(action line:40 vrill_energy :confidence 0.90)
(action line:79 retreat :confidence 0.90)

; ---- Thoughts ----

