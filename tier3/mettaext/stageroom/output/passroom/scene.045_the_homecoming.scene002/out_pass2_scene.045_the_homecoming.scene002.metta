; PASS2 ENHANCED INFERENCES
; Enhanced extraction for complex narratives

; ---- Entity Candidates ----
; Geralt: 9 mentions, traits: none
(entity Geralt :known true :spawnable true :classification "known_spawnable" :mentions 9)
; Mika: 13 mentions, traits: none
(entity Mika :known true :spawnable true :classification "known_spawnable" :mentions 13)
; Month: 3 mentions, traits: none
(entity Month :known false :spawnable false :classification "unknown" :mentions 3)
; Zephyr: 5 mentions, traits: none
(entity Zephyr :known true :spawnable true :classification "known_spawnable" :mentions 5)

; ---- Scene Content Observations ----
(scene_object "Falcon Ridge" :category "settlement" :normalized_type "settlement" :mentions 2)
(scene_object "Star Needle Spire" :category "landmark" :normalized_type "spire" :mentions 1)
(scene_object "archive" :category "structure" :normalized_type "archive" :mentions 1)
(scene_object "barracks" :category "structure" :normalized_type "barracks" :mentions 1)
(scene_object "fields" :category "settlement_feature" :normalized_type "fields" :mentions 2)
(scene_object "hut" :category "structure" :normalized_type "hut" :mentions 2)
(scene_object "irrigation ditches" :category "settlement_feature" :normalized_type "ditches" :mentions 1)
(scene_object "perimeter wall" :category "boundary" :normalized_type "wall" :mentions 1)
(scene_object "plateau" :category "terrain_feature" :normalized_type "plateau" :mentions 2)
(scene_object "settlement" :category "settlement" :normalized_type "settlement" :mentions 1)
(scene_object "solid stone building" :category "structure" :normalized_type "building" :mentions 1)
(scene_object "storage cache" :category "settlement_feature" :normalized_type "cache" :mentions 1)
(scene_object "stream" :category "terrain_feature" :normalized_type "stream" :mentions 4)
(scene_object "valley" :category "terrain_feature" :normalized_type "valley" :mentions 6)
(scene_object "wall" :category "boundary" :normalized_type "wall" :mentions 1)
(scene_object "waterfall" :category "terrain_feature" :normalized_type "waterfall" :mentions 1)

; ---- Speaker Inference ----
(speaker line:53 Mika :confidence 0.95)
(speaker line:82 Geralt :confidence 0.95)
(speaker line:129 Zephyr :confidence 0.95)
(speaker line:139 Zephyr :confidence 0.95)

; ---- Emotions ----
(emotion line:95 Month hope :confidence 0.90)

; ---- Actions ----
(action line:16 speak :confidence 0.90)
(action line:115 speak :confidence 0.90)

; ---- Thoughts ----

