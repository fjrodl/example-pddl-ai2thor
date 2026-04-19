def generate_problem(predicates, objects, goal, path="pddl/problem.pddl"):
    with open(path, "w") as f:
        f.write("(define (problem thor-problem)\n")
        f.write("  (:domain thor-domain)\n")

        #  OBJETOS DINÁMICOS
        f.write("  (:objects\n")
        for obj in sorted(objects):
            f.write(f"    {obj}\n")
        f.write("  )\n")

        # estado inicial
        f.write("  (:init\n")
        for p in predicates:
            f.write(f"    {p}\n")
        f.write("  )\n")

        # objetivo
        f.write(f"  (:goal {goal})\n")
        f.write(")\n")