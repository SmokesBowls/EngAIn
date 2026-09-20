; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Anunnaki: 6 mentions, traits: none
(entity Anunnaki :known false :spawnable false :classification "unknown" :mentions 6 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Applicator: 8 mentions, traits: pragmatic
(entity Applicator :known false :spawnable false :classification "unknown" :mentions 8 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Five: 7 mentions, traits: none
(entity Five :known false :spawnable false :classification "unknown" :mentions 7 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Freed: 0 mentions, traits: none
(entity Freed :known false :spawnable false :classification "unknown" :mentions 0 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Geralt: 24 mentions, traits: none
(entity Geralt :known true :spawnable true :classification "known_spawnable" :mentions 24 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Hours: 4 mentions, traits: none
(entity Hours :known false :spawnable false :classification "unknown" :mentions 4 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Kael: 1 mentions, traits: none
(entity Kael :known false :spawnable false :classification "unknown" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Mika: 9 mentions, traits: none
(entity Mika :known true :spawnable true :classification "known_spawnable" :mentions 9 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Only: 3 mentions, traits: none
(entity Only :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Oreck: 8 mentions, traits: none
(entity Oreck :known true :spawnable true :classification "known_spawnable" :mentions 8 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Slaves: 0 mentions, traits: none
(entity Slaves :known false :spawnable false :classification "unknown" :mentions 0 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Tess: 1 mentions, traits: none
(entity Tess :known false :spawnable false :classification "unknown" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Tomorrow: 3 mentions, traits: none
(entity Tomorrow :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Vale: 1 mentions, traits: none
(entity Vale :known true :spawnable true :classification "known_spawnable" :mentions 1 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Zaron: 8 mentions, traits: pragmatic
(entity Zaron :known false :spawnable false :classification "unknown" :mentions 8 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)

; ---- Speaker Inference ----
(speaker line:43 Oreck :confidence 0.95)
(speaker line:65 Oreck :confidence 0.95)
(speaker line:76 Oreck :confidence 0.95)
(speaker line:231 Geralt :confidence 0.95)
(speaker line:271 Geralt :confidence 0.95)

; ---- Emotions ----
(emotion line:31 Five caution :confidence 0.90)
(emotion line:87 Geralt uncertainty :confidence 0.90)
(emotion line:101 Mika caution :confidence 0.90)
(emotion line:131 Mika caution :confidence 0.90)
(emotion line:142 Mika hope :confidence 0.90)
(emotion line:153 Mika sadness :confidence 0.90)
(emotion line:158 Geralt hope :confidence 0.90)
(emotion line:183 Applicator fear :confidence 0.90)
(emotion line:213 Freed fear :confidence 0.90)
(emotion line:213 Freed hope :confidence 0.90)
(emotion line:213 Freed uncertainty :confidence 0.90)
(emotion line:215 Only triumph :confidence 0.90)
(emotion line:219 Mika fear :confidence 0.90)
(emotion line:249 Freed fear :confidence 0.90)

; ---- Actions ----
(action line:87 gather :confidence 0.90)
(action line:118 submission :confidence 0.90)
(action line:142 shaping :confidence 0.90)
(action line:160 attack :confidence 0.90)
(action line:207 flee :confidence 0.90)
(action line:262 observe :confidence 0.90)

; ---- Thoughts ----

; ---- Relationships ----
(relationship Geralt Oreck respect :confidence 0.70)
(relationship Geralt Oreck respect :confidence 0.70)

