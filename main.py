import os
import time
import argparse
import random

from typing import Dict, Tuple
from direct.showbase.ShowBase import ShowBase
from direct.filter.FilterManager import FilterManager
from direct.task import Task
from panda3d.core import *

from CustomObject3D import CustomObject3D
from Player import Player
from mobs import Bird, Spider, Firefly
from labyrinth import TEXTURE_WALL, Floor, Parallelepiped, Labyrinth, Wall, Window

from common import *
from objects import Table, SpotlightOBJ

WIDTH = 800
HEIGHT = 600
PLAYER_SPEED = 0.25
PLAYER_JUMP_SPEED = 0.35
AMBIENT_LIGHT_INTENSITY = 0.4
DIRECTIONAL_LIGHT_INTENSITY = 0.3
SKY_COLOR = (0.0, 0.0, AMBIENT_LIGHT_INTENSITY)
SPIDER_SPAWN_CHANCE = 0.2
OBJECT_SPAWN_CHANCE = 0.1
CAMERA_SENSIBILITY = 90
ZOOM_SENSIBILITY = 5
ZOOM_INITIAL = 60

PERSPECTIVE_CHANCE = 0.001
PERSPECTIVE_RETURN_CHANCE = 0.05

FLASHLIGHT_POWER = 1
FLASHLIGHT_RADIUS = 0.2
FLASHLIGHT_FLICKER_CHANCE = 0.01
FLASHLIGHT_RETURN_CHANCE = 0.01

LIGHTNING_STRIKE_INTENSITY = 1.0
LIGHTNING_STRIKE_DURATION = 0.05   # in seconds
LIGHTNING_BACKGROUND_SIZE = 500
LIGHTNING_BACKGROUND_POS = (-LIGHTNING_BACKGROUND_SIZE/2, LIGHTNING_BACKGROUND_SIZE, -70)
LIGHTNING_CHANCE = 0.01

IGNORE_RANDOM_EVENTS = True

LABYRINTH_WALL_HEIGHT_TEXTURE_PATH = 'textures/wall_height.png'
LIGHTNING_BACKGROUND_TEXTURE_PATH = 'textures/lightning.png'
GRASS_COLOR_TEXTURE_PATH = 'models/grass/everytexture.com-stock-nature-grass-texture-00004-diffuse.jpg'
GRASS_HEIGHT_TEXTURE_PATH = 'models/grass/everytexture.com-stock-nature-grass-texture-00004-bump.jpg'
GRASS_NORMAL_TEXTURE_PATH = 'models/grass/everytexture.com-stock-nature-grass-texture-00004-normal.jpg'

MOON_PATH = "models/moon/moon2.obj"
MOON_LIGHT_INTENSITY = 0.25
MOON_SELF_LIGHT_INTENSITY = 0.9
GRASS_PATH = "models/grass/grass_bump4.obj"
GRASS_SCALE = 100
GRASS_FOG_DENSITY = 0.0035
GRASS_HEIGHT = -30 #-50

GRASS_LIGHT = True
GRASS_LIGHT_COLOR = (.6, .6, .6, 1)

SPOTLIGHT_SCALE = 0.2
# Enable non-power-of-2 textures. This is relevant for the FilterManager post-processing.
# If power-of-2 textures is enforced, then the code has to deal with the texture padding.
# We want so simplify the shader code so they are disabled. There is already wide support for non-power-of-2 textures (https://discourse.panda3d.org/t/cg-glsl-filtermanager-texpad-x/14694/8)
# Additionally, set the number of bits used for the depth buffer so that the orthographic projection's visual artifacts are reduced
loadPrcFileData('', '''
textures-power-2 none
depth-bits 24
''')


class ExplorerApp(ShowBase):

    labyrinth_block_nodes: Dict[Parallelepiped, NodePath] = {}

    def __init__(self, labyrinth_file: str, debug_opts: dict):
        ShowBase.__init__(self)


        # simplepbr.init()
        self.previous_mouse_pos = None
        self.set_background_color(*SKY_COLOR)

        self.DEBUG_LOG = debug_opts.get('log', False)
        self.DEBUG_MAP = debug_opts.get('map', False)
        self.DEBUG_3D_AXIS = debug_opts.get('3d_axis', False)
        self.DEBUG_COLLISIONS = debug_opts.get('collisions', False)
        self.DEBUG_MOUSE_CAMERA = debug_opts.get('mouse_camera', False)
        self.DEBUG_HIDE_UNLIT = debug_opts.get('hide_unlit', False)

        # set window size
        props = WindowProperties()
        props.setSize(WIDTH, HEIGHT)
        self.win.requestProperties(props)

        # camera variables
        self.camera_pos = [0, 180, 0]
        self.camera_zoom = ZOOM_INITIAL
        self.camera_focus = (0, 0, 0)
        self.camera_perspective_lens = self.cam.node().getLens()
        self.camera_orthographic_lens = OrthographicLens()
        update_orthographic_lens(self.camera_orthographic_lens, WIDTH, HEIGHT, self.camera_zoom)

        self.path = os.path.dirname(os.path.abspath(__file__))
        self.path_p3d = Filename.fromOsSpecific(self.path)
        
        if not self.DEBUG_MOUSE_CAMERA:
            self.disableMouse()

        if self.DEBUG_3D_AXIS:
            self.create3dAxis()

        # Collision stuff
        self.cTrav = CollisionTraverser()
        self.pusher = CollisionHandlerPusher()

        # Load the environment model
        self.labyrinth_np, self.labyrinth = self.generateLabyrinth(
            parent_node=self.render,
            labyrinth_file=labyrinth_file,
        )

        self.init_models()

        # Lighting
        # Create Ambient Light
        ambient_light_intensity = AMBIENT_LIGHT_INTENSITY
        ambient_light = AmbientLight('ambient_light')
        ambient_light.setColor((ambient_light_intensity, ambient_light_intensity, ambient_light_intensity, 1))
        self.ambient_light_np = self.render.attachNewNode(ambient_light)
        self.labyrinth_np.setLight(self.ambient_light_np)
        
        # Create Directional Light
        directional_light = DirectionalLight('directional_light')
        directional_light.setColor((DIRECTIONAL_LIGHT_INTENSITY, DIRECTIONAL_LIGHT_INTENSITY, DIRECTIONAL_LIGHT_INTENSITY, 1))
        directional_light.direction = Vec3(0, 0, -0.5)
        dlnp = self.render.attachNewNode(directional_light)

        for floor in self.labyrinth.floors:
            if floor.strictly_roof:
                self.labyrinth_block_nodes[floor].setLight(dlnp)
        self.bird.model.setLight(dlnp)
        
        self.grass_light = PointLight('plightt')
        self.grass_light.setColor(GRASS_LIGHT_COLOR)
        if GRASS_LIGHT:
            self.grass_lightnp = self.render.attach_new_node(self.grass_light)
            self.grass_lightnp.setPos((0, 0, 0))
        
        grass_fog = Fog('Grass fog')
        grass_fog.setColor(*SKY_COLOR)
        grass_fog.setExpDensity(GRASS_FOG_DENSITY)
        for grass in self.grasses:
            grass.setLight(dlnp)
            if GRASS_LIGHT:
                grass.setLight(self.grass_lightnp)
            grass.setFog(grass_fog)

        # Task management
        self.mouse_coords = [0, 0]
        self.accept('tab', self.change_camera_focus)
        self.taskMgr.add(self.update_mouse_coords_task, 'update_mouse_coords_task')
        self.taskMgr.add(self.read_inputs_task, 'read_inputs_task')

        self.quad_filter = None
        self.flashlight_power = FLASHLIGHT_POWER
        self.flashlight_flicker = 0
        self.start_time = time.time()   # avoid providing extremelly large numbers to the shaders, since GLSL acts funky with those (in sin() for instance), so send time since app launch
        self.setupShaders()

        # inputs
        self.is_light_toogle = False
        self.is_perspective_toogle = False

        self.accept('v', self.toggle_light)
        self.accept('c', self.toggle_perspective)
        self.accept('b', self.lightning_strike)

        self.taskMgr.add(self.generate_random_event, 'generate_random_event')
        self.pusher.addInPattern('%fn-into-%in')
        self.pusher.addOutPattern('%fn-out-%in')
        self.pusher.addAgainPattern('%fn-again-%in')
        
        self.accept("Player-out-Ground", self.player_out_ground)
        self.accept("Player-into-Ground", self.player_hit_ground)
        self.accept("Player-again-Ground", self.player_hit_ground)
        
        # Mouse inputs
        self.is_mouse_holded = False
        self.accept("mouse1", self.left_click)
        self.accept("mouse1-up", self.left_release)
        self.accept("wheel_up", self.on_mouse_wheel, [ZOOM_SENSIBILITY])
        self.accept("wheel_down", self.on_mouse_wheel, [-ZOOM_SENSIBILITY])
          
        self.taskMgr.add(self.update_camera_rotation_task, 'update_camera_rotation_task')

        if GRASS_LIGHT:
            self.taskMgr.add(self.move_grasslight_task, 'move_grasslight_task')
               
    def move_grasslight_task(self, task):
        angle = task.time / 2
        self.grass_lightnp.setPos(100 * math.sin(angle), -100.0 * math.cos(angle), 3)
        return task.cont
        
    def init_models(self):
        player_model: NodePath = self.loader.loadModel(self.path_p3d / 'models/player/amongus_flat.obj')
        for material in player_model.find_all_materials():
            material.set_ambient(material.get_diffuse())
        # rotate player model vertically
        player_model.setHpr(0, 90, 0)
        player_scale = (.5,) * 3
        player_position = self.labyrinth.start_pos if self.labyrinth.start_pos is not None else [self.labyrinth.width / 2, self.labyrinth.depth / 2, self.labyrinth.height]
        # Create collision node
        player_collider_node = CollisionNode("Player")
        
        player_collider_node.addSolid(CollisionCapsule(0, 0, 1, 0, 0, 2, 1))
        player_collider = player_model.attachNewNode(player_collider_node)
        player_collider.setHpr(0, -90, 0)
        if self.DEBUG_COLLISIONS:
            player_collider.show()

        self.player = Player(player_model, player_position, self.labyrinth_np, scale=player_scale)
        self.player_position = player_position
        
        self.pusher.addCollider(player_collider, self.player.model)
        self.cTrav.addCollider(player_collider, self.pusher)
        move_camera(self.camera, self.camera_zoom, self.camera_pos, self.camera_focus)
    
        # create bird
        self.bird = Bird([player_position[0] + 5, player_position[1], player_position[2]], self.labyrinth_np, self)
        
        # create moon
        moon_model = self.loader.loadModel(self.path_p3d / MOON_PATH)
        moon_position = LPoint3(-125, 300, 75)
        moon_scale = [5 for _ in range(3)]
        self.moon = CustomObject3D(moon_model, moon_position, self.render, scale=moon_scale, is_flat=True)
        
        # create ambient light only for the moon
        moon_self_light = AmbientLight('Moon self light')
        moon_self_light.setColor((MOON_SELF_LIGHT_INTENSITY, MOON_SELF_LIGHT_INTENSITY, MOON_SELF_LIGHT_INTENSITY, 1))
        self.moon.model.setLight(self.moon.model.attachNewNode(moon_self_light))
        

        pl = PointLight('plight')
        pl.setColor((MOON_LIGHT_INTENSITY, MOON_LIGHT_INTENSITY, MOON_LIGHT_INTENSITY, 1))
        pn = self.moon.model.attachNewNode(pl)
        # pn.setPos(LPoint3(moon_position[0], 0, 0))
        pn.setPos((0, 0, 0))
        
        self.moon.model.setLight(pn)
        
        # create grass
        self.grasses = []
        
        grass_color_texture = self.loader.loadTexture(self.path_p3d / GRASS_COLOR_TEXTURE_PATH)
        grass_height_texture = self.loader.loadTexture(self.path_p3d / GRASS_HEIGHT_TEXTURE_PATH)
        grass_normal_texture = self.loader.loadTexture(self.path_p3d / GRASS_NORMAL_TEXTURE_PATH)

        for i in range(-10, 10):
            for j in range(-10, 10):
                grass_plane = generateGeometry(Parallelepiped(GRASS_SCALE, 0, GRASS_SCALE), f'grass_{i}x{j}')

                grass = self.labyrinth_np.attachNewNode(grass_plane)
                grass.setPos(i * GRASS_SCALE, j * GRASS_SCALE, GRASS_HEIGHT)

                grass.setTexture(grass_color_texture)

                ts = TextureStage('Grass Height')
                ts.setMode(TextureStage.MHeight)
                grass.setTexture(ts, grass_height_texture)

                ts = TextureStage('Grass Normal')
                ts.setMode(TextureStage.MNormal)
                grass.setTexture(ts, grass_normal_texture)
                
                self.grasses.append(grass)
        
        # create the lightning strike background
        lightning_image = self.loader.loadTexture(self.path_p3d / LIGHTNING_BACKGROUND_TEXTURE_PATH)
        cm = CardMaker('lightning maker')
        cm.set_frame(0, LIGHTNING_BACKGROUND_SIZE, 0, LIGHTNING_BACKGROUND_SIZE * lightning_image.get_y_size() / lightning_image.get_x_size())
        self.lightning_strike_background = self.render.attachNewNode(cm.generate())
        self.lightning_strike_background.setPos(LIGHTNING_BACKGROUND_POS)
        self.lightning_strike_background.setTransparency(True)
        self.lightning_strike_background.hide()
        self.lightning_strike_background.setTexture(lightning_image)

        # create fireflies
        firefly_height = -10
        # self.firefly = Firefly([player_position[0], player_position[1], player_position[2] - firefly_height], 
        #                       self.labyrinth_np, self, rotation_center=[15, 10, firefly_height])
        
        # create spotlight object
        self.spotlight_obj = SpotlightOBJ([player_position[0] - 50, player_position[1] - 50, GRASS_HEIGHT], self.labyrinth_np, self,
                                          scale=[SPOTLIGHT_SCALE for _ in range(3)], look_at=LPoint3(0, 0, 0), grass_height=GRASS_HEIGHT, test=self.render)
    
        self.spotlight_obj.look_at(LPoint3(0, 0, GRASS_HEIGHT))
        
        
    
    def init_objs(self, wall_obj: Wall, labyrinth_np: NodePath):
        spider_scale = [Spider.SCALE * 1 for _ in range(3)]
        table_scale = [0.025 for _ in range(3)]
        table_distance = table_scale[0] * 20
        if wall_obj.east_inside:
            self.spawn_spider(wall_obj.position[0] + wall_obj.width, wall_obj.position[1] + wall_obj.depth / 2, wall_obj.position[2] + wall_obj.height / 2, 90, -90, 0, labyrinth_np, spider_scale, (0,1,1), wall_obj)
            self.spawn_obj(wall_obj.position[0] + wall_obj.width + table_distance, wall_obj.position[1] + wall_obj.depth / 2, wall_obj.position[2], -90, 90, 0, labyrinth_np, table_scale)            

        if wall_obj.west_inside:
            self.spawn_spider(wall_obj.position[0], wall_obj.position[1] + wall_obj.depth / 2, wall_obj.position[2] + wall_obj.height / 2, 90, -90, 0, labyrinth_np, spider_scale, (0,1,1), wall_obj)
            self.spawn_obj(wall_obj.position[0] - table_distance, wall_obj.position[1] + wall_obj.depth / 2, wall_obj.position[2], -90, 90, 0, labyrinth_np, table_scale)

        if wall_obj.south_inside:
            self.spawn_spider(wall_obj.position[0] + wall_obj.width / 2, wall_obj.position[1] + wall_obj.depth, wall_obj.position[2] + wall_obj.height / 2, 0, -90, 0, labyrinth_np, spider_scale, (1,0,1), wall_obj)
            self.spawn_obj(wall_obj.position[0] + wall_obj.width / 2, wall_obj.position[1] + wall_obj.depth + table_distance, wall_obj.position[2], 180, 90, 0, labyrinth_np, table_scale)

        if wall_obj.north_inside:
            self.spawn_spider(wall_obj.position[0] + wall_obj.width / 2, wall_obj.position[1], wall_obj.position[2] + wall_obj.height / 2, 180, -90, 0, labyrinth_np, spider_scale, (1,0,1), wall_obj)
            self.spawn_obj(wall_obj.position[0] + wall_obj.width / 2, wall_obj.position[1] - table_distance, wall_obj.position[2], 0, 90, 0, labyrinth_np, table_scale)

    def spawn_spider(self, x, y, z, h, p, r, labyrinth_np, scale, movement_axis, wall):
        spawn_chance = random.random()
        if spawn_chance < SPIDER_SPAWN_CHANCE:
            spider = Spider([x, y, z], labyrinth_np, self, scale=scale, movement_axis=movement_axis, wall_dimensions=(wall.width, wall.depth, wall.height))
            spider.model.setHpr(h, p, r)

            self.spiders.append(spider)
            return spider
    
    def spawn_obj(self, x, y, z, h, p, r, labyrinth_np, scale):
        spawn_chance = random.random()
        if spawn_chance < OBJECT_SPAWN_CHANCE:
            table = Table([x, y, z], labyrinth_np, self, scale=scale)
            table.model.setHpr(h, p, r)
            
    def player_hit_ground(self, entity):
        is_bellow_player = entity.getSurfacePoint(self.player.model).getY() <= 0
        self.player.velocity[2] = 0
        
        if is_bellow_player:
            if self.DEBUG_LOG: print("Hit ground", entity)
            self.player.is_on_ground = True       
    
    def player_out_ground(self, entity):
        # print("Out of ground", entity)]
        if self.DEBUG_LOG: print("Out of ground")
        self.player.is_on_ground = False
        
    def move_entity(self, entity, direction):
        entity.move(*direction)

    def left_click(self):
        self.is_mouse_holded = True
        
    def left_release(self):
        self.is_mouse_holded = False
    
    def on_mouse_wheel(self, delta):
        new_camera_zoom = self.camera_zoom - delta
        new_camera_zoom = max(new_camera_zoom, 10)
        new_camera_zoom = min(new_camera_zoom, 150)
        
        has_moved = move_camera(self.camera, new_camera_zoom, self.camera_pos, self.camera_focus,
                                grass_height=GRASS_HEIGHT, labyrinth_boundaries=[self.labyrinth.width, self.labyrinth.depth, self.labyrinth.height])
        
        if has_moved: 
            self.camera_zoom = new_camera_zoom
            update_orthographic_lens(self.camera_orthographic_lens, WIDTH, HEIGHT, self.camera_zoom)
            
        
        # Reduce the flashlight radius when the camera is zoomed out, sorta following the inverse square law
        self.quad_filter.setShaderInput('lightRadius', 1 / (self.camera_zoom**2 * (1 / FLASHLIGHT_RADIUS) / ZOOM_INITIAL**2))

    def read_inputs_task(self, task):
        isDown = self.mouseWatcherNode.is_button_down
        MouseWatcher

        #Player
        self.player.velocity[0] = 0
        self.player.velocity[1] = 0
        player_radians = math.radians(self.camera_pos[0])
        player_sin = math.sin(player_radians)
        player_cos = math.cos(player_radians)
        horizontal_idx = 0
        rev_horizontal_idx = 1
        vertical_idx = 1
        rev_vertical_idx = 0
        player_rotation = 0
        had_player_input = False
        
        if isDown(KeyboardButton.asciiKey("a")):
            self.player.velocity[horizontal_idx] -= PLAYER_SPEED * player_cos
            self.player.velocity[rev_horizontal_idx] -= PLAYER_SPEED * player_sin
            player_rotation += 90
            had_player_input = True
        if isDown(KeyboardButton.asciiKey("d")):
            self.player.velocity[horizontal_idx] += PLAYER_SPEED * player_cos 
            self.player.velocity[rev_horizontal_idx] += PLAYER_SPEED * player_sin
            player_rotation -= 90
            had_player_input = True
        if isDown(KeyboardButton.asciiKey("w")):
            self.player.velocity[vertical_idx] += PLAYER_SPEED * player_cos 
            self.player.velocity[rev_vertical_idx] -= PLAYER_SPEED * player_sin
            if player_rotation < 0:
                player_rotation += 45
            elif player_rotation > 0:
                player_rotation -= 45
            had_player_input = True
        if isDown(KeyboardButton.asciiKey("s")):
            self.player.velocity[vertical_idx] -= PLAYER_SPEED * player_cos 
            self.player.velocity[rev_vertical_idx] += PLAYER_SPEED * player_sin
            if player_rotation > 0:
                player_rotation += 45
            elif player_rotation < 0:
                player_rotation -= 45
            else:
                player_rotation = 180
            had_player_input = True

        self.player.rotation = self.camera_pos[0] + player_rotation if had_player_input else self.player.rotation
        
        if isDown(KeyboardButton.space()):
            if self.player.is_on_ground:
                self.player.velocity[2] = PLAYER_JUMP_SPEED
                self.player.is_on_ground = False
        if isDown(KeyboardButton.asciiKey("f")):
            if self.DEBUG_HIDE_UNLIT:
                for np in self.labyrinth_np.children:
                    np.hide()
            self.player.put_light()
        
        # Update entities
        self.player.update()
        
        for spider in self.spiders:
            spider.update()
        
        self.bird.update(task.time)
        # self.firefly.update(task.time)
        self.spotlight_obj.update()

        return Task.cont

    def toggle_light(self):
        self.flashlight_flicker = 1 - self.flashlight_flicker
        self.quad_filter.setShaderInput('lightFlickerRatio', self.flashlight_flicker)

    def toggle_perspective(self):
        if isinstance(self.cam.node().getLens(), PerspectiveLens):
            self.cam.node().setLens(self.camera_orthographic_lens)
            update_orthographic_lens(self.camera_orthographic_lens, WIDTH, HEIGHT, self.camera_zoom)
        else:
            self.cam.node().setLens(self.camera_perspective_lens)

    def lightning_strike(self):
        self.lightning_strike_background.show()
        x_angle = math.radians(self.camera_pos[0])
        self.lightning_strike_background.setPos(
            LIGHTNING_BACKGROUND_POS[0] * math.cos(x_angle) - LIGHTNING_BACKGROUND_POS[1] * math.sin(x_angle),
            LIGHTNING_BACKGROUND_POS[0] * math.sin(x_angle) + LIGHTNING_BACKGROUND_POS[1] * math.cos(x_angle),
            LIGHTNING_BACKGROUND_POS[2]
        )
        self.lightning_strike_background.lookAt(self.cam)
        self.lightning_strike_background.setH(self.lightning_strike_background.getH() + 180)

        self.ambient_light_np.node().setColor((LIGHTNING_STRIKE_INTENSITY, LIGHTNING_STRIKE_INTENSITY, LIGHTNING_STRIKE_INTENSITY, 1))
        self.quad_filter.setShaderInput('lightRadius', 2.0)
        self.quad_filter.setShaderInput('lightFlickerRatio', 0.0)
        self.taskMgr.doMethodLater(LIGHTNING_STRIKE_DURATION, self.lightning_strike_stop, 'Stop lightning strike')

    def lightning_strike_stop(self, task):
        self.lightning_strike_background.hide()
        self.ambient_light_np.node().setColor((AMBIENT_LIGHT_INTENSITY, AMBIENT_LIGHT_INTENSITY, AMBIENT_LIGHT_INTENSITY, 1))
        self.quad_filter.setShaderInput('lightRadius', FLASHLIGHT_RADIUS)
        self.quad_filter.setShaderInput('lightFlickerRatio', self.flashlight_flicker)

        return Task.done

    def generateLabyrinth(self, parent_node: NodePath, labyrinth_file: str) -> Tuple[NodePath, Labyrinth]:
        self.labyrinth_block_nodes.clear()
        # Keep track of textures used by the labyrinth's blocks, so we don't have to tell Panda3D to repeatedly load them
        textures = {
            LABYRINTH_WALL_HEIGHT_TEXTURE_PATH: self.loader.loadTexture(self.path_p3d / LABYRINTH_WALL_HEIGHT_TEXTURE_PATH)
        } 
        self.spiders = []
        labyrinth_np = parent_node.attachNewNode('Labyrinth')
        labyrinth = Labyrinth.from_map_file(labyrinth_file, self.DEBUG_MAP)
        labyrinth_blocks = [(block, generateGeometry(block, f'labyrinth_block_{idx}')) for idx, block in enumerate(labyrinth.blocks)]
        if self.DEBUG_LOG: print('Number of walls:', len(labyrinth_blocks))
        for block, block_geom in labyrinth_blocks:
            block_node = labyrinth_np.attachNewNode(block_geom)
            self.labyrinth_block_nodes[block] = block_node
            
            if block.texture not in textures:
                textures[block.texture] = self.loader.loadTexture(self.path_p3d / block.texture)
            block_node.setTexture(textures[block.texture])
            if block.texture == TEXTURE_WALL:
                ts = TextureStage('Wall Height')
                ts.setMode(TextureStage.MHeight)
                block_node.setTexture(ts, textures[LABYRINTH_WALL_HEIGHT_TEXTURE_PATH])
            block_node.setPos(block.position)
            
            if isinstance(block, Window):
                block_node.setTransparency(True)
            
            if isinstance(block, Wall):
                self.init_objs(block, labyrinth_np)
            
            # Collisions
            is_ground = isinstance(block, Floor)
            node_name = "Ground" if is_ground else "Wall"
            wall_collider_node = CollisionNode(node_name)
            # get center of the wall
            wall_center = Point3(block.width / 2, block.depth / 2, block.height / 2)
            wall_collider_node.addSolid(CollisionBox(wall_center,
                                                     block.width / 2,
                                                     block.depth / 2,
                                                     block.height / 2))
            wall_collider = block_node.attachNewNode(wall_collider_node)
            if self.DEBUG_COLLISIONS:
                wall_collider.show()
        
        # Center the labyrinth to the origin
        labyrinth_np.setPos(
            - labyrinth.width / 2,
            - labyrinth.depth / 2,
            - labyrinth.height / 2,
        )

        return labyrinth_np, labyrinth

    def windowResized(self):
        newX, newY = self.win.getSize()
        self.quad_filter.setShaderInput('u_resolution', (newX, newY))
        update_orthographic_lens(self.camera_orthographic_lens, newX, newY, self.camera_zoom)

    def setupShaders(self):
        # Plenty of features, including normal maps and per-pixel lighting
        # (https://docs.panda3d.org/1.10/python/programming/shaders/shader-generator)
        self.render.setShaderAuto()
        
        # Apply the flashlight effect, and others, using deferred lighting
        flashlight_shader = Shader.load(Shader.SL_GLSL,
            vertex='shaders/flashlight.vert',
            fragment='shaders/flashlight.frag')

        # Save the normal buffer into the auxiliary bitplane
        self.render.setAttrib(AuxBitplaneAttrib.make(AuxBitplaneAttrib.ABO_aux_normal))

        manager = FilterManager(self.win, self.cam)
        tex = Texture()
        dtex = Texture()
        ntex = Texture()
        self.quad_filter = manager.renderSceneInto(colortex=tex, depthtex=dtex, auxtex=ntex)
        self.quad_filter.setShader(flashlight_shader)
        self.quad_filter.setShaderInputs(
            tex=tex,
            dtex=dtex,
            ntex=ntex,
            u_mouse=self.mouse_coords,
            u_resolution=(WIDTH, HEIGHT),
            u_time=time.time() - self.start_time,
            lightRadius=FLASHLIGHT_RADIUS,
            lightPower=self.flashlight_power,
            lightFlickerRatio=self.flashlight_flicker,
        )

        self.accept('aspectRatioChanged', self.windowResized)
        self.taskMgr.add(self.update_shader_time_task, 'update_shader_time_task')

        # glow_shader = Shader.load(Shader.SL_GLSL,
        #     vertex='shaders/glow.vert',
        #     fragment='shaders/glow.frag')

        # glow_buffer: GraphicsBuffer = self.win.makeTextureBuffer("Glow buffer", 512, 512)
        # glow_buffer.setSort(-3)
        # glow_buffer.setClearColor((0, 0, 0, 1))

        # glow_camera = self.makeCamera(glow_buffer, lens=self.cam.node().getLens())

        # tempnode = NodePath(PandaNode('temp node'))
        # tempnode.setShader(glow_shader)
        # glow_camera.node().setInitialState(tempnode.getState())
        
        # glow_buffer.getTextureCard().reparentTo(self.render2d)
        # self.bufferViewer.enable(True)
        # self.bufferViewer.setPosition("llcorner")
        # self.bufferViewer.setLayout("hline")
        # self.bufferViewer.setCardSize(0, 0)

    def update_shader_time_task(self, task):
        self.quad_filter.setShaderInput('u_time', time.time() - self.start_time)
        return Task.cont

    def create3dAxis(self, heads: bool = False):
        axis3d = self.render.attachNewNode('axis3d')

        x_axis = Parallelepiped(10, 0.1, 0.1, color=(1, 0, 0, 1))
        y_axis = Parallelepiped(0.1, 0.1, 10, color=(0, 1, 0, 1))
        z_axis = Parallelepiped(0.1, 10, 0.1, color=(0, 0, 1, 1))

        axis3d.attach_new_node(generateGeometry(x_axis, 'x_axis'))
        axis3d.attach_new_node(generateGeometry(y_axis, 'y_axis'))
        axis3d.attach_new_node(generateGeometry(z_axis, 'z_axis'))

        if heads:
            x_axis_head = Parallelepiped(0.3, 0.3, 0.3, color=(1, 0, 0, 1))
            y_axis_head = Parallelepiped(0.3, 0.3, 0.3, color=(0, 1, 0, 1))
            z_axis_head = Parallelepiped(0.3, 0.3, 0.3, color=(0, 0, 1, 1))

            x_axis_head_node = axis3d.attach_new_node(generateGeometry(x_axis_head, 'x_axis_head'))
            x_axis_head_node.setPos(10, 0, 0)
            y_axis_head_node = axis3d.attach_new_node(generateGeometry(y_axis_head, 'y_axis_head'))
            y_axis_head_node.setPos(0, 10, 0)
            z_axis_head_node = axis3d.attach_new_node(generateGeometry(z_axis_head, 'z_axis_head'))
            z_axis_head_node.setPos(0, 0, 10)

    def update_mouse_coords_task(self, task):
        if self.mouseWatcherNode.hasMouse():
            self.mouse_coords[0] = self.mouseWatcherNode.getMouseX()
            self.mouse_coords[1] = self.mouseWatcherNode.getMouseY()
        
        self.quad_filter.setShaderInput('u_mouse', self.mouse_coords)

        return Task.cont

    def change_camera_focus(self):
        if self.camera_focus == (0, 0, 0):
            self.camera_focus = self.moon.model.getPos()
        else:
            self.camera_focus = (0, 0, 0)
        move_camera(self.camera, self.camera_zoom, self.camera_pos, self.camera_focus)

    def update_camera_rotation_task(self, task):
        if self.mouseWatcherNode.hasMouse() and self.is_mouse_holded:
            mouse_x = self.mouseWatcherNode.getMouseX()
            mouse_y = self.mouseWatcherNode.getMouseY()
            if self.previous_mouse_pos is None:
                self.previous_mouse_pos = [mouse_x, mouse_y]
                
            mouse_offset = [mouse_x - self.previous_mouse_pos[0], mouse_y - self.previous_mouse_pos[1]]
            new_camera_pos = self.camera_pos.copy()
            new_camera_pos[0] -= mouse_offset[0] * CAMERA_SENSIBILITY
            new_camera_pos[1] += mouse_offset[1] * CAMERA_SENSIBILITY
            new_camera_pos[1] = max(120, new_camera_pos[1])
            new_camera_pos[1] = min(230, new_camera_pos[1])	
        
            had_move = move_camera(self.camera, self.camera_zoom, new_camera_pos, self.camera_focus, 
                                   grass_height=GRASS_HEIGHT, labyrinth_boundaries=[self.labyrinth.width, self.labyrinth.depth, self.labyrinth.height])
            if had_move:
                self.camera_pos = new_camera_pos.copy()
                
            self.previous_mouse_pos = [mouse_x, mouse_y]
            
        elif not self.is_mouse_holded and self.previous_mouse_pos is not None:
            self.previous_mouse_pos = None

        return Task.cont

    def generate_random_event(self, task):
        if IGNORE_RANDOM_EVENTS: return Task.cont
        if random.random() < LIGHTNING_CHANCE:
            self.lightning_strike()
        
        flick_chance = random.random()
        if (not self.is_light_toogle and flick_chance < FLASHLIGHT_FLICKER_CHANCE) or \
            self.is_light_toogle and flick_chance < FLASHLIGHT_RETURN_CHANCE:
            self.toggle_light()
            self.is_light_toogle = not self.is_light_toogle
        
        perspective_chance = random.random()
        if (not self.is_perspective_toogle and perspective_chance < PERSPECTIVE_CHANCE) or \
            self.is_perspective_toogle and perspective_chance < PERSPECTIVE_RETURN_CHANCE:
            self.toggle_perspective()
            self.is_perspective_toogle = not self.is_perspective_toogle

        return Task.cont


parser = argparse.ArgumentParser('cv-proj')
parser.add_argument('--map', '-m',
    type=str,
    default='test1.map',
    help='the labyrinth map file to be loaded (default=\'test1.map\')')

parser_debug = parser.add_argument_group('debug', 'Add debug info to the game.')
parser_debug.add_argument('--debug.map',
    action='store_true',
    help='activate the debug environment for the labyrinth scene (colored walls, for instance)')
parser_debug.add_argument('--debug.mouse-camera',
    action='store_true',
    help='let the camera be controllable with the mouse')
parser_debug.add_argument('--debug.3d-axis',
    action='store_true',
    help='place a 3D axis in the scene at the origin')
parser_debug.add_argument('--debug.collisions',
    action='store_true',
    help='show the collision boundaries')
parser_debug.add_argument('--debug.hide-unlit',
    action='store_true',
    help='when putting a light, only show the labyrinth nodes that were lit')
parser_debug.add_argument('--debug.fps',
    action='store_true',
    help='show an FPS counter at the top right')
parser_debug.add_argument('--debug.log',
    action='store_true',
    help='print debug messages (reduces performance)')


args = parser.parse_args()

debug_opts = {k.split('.')[1]: v for k, v in args._get_kwargs() if k.startswith('debug.')}

app = ExplorerApp(
    labyrinth_file=args.map,
    debug_opts=debug_opts,
)
app.setFrameRateMeter(debug_opts['fps'])
app.run()
