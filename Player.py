from CustomObject3D import CustomObject3D
from panda3d.core import *
from typing import Generator, Iterable, Tuple, List
from labyrinth import Labyrinth, Parallelepiped
from common import *

N_LIGHTS = 3
LIGHT_COLOR = (1, 0.05, 0.5, 1)
LIGHT_POWER = 20
LIGHT_DISTANCE_THRESHOLD = 10
SHADOW_RESOLUTION = 128

class Player(CustomObject3D):
    
    ROTATION_SPEED = 20
    
    def __init__(self, model: NodePath, position: Tuple[float, float, float],
                 parent: NodePath, scale: Tuple[float, float, float] = (1, 1, 1)):
        
        super().__init__(model, position, parent, scale)
        self.is_on_ground = False
        self.lights = [self.generate_light() for _ in range(N_LIGHTS)]
        self.rotation = 0
    
    def update(self):
        if self.is_on_ground:
                self.velocity[2] = 0
        else:
            self.velocity[2] -= self.gravity
        self.move()
        
        if abs(self.model.getH() - self.rotation) > Player.ROTATION_SPEED:
            if self.model.getH() < self.rotation:
                self.model.setH(self.model.getH() + Player.ROTATION_SPEED)
            elif self.model.getH() > self.rotation:
                self.model.setH(self.model.getH() - Player.ROTATION_SPEED)
        else:
            self.model.setH(self.rotation)

    def generate_light(self):
        pl = PointLight('plight')

        pl.setColor((LIGHT_COLOR[0] * LIGHT_POWER, LIGHT_COLOR[1] * LIGHT_POWER, LIGHT_COLOR[2] * LIGHT_POWER, LIGHT_COLOR[3]))
        pl.setShadowCaster(True, SHADOW_RESOLUTION, SHADOW_RESOLUTION)
        pl.setAttenuation((1, 0, 1))
        light_cube = generateGeometry(Parallelepiped(0.5, 0.5, 0.5, color=LIGHT_COLOR), 'flashlight')
        pn = self.parent.attachNewNode(pl)
        return light_cube, pn

    def put_light(self):
        if len(self.lights) == 0:
            return
        
        light_cube, pn = self.lights.pop()
        pn.attachNewNode(light_cube)
        light_position = (self.position[0], self.position[1], self.position[2] + Labyrinth.DIMS_WALL_HEIGHT / 2)
        pn.setPos(light_position)
       
        for node_to_illuminate in self.get_light_surroundings(distance_threshold=LIGHT_DISTANCE_THRESHOLD):
            node_to_illuminate.setLight(pn)
            node_to_illuminate.show()

    def get_light_surroundings(self, distance_threshold: float) -> Generator[NodePath, None, None]:
        for child in self.parent.children:
            # To make sure that the light only affects objects within the same floor
            # This also assumes the objects to be lit are above the light (the light is on the floor)
            height_difference = child.getZ() - self.model.getZ()
            if self.model.get_distance(child) < distance_threshold and height_difference <= Labyrinth.DIMS_WALL_HEIGHT and height_difference >= -Labyrinth.DIMS_FLOOR_HEIGHT:
                yield child

