from CustomObject3D import CustomObject3D
from panda3d.core import NodePath, PointLight, VBase4, Spotlight, PerspectiveLens

class Table(CustomObject3D):
    
    MODEL_PATH = "models/asylum-table/asylum_table01.obj"
    
    def __init__(self, position, parent, game, scale=[0.025 for _ in range(3)]):
        model = game.loader.loadModel(Table.MODEL_PATH)
        super().__init__(model, position, parent, scale)
        self.gravity = 0
        