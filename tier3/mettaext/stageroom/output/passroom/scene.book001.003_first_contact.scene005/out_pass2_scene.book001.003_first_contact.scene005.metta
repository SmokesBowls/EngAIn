; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Elyraen: 1 mentions, traits: none
(entity Elyraen :known true :spawnable true :classification "known_spawnable" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Giant: 5 mentions, traits: none
(entity Giant :known false :spawnable false :classification "unknown" :mentions 5 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Giants: 3 mentions, traits: none
(entity Giants :known true :spawnable false :classification "known_non_spawnable" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Kyreth: 12 mentions, traits: none
(entity Kyreth :known true :spawnable true :classification "known_spawnable" :mentions 12 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Nephoretti: 3 mentions, traits: none
(entity Nephoretti :known true :spawnable false :classification "known_non_spawnable" :mentions 3 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Senareth: 1 mentions, traits: none
(entity Senareth :known true :spawnable true :classification "known_spawnable" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Torhh: 9 mentions, traits: none
(entity Torhh :known true :spawnable true :classification "known_spawnable" :mentions 9 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Vairis: 1 mentions, traits: none
(entity Vairis :known true :spawnable true :classification "known_spawnable" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)

; ---- Speaker Inference ----
(speaker line:87 Elyraen :confidence 0.95)
(speaker line:89 Senareth :confidence 0.95)
(speaker line:91 Vairis :confidence 0.95)

; ---- Emotions ----
(emotion line:37 Kyreth anxiety :confidence 0.90)
(emotion line:37 Kyreth fear :confidence 0.90)
(emotion line:49 Kyreth fear :confidence 0.90)
(emotion line:79 Kyreth wonder :confidence 1.00)
(emotion line:80 Kyreth triumph :confidence 1.00)
(emotion line:81 Kyreth relief :confidence 1.00)
(emotion line:82 Kyreth hope :confidence 1.00)

; ---- Actions ----
(action line:27 vrill_manipulation :confidence 0.90)
(action line:32 approach :confidence 0.90)
(action line:40 approach :confidence 0.90)
(action line:45 submission :confidence 0.90)
(action line:51 attack :confidence 0.90)
(action line:59 approach :confidence 0.90)
(action line:61 vrill_manipulation :confidence 0.90)
(action line:76 shaping :confidence 0.90)
(action line:78 retreat :confidence 0.90)
(action line:78 submission :confidence 0.90)

; ---- Thoughts ----

; ---- Relationships ----
(relationship Kyreth Torhh collaborate :confidence 0.70)

