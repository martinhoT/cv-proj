import numpy as np

from typing import Tuple, List
from dataclasses import dataclass



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
        # TODO: obtain map dimensions
        width, depth = None, None

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
                width=width,
                height=floor_height,
                depth=depth,
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



    @classmethod
    def from_map_file(cls, path: str) -> 'Scene':
        content = None
        with open(path, 'rt') as map_file:
            content = map_file.read()

        return Scene.from_map_str(content)



class Object3D:

    def get_pos(self) -> Tuple[float, float, float]:
        raise NotImplementedError()

    def get_vertices(self) -> List[List[float]]:
        raise NotImplementedError()


class Parallelepiped(Object3D):

    def __init__(self, width: float, height: float, depth: float, color: Tuple[float, float, float, float]=(1.0, 1.0, 1.0, 1.0), tiling_factors: Tuple[float, float]=(1.0, 0.5)):
        r, g, b, a = color
        w, h, d = width, height, depth
        u, v = tiling_factors

        # Clockwise order (?)
        vertices = np.array([
            # FRONT
            [0, 0, 0, 0,    0],
            [0, h, 0, 0,    v*h],
            [w, h, 0, u*w,  v*h],

            [0, 0, 0, 0,    0],
            [w, h, 0, u*w,  v*h],
            [w, 0, 0, u*w,  0],

            # BACK
            [0, 0, d, u*w,  0],
            [w, h, d, 0,    v*h],
            [0, h, d, u*w,  v*h],

            [0, 0, d, u*w,  0],
            [w, 0, d, 0,    0],
            [w, h, d, 0,    v*h],

            # LEFT
            [0, h, d, 0,    v*h],
            [0, h, 0, u*d,  v*h],
            [0, 0, d, 0,    0],

            [0, h, 0, u*d,  v*h],
            [0, 0, 0, u*d,  0],
            [0, 0, d, 0,    0],

            # RIGHT
            [w, 0, d, u*d,  0],
            [w, h, 0, 0,    v*h],
            [w, h, d, u*d,  v*h],

            [w, 0, d, u*d,  0],
            [w, 0, 0, 0,    0],
            [w, h, 0, 0,    v*h],

            # TOP
            [0, h, d, 0,    v*d],
            [w, h, d, u*w,  v*d],
            [0, h, 0, 0,    0],

            [w, h, d, u*w,  v*d],
            [w, h, 0, u*w,  0],
            [0, h, 0, 0,    0],

            # BOTTOM
            [0, 0, 0, 0,    v*d],
            [w, 0, d, u*w,  0],
            [0, 0, d, 0,    0],

            [0, 0, 0, 0,    v*d],
            [w, 0, 0, u*w,  v*d],
            [w, 0, d, u*w,  0],
        ], 'f')

        # Color each face with a different shade, mainly for debugging
        # color_cols = np.vstack( [np.repeat([[r_, g_, b_, a_]], 6, axis=0) for r_, g_, b_, a_ in np.linspace([0, 0, 0, 0], [r, g, b, a], 6)] )
        color_cols = np.repeat([[r, g, b, a]], len(vertices), axis=0)
        
        self.vertices = np.hstack([ vertices, color_cols ])
        self.pos = None
        
    
    def set_pos(self, pos: Tuple[float, float, float]):
        self.pos = pos


    def get_pos(self) -> Tuple[float, float, float]:
        return self.pos


    def get_vertices(self) -> List[List[float]]:
        return self.vertices



if __name__ == '__main__':
    scene = Scene.from_map_string('test1.map')