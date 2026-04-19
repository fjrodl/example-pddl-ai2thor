import time
import re
import cv2
import numpy as np


# =========================
# 🎥 GLOBAL CAMERA CONFIG
# =========================
CAMERA_ID = None  # Will be set by set_camera_id()

def set_camera_id(camera_id):
    """Configurar el ID de la cámara de tercera persona"""
    global CAMERA_ID
    CAMERA_ID = camera_id
    print(f"[INFO] Camera ID establecido: {CAMERA_ID}")



# =========================
# ⚙️ CONFIG LOCAL (puedes moverlo a settings.py)
# =========================
DEFAULT_CONFIG = {
    "DELAY": 0.0,
    "VERBOSE": True,
    "FAIL_FAST": False,   # si una acción falla, parar ejecución
}


# =========================
# 🧠 UTILIDADES
# =========================
def log(msg, verbose=True):
    if verbose:
        print(f"[EXECUTOR] {msg}")


def normalize(name):
    """Convierte objectId de THOR a nombre PDDL"""
    return re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())


def display_third_party_frame(event):
    """Captura y muestra el frame de la cámara de tercera persona"""
    import numpy as np
    
    if len(event.third_party_camera_frames) > 0:
        frame = event.third_party_camera_frames[0]
        
        # 👇 Asegurar que el frame está en formato correcto
        if isinstance(frame, np.ndarray):
            # Convertir a uint8 si es necesario
            if frame.dtype != np.uint8:
                frame = np.clip(frame, 0, 255).astype(np.uint8)
            
            # Si está en RGB, convertir a BGR para OpenCV
            if len(frame.shape) == 3 and frame.shape[2] == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # Mostrar frame
            cv2.imshow("Third Person Camera", frame)
            cv2.waitKey(1)  # No bloquear, permitir otras operaciones
            
            log(f"Frame capturado: {frame.dtype}, shape={frame.shape}, min={frame.min()}, max={frame.max()}", True)
        
        return frame
    else:
        log(f"⚠️  No third_party_camera_frames disponibles. Total frames: 0", True)
        return None


def find_object_by_name(event, target_name):
    """Busca objeto en THOR a partir del nombre PDDL"""
    for obj in event.metadata["objects"]:
        name = normalize(obj["objectId"])
        if name == target_name:
            return obj
    return None


# =========================
# 🎬 ACCIONES
# =========================
def move_to_object(controller, target_name, max_steps=80, delay=0.2):
    """
    Move to object with detailed step logging
    Breaks movement into smaller, more visible steps
    """
    import time
    import math
    import numpy as np

    # Initial frame
    event = controller.step(action="Pass")
    frame = display_third_party_frame(event)

    event = controller.last_event
    sub_step = 0

    for step in range(max_steps):
        event = controller.last_event
        agent = event.metadata["agent"]
        agent_pos = agent["position"]
        agent_rot = agent["rotation"]["y"]

        target_obj = None

        for obj in event.metadata["objects"]:
            name = normalize(obj["objectId"])
            if name == target_name:
                target_obj = obj
                break

        if target_obj is None:
            log(f"[ROTATION] ↻ Buscando objeto, girando a la derecha... (sub-step {sub_step})", True)
            event = controller.step(action="RotateRight", degrees=15)
            display_third_party_frame(event)
            sub_step += 1
            time.sleep(delay)
            continue

        obj_pos = target_obj["position"]
        distance = target_obj.get("distance", float('inf'))
        
        dx = obj_pos["x"] - agent_pos["x"]
        dz = obj_pos["z"] - agent_pos["z"]

        angle_to_obj = math.degrees(math.atan2(dx, dz))
        diff = (angle_to_obj - agent_rot + 360) % 360

        # ✔ Ya cerca del objeto
        if distance is not None and distance < 0.5:
            log(f"[APPROACH] ✅ ¡Objeto alcanzado! Distancia: {distance:.2f}m", True)
            display_third_party_frame(event)
            return True

        # 🔁 GIRAR hacia el objeto primero
        if diff > 180:
            log(f"[ROTATION] ↻ Girando izquierda... Ángulo: {diff:.0f}° (sub-step {sub_step})", True)
            event = controller.step(action="RotateLeft", degrees=10)
        elif diff > 10:
            log(f"[ROTATION] ↻ Girando derecha... Ángulo: {diff:.0f}° (sub-step {sub_step})", True)
            event = controller.step(action="RotateRight", degrees=10)
        else:
            # 🚶 AVANZAR si ya está orientado
            move_distance = 0.2  # Larger steps for visibility
            log(f"[MOVEMENT] 🚶 Avanzando {move_distance}m hacia el objeto... Distancia restante: {distance:.2f}m (sub-step {sub_step})", True)
            event = controller.step(action="MoveAhead", moveMagnitude=move_distance)
        
        # Mostrar frame de cada sub-paso
        display_third_party_frame(event)
        sub_step += 1
        time.sleep(delay)

    log(f"⚠️  No se alcanzó el objeto después de {max_steps} pasos", True)
    return False


def action_move_to(controller, target, config):
    success = move_to_object(
        controller,
        target,
        delay=config.get("DELAY", 0.5)
    )

    if success:
        log(f"Move-to ejecutado: {target}", config["VERBOSE"])
    else:
        log(f"No se pudo mover a: {target}", config["VERBOSE"])

    return success
    
def action_pickup(controller, target, config):
    event = controller.last_event
    obj = find_object_by_name(event, target)

    if obj is None:
        log(f"No se encontró objeto: {target}", config["VERBOSE"])
        return False

    if not obj["pickupable"]:
        log(f"Objeto no pickupable: {target}", config["VERBOSE"])
        return False

    # 1. moverse hacia el objeto
    # if not move_to_object(controller, target):
    #     log(f"No se pudo alcanzar: {target}", config["VERBOSE"])
    #     return False

    # 2. ejecutar pickup
    controller.step(
        action="PickupObject",
        objectId=obj["objectId"]
    )

    log(f"Pickup ejecutado: {target}", config["VERBOSE"])
    return True


# =========================
# 🧩 PARSER DE PLAN
# =========================
def parse_plan_line(line):
    line = line.strip().lower()

    if not line:
        return None, []

    # eliminar dobles paréntesis
    line = line.replace("((", "(").replace("))", ")")

    tokens = line.replace("(", "").replace(")", "").split()

    if not tokens:
        return None, []

    return tokens[0], tokens[1:]


# =========================
# ▶️ EJECUTOR PRINCIPAL
# =========================
def execute_plan(controller, plan_path="plan.txt", config=None):
    if config is None:
        config = DEFAULT_CONFIG

    with open(plan_path) as f:
        lines = f.readlines()

    for step_id, line in enumerate(lines):
        action, params = parse_plan_line(line)

        if action is None:
            continue

        log(f"Step {step_id}: {action} {params}", config["VERBOSE"])

        success = False

        # =========================
        # 🔌 MAPEO DE ACCIONES
        # =========================
        if action == "pickup":
            success = action_pickup(controller, params[0], config)

        elif action == "move-to":
            success = action_move_to(controller, params[0], config)

        else:
            log(f"Acción no soportada: {action}", config["VERBOSE"])

        # =========================
        # ⚠️ GESTIÓN DE ERRORES
        # =========================
        if not success:
            msg = f"Falló acción {action} {params}"

            if config["FAIL_FAST"]:
                raise RuntimeError(msg)
            else:
                log(msg, config["VERBOSE"])

        # =========================
        # ⏱️ CONTROL DE TIEMPO
        # =========================
        if config["DELAY"] > 0:
            time.sleep(config["DELAY"])