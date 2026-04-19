#!/usr/bin/env python3
"""
Demo: Extended Multi-Step Plan Visualization
Shows: Look for object → Rotate to face it → Walk closer → Walk more → Pick up
"""
import time
import cv2
from src.controller.thor_controller import Controller
from config.settings import SCENE, WIDTH, HEIGHT
from src.symbolic.state_extractor import extract_state
from src.symbolic.pddl_generator import generate_problem
from src.planner.planner import run_planner
from src.executor.plan_executor import set_camera_id, display_third_party_frame
import re


def normalize(name):
    return re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())


def init_controller_with_camera():
    """Initialize controller with better camera angle for visualization"""
    controller = Controller(
        scene=SCENE,
        width=WIDTH,
        height=HEIGHT,
        renderThirdPartyCamera=True
    )
    
    # First pass to initialize
    controller.step(action="Pass")
    
    # Better camera angle - isometric view to see movement clearly
    event = controller.step(
        action="AddThirdPartyCamera",
        position={"x": 2, "y": 2, "z": 2},      # Isometric position
        rotation={"x": 45, "y": 225, "z": 0},   # Good angle to see movement
        fieldOfView=90
    )
    
    camera_id = event.metadata.get("thirdPartyCameras", [{}])[0].get("id") if event.metadata.get("thirdPartyCameras") else None
    
    # Settle camera
    controller.step(action="Pass")
    
    return controller, camera_id


def show_detailed_state(event, title=""):
    """Display detailed state information"""
    print(f"\n{'='*70}")
    if title:
        print(f"📊 {title}")
    print(f"{'='*70}")
    
    agent = event.metadata.get("agent", {})
    print(f"👤 Agent Position: ({agent['position']['x']:.2f}, {agent['position']['y']:.2f}, {agent['position']['z']:.2f})")
    print(f"   Rotation: {agent['rotation']['y']:.1f}°")
    print(f"   Inventory: {len(agent.get('inventoryObjects', []))} items")
    
    # Find closest visible objects
    objects = sorted(
        event.metadata.get('objects', []),
        key=lambda x: x.get('distance', float('inf'))
    )[:3]
    
    print(f"\n🔍 Closest Objects:")
    for i, obj in enumerate(objects, 1):
        dist = obj.get('distance', 'N/A')
        visible = "✅ Visible" if obj.get('visible') else "❌ Hidden"
        print(f"   {i}. {obj['objectId'][:30]:30} | Distance: {dist:.2f}m | {visible}")
    
    print(f"{'='*70}\n")


def demo_extended_plan():
    """
    Demo: Extended multi-step plan with visualization
    """
    print("\n" + "="*70)
    print("🎬 EXTENDED MULTI-STEP PLAN DEMO")
    print("="*70)
    print("\nThis demo shows a longer, more interesting plan with:")
    print("  1. Looking around to find objects")
    print("  2. Rotating to face the target")
    print("  3. Walking closer (multiple steps)")
    print("  4. Picking up the object")
    print("="*70 + "\n")
    
    # Initialize
    print("[INIT] Initializing controller with camera...")
    controller, camera_id = init_controller_with_camera()
    set_camera_id(camera_id)
    print(f"✅ Camera ready: {camera_id}\n")
    
    # Perform initial steps to let scene settle
    for _ in range(5):
        controller.step(action="Pass")
    
    # Show initial state
    event = controller.last_event
    show_detailed_state(event, "INITIAL STATE - Looking for objects")
    
    # Extract state
    print("[STATE] Extracting predicates from environment...")
    predicates, objects = extract_state(event)
    print(f"✅ Found {len(objects)} objects, {len(predicates)} predicates\n")
    
    # Find target
    visible = set()
    pickupable = set()
    
    for p in predicates:
        tokens = p.replace("(", "").replace(")", "").split()
        if tokens[0] == "visible":
            visible.add(tokens[1])
        elif tokens[0] == "pickupable":
            pickupable.add(tokens[1])
    
    candidates = sorted([
        obj for obj in (visible & pickupable)
        if not any(x in obj for x in ["fridge", "cabinet", "sink", "table"])
    ])
    
    if not candidates:
        print("❌ No valid pickup targets found")
        return
    
    target = candidates[0]
    goal = f"(holding {target})"
    
    print(f"🎯 TARGET: {goal}")
    print(f"✅ {len(candidates)} valid pickup candidates\n")
    
    input("Press ENTER to continue with planning...")
    
    # Generate PDDL problem
    print("\n[PLANNING] Generating PDDL problem...")
    predicates_filtered = [p for p in predicates if target in p]
    objects_set = {target}
    generate_problem(predicates_filtered, objects_set, goal)
    print("✅ PDDL problem generated\n")
    
    input("Press ENTER to run planner...")
    
    # Run planner
    print("[PLANNER] Running PDDL planner...")
    run_planner()
    
    with open("plan.txt") as f:
        plan_content = f.read()
    
    print("\n" + "="*70)
    print("📋 GENERATED PLAN:")
    print("="*70)
    for i, line in enumerate(plan_content.strip().split('\n'), 1):
        print(f"  {i}. {line}")
    print("="*70 + "\n")
    
    if not plan_content.strip():
        print("❌ Empty plan")
        return
    
    input("Press ENTER to execute plan (watch the camera visualization)...\n")
    
    # Execute plan manually with detailed visualization
    print("🚀 EXECUTING PLAN WITH DETAILED VISUALIZATION:\n")
    
    # Extract actions
    actions = []
    for line in plan_content.strip().split('\n'):
        line = line.strip().strip('()')
        if line and not line.startswith(';'):
            actions.append(line)
    
    print(f"📋 Executing {len(actions)} actions:\n")
    
    # MOVE-TO action
    if actions and actions[0].startswith("move-to"):
        print("🔶 PHASE 1: MOVE TO OBJECT")
        print("-" * 70)
        print("Starting detailed movement visualization...")
        print("Watch: Rotation → Movement → Approach\n")
        time.sleep(1)
        
        # Import executor function
        from src.executor.plan_executor import move_to_object
        success = move_to_object(controller, target, max_steps=80, delay=0.15)
        
        if success:
            print("\n✅ Movement complete - object reached!\n")
        else:
            print("\n⚠️  Movement timeout\n")
        
        input("Press ENTER to continue to pickup phase...")
    
    # PICKUP action
    if len(actions) > 1 and actions[1].startswith("pickup"):
        print("\n🔶 PHASE 2: PICKUP OBJECT")
        print("-" * 70)
        
        event = controller.last_event
        show_detailed_state(event, "BEFORE PICKUP")
        
        # Find and pickup object
        for obj in event.metadata.get('objects', []):
            if normalize(obj['objectId']) == target:
                obj_id = obj['objectId']
                print(f"[PICKUP] Attempting to pick up: {obj_id}\n")
                time.sleep(0.5)
                
                event = controller.step(
                    action="PickupObject",
                    objectId=obj_id
                )
                
                display_third_party_frame(event)
                time.sleep(1)
                
                show_detailed_state(event, "AFTER PICKUP")
                
                if obj_id in event.metadata['agent'].get('inventoryObjects', []):
                    print(f"✅ SUCCESS! {obj_id} is now in inventory!\n")
                else:
                    print(f"⚠️  Object pickup may have failed\n")
                
                break
    
    # Summary
    print("="*70)
    print("✅ PLAN EXECUTION COMPLETE!")
    print("="*70)
    print("\nSummary:")
    print(f"  • Rotated to find object")
    print(f"  • Walked multiple steps toward target")
    print(f"  • Picked up: {target}")
    print("="*70 + "\n")
    
    controller.stop()
    cv2.destroyAllWindows()
    print("🛑 Session ended")


if __name__ == "__main__":
    demo_extended_plan()
