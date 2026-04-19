#!/usr/bin/env python3
"""
CAMERA CONFIGURATION GUIDE

This file explains how to adjust the camera in AI2-Thor

CAMERA PARAMETERS (in src/controller/thor_controller.py):
=========================================================

1. POSITION - Where the camera is located in 3D space
   position={"x": 0, "y": 4, "z": 0}
   
   - x: Left/Right (positive = right from agent's perspective)
   - y: Up/Down (height - typically 0.5 to 4)
   - z: Forward/Back (positive = forward)

2. ROTATION - Which direction the camera is looking
   rotation={"x": 90, "y": 0, "z": 0}
   
   - x: Pitch (vertical tilt)
     * 0° = looking horizontally
     * 45° = looking 45° down
     * 90° = looking straight down
     * -45° = looking 45° up
   
   - y: Yaw (horizontal rotation)
     * 0° = looking forward (positive Z)
     * 45° = looking northeast
     * 90° = looking right (positive X)
     * 180° = looking back (negative Z)
     * 270° = looking left (negative X)
   
   - z: Roll (camera tilt/rotation)
     * Usually 0° for stable view
     * 45° = camera tilted 45°

3. FIELD OF VIEW (FOV)
   fieldOfView=90
   
   - 30° = narrow, zoomed in
   - 60° = normal
   - 90° = wide
   - 120° = very wide (fish-eye effect)

QUICK FIXES FOR "SEEING NOTHING":
==================================

PROBLEM: Camera pointing at blank wall
SOLUTION: Adjust position closer to scene center and rotation angle

PROBLEM: Camera too high, only seeing ceiling
SOLUTION: Increase x or z rotation angle (pitch down)

PROBLEM: Camera too far away, objects are tiny
SOLUTION: Increase FOV (120) or move camera closer

PROBLEM: Camera orientation is wrong
SOLUTION: Adjust y rotation (yaw) to change horizontal direction


RECOMMENDED CAMERA CONFIGURATIONS:
===================================

Top-Down View (Bird's eye):
  position: {"x": 0, "y": 3, "z": 0}
  rotation: {"x": 90, "y": 0, "z": 0}
  fov: 90

Isometric View (3D perspective):
  position: {"x": 2, "y": 2, "z": 2}
  rotation: {"x": 45, "y": 225, "z": 0}
  fov: 90

Follow Camera (behind agent):
  position: {"x": -1, "y": 1.5, "z": 3}
  rotation: {"x": 15, "y": 0, "z": 0}
  fov: 90

Wide Vision (see more area):
  position: {"x": 1, "y": 2, "z": 1}
  rotation: {"x": 30, "y": 45, "z": 0}
  fov: 120

Close-up (detail view):
  position: {"x": 0.5, "y": 1.2, "z": 1}
  rotation: {"x": 20, "y": 45, "z": 0}
  fov: 45


HOW TO FIND THE RIGHT CONFIGURATION:
======================================

1. Use test_camera_config.py to preview different configurations:
   
   $ python test_camera_config.py
   
   This will show you several presets and let you test them!

2. Once you find a good one, update src/controller/thor_controller.py:
   
   OLD:
   event = controller.step(
       action="AddThirdPartyCamera",
       position={"x": 0, "y": 4, "z": 0},          # ← CHANGE THIS
       rotation={"x": 90, "y": 0, "z": 0},        # ← AND THIS
       fieldOfView=90                               # ← AND THIS
   )
   
   NEW (Example - Isometric):
   event = controller.step(
       action="AddThirdPartyCamera",
       position={"x": 2, "y": 2, "z": 2},
       rotation={"x": 45, "y": 225, "z": 0},
       fieldOfView=90
   )

3. Re-run your script to see changes applied


DEBUGGING FRAME ISSUES:
=======================

Frame statistics from visualize_steps.py or test_pddl.py:
  min=136, max=255     ✅ Good - values spread across range
  min=0, max=0         ❌ Black frame - camera pointing at nothing
  min=255, max=255     ❌ White frame - camera pointing at bright area

If you see all black frames:
  1. Check position - try {"x": 0, "y": 2, "z": 0}
  2. Check rotation - try {"x": 60, "y": 45, "z": 0}
  3. Check FOV - try 100-120 for wider view


EXAMPLE ADJUSTMENT:
====================

Current (Black frames):
  position={"x": 10, "y": 10, "z": 10}
  rotation={"x": 90, "y": 0, "z": 0}
  fieldOfView=90

Fix - Move closer and angle towards scene:
  position={"x": 1, "y": 2, "z": 1}
  rotation={"x": 45, "y": 45, "z": 0}
  fieldOfView=100

"""

if __name__ == "__main__":
    print(__doc__)
