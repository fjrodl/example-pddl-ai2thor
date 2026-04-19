from ai2thor.controller import Controller
from config.settings import SCENE, WIDTH, HEIGHT

def init_controller():
    controller = Controller(
        scene=SCENE,
        width=WIDTH,
        height=HEIGHT,
        renderThirdPartyCamera=True  # 👈 IMPORTANTE: habilitar renderización
    )

    # 👇 IMPORTANTE: primer step para inicializar escena
    event = controller.step(action="Pass")

    # 👇 añadir cámara DESPUÉS de inicializar
    # Isometric view for better visualization of movement
    event = controller.step(
        action="AddThirdPartyCamera",
        position={"x": 2, "y": 2, "z": 2},      # Isometric position
        rotation={"x": 45, "y": 225, "z": 0},   # Good angle to see movement and objects
        fieldOfView=90
    )
    
    # 👇 Guardar el ID de la cámara para usarlo luego
    camera_id = event.metadata.get("thirdPartyCameras", [{}])[0].get("id") if event.metadata.get("thirdPartyCameras") else None
    
    # 👇 FORZAR actualización real de la cámara
    event = controller.step(action="Pass")

    return controller, camera_id