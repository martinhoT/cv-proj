
from CustomObject3D import CustomObject3D
import random
from panda3d.core import ShadeModelAttrib

MODEL_PATH = 'models/spider/SM_Japanise_Krab.obj'
FLAT_SHADING_CHANCE = 1
SPIDER_SCALE_VARIATION = 0.005

class Spider(CustomObject3D):
    
    SCALE = 0.01
    SPEED = 0.1
    
    def __init__(self, position, parent, game, scale=[.01, .01, .01], movement_axis=(1, 1, 1), wall_dimensions=(1, 1, 1)):
        model = game.loader.loadModel(MODEL_PATH)
        flat_chance = random.random()
        if flat_chance < FLAT_SHADING_CHANCE:
            model.node().setAttrib(ShadeModelAttrib.make(ShadeModelAttrib.MFlat))
        random_scale = random.uniform(-SPIDER_SCALE_VARIATION, SPIDER_SCALE_VARIATION)
        scale = [scale[i] + random_scale for i in range(3)]
        super().__init__(model, position, parent, scale)
        self.gravity = 0
        self.movement_axis = movement_axis
        self.wall_dimensions = wall_dimensions
        
    def update(self):
        # Reset velocity if it is 0
        if self.velocity == [0, 0, 0]:
            self.velocity = [random.uniform(-1, 1) * self.SPEED * self.movement_axis[i] for i in range(3)]
        
        # If the spider is close to the wall, remake movement
        for i in range(len(self.velocity)):
            if abs(self.relative_position[i] + self.velocity[i]) > abs(self.wall_dimensions[i] / 3):
                self.velocity = [0, 0, 0]
                break
        super().update()