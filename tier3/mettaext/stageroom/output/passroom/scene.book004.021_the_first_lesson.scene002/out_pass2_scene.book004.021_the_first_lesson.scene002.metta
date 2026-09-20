; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; First: 11 mentions, traits: none
(entity First :known false :spawnable false :classification "unknown" :mentions 11 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Grammar: 8 mentions, traits: none
(entity Grammar :known false :spawnable false :classification "unknown" :mentions 8 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Sage: 13 mentions, traits: none
(entity Sage :known false :spawnable false :classification "unknown" :mentions 13 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Torrhen: 12 mentions, traits: none
(entity Torrhen :known true :spawnable true :classification "known_spawnable" :mentions 12 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)

; ---- Speaker Inference ----
(speaker line:35 Torrhen :confidence 0.95)
(speaker line:41 Torrhen :confidence 0.95)
(speaker line:48 Torrhen :confidence 0.95)
(speaker line:64 Torrhen :confidence 0.95)
(speaker line:68 Torrhen :confidence 0.95)
(speaker line:74 Torrhen :confidence 0.95)

; ---- Emotions ----
(emotion line:66 Sage joy :confidence 0.90)

; ---- Actions ----
(action line:31 approach :confidence 0.90)
(action line:31 shaping :confidence 0.90)
(action line:34 shaping :confidence 0.90)
(action line:59 approach :confidence 0.90)
(action line:59 shaping :confidence 0.90)
(action line:66 approach :confidence 0.90)
(action line:67 approach :confidence 0.90)
(action line:71 approach :confidence 0.90)

; ---- Thoughts ----

; ---- Relationships ----
(relationship First Sage collaborate :confidence 0.70)
(relationship First Sage collaborate :confidence 0.70)

