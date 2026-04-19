# Cognitive Robotics: PDDL Planning Architecture for Autonomous Task Execution

## Introduction

This document explains how an autonomous robot uses **PDDL (Planning Domain Definition Language)** to understand its environment, plan actions, and execute tasks. We'll walk through the complete pipeline using the **AI2-Thor** simulator as our robotic platform.

**Key Concepts:**
- 🧠 **Symbolic Representation** - Understanding the world as logic facts
- 📋 **Domain Definition** - Describing what actions are possible  
- 🎯 **Problem Definition** - Describing the current state and goal
- 🤖 **Planning** - Finding a sequence of actions to reach the goal
- ⚙️ **Execution** - Carrying out the plan in the real simulator

---

## Part 1: Understanding PDDL - The Language of Robotics

PDDL is a formal language for describing:
1. **What a robot can do** (Domain)
2. **What the world looks like** (Problem)  
3. **What we want to achieve** (Goal)

### 1.1 The Domain File

The **domain** describes the robot's capabilities - what actions it can perform and under what conditions.

**File:** `pddl/domain.pddl`

```pddl
(define (domain thor-domain)
    (:requirements :strips)
    
    (:predicates
        (near ?x)           ;; Is the robot close to object X?
        (visible ?x)        ;; Can the robot see object X?
        (pickupable ?x)     ;; Can the robot pick up X?
        (holding ?x)        ;; Is the robot holding X?
    )
    
    ;; ACTION 1: Navigate to an object
    (:action move-to
        :parameters (?x)
        :precondition (visible ?x)      ;; Can only move to visible objects
        :effect (near ?x)               ;; Result: now near that object
    )
    
    ;; ACTION 2: Pick up an object
    (:action pickup
        :parameters (?x)
        :precondition (and (near ?x) (pickupable ?x))  ;; Must be close AND pickupable
        :effect (holding ?x)                           ;; Result: now holding it
    )
)
```

**What This Tells the Robot:**
- ✅ You can `move-to` any object that is `visible`
- ✅ You can `pick-up` any object that is `near` you AND `pickupable`
- ❌ You cannot move to invisible objects
- ❌ You cannot pick up distant objects

---

## Part 2: Perceiving the World - State Extraction

Before the robot can plan, it must understand **what the world looks like right now**. This happens through perception.

### 2.1 The Perception Pipeline

```
AI2-Thor Simulator Camera Frame
           ↓
    Computer Vision / Object Detection
           ↓
    Extract Object Positions, Visibility, Properties
           ↓
    Generate Symbolic State (Predicates)
           ↓
    PDDL Facts the Planner Can Understand
```

**File:** `src/symbolic/state_extractor.py`

**Example - What the Robot Sees:**

```
SENSOR INPUT (from camera):
- I can see an apple 0.79 meters away
- I can see a book 1.23 meters away
- The apple is not being held by anything
- The book is on a shelf

↓ EXTRACTION ↓

SYMBOLIC STATE (Predicates):
- (visible apple__00_47__01_15__00_48)      ← Apple is visible
- (pickupable apple__00_47__01_15__00_48)   ← Apple can be picked up
- (visible book__00_15__01_10__00_62)       ← Book is visible
- (pickupable book__00_15__01_10__00_62)    ← Book can be picked up
```

### 2.2 Key State Information

The system extracts:

| Predicate Type | Example | Meaning |
|---|---|---|
| **Visibility** | `(visible apple)` | Robot can perceive this object |
| **Reachability** | `(pickupable apple)` | Robot can physically interact with this |
| **Status** | `(holding apple)` | Robot currently holds this |
| **Position** | Agent at (-1.0, 0.9, 1.0) | Where the robot is in 3D space |

---

## Part 3: Creating the Problem - Goal-Directed Planning

Now the robot knows *what it can do* (domain) and *what the world looks like* (state). Next, it needs to know *what we want it to achieve* (goal).

### 3.1 Problem Definition

The **problem** file specifies:
1. The initial state (what's true right now)
2. The goal state (what we want to be true)

**File:** `pddl/problem.pddl`

**Example Problem:**

```pddl
(define (problem pick-apple)
    (:domain thor-domain)
    
    (:objects
        apple__00_47__01_15__00_48     ;; The specific apple object
    )
    
    (:init
        ;; CURRENT STATE: What's true in the world RIGHT NOW
        (visible apple__00_47__01_15__00_48)
        (pickupable apple__00_47__01_15__00_48)
    )
    
    (:goal
        ;; DESIRED STATE: What we want to be true
        (holding apple__00_47__01_15__00_48)
    )
)
```

### 3.2 Problem Creation in Code

**File:** `src/symbolic/pddl_generator.py`

This module automatically creates the problem based on:
1. ✅ Current state extracted from sensors
2. ✅ Goal selected by the system or user
3. ✅ Relevant objects involved

```python
def generate_problem(predicates, objects, goal):
    """
    Creates PDDL problem file automatically
    
    Input:
      - predicates: [(visible apple), (pickupable apple), ...]
      - objects: {apple__00_47__01_15__00_48}
      - goal: (holding apple__00_47__01_15__00_48)
    
    Output:
      - Writes pddl/problem.pddl with all the information
    """
```

---

## Part 4: Goal Selection Strategy

How does the robot decide *what* to pick up?

### 4.1 The Goal Selection Algorithm

Looking at `run.py`:

```python
def planning_cycle(controller, step_id=0):
    # 1. PERCEPTION - Extract current state
    event = controller.last_event
    predicates, objects = extract_state(event)
    
    # 2. IDENTIFY VALID TARGETS
    visible = set()
    pickupable = set()
    
    for p in predicates:
        if p.startswith("(visible"):
            visible.add(object_from_predicate)
        if p.startswith("(pickupable"):
            pickupable.add(object_from_predicate)
    
    # 3. FILTER INVALID OBJECTS (containers, furniture)
    candidates = sorted([
        obj for obj in (visible & pickupable)
        if not any(x in obj for x in ["fridge", "cabinet", "sink", "table"])
    ])
    
    # 4. SELECT GOAL
    target = candidates[0]  # Pick the first valid target
    goal = f"(holding {target})"
```

**Selection Logic:**

```
All Objects
    ↓
Filter: Visible AND Pickupable
    ↓
Filter: NOT (Furniture/Containers)
    ↓
Sorted Candidates
    ↓
Select First → GOAL
```

**Example:**
- Visible objects: 10
- Visible + Pickupable: 8  
- After filtering containers: 7
- **Selected goal:** `(holding apple__00_47__01_15__00_48)`

---

## Part 5: Planning - Finding the Solution

Now we have:
- ✅ Domain (what the robot can do)
- ✅ Problem (current state + goal)

The **planner** finds a sequence of actions!

### 5.1 The Planning Process

**File:** `src/planner/planner.py`

```python
def run_planner():
    """
    Calls external PDDL planner (e.g., FF, FastForward)
    
    Input:
      - pddl/domain.pddl (robot capabilities)
      - pddl/problem.pddl (current state + goal)
    
    Output:
      - plan.txt (sequence of actions)
    """
```

### 5.2 Example Plan Output

**Starting State:**
```
- Robot position: (-1.0, 0.9, 1.0)
- Can see apple at 0.79m away
- Not holding anything
```

**Goal:**
```
- Robot holding apple
```

**Generated Plan:**
```
1. (move-to apple__00_47__01_15__00_48)
   ├─ Precondition: apple is visible ✅
   └─ Effect: robot is now near apple
   
2. (pickup apple__00_47__01_15__00_48)
   ├─ Precondition: robot is near apple ✅
   ├─ Precondition: apple is pickupable ✅
   └─ Effect: robot is holding apple ✓ GOAL ACHIEVED!
```

### 5.3 Planning Complexity

The planner searches through possible action sequences:

```
State 0: (visible apple)
  |
  ├─ Try action: move-to apple
  │  State 1: (near apple)
  │    |
  │    ├─ Try action: pickup apple
  │    │  State 2: (holding apple) ✓ GOAL FOUND!
  │    │
  │    └─ Try action: ...
  │
  └─ Try action: ...
```

---

## Part 6: Execution - Making the Plan Real

The plan is just a list of abstract actions. Now the robot must **execute** them in the simulator.

### 6.1 The Execution Pipeline

**File:** `src/executor/plan_executor.py`

```
Abstract Plan
    ↓
(move-to apple)  →  [ROTATION: 13 steps] → [WALK FORWARD] → [APPROACH]
(pickup apple)   →  [GRASP ACTION]
    ↓
Concrete Robot Actions
    ↓
AI2-Thor Simulator Updates
    ↓
New Camera Frames
    ↓
Execution Verification
```

### 6.2 Example Execution - Move to Apple

When the planner says `(move-to apple)`, the executor breaks it into detailed steps:

**Step 1: Locate Target**
```
Initial state: Robot at (-1.0, 0.9, 1.0), facing 270°
Look for apple: Found at bearing 224° away
```

**Step 2: Rotate to Face Target**
```
Sub-step 1: Rotate left 10° → facing 260°
Sub-step 2: Rotate left 10° → facing 250°
...
Sub-step 13: Rotate left 10° → facing 0° (facing apple)
VISUALLY: Watch the camera rotate around the apple
```

**Step 3: Walk Forward**
```
Sub-step 14: Move forward 0.2m → distance to apple: 0.6m
Sub-step 15: Approached close enough → DONE
VISUALLY: Watch the apple get larger in the camera
```

### 6.3 Execution Logging

At each sub-step, the system outputs:

```
[ROTATION] ↻ Girando izquierda... Ángulo: 224° (sub-step 0)
[ROTATION] ↻ Girando izquierda... Ángulo: 234° (sub-step 1)
[MOVEMENT] 🚶 Avanzando 0.2m hacia el objeto... Distancia restante: 0.79m (sub-step 14)
[APPROACH] ✅ ¡Objeto alcanzado! Distancia: 0.47m
```

Each sub-step captures a camera frame showing the action!

---

## Part 7: Complete Architecture Overview

### 7.1 The Full Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    COGNITIVE ROBOTICS PIPELINE                  │
└─────────────────────────────────────────────────────────────────┘

1. PERCEPTION PHASE
   ├─ Camera: Capture view of environment
   ├─ Vision: Detect objects, positions, properties
   └─ Extraction: Convert to symbolic state (predicates)

2. REPRESENTATION PHASE
   ├─ Domain: Define robot capabilities (actions, preconditions)
   ├─ State: Represent current world as logic facts
   └─ Goal: Define desired state

3. PLANNING PHASE
   ├─ Input: Domain + Problem
   ├─ Process: Search for action sequence
   └─ Output: Plan (sequence of abstract actions)

4. EXECUTION PHASE
   ├─ Parse: Convert abstract actions to concrete commands
   ├─ Control: Send commands to robot/simulator
   ├─ Monitor: Track progress with camera feedback
   └─ Adapt: Adjust if something goes wrong

5. PERCEPTION VERIFICATION
   ├─ New state captured after execution
   ├─ Compare with expected state
   └─ Verify goal was achieved
```

### 7.2 Architecture Diagram

```
World State → Perception → Symbolic State
    ↑                           ↓
    │                    Planning Problem
    │                      (Domain + State)
    │                           ↓
    │                      PDDL Planner
    │                           ↓
    │                          Plan
    │                           ↓
    └─ Execution Engine → Robot Actions
         (run.py) ← Controller Commands
                       ↓
                 AI2-Thor Simulator
                       ↓
                  New World State
```

---

## Part 8: From Theory to Practice

### 8.1 Running the Full System

**File:** `run.py` - Complete cognitive robotics pipeline

```bash
python run.py
```

**What Happens:**

```
STEP 0: PERCEPTION
─────────────────
  Agent Position: (-1.00, 0.90, 1.00)
  Rotation: 270.0°
  
  Closest Objects:
  1. CreditCard|-00.46|+01.10|+00.87 | 0.59m | Hidden
  2. Apple|-00.47|+01.15|+00.48      | 0.79m | Hidden
  3. Cabinet|-01.55|+00.50|+00.38    | 0.92m | Hidden

STEP 1: STATE EXTRACTION
────────────────────────
  ✅ Objects detected: 76
  ✅ Predicates generated: 64
  ✅ (visible apple__00_47__01_15__00_48)
  ✅ (pickupable apple__00_47__01_15__00_48)

STEP 2: GOAL SELECTION
──────────────────────
  🎯 Goal selected: (holding apple__00_47__01_15__00_48)
  Available targets: 30 valid objects

STEP 3: PROBLEM GENERATION
──────────────────────────
  🔄 Generating PDDL problem...
  ✅ Problem PDDL generated

STEP 4: PLANNING
────────────────
  🔄 Running planner...
  [PLANNER] Plan con 2 acciones generado

  Generated Plan:
  1. ((move-to apple__00_47__01_15__00_48))
  2. ((pickup apple__00_47__01_15__00_48))

STEP 5: EXECUTION
─────────────────
  [ROTATION] ↻ Girando izquierda... Ángulo: 224° (sub-step 0)
  [ROTATION] ↻ Girando izquierda... Ángulo: 234° (sub-step 1)
  ...
  [MOVEMENT] 🚶 Avanzando 0.2m hacia el objeto... Distancia restante: 0.79m
  [APPROACH] ✅ ¡Objeto alcanzado! Distancia: 0.47m

STEP 6: VERIFICATION
────────────────────
  Agent Position: (-0.75, 0.90, 0.75)    ← Moved!
  Apple visibility: ✅ Visible
  Apple distance: 0.64m                  ← Closer!

FINAL STATE:
────────────
  ✅ GOAL ACHIEVED - Plan successful!
```

---

## Part 9: Key Concepts for Students

### 9.1 Why PDDL?

**Problem:** Robots need to understand tasks symbolically
**Solution:** PDDL provides a standard, formal language

**Benefits:**
- ✅ General: Works for any domain
- ✅ Automated: Computer finds solutions
- ✅ Optimal: Finds shortest plans
- ✅ Verifiable: Can prove correctness

### 9.2 The Grounding Problem

How does `(visible apple)` become `(visible apple__00_47__01_15__00_48)`?

```
Abstract Level:          Can we see apple?
                         ↓ (symbolic)
                         
Instance Level:          Can we see apple__00_47__01_15__00_48?
                         Which apple at coordinates (-0.47, 1.15, 0.48)?
                         ↓ (concrete)
                         
Sensor Level:            Detect object in camera frame
                         Estimate 3D position from vision
                         ↓ (perception)
```

### 9.3 The Execution Challenge

Abstract plan vs. real execution:

| Abstract | Concrete | Reality |
|----------|----------|---------|
| `move-to apple` | 10° rotate, walk 0.2m | Must avoid obstacles, adjust for friction |
| `pickup apple` | Execute grasp | Handle object deformation, slipping |

The executor handles these abstraction gaps!

---

## Part 10: Extending the System

### 10.1 More Complex Domains

Current domain: Simple pickup task

**Possible extensions:**
1. **Constraints:** "Pick up apple but not if holder is fragile"
2. **Preconditions:** "Must be near table to put down object"
3. **Temporal:** "Complete task within 5 minutes"
4. **Preferences:** "Prefer soft objects to hard"

Example extended domain definition:

```pddl
(:action put-down
    :parameters (?x ?y)
    :precondition (and 
        (holding ?x)      ;; Must be holding it
        (near ?y)         ;; Must be near surface
        (surface ?y)      ;; Surface must exist
    )
    :effect (and
        (not (holding ?x))
        (on ?x ?y)        ;; Object now on surface
    )
)
```

### 10.2 Better Perception

Current: Binary predicates (visible, pickupable)

**Improvements:**
- Numerical: `(distance apple 0.79)` - exact distance
- Fuzzy: `(nearby apple)` instead of exact positions
- Temporal: `(visible-for-next-5-seconds apple)`
- Probabilistic: `(probably-pickupable apple 0.9)`

---

## Part 11: Summary - The Complete Cycle

### 11.1 The Cognitive Loop

```
         ┌─────────────────┐
         │  Perception     │ ← What do we see?
         │  (Sensors)      │
         └────────┬────────┘
                  ↓
         ┌─────────────────┐
         │  Representation │ ← How do we model it?
         │  (Symbolic)     │
         └────────┬────────┘
                  ↓
         ┌─────────────────┐
         │  Planning       │ ← What should we do?
         │  (Search)       │
         └────────┬────────┘
                  ↓
         ┌─────────────────┐
         │  Execution      │ ← How do we do it?
         │  (Control)      │
         └────────┬────────┘
                  ↓
         ┌─────────────────┐
         │  Action Effect  │ ← Did it work?
         │  (New state)    │
         └────────┬────────┘
                  │
                  └→ Loop back to Perception
```

### 11.2 Real World Applications

This pipeline is used in:
- 🏭 Industrial robots picking objects
- 🏠 Home robots (vacuuming, organizing)
- 🔬 Laboratory automation
- 🤖 Autonomous vehicles (traffic scenarios)

---

## Part 12: Hands-On Exercise

### 12.1 Try It Yourself

**Step 1: Run basic pipeline**
```bash
python run.py
```
Observe: Perception → Planning → Execution

**Step 2: Test extended visualization**
```bash
python demo_extended_plan.py
```
Observe: Detailed sub-steps with camera frames

**Step 3: Modify domain**
Edit `pddl/domain.pddl` and add:
```pddl
(:action look-at
    :parameters (?x)
    :precondition (near ?x)
    :effect (visible ?x)
)
```
See how planner uses new action.

**Step 4: Change goal**
In `run.py`, modify:
```python
CONFIG = {
    "GOAL": "(holding mug)",  # Change this to something else
}
```

---

## Conclusion

This architecture demonstrates **cognitive robotics** principles:

1. **Perception** - Extract symbolic facts from sensory data
2. **Representation** - Use formal languages (PDDL) for reasoning
3. **Planning** - Automatically find action sequences
4. **Execution** - Ground abstract plans in reality
5. **Feedback** - Verify results and adapt

The key insight: **Robots don't just follow hardcoded sequences. They reason about what's needed, plan autonomously, and adapt to new situations.**

---

## References and Further Reading

- **PDDL Tutorial:** Introduction to Hierarchical Task Network Planning
- **AI2-Thor Documentation:** Interactive 3D Environments for AI Learning
- **Planning Algorithms:** Automated Planning Theory and Practice
- **Related Files in Project:**
  - `pddl/domain.pddl` - Domain definition
  - `src/symbolic/state_extractor.py` - Perception
  - `src/symbolic/pddl_generator.py` - Problem generation
  - `src/planner/planner.py` - Planning interface
  - `src/executor/plan_executor.py` - Execution engine
  - `run.py` - Complete pipeline demo

---

**By understanding this architecture, you now know how autonomous robots think! 🤖**
