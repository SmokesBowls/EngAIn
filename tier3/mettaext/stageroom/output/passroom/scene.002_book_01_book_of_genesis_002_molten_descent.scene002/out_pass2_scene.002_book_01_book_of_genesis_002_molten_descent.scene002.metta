; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Around: 4 mentions, traits: none
(entity Around :known false :spawnable false :classification "unknown" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Bodies: 3 mentions, traits: none
(entity Bodies :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Elyraen: 2 mentions, traits: none
(entity Elyraen :known true :spawnable true :classification "known_spawnable" :mentions 2 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Ethereal: 3 mentions, traits: none
(entity Ethereal :known true :spawnable false :classification "known_non_spawnable" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Giant: 6 mentions, traits: none
(entity Giant :known false :spawnable false :classification "unknown" :mentions 6 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Giants: 11 mentions, traits: none
(entity Giants :known true :spawnable false :classification "known_non_spawnable" :mentions 11 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Nephoretti: 15 mentions, traits: pragmatic
(entity Nephoretti :known true :spawnable false :classification "known_non_spawnable" :mentions 15 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Olythae: 1 mentions, traits: creative
(entity Olythae :known true :spawnable true :classification "known_spawnable" :mentions 1 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Others: 3 mentions, traits: none
(entity Others :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Pelagor: 3 mentions, traits: none
(entity Pelagor :known true :spawnable true :classification "known_spawnable" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Prime: 3 mentions, traits: none
(entity Prime :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Senareth: 34 mentions, traits: pragmatic
(entity Senareth :known true :spawnable true :classification "known_spawnable" :mentions 34 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Through: 3 mentions, traits: patient
(entity Through :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Vairis: 2 mentions, traits: pragmatic
(entity Vairis :known true :spawnable true :classification "known_spawnable" :mentions 2 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Zoup: 3 mentions, traits: none
(entity Zoup :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)

; ---- Scene Content Observations ----
(scene_object "wall" :category "boundary" :normalized_type "wall" :mentions 1)

; ---- Speaker Inference ----
(speaker line:193 Senareth :confidence 0.95)
(speaker line:195 Senareth :confidence 0.95)
(speaker line:217 Senareth :confidence 0.95)
(speaker line:234 Senareth :confidence 0.95)
(speaker line:243 Elyraen :confidence 0.95)
(speaker line:245 Vairis :confidence 0.95)
(speaker line:247 Elyraen :confidence 0.95)
(speaker line:254 Senareth :confidence 0.95)
(speaker line:256 Olythae :confidence 0.95)
(speaker line:272 Senareth :confidence 0.95)
(speaker line:274 Vairis :confidence 0.95)
(speaker line:290 Senareth :confidence 0.95)

; ---- Emotions ----
(emotion line:17 Senareth uncertainty :confidence 0.90)
(emotion line:17 Senareth wonder :confidence 0.90)
(emotion line:130 Bodies wonder :confidence 0.90)
(emotion line:153 Others patience :confidence 0.90)
(emotion line:173 Giants fear :confidence 1.00)
(emotion line:205 Pelagor fear :confidence 0.90)
(emotion line:215 Senareth fear :confidence 0.90)
(emotion line:232 Senareth curiosity :confidence 0.90)
(emotion line:238 Giant anxiety :confidence 0.90)
(emotion line:241 Senareth curiosity :confidence 0.90)
(emotion line:251 Giants fear :confidence 0.90)
(emotion line:263 Giants fear :confidence 1.00)
(emotion line:268 Through patience :confidence 0.90)
(emotion line:268 Through vulnerability :confidence 0.90)
(emotion line:276 Senareth curiosity :confidence 0.90)
(emotion line:276 Senareth fear :confidence 0.90)
(emotion line:298 Giants fear :confidence 0.90)
(emotion line:304 Through fear :confidence 0.90)
(emotion line:304 Through patience :confidence 0.90)

; ---- Actions ----
(action line:89 vrill_energy :confidence 0.90)
(action line:131 vrill_energy :confidence 0.90)
(action line:136 vrill_energy :confidence 0.90)
(action line:159 observe :confidence 0.90)
(action line:167 attack :confidence 0.90)
(action line:198 observe :confidence 0.90)
(action line:206 flee :confidence 0.90)
(action line:210 gather :confidence 0.90)
(action line:215 observe :confidence 0.90)
(action line:225 vrill_energy :confidence 0.90)
(action line:240 approach :confidence 0.90)
(action line:280 flee :confidence 0.90)
(action line:294 gather :confidence 0.90)

; ---- Thoughts ----

; ---- Relationships ----
(relationship Senareth Nephoretti trust :confidence 0.70)

