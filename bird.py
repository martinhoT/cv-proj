from CustomObject3D import CustomObject3D
import math

MODEL_PATH = 'models/bird/MN64-Eagle/MN64-Eagle.obj'

class Bird(CustomObject3D):
    
    ROTATION_SPEED = 40
    
    def __init__(self, position, parent, game, scale=[1, 1, 1], rotation_center=(15, 10, 20), 
                 distance_from_center=20):
        model = game.loader.loadModel(MODEL_PATH)
        super().__init__(model, position, parent, scale)
        self.gravity = 0
        self.distance_from_center = distance_from_center
        self.rotation_center = rotation_center
        self.model.setP(90)
    
    def update(self, time):
        # super().update()
        angleDegrees = time * self.ROTATION_SPEED
        angleRadians = angleDegrees * (math.pi / 180.0)
        
        self.model.setPos(
            (self.distance_from_center) * math.sin(angleRadians) + self.rotation_center[0],
            -(self.distance_from_center) * math.cos(angleRadians) + self.rotation_center[1],
            self.rotation_center[2]
        )
        
        self.model.setH(angleDegrees + 90)
