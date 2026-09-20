; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Aeon: 3 mentions, traits: none
(entity Aeon :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Applicator: 15 mentions, traits: none
(entity Applicator :known false :spawnable false :classification "unknown" :mentions 15 :presence "local" :presence_confidence 1.00 :physicality "unknown" :physicality_confidence 0.00)
; Dragon: 6 mentions, traits: none
(entity Dragon :known false :spawnable false :classification "unknown" :mentions 6 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Geralt: 29 mentions, traits: compassionate
(entity Geralt :known true :spawnable true :classification "known_spawnable" :mentions 29 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Host: 3 mentions, traits: none
(entity Host :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Immediately: 5 mentions, traits: compassionate
(entity Immediately :known false :spawnable false :classification "unknown" :mentions 5 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Mail: 6 mentions, traits: none
(entity Mail :known false :spawnable false :classification "unknown" :mentions 6 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Oreck: 5 mentions, traits: none
(entity Oreck :known true :spawnable true :classification "known_spawnable" :mentions 5 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Your: 5 mentions, traits: pragmatic
(entity Your :known false :spawnable false :classification "unknown" :mentions 5 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Zaron: 22 mentions, traits: none
(entity Zaron :known false :spawnable false :classification "unknown" :mentions 22 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)

; ---- Scene Content Observations ----
(scene_object "wall" :category "boundary" :normalized_type "wall" :mentions 1)

; ---- Speaker Inference ----
(speaker line:189 Geralt :confidence 0.95)
(speaker line:240 Geralt :confidence 0.95)
(speaker line:272 Geralt :confidence 0.95)
(speaker line:278 Oreck :confidence 0.95)
(speaker line:287 Geralt :confidence 0.95)

; ---- Emotions ----
(emotion line:52 Zaron fear :confidence 0.90)
(emotion line:52 Zaron vulnerability :confidence 0.90)
(emotion line:149 Zaron joy :confidence 0.90)
(emotion line:201 Geralt relief :confidence 0.90)
(emotion line:204 Oreck wonder :confidence 0.90)
(emotion line:246 Oreck uncertainty :confidence 0.90)
(emotion line:280 Immediately gentleness :confidence 0.90)

; ---- Actions ----
(action line:84 approach :confidence 0.90)
(action line:145 speak :confidence 0.90)
(action line:201 observe :confidence 0.90)
(action line:204 observe :confidence 0.90)
(action line:207 question :confidence 0.90)
(action line:225 speak :confidence 0.90)
(action line:246 approach :confidence 0.90)
(action line:249 observe :confidence 0.90)

; ---- Thoughts ----

