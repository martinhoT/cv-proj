import math
import os

from typing import Tuple
from direct.showbase.ShowBase import ShowBase
from direct.filter.FilterManager import FilterManager
from direct.task import Task
from panda3d.core import *

from CustomObject3D import CustomObject3D
from labyrinth import Parallelepiped, Labyrinth

WIDTH = 800
HEIGHT = 600
PLAYER_SPEED = 0.25
# to facilitate analysing the model when debugging
MOUSE_CAMERA = False
HELPER_3D_AXIS = True
SHOW_COLLISIONS = False

# Enable non-power-of-2 textures. This is relevant for the FilterManager post-processing.
# If power-of-2 textures is enforced, then the code has to deal with the texture padding.
# We want so simplify the shader code so they are disabled. There is already wide support for non-power-of-2 textures (https://discourse.panda3d.org/t/cg-glsl-filtermanager-texpad-x/14694/8)
loadPrcFileData('', '''
textures-power-2 none
''')


# TODO: consistent case style? camelCase, snake_case...
# TODO: to consider: temporary lights (like candles)? fixed literal spotlights?
class ExplorerApp(ShowBase):

    def __init__(self):
        ShowBase.__init__(self)

        # set window size
        props = WindowProperties()
        props.setSize(WIDTH, HEIGHT)
        self.win.requestProperties(props)

        # camera variables
        self.camera_pos = [0, 180, 0]
        self.camera_zoom = 60

        self.path = os.path.dirname(os.path.abspath(__file__))
        self.path_p3d = Filename.fromOsSpecific(self.path)

        if not MOUSE_CAMERA:
            self.disableMouse()

        if HELPER_3D_AXIS:
            self.create3dAxis()

        # Load the environment model
        # table_model = self.loader.loadModel(self.path_p3d / 'models/table-old/o_table_old_01_a.obj')
        # simplepbr.init()
        player_model = self.loader.loadModel(self.path_p3d / 'models/player/amongus.obj')
        # rotate player model vertically
        player_model.setHpr(0, 90, 0)
        player_scale = (0.5, 0.5, 0.5)
        player_position = [-1.25, -0.125, -8.5]
        # Create collision node
        player_collider_node = CollisionNode("Player")

        player_collider_node.addSolid(CollisionCapsule(4, 3, 2, 4, 1, 2, 1))
        player_collider = player_model.attachNewNode(player_collider_node)
        if SHOW_COLLISIONS:
            player_collider.show()

        self.player = CustomObject3D(player_model, player_position, self.render, scale=player_scale, speed=PLAYER_SPEED)
        self.player_position = player_position

        self.labyrinth = self.generateLabyrinth(
            parent_node=self.render,
            labyrinth_file='test2.map',
        )        

        # Lighting
        self.flashlight_pos = [0, 10, 0]
        self.flashlight = Spotlight('flashlight')
        self.flashlight.setColor((1, 1, 1, 1))
        # self.flashlight.setAttenuation((1, 0, 1))   # fall off with distance
        # self.flashlight.setShadowCaster(True, 512, 512)   # enable shadows
        lens = PerspectiveLens()
        self.flashlight.setLens(lens)

        self.flashlight_np = self.render.attachNewNode(self.flashlight)
        self.flashlight_np.setPos(0, 10, 0)
        self.flashlight_np.lookAt(self.player.model)
        self.render.setLight(self.flashlight_np)

        flashlight_cube = self.generateGeometry(Parallelepiped(2, 2, 2), 'flashlight')
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
        if not MOUSE_CAMERA:
            self.taskMgr.add(self.move_camera_task, 'move_camera_task')
        self.taskMgr.add(self.move_flashlight_task, 'move_flashlight_task')
        self.taskMgr.add(self.move_player_task, 'move_player_task')

        self.quad_filter = None
        self.flashlight_power = 1
        self.setupShaders()

        # inputs
        self.accept('x', self.toggle_light)
        # self.accept('j', self.move_entity, [self.player, (-1, 0, 0)])
        # self.accept('l', self.move_entity, [self.player, (1, 0, 0)])
        # self.accept('i', self.move_entity, [self.player, (0, -1, 0)])
        # self.accept('k', self.move_entity, [self.player, (0, 1, 0)])
        # self.accept('j-repeat', self.move_entity, [self.player, (-1, 0, 0)])
        # self.accept('l-repeat', self.move_entity, [self.player, (1, 0, 0)])
        # self.accept('i-repeat', self.move_entity, [self.player, (0, -1, 0)])
        # self.accept('k-repeat', self.move_entity, [self.player, (0, 1, 0)])
        
    
    def move_entity(self, entity, direction):
        print("Amogus")
        entity.move(*direction)
        print(f"{entity.model.getPos() = }")

    # TODO: use self.accept(key, func, args) instead?
    def read_inputs_task(self, task):
        isDown = self.mouseWatcherNode.is_button_down

        # Camera
        if isDown(KeyboardButton.asciiKey("a")):
            self.camera_pos[0] -= 1
        if isDown(KeyboardButton.asciiKey("d")):
            self.camera_pos[0] += 1
        if isDown(KeyboardButton.asciiKey("w")):
            self.camera_pos[1] -= 1
        if isDown(KeyboardButton.asciiKey("s")):
            self.camera_pos[1] += 1
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
        player_movement = [0, 0, 0]
        if isDown(KeyboardButton.asciiKey("j")):
            player_movement[0] -= PLAYER_SPEED
        if isDown(KeyboardButton.asciiKey("l")):
            player_movement[0] += PLAYER_SPEED
        if isDown(KeyboardButton.asciiKey("i")):
            player_movement[1] += PLAYER_SPEED
        if isDown(KeyboardButton.asciiKey("k")):
            player_movement[1] -= PLAYER_SPEED
        if isDown(KeyboardButton.asciiKey("u")):
            player_movement[2] += PLAYER_SPEED
        if isDown(KeyboardButton.asciiKey("o")):
            player_movement[2] -= PLAYER_SPEED
        
        self.player.move(*player_movement)

        return Task.cont

    def toggle_light(self):
        self.flashlight_power = 1 - self.flashlight_power
        self.quad_filter.setShaderInput('lightPower', self.flashlight_power)

    def generateGeometry(self, parallelepiped: Parallelepiped, name: str) -> GeomNode:
        # Number of vertices per primitive (triangles)
        nvp = 3

        # OpenGL style
        vertex_format = GeomVertexFormat.getV3n3c4t2()
        vertex_data = GeomVertexData('v_' + name, vertex_format, Geom.UHStatic)

        vertices = parallelepiped.vertices
        vertex_data.setNumRows(len(vertices))

        vertex_writer = GeomVertexWriter(vertex_data, 'vertex')
        texcoord_writer = GeomVertexWriter(vertex_data, 'texcoord')
        color_writer = GeomVertexWriter(vertex_data, 'color')
        normal_writer = GeomVertexWriter(vertex_data, 'normal')

        for vertex in vertices:
            vertex_writer.addData3(*vertex[:nvp])
            texcoord_writer.addData2(*vertex[nvp:nvp + 2])
            color_writer.addData4(*vertex[nvp + 2:nvp + 6])
            normal_writer.addData3(*vertex[nvp + 6:])

        primitive = GeomTriangles(Geom.UHStatic)

        for _ in range(len(vertices) // nvp):
            primitive.add_next_vertices(nvp)
            primitive.closePrimitive()

        geom = Geom(vertex_data)
        geom.addPrimitive(primitive)

        node = GeomNode(name)
        node.addGeom(geom)

        return node

    def generateLabyrinth(self, parent_node: NodePath, labyrinth_file: str) -> NodePath:
        # Keep track of textures used by the labyrinth's blocks, so we don't have to tell Panda3D to repeatedly load them
        textures = {}

        labyrinth_np = parent_node.attachNewNode('Labyrinth')
        labyrinth = Labyrinth.from_map_file(labyrinth_file)
        labyrinth_walls = [self.generateGeometry(obj, f'wall_{idx}') for idx, obj in enumerate(labyrinth.blocks)]
        print('Number of walls:', len(labyrinth_walls))
        for idx, wall in enumerate(labyrinth_walls):
            wall_obj = labyrinth.blocks[idx]

            wall_node = labyrinth_np.attachNewNode(wall)
            if wall_obj.texture not in textures:
                textures[wall_obj.texture] = self.loader.loadTexture(self.path_p3d / wall_obj.texture)
            wall_node.setTexture(textures[wall_obj.texture])
            wall_node.setPos(wall_obj.position)
            
            if labyrinth.is_window(wall_obj):
                wall_node.setTransparency(True)

            # Collisions
            wall_collider_node = CollisionNode(f"Wall_{idx}")
            # get center of the wall
            wall_center = Point3(wall_obj.width / 2, wall_obj.depth / 2, wall_obj.height / 2)
            wall_collider_node.addSolid(CollisionBox(wall_center,
                                                     wall_obj.width / 2,
                                                     wall_obj.depth / 2,
                                                     wall_obj.height / 2))
            wall_collider = wall_node.attachNewNode(wall_collider_node)
            if SHOW_COLLISIONS:
                wall_collider.show()
        
        # Center the labyrinth to the origin
        labyrinth_np.setPos(
            - labyrinth.width / 2,
            - labyrinth.depth / 2,
            - labyrinth.height / 2,
        )

        return labyrinth_np

    def windowResized(self):
        self.quad_filter.setShaderInput('u_resolution', (self.win.getXSize(), self.win.getYSize()))

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
            lightPower=self.flashlight_power,
        )

        self.accept('aspectRatioChanged', self.windowResized)

    # get mouse position in 3d space
    def calculateMouseProjection(self) -> Tuple[float, float, float]:
        distance = 20
        width = self.win.getProperties().getXSize()
        height = self.win.getProperties().getYSize()
        x_multiplier = width / 110.34482758620689  # 7.25
        y_multiplier = height / 110.091743119  # 5.45
        x_offset = -0.5
        y_offset = -0.5

        if self.mouseWatcherNode.hasMouse():
            x = self.mouseWatcherNode.getMouseX()
            y = self.mouseWatcherNode.getMouseY()
            return x * x_multiplier + x_offset, distance, y * y_multiplier + y_offset

        return 0, distance, 0

    def create3dAxis(self, heads: bool = False):
        axis3d = self.render.attachNewNode('axis3d')

        x_axis = Parallelepiped(10, 0.1, 0.1, color=(1, 0, 0, 1))
        y_axis = Parallelepiped(0.1, 0.1, 10, color=(0, 1, 0, 1))
        z_axis = Parallelepiped(0.1, 10, 0.1, color=(0, 0, 1, 1))

        axis3d.attach_new_node(self.generateGeometry(x_axis, 'x_axis'))
        axis3d.attach_new_node(self.generateGeometry(y_axis, 'y_axis'))
        axis3d.attach_new_node(self.generateGeometry(z_axis, 'z_axis'))

        if heads:
            x_axis_head = Parallelepiped(0.3, 0.3, 0.3, color=(1, 0, 0, 1))
            y_axis_head = Parallelepiped(0.3, 0.3, 0.3, color=(0, 1, 0, 1))
            z_axis_head = Parallelepiped(0.3, 0.3, 0.3, color=(0, 0, 1, 1))

            x_axis_head_node = axis3d.attach_new_node(self.generateGeometry(x_axis_head, 'x_axis_head'))
            x_axis_head_node.setPos(10, 0, 0)
            y_axis_head_node = axis3d.attach_new_node(self.generateGeometry(y_axis_head, 'y_axis_head'))
            y_axis_head_node.setPos(0, 10, 0)
            z_axis_head_node = axis3d.attach_new_node(self.generateGeometry(z_axis_head, 'z_axis_head'))
            z_axis_head_node.setPos(0, 0, 10)

    def updateMouseProjection(self, task):

        # # Pre inputs flash light
        # target = self.calculateMouseProjection()
        # self.mouse_np.setPos(target)
        # self.flashlight_np.lookAt(target)

        # self.flashlight_np.lookAt(self.table.model)

        # print(target, ' ' * 20, end='\r')

        return Task.cont

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


app = ExplorerApp()
app.setFrameRateMeter(True)
app.run()
