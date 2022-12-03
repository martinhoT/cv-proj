import numpy as np

from typing import Tuple, List
from dataclasses import dataclass
from panda3d.core import GeomVertexFormat



DEBUG = True

@dataclass(frozen=True)
class Labyrinth:
    blocks:     List['Parallelepiped']
    width:      float
    height:     float
    depth:      float


    @classmethod
    def from_map_string(cls, map_str: str) -> 'Labyrinth':
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
        
        # Width and depth of each floor in terms of the number of tiles
        width_units, depth_units = None, None
        for floor_layout in floor_layouts:

            floor_width = (len(floor_layout[0]) - 1) // 2
            floor_depth = (len(floor_layout) - 1) // 2

            if width_units is None or depth_units is None:
                width_units = floor_width
                depth_units = floor_depth
            elif floor_width != width_units:
                raise ValueError('The width is not consistent among floors!')
            elif floor_depth != depth_units:
                raise ValueError('The depth is not consistent among floors!')
        
        blocks = []

        floor_height = 1
        wall_length = 5
        wall_height = 5
        wall_thin = 1

        labyrinth_width = wall_thin + width_units * (wall_thin + wall_length)
        labyrinth_height = floor_height + len(floor_layouts) * (floor_height + wall_height)
        labyrinth_depth = wall_thin + depth_units * (wall_thin + wall_length)

        if DEBUG:
            floor_color = (1.0, 0.0, 0.0, 1.0)
            wall_color = (0.0, 1.0, 0.0, 1.0)
            pillar_color = (0.0, 0.0, 1.0, 1.0)
        else:
            floor_color = (1.0, 1.0, 1.0, 1.0)
            wall_color = (1.0, 1.0, 1.0, 1.0)
            pillar_color = (1.0, 1.0, 1.0, 1.0)

        previous_layout = []
        for idx, floor_layout in enumerate(floor_layouts):
            for y_idx, row in enumerate(floor_layout):
                for x_idx, object_type in enumerate(row):
                    block_kwargs = None

                    # Horizontal wall
                    if object_type == '-':
                        block_kwargs = {
                            'width': wall_length,
                            'height': floor_height + wall_height,
                            'depth': wall_thin,
                            'color': wall_color,
                        }

                    # Vertical wall
                    elif object_type == '|':
                        block_kwargs = {
                            'width': wall_thin,
                            'height': floor_height + wall_height,
                            'depth': wall_length,
                            'color': wall_color,
                        }

                    # Pillar
                    elif object_type == '+':
                        block_kwargs = {
                            'width': wall_thin,
                            'height': floor_height + wall_height,
                            'depth': wall_thin,
                            'color': pillar_color,
                        }
                    
                    # Floor
                    elif object_type == '.' \
                            or (object_type != 'X' and previous_layout and previous_layout[y_idx][x_idx] != ' '):
                        # Middle floor
                        if (x_idx % 2) == 1 and (y_idx % 2) == 1:
                            block_kwargs = {
                                'width': wall_length,
                                'height': floor_height,
                                'depth': wall_length,
                                'color': floor_color,
                            }
                        # Horizontal floor
                        elif (x_idx % 2) == 1:
                            block_kwargs = {
                                'width': wall_length,
                                'height': floor_height,
                                'depth': wall_thin,
                                'color': floor_color,
                            }
                        # Vertical floor
                        elif (y_idx % 2) == 1:
                            block_kwargs = {
                                'width': wall_thin,
                                'height': floor_height,
                                'depth': wall_length,
                                'color': floor_color,
                            }
                        # Pillar floor
                        else:
                            block_kwargs = {
                                'width': wall_thin,
                                'height': floor_height,
                                'depth': wall_thin,
                                'color': floor_color,
                            }
                    
                    if block_kwargs:
                        x = (x_idx % 2) * wall_thin + (x_idx // 2) * (wall_length + wall_thin)
                        y = (y_idx % 2) * wall_thin + (y_idx // 2) * (wall_length + wall_thin)
                        z = idx * (wall_height + floor_height)
                        blocks.append( Parallelepiped(**block_kwargs, position=(x, y, z)) )

            previous_layout = floor_layout
        
        # Roof
        for y_idx, row in enumerate(previous_layout):
            for x_idx, object_type in enumerate(row):
                block_kwargs = None

                # Floor
                if object_type != ' ':
                    # Middle floor
                    if (x_idx % 2) == 1 and (y_idx % 2) == 1:
                        block_kwargs = {
                            'width': wall_length,
                            'height': floor_height,
                            'depth': wall_length,
                            'color': floor_color,
                        }
                    # Horizontal floor
                    elif (x_idx % 2) == 1:
                        block_kwargs = {
                            'width': wall_length,
                            'height': floor_height,
                            'depth': wall_thin,
                            'color': floor_color,
                        }
                    # Vertical floor
                    elif (y_idx % 2) == 1:
                        block_kwargs = {
                            'width': wall_thin,
                            'height': floor_height,
                            'depth': wall_length,
                            'color': floor_color,
                        }
                    # Pillar floor
                    else:
                        block_kwargs = {
                            'width': wall_thin,
                            'height': floor_height,
                            'depth': wall_thin,
                            'color': floor_color,
                        }
                
                if block_kwargs:
                    x = (x_idx % 2) * wall_thin + (x_idx // 2) * (wall_length + wall_thin)
                    y = (y_idx % 2) * wall_thin + (y_idx // 2) * (wall_length + wall_thin)
                    z = (idx + 1) * (wall_height + floor_height)
                    blocks.append( Parallelepiped(**block_kwargs, position=(x, y, z)) )

        return Labyrinth(
            blocks=blocks,
            width=labyrinth_width,
            height=labyrinth_height,
            depth=labyrinth_depth,
        )


    @classmethod
    def from_map_file(cls, path: str) -> 'Labyrinth':
        content = None
        with open(path, 'rt') as map_file:
            content = map_file.read()

        return Labyrinth.from_map_string(content)



@dataclass(init=False, frozen=True)
class Parallelepiped:
    width:      float
    height:     float
    depth:      float
    vertices:   np.ndarray
    position:   Tuple[float, float, float]


    def __init__(self, width: float, height: float, depth: float,
                color: Tuple[float, float, float, float]=(1.0, 1.0, 1.0, 1.0),
                tiling_factors: Tuple[float, float]=(1.0, 0.5),
                position: Tuple[float, float, float]=None):

        # TODO: eww (required since it's frozen...)
        object.__setattr__(self, 'height', height)
        object.__setattr__(self, 'width', width)
        object.__setattr__(self, 'depth', depth)

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
        # color_cols = np.vstack( [np.repeat([[r_, g_, b_, a_]], 6, axis=0) for r_, g_, b_, a_ in np.linspace([0, 0, 0, 0], [r, g, b, a], 6)] )
        color_cols = np.repeat([[r, g, b, a]], len(vertices), axis=0)
        
        normals = [
            [ 0,  0, -1],   # BOTTOM
            [ 0,  0,  1],   # TOP
            [-1,  0,  0],   # LEFT
            [ 1,  0,  0],   # RIGHT
            [ 0,  1,  0],   # BACK
            [ 0, -1,  0],   # FRONT
        ]
        normal_cols = np.vstack( [np.repeat([normal], 6, axis=0) for normal in normals] )

        object.__setattr__(self, 'vertices', np.hstack([ vertices, color_cols, normal_cols ]))
        object.__setattr__(self, 'position', position)
    


if __name__ == '__main__':
    scene = Labyrinth.from_map_string('test1.map')