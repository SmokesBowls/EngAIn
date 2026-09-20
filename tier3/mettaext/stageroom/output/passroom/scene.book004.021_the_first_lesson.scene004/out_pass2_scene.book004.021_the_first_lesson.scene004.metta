; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Codex: 10 mentions, traits: pragmatic
(entity Codex :known false :spawnable false :classification "unknown" :mentions 10 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; First: 9 mentions, traits: none
(entity First :known false :spawnable false :classification "unknown" :mentions 9 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Grammar: 3 mentions, traits: none
(entity Grammar :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Harmonic: 7 mentions, traits: pragmatic
(entity Harmonic :known false :spawnable false :classification "unknown" :mentions 7 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Resonances: 5 mentions, traits: none
(entity Resonances :known false :spawnable false :classification "unknown" :mentions 5 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Sage: 8 mentions, traits: pragmatic
(entity Sage :known false :spawnable false :classification "unknown" :mentions 8 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Synthesis: 3 mentions, traits: none
(entity Synthesis :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)
; Torrhen: 8 mentions, traits: pragmatic
(entity Torrhen :known true :spawnable true :classification "known_spawnable" :mentions 8 :presence "local" :presence_confidence 1.00 :physicality "physical" :physicality_confidence 0.85)
; Year: 3 mentions, traits: none
(entity Year :known false :spawnable false :classification "unknown" :mentions 3 :presence "unknown" :presence_confidence 0.00 :physicality "unknown" :physicality_confidence 0.00)

; ---- Speaker Inference ----
(speaker line:35 Torrhen :confidence 0.95)
(speaker line:44 Torrhen :confidence 0.95)
(speaker line:50 Torrhen :confidence 0.95)
(speaker line:59 Torrhen :confidence 0.95)
(speaker line:69 Torrhen :confidence 0.95)

; ---- Emotions ----

; ---- Actions ----
(action line:31 approach :confidence 0.90)
(action line:38 approach :confidence 0.90)
(action line:40 approach :confidence 0.90)
(action line:41 approach :confidence 0.90)
(action line:43 approach :confidence 0.90)
(action line:43 observe :confidence 0.90)
(action line:68 observe :confidence 0.90)

; ---- Thoughts ----

; ---- Relationships ----
(relationship Harmonic Sage collaborate :confidence 0.70)
(relationship Harmonic First collaborate :confidence 0.70)

