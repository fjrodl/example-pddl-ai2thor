# AI2-THOR Minimal Example

A complete pipeline for autonomous task planning and execution in the AI2-Thor simulator, integrating:
- **State Extraction**: Extract symbolic state from AI2-Thor events
- **PDDL Planning**: Generate and solve PDDL problems
- **Plan Execution**: Execute PDDL plans in the simulator
- **3D Visualization**: Third-party camera visualization with OpenCV

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🚀 Launchers

### 1. **Main Pipeline** - `run.py`
Complete sense-plan-act loop with optional replanning.

```bash
python run.py
```

**Features:**
- Perception → State extraction
- PDDL problem generation
- Plan execution
- Optional replanning for complex tasks

**Configuration** (in `run.py`):
```python
CONFIG = {
    "GOAL": "(holding mug)",           # Target goal
    "MAX_STEPS": 10,                   # Max replanning iterations
    "DELAY": 1.5,                      # Delay between actions (seconds)
    "DEMO_MODE": True,                 # Slow visualization mode
    "REPLAN": False,                   # Enable replanning loop
    "SAVE_PDDL": True,                 # Save PDDL files
    "SAVE_PLAN": True,                 # Save generated plans
    "VERBOSE": True,                   # Debug output
}
```

---

### 2. **PDDL Testing** - `test_pddl.py`
Fast PDDL planning and execution testing without heavy visualization. Ideal for:
- Iterating on PDDL domain/problem generation
- Quick planning tests
- Debugging state extraction

```bash
python test_pddl.py
```

**Output:**
```
[PDDL_TEST] ✅ Controlador inicializado | Camera ID: None
[PDDL_TEST] Objetos detectados: 76
[PDDL_TEST] Predicados generados: 64
[PDDL_TEST] ✅ Goal seleccionado: (holding apple__00_47__01_15__00_48)
[PLANNER] Plan con 2 acciones generado
((move-to apple__00_47__01_15__00_48))
((pickup apple__00_47__01_15__00_48))
[PDDL_TEST] ✅ Ciclo completado exitosamente
```

---

### 3. **Camera Testing** - `test_camera.py`
Verify third-party camera is working correctly and frames are captured.

```bash
python test_camera.py
```

**Features:**
- Initialize controller with camera support
- Capture 5 test frames
- Display frame info (dtype, shape, min/max values)
- Verify no black frames issue

**Output:**
```
✅ Frame capturado: uint8, shape=(480, 640, 3), min=136, max=255
✅ Frame capturado: uint8, shape=(480, 640, 3), min=128, max=255
```

---

### 3b. **Camera Configuration Tester** - `test_camera_config.py`
Test and adjust camera position, rotation, and FOV interactively.

```bash
python test_camera_config.py
```

**Options:**
1. Top-down view (bird's eye)
2. Isometric view (45° angle)
3. Follow camera (behind agent)
4. Wide vision (large FOV)
5. Close-up (narrow FOV)
6. Overhead angle
7. Custom (define your own values)
8. Test all (cycle through presets)

**Example:** If you see nothing or only black frames, use this tool to find the right camera angle!

See [CAMERA_CONFIG_GUIDE.md](CAMERA_CONFIG_GUIDE.md) for detailed camera parameter explanations.

---

### 4. **Step-by-Step Visualization** - `visualize_steps.py`
Interactive or automated visualization of the AI2-Thor simulator with detailed state inspection.

#### **Interactive Mode** - Manual control
```bash
python visualize_steps.py
```
Choose option 1 or 2 at the prompt:
- **Option 1**: Manual control - Execute predefined actions one at a time with visual feedback
- **Option 2**: PDDL visualization with pauses between steps

#### **Automated Mode** - Full pipeline without pauses
```bash
python visualize_steps.py --auto
```

**Features:**
- Real-time simulator state display (agent position, inventory, nearby objects)
- Extracted PDDL predicates visualization
- Plan generation and display
- Step-by-step plan execution with camera frames
- Automatic frame capture with action metadata overlays
- Saved frames in `frames_output/` directory

**Captured Information Per Step:**
```
📋 STATE PREDICATES:
  (visible apple__00_47__01_15__00_48)
  (pickupable apple__00_47__01_15__00_48)
  ...

🎯 GOAL SELECTED: (holding apple__00_47__01_15__00_48)

PLAN GENERATED:
  ((move-to apple__00_47__01_15__00_48))
  ((pickup apple__00_47__01_15__00_48))
```

**Example Frame Output:**
Each frame shows:
- Step number
- Action name (MoveAhead, PickupObject, etc.)
- Action parameters
- Camera view from simulator
- Saved to: `frames_output/step_0001.jpg`, `step_0002.jpg`, etc.

---

### 5. **Extended Multi-Step Plan Demo** - `demo_extended_plan.py`
**NEW** - Shows a longer, more detailed execution with multiple movement steps

```bash
python demo_extended_plan.py
```

**Features:**
- Interactive walkthrough of the planning pipeline
- Detailed movement visualization (rotation + walk steps)
- Real-time state inspection before/after phases
- Multiple sub-steps during movement execution:
  - **Phase 1**: Object detection → Rotation → Movement (multiple steps)
  - **Phase 2**: Pickup execution
- Better camera angle (isometric) for visibility
- Press ENTER between phases to observe results

**Example Output:**
```
🚀 EXECUTING PLAN WITH DETAILED VISUALIZATION:

🔶 PHASE 1: MOVE TO OBJECT
[ROTATION] ↻ Girando derecha... Ángulo: 45° (sub-step 1)
[MOVEMENT] 🚶 Avanzando 0.2m hacia el objeto... Distancia restante: 2.3m (sub-step 5)
[MOVEMENT] 🚶 Avanzando 0.2m hacia el objeto... Distancia restante: 2.1m (sub-step 6)
[MOVEMENT] 🚶 Avanzando 0.2m hacia el objeto... Distancia restante: 1.8m (sub-step 7)
...
[APPROACH] ✅ ¡Objeto alcanzado! Distancia: 0.45m

🔶 PHASE 2: PICKUP OBJECT
[PICKUP] Attempting to pick up: Apple|-00.47|+01.15|+00.48
✅ SUCCESS! Apple is now in inventory!
```

✅ **This is the launcher to use for a longer, more interesting example!**

---

## 📁 Project Structure

```
ai2-thor/
├── run.py                          # Main pipeline
├── test_pddl.py                    # PDDL testing script
├── test_camera.py                  # Camera verification
├── test_camera_config.py           # Camera angle tester
├── visualize_steps.py              # Step-by-step visualization
├── demo_extended_plan.py           # Extended multi-step demo ⭐ NEW
├── CAMERA_CONFIG_GUIDE.md          # Camera configuration reference
├── config/
│   └── settings.py                 # Configuration (SCENE, WIDTH, HEIGHT)
├── pddl/
│   ├── domain.pddl                 # PDDL domain
│   ├── domain_extended.pddl        # Extended domain (experimental)
│   ├── problem.pddl                # Generated PDDL problem
│   └── problem.pddl.soln           # Solution from planner
├── src/
│   ├── controller/
│   │   └── thor_controller.py      # AI2-Thor controller initialization
│   ├── executor/
│   │   └── plan_executor.py        # Plan execution engine (with detailed movement logging)
│   ├── planner/
│   │   └── planner.py              # PDDL planner interface
│   ├── symbolic/
│   │   ├── state_extractor.py      # State → Predicates
│   │   └── pddl_generator.py       # Predicates → PDDL problem
│   ├── actions/
│   │   └── basic_actions.py        # Basic AI2-Thor actions
│   └── visualization/
│       └── camera.py               # Visualization utilities
├── frames_output/                  # Saved visualization frames
├── requirements.txt
└── README.md
```

---

## 🔄 Workflow

### Quick PDDL Testing
```bash
python test_pddl.py                # Single planning cycle
```

### Verify Camera Setup
```bash
python test_camera.py              # Test camera capture
python test_camera_config.py       # Test different camera angles
```

### Visual Debugging & Demonstrations
```bash
python visualize_steps.py --auto   # Auto watch full pipeline
python demo_extended_plan.py       # Interactive extended demo with multiple steps
```

### Production/Full Replanning
```bash
python run.py                      # Full sense-plan-act loop
```

---

## 🐛 Troubleshooting

### Black Frames in Camera Visualization
✅ **Fixed**: Controller now has `renderThirdPartyCamera=True`

### PDDL Files Not Generated
Check `pddl/` directory and ensure PDDL planner is configured in `src/planner/planner.py`

### Objects Not Detected
Run `test_pddl.py` to verify state extraction is working:
```bash
python test_pddl.py 2>&1 | grep "Predicados generados"
```

---

## 📝 Configuration

Edit `config/settings.py`:
```python
SCENE = "FloorPlan1"    # AI2-Thor scene
WIDTH = 640             # Camera width
HEIGHT = 480            # Camera height
```

---

## 🎯 Next Steps

1. **Test camera**: `python test_camera.py`
2. **Test PDDL pipeline**: `python test_pddl.py`
3. **Visualize execution**: `python visualize_steps.py --auto`
4. **Run full system**: `python run.py` 
