import numpy as np

from typing import Tuple, List
from dataclasses import dataclass
from panda3d.core import GeomVertexFormat



@dataclass
class Scene:
    objects:    List['Object3D']


    @classmethod
    def from_map_string(cls, map_str: str) -> 'Scene':
        floor_layouts = []
        floor_layout = []
        for line in map_str.splitlines():
            if line:
                floor_layout.append(line)
            
            else:
                if floor_layout:
                    floor_layouts.append(floor_layout.copy())
                    floor_layout.clear()

        # Leftover
        if floor_layout:
            floor_layouts.append(floor_layout.copy())
            floor_layout.clear()
        
        # TODO: check that it's a valid map
        width, depth = None, None
        for floor_layout in floor_layouts:

            floor_width = floor_layout[0].count('+') - 1
            floor_depth = (len(floor_layout) - 1) // 2

            if width is None or depth is None:
                width = floor_width
                depth = floor_depth
            elif floor_width != width:
                raise ValueError('The width is not consistent among floors!')
            elif floor_depth != depth:
                raise ValueError('The depth is not consistent among floors!')

        objects = []
        scene = Scene(objects)

        floor_height = 1
        wall_length = 5
        wall_height = 5
        wall_thin = 1

        for idx, floor_layout in enumerate(floor_layouts):
            floor_objects = []
            
            # TODO: take into account the 'X' tiles
            floor = Parallelepiped(
                width=width*wall_length,
                height=floor_height,
                depth=depth*wall_length,
            )
            floor.set_pos((0, 0, idx * (wall_height + floor_height)))
            floor_objects.append(floor)

            for y, row in enumerate(floor_layout):
                for x, object_type in enumerate(row):
                    if object_type == '-':
                        wall = Parallelepiped(
                            width=wall_length,
                            height=wall_height,
                            depth=wall_thin,
                        )

                    elif object_type == '|':
                        wall = Parallelepiped(
                            width=wall_thin,
                            height=wall_height,
                            depth=wall_length,
                        )

                    else:
                        wall = None
                    
                    if wall:
                        z = floor_height + idx * (wall_height + floor_height)
                        wall.set_pos((x, y, z))
                        floor_objects.append(wall)

            objects.extend(floor_objects)

        return scene


    @classmethod
    def from_map_file(cls, path: str) -> 'Scene':
        content = None
        with open(path, 'rt') as map_file:
            content = map_file.read()

        return Scene.from_map_string(content)



class Object3D:

    def get_vertex_format(self) -> GeomVertexFormat:
        raise NotImplementedError()

    def get_pos(self) -> Tuple[float, float, float]:
        raise NotImplementedError()

    def get_vertices(self) -> List[List[float]]:
        raise NotImplementedError()


class Parallelepiped(Object3D):

    def __init__(self, width: float, height: float, depth: float, color: Tuple[float, float, float, float]=(1.0, 1.0, 1.0, 1.0), tiling_factors: Tuple[float, float]=(1.0, 0.5)):
        r, g, b, a = color
        # Panda3D uses the geographical coordinate system, where XY is on the floor and Z is the height
        # (https://docs.panda3d.org/1.10/python/introduction/tutorial/loading-the-grassy-scenery)
        x, y, z = width, depth, height
        u, v = tiling_factors

        # Clockwise order (?)
        vertices = np.array([
            # BOTTOM
            [0, 0, 0, 0,    0],
            [0, y, 0, 0,    v*y],
            [x, y, 0, u*x,  v*y],

            [0, 0, 0, 0,    0],
            [x, y, 0, u*x,  v*y],
            [x, 0, 0, u*x,  0],

            # TOP
            [0, 0, z, u*x,  0],
            [x, y, z, 0,    v*y],
            [0, y, z, u*x,  v*y],

            [0, 0, z, u*x,  0],
            [x, 0, z, 0,    0],
            [x, y, z, 0,    v*y],

            # LEFT
            [0, y, z, 0,    v*y],
            [0, y, 0, u*z,  v*y],
            [0, 0, z, 0,    0],

            [0, y, 0, u*z,  v*y],
            [0, 0, 0, u*z,  0],
            [0, 0, z, 0,    0],

            # RIGHT
            [x, 0, z, u*z,  0],
            [x, y, 0, 0,    v*y],
            [x, y, z, u*z,  v*y],

            [x, 0, z, u*z,  0],
            [x, 0, 0, 0,    0],
            [x, y, 0, 0,    v*y],

            # BACK
            [0, y, z, 0,    v*z],
            [x, y, z, u*x,  v*z],
            [0, y, 0, 0,    0],

            [x, y, z, u*x,  v*z],
            [x, y, 0, u*x,  0],
            [0, y, 0, 0,    0],

            # FRONT
            [0, 0, 0, 0,    v*z],
            [x, 0, z, u*x,  0],
            [0, 0, z, 0,    0],

            [0, 0, 0, 0,    v*z],
            [x, 0, 0, u*x,  v*z],
            [x, 0, z, u*x,  0],
        ], 'f')

        # Color each face with a different shade, mainly for debugging
        color_cols = np.vstack( [np.repeat([[r_, g_, b_, a_]], 6, axis=0) for r_, g_, b_, a_ in np.linspace([0, 0, 0, 0], [r, g, b, a], 6)] )
        # color_cols = np.repeat([[r, g, b, a]], len(vertices), axis=0)
        
        normals = [
            [ 0,  0, -1],   # BOTTOM
            [ 0,  0,  1],   # TOP
            [-1,  0,  0],   # LEFT
            [ 1,  0,  0],   # RIGHT
            [ 0,  1,  0],   # BACK
            [ 0, -1,  0],   # FRONT
        ]
        normal_cols = np.vstack( [np.repeat([normal], 6, axis=0) for normal in normals] )

        self.vertices = np.hstack([ vertices, color_cols, normal_cols ])
        self.pos = None
        
    
    def set_pos(self, pos: Tuple[float, float, float]):
        self.pos = pos


    def get_pos(self) -> Tuple[float, float, float]:
        return self.pos


    def get_vertices(self) -> List[List[float]]:
        return self.vertices
    

    # TODO: need normals as well
    def get_vertex_format(self) -> GeomVertexFormat:
        return GeomVertexFormat.getV3n3c4t2()



if __name__ == '__main__':
    scene = Scene.from_map_string('test1.map')