import os
import time
import argparse
import random

import simplepbr

from typing import Tuple
from direct.showbase.ShowBase import ShowBase
from direct.filter.FilterManager import FilterManager
from direct.task import Task
from panda3d.core import *

from CustomObject3D import CustomObject3D
from Player import Player
from bird import Bird
from spider import Spider
from labyrinth import Floor, Parallelepiped, Labyrinth, Wall, Window

from common import *

WIDTH = 800
HEIGHT = 600
PLAYER_SPEED = 0.25
PLAYER_JUMP_SPEED = 0.35
AMBIENT_LIGHT_INTENSITY = 0.4
DIRECTIONAL_LIGHT_INTENSITY = 0.4
SKY_COLOR = (0.0, 0.0, AMBIENT_LIGHT_INTENSITY)
SPIDER_SPAWN_CHANCE = 1

MOON_PATH = "models/moon/moon2.obj"
GRASS_PATH = "models/grass/grass.glb"

# Enable non-power-of-2 textures. This is relevant for the FilterManager post-processing.
# If power-of-2 textures is enforced, then the code has to deal with the texture padding.
# We want so simplify the shader code so they are disabled. There is already wide support for non-power-of-2 textures (https://discourse.panda3d.org/t/cg-glsl-filtermanager-texpad-x/14694/8)
# Additionally, set the number of bits used for the depth buffer so that the orthographic projection's visual artifacts are reduced
loadPrcFileData('', '''
textures-power-2 none
depth-bits 24
''')


# TODO: consistent case style? camelCase, snake_case...
# TODO: to consider: temporary lights (like candles)? fixed literal spotlights?
class ExplorerApp(ShowBase):

    def __init__(self, labyrinth_file: str, debug_opts: dict):
        ShowBase.__init__(self)

        # simplepbr.init()

        self.set_background_color(*SKY_COLOR)

        self.DEBUG_LOG = debug_opts.get('log', False)
        self.DEBUG_MAP = debug_opts.get('map', False)
        self.DEBUG_3D_AXIS = debug_opts.get('3d_axis', False)
        self.DEBUG_COLLISIONS = debug_opts.get('collisions', False)
        self.DEBUG_MOUSE_CAMERA = debug_opts.get('mouse_camera', False)

        # set window size
        props = WindowProperties()
        props.setSize(WIDTH, HEIGHT)
        self.win.requestProperties(props)

        # camera variables
        self.camera_pos = [0, 180, 0]
        self.camera_zoom = 60
        self.camera_perspective_lens = self.cam.node().getLens()
        self.camera_orthographic_lens = OrthographicLens()
        update_orthographic_lens(self.camera_orthographic_lens, WIDTH, HEIGHT)

        self.path = os.path.dirname(os.path.abspath(__file__))
        self.path_p3d = Filename.fromOsSpecific(self.path)
        
        if not self.DEBUG_MOUSE_CAMERA:
            self.disableMouse()

        if self.DEBUG_3D_AXIS:
            self.create3dAxis()

        # Collision stuff
        self.cTrav = CollisionTraverser()
        self.pusher = CollisionHandlerPusher()

        # Load the environment model
        self.labyrinth_np, self.labyrinth = self.generateLabyrinth(
            parent_node=self.render,
            labyrinth_file=labyrinth_file,
        )

        self.init_models()

        # Lighting
        # Create Ambient Light
        ambient_light_intensity = AMBIENT_LIGHT_INTENSITY
        ambient_light = AmbientLight('ambient_light')
        ambient_light.setColor((ambient_light_intensity, ambient_light_intensity, ambient_light_intensity, 1))
        ambient_light_np = self.render.attachNewNode(ambient_light)
        self.render.setLight(ambient_light_np)
        
        # Create Directional Light
        directional_light = DirectionalLight('directional_light')
        directional_light.setColor((DIRECTIONAL_LIGHT_INTENSITY, DIRECTIONAL_LIGHT_INTENSITY, DIRECTIONAL_LIGHT_INTENSITY, 1))
        directional_light.direction = Vec3(0, 0, -0.5)
        dlnp = self.render.attachNewNode(directional_light)
        self.render.setLight(dlnp)

        # Task management
        self.mouse_coords = [0, 0]

        self.taskMgr.add(self.update_mouse_coords_task, 'update_mouse_coords_task')
        self.taskMgr.add(self.read_inputs_task, 'read_inputs_task')

        self.quad_filter = None
        self.flashlight_power = 1
        self.flashlight_flicker = 0
        self.start_time = time.time()   # avoid providing extremelly large numbers to the shaders, since GLSL acts funky with those (in sin() for instance), so send time since app launch
        self.setupShaders()

        # inputs
        self.accept('v', self.toggle_light)
        self.accept('c', self.toggle_perspective)
        self.pusher.addInPattern('%fn-into-%in')
        self.pusher.addOutPattern('%fn-out-%in')
        self.pusher.addAgainPattern('%fn-again-%in')
        
        self.accept("Player-out-Ground", self.player_out_ground)
        self.accept("Player-into-Ground", self.player_hit_ground)
        self.accept("Player-again-Ground", self.player_hit_ground)
        
        self.accept("q", self.move_camera, [(-1, 0, 0)]) 
        self.accept("e", self.move_camera, [(1, 0, 0)])      
          
               
        
        
    def init_models(self):
        player_model: NodePath = self.loader.loadModel(self.path_p3d / 'models/player/amongus_corrected.obj')
        for material in player_model.find_all_materials():
            material.set_ambient(material.get_diffuse())
        # rotate player model vertically
        player_model.setHpr(0, 90, 0)
        player_scale = (.5,) * 3
        player_position = self.labyrinth.start_pos if self.labyrinth.start_pos is not None else [self.labyrinth.width / 2, self.labyrinth.depth / 2, self.labyrinth.height]
        # Create collision node
        player_collider_node = CollisionNode("Player")
        
        player_collider_node.addSolid(CollisionCapsule(0, 0, 1, 0, 0, 2, 1))
        player_collider = player_model.attachNewNode(player_collider_node)
        player_collider.setHpr(0, -90, 0)
        if self.DEBUG_COLLISIONS:
            player_collider.show()

        self.player = Player(player_model, player_position, self.labyrinth_np, scale=player_scale)
        self.player_position = player_position
        
        self.pusher.addCollider(player_collider, self.player.model)
        self.cTrav.addCollider(player_collider, self.pusher)
        move_camera(self.camera, self.camera_zoom, self.camera_pos)
    
        # create bird
        self.bird = Bird([player_position[0] + 5, player_position[1], player_position[2]], self.labyrinth_np, self)
        
        # create moon
        moon_model = self.loader.loadModel(self.path_p3d / MOON_PATH)
        moon_position = (-125, 300, 75)
        moon_scale = [5 for _ in range(3)]
        self.moon = CustomObject3D(moon_model, moon_position, self.labyrinth_np, scale=moon_scale)
        
        # create grass
        grass_model = self.loader.loadModel(self.path_p3d / GRASS_PATH)
        grass_position = player_position
        grass_scale = [2 for _ in range(3)]
        self.grass = CustomObject3D(grass_model, grass_position, self.labyrinth_np, scale=grass_scale)
        
    
    def init_spider(self, wall_obj: Wall, labyrinth_np: NodePath):
        spider_scale = [Spider.SCALE * 1 for _ in range(3)]
        if wall_obj.east_inside:
            self.spawn_spider(wall_obj.position[0] + wall_obj.width, wall_obj.position[1] + wall_obj.depth / 2, wall_obj.position[2] + wall_obj.height / 2, -90, -90, 0, labyrinth_np, spider_scale, (0,1,1), wall_obj)

        if wall_obj.west_inside:
            self.spawn_spider(wall_obj.position[0], wall_obj.position[1] + wall_obj.depth / 2, wall_obj.position[2] + wall_obj.height / 2, 90, -90, 0, labyrinth_np, spider_scale, (0,1,1), wall_obj)

        if wall_obj.south_inside:
            self.spawn_spider(wall_obj.position[0] + wall_obj.width / 2, wall_obj.position[1] + wall_obj.depth, wall_obj.position[2] + wall_obj.height / 2, 0, -90, 0, labyrinth_np, spider_scale, (1,0,1), wall_obj)

        if wall_obj.north_inside:
            self.spawn_spider(wall_obj.position[0] + wall_obj.width / 2, wall_obj.position[1], wall_obj.position[2] + wall_obj.height / 2, 180, -90, 0, labyrinth_np, spider_scale, (1,0,1), wall_obj)

    def spawn_spider(self, x, y, z, h, p, r, labyrinth_np, scale, movement_axis, wall):
        spawn_chance = random.random()
        if spawn_chance < SPIDER_SPAWN_CHANCE:
            spider = Spider([x, y, z], labyrinth_np, self, scale=scale, movement_axis=movement_axis, wall_dimensions=(wall.width, wall.depth, wall.height))
            spider.model.setHpr(h, p, r)

            self.spiders.append(spider)
            return spider
            
    def player_hit_ground(self, entity):
        is_bellow_player = entity.getSurfacePoint(self.player.model).getY() <= 0
        self.player.velocity[2] = 0
        
        if is_bellow_player:
            if self.DEBUG_LOG: print("Hit ground", entity)
            self.player.is_on_ground = True       
    
    def player_out_ground(self, entity):
        # print("Out of ground", entity)]
        if self.DEBUG_LOG: print("Out of ground")
        self.player.is_on_ground = False
        
    def move_entity(self, entity, direction):
        entity.move(*direction)

    def move_camera(self, direction):
        self.camera_pos[0] += direction[0] * 90
        self.player.model.setH(self.camera_pos[0])
        
        # TODO: not used ig?
        if direction[1] < 0 and self.camera_pos[1] > 120 or direction[1] > 0 and self.camera_pos[1] < 230:
            self.camera_pos[1] += direction[1] * 90
        
        move_camera(self.camera, self.camera_zoom, self.camera_pos)


    def read_inputs_task(self, task):
        isDown = self.mouseWatcherNode.is_button_down
        MouseWatcher

        # Camera
        has_camera_moved = False

        if isDown(KeyboardButton.asciiKey("x")):
            self.camera_zoom -= 1
            has_camera_moved = True
        if isDown(KeyboardButton.asciiKey("z")):
            self.camera_zoom += 1
            has_camera_moved = True
        
        if has_camera_moved:
            move_camera(self.camera, self.camera_zoom, self.camera_pos)

        #Player
        self.player.velocity[0] = 0
        self.player.velocity[1] = 0
        player_radians = math.radians(self.player.model.getH())
        horizontal_idx = int(math.sin(player_radians))
        vertical_idx = int(math.cos(player_radians))
        if isDown(KeyboardButton.asciiKey("a")): # 0 -> 0, 90 -> 1, 180 -> 0, 270 -> 1
            self.player.velocity[abs(horizontal_idx)] -= PLAYER_SPEED * horizontal_idx if horizontal_idx != 0 else PLAYER_SPEED
        if isDown(KeyboardButton.asciiKey("d")):
            self.player.velocity[abs(horizontal_idx)] += PLAYER_SPEED * horizontal_idx if horizontal_idx != 0 else PLAYER_SPEED
        if isDown(KeyboardButton.asciiKey("w")):
            self.player.velocity[abs(vertical_idx)] += PLAYER_SPEED * -horizontal_idx if vertical_idx == 0 else PLAYER_SPEED
        if isDown(KeyboardButton.asciiKey("s")):
            self.player.velocity[abs(vertical_idx)] -= PLAYER_SPEED * -horizontal_idx if vertical_idx == 0 else PLAYER_SPEED
        if isDown(KeyboardButton.space()):
            if self.player.is_on_ground:
                self.player.velocity[2] = PLAYER_JUMP_SPEED
                self.player.is_on_ground = False
        if isDown(KeyboardButton.asciiKey("f")):
            self.player.put_light()
        
        # Update entities
        
        self.player.update()
        
        for spider in self.spiders:
            spider.update()
        
        self.bird.update(task.time)

        return Task.cont

    def toggle_light(self):
        self.flashlight_flicker = 1 - self.flashlight_flicker
        self.quad_filter.setShaderInput('lightFlickerRatio', self.flashlight_flicker)

    def toggle_perspective(self):
        if isinstance(self.cam.node().getLens(), PerspectiveLens):
            self.cam.node().setLens(self.camera_orthographic_lens)
        else:
            self.cam.node().setLens(self.camera_perspective_lens)

    def generateLabyrinth(self, parent_node: NodePath, labyrinth_file: str) -> Tuple[NodePath, Labyrinth]:
        # Keep track of textures used by the labyrinth's blocks, so we don't have to tell Panda3D to repeatedly load them
        textures = {} 
        self.spiders = []
        labyrinth_np = parent_node.attachNewNode('Labyrinth')
        labyrinth = Labyrinth.from_map_file(labyrinth_file, self.DEBUG_MAP)
        labyrinth_blocks = [(block, generateGeometry(block, f'labyrinth_block_{idx}')) for idx, block in enumerate(labyrinth.blocks)]
        if self.DEBUG_LOG: print('Number of walls:', len(labyrinth_blocks))
        for block, block_geom in labyrinth_blocks:
            is_ground = isinstance(block, Floor)
            wall_node = labyrinth_np.attachNewNode(block_geom)
            if block.texture not in textures:
                textures[block.texture] = self.loader.loadTexture(self.path_p3d / block.texture)
            wall_node.setTexture(textures[block.texture])
            wall_node.setPos(block.position)
            node_name = "Ground" if is_ground else "Wall"
            wall_collider_node = CollisionNode(node_name)
            
            if isinstance(block, Window):
                wall_node.setTransparency(True)
            
            if isinstance(block, Wall):
                self.init_spider(block, labyrinth_np)
            
            # Collisions
            # get center of the wall
            wall_center = Point3(block.width / 2, block.depth / 2, block.height / 2)
            wall_collider_node.addSolid(CollisionBox(wall_center,
                                                     block.width / 2,
                                                     block.depth / 2,
                                                     block.height / 2))
            wall_collider = wall_node.attachNewNode(wall_collider_node)
            if self.DEBUG_COLLISIONS:
                wall_collider.show()
        
        # Center the labyrinth to the origin
        labyrinth_np.setPos(
            - labyrinth.width / 2,
            - labyrinth.depth / 2,
            - labyrinth.height / 2,
        )

        return labyrinth_np, labyrinth

    def windowResized(self):
        newX, newY = self.win.getSize()
        self.quad_filter.setShaderInput('u_resolution', (newX, newY))
        update_orthographic_lens(self.camera_orthographic_lens, newX, newY)

    def setupShaders(self):
        # Plenty of features, including normal maps and per-pixel lighting
        # (https://docs.panda3d.org/1.10/python/programming/shaders/shader-generator)
        self.render.setShaderAuto()
        
        # Apply the flashlight effect, and others, using deferred lighting
        flashlight_shader = Shader.load(Shader.SL_GLSL,
            vertex='shaders/flashlight.vert',
            fragment='shaders/flashlight.frag')

        # Save the normal buffer into the auxiliary bitplane
        self.render.setAttrib(AuxBitplaneAttrib.make(AuxBitplaneAttrib.ABO_aux_normal))

        manager = FilterManager(self.win, self.cam)
        tex = Texture()
        dtex = Texture()
        ntex = Texture()
        self.quad_filter = manager.renderSceneInto(colortex=tex, depthtex=dtex, auxtex=ntex)
        self.quad_filter.setShader(flashlight_shader)
        self.quad_filter.setShaderInputs(
            tex=tex,
            dtex=dtex,
            ntex=ntex,
            u_mouse=self.mouse_coords,
            u_resolution=(WIDTH, HEIGHT),
            u_time=time.time() - self.start_time,
            lightPower=self.flashlight_power,
            lightFlickerRatio=self.flashlight_flicker,
        )

        self.accept('aspectRatioChanged', self.windowResized)
        self.taskMgr.add(self.update_shader_time_task, 'update_shader_time_task')

    def update_shader_time_task(self, task):
        self.quad_filter.setShaderInput('u_time', time.time() - self.start_time)
        return Task.cont

    def create3dAxis(self, heads: bool = False):
        axis3d = self.render.attachNewNode('axis3d')

        x_axis = Parallelepiped(10, 0.1, 0.1, color=(1, 0, 0, 1))
        y_axis = Parallelepiped(0.1, 0.1, 10, color=(0, 1, 0, 1))
        z_axis = Parallelepiped(0.1, 10, 0.1, color=(0, 0, 1, 1))

        axis3d.attach_new_node(generateGeometry(x_axis, 'x_axis'))
        axis3d.attach_new_node(generateGeometry(y_axis, 'y_axis'))
        axis3d.attach_new_node(generateGeometry(z_axis, 'z_axis'))

        if heads:
            x_axis_head = Parallelepiped(0.3, 0.3, 0.3, color=(1, 0, 0, 1))
            y_axis_head = Parallelepiped(0.3, 0.3, 0.3, color=(0, 1, 0, 1))
            z_axis_head = Parallelepiped(0.3, 0.3, 0.3, color=(0, 0, 1, 1))

            x_axis_head_node = axis3d.attach_new_node(generateGeometry(x_axis_head, 'x_axis_head'))
            x_axis_head_node.setPos(10, 0, 0)
            y_axis_head_node = axis3d.attach_new_node(generateGeometry(y_axis_head, 'y_axis_head'))
            y_axis_head_node.setPos(0, 10, 0)
            z_axis_head_node = axis3d.attach_new_node(generateGeometry(z_axis_head, 'z_axis_head'))
            z_axis_head_node.setPos(0, 0, 10)

    def update_mouse_coords_task(self, task):
        if self.mouseWatcherNode.hasMouse():
            self.mouse_coords[0] = self.mouseWatcherNode.getMouseX()
            self.mouse_coords[1] = self.mouseWatcherNode.getMouseY()
        
        self.quad_filter.setShaderInput('u_mouse', self.mouse_coords)

        return Task.cont



parser = argparse.ArgumentParser('cv-proj')
parser.add_argument('--map', '-m',
    type=str,
    default='test1.map',
    help='the labyrinth map file to be loaded (default=\'test1.map\')')

parser_debug = parser.add_argument_group('debug', 'Add debug info to the game.')
parser_debug.add_argument('--debug.map',
    action='store_true',
    help='activate the debug environment for the labyrinth scene (colored walls, for instance)')
parser_debug.add_argument('--debug.mouse-camera',
    action='store_true',
    help='let the camera be controllable with the mouse')
parser_debug.add_argument('--debug.3d-axis',
    action='store_true',
    help='place a 3D axis in the scene at the origin')
parser_debug.add_argument('--debug.collisions',
    action='store_true',
    help='show the collision boundaries')
parser_debug.add_argument('--debug.fps',
    action='store_true',
    help='show an FPS counter at the top right')
parser_debug.add_argument('--debug.log',
    action='store_true',
    help='print debug messages (reduces performance)')


args = parser.parse_args()

debug_opts = {k.split('.')[1]: v for k, v in args._get_kwargs() if k.startswith('debug.')}

app = ExplorerApp(
    labyrinth_file=args.map,
    debug_opts=debug_opts,
)
app.setFrameRateMeter(debug_opts['fps'])
app.run()
