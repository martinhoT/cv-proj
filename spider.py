
from CustomObject3D import CustomObject3D

MODEL_PATH = 'models/spider/SM_Japanise_Krab.obj'

class Spider(CustomObject3D):
    
    SCALE = 0.01
    
    def __init__(self, position, parent, game, scale=(.01, .01, .01)):
        model = game.loader.loadModel(MODEL_PATH)
        super().__init__(model, position, parent, scale)