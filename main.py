import math
import os
import time
import argparse

from typing import Tuple
from direct.showbase.ShowBase import ShowBase
from direct.filter.FilterManager import FilterManager
from direct.task import Task
from panda3d.core import *

from CustomObject3D import CustomObject3D
from Player import Player
from labyrinth import Parallelepiped, Labyrinth

from common import *

WIDTH = 800
HEIGHT = 600
PLAYER_SPEED = 0.25
PLAYER_JUMP_SPEED = 0.35

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

        self.labyrinth_np, self.labyrinth = self.generateLabyrinth(
            parent_node=self.render,
            labyrinth_file=labyrinth_file,
        )

        # Load the environment model
        # table_model = self.loader.loadModel(self.path_p3d / 'models/table-old/o_table_old_01_a.obj')
        # simplepbr.init()
        player_model = self.loader.loadModel(self.path_p3d / 'models/player/amongus.obj')
        # rotate player model vertically
        player_model.setHpr(0, 90, 0)
        player_scale = (0.5, 0.5, 0.5)
        player_position = self.labyrinth.start_pos if self.labyrinth.start_pos is not None else [self.labyrinth.width / 2, self.labyrinth.depth / 2, self.labyrinth.height]
        # Create collision node
        player_collider_node = CollisionNode("Player")

        player_collider_node.addSolid(CollisionCapsule(4, 3, 2, 4, 1, 2, 1))
        player_collider = player_model.attachNewNode(player_collider_node)
        if self.DEBUG_COLLISIONS:
            player_collider.show()

        self.player = Player(player_model, player_position, self.labyrinth_np, scale=player_scale, speed=PLAYER_SPEED)
        self.player_position = player_position

        # Lighting
        self.flashlight_pos = [0, 10, 0]
        self.flashlight = Spotlight('flashlight')
        self.flashlight.setColor((1, 1, 1, 1))
        
        self.flashlight.setShadowCaster(True, 512, 512)   # enable shadows

        lens = PerspectiveLens()
        self.flashlight.setLens(lens)

        self.flashlight_np = self.render.attachNewNode(self.flashlight)
        self.flashlight_np.setPos(0, 10, 0)
        self.flashlight_np.lookAt(self.player.model)
        self.render.setLight(self.flashlight_np)

        flashlight_cube = generateGeometry(Parallelepiped(2, 2, 2), 'flashlight')
        self.flashlight_np.attachNewNode(flashlight_cube)

        # Create Ambient Light
        ambient_light_intensity = 0.3
        ambient_light = AmbientLight('ambient_light')
        ambient_light.setColor((ambient_light_intensity, ambient_light_intensity, ambient_light_intensity, 1))
        ambient_light_np = self.render.attachNewNode(ambient_light)
        self.render.setLight(ambient_light_np)

        # Collision stuff
        self.cTrav = CollisionTraverser()
        self.pusher = CollisionHandlerPusher()

        self.pusher.addCollider(player_collider, self.player.model)
        self.cTrav.addCollider(player_collider, self.pusher)

        # Task management
        self.mouse_coords = [0, 0]

        self.taskMgr.add(self.update_mouse_coords_task, 'update_mouse_coords_task')
        self.taskMgr.add(self.read_inputs_task, 'read_inputs_task')
        if not self.DEBUG_MOUSE_CAMERA:
            self.taskMgr.add(self.move_camera_task, 'move_camera_task')
        self.taskMgr.add(self.move_flashlight_task, 'move_flashlight_task')
        self.taskMgr.add(self.move_player_task, 'move_player_task')

        self.quad_filter = None
        self.flashlight_power = 1
        self.flashlight_flicker = 0
        self.start_time = time.time()   # avoid providing extremelly large numbers to the shaders, since GLSL acts funky with those (in sin() for instance), so send time since app launch
        self.setupShaders()

        # inputs
        self.accept('x', self.toggle_light)
        self.accept('c', self.toggle_perspective)
        self.pusher.addInPattern('%fn-into-%in')
        self.pusher.addOutPattern('%fn-out-%in')
        self.pusher.addAgainPattern('%fn-again-%in')
        
        self.accept("Player-out-Ground", self.player_out_ground)
        self.accept("Player-into-Ground", self.player_hit_ground)
        self.accept("Player-again-Ground", self.player_hit_ground)
        
    def player_hit_ground(self, entity):
        is_bellow_player = entity.getSurfacePoint(self.player.model).getY() < 0
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

    def read_inputs_task(self, task):
        isDown = self.mouseWatcherNode.is_button_down

        # Camera
        if isDown(KeyboardButton.asciiKey("a")):
            self.camera_pos[0] -= 1
        if isDown(KeyboardButton.asciiKey("d")):
            self.camera_pos[0] += 1
        if isDown(KeyboardButton.asciiKey("w")):
            self.camera_pos[1] = max(95, self.camera_pos[1] - 1)
        if isDown(KeyboardButton.asciiKey("s")):
            self.camera_pos[1] = min(265, self.camera_pos[1] + 1)
        if isDown(KeyboardButton.asciiKey("e")):
            self.camera_zoom -= 1
        if isDown(KeyboardButton.asciiKey("q")):
            self.camera_zoom += 1

        # Flashlight
        if isDown(KeyboardButton.left()):
            self.flashlight_pos[0] -= 1
        if isDown(KeyboardButton.right()):
            self.flashlight_pos[0] += 1
        if isDown(KeyboardButton.up()):
            self.flashlight_pos[1] += 1
        if isDown(KeyboardButton.down()):
            self.flashlight_pos[1] -= 1

        #Player
        self.player.velocity[0] = 0
        self.player.velocity[1] = 0
        if isDown(KeyboardButton.asciiKey("j")):
            self.player.velocity[0] -= PLAYER_SPEED
        if isDown(KeyboardButton.asciiKey("l")):
            self.player.velocity[0] += PLAYER_SPEED
        if isDown(KeyboardButton.asciiKey("i")):
            self.player.velocity[1] += PLAYER_SPEED
        if isDown(KeyboardButton.asciiKey("k")):
            self.player.velocity[1] -= PLAYER_SPEED
        if isDown(KeyboardButton.asciiKey("u")):
            if self.player.is_on_ground:
                self.player.velocity[2] = PLAYER_JUMP_SPEED
                self.player.is_on_ground = False
        if isDown(KeyboardButton.asciiKey("o")):
            self.player.put_light()
        
        self.player.update()

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

        labyrinth_np = parent_node.attachNewNode('Labyrinth')
        labyrinth = Labyrinth.from_map_file(labyrinth_file, self.DEBUG_MAP)
        labyrinth_walls = [generateGeometry(obj, f'wall_{idx}') for idx, obj in enumerate(labyrinth.blocks)]
        if self.DEBUG_LOG: print('Number of walls:', len(labyrinth_walls))
        for idx, wall in enumerate(labyrinth_walls):
            wall_obj = labyrinth.blocks[idx]
            is_ground = wall_obj.otype == Labyrinth.TYPE_FLOOR
            wall_node = labyrinth_np.attachNewNode(wall)
            if wall_obj.texture not in textures:
                textures[wall_obj.texture] = self.loader.loadTexture(self.path_p3d / wall_obj.texture)
            wall_node.setTexture(textures[wall_obj.texture])
            wall_node.setPos(wall_obj.position)
            node_name = "Ground" if is_ground else "Wall"
            wall_collider_node = CollisionNode(node_name)
            
            if labyrinth.is_window(wall_obj):
                wall_node.setTransparency(True)

            # Collisions
            # get center of the wall
            wall_center = Point3(wall_obj.width / 2, wall_obj.depth / 2, wall_obj.height / 2)
            wall_collider_node.addSolid(CollisionBox(wall_center,
                                                     wall_obj.width / 2,
                                                     wall_obj.depth / 2,
                                                     wall_obj.height / 2))
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
        update_orthographic_lens(self.camera_orthographic_lens,newX, newY)

    def setupShaders(self):
        # Plenty of features, including normal maps and per-pixel lighting
        # (https://docs.panda3d.org/1.10/python/programming/shaders/shader-generator)
        self.render.setShaderAuto()

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

    def move_camera_task(self, task):
        multiplier = self.camera_zoom
        angle_x_degrees = self.camera_pos[0] * 1
        angle_y_degrees = self.camera_pos[1] * 1
        angle_x_radians = angle_x_degrees * (math.pi / 180.0)
        angle_y_radians = angle_y_degrees * (math.pi / 180.0)

        self.camera.setPos(
            math.sin(angle_x_radians) * multiplier,
            -math.cos(angle_x_radians) * multiplier * -math.cos(angle_y_radians),
            math.sin(angle_y_radians) * multiplier
        )

        self.camera.lookAt((0,0,0))
        return Task.cont

    def move_flashlight_task(self, task):
        self.flashlight_np.setPos(*self.flashlight_pos)
        self.flashlight_np.lookAt((0,0,0))
        return Task.cont

    def move_player_task(self, task):
        # self.player.model.setPos(*self.player_position)
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
