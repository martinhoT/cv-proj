from panda3d.core import *
import math

from labyrinth import Parallelepiped


def generateGeometry(parallelepiped: Parallelepiped, name: str) -> GeomNode:
    # Number of vertices per primitive (triangles)
    nvp = 3

    # We have to build our own array format, since Panda3D's defaults don't include tangent and binormal vectors which we need for bump mapping
    # https://docs.panda3d.org/1.10/python/programming/internal-structures/geometry-storage/geomvertexformat
    vertex_format_array = GeomVertexArrayFormat()
    vertex_format_array.addColumn('vertex', 3, Geom.NTFloat32, Geom.CPoint)
    vertex_format_array.addColumn('normal', 3, Geom.NTFloat32, Geom.CNormal)
    vertex_format_array.addColumn('color', 4, Geom.NTUint8, Geom.C_color)   # OpenGL color format
    vertex_format_array.addColumn('texcoord', 2, Geom.NTFloat32, Geom.C_texcoord)
    vertex_format_array.addColumn('tangent', 3, Geom.NTFloat32, Geom.C_vector)
    vertex_format_array.addColumn('binormal', 3, Geom.NTFloat32, Geom.C_vector)
    vertex_format = GeomVertexFormat.registerFormat(vertex_format_array)
    vertex_data = GeomVertexData('v_' + name, vertex_format, Geom.UHStatic)

    vertices = parallelepiped.get_vertices()
    vertex_data.setNumRows(len(vertices))

    vertex_writer = GeomVertexWriter(vertex_data, 'vertex')
    texcoord_writer = GeomVertexWriter(vertex_data, 'texcoord')
    color_writer = GeomVertexWriter(vertex_data, 'color')
    normal_writer = GeomVertexWriter(vertex_data, 'normal')
    tangent_writer = GeomVertexWriter(vertex_data, 'tangent')
    binormal_writer = GeomVertexWriter(vertex_data, 'binormal')

    for vertex in vertices:
        vertex_writer.addData3(*vertex[:nvp])
        texcoord_writer.addData2(*vertex[nvp:nvp + 2])
        color_writer.addData4(*vertex[nvp + 2:nvp + 6])
        normal_writer.addData3(*vertex[nvp + 6:nvp + 9])
        tangent_writer.addData3(*vertex[nvp + 9:nvp + 12])
        binormal_writer.addData3(*vertex[nvp + 12:])

    primitive = GeomTriangles(Geom.UHStatic)

    for _ in range(len(vertices) // nvp):
        primitive.add_next_vertices(nvp)
        primitive.closePrimitive()

    geom = Geom(vertex_data)
    geom.addPrimitive(primitive)

    node = GeomNode(name)
    node.addGeom(geom)

    return node


def update_orthographic_lens(camera_orthographic_lens, windowX: int, windowY: int):
    """Set the orthographic lens' parameters with respect to the window size."""
    camera_orthographic_lens.setFilmSize(30 * max(windowX / windowY, 1))   # Why? no clue
    camera_orthographic_lens.setAspectRatio(windowX / windowY)
    
    
def move_camera(camera, camera_zoom, camera_angle, camera_focus=(0, 0, 0), grass_height=-10, 
                grass_treshold=-5, labyrinth_boundaries=None):
    
    camera_pos_radians = math.radians(camera_angle[1])
    multiplier = camera_zoom * math.sin(camera_pos_radians)
    
    grass_limit = grass_height + grass_treshold
    
    angle_x_degrees = camera_angle[0]
    angle_y_degrees = camera_angle[1] 
    angle_x_radians = angle_x_degrees * (math.pi / 180.0)
    angle_y_radians = angle_y_degrees * (math.pi / 180.0)

    new_pos = (
        math.sin(angle_x_radians) * camera_zoom + camera_focus[0],
        -math.cos(angle_x_radians) * camera_zoom * -math.cos(angle_y_radians) + camera_focus[1],
        (math.sin(angle_y_radians) * camera_zoom + camera_focus[2])
    )
    
    if labyrinth_boundaries is not None:
        if -labyrinth_boundaries[0] < new_pos[0] < labyrinth_boundaries[0] and \
           -labyrinth_boundaries[1] < new_pos[1] < labyrinth_boundaries[1] and \
           -labyrinth_boundaries[2] < new_pos[2] < labyrinth_boundaries[2]:

            return False
    
    if multiplier < grass_limit: 
        return False
    

    camera.setPos(*new_pos)
    camera.lookAt(camera_focus)
    return True
