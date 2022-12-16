from CustomObject3D import CustomObject3D
from panda3d.core import *
from typing import Tuple, List
from labyrinth import Parallelepiped
from common import *

N_LIGHTS = 3
LIGHT_COLOR = (1, 0.05, 0.5, 1)

class Player(CustomObject3D):
    def __init__(self, model: NodePath, position: Tuple[float, float, float],
                 parent: NodePath, scale: Tuple[float, float, float] = (1, 1, 1),
                 collision: CollisionNode = None, speed: float = 0.0):
        
        super().__init__(model, position, parent, scale, collision, speed)
        self.is_on_ground = False
        self.lights = [self.generate_light() for _ in range(N_LIGHTS)]
    
    def update(self):
        if self.is_on_ground:
                self.velocity[2] = 0
        else:
            self.velocity[2] -= self.gravity
        self.move()

    def generate_light(self):
        pl = PointLight('plight')
        pl.setColor(LIGHT_COLOR)
        pl.setShadowCaster(True, 512, 512)
        light_cube = generateGeometry(Parallelepiped(0.5, 0.5, 0.5, color=LIGHT_COLOR), 'flashlight')
        pn = self.parent.attachNewNode(pl)
        return light_cube, pn

    def put_light(self):
        if len(self.lights) == 0:
            return
        
        light_cube, pn = self.lights.pop()
        pn.attachNewNode(light_cube)
        pn_mult = 5
        pn_position = (self.position[0] + pn_mult * self.scale[0], self.position[1] - pn_mult * self.scale[1]/2, self.position[2])
        pn.setPos(pn_position)
       
        self.parent.setLight(pn)
        
        
            