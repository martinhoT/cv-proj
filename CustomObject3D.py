from panda3d.core import NodePath, CollisionNode, LPoint3f
from typing import Tuple, List


GRAVITY = 0.01

class CustomObject3D:

    def __init__(self, model: NodePath, position: Tuple[float, float, float],
                 parent: NodePath, scale: Tuple[float, float, float] = (1, 1, 1),
                 collision: CollisionNode = None, speed: float = 0.0):
        self.model = model
        self.position = position
        # self.rotation = rotation
        self.scale = scale
        self.parent = parent
        self.speed = speed
        self.velocity = [0, 0, 0]
        self.gravity = GRAVITY
        self.model.reparentTo(parent)
        # Apply scale and position transforms on the model
        self.set_scale(*scale)
        self.set_pos(*position)

    def set_scale(self, scale_x, scale_y, scale_z):
        self.model.setScale(scale_x, scale_y, scale_z)
        self.scale = (scale_x, scale_y, scale_z)

    def set_pos(self, pos_x, pos_y, pos_z):
        self.model.setPos(pos_x, pos_y, pos_z)
        self.position = (pos_x, pos_y, pos_z)
    
    def move(self):
        # offset = (pos_x * self.speed, pos_y * self.speed, pos_z * self.speed)
        offset = self.velocity
        new_pos = self.model.getPos() + LPoint3f(*offset)
        self.model.setPos(new_pos)
        self.position = self.model.getPos()

    def update(self):
        self.move()
        self.velocity[2] -= self.gravity

    def set_light(self, light):
        self.model.setLight(light)