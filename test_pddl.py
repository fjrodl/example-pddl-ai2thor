#!/usr/bin/env python3
"""
Simplified PDDL testing script without blocking camera visualization
"""
import time
import os

from src.controller.thor_controller import init_controller
from src.symbolic.state_extractor import extract_state
from src.symbolic.pddl_generator import generate_problem
from src.planner.planner import run_planner
from src.executor.plan_executor import execute_plan, set_camera_id


# =========================
#  CONFIGURACIÓN GLOBAL (PDDL Testing)
# =========================
CONFIG = {
    "GOAL": "(holding mug)",
    "MAX_STEPS": 10,
    "DELAY": 0.5,               # reducido para testing
    "DEMO_MODE": False,         # sin pauses largas
    "REPLAN": False,            # ejecución única
    "SAVE_PDDL": True,
    "SAVE_PLAN": True,
    "VERBOSE": True,
    "SHOW_CAMERA": False,       # desactivar visualización de cámara por ahora
}


# =========================
#  UTILIDADES
# =========================
def log(msg):
    if CONFIG["VERBOSE"]:
        print(f"[PDDL_TEST] {msg}")


def maybe_sleep():
    if CONFIG["DEMO_MODE"]:
        time.sleep(CONFIG["DELAY"])


# =========================
# CICLO PRINCIPAL
# =========================
def planning_cycle(controller, step_id=0):
    log(f"--- PLANNING CYCLE {step_id} ---")

    # 1. PERCEPCIÓN
    event = controller.last_event
    predicates, objects = extract_state(event)

    log(f"Objetos detectados: {len(objects)}")
    log(f"Predicados generados: {len(predicates)}")

    # =========================
    # 🎯 SELECCIÓN DE GOAL DINÁMICO
    # =========================
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
        log("❌ No hay objetos válidos para pickup. Abortando ciclo.")
        return False

    # selección estable (siempre el mismo)
    target = candidates[0]
    goal = f"(holding {target})"

    log(f"✅ Goal seleccionado: {goal}")

    # Reducir estado al objetivo para evitar explosión combinatoria
    predicates = [p for p in predicates if target in p]
    objects = {target}

    # =========================
    # 2. GENERAR PROBLEMA PDDL
    # =========================
    generate_problem(predicates, objects, goal)

    if CONFIG["SAVE_PDDL"]:
        log("✅ Problem PDDL generado")

    # =========================
    # 3. PLANIFICAR
    # =========================
    log("🔍 Ejecutando planificador...")
    run_planner()

    if CONFIG["SAVE_PLAN"]:
        log("✅ Plan generado")

    # =========================
    # 🧪 DEBUG PLAN
    # =========================
    with open("plan.txt") as f:
        content = f.read()
        print("\n" + "="*50)
        print("PLAN GENERADO:")
        print("="*50)
        print(content)
        print("="*50 + "\n")

    # =========================
    # ❌ SI NO HAY PLAN → NO EJECUTAR
    # =========================
    if not content.strip():
        log("❌ Plan vacío. No se ejecuta nada.")
        return False

    # =========================
    # 4. EJECUTAR PLAN
    # =========================
    log("🚀 Ejecutando plan...")
    execute_plan(
        controller,
        plan_path="plan.txt",
        config={
            "DELAY": CONFIG["DELAY"],
            "VERBOSE": CONFIG["VERBOSE"],
            "FAIL_FAST": False
        }
    )
    
    return True


# =========================
#  MAIN
# =========================
def main():
    log("🚀 Inicializando AI2-THOR with PDDL Testing...")
    
    controller, camera_id = init_controller()
    log(f"✅ Controlador inicializado | Camera ID: {camera_id}")
    
    # Configurar el ID de la cámara en el executor
    set_camera_id(camera_id)

    # acción inicial para obtener estado
    log("📸 Capturando estado inicial...")
    for i in range(3):
        controller.step(action="Pass")

    log("🔄 Iniciando ciclo de planificación PDDL...")
    success = planning_cycle(controller, step_id=0)
    
    if success:
        log("✅ Ciclo completado exitosamente")
    else:
        log("❌ Ciclo falló o fue abortado")

    controller.stop()
    log("🛑 Ejecución finalizada")


# =========================
#  ENTRY POINT
# =========================
if __name__ == "__main__":
    main()
