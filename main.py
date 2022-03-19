import pygame as pg
import os
from random import randint
from pygame.locals import (RLEACCEL,
                           K_UP,
                           K_DOWN,
                           K_LEFT,
                           K_RIGHT,
                           K_SPACE,
                           KEYDOWN,
                           QUIT,
                           K_ESCAPE,
                           K_t,
                           K_h,
                           K_r,
                           K_n,
                           K_x)

MOUSE_STEERING = True
LAYOUT = pg.image.load("assets/layout3.png")
HEIGHT_TILES = LAYOUT.get_height()
WIDTH_TILES = LAYOUT.get_width()
TILE_S = 45
WIDTH_PIXELS = WIDTH_TILES * TILE_S
HEIGHT_PIXELS = HEIGHT_TILES * TILE_S
TICK_RATE = 30


class Statistics:
    def __init__(self):
        self.font_size = 24
        self.stat_window = pg.Surface((self.font_size * 20, self.font_size * 10))
        self.stat_window.fill((0, 0, 0))
        self.font = pg.font.SysFont('consolas', self.font_size)
        self.rect = self.stat_window.get_rect(bottom=HEIGHT_PIXELS - 2, right=WIDTH_PIXELS - 4)

    def update_stats(self, xy, structure_map, tile_type_map):
        def blit_stat(stat):
            nonlocal stat_height
            stat_surf = self.font.render(stat, False, (255, 255, 255), (0, 0, 0))
            stat_rect = stat_surf.get_rect(bottom=self.stat_window.get_height() - stat_height,
                                           right=self.stat_window.get_width())
            self.stat_window.blit(stat_surf, stat_rect)
            stat_height += self.font_size + 4

        self.stat_window.fill((0, 0, 0))
        stat_height = 4

        if isinstance(structure_map[xy[0]][xy[1]], Structure):
            blit_stat(str(type(structure_map[xy[0]][xy[1]]))[17:-2])
        blit_stat(tile_type_map[xy[0]][xy[1]])
        blit_stat(str(xy))
        self.stat_window.set_colorkey((0, 0, 0), RLEACCEL)


class Cursor(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.windup = [0 for _ in range(4)]
        self.cooldown = [0 for _ in range(4)]
        self.surf = pg.transform.scale(pg.image.load("assets/cursor3.png").convert(), (TILE_S, TILE_S))
        self.surf.set_colorkey((255, 255, 255), RLEACCEL)
        self.rect = self.surf.get_rect()
        self.pos = [0, 0]
        self.hold = None

    def update_arrows(self, pressed_keys):
        cooltime = 10
        key_list = [True if pressed_keys[key] else False for key in (K_UP, K_DOWN, K_LEFT, K_RIGHT)]
        iter_list = [(key, sign, xy) for key, sign, xy in zip(key_list, (-1, 1, -1, 1), (1, 1, 0, 0))]
        for i, elem in enumerate(iter_list):
            if elem[0]:
                if self.cooldown[i] <= self.windup[i]:
                    if self.windup[i] < cooltime: self.windup[i] += 4
                    self.pos[elem[2]] += elem[1]
                    self.cooldown[i] = cooltime
            else:
                self.windup[i] = 0
                self.cooldown[i] = 0
        bruh = False
        if self.pos[0] < 0:
            self.pos[0] = 0
            bruh = True
        if self.pos[0] > WIDTH_TILES - 1:
            self.pos[0] = WIDTH_TILES - 1
            bruh = True
        if self.pos[1] < 0:
            self.pos[1] = 0
            bruh = True
        if self.pos[1] > HEIGHT_TILES - 1:
            self.pos[1] = HEIGHT_TILES - 1
            bruh = True
        if bruh:
            speech_channel.play(sounds["Insult" + str(randint(1, 20))])

        self.cooldown = [x - 1 if x > 0 else 0 for x in self.cooldown]
        self.rect.x = self.pos[0] * TILE_S
        self.rect.y = self.pos[1] * TILE_S

    def update_mouse(self, xy):
        self.pos[0] = xy[0] // TILE_S
        self.pos[1] = xy[1] // TILE_S
        self.rect.x = self.pos[0] * TILE_S
        self.rect.y = self.pos[1] * TILE_S


class Ghost(pg.sprite.Sprite):
    def __init__(self, xy, surf):
        super().__init__()
        self.surf = surf
        self.surf.set_alpha(128)
        self.position = xy
        self.rect = surf.get_rect(top=(TILE_S * xy[1]), left=(TILE_S * xy[0]))

    def update(self, xy):
        self.position = xy
        self.rect.x = xy[0] * TILE_S
        self.rect.y = xy[1] * TILE_S


class Tile(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()


class Structure(pg.sprite.Sprite):
    def __init__(self, xy):
        super().__init__()
        self.surf = pg.Surface((60, 60))
        self.surf.fill((0, 0, 0))
        self.pos = xy
        self.rect = self.surf.get_rect(top=(TILE_S * xy[1]), left=(TILE_S * xy[0]))


class House(Structure):
    def __init__(self, xy):
        super().__init__(xy)
        self.surf = pg.transform.scale(pg.image.load("assets/hut1.png").convert(), (TILE_S, TILE_S))
        self.surf.set_colorkey((255, 255, 255), RLEACCEL)
        self.taxed = False
        self.debt = 10

    def tax(self):
        pg.draw.circle(self.surf, (255, max(355 - 10 * self.debt, 0), 0), (30, 30), self.debt)
        self.debt += 5
        self.taxed = True


class Tower(Structure):
    def __init__(self, xy):
        super().__init__(xy)
        self.surf = pg.transform.scale(pg.image.load("assets/tower.png").convert(), (TILE_S, TILE_S))
        self.surf.set_colorkey((0, 0, 0), RLEACCEL)


class Road(Structure):
    def __init__(self, xy):
        super().__init__(xy)
        self.neighbours = set()
        self.surf = pg.transform.scale(pg.image.load("assets/roads/road0.png").convert(), (TILE_S, TILE_S))
        self.surf.set_colorkey((255, 255, 255), RLEACCEL)

    def update_edges(self, direction, roads_list, add):
        if add:
            self.neighbours.add(direction)
        elif direction in self.neighbours:
            self.neighbours.remove(direction)

        def assign_value(direct):
            if direct == 'N': return 0
            if direct == 'E': return 1
            if direct == 'S': return 2
            if direct == 'W': return 3

        directions = tuple(sorted(self.neighbours, key=assign_value))
        if not directions:
            directions = ('0',)
        self.surf = roads_list[directions]


def fill_roads_list():
    directory = os.listdir("assets/roads")
    dir_cut = []
    directions_list = [('0',), ('N',), ('E',), ('S',), ('W',), ('N', 'E'), ('E', 'S'), ('S', 'W'), ('N', 'W'),
                       ('N', 'S'), ('E', 'W'), ('N', 'E', 'S'), ('E', 'S', 'W'),
                       ('N', 'S', 'W'), ('N', 'E', 'W'), ('N', 'E', 'S', 'W')]
    roads_list = {directions_list[i]: pg.Surface((60, 60)) for i in range(16)}

    for name in directory:
        dir_cut.append(tuple(name[4:-4]))

    for file, name in zip(directory, dir_cut):
        roads_list[name] = pg.transform.scale(pg.image.load("assets/roads/" + file).convert(), (TILE_S, TILE_S))
        roads_list[name].set_colorkey((255, 255, 255), RLEACCEL)

    return roads_list


def pos_oob(x, y):
    if x < 0: return True
    if x > WIDTH_TILES - 1: return True
    if y < 0: return True
    if y > HEIGHT_TILES - 1: return True
    return False


def place_structure():
    if isinstance(cursor.hold, Structure):
        if structure_map[cursor.pos[0]][cursor.pos[1]] not in structures \
                and tile_type_map[cursor.pos[0]][cursor.pos[1]] != "sea":
            new_structure = type(cursor.hold)(cursor.pos)
            structure_group_dict[type(cursor.hold)].add(new_structure)
            structures.add(new_structure)
            all_sprites.add(new_structure)
            structure_map[cursor.pos[0]][cursor.pos[1]] = new_structure
            # boom_se.play()
            sounds["drawbridge_control"].play()
            if isinstance(new_structure, Road):
                for direction, direction_rev, x, y in zip(('N', 'E', 'S', 'W'), ('S', 'W', 'N', 'E'),
                                                          (0, -1, 0, 1), (1, 0, -1, 0)):
                    if not pos_oob(cursor.pos[0] + x, cursor.pos[1] + y) \
                            and isinstance(structure_map[cursor.pos[0] + x][cursor.pos[1] + y], Road):
                        structure_map[cursor.pos[0] + x][cursor.pos[1] + y].update_edges(direction, roads_list, True)
                        new_structure.update_edges(direction_rev, roads_list, True)
            # else:
            #     cursor.holding = None
        elif not place_hold:
            speech_channel.play(sounds["Placement_Warning16"])
    return


def remove_structure():
    if structure_map[cursor.pos[0]][cursor.pos[1]] in structures:
        structure_map[cursor.pos[0]][cursor.pos[1]].kill()
        structure_map[cursor.pos[0]][cursor.pos[1]] = 0
        sounds["buildingwreck_01"].play()
        for direction, x, y in zip(('N', 'E', 'S', 'W'), (0, -1, 0, 1), (1, 0, -1, 0)):
            if not pos_oob(cursor.pos[0] + x, cursor.pos[1] + y) \
                    and isinstance(structure_map[cursor.pos[0] + x][cursor.pos[1] + y], Road):
                structure_map[cursor.pos[0] + x][cursor.pos[1] + y].update_edges(direction, roads_list, False)


def generate_map():
    color_to_type = {(0, 255, 0, 255): "grassland", (0, 0, 255, 255): "sea"}
    tile_dict = {"grassland": pg.transform.scale(pg.image.load("assets/tiles/grassland_tile.png").convert(),
                                                 (TILE_S, TILE_S)),
                 "sea": pg.transform.scale(pg.image.load("assets/tiles/sea_tile.png").convert(),
                                           (TILE_S, TILE_S))}
    background = pg.Surface((WIDTH_TILES * TILE_S, HEIGHT_TILES * TILE_S))
    tile_map = [[0 for _ in range(HEIGHT_TILES)] for _ in range(WIDTH_TILES)]

    for x in range(WIDTH_TILES):
        for y in range(HEIGHT_TILES):
            tile_color = tuple(LAYOUT.get_at((x, y)))
            background.blit(tile_dict[color_to_type[tile_color]], (x * TILE_S, y * TILE_S))
            tile_map[x][y] = color_to_type[tile_color]
    return background, tile_map


def load_sounds():
    fx_dir = os.listdir("assets/fx")
    soundtrack_dir = os.listdir("assets/soundtrack")
    sounds = {file[:-4]: pg.mixer.Sound("assets/fx/" + file) for file in fx_dir}
    tracks = [pg.mixer.Sound("assets/soundtrack/" + file) for file in soundtrack_dir]
    for track in tracks:
        track.set_volume(0.20)
    for sound in sounds.values():
        sound.set_volume(0.4)

    return sounds, tracks


def play_soundtrack():
    if not soundtrack_channel.get_busy():
        soundtrack_channel.play(tracks[randint(0, 13)])


if __name__ == "__main__":
    pg.init()
    pg.mixer.init()

    sounds, tracks = load_sounds()
    soundtrack_channel = pg.mixer.Channel(5)
    speech_channel = pg.mixer.Channel(3)

    screen = pg.display.set_mode([WIDTH_PIXELS, HEIGHT_PIXELS])
    cursor = Cursor()
    statistics = Statistics()
    structure_map = [[0 for _ in range(HEIGHT_TILES)] for _ in range(WIDTH_TILES)]

    roads_list = fill_roads_list()

    background, tile_type_map = generate_map()

    pg.display.set_caption("Twierdza: Zawodzie")

    houses = pg.sprite.Group()
    towers = pg.sprite.Group()
    roads = pg.sprite.Group()
    structures = pg.sprite.Group()
    all_sprites = pg.sprite.Group()
    all_sprites.add(cursor)

    clock = pg.time.Clock()
    key_structure_dict = {K_h: House, K_t: Tower, K_r: Road}
    structure_group_dict = {House: houses, Tower: towers, Road: roads}
    running = True
    # ------ MAIN LOOP -------
    while running:

        pressed_keys = pg.key.get_pressed()
        # checking events
        for event in pg.event.get():
            if event.type == QUIT:
                running = False
            if event.type == KEYDOWN:

                if event.key in key_structure_dict:  # picking up a chosen structure
                    cursor.hold = key_structure_dict[event.key]([0, 0])
                    structure_ghost = Ghost(cursor.pos, cursor.hold.surf)
                    sounds["menusl_" + str(randint(1, 3)) ].play()
                    # violin_se.play()

                if event.key == K_n:
                    cursor.hold = None

                if event.key == K_ESCAPE:
                    running = False

                # if event.key == pg.:
                #     place_structure()

        if pressed_keys[K_SPACE] or pg.mouse.get_pressed(num_buttons=3)[0]:  # placing down held structure
            place_structure()
            place_hold = True
        else:
            place_hold = False

        if pressed_keys[K_x]:  # removing a structure
            remove_structure()
        if MOUSE_STEERING:
            cursor.update_mouse(pg.mouse.get_pos())
        else:
            cursor.update_arrows(pressed_keys)
        screen.blit(background, (0, 0))
        for entity in structures:
            screen.blit(entity.surf, entity.rect)

        if cursor.hold is not None:
            structure_ghost.update(cursor.pos)
            screen.blit(structure_ghost.surf, structure_ghost.rect)

        screen.blit(cursor.surf, cursor.rect)
        statistics.update_stats(cursor.pos, structure_map, tile_type_map)
        screen.blit(statistics.stat_window, statistics.rect)

        play_soundtrack()
        if randint(1, 100000) == 1: sounds["Random_Events13"].play()
        pg.display.flip()
        clock.tick(TICK_RATE)
    pg.quit()
