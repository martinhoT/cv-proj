import numpy as np

from typing import Tuple, List
from dataclasses import dataclass



DEBUG = True

@dataclass(frozen=True)
class Labyrinth:
    blocks:     List['Parallelepiped']
    width:      float
    height:     float
    depth:      float


    TEXTURE_WALL = 'textures/wall.png'
    TEXTURE_WINDOW = 'textures/glass.png'

    NODE_WALL_H = '-'
    NODE_WALL_V = '|'
    NODE_WINDOW_H = '_'
    NODE_WINDOW_V = '!'
    NODE_PILLAR = '+'
    NODE_FLOOR = '.'
    NODE_EMPTY = ' '
    NODE_HOLE = 'X'
    NODE_START = 'S'
    NODE_FINISH = 'F'

    NODES_WALL = {NODE_WALL_H, NODE_WALL_V}
    NODES_WINDOW = {NODE_WINDOW_H, NODE_WINDOW_V}
    NODES_H = {NODE_WALL_H, NODE_WINDOW_H}
    NODES_V = {NODE_WALL_V, NODE_WINDOW_V}

    DIMS_FLOOR_HEIGHT = 1
    DIMS_WALL_LENGTH = 5
    DIMS_WALL_HEIGHT = 5
    DIMS_WALL_THIN = 1

    ATTRIBUTES_WALL_H = {
        'width': DIMS_WALL_LENGTH,
        'height': DIMS_FLOOR_HEIGHT + DIMS_WALL_HEIGHT,
        'depth': DIMS_WALL_THIN,
    }
    ATTRIBUTES_WALL_V = {
        'width': DIMS_WALL_THIN,
        'height': DIMS_FLOOR_HEIGHT + DIMS_WALL_HEIGHT,
        'depth': DIMS_WALL_LENGTH,
    }
    ATTRIBUTES_PILLAR = {
        'width': DIMS_WALL_THIN,
        'height': DIMS_FLOOR_HEIGHT + DIMS_WALL_HEIGHT,
        'depth': DIMS_WALL_THIN,
    }
    ATTRIBUTES_FLOOR_MIDDLE = {
        'width': DIMS_WALL_LENGTH,
        'height': DIMS_FLOOR_HEIGHT,
        'depth': DIMS_WALL_LENGTH,
    }
    ATTRIBUTES_FLOOR_WALL_H = {
        'width': DIMS_WALL_LENGTH,
        'height': DIMS_FLOOR_HEIGHT,
        'depth': DIMS_WALL_THIN,
    }
    ATTRIBUTES_FLOOR_WALL_V = {
        'width': DIMS_WALL_THIN,
        'height': DIMS_FLOOR_HEIGHT,
        'depth': DIMS_WALL_LENGTH,
    }
    ATTRIBUTES_FLOOR_PILLAR = {
        'width': DIMS_WALL_THIN,
        'height': DIMS_FLOOR_HEIGHT,
        'depth': DIMS_WALL_THIN,
    }


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

        labyrinth_width = cls.DIMS_WALL_THIN + width_units * (cls.DIMS_WALL_THIN + cls.DIMS_WALL_LENGTH)
        labyrinth_height = cls.DIMS_FLOOR_HEIGHT + len(floor_layouts) * (cls.DIMS_FLOOR_HEIGHT + cls.DIMS_WALL_HEIGHT)
        labyrinth_depth = cls.DIMS_WALL_THIN + depth_units * (cls.DIMS_WALL_THIN + cls.DIMS_WALL_LENGTH)

        if DEBUG:
            floor_color = (1.0, 0.0, 0.0, 1.0)
            wall_color = (0.0, 1.0, 0.0, 1.0)
            pillar_color = (0.0, 0.0, 1.0, 1.0)
        else:
            floor_color = (1.0, 1.0, 1.0, 1.0)
            wall_color = (1.0, 1.0, 1.0, 1.0)
            pillar_color = (1.0, 1.0, 1.0, 1.0)

        get_position = lambda x, y, floor: (
            (x % 2) * cls.DIMS_WALL_THIN + (x // 2) * (cls.DIMS_WALL_LENGTH + cls.DIMS_WALL_THIN),   # X
            (y % 2) * cls.DIMS_WALL_THIN + (y // 2) * (cls.DIMS_WALL_LENGTH + cls.DIMS_WALL_THIN),   # Y
            floor * (cls.DIMS_WALL_HEIGHT + cls.DIMS_FLOOR_HEIGHT)                                   # Z
        )

        previous_layout = []
        for idx, floor_layout in enumerate(floor_layouts):
            for y_idx, row in enumerate(floor_layout):
                for x_idx, object_type in enumerate(row):
                    block_kwargs = None

                    # Horizontal wall
                    if object_type in cls.NODES_H:
                        block_kwargs = {
                            **cls.ATTRIBUTES_WALL_H,
                            'color': wall_color,
                        }

                    # Vertical wall
                    elif object_type in cls.NODES_V:
                        block_kwargs = {
                            **cls.ATTRIBUTES_WALL_V,
                            'color': wall_color,
                        }

                    # Pillar
                    elif object_type == cls.NODE_PILLAR:
                        block_kwargs = {
                            **cls.ATTRIBUTES_PILLAR,
                            'color': pillar_color,
                        }
                    
                    # Floor
                    elif object_type == cls.NODE_FLOOR \
                            or (object_type != cls.NODE_HOLE and previous_layout and previous_layout[y_idx][x_idx] != cls.NODE_EMPTY):
                        
                        # Middle floor
                        if (x_idx % 2) == 1 and (y_idx % 2) == 1:
                            block_kwargs = cls.ATTRIBUTES_FLOOR_MIDDLE.copy()

                        # Horizontal floor
                        elif (x_idx % 2) == 1:
                            block_kwargs = cls.ATTRIBUTES_FLOOR_WALL_H.copy()

                        # Vertical floor
                        elif (y_idx % 2) == 1:
                            block_kwargs = cls.ATTRIBUTES_FLOOR_WALL_V.copy()

                        # Pillar floor
                        else:
                            block_kwargs = cls.ATTRIBUTES_FLOOR_PILLAR.copy()

                        block_kwargs['color'] = floor_color
                    
                    if block_kwargs:
                        position = get_position(x_idx, y_idx, idx)
                        block_kwargs['position'] = position
                        if object_type in cls.NODES_WINDOW:
                            block_kwargs['texture'] = cls.TEXTURE_WINDOW

                            # Add an extra floor block below the window to look better
                            attrs = cls.ATTRIBUTES_FLOOR_WALL_H if object_type == cls.NODE_WINDOW_H else cls.ATTRIBUTES_FLOOR_WALL_V
                            base_floor_kwargs = {
                                **attrs,
                                'color': floor_color,
                                'position': position,
                                'texture': cls.TEXTURE_WALL,
                                'tiling_factors': (1.0, 0.5),
                            }
                            blocks.append( Parallelepiped(**base_floor_kwargs) )

                            # Account for the fact that there is now floor below
                            block_kwargs['height'] -= cls.DIMS_FLOOR_HEIGHT
                            block_kwargs['position'] = (position[0], position[1], position[2] + cls.DIMS_FLOOR_HEIGHT)
                        else:
                            block_kwargs['texture'] = cls.TEXTURE_WALL
                            block_kwargs['tiling_factors'] = (1.0, 0.5)
                        blocks.append( Parallelepiped(**block_kwargs) )

            previous_layout = floor_layout
        
        # Roof
        for y_idx, row in enumerate(previous_layout):
            for x_idx, object_type in enumerate(row):
                block_kwargs = None

                # Floor
                if object_type != cls.NODE_EMPTY:
                   
                    # Middle floor
                    if (x_idx % 2) == 1 and (y_idx % 2) == 1:
                        block_kwargs = cls.ATTRIBUTES_FLOOR_MIDDLE.copy()

                    # Horizontal floor
                    elif (x_idx % 2) == 1:
                        block_kwargs = cls.ATTRIBUTES_FLOOR_WALL_H.copy()

                    # Vertical floor
                    elif (y_idx % 2) == 1:
                        block_kwargs = cls.ATTRIBUTES_FLOOR_WALL_V.copy()

                    # Pillar floor
                    else:
                        block_kwargs = cls.ATTRIBUTES_FLOOR_PILLAR.copy()

                    block_kwargs['color'] = floor_color
                
                if block_kwargs:
                    block_kwargs['position'] = get_position(x_idx, y_idx, idx)
                    block_kwargs['texture'] = cls.TEXTURE_WALL
                    block_kwargs['tiling_factors'] = (1.0, 0.5)
                    blocks.append( Parallelepiped(**block_kwargs) )

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


    # TODO: A rather lazy way to determine this...
    def is_window(self, obj: 'Parallelepiped') -> bool:
        return obj.texture == self.TEXTURE_WINDOW



@dataclass(init=False, frozen=True)
class Parallelepiped:
    width:      float
    height:     float
    depth:      float
    vertices:   np.ndarray
    position:   Tuple[float, float, float]
    texture:    str


    def __init__(self, width: float, height: float, depth: float,
                color: Tuple[float, float, float, float]=(1.0, 1.0, 1.0, 1.0),
                tiling_factors: Tuple[float, float]=None,
                position: Tuple[float, float, float]=None,
                texture: str=None):

        # Required, since it's frozen...
        object.__setattr__(self, 'height', height)
        object.__setattr__(self, 'width', width)
        object.__setattr__(self, 'depth', depth)

        r, g, b, a = color
        # Panda3D uses the geographical coordinate system, where XY is on the floor and Z is the height
        # (https://docs.panda3d.org/1.10/python/introduction/tutorial/loading-the-grassy-scenery)
        x, y, z = width, depth, height
        
        # Determine how textures should be tiled.
        # If the tiling factors are not specified, then the whole texture is mapped to the face.
        # Otherwise, the UVs are a factor of the object's dimensions.
        if tiling_factors is not None:
            u, v = tiling_factors
            ux, uy = u*x, u*y
            vy, vz = v*y, v*z
        else:
            ux, uy = 1, 1
            vy, vz = 1, 1

        # Clockwise order
        vertices = np.array([
            # BOTTOM
            [0, 0, 0,  0,  0],
            [0, y, 0,  0, vy],
            [x, y, 0, ux, vy],

            [0, 0, 0,  0,  0],
            [x, y, 0, ux, vy],
            [x, 0, 0, ux,  0],

            # TOP
            [0, 0, z, ux,  0],
            [x, y, z,  0, vy],
            [0, y, z, ux, vy],

            [0, 0, z, ux,  0],
            [x, 0, z,  0,  0],
            [x, y, z,  0, vy],

            # LEFT
            [0, y, z,  0, vz],
            [0, y, 0,  0,  0],
            [0, 0, z, uy, vz],

            [0, y, 0,  0,  0],
            [0, 0, 0, uy,  0],
            [0, 0, z, uy, vz],

            # RIGHT
            [x, 0, z,  0, vz],
            [x, y, 0, uy,  0],
            [x, y, z, uy, vz],

            [x, 0, z,  0, vz],
            [x, 0, 0,  0,  0],
            [x, y, 0, uy,  0],

            # BACK
            [0, y, z,  0, vz],
            [x, y, z, ux, vz],
            [0, y, 0,  0,  0],

            [x, y, z, ux, vz],
            [x, y, 0, ux,  0],
            [0, y, 0,  0,  0],

            # FRONT
            [0, 0, 0,  0, vz],
            [x, 0, z, ux,  0],
            [0, 0, z,  0,  0],

            [0, 0, 0,  0, vz],
            [x, 0, 0, ux, vz],
            [x, 0, z, ux,  0],
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
        object.__setattr__(self, 'texture', texture)
    


if __name__ == '__main__':
    scene = Labyrinth.from_map_string('test1.map')