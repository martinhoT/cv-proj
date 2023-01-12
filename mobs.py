from CustomObject3D import CustomObject3D
from panda3d.core import NodePath, PointLight
from typing import Generator
import math
import random

class Bird(CustomObject3D):
    
    ROTATION_SPEED = 40
    MODEL_PATH = 'models/bird/MN64-Eagle/MN64-Eagle.obj'
    
    def __init__(self, position, parent, game, scale=[1, 1, 1], rotation_center=(15, 10, 20), 
                 distance_from_center=20):
        model = game.loader.loadModel(Bird.MODEL_PATH)
        super().__init__(model, position, parent, scale)
        self.gravity = 0
        self.distance_from_center = distance_from_center
        self.rotation_center = rotation_center
        self.model.setP(90)
    
    def update(self, time):
        angleDegrees = time * self.ROTATION_SPEED
        angleRadians = angleDegrees * (math.pi / 180.0)
        
        self.model.setPos(
            (self.distance_from_center) * math.sin(angleRadians) + self.rotation_center[0],
            -(self.distance_from_center) * math.cos(angleRadians) + self.rotation_center[1],
            self.rotation_center[2]
        )
        
        self.model.setH(angleDegrees + 90)

class Spider(CustomObject3D):
    
    SCALE = 0.01
    SPEED = 0.1
    MODEL_PATH = 'models/spider/SM_Japanise_Krab.obj'
    FLAT_SHADING_CHANCE = 0
    SPIDER_SCALE_VARIATION = 0.005
    
    def __init__(self, position, parent, game, scale=[.01, .01, .01], movement_axis=(1, 1, 1), wall_dimensions=(1, 1, 1)):
        model = game.loader.loadModel(Spider.MODEL_PATH)
        flat_chance = random.random()
        is_flat = flat_chance < Spider.FLAT_SHADING_CHANCE
        random_scale = random.uniform(-Spider.SPIDER_SCALE_VARIATION, Spider.SPIDER_SCALE_VARIATION)
        scale = [scale[i] + random_scale for i in range(3)]
        super().__init__(model, position, parent, scale, is_flat=is_flat)
        self.gravity = 0
        self.movement_axis = movement_axis
        self.wall_dimensions = wall_dimensions
        
    def update(self):
        # Reset velocity if it is 0
        if self.velocity == [0, 0, 0]:
            self.velocity = [random.uniform(-1, 1) * self.SPEED * self.movement_axis[i] for i in range(3)]
        
        # If the spider is close to the wall, remake movement
        for i in range(len(self.velocity)):
            if abs(self.relative_position[i] + self.velocity[i]) > abs(self.wall_dimensions[i] / 4):
                self.velocity = [0, 0, 0]
                break
        super().update()


class Firefly(CustomObject3D):
    
    MODEL_PATH = "models/firefly/obj/firefly.obj"
    LIGHT_COLOR = 6500
    LIGHT_DISTANCE_THRESHOLD = 12
    ROTATION_SPEED = 20
    
    
    def __init__(self, position, parent, game, scale=[1, 1, 1], distance_from_center=100, 
                 rotation_center=[15, 10, -40]):
        model = game.loader.loadModel(Firefly.MODEL_PATH)
        super().__init__(model, position, parent, scale, emmits_light=True, 
                         light_color_temperature=Firefly.LIGHT_COLOR, light_distance_threshold=Firefly.LIGHT_DISTANCE_THRESHOLD)
        self.gravity = 0
        self.velocity = [0, 0, 0]
        self.distance_from_center = distance_from_center
        self.rotation_center = rotation_center
        self.model.setP(90)
        
        pl = PointLight('pl')
        pl.setColorTemperature(Firefly.LIGHT_COLOR)
        pl.setShadowCaster(True, CustomObject3D.SHADOW_RESOLUTION, CustomObject3D.SHADOW_RESOLUTION)
        self.pn = self.parent.attachNewNode(pl)
        self.pn.setPos(self.model.getPos())
        
        if Firefly.LIGHT_DISTANCE_THRESHOLD > 0:
            for node_to_illuminate in self.get_light_surroundings(distance_threshold=Firefly.LIGHT_DISTANCE_THRESHOLD):
                node_to_illuminate.setLight(self.pn)
                node_to_illuminate.show()
        else:
            self.parent.setLight(self.pn)
    
    
    def update(self, time):
        angleDegrees = time * Firefly.ROTATION_SPEED
        angleRadians = angleDegrees * (math.pi / 180.0)
        
        self.model.setPos(
            (self.distance_from_center) * math.sin(angleRadians) + self.rotation_center[0],
            -(self.distance_from_center) * math.cos(angleRadians) + self.rotation_center[1],
            self.rotation_center[2]
        )
        self.pn.setPos(self.model.getPos())
        self.model.setH(angleDegrees + 90)
        
        for node_to_illuminate in self.get_light_surroundings(distance_threshold=Firefly.LIGHT_DISTANCE_THRESHOLD):
            node_to_illuminate.setLight(self.pn)
            node_to_illuminate.show()
        
    
    def get_light_surroundings(self, distance_threshold: float) -> Generator[NodePath, None, None]:
        for child in self.parent.children:
            # To make sure that the light only affects objects within the same floor
            # This also assumes the objects to be lit are above the light (the light is on the floor)
            if "grass" in child.name or self.model.get_distance(child) < distance_threshold:
                yield child
    

