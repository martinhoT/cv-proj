
from CustomObject3D import CustomObject3D
import random

MODEL_PATH = 'models/spider/SM_Japanise_Krab.obj'

class Spider(CustomObject3D):
    
    SCALE = 0.01
    SPEED = 0.1
    
    def __init__(self, position, parent, game, scale=(.01, .01, .01), movement_axis=(1, 1, 1)):
        model = game.loader.loadModel(MODEL_PATH)
        super().__init__(model, position, parent, scale)
        self.gravity = 0
        self.movement_axis = movement_axis
    
    def update(self):
        self.velocity = [random.uniform(-1, 1) * self.SPEED * self.movement_axis[i] for i in range(3)]
        super().update()