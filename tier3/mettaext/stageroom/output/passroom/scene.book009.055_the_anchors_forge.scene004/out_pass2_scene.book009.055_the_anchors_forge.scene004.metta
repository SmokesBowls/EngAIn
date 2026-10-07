; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Anunnaki: 4 mentions, traits: none
(entity Anunnaki :known false :spawnable false :classification "unknown" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Chapter: 7 mentions, traits: none
(entity Chapter :known false :spawnable false :classification "unknown" :mentions 7 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Clay: 5 mentions, traits: none
(entity Clay :known false :spawnable false :classification "unknown" :mentions 5 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Dragon: 4 mentions, traits: none
(entity Dragon :known false :spawnable false :classification "unknown" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Geralt: 21 mentions, traits: patient
(entity Geralt :known true :spawnable true :classification "known_spawnable" :mentions 21 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Heart: 3 mentions, traits: none
(entity Heart :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Kulla: 19 mentions, traits: patient
(entity Kulla :known false :spawnable false :classification "unknown" :mentions 19 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Mail: 4 mentions, traits: none
(entity Mail :known false :spawnable false :classification "unknown" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Mind: 7 mentions, traits: none
(entity Mind :known false :spawnable false :classification "unknown" :mentions 7 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Moon: 4 mentions, traits: none
(entity Moon :known false :spawnable false :classification "unknown" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Only: 3 mentions, traits: none
(entity Only :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Oreck: 8 mentions, traits: patient
(entity Oreck :known true :spawnable true :classification "known_spawnable" :mentions 8 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Shattered: 7 mentions, traits: none
(entity Shattered :known false :spawnable false :classification "unknown" :mentions 7 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Unmentioned: 4 mentions, traits: none
(entity Unmentioned :known false :spawnable false :classification "unknown" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)

; ---- Scene Content Observations ----
(scene_object "wall" :category "boundary" :normalized_type "wall" :mentions 1)

; ---- Speaker Inference ----

; ---- Emotions ----
(emotion line:176 Only anger :confidence 0.90)
(emotion line:207 Geralt patience :confidence 0.90)

; ---- Actions ----
(action line:13 approach :confidence 0.90)
(action line:67 approach :confidence 0.90)
(action line:178 speak :confidence 0.90)
(action line:205 speak :confidence 0.90)
(action line:207 flee :confidence 0.90)
(action line:214 observe :confidence 0.90)

; ---- Thoughts ----

; ---- Relationships ----
(relationship Kulla Moon collaborate :confidence 0.70)
(relationship Kulla Moon collaborate :confidence 0.70)
(relationship Shattered Mind collaborate :confidence 0.70)

