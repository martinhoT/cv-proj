import os

from math import pi, sin, cos
from typing import Tuple
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import Filename, GeomVertexData, GeomVertexFormat, Geom, GeomVertexWriter, GeomTriangles, GeomNode, Spotlight, PerspectiveLens

from scene import Object3D, Parallelepiped


class ExplorerApp(ShowBase):

    def __init__(self):
            ShowBase.__init__(self)

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
            self.wall_0 = self.render.attachNewNode(self.generateGeometry(Parallelepiped(3, 1, 3, (1.0, 1.0, 1.0, 1.0)), 'parallelepiped_0') )
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
            self.mouse_np = self.render.attachNewNode(self.generateGeometry(Parallelepiped(1, 1, 1), 'mouse') )
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
            texcoord_writer.addData2(*vertex[nvp:nvp+2])
            color_writer.addData4(*vertex[nvp+2:])
        
        primitive = GeomTriangles(Geom.UHStatic)

        for _ in range(len(vertices) // nvp):
            primitive.add_next_vertices(nvp)
            primitive.closePrimitive()

        geom = Geom(vertex_data)
        geom.addPrimitive(primitive)

        node = GeomNode(name)
        node.addGeom(geom)

        return node


    def calculateMouseProjection(self) -> Tuple[float, float, float]:
        if self.mouseWatcherNode.hasMouse():
            x = self.mouseWatcherNode.getMouseX() * 10
            y = self.mouseWatcherNode.getMouseY() * 8
        else:
            x, y = 0, 0

        return x, 20, y

    
    def updateMouseProjection(self, task):
        target = self.calculateMouseProjection()
        self.mouse_np.setPos(target)
        self.flashlight_np.lookAt(target)

        print(target, ' '*20, end='\r')

        return Task.cont



app = ExplorerApp()
app.run()