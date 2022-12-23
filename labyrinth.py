import copy
from functools import reduce
import numpy as np

from typing import Any, Callable, Dict, Set, Tuple, List
from dataclasses import dataclass



TEXTURE_WALL = 'textures/wall.png'
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
                    
                    elif object_type == cls.NODE_FLOOR \
                            or (object_type != cls.NODE_HOLE and previous_layout and previous_layout[y_idx][x_idx] != cls.NODE_EMPTY):
                        
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
                        block = Floor(**block_args, **cls.ATTRIBUTES_FLOOR_MIDDLE, color=floor_color)
                    
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

        for floor, floor_blocks in floors.items():
            # Just blocks for each Y from which to derive non-trivial attributes, but which are assumed to be the same for all blocks in that row
            row_model_blocks = {block.cell[1]: block for block in floor_blocks}
            
            # Try to create horizontal strips
            horizontal_strips = []

            horizontal_spans = {}
            for block in floor_blocks:
                x, y = block.cell
                horizontal_spans.setdefault(y, []).append(x)

            # Resolve breaks, as there may be holes in the spans
            for y, xs in horizontal_spans.items():
                horizontal_spans[y] = cls.merge_values(
                    values=xs,
                    sort_key=lambda x: x,
                    merge_key=lambda x1, x0: (x1 - x0) == 1,
                    merge_method=lambda lst: set(lst),
                )

            # NOTE: this code is attempting to also merge along the Y axis, but it's not working properly and I don't know how to correctly handle the problem
            # TODO: merge along y but don't accomodate for the holes, forget it
            # def will_merge_consecutive_y_spans(y_spans1: Tuple[int, List[Set[int]]], y_spans0: Tuple[int, List[Set[int]]]) -> bool:
            #     x_spans1 = y_spans1[1]
            #     x_spans0 = y_spans0[1]

            #     return min(x_spans1[0]) == min(x_spans0[0]) and max(x_spans1[-1]) == max(x_spans0[-1])

            # def merge_consecutive_y_spans(y_spans: List[Tuple[int, List[Set[int]]]]) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
            #     x_span_max = ...
            #     x_span_min = ...
            #     x_span_total = set(range(x_span_min, x_span_max + 1))
                
            #     y_holes = [(y, x_span_total - reduce(lambda a, b: a | b, x_spans, set())) for y, x_spans in y_spans]


            # horizontal_strips = cls.merge_values(
            #     values=horizontal_spans.items(),
            #     sort_key=tuple.__le__,
            #     merge_key=will_merge_consecutive_y_spans,
            #     merge_method=merge_consecutive_y_spans,
            # )

            # # Merge the spans along the y axis
            # can_merge = set()
            # prev_span = None
            # for y, x_span in sorted(horizontal_spans.items()):    
            #     if prev_span is not None and can_merge and prev_span != x_span:
            #         print(can_merge)
            #         print(x_span)
            #         min_y = min(can_merge)
            #         horizontal_strips.append(Floor(
            #             width=prev_span[1] - prev_span[0] + cls.DIMS_WALL_THIN,
            #             depth=y - min_y,
            #             position=(prev_span[0], min_y, model_block.position[2]),
            #             height=model_block.height,
            #             index=model_block.index,
            #             color=model_block.color
            #         ))
            #         can_merge.clear()
                
            #     can_merge.add(y)
            #     prev_span = x_span
            
            # # Leftover
            # print(can_merge)
            # y_span = (min(can_merge), max(can_merge))
            # horizontal_strips.append(Floor(
            #     width=x_span[1] - x_span[0] + cls.DIMS_WALL_THIN,
            #     depth=y_span[1] - y_span[0] + cls.DIMS_WALL_THIN,
            #     position=(x_span[0], y_span[0], model_block.position[2]),
            #     height=model_block.height,
            #     index=model_block.index,
            #     color=model_block.color
            # ))

            # TODO: create vertical strips and compare to see which should be used

            for y, x_spans in horizontal_spans.items():
                model_block = row_model_blocks[y]
                for x_span in x_spans:
                    floor_blocks_at_span = [block for block in floor_blocks if block.cell[0] in x_span and block.cell[1] == y]

                    merged_floor = copy.copy(model_block)
                    merged_floor.width = sum(block.width for block in floor_blocks_at_span)
                    merged_floor.position = (min(block.position[0] for block in floor_blocks_at_span), model_block.position[1], model_block.position[2])
                    horizontal_strips.append(merged_floor)

            merged.extend(horizontal_strips)

        # Merge the rest
        for block in blocks:
            if not isinstance(block, Floor):
                merged.append(block)

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

        self._vertices = np.hstack([ vertices, color_cols, normal_cols ])


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

    def __init__(self, 
            *args, **kwargs):

        kwargs.setdefault('tiling_factors', (1.0, 0.5))
        kwargs.setdefault('texture', TEXTURE_WALL)

        super().__init__(*args, **kwargs)


class Wall(LabyrinthBlock):
    east_inside:    bool
    west_inside:    bool
    south_inside:   bool
    north_inside:   bool

    def __init__(self,
            right_inside: bool=False,
            left_inside: bool=False,
            down_inside: bool=False,
            up_inside: bool=False,
            *args, **kwargs):

        kwargs.setdefault('tiling_factors', (1.0, 0.5))
        kwargs.setdefault('texture', TEXTURE_WALL)

        super().__init__(*args, **kwargs)
        
        self.east_inside = right_inside
        self.west_inside = left_inside
        self.south_inside = down_inside
        self.north_inside = up_inside


class Pillar(LabyrinthBlock):

    def __init__(self,
            *args, **kwargs):

        kwargs.setdefault('tiling_factors', (1.0, 0.5))
        kwargs.setdefault('texture', TEXTURE_WALL)

        super().__init__(*args, **kwargs)


class Window(Wall):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('tiling_factors', None)
        kwargs.setdefault('texture', TEXTURE_WINDOW)

        super().__init__(*args, **kwargs)



if __name__ == '__main__':
    scene = Labyrinth.from_map_string('test1.map')