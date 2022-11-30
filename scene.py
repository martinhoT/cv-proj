import numpy as np

from typing import Tuple, List
from dataclasses import dataclass



@dataclass
class Scene:
    objects:    List['Object3D']


class Object3D:

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
        
    
    def get_vertices(self) -> List[List[float]]:
        return self.vertices
