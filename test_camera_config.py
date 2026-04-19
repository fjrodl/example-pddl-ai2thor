#!/usr/bin/env python3
"""
Camera configuration helper - Test different camera positions and angles
"""
import cv2
import time
from src.controller.thor_controller import Controller
from config.settings import SCENE, WIDTH, HEIGHT

def init_controller_basic():
    """Initialize controller without the camera"""
    return Controller(
        scene=SCENE,
        width=WIDTH,
        height=HEIGHT,
        renderThirdPartyCamera=True
    )

def test_camera_config(position, rotation, fov=90, duration=3):
    """Test a specific camera configuration"""
    print(f"\n{'='*70}")
    print(f"Testing Camera Configuration:")
    print(f"  Position: {position}")
    print(f"  Rotation: {rotation}")
    print(f"  FOV: {fov}°")
    print(f"{'='*70}")
    
    controller = init_controller_basic()
    controller.step(action="Pass")
    
    # Add camera
    event = controller.step(
        action="AddThirdPartyCamera",
        position=position,
        rotation=rotation,
        fieldOfView=fov
    )
    
    # Let camera settle
    for _ in range(3):
        controller.step(action="Pass")
    
    # Capture and display frames
    start_time = time.time()
    frame_count = 0
    
    while time.time() - start_time < duration:
        event = controller.step(action="Pass")
        
        if len(event.third_party_camera_frames) > 0:
            frame = event.third_party_camera_frames[0]
            
            # Display frame info
            if frame_count % 3 == 0:  # Every 3rd frame
                print(f"Frame {frame_count}: shape={frame.shape}, dtype={frame.dtype}, "
                      f"min={frame.min()}, max={frame.max()}")
            
            # Show in window
            if frame.dtype != 'uint8':
                frame = (frame.clip(0, 255)).astype('uint8')
            
            if len(frame.shape) == 3 and frame.shape[2] == 3:
                import numpy as np
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            else:
                frame_bgr = frame
            
            cv2.imshow("Camera Test", frame_bgr)
            cv2.waitKey(30)
            
            frame_count += 1
    
    controller.stop()
    cv2.destroyAllWindows()
    print(f"✅ Captured {frame_count} frames")

# =========================
# PRESET CAMERA CONFIGURATIONS
# =========================
CAMERA_PRESETS = {
    "top_down": {
        "name": "Top-down view (looking straight down)",
        "position": {"x": 0, "y": 3, "z": 0},
        "rotation": {"x": 90, "y": 0, "z": 0},
        "fov": 90
    },
    "isometric": {
        "name": "Isometric view (45° angle)",
        "position": {"x": 2, "y": 2, "z": 2},
        "rotation": {"x": 45, "y": 225, "z": 0},
        "fov": 90
    },
    "follow": {
        "name": "Follow camera (behind and above agent)",
        "position": {"x": -1, "y": 1.5, "z": 3},
        "rotation": {"x": 15, "y": 0, "z": 0},
        "fov": 90
    },
    "wide_vision": {
        "name": "Wide vision (large FOV)",
        "position": {"x": 1, "y": 2, "z": 1},
        "rotation": {"x": 30, "y": 45, "z": 0},
        "fov": 120
    },
    "closeup": {
        "name": "Close-up view (narrow FOV)",
        "position": {"x": 0.5, "y": 1.2, "z": 1},
        "rotation": {"x": 20, "y": 45, "z": 0},
        "fov": 45
    },
    "overhead_angle": {
        "name": "Overhead angle (better view of objects)",
        "position": {"x": 1, "y": 2.5, "z": 1},
        "rotation": {"x": 60, "y": 45, "z": 0},
        "fov": 100
    },
}

def main():
    print("\n" + "="*70)
    print("AI2-THOR CAMERA CONFIGURATION TESTER")
    print("="*70)
    print("\nAvailable presets:\n")
    
    for i, (key, config) in enumerate(CAMERA_PRESETS.items(), 1):
        print(f"{i}. {key.upper():20} - {config['name']}")
    
    print(f"{len(CAMERA_PRESETS) + 1}. CUSTOM - Define your own")
    print(f"{len(CAMERA_PRESETS) + 2}. TEST_ALL - Run through all presets")
    
    choice = input("\nSelect preset (1-7): ").strip()
    
    try:
        choice_num = int(choice)
        
        if choice_num == len(CAMERA_PRESETS) + 2:
            # Test all presets
            print("\n🔄 Testing all presets...\n")
            for key, config in CAMERA_PRESETS.items():
                test_camera_config(
                    config["position"],
                    config["rotation"],
                    config.get("fov", 90),
                    duration=2
                )
                time.sleep(1)
        
        elif choice_num == len(CAMERA_PRESETS) + 1:
            # Custom configuration
            print("\n📝 Custom Camera Configuration")
            print("Enter camera parameters:\n")
            
            x = float(input("Position X (default 0): ") or "0")
            y = float(input("Position Y (default 2): ") or "2")
            z = float(input("Position Z (default 0): ") or "0")
            
            rot_x = float(input("Rotation X (default 45): ") or "45")
            rot_y = float(input("Rotation Y (default 45): ") or "45")
            rot_z = float(input("Rotation Z (default 0): ") or "0")
            
            fov = float(input("Field of View (default 90): ") or "90")
            
            position = {"x": x, "y": y, "z": z}
            rotation = {"x": rot_x, "y": rot_y, "z": rot_z}
            
            test_camera_config(position, rotation, fov, duration=5)
        
        elif 1 <= choice_num <= len(CAMERA_PRESETS):
            preset_key = list(CAMERA_PRESETS.keys())[choice_num - 1]
            config = CAMERA_PRESETS[preset_key]
            test_camera_config(
                config["position"],
                config["rotation"],
                config.get("fov", 90),
                duration=5
            )
        else:
            print("❌ Invalid choice")
    
    except ValueError:
        print("❌ Please enter a valid number")

if __name__ == "__main__":
    main()
