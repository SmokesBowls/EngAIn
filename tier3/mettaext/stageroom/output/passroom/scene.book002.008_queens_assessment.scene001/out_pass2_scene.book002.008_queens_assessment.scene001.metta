; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Anunnaki: 3 mentions, traits: none
(entity Anunnaki :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Eduhauana: 23 mentions, traits: none
(entity Eduhauana :known false :spawnable false :classification "unknown" :mentions 23 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Giant: 17 mentions, traits: none
(entity Giant :known false :spawnable false :classification "unknown" :mentions 17 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Giants: 8 mentions, traits: none
(entity Giants :known true :spawnable false :classification "known_non_spawnable" :mentions 8 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Igigi: 8 mentions, traits: none
(entity Igigi :known false :spawnable false :classification "unknown" :mentions 8 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Marduk: 6 mentions, traits: none
(entity Marduk :known true :spawnable false :classification "known_non_spawnable" :mentions 6 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Needle: 3 mentions, traits: none
(entity Needle :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Overseer: 1 mentions, traits: none
(entity Overseer :known false :spawnable false :classification "unknown" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Queen: 9 mentions, traits: none
(entity Queen :known false :spawnable false :classification "unknown" :mentions 9 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; These: 7 mentions, traits: none
(entity These :known false :spawnable false :classification "unknown" :mentions 7 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Your: 4 mentions, traits: none
(entity Your :known false :spawnable false :classification "unknown" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)

; ---- Speaker Inference ----
(speaker line:47 Marduk :confidence 0.95)
(speaker line:113 Eduhauana :confidence 0.95)
(speaker line:158 Eduhauana :confidence 0.95)

; ---- Emotions ----
(emotion line:67 Marduk uncertainty :confidence 0.90)
(emotion line:82 Queen patience :confidence 0.90)
(emotion line:85 Giant caution :confidence 0.90)
(emotion line:85 Giant curiosity :confidence 0.90)
(emotion line:85 Giant uncertainty :confidence 0.90)
(emotion line:135 Giant sadness :confidence 0.90)

; ---- Actions ----
(action line:38 approach :confidence 0.90)
(action line:55 gather :confidence 0.90)
(action line:71 question :confidence 0.90)
(action line:81 observe :confidence 0.90)
(action line:99 approach :confidence 0.90)
(action line:99 vrill_manipulation :confidence 0.90)
(action line:160 retreat :confidence 0.90)
(action line:161 observe :confidence 0.90)
(action line:193 approach :confidence 0.90)
(action line:207 retreat :confidence 0.90)

; ---- Thoughts ----

; ---- Relationships ----
(relationship Giant Giants trust :confidence 0.70)

