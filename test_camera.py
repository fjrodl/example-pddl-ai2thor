#!/usr/bin/env python3
"""
Diagnostic script to test third-party camera visualization
"""
import cv2
import numpy as np
from src.controller.thor_controller import init_controller
from src.executor.plan_executor import set_camera_id, display_third_party_frame

def test_camera():
    print("[TEST] Inicializando controlador con cámara...")
    controller, camera_id = init_controller()
    print(f"✅ Camera ID: {camera_id}")
    
    set_camera_id(camera_id)
    
    # Realizar algunos pasos para verificar que se capturan frames
    print("\n[TEST] Capturando frames durante 5 pasos...\n")
    
    for step in range(5):
        print(f"--- Step {step} ---")
        event = controller.step(action="MoveAhead", moveMagnitude=0.1)
        
        # Mostrar información del evento
        print(f"third_party_camera_frames: {len(event.third_party_camera_frames)}")
        if hasattr(event, 'metadata') and 'thirdPartyCameras' in event.metadata:
            print(f"thirdPartyCameras in metadata: {len(event.metadata['thirdPartyCameras'])}")
        
        # Intentar mostrar el frame
        frame = display_third_party_frame(event)
        
        if frame is not None:
            print(f"✅ Frame capturado exitosamente")
        else:
            print(f"❌ No se pudo capturar frame")
        
        print()
    
    print("[TEST] Cerrando ventanas...")
    cv2.destroyAllWindows()
    print("✅ Test completado")

if __name__ == "__main__":
    test_camera()
