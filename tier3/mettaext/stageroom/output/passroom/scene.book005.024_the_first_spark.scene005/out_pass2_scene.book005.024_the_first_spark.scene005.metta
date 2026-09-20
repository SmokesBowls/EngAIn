; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Five: 4 mentions, traits: none
(entity Five :known false :spawnable false :classification "unknown" :mentions 4 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Mika: 0 mentions, traits: none
(entity Mika :known true :spawnable true :classification "known_spawnable" :mentions 0 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Nameless: 14 mentions, traits: none
(entity Nameless :known false :spawnable false :classification "unknown" :mentions 14 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Night: 4 mentions, traits: none
(entity Night :known false :spawnable false :classification "unknown" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Something: 3 mentions, traits: none
(entity Something :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Waiting: 3 mentions, traits: none
(entity Waiting :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)

; ---- Scene Content Observations ----
(scene_object "wall" :category "boundary" :normalized_type "wall" :mentions 2)

; ---- Speaker Inference ----

; ---- Emotions ----
(emotion line:70 Something uncertainty :confidence 0.90)
(emotion line:85 Nameless hope :confidence 0.90)
(emotion line:125 Nameless exhaustion :confidence 0.90)
(emotion line:151 Nameless exhaustion :confidence 0.90)

; ---- Actions ----
(action line:31 speak :confidence 0.90)
(action line:75 speak :confidence 0.90)

; ---- Thoughts ----

