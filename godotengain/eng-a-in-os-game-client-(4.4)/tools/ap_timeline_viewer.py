#!/usr/bin/env python3
"""
ap_timeline_viewer.py - CLI Timeline Viewer (Thin Slice 5A)

Mechanical audit of AP execution history.
Detects fired counts, persistent streaks, and starvation.
"""

import json
import argparse
import urllib.request
from collections import Counter, defaultdict

def api_call(msg_type, extra_params=None):
    url = "http://127.0.0.1:8765/ap_query"
    payload = {"type": msg_type}
    if extra_params:
        payload.update(extra_params)
    
    try:
        req = urllib.request.Request(
            url, 
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}

def main():
    parser = argparse.ArgumentParser(description="AP Timeline Viewer")
    parser.add_argument("--limit", type=int, default=50, help="Number of ticks to analyze")
    parser.add_argument("--streak-min", type=int, default=3, help="Minimum streak to report")
    args = parser.parse_args()

    # 1. Fetch data
    history_resp = api_call("ap_execution_history", {"limit": args.limit})
    entries = history_resp.get("entries", [])
    
    rules_resp = api_call("ap_list_rules")
    all_rule_ids = [r['id'] for r in rules_resp.get("rules", [])] if "rules" in rules_resp else []

    if not entries:
        print("No execution history found.")
        return

    # 2. Application of mechanical detection rules
    fired_count = Counter()
    ever_fired = set()
    current_streak = defaultdict(int) # streak at the end of window
    
    # For persistent blocking, we need to track streaks through the whole window
    for entry in entries:
        applied = entry.get("applied_rules", [])
        blocked = entry.get("blocked_rules", [])
        
        for r in applied:
            fired_count[r] += 1
            ever_fired.add(r)
        
        for r in all_rule_ids:
            if r in blocked:
                current_streak[r] += 1
            else:
                current_streak[r] = 0

    # 3. Output sections
    print(f"AP TIMELINE SUMMARY (last {len(entries)} ticks)")
    print("==================================")
    print()

    print("Rules that fired:")
    for rid in sorted(all_rule_ids):
        print(f"  {rid:<24}: {fired_count[rid]}")
    print()

    print("Persistent blocking:")
    had_streaks = False
    for rid in sorted(all_rule_ids):
        streak = current_streak[rid]
        if streak >= args.streak_min:
            had_streaks = True
            print(f"  {rid}")
            print(f"    blocked for {streak} consecutive ticks")
            
            # Mechanical fact: get the reason from the last tick for context
            # We fetch this live to ensure 'last reason' is accurate to current state
            expl_resp = api_call("ap_evaluate_rule", {"rule_id": rid, "context": {"player": "player"}})
            blocked_by = expl_resp.get("blocked_by", [])
            reason = blocked_by[0] if blocked_by else "None"
            print(f"    last reason: {reason}")
    
    if not had_streaks:
        print("  none")
    print()

    print("Starvation (Blocked throughout window, never fired):")
    # Interpretation: Starved if blocked in the FINAL tick AND never fired in this window
    starved = [r for r in all_rule_ids if r not in ever_fired and current_streak[r] >= len(entries)]
    if not starved:
        print("  none")
    else:
        for r in starved:
            print(f"  {r}")
    print()

    print("Conflicts observed:")
    # Only report in the latest tick to avoid noisy history
    conflicts = entries[-1].get("conflicts", [])
    if not conflicts:
        print("  none")
    else:
        print(f"  {json.dumps(conflicts)}")
    print()

    print("Last state delta:")
    last_entry = entries[-1]
    delta = last_entry.get("state_delta", {})
    print(f"  tick {last_entry.get('tick')}")
    if not delta:
        print("  (no changes)")
    else:
        for key, val in sorted(delta.items()):
            print(f"  {key} \u2192 {val}")

if __name__ == "__main__":
    main()
