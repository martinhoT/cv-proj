from panda3d.core import NodePath, LPoint3f, ShadeModelAttrib
from typing import Tuple, Generator

GRAVITY = 0.01

class CustomObject3D:
    
    SHADOW_RESOLUTION = 32

    def __init__(self, model: NodePath, position: Tuple[float, float, float],
                 parent: NodePath, scale: Tuple[float, float, float] = (1, 1, 1),
                 is_flat: bool = False, emmits_light: bool = False, light_color: Tuple[float, float, float] = None,
                 light_color_temperature: float = None, light_distance_threshold: float = 0):

        self.model = model
        self.position = position
        self.relative_position = [0, 0, 0]
        self.scale = scale
        self.parent = parent
        self.velocity = [0, 0, 0]
        self.gravity = GRAVITY
        self.model.reparentTo(parent)
        # Apply scale and position transforms on the model
        self.set_scale(*scale)
        self.set_pos(*position)
        self.pn = None
        if is_flat:
            self.model.node().setAttrib(ShadeModelAttrib.make(ShadeModelAttrib.MFlat))
        
    def set_scale(self, scale_x, scale_y, scale_z):
        self.model.setScale(scale_x, scale_y, scale_z)
        self.scale = (scale_x, scale_y, scale_z)

    def set_pos(self, pos_x, pos_y, pos_z):
        self.model.setPos(pos_x, pos_y, pos_z)
        self.position = (pos_x, pos_y, pos_z)
    
    def move(self):
        offset = self.velocity
        new_pos = self.model.getPos() + LPoint3f(*offset)
        self.model.setPos(new_pos)
        self.position = self.model.getPos()
        self.relative_position = [self.relative_position[i] + offset[i] for i in range(3)]
        if self.pn is not None:
            self.pn.setPos(self.model.getPos())

    def update(self):
        self.move()
        self.velocity[2] -= self.gravity

    def set_light(self, light):
        self.model.setLight(light)
    
    def get_light_surroundings(self, distance_threshold: float) -> Generator[NodePath, None, None]:
        for child in self.parent.children:
            # To make sure that the light only affects objects within the same floor
            # This also assumes the objects to be lit are above the light (the light is on the floor)
            if self.model.get_distance(child) < distance_threshold:
                yield child