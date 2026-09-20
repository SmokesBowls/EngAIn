; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Elyraen: 1 mentions, traits: pragmatic, analytical, creative, compassionate
(entity Elyraen :known true :spawnable true :classification "known_spawnable" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Giants: 6 mentions, traits: none
(entity Giants :known true :spawnable false :classification "known_non_spawnable" :mentions 6 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Kyreth: 1 mentions, traits: pragmatic, analytical, creative, compassionate
(entity Kyreth :known true :spawnable true :classification "known_spawnable" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Nephoretti: 7 mentions, traits: none
(entity Nephoretti :known true :spawnable false :classification "known_non_spawnable" :mentions 7 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Olythae: 1 mentions, traits: pragmatic, analytical, creative, compassionate
(entity Olythae :known true :spawnable true :classification "known_spawnable" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Senareth: 2 mentions, traits: pragmatic, analytical, creative, compassionate
(entity Senareth :known true :spawnable true :classification "known_spawnable" :mentions 2 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Tidecaller: 5 mentions, traits: none
(entity Tidecaller :known false :spawnable false :classification "unknown" :mentions 5 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Tidecallers: 5 mentions, traits: none
(entity Tidecallers :known false :spawnable false :classification "unknown" :mentions 5 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Torhh: 6 mentions, traits: pragmatic, analytical, creative, compassionate
(entity Torhh :known true :spawnable true :classification "known_spawnable" :mentions 6 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Vairis: 1 mentions, traits: pragmatic, analytical, creative, compassionate
(entity Vairis :known true :spawnable true :classification "known_spawnable" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)

; ---- Scene Content Observations ----
(scene_object "wall" :category "boundary" :normalized_type "wall" :mentions 1)

; ---- Speaker Inference ----
(speaker line:61 Torhh :confidence 0.95)

; ---- Emotions ----
(emotion line:29 Giants caution :confidence 0.90)
(emotion line:30 Torhh curiosity :confidence 0.90)
(emotion line:31 Tidecaller patience :confidence 0.90)
(emotion line:41 Tidecaller curiosity :confidence 0.90)
(emotion line:41 Tidecaller fear :confidence 0.90)
(emotion line:42 Tidecaller vulnerability :confidence 0.90)
(emotion line:44 Torhh fear :confidence 0.90)
(emotion line:44 Torhh gentleness :confidence 0.90)
(emotion line:61 Torhh fear :confidence 0.90)

; ---- Actions ----
(action line:33 approach :confidence 0.90)
(action line:41 retreat :confidence 0.90)
(action line:53 shaping :confidence 0.90)
(action line:66 shaping :confidence 0.90)
(action line:67 question :confidence 0.90)

; ---- Thoughts ----

; ---- Relationships ----
(relationship Torhh Senareth collaborate :confidence 0.70)

