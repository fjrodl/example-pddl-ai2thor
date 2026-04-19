import time
import os

from src.controller.thor_controller import init_controller
from src.symbolic.state_extractor import extract_state
from src.symbolic.pddl_generator import generate_problem
from src.planner.planner import run_planner
from src.executor.plan_executor import execute_plan, set_camera_id


# =========================
#  CONFIGURACIÓN GLOBAL
# =========================
CONFIG = {
    "GOAL": "(holding mug)",
    "MAX_STEPS": 10,            # para replanning iterativo
    "DELAY": 1.5,               # segundos entre acciones (modo demo)
    "DEMO_MODE": True,          # activar visualización lenta
    "REPLAN": False,            # ciclo sense-plan-act continuo
    "SAVE_PDDL": True,
    "SAVE_PLAN": True,
    "VERBOSE": True,
}


# =========================
#  UTILIDADES
# =========================
def log(msg):
    if CONFIG["VERBOSE"]:
        print(f"[INFO] {msg}")


def maybe_sleep():
    if CONFIG["DEMO_MODE"]:
        time.sleep(CONFIG["DELAY"])

# =========================
# CICLO PRINCIPAL
# =========================
def planning_cycle(controller, step_id=0):
    log(f"--- STEP {step_id} ---")

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
        log("No hay objetos válidos para pickup. Abortando ciclo.")
        return

    # selección estable (siempre el mismo)
    target = candidates[0]
    # log(f"Pickupables detectados: {list(pickupable)[:5]}")

    # if not candidates:
    #     log("No hay objetos válidos para pickup. Abortando ciclo.")
    #     return

    # target = candidates[0]
    goal = f"(holding {target})"

    log(f"Goal seleccionado: {goal}")

    # Reducir estado al objetivo para evitar explosión combinatoria
    predicates = [p for p in predicates if target in p]
    objects = {target}

    # =========================
    # 2. GENERAR PROBLEMA PDDL
    # =========================
    generate_problem(predicates, objects, goal)

    if CONFIG["SAVE_PDDL"]:
        log("Problem PDDL generado")

    # =========================
    # 3. PLANIFICAR
    # =========================
    run_planner()

    if CONFIG["SAVE_PLAN"]:
        log("Plan generado")

    # =========================
    # 🧪 DEBUG PLAN
    # =========================
    with open("plan.txt") as f:
        content = f.read()
        print("\n=== PLAN ===")
        print(content)
        print("============\n")

    # =========================
    # ❌ SI NO HAY PLAN → NO EJECUTAR
    # =========================
    if not content.strip():
        log("Plan vacío. No se ejecuta nada.")
        return

    # =========================
    # 4. EJECUTAR PLAN
    # =========================
    execute_plan(
        controller,
        config={
            "DELAY": CONFIG["DELAY"] if CONFIG["DEMO_MODE"] else 0,
            "VERBOSE": CONFIG["VERBOSE"],
            "FAIL_FAST": False
        }
    )

# =========================
#  MAIN
# =========================
def main():
    controller, camera_id = init_controller()
    log(f"Controlador inicializado con camera_id: {camera_id}")
    
    # Configurar el ID de la cámara en el executor
    set_camera_id(camera_id)

    # acción inicial para obtener estado
    controller.step(action="MoveAhead", moveMagnitude=0.01)

    if CONFIG["REPLAN"]:
        log("Modo REPLAN activado")

        for step in range(CONFIG["MAX_STEPS"]):
            planning_cycle(controller, step)

            # condición de parada simple
            event = controller.last_event
            predicates, _ = extract_state(event)

            if CONFIG["GOAL"] in predicates:
                log("Objetivo alcanzado")
                break

            maybe_sleep()

    else:
        log("Modo ejecución única")

        planning_cycle(controller)

    controller.stop()
    log("Ejecución finalizada")


# =========================
#  ENTRY POINT
# =========================
if __name__ == "__main__":
    main()