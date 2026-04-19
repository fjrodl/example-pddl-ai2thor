(define (domain thor-domain-extended)

    (:requirements :strips)

    (:predicates
        (at-location ?pos) ;; Current agent location
        (visible ?x) ;; Object is visible
        (nearby ?x) ;; Object is close
        (pickupable ?x) ;; Object can be picked up
        (holding ?x) ;; Agent holding object
        (facing-direction ?dir) ;; Which direction facing
        (agent-ready) ;; Ready to act
    )

    ;; =========================
    ;; 🔍 PERCEPTION
    ;; =========================
    (:action look-for-object
        :parameters (?x)
        :precondition (visible ?x)
        :effect (nearby ?x)
    )

    ;; =========================
    ;; 🔄 ROTATION/TURNING
    ;; =========================
    (:action rotate-to-target
        :parameters (?x)
        :precondition (nearby ?x)
        :effect (facing-direction ?x)
    )

    ;; =========================
    ;; 🚶 MOVEMENT STEPS
    ;; =========================
    (:action walk-step-1
        :parameters (?x)
        :precondition (and (facing-direction ?x) (visible ?x))
        :effect (at-location ?x)
    )

    (:action walk-step-2
        :parameters (?x)
        :precondition (and (at-location ?x) (visible ?x))
        :effect (nearby ?x)
    )

    ;; =========================
    ;; ✋ PICKUP/MANIPULATION
    ;; =========================
    (:action approach
        :parameters (?x)
        :precondition (nearby ?x)
        :effect (agent-ready)
    )

    (:action pickup
        :parameters (?x)
        :precondition (and (agent-ready) (pickupable ?x) (nearby ?x))
        :effect (and
            (holding ?x)
            (not (nearby ?x))
            (not (agent-ready))
        )
    )

)