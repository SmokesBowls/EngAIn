#!/usr/bin/env python3
"""
Test the fixed biomechanical constraints vs original intent
"""

import json
from biomechanical_constraints_fixed import BiomechanicalConstraintsFixed

def create_test_animation():
    """Create two slightly different walk cycles"""
    intent1 = {
        'left_thigh': {'rotation': 25},
        'right_thigh': {'rotation': -25},
        'left_arm': {'rotation': -20},
        'right_arm': {'rotation': 20},
        'hip': {'translate_x': 0, 'translate_y': 0}
    }
    
    intent2 = {
        'left_thigh': {'rotation': 35},  # More aggressive
        'right_thigh': {'rotation': -15}, # Asymmetric
        'left_arm': {'rotation': -10},
        'right_arm': {'rotation': 30},
        'hip': {'translate_x': 4, 'translate_y': 2}
    }
    
    return intent1, intent2

def compare_poses(intent, name, frame_num):
    constraints = BiomechanicalConstraintsFixed()
    
    pose = dict(intent)
    constrained = constraints.apply_biomechanical_constraints(
        pose, 
        t=frame_num * 0.1, 
        duration=1.0,
        ground_height=300
    )
    
    print(f"\n🔍 {name} - Frame {frame_num}")
    print("-" * 40)
    
    parts_to_compare = ['left_thigh', 'right_thigh', 'left_arm']
    for part in parts_to_compare:
        if part in intent and part in constrained:
            intent_val = intent[part].get('rotation', 0)
            constr_val = constrained[part].get('rotation', 0)
            diff = constr_val - intent_val
            preserved = abs(constr_val / intent_val * 100) if intent_val != 0 else 100
            print(f"  {part:15s}: {intent_val:6.1f} → {constr_val:6.1f} (Δ={diff:5.1f}, {preserved:.0f}% preserved)")
    
    return constrained

print("=" * 60)
print("🔄 TESTING INTENT PRESERVATION & VISIBLE DIFFERENCES")
print("=" * 60)

intent1, intent2 = create_test_animation()

for frame in [0, 5]:
    print("\n" + "=" * 60)
    print(f"FRAME {frame}")
    print("=" * 60)
    
    result1 = compare_poses(intent1, "INTENT 1", frame)
    result2 = compare_poses(intent2, "INTENT 2", frame)
    
    print("\n📊 DIFFERENCE BETWEEN INTENT 1 AND INTENT 2:")
    print("-" * 40)
    
    for part in ['left_thigh', 'right_thigh']:
        val1 = result1[part].get('rotation', 0)
        val2 = result2[part].get('rotation', 0)
        diff = abs(val2 - val1)
        pixel_diff = diff * 1.5
        
        print(f"  {part:15s}: {val1:6.1f} vs {val2:6.1f} (Δ={diff:.1f}, ~{pixel_diff:.0f} pixels)")
        if pixel_diff >= 3:
            print(f"      ✅ VISIBLE DIFFERENCE")
        else:
            print(f"      ⚠️ Small difference")
