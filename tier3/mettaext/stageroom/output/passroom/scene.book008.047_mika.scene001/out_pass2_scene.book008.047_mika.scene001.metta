; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Celly: 7 mentions, traits: none
(entity Celly :known false :spawnable false :classification "unknown" :mentions 7)
; Geralt: 9 mentions, traits: none
(entity Geralt :known true :spawnable true :classification "known_spawnable" :mentions 9)
; Ironspire: 4 mentions, traits: none
(entity Ironspire :known false :spawnable false :classification "unknown" :mentions 4)
; Legion: 3 mentions, traits: none
(entity Legion :known false :spawnable false :classification "unknown" :mentions 3)
; Mika: 7 mentions, traits: none
(entity Mika :known true :spawnable true :classification "known_spawnable" :mentions 7)
; Needle: 3 mentions, traits: none
(entity Needle :known false :spawnable false :classification "unknown" :mentions 3)
; Roric: 4 mentions, traits: none
(entity Roric :known false :spawnable false :classification "unknown" :mentions 4)

; ---- Scene Content Observations ----
(scene_object "FALCON RIDGE" :category "settlement" :normalized_type "settlement" :mentions 1)
(scene_object "Star Needle" :category "landmark" :normalized_type "spire" :mentions 1)
(scene_object "Star Needle Spire" :category "landmark" :normalized_type "spire" :mentions 1)
(scene_object "crash site" :category "location" :normalized_type "location" :mentions 1)
(scene_object "fields" :category "settlement_feature" :normalized_type "fields" :mentions 1)
(scene_object "gate" :category "boundary" :normalized_type "gate" :mentions 2)
(scene_object "longhouse" :category "structure" :normalized_type "longhouse" :mentions 1)
(scene_object "settlement" :category "settlement" :normalized_type "settlement" :mentions 1)
(scene_object "wall" :category "boundary" :normalized_type "wall" :mentions 4)

; ---- Speaker Inference ----
(speaker line:39 Mika :confidence 0.95)
(speaker line:51 Geralt :confidence 0.95)
(speaker line:61 Mika :confidence 0.95)
(speaker line:99 Celly :confidence 0.95)

; ---- Emotions ----
(emotion line:94 Legion exhaustion :confidence 0.90)
(emotion line:94 Legion gratitude :confidence 0.90)

; ---- Actions ----
(action line:23 shaping :confidence 0.90)
(action line:41 approach :confidence 0.90)
(action line:117 gather :confidence 0.90)

; ---- Thoughts ----

