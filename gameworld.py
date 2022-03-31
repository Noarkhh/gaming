import os
from classes import *
from pygame.locals import (RLEACCEL,
                           K_t,
                           K_h,
                           K_r,
                           K_w,
                           K_g)


class GameWorld:
    """
    Class of a main object called gw (gameworld) used for storing data of the current gamestate
    as well as generating necessary data structures and setting up the game.

    Object gw is passed to all almost all functions, objects and methods as it contains most of
    the information about current gamestate.

    Attributes:

        SOUNDTRACK: Option to turn soundtrack on or off
        MOUSE_STEERING: Option to turn mouse steering on or off
        MOUSE_STEERING: Option to turn windowed mode on or off
        LAYOUT: Image representing the terrain
        HEIGHT_TILES, WIDTH_TILES: Map size in tiles
        WINDOW_HEIGHT, WINDOWS_WIDTH: Window size in pixels
        TICK_RATE: Amount of game ticks per second

        tile_s: Size of a single tile in pixels
        width_pixels, height_pixels: Map size in pixels
        wall_set: Set of tuples of coordinates of all Walls
        key_structure_dict: Dictionary that assigns classes of different structures to keys, that will
                            place instances of these classes
        entities: sprite group of all entities on the map
        structs: sprite group of all structures
        vault: object used for tracking gold
        soundtrack_channel: Mixer channel used for soundtrack
        speech_channel: Mixer channel used for speech

        screen: Main surface that is displayed
        snapper_dict: Dictionary of dictionaries for different Snappers
        map_surf: Surface of the map terrain
        tile_type_map: 2-dimensional array of tile types
        surrounded_tiles: 2-dimensional array that indicates which tiles are inside walls
        struct_map: 2-dimensional array of all structures, main way to reference structures
        sounds, tracks: Dictionaries that assign sounds and tracks to their corresponding names
    """

    def __init__(self):
        self.SOUNDTRACK = False
        self.MOUSE_STEERING = True
        self.WINDOWED = True
        self.LAYOUT = pg.image.load("assets/maps/desert_delta_L.png")
        self.HEIGHT_TILES = self.LAYOUT.get_height()
        self.WIDTH_TILES = self.LAYOUT.get_width()
        self.WINDOW_HEIGHT = 720
        self.WINDOW_WIDTH = 1080
        self.TICK_RATE = 60
        self.STARTING_GOLD = 300

        self.tile_s = 30
        self.width_pixels = self.WIDTH_TILES * self.tile_s
        self.height_pixels = self.HEIGHT_TILES * self.tile_s
        self.wall_set = set()
        self.key_structure_dict = {K_h: House, K_t: Tower, K_r: Road, K_w: Wall, K_g: Gate, pg.K_p: Pyramid,
                                   pg.K_f: Farmland}
        self.entities = Entities()
        self.structs = pg.sprite.Group()
        self.vault = Vault(self)
        self.soundtrack_channel = pg.mixer.Channel(5)
        self.speech_channel = pg.mixer.Channel(3)

        self.screen = self.set_window()
        self.snapper_dict = self.fill_snappers_dict()
        self.map_surf, self.tile_type_map = self.load_map()
        self.surrounded_tiles = [[0 for _ in range(self.HEIGHT_TILES)] for _ in range(self.WIDTH_TILES)]
        self.struct_map = [[0 for _ in range(self.HEIGHT_TILES)] for _ in range(self.WIDTH_TILES)]
        self.sounds, self.tracks = self.load_sounds()

    def set_window(self):
        """
        Initializes display, caption and icon

            :return: Screen surface
        """
        if self.WINDOWED:
            screen = pg.display.set_mode([self.WINDOW_WIDTH, self.WINDOW_HEIGHT])
        else:
            screen = pg.display.set_mode((0, 0), pg.FULLSCREEN)
            self.WINDOW_WIDTH, self.WINDOW_HEIGHT = pg.display.get_surface().get_size()
        pg.display.set_caption("Twierdza: Zawodzie")
        pg.display.set_icon(pg.image.load("assets/icon.png").convert())
        return screen

    def fill_snappers_dict(self):
        """
        Fills dictionaries that assign different version of a Snapper sprite to tuples of directions that the
        sprite has connections with.

            :return: Dictionary of dictionaries for different Snappers
        """
        snapper_dict = {}
        for curr_dict_name, snapper_dir, height in (("walls", "assets/walls", self.tile_s),
                                                    ("roads", "assets/roads", self.tile_s),
                                                    ("vgates", "assets/vgates", self.tile_s * 20 / 15),
                                                    ("hgates", "assets/hgates", self.tile_s * 20 / 15)):
            directory = os.listdir(snapper_dir)
            dir_cut = []
            curr_dict = {}
            for name in directory:
                dir_cut.append(tuple(name[4:-4]))
            for file, name in zip(directory, dir_cut):
                curr_dict[name] = pg.transform.scale(pg.image.load(snapper_dir + "/" + file).convert(),
                                                     (self.tile_s, height))
                curr_dict[name].set_colorkey((255, 255, 255), RLEACCEL)
            snapper_dict[curr_dict_name] = curr_dict
        return snapper_dict

    def load_map(self):
        """
        Converts an image representing the layout of terrain to map of tile types and generates a
        background surface.

            :return: Surface of the map terrain, 2-dimensional array of tile types
        """
        color_to_type = {(0, 255, 0, 255): "grassland", (0, 0, 255, 255): "water", (255, 255, 0, 255): "desert"}
        tile_dict = {name: pg.transform.scale(pg.image.load("assets/tiles/" + name + "_tile.png").convert(),
                                              (self.tile_s, self.tile_s)) for name in color_to_type.values()}

        background = pg.Surface((self.WIDTH_TILES * self.tile_s, self.HEIGHT_TILES * self.tile_s))
        tile_map = [[0 for _ in range(self.HEIGHT_TILES)] for _ in range(self.WIDTH_TILES)]

        for x in range(self.WIDTH_TILES):
            for y in range(self.HEIGHT_TILES):
                tile_color = tuple(self.LAYOUT.get_at((x, y)))
                background.blit(tile_dict[color_to_type[tile_color]], (x * self.tile_s, y * self.tile_s))
                tile_map[x][y] = color_to_type[tile_color]
                # if tile_map[x][y] == "grassland" and randint(1, 16) == 1:
                #     self.struct_map[x][y] = Tree([x, y])
                #     gw.structs.add(self.struct_map[x][y])
                #     gw.entities.add(self.struct_map[x][y])
                # elif tile_map[x][y] == "desert" and randint(1, 25) == 1:
                #     gw.struct_map[x][y] = Cactus([x, y])
                #     gw.structs.add(gw.struct_map[x][y])
                #     gw.entities.add(gw.struct_map[x][y])

        return background, tile_map

    def load_sounds(self):
        """
        Loads sound effects and sountrack to dictionaries

            :return: dictionaries of sounds and tracks
        """
        fx_dir = os.listdir("assets/fx")
        soundtrack_dir = os.listdir("assets/soundtrack")
        sounds = {file[:-4]: pg.mixer.Sound("assets/fx/" + file) for file in fx_dir}
        if self.SOUNDTRACK:
            tracks = [pg.mixer.Sound("assets/soundtrack/" + file) for file in soundtrack_dir]
        else:
            tracks = []
        for track in tracks:
            track.set_volume(0.4)
        for sound in sounds.values():
            sound.set_volume(0.7)

        return sounds, tracks