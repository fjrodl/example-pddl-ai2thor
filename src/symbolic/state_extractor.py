import re

# =========================
# ⚙️ CONFIGURACIÓN
# =========================
DEFAULT_CONFIG = {
    "ONLY_VISIBLE": False,        # si True → solo incluye objetos visibles
    "INCLUDE_PICKUPABLE": True,   # incluir predicado pickupable
    "INCLUDE_VISIBLE": True,      # incluir predicado visible
    "INCLUDE_HOLDING": True,      # incluir predicado holding
    "NORMALIZE_NAMES": True,      # limpiar nombres para PDDL
    "VERBOSE": False,
    "INCLUDE_NEAR": True,
"NEAR_THRESHOLD": 0.5,
}


# =========================
# 🧠 UTILIDADES
# =========================
def normalize(name):
    return re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())


def log(msg, config):
    if config.get("VERBOSE", False):
        print(f"[STATE] {msg}")


# =========================
# 🔍 EXTRACTOR PRINCIPAL
# =========================
def extract_state(event, config=None):
    if config is None:
        config = DEFAULT_CONFIG

    objects = event.metadata["objects"]

    predicates = []
    object_names = set()

    for obj in objects:

        # -------------------------
        # 🧾 NOMBRE
        # -------------------------
        raw_name = obj["objectId"]
        name = normalize(raw_name) if config["NORMALIZE_NAMES"] else raw_name

        # -------------------------
        # 👁️ FILTRADO
        # -------------------------
        if config["ONLY_VISIBLE"] and not obj["visible"]:
            continue

        object_names.add(name)

        # -------------------------
        # 👁️ VISIBLE
        # -------------------------
        if config["INCLUDE_VISIBLE"] and (obj["visible"] or obj["pickupable"]):
            predicates.append(f"(visible {name})")

        # -------------------------
        # ✋ PICKUPABLE (SIEMPRE independiente de visible)
        # -------------------------
        if config["INCLUDE_PICKUPABLE"] and obj["pickupable"]:
            predicates.append(f"(pickupable {name})")

        # -------------------------
        # 📏 NEAR (distancia)
        # -------------------------
        if config.get("INCLUDE_NEAR", False):
            dist = obj.get("distance", None)

            if (
                obj.get("visible", False)
                and dist is not None
                and dist < config.get("NEAR_THRESHOLD", 1.0)
            ):
                predicates.append(f"(near {name})")

        # -------------------------
        # 🧲 HOLDING
        # -------------------------
        if config["INCLUDE_HOLDING"] and obj["isPickedUp"]:
            predicates.append(f"(holding {name})")

    log(f"Objetos finales: {len(object_names)}", config)
    log(f"Predicados finales: {len(predicates)}", config)

    return predicates, object_names