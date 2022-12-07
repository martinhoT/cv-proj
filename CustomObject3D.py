from panda3d.core import NodePath, CollisionNode, LPoint3f
from typing import Tuple, List


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
    
    def move(self, pos_x, pos_y, pos_z):
        print(f"{self.model.getPos() =}")
        # pos = (self.model.getPos()[0], self.model.getPos()[1], self.model.getPos()[2])
        offset = (pos_x * self.speed, pos_y * self.speed, pos_z * self.speed)
        print(f"{offset =}")
        new_pos = self.model.getPos() + LPoint3f(*offset)
        print(f"{new_pos =}")
        self.model.setPos(new_pos)
        self.position = self.model.getPos()


    def set_light(self, light):
        self.model.setLight(light)