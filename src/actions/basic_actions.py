def move_ahead(controller):
    return controller.step(action="MoveAhead")

def rotate_right(controller):
    return controller.step(action="RotateRight")

def rotate_left(controller):
    return controller.step(action="RotateLeft")