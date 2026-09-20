; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Akashic: 5 mentions, traits: none
(entity Akashic :known false :spawnable false :classification "unknown" :mentions 5 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Around: 4 mentions, traits: none
(entity Around :known false :spawnable false :classification "unknown" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Bodies: 3 mentions, traits: none
(entity Bodies :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Elyraen: 2 mentions, traits: none
(entity Elyraen :known true :spawnable true :classification "known_spawnable" :mentions 2 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Ethereal: 3 mentions, traits: none
(entity Ethereal :known true :spawnable false :classification "known_non_spawnable" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Giant: 6 mentions, traits: none
(entity Giant :known false :spawnable false :classification "unknown" :mentions 6 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Giants: 11 mentions, traits: none
(entity Giants :known true :spawnable false :classification "known_non_spawnable" :mentions 11 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Mordain: 1 mentions, traits: none
(entity Mordain :known true :spawnable true :classification "known_spawnable" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Nephoretti: 21 mentions, traits: pragmatic
(entity Nephoretti :known true :spawnable false :classification "known_non_spawnable" :mentions 21 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Olythae: 1 mentions, traits: creative
(entity Olythae :known true :spawnable true :classification "known_spawnable" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Others: 3 mentions, traits: none
(entity Others :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Pelagor: 5 mentions, traits: none
(entity Pelagor :known true :spawnable true :classification "known_spawnable" :mentions 5 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Prime: 5 mentions, traits: none
(entity Prime :known false :spawnable false :classification "unknown" :mentions 5 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Senareth: 36 mentions, traits: pragmatic
(entity Senareth :known true :spawnable true :classification "known_spawnable" :mentions 36 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Through: 3 mentions, traits: patient
(entity Through :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Vairis: 2 mentions, traits: pragmatic
(entity Vairis :known true :spawnable true :classification "known_spawnable" :mentions 2 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Veil: 3 mentions, traits: none
(entity Veil :known true :spawnable false :classification "known_non_spawnable" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Zoup: 3 mentions, traits: none
(entity Zoup :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)

; ---- Scene Content Observations ----
(scene_object "wall" :category "boundary" :normalized_type "wall" :mentions 1)

; ---- Speaker Inference ----
(speaker line:205 Senareth :confidence 0.95)
(speaker line:207 Senareth :confidence 0.95)
(speaker line:229 Senareth :confidence 0.95)
(speaker line:246 Senareth :confidence 0.95)
(speaker line:255 Elyraen :confidence 0.95)
(speaker line:257 Vairis :confidence 0.95)
(speaker line:259 Elyraen :confidence 0.95)
(speaker line:266 Senareth :confidence 0.95)
(speaker line:268 Olythae :confidence 0.95)
(speaker line:284 Senareth :confidence 0.95)
(speaker line:286 Vairis :confidence 0.95)
(speaker line:302 Senareth :confidence 0.95)

; ---- Emotions ----
(emotion line:29 Senareth uncertainty :confidence 0.90)
(emotion line:29 Senareth wonder :confidence 0.90)
(emotion line:142 Bodies wonder :confidence 0.90)
(emotion line:165 Others patience :confidence 0.90)
(emotion line:185 Giants fear :confidence 1.00)
(emotion line:217 Pelagor fear :confidence 0.90)
(emotion line:227 Nephoretti fear :confidence 0.90)
(emotion line:244 Senareth curiosity :confidence 0.90)
(emotion line:250 Giant anxiety :confidence 0.90)
(emotion line:253 Nephoretti curiosity :confidence 0.90)
(emotion line:263 Giants fear :confidence 0.90)
(emotion line:275 Giants fear :confidence 1.00)
(emotion line:280 Through patience :confidence 0.90)
(emotion line:280 Through vulnerability :confidence 0.90)
(emotion line:288 Senareth curiosity :confidence 0.90)
(emotion line:288 Senareth fear :confidence 0.90)
(emotion line:310 Giants fear :confidence 0.90)
(emotion line:316 Through fear :confidence 0.90)
(emotion line:316 Through patience :confidence 0.90)

; ---- Actions ----
(action line:101 vrill_energy :confidence 0.90)
(action line:143 vrill_energy :confidence 0.90)
(action line:148 vrill_energy :confidence 0.90)
(action line:171 observe :confidence 0.90)
(action line:179 attack :confidence 0.90)
(action line:210 observe :confidence 0.90)
(action line:218 flee :confidence 0.90)
(action line:222 gather :confidence 0.90)
(action line:227 observe :confidence 0.90)
(action line:237 vrill_energy :confidence 0.90)
(action line:252 approach :confidence 0.90)
(action line:292 flee :confidence 0.90)
(action line:306 gather :confidence 0.90)

; ---- Thoughts ----

; ---- Relationships ----
(relationship Nephoretti Senareth trust :confidence 0.70)

