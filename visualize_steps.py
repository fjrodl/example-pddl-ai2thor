#!/usr/bin/env python3
"""
Interactive step-by-step visualization of AI2-Thor simulator
Shows camera frames, state, and metadata for each action
"""
import time
import os
import cv2
import numpy as np
import sys

from src.controller.thor_controller import init_controller
from src.symbolic.state_extractor import extract_state
from src.symbolic.pddl_generator import generate_problem
from src.planner.planner import run_planner
from src.executor.plan_executor import set_camera_id
import re


# =========================
#  CONFIGURACIÓN
# =========================
CONFIG = {
    "GOAL": "(holding mug)",
    "DELAY_BETWEEN_STEPS": 2.0,  # segundos entre pasos
    "SAVE_FRAMES": True,          # guardar frames en disco
    "FRAME_OUTPUT_DIR": "frames_output",
    "VERBOSE": True,
}


# =========================
#  UTILIDADES
# =========================
def log(msg):
    if CONFIG["VERBOSE"]:
        print(f"[VIZ] {msg}")


def normalize(name):
    """Convierte objectId de THOR a nombre PDDL"""
    return re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())


def display_frame_with_info(event, step_num, action_name=None, info_text=None):
    """
    Muestra el frame de la cámara con información superpuesta
    """
    if len(event.third_party_camera_frames) == 0:
        log(f"⚠️  No hay frames disponibles en step {step_num}")
        return None
    
    frame = event.third_party_camera_frames[0]
    
    # Convertir a formato correcto si es necesario
    if isinstance(frame, np.ndarray):
        if frame.dtype != np.uint8:
            frame = np.clip(frame, 0, 255).astype(np.uint8)
        
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Crear copia para añadir texto
        display_frame = frame.copy()
        
        # Añadir información superpuesta
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        color = (0, 255, 0)  # Verde
        thickness = 2
        
        y_offset = 30
        
        # Step number
        cv2.putText(display_frame, f"STEP {step_num}", (10, y_offset),
                   font, font_scale, color, thickness)
        y_offset += 35
        
        # Action name
        if action_name:
            cv2.putText(display_frame, f"ACTION: {action_name}", (10, y_offset),
                       font, font_scale, color, thickness)
            y_offset += 35
        
        # Additional info
        if info_text:
            for line in info_text.split('\n'):
                cv2.putText(display_frame, line, (10, y_offset),
                           font, 0.6, color, 1)
                y_offset += 25
        
        # Mostrar
        cv2.imshow("AI2-Thor Step-by-Step Visualization", display_frame)
        cv2.waitKey(1)
        
        # Guardar frame si está habilitado
        if CONFIG["SAVE_FRAMES"]:
            os.makedirs(CONFIG["FRAME_OUTPUT_DIR"], exist_ok=True)
            frame_path = os.path.join(CONFIG["FRAME_OUTPUT_DIR"], f"step_{step_num:04d}.jpg")
            cv2.imwrite(frame_path, display_frame)
            log(f"📸 Frame guardado: {frame_path}")
        
        return display_frame
    
    return None


def print_state_info(event, step_num):
    """
    Imprime información detallada del estado actual
    """
    print("\n" + "="*70)
    print(f"STEP {step_num} - SIMULATOR STATE")
    print("="*70)
    
    # Información del agente
    agent = event.metadata.get("agent", {})
    print(f"\n👤 AGENT:")
    print(f"  Position: ({agent['position']['x']:.2f}, {agent['position']['y']:.2f}, {agent['position']['z']:.2f})")
    print(f"  Rotation: {agent['rotation']['y']:.1f}°")
    print(f"  Inventory: {agent.get('inventoryObjects', [])}")
    
    # Objetos cercanos
    print(f"\n🔍 NEARBY OBJECTS ({len(event.metadata.get('objects', []))} total):")
    for i, obj in enumerate(event.metadata.get('objects', [])[:5]):  # primeros 5
        obj_id = obj.get('objectId', 'unknown')
        distance = obj.get('distance', 'N/A')
        visible = obj.get('visible', False)
        print(f"  {i+1}. {obj_id}")
        print(f"     Distance: {distance}, Visible: {visible}")
    
    if len(event.metadata.get('objects', [])) > 5:
        print(f"  ... y {len(event.metadata.get('objects', [])) - 5} objetos más")
    
    print("\n" + "="*70 + "\n")


def print_predicates(predicates, objects):
    """
    Imprime predicados extraídos
    """
    print("\n📋 STATE PREDICATES:")
    print("-" * 50)
    for p in predicates[:10]:  # primeros 10
        print(f"  {p}")
    if len(predicates) > 10:
        print(f"  ... y {len(predicates) - 10} predicados más")
    print()


def execute_step(controller, action_dict, step_num):
    """
    Ejecuta un paso individual y muestra visualización
    """
    log(f"\n🎬 Ejecutando Step {step_num}...")
    
    # Ejecutar acción
    event = controller.step(**action_dict)
    
    # Extraer información
    action_name = action_dict.get("action", "Unknown")
    action_params = {k: v for k, v in action_dict.items() if k != "action"}
    
    # Mostrar estado
    print_state_info(event, step_num)
    
    # Preparar información para mostrar en frame
    info_text = f"Parameters: {str(action_params)[:50]}"
    
    # Mostrar frame con información
    display_frame_with_info(event, step_num, action_name, info_text)
    
    # Esperar
    log(f"⏸️  Esperando {CONFIG['DELAY_BETWEEN_STEPS']}s antes del siguiente paso...")
    time.sleep(CONFIG["DELAY_BETWEEN_STEPS"])
    
    return event


def interactive_mode(controller):
    """
    Modo interactivo: permite controlar el simulador paso a paso
    """
    log("\n🎮 MODO INTERACTIVO - Controla el simulador paso a paso\n")
    
    step = 0
    
    actions = [
        {"action": "MoveAhead", "moveMagnitude": 0.25},
        {"action": "RotateRight", "degrees": 15},
        {"action": "MoveAhead", "moveMagnitude": 0.25},
        {"action": "LookUp", "degrees": 15},
        {"action": "Pass"},
    ]
    
    print("\n📌 Secuencia de acciones planeadas:")
    for i, act in enumerate(actions):
        print(f"  {i+1}. {act['action']} {[f'{k}={v}' for k,v in act.items() if k != 'action']}")
    
    print("\n")
    
    for i, action in enumerate(actions):
        input(f"Presiona ENTER para ejecutar: {action['action']}... ")
        execute_step(controller, action, i)
    
    cv2.destroyAllWindows()


def pddl_planning_visualization(controller, interactive=True):
    """
    Visualiza el ciclo completo de PDDL: estado → planner → ejecución
    """
    log("\n🤖 MODO PDDL - Visualización del ciclo de planificación\n")
    
    step = 0
    
    # 1. PERCEPCIÓN
    log("1️⃣  PERCEPTION - Extrayendo estado...")
    event = controller.last_event
    print_state_info(event, 0)
    
    predicates, objects = extract_state(event)
    print_predicates(predicates, objects)
    
    # 2. SELECCIONAR GOAL
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
        log("❌ No hay objetos válidos para pickup")
        return
    
    target = candidates[0]
    goal = f"(holding {target})"
    
    print(f"\n🎯 GOAL SELECTED: {goal}\n")
    if interactive:
        input("Presiona ENTER para continuar con la planificación...")
    else:
        time.sleep(1)
    
    # 3. GENERAR PDDL Y PLANIFICAR
    log("\n2️⃣  PLANNING - Generando PDDL y ejecutando planificador...")
    
    predicates = [p for p in predicates if target in p]
    objects = {target}
    
    generate_problem(predicates, objects, goal)
    log("✅ PDDL problem generado")
    
    if interactive:
        input("Presiona ENTER para ejecutar el planificador...")
    else:
        time.sleep(0.5)
    
    run_planner()
    
    # Leer plan
    with open("plan.txt") as f:
        plan_content = f.read()
    
    print("\n" + "="*70)
    print("PLAN GENERADO:")
    print("="*70)
    print(plan_content)
    print("="*70 + "\n")
    
    if not plan_content.strip():
        log("❌ Plan vacío")
        return
    
    # 4. EJECUTAR PLAN PASO A PASO
    log("\n3️⃣  EXECUTION - Ejecutando plan paso a paso...\n")
    
    actions = parse_plan(plan_content)
    
    print(f"📋 Total acciones en plan: {len(actions)}\n")
    
    for i, action in enumerate(actions):
        action_dict = parse_pddl_action(action)
        if action_dict:
            if interactive:
                input(f"Presiona ENTER para ejecutar step {i+1}: {action}... ")
            else:
                log(f"Ejecutando step {i+1}: {action}")
            execute_step(controller, action_dict, i+1)
    
    cv2.destroyAllWindows()
    log("\n✅ Plan ejecutado completamente!")


def parse_plan(plan_content):
    """
    Parsea el contenido del plan para extraer acciones
    """
    actions = []
    for line in plan_content.strip().split('\n'):
        line = line.strip()
        if line and not line.startswith(';'):
            # Eliminar paréntesis exteriores
            line = line.strip('()')
            actions.append(line)
    return actions


def parse_pddl_action(action_str):
    """
    Convierte una acción PDDL a formato que entiende AI2-Thor
    """
    tokens = action_str.split()
    if not tokens:
        return None
    
    action_name = tokens[0]
    params = tokens[1:] if len(tokens) > 1 else []
    
    # Mapeo de acciones PDDL a AI2-Thor
    if action_name == "move-to":
        return {
            "action": "MoveAhead",
            "moveMagnitude": 0.1
        }
    elif action_name == "pickup":
        return {
            "action": "PickupObject",
            "objectId": params[0] if params else None
        }
    elif action_name == "put-down":
        return {
            "action": "PutObject",
            "receptacleObjectId": params[0] if params else None
        }
    else:
        return {"action": "Pass"}


# =========================
#  MAIN
# =========================
def main():
    log("🚀 AI2-Thor Step-by-Step Visualization Tool\n")
    
    # Inicializar
    log("Inicializando controlador...")
    controller, camera_id = init_controller()
    log(f"✅ Controlador listo | Camera ID: {camera_id}\n")
    set_camera_id(camera_id)
    
    # Detectar modo interactivo
    is_interactive = sys.stdin.isatty()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        is_interactive = False
    
    # Menú
    if is_interactive:
        print("="*70)
        print("MODO DE VISUALIZACIÓN")
        print("="*70)
        print("1. Modo Interactivo (controla el simulador manualmente)")
        print("2. Modo PDDL (visualiza ciclo completo de planificación)")
        print("="*70)
        
        choice = input("\nSelecciona modo (1 o 2): ").strip()
        
        if choice == "1":
            interactive_mode(controller)
        elif choice == "2":
            pddl_planning_visualization(controller, interactive=True)
        else:
            log("Opción inválida")
    else:
        # Modo automático: ejecutar PDDL sin pausas
        log("🔄 Modo automático (no-interactivo)")
        pddl_planning_visualization(controller, interactive=False)
    
    controller.stop()
    log("\n🛑 Sesión finalizada")


# =========================
#  ENTRY POINT
# =========================
if __name__ == "__main__":
    # Usage:
    #   python visualize_steps.py              # Interactive mode
    #   python visualize_steps.py --auto       # Auto mode (PDDL visualization without pauses)
    main()
