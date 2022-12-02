from panda3d.core import NodePath, CollisionNode
from typing import Tuple, List


class CustomObject3D:

    def __init__(self, model: NodePath, position: Tuple[float, float, float],
                 parent: NodePath, scale: Tuple[float, float, float] = (1, 1, 1),
                 collision: CollisionNode = None):
        self.model = model
        self.position = position
        # self.rotation = rotation
        self.scale = scale
        self.parent = parent

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

    def set_light(self, light):
        self.model.setLight(light)