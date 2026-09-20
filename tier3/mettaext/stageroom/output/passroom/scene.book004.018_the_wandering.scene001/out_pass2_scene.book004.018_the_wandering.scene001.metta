; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Cannot: 3 mentions, traits: none
(entity Cannot :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Giant: 5 mentions, traits: none
(entity Giant :known false :spawnable false :classification "unknown" :mentions 5 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Tidecaller: 1 mentions, traits: none
(entity Tidecaller :known false :spawnable false :classification "unknown" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Torrhen: 21 mentions, traits: none
(entity Torrhen :known true :spawnable true :classification "known_spawnable" :mentions 21 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Zephyr: 22 mentions, traits: none
(entity Zephyr :known true :spawnable true :classification "known_spawnable" :mentions 22 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)

; ---- Scene Content Observations ----
(scene_object "wall" :category "boundary" :normalized_type "wall" :mentions 3)

; ---- Speaker Inference ----
(speaker line:52 Zephyr :confidence 0.95)
(speaker line:65 Torrhen :confidence 0.95)
(speaker line:94 Zephyr :confidence 0.95)
(speaker line:114 Torrhen :confidence 0.95)
(speaker line:116 Zephyr :confidence 0.95)

; ---- Emotions ----
(emotion line:76 Zephyr exhaustion :confidence 0.90)
(emotion line:97 Torrhen sadness :confidence 0.90)

; ---- Actions ----
(action line:12 shaping :confidence 0.90)
(action line:24 shaping :confidence 0.90)
(action line:47 shaping :confidence 0.90)
(action line:48 shaping :confidence 0.90)
(action line:61 shaping :confidence 0.90)

; ---- Thoughts ----

; ---- Relationships ----
(relationship Torrhen Giant collaborate :confidence 0.70)

