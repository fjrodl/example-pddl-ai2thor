import time
import os
import cv2

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
# VISUALIZACIÓN DE ESTADO
# =========================
def print_state_info(event, title=""):
    """Display detailed state information with camera view"""
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
    )[:5]  # Show 5 closest
    
    print(f"\n🔍 Closest Objects:")
    for i, obj in enumerate(objects, 1):
        dist = obj.get('distance', 'N/A')
        visible = "✅ Visible" if obj.get('visible') else "❌ Hidden"
        print(f"   {i}. {obj['objectId'][:35]:35} | {dist:>5.2f}m | {visible}")
    
    print(f"{'='*70}\n")

# =========================
# CICLO PRINCIPAL
# =========================
def planning_cycle(controller, step_id=0):
    log(f"\n--- PLANNING CYCLE {step_id} ---\n")

    # 1. PERCEPCIÓN
    event = controller.last_event
    print_state_info(event, "INITIAL STATE - Analyzing environment")
    
    predicates, objects = extract_state(event)

    log(f"✅ Objetos detectados: {len(objects)}")
    log(f"✅ Predicados generados: {len(predicates)}")

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
        return

    # selección estable (siempre el mismo)
    target = candidates[0]
    goal = f"(holding {target})"

    print(f"\n🎯 GOAL SELECTED: {goal}")
    print(f"   Available targets: {len(candidates)} valid objects")
    log(f"✅ Goal seleccionado: {goal}")

    # Reducir estado al objetivo para evitar explosión combinatoria
    predicates = [p for p in predicates if target in p]
    objects = {target}

    # =========================
    # 2. GENERAR PROBLEMA PDDL
    # =========================
    log("\n🔄 Generating PDDL problem...")
    generate_problem(predicates, objects, goal)

    if CONFIG["SAVE_PDDL"]:
        log("✅ Problem PDDL generado")

    # =========================
    # 3. PLANIFICAR
    # =========================
    log("\n🔄 Running planner...")
    run_planner()

    if CONFIG["SAVE_PLAN"]:
        log("✅ Plan generado")

    # =========================
    # 🧪 DEBUG PLAN
    # =========================
    with open("plan.txt") as f:
        content = f.read()
        print("\n" + "="*70)
        print("📋 GENERATED PLAN:")
        print("="*70)
        for i, line in enumerate(content.strip().split('\n'), 1):
            print(f"  {i}. {line}")
        print("="*70)

    # =========================
    # ❌ SI NO HAY PLAN → NO EJECUTAR
    # =========================
    if not content.strip():
        log("❌ Plan vacío. No se ejecuta nada.")
        return

    # =========================
    # 4. EJECUTAR PLAN
    # =========================
    print(f"\n🚀 Executing plan...\n")
    execute_plan(
        controller,
        config={
            "DELAY": CONFIG["DELAY"] if CONFIG["DEMO_MODE"] else 0.1,
            "VERBOSE": CONFIG["VERBOSE"],
            "FAIL_FAST": False
        }
    )
    
    # Show final state
    event = controller.last_event
    print_state_info(event, "FINAL STATE - After plan execution")

# =========================
#  MAIN
# =========================
def main():
    print("\n" + "="*70)
    print("🤖 AI2-THOR PDDL PLANNING PIPELINE - MAIN EXECUTION")
    print("="*70)
    
    controller, camera_id = init_controller()
    log(f"✅ Controlador inicializado")
    log(f"   Camera angle: Isometric (position: 2,2,2 | rotation: 45°,225°,0°)")
    log(f"   Camera ID: {camera_id}")
    
    # Configurar el ID de la cámara en el executor
    set_camera_id(camera_id)

    # acción inicial para obtener estado
    for _ in range(5):
        controller.step(action="Pass")

    if CONFIG["REPLAN"]:
        log("\n🔄 REPLAN MODE - Sense-Plan-Act loop")

        for step in range(CONFIG["MAX_STEPS"]):
            planning_cycle(controller, step)

            # condición de parada simple
            event = controller.last_event
            predicates, _ = extract_state(event)

            if CONFIG["GOAL"] in predicates:
                print(f"\n{'='*70}")
                print("✅ GOAL ACHIEVED!")
                print(f"{'='*70}\n")
                log("Objetivo alcanzado")
                break

            maybe_sleep()

    else:
        log("\n📋 SINGLE EXECUTION MODE - Run one planning cycle")
        planning_cycle(controller)

    controller.stop()
    print(f"\n{'='*70}")
    print("🛑 EXECUTION FINISHED")
    print(f"{'='*70}\n")
    log("Ejecución finalizada")


# =========================
#  ENTRY POINT
# =========================
if __name__ == "__main__":
    main()