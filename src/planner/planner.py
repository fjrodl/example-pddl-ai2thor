import subprocess


DEFAULT_CONFIG = {
    "PLANNER_CMD": "pyperplan",
    "DOMAIN": "pddl/domain.pddl",
    "PROBLEM": "pddl/problem.pddl",
    "OUTPUT_PLAN": "plan.txt",
    "LOG_LEVEL": "error",   # evita logs innecesarios
    "VERBOSE": True
}


def log(msg, verbose=True):
    if verbose:
        print(f"[PLANNER] {msg}")

def run_planner():
    from pyperplan.pddl.parser import Parser
    from pyperplan.planner import _ground, _search
    from pyperplan.search import breadth_first_search

    domain_file = "pddl/domain.pddl"
    problem_file = "pddl/problem.pddl"

    # Parseo
    parser = Parser(domain_file, problem_file)
    domain = parser.parse_domain()
    problem = parser.parse_problem(domain)

    # Grounding
    task = _ground(problem)

    # Búsqueda
    solution = breadth_first_search(task)

    # Guardar plan
    plan_lines = []
    if solution is not None:
        for op in solution:
            action = f"({op.name})"
            plan_lines.append(action)

    # escribir plan.txt
    with open("plan.txt", "w") as f:
        for line in plan_lines:
            f.write(line + "\n")

    if plan_lines:
        print(f"[PLANNER] Plan con {len(plan_lines)} acciones generado")
    else:
        print("[PLANNER] No se encontró plan válido")

    return plan_lines
