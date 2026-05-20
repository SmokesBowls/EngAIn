extends Node
class_name RealityStateController

# ===== STATE =====
var current_mode = "WAKING"  # WAKING, DREAM, BROADCAST, LOCKED
var anchor_locked = false

# ===== REFERENCES =====
@onready var dream_store = get_node("/root/DreamEventStore")

# ===== ENTRY POINTS =====

func enter_dream():
    if current_mode != "WAKING":
        return

    current_mode = "DREAM"
    DreamStateManager.enter_dream()

    dream_store.record_event(
        DreamEventStore.EventType.DREAM_ENTERED,
        {"mode": "dream"}
    )


func exit_dream():
    if current_mode != "DREAM":
        return

    current_mode = "WAKING"
    DreamStateManager.exit_dream()

    dream_store.record_event(
        DreamEventStore.EventType.DREAM_EXITED,
        {"mode": "waking"}
    )


# ===== BLACK KNIGHT INJECTION =====

func trigger_black_knight():
    if anchor_locked:
        return  # cannot override locked reality

    current_mode = "BROADCAST"

    dream_store.record_event(
        DreamEventStore.EventType.REALITY_SHIFTED,
        {"source": "black_knight"}
    )

    apply_broadcast_effects()


func apply_broadcast_effects():
    # Example: gravity inversion
    PhysicsStack.apply_physics_mod("black_knight_gravity", {
        "gravity": -9.8
    })


# ===== MANDELA LOCK =====

func attempt_anchor_lock(anchor_id: String):
    if anchor_locked:
        return

    if not can_lock_anchor():
        return

    apply_anchor(anchor_id)


func can_lock_anchor() -> bool:
    return Global.timeline_relics >= 5 and Global.reality_integrity <= 25


func apply_anchor(anchor_id: String):
    anchor_locked = true
    current_mode = "LOCKED"
    Global.locked_anchor = anchor_id

    dream_store.record_event(
        DreamEventStore.EventType.ANCHOR_APPLIED,
        {"anchor": anchor_id}
    )

    commit_reality(anchor_id)


func commit_reality(anchor_id: String):
    # HARD COMMIT — NO ROLLBACK

    match anchor_id:

        "REBELLION_WON":
            load_rebellion_world()

        "VRIL_DOMINANCE":
            disable_vril_system()

        "AEON_BETRAYAL":
            collapse_anchor_support()

    purge_unselected_timelines()


# ===== WORLD EFFECTS =====

func load_rebellion_world():
    get_tree().change_scene_to_file("res://Worlds/RebellionWorld.tscn")


func disable_vril_system():
    Global.vril_power_enabled = false


func collapse_anchor_support():
    RealityEngine.timeline_entropy += 20


func purge_unselected_timelines():
    ResourceLoader.clear_cache()
