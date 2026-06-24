#!/usr/bin/env python3
"""dialogue3d_mr.py - Pure Functional Dialogue Kernel"""

from typing import Dict, Any, List, Tuple

DEFAULT_REPUTATION = 50
MIN_REPUTATION = 0
MAX_REPUTATION = 100

def step_dialogue(snapshot_in: Dict[str, Any], deltas: List[Dict[str, Any]], dt: float) -> Tuple[Dict[str, Any], List[Dict], List[Dict]]:
    """Pure functional dialogue resolution"""
    snapshot_out = {"dialogue3d": {"entities": {}, "conversations": {}}}
    
    dlg_in = snapshot_in.get("dialogue3d", {})
    entities_in = dlg_in.get("entities", {})
    convos_in = dlg_in.get("conversations", {})
    
    # Copy state
    for eid, edata in entities_in.items():
        snapshot_out["dialogue3d"]["entities"][eid] = {
            "reputation": edata.get("reputation", {}).copy(),
            "knowledge_flags": set(edata.get("knowledge_flags", set())),
            "responses_given": set(edata.get("responses_given", set())),
            "active_conversation": edata.get("active_conversation")
        }
    
    for cid, cdata in convos_in.items():
        snapshot_out["dialogue3d"]["conversations"][cid] = cdata.copy()
    
    accepted = []
    alerts = []
    entities = snapshot_out["dialogue3d"]["entities"]
    conversations = snapshot_out["dialogue3d"]["conversations"]
    
    # Process deltas
    for delta in deltas:
        delta_type = delta.get("type")
        payload = delta.get("payload", {})
        
        if delta_type == "dialogue3d/say":
            if _handle_say(entities, conversations, payload, alerts):
                accepted.append(delta)
        elif delta_type == "dialogue3d/ask":
            if _handle_ask(entities, payload, alerts):
                accepted.append(delta)
        elif delta_type == "dialogue3d/respond":
            if _handle_respond(entities, conversations, payload, alerts):
                accepted.append(delta)
    
    return snapshot_out, accepted, alerts

def _handle_say(entities, conversations, payload, alerts):
    speaker_id = payload.get("speaker")
    listener_id = payload.get("listener")
    line_id = payload.get("line_id")
    
    if not all([speaker_id, listener_id, line_id]) or speaker_id not in entities or listener_id not in entities:
        return False
    
    rep = entities[listener_id].get("reputation", {}).get(speaker_id, DEFAULT_REPUTATION)
    convo_id = f"{speaker_id}_{listener_id}"
    
    if convo_id not in conversations:
        conversations[convo_id] = {"participants": [speaker_id, listener_id], "current_line": None, "history": []}
    
    conversations[convo_id]["current_line"] = line_id
    conversations[convo_id]["history"].append({"speaker": speaker_id, "line_id": line_id})
    entities[speaker_id]["active_conversation"] = convo_id
    entities[listener_id]["active_conversation"] = convo_id
    
    alerts.append({"type": "dialogue_started", "speaker": speaker_id, "listener": listener_id, "line_id": line_id, "reputation": rep})
    return True

def _handle_ask(entities, payload, alerts):
    asker_id = payload.get("asker")
    target_id = payload.get("target")
    topic = payload.get("topic")
    
    if not all([asker_id, target_id, topic]) or asker_id not in entities or target_id not in entities:
        return False
    
    if topic in entities[target_id].get("knowledge_flags", set()):
        entities[asker_id].get("knowledge_flags", set()).add(topic)
        alerts.append({"type": "knowledge_shared", "asker": asker_id, "target": target_id, "topic": topic})
        return True
    else:
        alerts.append({"type": "knowledge_unknown", "asker": asker_id, "target": target_id, "topic": topic})
        return False

def _handle_respond(entities, conversations, payload, alerts):
    speaker_id = payload.get("speaker")
    branch_id = payload.get("branch_id")
    
    if not all([speaker_id, branch_id]) or speaker_id not in entities:
        return False
    
    convo_id = entities[speaker_id].get("active_conversation")
    if not convo_id or convo_id not in conversations:
        alerts.append({"type": "respond_failed", "reason": "no_active_conversation"})
        return False
    
    entities[speaker_id].get("responses_given", set()).add(branch_id)
    effects = payload.get("effects", {})
    
    rep_change = effects.get("reputation_change", 0)
    if rep_change != 0:
        participants = conversations[convo_id]["participants"]
        other_id = [p for p in participants if p != speaker_id][0]
        rep_dict = entities[other_id].get("reputation", {})
        current = rep_dict.get(speaker_id, DEFAULT_REPUTATION)
        rep_dict[speaker_id] = max(MIN_REPUTATION, min(MAX_REPUTATION, current + rep_change))
        entities[other_id]["reputation"] = rep_dict
    
    knowledge_unlock = effects.get("knowledge_unlock")
    if knowledge_unlock:
        entities[speaker_id].get("knowledge_flags", set()).add(knowledge_unlock)
    
    alerts.append({"type": "branch_selected", "speaker": speaker_id, "branch_id": branch_id, "effects": effects})
    return True

if __name__ == "__main__":
    test_snapshot = {"dialogue3d": {"entities": {"player": {"reputation": {}, "knowledge_flags": set(), "responses_given": set(), "active_conversation": None}, "guard": {"reputation": {}, "knowledge_flags": {"fire_crystal_location"}, "responses_given": set(), "active_conversation": None}}, "conversations": {}}}
    
    deltas = [{"type": "dialogue3d/say", "payload": {"speaker": "player", "listener": "guard", "line_id": "greeting_1"}}, {"type": "dialogue3d/ask", "payload": {"asker": "player", "target": "guard", "topic": "fire_crystal_location"}}]
    
    snapshot_out, accepted, alerts = step_dialogue(test_snapshot, deltas, 0.016)
    
    print("=== Dialogue Test ===")
    print(f"Conversations: {len(snapshot_out['dialogue3d']['conversations'])}")
    print(f"Player knowledge: {snapshot_out['dialogue3d']['entities']['player']['knowledge_flags']}")
    print(f"Alerts: {len(alerts)}")
    for alert in alerts:
        print(f"  - {alert['type']}: {alert}")
