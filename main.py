import math
import os

from typing import List, Tuple
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import *

from CustomObject3D import CustomObject3D
from scene import Object3D, Parallelepiped, Scene

WIDTH = 800
HEIGHT = 600
# to facilitate analysing the model when debugging
MOUSE_CAMERA = False
HELPER_3D_AXIS = True


# TODO: consistent case style? camelCase, snake_case...
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
        table_model = self.loader.loadModel(self.path_p3d / 'models/table-old/o_table_old_01_a.obj')
        table_scale = (0.25, 0.25, 0.25)
        table_position = (0, 40, 0)

        self.table = CustomObject3D(table_model, table_position, table_scale, self.render)

        # OpenGL style coloring
        wall_texture = self.loader.loadTexture(self.path_p3d / 'textures/wall.png')
        # self.wall_0 = self.render.attachNewNode(
        #     self.generateGeometry(Parallelepiped(3, 1, 3, (1.0, 1.0, 1.0, 1.0)), 'parallelepiped_0'))
        # self.wall_0.setTexture(texture_wall)
        self.labyrinth = self.render.attachNewNode('Labyrinth')
        labyrinth_scene = Scene.from_map_file('test2.map')
        labyrinth_walls = [self.generateGeometry(obj, f'wall_{idx}') for idx, obj in enumerate(labyrinth_scene.objects)]
        print('Number of walls:', len(labyrinth_walls))
        for idx, wall in enumerate(labyrinth_walls):
            wall_obj = labyrinth_scene.objects[idx]

            wall_node = self.labyrinth.attachNewNode(wall)
            wall_node.setTexture(wall_texture)
            wall_node.setPos(wall_obj.get_pos())

        # Lighting
        self.flashlight_pos = [0, 10, 0]
        self.flashlight = Spotlight('flashlight')
        self.flashlight.setColor((1, 1, 1, 1))
        lens = PerspectiveLens()
        self.flashlight.setLens(lens)

        self.flashlight_np = self.render.attachNewNode(self.flashlight)
        self.flashlight_np.setPos(0, 10, 0)
        self.flashlight_np.lookAt(self.table.model)
        self.render.setLight(self.flashlight_np)

        flashlight_cube = self.generateGeometry(Parallelepiped(2, 2, 2), 'flashlight')
        self.flashlight_np.attachNewNode(flashlight_cube)

        # mouse_projection = self.calculateMouseProjection()
        # self.mouse_np = self.render.attachNewNode(self.generateGeometry(Parallelepiped(1, 1, 1), 'mouse'))
        # self.mouse_np.setPos(*mouse_projection)

        # Create Ambient Light
        ambient_light_intensity = 0.3
        ambient_light = AmbientLight('ambient_light')
        ambient_light.setColor((ambient_light_intensity, ambient_light_intensity, ambient_light_intensity, 1))
        ambient_light_np = self.render.attachNewNode(ambient_light)
        self.render.setLight(ambient_light_np)


        # self.render.setShaderInput()

        # self.taskMgr.add(self.updateMouseProjection, 'updateMouseProjection')
        self.taskMgr.add(self.read_inputs_task, 'read_inputs_task')
        if not MOUSE_CAMERA:
            self.taskMgr.add(self.move_camera_task, 'move_camera_task')
        self.taskMgr.add(self.move_flashlight_task, 'move_flashlight_task')

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

        return Task.cont

    def generateGeometry(self, object3d: Object3D, name: str) -> GeomNode:
        # Number of vertices per primitive (triangles)
        nvp = 3

        vertex_format = object3d.get_vertex_format()
        vertex_data = GeomVertexData('v_' + name, vertex_format, Geom.UHStatic)

        vertices = object3d.get_vertices()
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

    def create3dAxis(self, heads: bool=False):
        axis3d = self.render.attachNewNode('axis3d')

        x_axis = Parallelepiped(10, 0.1, 0.1, color=(1, 0, 0, 1))
        y_axis = Parallelepiped(0.1, 0.1, 10, color=(0, 1, 0, 1))
        z_axis = Parallelepiped(0.1, 10, 0.1, color=(0, 0, 1, 1))

        axis3d.attach_new_node( self.generateGeometry(x_axis, 'x_axis') )
        axis3d.attach_new_node( self.generateGeometry(y_axis, 'y_axis') )
        axis3d.attach_new_node( self.generateGeometry(z_axis, 'z_axis') )

        if heads:

            x_axis_head = Parallelepiped(0.3, 0.3, 0.3, color=(1, 0, 0, 1))
            y_axis_head = Parallelepiped(0.3, 0.3, 0.3, color=(0, 1, 0, 1))
            z_axis_head = Parallelepiped(0.3, 0.3, 0.3, color=(0, 0, 1, 1))

            x_axis_head_node = axis3d.attach_new_node( self.generateGeometry(x_axis_head, 'x_axis_head') )
            x_axis_head_node.setPos(10, 0, 0)
            y_axis_head_node = axis3d.attach_new_node( self.generateGeometry(y_axis_head, 'y_axis_head') )
            y_axis_head_node.setPos(0, 10, 0)
            z_axis_head_node = axis3d.attach_new_node( self.generateGeometry(z_axis_head, 'z_axis_head') )
            z_axis_head_node.setPos(0, 0, 10)

    def updateMouseProjection(self, task):

        # # Pre inputs flash light
        # target = self.calculateMouseProjection()
        # self.mouse_np.setPos(target)
        # self.flashlight_np.lookAt(target)

        # self.flashlight_np.lookAt(self.table.model)

        # print(target, ' ' * 20, end='\r')

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

        self.camera.lookAt(self.labyrinth)
        return Task.cont

    def move_flashlight_task(self, task):
        self.flashlight_np.setPos(*self.flashlight_pos)
        self.flashlight_np.lookAt(self.labyrinth)
        return Task.cont


app = ExplorerApp()
app.run()
