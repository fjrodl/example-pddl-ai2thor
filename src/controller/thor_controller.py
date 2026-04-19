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
    event = controller.step(
        action="AddThirdPartyCamera",
        position={"x": 0, "y": 4, "z": 0},
        rotation={"x": 90, "y": 0, "z": 0},
        fieldOfView=90
    )
    
    # 👇 Guardar el ID de la cámara para usarlo luego
    camera_id = event.metadata.get("thirdPartyCameras", [{}])[0].get("id") if event.metadata.get("thirdPartyCameras") else None
    
    # 👇 FORZAR actualización real de la cámara
    event = controller.step(action="Pass")

    return controller, camera_id