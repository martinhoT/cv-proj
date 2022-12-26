import copy
import numpy as np

from typing import Any, Callable, Dict, Tuple, List, Union
from dataclasses import dataclass



TEXTURE_WALL = 'textures/wall.png'
TEXTURE_WALL_TILING_FACTORS = (0.3, 0.15)
TEXTURE_WINDOW = 'textures/glass.png'

@dataclass(frozen=True)
class Labyrinth:
    blocks:         List['LabyrinthBlock']
    width:          float
    height:         float
    depth:          float
    start_pos:      Tuple[float, float, float]
    finish_pos:     Tuple[float, float, float]
    n_floors:       int
    
    # Convenience attributes
    walls:          List['Wall']
    windows:        List['Window']
    floors:         List['Floor']
    pillars:        List['Pillar']



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
    NODES_INSIDE = {NODE_FLOOR, NODE_HOLE, NODE_START}   # Nodes that are inside the labyrinth (not walls, pillars etc.), with walkable space

    DIMS_FLOOR_HEIGHT = 1
    DIMS_WALL_LENGTH = 5
    DIMS_WALL_HEIGHT = 5
    DIMS_WALL_THIN = 1

    ATTRIBUTES_WALL_H = {
        'width': DIMS_WALL_LENGTH,
        'height': DIMS_WALL_HEIGHT,
        'depth': DIMS_WALL_THIN,
    }
    ATTRIBUTES_WALL_V = {
        'width': DIMS_WALL_THIN,
        'height': DIMS_WALL_HEIGHT,
        'depth': DIMS_WALL_LENGTH,
    }
    ATTRIBUTES_PILLAR = {
        'width': DIMS_WALL_THIN,
        'height': DIMS_WALL_HEIGHT,
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
    def from_map_string(cls, map_str: str, debug: bool=False) -> 'Labyrinth':
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

        if debug:
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

        start_pos = None
        finish_pos = None

        previous_layout = []
        for idx, floor_layout in enumerate(floor_layouts):
            for y_idx, row in enumerate(floor_layout):
                for x_idx, object_type in enumerate(row):
                    block = None
                    block_args = {
                        'cell': (x_idx, y_idx),
                        'floor_index': idx,
                    }

                    object_underneath: bool = object_type != cls.NODE_HOLE \
                        and previous_layout and previous_layout[y_idx][x_idx] != cls.NODE_EMPTY

                    if object_type == cls.NODE_WALL_H:
                        block = Wall(**block_args, **cls.ATTRIBUTES_WALL_H, color=wall_color)

                    elif object_type == cls.NODE_WINDOW_H:
                        block = Window(**block_args, **cls.ATTRIBUTES_WALL_H)

                    elif object_type == cls.NODE_WALL_V:
                        block = Wall(**block_args, **cls.ATTRIBUTES_WALL_V, color=wall_color)
                    
                    elif object_type == cls.NODE_WINDOW_V:
                        block = Window(**block_args, **cls.ATTRIBUTES_WALL_V)

                    elif object_type == cls.NODE_PILLAR:
                        block = Pillar(**block_args, **cls.ATTRIBUTES_PILLAR, color=pillar_color)
                    
                    elif object_type == cls.NODE_FLOOR or object_underneath:
                        
                        # Whether or not this is strictly a roof, and so not meant to be a walkable floor
                        block_args['strictly_roof'] = object_type != cls.NODE_FLOOR and object_underneath

                        # Middle floor
                        if (x_idx % 2) == 1 and (y_idx % 2) == 1:
                            block = Floor(**block_args, **cls.ATTRIBUTES_FLOOR_MIDDLE)

                        # Horizontal floor
                        elif (x_idx % 2) == 1:
                            block = Floor(**block_args, **cls.ATTRIBUTES_FLOOR_WALL_H)

                        # Vertical floor
                        elif (y_idx % 2) == 1:
                            block = Floor(**block_args, **cls.ATTRIBUTES_FLOOR_WALL_V)

                        # Pillar floor
                        else:
                            block = Floor(**block_args, **cls.ATTRIBUTES_FLOOR_PILLAR)

                        block.color = floor_color
                    
                    elif object_type == cls.NODE_START:
                        position = get_position(x_idx, y_idx, idx)
                        length_to_center = cls.DIMS_WALL_LENGTH / 2
                        start_pos = (position[0] + length_to_center, position[1] + length_to_center, position[2] + cls.DIMS_FLOOR_HEIGHT)   # not sure why only center Y, but works
                        # Create a floor underneath
                        block = Floor(**block_args, **cls.ATTRIBUTES_FLOOR_MIDDLE, strictly_roof=False, color=floor_color)
                    
                    elif object_type == cls.NODE_FINISH:
                        finish_pos = get_position(x_idx, y_idx, idx)


                    if block is not None:
                        position = get_position(x_idx, y_idx, idx)
                        block.position = position
                        
                        if isinstance(block, Pillar):
                            # Add an extra floor block below
                            blocks.append(Floor(
                                **block_args,
                                **cls.ATTRIBUTES_FLOOR_PILLAR,
                                strictly_roof=False,
                                position=position,
                                color=floor_color,
                            ))

                            # Account for the fact that there is floor below
                            block.position = (position[0], position[1], position[2] + cls.DIMS_FLOOR_HEIGHT)

                        if isinstance(block, Wall):
                            # Add an extra floor block below
                            attrs = cls.ATTRIBUTES_FLOOR_WALL_H if object_type in cls.NODES_H else cls.ATTRIBUTES_FLOOR_WALL_V
                            rampart_block = Floor(
                                **block_args,
                                **attrs,
                                strictly_roof=False,
                                position=position,
                                color=floor_color,
                            )
                            blocks.append(rampart_block)

                            # Account for the fact that there is floor below
                            block.position = (position[0], position[1], position[2] + cls.DIMS_FLOOR_HEIGHT)

                            # Determine which sides of the wall are facing inside the labyrinth
                            block.east_inside  = x_idx < len(row) - 1          and row[x_idx + 1] in cls.NODES_INSIDE
                            block.west_inside  = x_idx > 0                     and row[x_idx - 1] in cls.NODES_INSIDE
                            block.south_inside = y_idx < len(floor_layout) - 1 and floor_layout[y_idx + 1][x_idx] in cls.NODES_INSIDE
                            block.north_inside = y_idx > 0                     and floor_layout[y_idx - 1][x_idx] in cls.NODES_INSIDE

                        blocks.append(block)

            previous_layout = floor_layout
        
        # Roof
        for y_idx, row in enumerate(previous_layout):
            for x_idx, object_type in enumerate(row):
                block = None
                block_args = {
                    'cell': (x_idx, y_idx),
                    'floor_index': idx + 1,
                    'strictly_roof': True,
                }

                # Cover any node with roof
                if object_type != cls.NODE_EMPTY:
                   
                    # Middle floor
                    if (x_idx % 2) == 1 and (y_idx % 2) == 1:
                        block = Floor(**block_args, **cls.ATTRIBUTES_FLOOR_MIDDLE, color=floor_color)

                    # Horizontal floor
                    elif (x_idx % 2) == 1:
                        block = Floor(**block_args, **cls.ATTRIBUTES_FLOOR_WALL_H, color=floor_color)

                    # Vertical floor
                    elif (y_idx % 2) == 1:
                        block = Floor(**block_args, **cls.ATTRIBUTES_FLOOR_WALL_V, color=floor_color)

                    # Pillar floor
                    else:
                        block = Floor(**block_args, **cls.ATTRIBUTES_FLOOR_PILLAR, color=floor_color)
                
                if block is not None:
                    block.position = get_position(x_idx, y_idx, idx + 1)   # evil usage of 'idx' left from the previous loop
                    blocks.append(block)

        # Optimize the blocks, to avoid many unnecessary repetitions
        # TODO: merges may affect other code that expects the labyrinth to be in cells (such as floor positions, or walls for the spiders)
        blocks = cls.merge_blocks(blocks)
        print('Number of blocks:', len(blocks))

        return Labyrinth(
            blocks=blocks,
            width=labyrinth_width,
            height=labyrinth_height,
            depth=labyrinth_depth,
            start_pos=start_pos,
            finish_pos=finish_pos,
            n_floors=idx + 1,
            walls=[block for block in blocks if isinstance(block, Wall)],
            windows=[block for block in blocks if isinstance(block, Window)],
            floors=[block for block in blocks if isinstance(block, Floor)],
            pillars=[block for block in blocks if isinstance(block, Pillar)],
        )


    @classmethod
    def from_map_file(cls, path: str, debug: bool=False) -> 'Labyrinth':
        content = None
        with open(path, 'rt') as map_file:
            content = map_file.read()

        return Labyrinth.from_map_string(content, debug)


    @classmethod
    def merge_blocks(cls, blocks: List['LabyrinthBlock']) -> List['LabyrinthBlock']:
        merged = []

        # Merge the floors
        floors: Dict[int, List[Floor]] = {}
        for block in blocks:
            if isinstance(block, Floor):
                floors.setdefault(block.floor_index, []).append(block)

        merged.extend(cls.merge_horizontal_blocks(floors,
            # they have to be in adjacent cells and have the same attributes
            merge_key=lambda x_block1, x_block0: (x_block1[0] - x_block0[0]) == 1 and x_block1[1].same_attributes(x_block0[1]),
            # get the span of cell x coordinates, and also a model block whose attributes will be used
            merge_method=lambda x_blocks: (set(x for x, block in x_blocks), x_blocks[0][1]),
        ))

        # TODO: it's merging the walls as pillars
        # Merge the walls and pillars
        walls: Dict[int, List[Union[Wall, Pillar]]] = {}
        # for block in blocks:
        #     # Ignore Windows
        #     if type(block) == Wall or type(block) == Pillar:
        #         walls.setdefault(block.floor_index, []).append(block)

        # merged.extend(cls.merge_horizontal_blocks(floors,
        #     # they have to be in adjacent cells and have the same attributes or be a Pillar
        #     merge_key=lambda x_block1, x_block0: (x_block1[0] - x_block0[0]) == 1 and x_block1[1].same_attributes(x_block0[1]),
        #     # get the span of cell x coordinates, and also a model block whose attributes will be used
        #     merge_method=lambda x_blocks: (set(x for x, block in x_blocks), x_blocks[0][1]),
        # ))

        # Don't merge the rest
        for block in blocks:
            floors_to_merge = floors[block.floor_index] if block.floor_index in floors else []
            walls_to_merge = walls[block.floor_index] if block.floor_index in walls else []
            if block not in floors_to_merge and block not in walls_to_merge:
                merged.append(block)

        return merged


    @classmethod
    def merge_horizontal_blocks(cls, blocks_at_floor: Dict[int, List['Parallelepiped']], merge_key, merge_method) -> List['Parallelepiped']:
        merged = []
        for floor, floor_blocks in blocks_at_floor.items():
            # Try to create horizontal strips
            horizontal_strips = []

            horizontal_spans = {}
            for block in floor_blocks:
                x, y = block.cell
                horizontal_spans.setdefault(y, []).append((x, block))

            # Resolve breaks, as there may be holes in the spans
            for y, x_blocks in horizontal_spans.items():
                horizontal_spans[y] = cls.merge_values(
                    values=x_blocks,
                    # sort by the cell x coordinate
                    sort_key=lambda x_block: x_block[0],
                    merge_key=merge_key,
                    merge_method=merge_method,
                )

            # TODO: merge along y but don't accomodate for the holes, forget it
            # TODO: create vertical strips and compare to see which should be used

            for y, x_spans in horizontal_spans.items():
                for x_span, model_block in x_spans:
                    floor_blocks_at_span = [block for block in floor_blocks if block.cell[0] in x_span and block.cell[1] == y]

                    merged_floor = copy.copy(model_block)
                    merged_floor.width = sum(block.width for block in floor_blocks_at_span)
                    merged_floor.position = (min(block.position[0] for block in floor_blocks_at_span), model_block.position[1], model_block.position[2])
                    horizontal_strips.append(merged_floor)

            merged.extend(horizontal_strips)
        
        return merged


    @classmethod
    def merge_values(cls, values: List[Any],
            sort_key: Callable[[Any, Any], bool],
            merge_key: Callable[[Any, Any], bool],
            merge_method: Callable[[List[Any]], Any]) -> List[Any]:
        """
        Merge a continuous stream of values sorted according to `sort_key`.
        Values are considered mergeable according to `merge_key`, and each list of values to merge will be merged according to `merge_method`.
        """
        
        merged = []
        to_merge = []
        prev_v = None
        for v in sorted(values, key=sort_key):
            if prev_v is not None and not merge_key(v, prev_v):
                merged.append(merge_method(to_merge))
                to_merge.clear()
            to_merge.append(v)
            prev_v = v
        
        # Leftover
        merged.append(merge_method(to_merge))

        return merged



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

        self.height = height
        self.width = width
        self.depth = depth
        self.position = position
        self.texture = texture
        self.color = color
        self.tiling_factors = tiling_factors
    
        self._vertices = None


    def generate_vertices(self) -> np.ndarray:
        r, g, b, a = self.color
        # Panda3D uses the geographical coordinate system, where XY is on the floor and Z is the height
        # (https://docs.panda3d.org/1.10/python/introduction/tutorial/loading-the-grassy-scenery)
        x, y, z = self.width, self.depth, self.height
        
        # Determine how textures should be tiled.
        # If the tiling factors are not specified, then the whole texture is mapped to the face.
        # Otherwise, the UVs are a factor of the object's dimensions.
        if self.tiling_factors is not None:
            u, v = self.tiling_factors
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

        # Tangent and binormal vectors are needed for bump mapping: https://discourse.panda3d.org/t/custom-geometry-and-bump-mapping-bts-space/24256/3
        tangents = [
            [ ux,  0,  0],   # BOTTOM
            [-ux,  0,  0],   # TOP
            [ 0, -ux,  0],   # LEFT
            [ 0,  ux,  0],   # RIGHT
            [ ux,  0,  0],   # BACK
            [ ux,  0,  0],   # FRONT
        ]
        tangent_cols = np.vstack( [np.repeat([tangent], 6, axis=0) for tangent in tangents] )

        binormals = [
            [ 0,  uy,  0],   # BOTTOM
            [ 0,  uy,  0],   # TOP
            [ 0,  0,  uy],   # LEFT
            [ 0,  0,  uy],   # RIGHT
            [ 0,  0,  uy],   # BACK
            [ 0,  0,  uy],   # FRONT
        ]
        binormal_cols = np.vstack( [np.repeat([binormal], 6, axis=0) for binormal in binormals] )

        self._vertices = np.hstack([ vertices, color_cols, normal_cols, tangent_cols, binormal_cols ])


    def get_vertices(self) -> np.ndarray:
        if self._vertices is None:
            self.generate_vertices()
        return self._vertices
    

class LabyrinthBlock(Parallelepiped):
    cell:           Tuple[int, int]
    floor_index:    int

    def __init__(self,
            cell: Tuple[int, int],
            floor_index: int,
            *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.cell = cell
        self.floor_index = floor_index


class Floor(LabyrinthBlock):
    strictly_roof:  bool

    def __init__(self,
            strictly_roof: bool,
            *args, **kwargs):

        kwargs.setdefault('tiling_factors', TEXTURE_WALL_TILING_FACTORS)
        kwargs.setdefault('texture', TEXTURE_WALL)

        super().__init__(*args, **kwargs)

        self.strictly_roof = strictly_roof

    def same_attributes(self, other: 'Floor') -> bool:
        return self.strictly_roof == other.strictly_roof


class Wall(LabyrinthBlock):
    east_inside:    bool
    west_inside:    bool
    south_inside:   bool
    north_inside:   bool

    def __init__(self,
            east_inside: bool=False,
            west_inside: bool=False,
            south_inside: bool=False,
            north_inside: bool=False,
            *args, **kwargs):

        kwargs.setdefault('tiling_factors', TEXTURE_WALL_TILING_FACTORS)
        kwargs.setdefault('texture', TEXTURE_WALL)

        super().__init__(*args, **kwargs)
        
        self.east_inside = east_inside
        self.west_inside = west_inside
        self.south_inside = south_inside
        self.north_inside = north_inside
    
    def same_attributes(self, other: 'Wall') -> bool:
        return self.east_inside == other.east_inside \
            and self.west_inside == other.west_inside \
            and self.south_inside == other.south_inside \
            and self.north_inside == other.north_inside


class Pillar(LabyrinthBlock):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('tiling_factors', TEXTURE_WALL_TILING_FACTORS)
        kwargs.setdefault('texture', TEXTURE_WALL)

        super().__init__(*args, **kwargs)


class Window(Wall):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('tiling_factors', None)
        kwargs.setdefault('texture', TEXTURE_WINDOW)

        super().__init__(*args, **kwargs)



if __name__ == '__main__':
    scene = Labyrinth.from_map_string('test1.map')