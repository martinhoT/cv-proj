from CustomObject3D import CustomObject3D
from panda3d.core import NodePath, CollisionNode, LPoint3f
from typing import Tuple, List


class Player(CustomObject3D):
    def __init__(self, model: NodePath, position: Tuple[float, float, float],
                 parent: NodePath, scale: Tuple[float, float, float] = (1, 1, 1),
                 collision: CollisionNode = None, speed: float = 0.0):
        
        super().__init__(model, position, parent, scale, collision, speed)
        self.is_on_ground = False
    
    def update(self):
        if self.is_on_ground:
                self.velocity[2] = 0
        else:
            self.velocity[2] -= self.gravity
        self.move()

            