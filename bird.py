from CustomObject3D import CustomObject3D

MODEL_PATH = 'models/bird/MN64-Eagle/MN64-Eagle.obj'

class Bird(CustomObject3D):
    
    def __init__(self, position, parent, game, scale=[1, 1, 1], rotation_center=(0, 0, 0)):
        model = game.loader.loadModel(MODEL_PATH)
        super().__init__(model, position, parent, scale)
        self.gravity = 0
