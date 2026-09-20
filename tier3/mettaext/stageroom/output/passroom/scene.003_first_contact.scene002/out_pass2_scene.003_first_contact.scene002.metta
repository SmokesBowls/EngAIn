; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Elyraen: 1 mentions, traits: none
(entity Elyraen :known true :spawnable true :classification "known_spawnable" :mentions 1 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Giant: 9 mentions, traits: none
(entity Giant :known false :spawnable false :classification "unknown" :mentions 9 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Giants: 3 mentions, traits: none
(entity Giants :known true :spawnable false :classification "known_non_spawnable" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Kyreth: 12 mentions, traits: none
(entity Kyreth :known true :spawnable true :classification "known_spawnable" :mentions 12 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Nephoretti: 5 mentions, traits: none
(entity Nephoretti :known true :spawnable false :classification "known_non_spawnable" :mentions 5 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Olythae: 4 mentions, traits: none
(entity Olythae :known true :spawnable true :classification "known_spawnable" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Senareth: 6 mentions, traits: none
(entity Senareth :known true :spawnable true :classification "known_spawnable" :mentions 6 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Torhh: 10 mentions, traits: none
(entity Torhh :known true :spawnable true :classification "known_spawnable" :mentions 10 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Vairis: 2 mentions, traits: none
(entity Vairis :known true :spawnable true :classification "known_spawnable" :mentions 2 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)

; ---- Speaker Inference ----
(speaker line:11 Vairis :confidence 0.95)
(speaker line:85 Elyraen :confidence 0.95)
(speaker line:87 Senareth :confidence 0.95)
(speaker line:89 Vairis :confidence 0.95)

; ---- Emotions ----
(emotion line:35 Kyreth anxiety :confidence 0.90)
(emotion line:35 Kyreth fear :confidence 0.90)
(emotion line:47 Kyreth fear :confidence 0.90)
(emotion line:77 Kyreth wonder :confidence 1.00)
(emotion line:78 Kyreth triumph :confidence 1.00)
(emotion line:79 Kyreth relief :confidence 1.00)
(emotion line:80 Kyreth hope :confidence 1.00)
(emotion line:112 Nephoretti fear :confidence 0.90)
(emotion line:113 Nephoretti curiosity :confidence 0.90)

; ---- Actions ----
(action line:18 retreat :confidence 0.90)
(action line:25 vrill_manipulation :confidence 0.90)
(action line:30 approach :confidence 0.90)
(action line:38 approach :confidence 0.90)
(action line:43 submission :confidence 0.90)
(action line:49 attack :confidence 0.90)
(action line:57 approach :confidence 0.90)
(action line:59 vrill_manipulation :confidence 0.90)
(action line:74 shaping :confidence 0.90)
(action line:76 retreat :confidence 0.90)
(action line:76 submission :confidence 0.90)
(action line:99 observe :confidence 0.90)
(action line:103 shaping :confidence 0.90)
(action line:103 submission :confidence 0.90)
(action line:115 shaping :confidence 0.90)

; ---- Thoughts ----

; ---- Relationships ----
(relationship Kyreth Torhh collaborate :confidence 0.70)

