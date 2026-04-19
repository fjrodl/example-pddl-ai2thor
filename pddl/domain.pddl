(define (domain thor-domain)

    (:requirements :strips)

    (:predicates
        (near ?x)
        (visible ?x)
        (pickupable ?x)
        (holding ?x)
    )

    ;; =========================
    ;; 🚶 NAVEGACIÓN
    ;; =========================
    (:action move-to
        :parameters (?x)
        :precondition (visible ?x)
        :effect (near ?x)
    )

    ;; =========================
    ;; ✋ MANIPULACIÓN
    ;; =========================
    (:action pickup
        :parameters (?x)
        :precondition (and (near ?x) (pickupable ?x))
        :effect (and
            (holding ?x)
            (not (near ?x)) ;; opcional: ya no necesitas estar "near"
        )
    )

)