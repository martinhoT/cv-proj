from CustomObject3D import CustomObject3D
from panda3d.core import *
from typing import Tuple, List
from labyrinth import Parallelepiped
from common import *


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


    def create_light(self):
        pl = PointLight('plight')
        pl_color = (.5, .5, 1, 1)
        pl.setColor(pl_color)
                
        pn = self.parent.attachNewNode(pl)
        pn_mult = 5
        pn_position = (self.position[0] + pn_mult * self.scale[0], self.position[1] - pn_mult * self.scale[1]/2, self.position[2])
        pn.setPos(pn_position)
        
        light_cube = generateGeometry(Parallelepiped(0.5, 0.5, 0.5, color=pl_color), 'flashlight')
        pn.attachNewNode(light_cube)
        
        self.parent.setLight(pn)
        
        
            