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
    LIGHT_COLOR = (
        1, 
        1, 
        1, 
        1)
    SELF_LIGHT_COLOR = (
        1.5, 
        1.5, 
        1.5, 
        1)
    LIGHT_DISTANCE_THRESHOLD = 12
    LIGHT_MOVEMENT_SPEED = 0.1
    
    def __init__(self, position, parent, game, scale=[1, 1, 1], look_at=(0, 0, 0), 
                grass_height=-10, target_height_limit=0, test=None):
        model = game.loader.loadModel(SpotlightOBJ.MODEL_PATH)
        super().__init__(model, position, parent, scale, emmits_light=True, 
                         light_color_temperature=SpotlightOBJ.LIGHT_COLOR, light_distance_threshold=SpotlightOBJ.LIGHT_DISTANCE_THRESHOLD)
        self.gravity = 0
        self.velocity = [0, 0, 0]
        self.model.setP(90)
        self.model.setH(135)
        self.grass_height = grass_height
        self.current_target = look_at
        self.look_direction = 1
        self.target_height_limit = target_height_limit

        peak = self.model.getTightBounds()[1]
        self.slight = Spotlight('slight')
        self.slight.setColor(SpotlightOBJ.LIGHT_COLOR)
        self.lens = PerspectiveLens()
        self.slight.setLens(self.lens)
        self.slnp = self.parent.attachNewNode(self.slight)
        self.slnp.setPos(peak + LPoint3(-10, 0, -10))
        self.slnp.lookAt(look_at)
        parent.setLight(self.slnp)
        
        # create pointlight to make the lamp glow
        self.self_slight = Spotlight('self_slight')
        self.self_slight.setColor(SpotlightOBJ.SELF_LIGHT_COLOR)
        self.self_slight.setLens(self.lens)
        self.pnp = self.parent.attachNewNode(self.self_slight)
        self.pnp.setPos(look_at)
        self.pnp.look_at(peak + LPoint3(-2, 0, -10))
        self.model.setLight(self.pnp)
    
    def update(self):
        if self.look_direction == 1 and self.current_target[2] >= self.target_height_limit:
            self.look_direction = -1
        elif self.look_direction == -1 and self.current_target[2] <= self.grass_height:
            self.look_direction = 1
        # print(f"current target: {self.current_target}, look direction: {self.look_direction}")
        self.current_target += LPoint3(0, 0, SpotlightOBJ.LIGHT_MOVEMENT_SPEED * self.look_direction)
    
        self.look_at(self.current_target)
        # self.pnp.setPos(self.current_target)
    
    def look_at(self, look_at):
        self.slnp.lookAt(look_at)
        