import os

from typing import Tuple
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import Filename, GeomVertexData, GeomVertexFormat, Geom, GeomVertexWriter, GeomTriangles, GeomNode, \
    Spotlight, PerspectiveLens, WindowProperties

from scene import Object3D, Parallelepiped

WIDTH = 800
HEIGHT = 600

class ExplorerApp(ShowBase):

    def __init__(self):
        ShowBase.__init__(self)

        # set window size
        props = WindowProperties()
        props.setSize(WIDTH, HEIGHT)
        self.win.requestProperties(props)



        self.path = os.path.dirname(os.path.abspath(__file__))
        self.path_p3d = Filename.fromOsSpecific(self.path)

        self.disableMouse()

        # Load the environment model
        self.table = self.loader.loadModel(self.path_p3d / 'models/table-old/o_table_old_01_a.obj')
        # Reparent the model to render
        self.table.reparentTo(self.render)
        # Apply scale and position transforms on the model
        self.table.setScale(0.25, 0.25, 0.25)
        self.table.setPos(0, 40, 0)

        # OpenGL style coloring
        self.scene_vertex_format = GeomVertexFormat.getV3c4t2()
        texture_wall = self.loader.loadTexture(self.path_p3d / 'textures/wall.png')
        self.wall_0 = self.render.attachNewNode(
            self.generateGeometry(Parallelepiped(3, 1, 3, (1.0, 1.0, 1.0, 1.0)), 'parallelepiped_0'))
        self.wall_0.setTexture(texture_wall)

        # Lighting
        self.flashlight = Spotlight('flashlight')
        self.flashlight.setColor((1, 1, 1, 1))
        lens = PerspectiveLens()
        self.flashlight.setLens(lens)

        self.flashlight_np = self.render.attachNewNode(self.flashlight)
        self.flashlight_np.setPos(0, 10, 0)
        self.flashlight_np.lookAt(self.table)
        self.render.setLight(self.flashlight_np)

        flashlight_cube = self.generateGeometry(Parallelepiped(2, 2, 2), 'flashlight')
        self.flashlight_np.attachNewNode(flashlight_cube)

        mouse_projection = self.calculateMouseProjection()
        self.mouse_np = self.render.attachNewNode(self.generateGeometry(Parallelepiped(1, 1, 1), 'mouse'))
        self.mouse_np.setPos(*mouse_projection)

        # self.render.setShaderInput()

        self.taskMgr.add(self.updateMouseProjection, 'updateMouseProjection')

    def generateGeometry(self, object3d: Object3D, name: str) -> GeomNode:
        # Number of vertices per primitive (triangles)
        nvp = 3

        vertex_data = GeomVertexData('v_' + name, self.scene_vertex_format, Geom.UHStatic)

        vertices = object3d.get_vertices()
        vertex_data.setNumRows(len(vertices))

        vertex_writer = GeomVertexWriter(vertex_data, 'vertex')
        texcoord_writer = GeomVertexWriter(vertex_data, 'texcoord')
        color_writer = GeomVertexWriter(vertex_data, 'color')

        for vertex in vertices:
            vertex_writer.addData3(*vertex[:nvp])
            texcoord_writer.addData2(*vertex[nvp:nvp + 2])
            color_writer.addData4(*vertex[nvp + 2:])

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
        x_multiplier = width / 110.34482758620689 # 7.25
        y_multiplier = height / 110.091743119 # 5.45
        x_offset = -0.5
        y_offset = -0.5

        if self.mouseWatcherNode.hasMouse():
            x = self.mouseWatcherNode.getMouseX()
            y = self.mouseWatcherNode.getMouseY()
            return x * x_multiplier + x_offset, distance, y * y_multiplier + y_offset

        return 0, distance, 0

    def updateMouseProjection(self, task):
        target = self.calculateMouseProjection()
        # target = -9, 20, 0
        self.mouse_np.setPos(target)
        self.flashlight_np.lookAt(target)

        print(target, ' ' * 20, end='\r')

        return Task.cont


app = ExplorerApp()
app.run()
