from CustomObject3D import CustomObject3D
from panda3d.core import NodePath, PointLight, VBase4, Spotlight, PerspectiveLens, LPoint3

class Table(CustomObject3D):
    
    MODEL_PATH = "models/asylum-table/asylum_table01.obj"
    
    def __init__(self, position, parent, game, scale=[0.025 for _ in range(3)]):
        model = game.loader.loadModel(Table.MODEL_PATH)
        super().__init__(model, position, parent, scale)
        self.gravity = 0
        
class SpotlightOBJ(CustomObject3D):
    
    MODEL_PATH = "models/spotlight/spotlight2.obj"
    LIGHT_COLOR = (10, 10, 10, 1)
    LIGHT_DISTANCE_THRESHOLD = 12
    
    
    def __init__(self, position, parent, game, scale=[1, 1, 1], look_at=(0, 0, 0), test=None):
        model = game.loader.loadModel(SpotlightOBJ.MODEL_PATH)
        super().__init__(model, position, parent, scale, emmits_light=True, 
                         light_color_temperature=SpotlightOBJ.LIGHT_COLOR, light_distance_threshold=SpotlightOBJ.LIGHT_DISTANCE_THRESHOLD)
        self.gravity = 0
        self.velocity = [0, 0, 0]
        self.model.setP(90)
        self.model.setH(180)

        self.slight = Spotlight('slight')
        self.slight.setColor(SpotlightOBJ.LIGHT_COLOR)
        self.lens = PerspectiveLens()
        self.slight.setLens(self.lens)
        self.slnp = self.parent.attachNewNode(self.slight)
        self.slnp.setPos(self.model.getPos() + LPoint3(0, 0, 5))
        self.slnp.lookAt(look_at)
        test.setLight(self.slnp)
        
        # create pointlight to make the lamp glow
        self.pointlight = PointLight('pointlight')
        self.pointlight.setColor(SpotlightOBJ.LIGHT_COLOR)
        self.pnp = self.model.attachNewNode(self.pointlight)
        self.pnp.setPos(0, 0, self.model.getPos()[2] + 0.5)
        self.model.setLight(self.pnp)
    
    def look_at(self, look_at):
        self.slnp.lookAt(look_at)
        