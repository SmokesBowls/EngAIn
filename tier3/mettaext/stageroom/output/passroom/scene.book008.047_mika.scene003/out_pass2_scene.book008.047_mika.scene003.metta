; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Falcon: 4 mentions, traits: none
(entity Falcon :known false :spawnable false :classification "unknown" :mentions 4)
; Geralt: 7 mentions, traits: none
(entity Geralt :known true :spawnable true :classification "known_spawnable" :mentions 7)
; Ironspire: 3 mentions, traits: none
(entity Ironspire :known false :spawnable false :classification "unknown" :mentions 3)
; Mika: 10 mentions, traits: none
(entity Mika :known true :spawnable true :classification "known_spawnable" :mentions 10)
; Ridge: 4 mentions, traits: none
(entity Ridge :known false :spawnable false :classification "unknown" :mentions 4)
; Spire: 4 mentions, traits: none
(entity Spire :known false :spawnable false :classification "unknown" :mentions 4)
; Sundrift: 4 mentions, traits: none
(entity Sundrift :known false :spawnable false :classification "unknown" :mentions 4)
; Year: 5 mentions, traits: none
(entity Year :known false :spawnable false :classification "unknown" :mentions 5)
; Zephyr: 3 mentions, traits: none
(entity Zephyr :known true :spawnable true :classification "known_spawnable" :mentions 3)

; ---- Scene Content Observations ----
(scene_object "Falcon Ridge" :category "settlement" :normalized_type "settlement" :mentions 4)
(scene_object "archive" :category "structure" :normalized_type "archive" :mentions 3)
(scene_object "gate" :category "boundary" :normalized_type "gate" :mentions 1)
(scene_object "hut" :category "structure" :normalized_type "hut" :mentions 1)
(scene_object "ridge" :category "terrain_feature" :normalized_type "ridge" :mentions 1)
(scene_object "settlement" :category "settlement" :normalized_type "settlement" :mentions 2)
(scene_object "valley" :category "terrain_feature" :normalized_type "valley" :mentions 3)
(scene_object "wall" :category "boundary" :normalized_type "wall" :mentions 1)

; ---- Speaker Inference ----
(speaker line:26 Mika :confidence 0.95)
(speaker line:63 Geralt :confidence 0.95)

; ---- Emotions ----

; ---- Actions ----
(action line:23 speak :confidence 0.90)
(action line:30 speak :confidence 0.90)
(action line:30 observe :confidence 0.90)
(action line:61 speak :confidence 0.90)
(action line:83 observe :confidence 0.90)
(action line:91 speak :confidence 0.90)
(action line:118 approach :confidence 0.90)
(action line:136 speak :confidence 0.90)

; ---- Thoughts ----

