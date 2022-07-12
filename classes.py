import pygame as pg
from random import randint
import time
from pygame.locals import (RLEACCEL,
                           K_UP,
                           K_DOWN,
                           K_LEFT,
                           K_RIGHT)


class Background(pg.sprite.Sprite):
    """

    """
    def __init__(self, gw):
        super().__init__()
        self.surf = pg.transform.scale(gw.map_surf.copy(), (gw.width_pixels, gw.height_pixels))
        self.surf_raw = self.surf.copy()
        self.surf_rendered = self.surf.subsurface((0, 0, gw.WINDOW_WIDTH, gw.WINDOW_HEIGHT))
        self.rect = self.surf_rendered.get_rect()

    def move_screen(self, gw):
        if not gw.MOUSE_STEERING:
            if gw.cursor.rect.right >= self.rect.right <= gw.width_pixels - gw.tile_s / 2:
                self.rect.move_ip(gw.tile_s / 2, 0)
            if gw.cursor.rect.left <= self.rect.left >= 0 + gw.tile_s / 2:
                self.rect.move_ip(-gw.tile_s / 2, 0)
            if gw.cursor.rect.bottom >= self.rect.bottom <= gw.height_pixels - gw.tile_s / 2:
                self.rect.move_ip(0, gw.tile_s / 2)
            if gw.cursor.rect.top <= self.rect.top >= 0 + gw.tile_s / 2:
                self.rect.move_ip(0, -gw.tile_s / 2)
        else:
            if pg.mouse.get_pos()[0] >= gw.WINDOW_WIDTH - gw.tile_s / 2 and \
                    self.rect.right <= gw.width_pixels - gw.tile_s / 2:
                self.rect.move_ip(gw.tile_s / 2, 0)
            if pg.mouse.get_pos()[0] <= 0 + gw.tile_s / 2 <= self.rect.left:
                self.rect.move_ip(-gw.tile_s / 2, 0)
            if pg.mouse.get_pos()[1] >= gw.WINDOW_HEIGHT - gw.tile_s / 2 and \
                    self.rect.bottom <= gw.height_pixels - gw.tile_s / 2:
                self.rect.move_ip(0, gw.tile_s / 2)
            if pg.mouse.get_pos()[1] <= 0 + gw.tile_s / 2 <= self.rect.top:
                self.rect.move_ip(0, -gw.tile_s / 2)
        self.surf_rendered = self.surf.subsurface(self.rect)


class Entities(pg.sprite.Group):
    def draw(self, background):
        sprites = self.sprites()
        for spr in sorted(sprites, key=lambda spr: spr.pos[1]):
            if spr.rect.colliderect(background.rect):
                background.surf.blit(spr.surf, spr.rect)
        self.lostsprites = []


class Statistics:
    def __init__(self):
        self.rect = None
        self.font_size = 20
        self.font = pg.font.Font('assets/Minecraft.otf', self.font_size)
        self.stat_window = pg.Surface((self.font_size * 20, self.font_size * 10))
        self.stat_window.fill((0, 0, 0))
        self.stat_background = pg.Surface((self.font_size * 20, self.font_size * 10))
        self.stat_background.fill((255, 255, 255))
        self.stat_height = self.font_size + 4
        self.screen_part = ""
        self.curr_coords = []

    def blit_stat(self, stat):
        stat_surf = self.font.render(stat, False, (255, 255, 255), (0, 0, 0))
        if self.screen_part == "topleft":
            stat_rect = stat_surf.get_rect(topleft=self.curr_coords)
        elif self.screen_part == "topright":
            stat_rect = stat_surf.get_rect(topright=self.curr_coords)
        elif self.screen_part == "bottomleft":
            stat_rect = stat_surf.get_rect(bottomleft=self.curr_coords)
        elif self.screen_part == "bottomright":
            stat_rect = stat_surf.get_rect(bottomright=self.curr_coords)
        else:
            stat_rect = stat_surf.get_rect(topleft=self.curr_coords)

        self.stat_window.blit(stat_surf, stat_rect)
        layer = pg.Surface((stat_rect.width + 8, stat_rect.height + 6))
        layer.fill((0, 0, 0))
        self.stat_background.blit(layer, (stat_rect.x - 5, stat_rect.y - 3))
        if self.screen_part in {"topleft", "topright"}:
            self.curr_coords[1] += self.stat_height
        else:
            self.curr_coords[1] -= self.stat_height

    def print_stats(self, gw):
        self.stat_window.set_colorkey((0, 0, 0), RLEACCEL)
        self.stat_background.set_colorkey((255, 255, 255), RLEACCEL)
        self.stat_background.set_alpha(48)

        gw.screen.blit(self.stat_background, self.rect)
        gw.screen.blit(self.stat_window, self.rect)


class GlobalStatistics(Statistics):
    def __init__(self, gw):
        super().__init__()
        self.rect = self.stat_window.get_rect(bottomleft=(0, gw.WINDOW_HEIGHT))
        self.screen_part = "bottomleft"
        self.curr_coords = [4, gw.WINDOW_HEIGHT - 4]

    def update_global_stats(self, gw):

        self.stat_window.fill((0, 0, 0))
        self.stat_background.fill((255, 255, 255))
        self.curr_coords = [4, self.stat_window.get_height() - 4]

        super().blit_stat(
            "Time: " + str(gw.time_manager.time[0]) + ":00, Day " + str(gw.time_manager.time[1] + 1) + ", Week " + str(gw.time_manager.time[2] + 1))
        super().blit_stat("Gold: " + str(gw.time_manager.gold) + "g")
        super().blit_stat("TPS: " + str("{:.2f}".format(1 / gw.time_manager.elapsed * gw.TICK_RATE)))
        super().blit_stat("Weekly Tribute: " + str(gw.time_manager.tribute) + "g")

        super().print_stats(gw)


class TileStatistics(Statistics):
    def __init__(self, gw):
        super().__init__()
        self.rect = self.stat_window.get_rect(bottomright=(gw.WINDOW_WIDTH, gw.WINDOW_HEIGHT))
        self.screen_part = "bottomright"
        self.curr_coords = [self.stat_window.get_width() - 4, self.stat_window.get_height() - 4]

    def update_tile_stats(self, xy, gw):
        self.stat_window.fill((0, 0, 0))
        self.stat_background.fill((255, 255, 255))
        self.curr_coords = [self.stat_window.get_width() - 4, self.stat_window.get_height() - 4]

        if isinstance(gw.struct_map[xy[0]][xy[1]], Structure):
            super().blit_stat(
                "time left: " + str("{:.2f}".format(gw.struct_map[xy[0]][xy[1]].time_left / gw.TICK_RATE)) + "s")
            super().blit_stat("cooldown: " + str(gw.struct_map[xy[0]][xy[1]].cooldown / gw.TICK_RATE) + "s")
            super().blit_stat("profit: " + str(gw.struct_map[xy[0]][xy[1]].profit) + "g")
            super().blit_stat("inside: " + str(gw.struct_map[xy[0]][xy[1]].inside))
            super().blit_stat(str(type(gw.struct_map[xy[0]][xy[1]]))[16:-2])
        super().blit_stat(gw.tile_type_map[xy[0]][xy[1]])
        super().blit_stat(str(xy))

        super().print_stats(gw)


class TimeManager:
    def __init__(self, gw):
        self.time = 0
        self.tick = 0
        self.time = [0, 0, 0]
        self.elapsed = 1
        self.start = time.time()
        self.end = 0
        self.tribute = 40
        self.gold = gw.STARTING_GOLD

    def time_lapse(self, gw):
        self.tick += 1
        if self.tick >= gw.TICK_RATE:
            self.tick = 0
            self.time[0] += 1
            self.end = time.time()
            self.elapsed = self.end - self.start
            self.start = time.time()
            if self.time[0] >= 24:
                self.time[0] = 0
                self.time[1] += 1
                if self.time[1] >= 7:
                    self.time[1] = 0
                    self.time[2] += 1
                    gw.time_manager.gold -= self.tribute
                    gw.sounds["ignite_oil"].play()
                    self.tribute = int(self.tribute ** 1.2)

    def to_json(self):
        return {
            "time": self.time,
            "tribute": self.tribute
        }

    def from_json(self, json_dict):
        self.time = json_dict["time"]
        self.tribute = json_dict["tribute"]
        return self


class Cursor(pg.sprite.Sprite):
    def __init__(self, gw):
        super().__init__()
        self.is_in_demolish_mode = False

        self.surf = pg.transform.scale(pg.image.load("assets/cursor2.png").convert(), (gw.tile_s, gw.tile_s))
        self.surf_demolish = pg.transform.scale(pg.image.load("assets/cursor_demolish.png").convert(),
                                                (gw.tile_s, gw.tile_s))
        self.surf_demolish.set_alpha(128)

        self.surf.set_colorkey((255, 255, 255), RLEACCEL)
        self.surf_demolish.set_colorkey((255, 255, 255), RLEACCEL)
        self.rect = self.surf.get_rect()
        self.pos = [0, 0]
        self.previous_pos = [0, 0]
        self.held_structure = None
        self.ghost = None

    def update(self, gw):
        self.previous_pos = self.pos.copy()
        self.pos[0] = (pg.mouse.get_pos()[0] + gw.background.rect.x) // gw.tile_s
        self.pos[1] = (pg.mouse.get_pos()[1] + gw.background.rect.y) // gw.tile_s
        self.rect.x = self.pos[0] * gw.tile_s
        self.rect.y = self.pos[1] * gw.tile_s

    def draw(self, gw):
        if self.is_in_demolish_mode:
            gw.background.surf.blit(self.surf_demolish, self.rect)
        else:
            gw.background.surf.blit(self.surf, self.rect)
        if self.held_structure is not None:
            self.ghost.update(gw)
            gw.background.surf.blit(self.ghost.surf, self.ghost.rect)

    def to_json(self):
        return {
            "pos": self.pos
        }


class Ghost(pg.sprite.Sprite):
    def __init__(self, gw):
        super().__init__()
        self.surf = gw.cursor.held_structure.surf
        self.surf.set_alpha(128)
        self.pos = gw.cursor.pos
        self.rect = self.surf.get_rect(bottomright=(gw.tile_s * (self.pos[0] + 1), gw.tile_s * (self.pos[1] + 1)))

    def update(self, gw):
        self.pos = gw.cursor.pos
        self.rect.right = gw.tile_s * (self.pos[0] + 1)
        self.rect.bottom = gw.tile_s * (self.pos[1] + 1)
        self.surf = gw.cursor.held_structure.surf
        self.surf.set_alpha(128)


class Structure(pg.sprite.Sprite):
    def __init__(self, xy, gw, *args):
        super().__init__()
        self.surf = pg.Surface((gw.tile_s, gw.tile_s))
        self.image_path = ""
        # self.string_type_dict = {"house": House, "tower": Tower, "road": Road, "wall": Wall, "gate": Gate,
        #                          "obama": Pyramid, "farmland": Farmland}
        self.type_string_dict = {val: key for key, val in gw.string_type_dict.items()}

        self.surf_ratio = (1, 1)
        self.pos = xy.copy()
        self.covered_tiles = {(0, 0)}
        self.rect = self.surf.get_rect(bottomright=(gw.tile_s * (xy[0] + 1), gw.tile_s * (xy[1] + 1)))
        self.base_profit = 0
        self.profit = self.base_profit
        self.cooldown = gw.TICK_RATE * 24
        self.time_left = self.cooldown
        self.build_cost = 0
        self.orientation = 'v'
        if gw.surrounded_tiles[self.pos[0]][self.pos[1]] == 2:
            self.inside = True
        else:
            self.inside = False

    def get_profit(self, gw):
        self.time_left -= 1
        if self.time_left == 0:
            self.time_left = self.cooldown
            gw.time_manager.gold += self.profit

    def update_zoom(self, gw):
        self.surf = pg.transform.scale(self.surf, (self.surf_ratio[0] * gw.tile_s, self.surf_ratio[1] * gw.tile_s))
        self.rect = self.surf.get_rect(bottomright=(gw.tile_s * (self.pos[0] + 1), gw.tile_s * (self.pos[1] + 1)))

    def to_json(self):
        return {
            "type": self.type_string_dict[type(self)],
            "image_path": self.image_path,
            "rect": (self.rect.left, self.rect.top, self.rect.width, self.rect.height),
            "pos": self.pos,
            "profit": self.profit,
            "time_left": self.time_left,
            "inside": self.inside
        }

    def from_json(self, y):
        self.rect = pg.rect.Rect(y["rect"])
        self.profit = y["profit"]
        self.time_left = y["time_left"]
        self.inside = y["inside"]
        return self


class Tree(Structure):
    def __init__(self, xy, gw, *args):
        super().__init__(xy, gw)
        self.image_path = "assets/tree.png"
        self.surf = pg.transform.scale(pg.image.load(self.image_path).convert(), (gw.tile_s, gw.tile_s))
        self.surf.set_colorkey((255, 255, 255), RLEACCEL)


class Mine(Structure):
    def __init__(self, xy, gw, *args):
        super().__init__(xy, gw)
        self.image_path = "assets/mine.png"
        self.surf = pg.transform.scale(pg.image.load(self.image_path).convert(), (gw.tile_s, gw.tile_s*2))
        self.surf_ratio = (1, 2)
        self.rect = self.surf.get_rect(bottomright=(gw.tile_s * (xy[0] + 1), gw.tile_s * (xy[1] + 1)))
        self.surf.set_colorkey((255, 255, 255), RLEACCEL)


class Sawmill(Structure):
    def __init__(self, xy, gw, *args):
        super().__init__(xy, gw)
        self.image_path = "assets/sawmill.png"
        self.surf = pg.transform.scale(pg.image.load(self.image_path).convert(), (gw.tile_s*2, gw.tile_s*2))
        self.surf_ratio = (2, 2)
        self.covered_tiles = {(0, 0), (-1, 0)}
        self.rect = self.surf.get_rect(bottomright=(gw.tile_s * (xy[0] + 1), gw.tile_s * (xy[1] + 1)))
        self.surf.set_colorkey((255, 255, 255), RLEACCEL)


class Farmland(Structure):
    def __init__(self, xy, gw, *args):
        super().__init__(xy, gw)
        self.image_path = "assets/farmland.png"
        self.surf = pg.transform.scale(pg.image.load(self.image_path).convert(), (gw.tile_s, gw.tile_s))
        self.surf.set_colorkey((255, 255, 255), RLEACCEL)


class Pyramid(Structure):
    def __init__(self, xy, gw, *args):
        super().__init__(xy, gw)
        self.image_path = "assets/obama.png"
        self.surf = pg.transform.scale(pg.image.load("assets/obama.png").convert(),
                                       (gw.tile_s * 2, gw.tile_s * 2))
        self.surf_ratio = (2, 2)
        self.covered_tiles = {(0, 0), (-1, 0)}
        self.rect = self.surf.get_rect(bottomright=(gw.tile_s * (xy[0] + 1), gw.tile_s * (xy[1] + 1)))
        self.surf.set_colorkey((255, 255, 255), RLEACCEL)


class House(Structure):
    def __init__(self, xy, gw, *args):
        super().__init__(xy, gw)
        self.image_path = "assets/house" + str(randint(1, 2)) + ".png"
        self.surf = pg.transform.scale(pg.image.load(self.image_path).convert(),
                                       (gw.tile_s, gw.tile_s * 21 / 15))
        self.surf_ratio = (1, 21 / 15)
        self.rect = self.surf.get_rect(bottomright=(gw.tile_s * (xy[0] + 1), gw.tile_s * (xy[1] + 1)))
        self.surf.set_colorkey((255, 255, 255), RLEACCEL)
        self.base_profit = 10
        self.profit = self.base_profit
        self.build_cost = 50

    def update_profit(self, gw):
        self.profit = self.base_profit
        visited = {tuple(self.pos)}
        nearby_houses = 0
        for xy in ((-1, 0), (0, 1), (1, 0), (0, -1)):
            if not gw.is_out_of_bounds(self.pos[0] + xy[0], self.pos[1] + xy[1]) and \
                    isinstance(gw.struct_map[self.pos[0] + xy[0]][self.pos[1] + xy[1]], Road):
                nearby_houses += self.detect_nearby_houses(gw, [self.pos[0] + xy[0], self.pos[1] + xy[1]], visited)
        self.profit += nearby_houses
        if self.inside:
            self.profit *= 2

    def detect_nearby_houses(self, gw, xy, visited):

        resolved = [[True for _ in range(gw.height_tiles)] for _ in range(gw.width_tiles)]
        direction_to_xy_dict = {'N': (0, -1), 'E': (1, 0), 'S': (0, 1), 'W': (-1, 0)}
        required = {"roads"}
        distance = 0
        nearby = 0

        def _detect_nearby_houses(gw, resolved, xy, direction_to_xy_dict, required, distance, visited):
            nonlocal nearby
            if distance >= 6:
                return
            for xy0 in direction_to_xy_dict.values():
                if isinstance(gw.struct_map[xy[0] + xy0[0]][xy[1] + xy0[1]], House) and \
                        (xy[0] + xy0[0], xy[1] + xy0[1]) not in visited:
                    nearby += 1
                    visited.add((xy[0] + xy0[0], xy[1] + xy0[1]))

            resolved[xy[0]][xy[1]] = False
            for direction in gw.struct_map[xy[0]][xy[1]].neighbours:
                next = direction_to_xy_dict[direction]
                if resolved[xy[0] + next[0]][xy[1] + next[1]] and \
                        bool(set(gw.struct_map[xy[0] + next[0]][xy[1] + next[1]].snapsto.values()) & required):
                    _detect_nearby_houses(gw, resolved, [xy[0] + next[0], xy[1] + next[1]], direction_to_xy_dict,
                                          required, distance + 1, visited)

        _detect_nearby_houses(gw, resolved, xy, direction_to_xy_dict, required, distance, visited)
        return nearby


class Tower(Structure):
    def __init__(self, xy, gw, *args):
        super().__init__(xy, gw)
        self.image_path = "assets/big_tower.png"
        self.surf = pg.transform.scale(pg.image.load(self.image_path).convert(), (gw.tile_s, 2 * gw.tile_s))
        self.surf_ratio = (1, 2)
        self.rect = self.surf.get_rect(bottomright=(gw.tile_s * (xy[0] + 1), gw.tile_s * (xy[1] + 1)))
        self.surf.set_colorkey((255, 255, 255), RLEACCEL)


class Snapper(Structure):
    def __init__(self, xy, gw):
        super().__init__(xy, gw)
        self.snapsto = {}
        self.neighbours = set()
        self.snapper_dict_key = ""
        self.snapper_dict = {}
        self.direction_to_int_dict = {direction: i for i, direction in enumerate(('N', 'E', 'S', 'W'))}

    def update_edges(self, direction, add):
        if add == 1:
            self.neighbours.update(direction)
        elif add == -1 and direction in self.neighbours:
            self.neighbours.remove(direction)

        directions = tuple(sorted(self.neighbours, key=lambda x: self.direction_to_int_dict[x]))
        self.surf = self.snapper_dict[directions].copy()

    def to_json(self):
        return {**super().to_json(), **{"snapper_dict_key": self.snapper_dict_key, "neighbours": list(self.neighbours)}}

    def from_json(self, y):
        super().from_json(y)
        self.snapper_dict_key = y["snapper_dict_key"]
        self.neighbours = set(y["neighbours"])
        self.update_edges('N', 0)
        return self


class Road(Snapper):
    def __init__(self, xy, gw, *args):
        super().__init__(xy, gw)
        self.image_path = ""
        self.snapper_dict_key = "roads"
        self.snapper_dict = gw.snapper_dict["roads"]
        self.surf = self.snapper_dict[()].copy()
        self.surf.set_colorkey((255, 255, 255), RLEACCEL)
        self.snapsto = {snap: "roads" for snap in ('N', 'E', 'S', 'W')}
        self.base_profit = -2
        self.profit = self.base_profit
        self.build_cost = 10


class Wall(Snapper):
    def __init__(self, xy, gw, *args):
        super().__init__(xy, gw)
        self.image_path = ""
        self.snapper_dict_key = "walls"
        self.snapper_dict = gw.snapper_dict["walls"]
        self.surf = self.snapper_dict[()].copy()
        self.surf.set_colorkey((255, 255, 255), RLEACCEL)
        self.snapsto = {snap: "walls" for snap in ('N', 'E', 'S', 'W')}
        self.base_profit = -3
        self.profit = self.base_profit
        self.build_cost = 20


class Gate(Wall, Road):
    def __init__(self, xy, gw, orientation="v"):
        super().__init__(xy, gw)
        self.orientation = orientation
        self.image_path = ""
        if orientation == "v":
            self.snapper_dict_key = "vgates"
            self.snapper_dict = gw.snapper_dict["vgates"]
            self.snapsto = {'N': "roads", 'E': "walls", 'S': "roads", 'W': "walls"}
        else:
            self.snapper_dict_key = "hgates"
            self.snapper_dict = gw.snapper_dict["hgates"]
            self.snapsto = {'N': "walls", 'E': "roads", 'S': "walls", 'W': "roads"}
        self.surf = self.snapper_dict[()].copy()
        self.surf_ratio = (1, 20 / 15)
        self.rect = self.surf.get_rect(bottomright=(gw.tile_s * (xy[0] + 1), gw.tile_s * (xy[1] + 1)))
        self.surf.set_colorkey((255, 255, 255), RLEACCEL)
        self.base_profit = -15
        self.profit = self.base_profit
        self.build_cost = 150

    def rotate(self, gw):
        if self.orientation == "v":
            self.orientation = "h"
            self.snapsto = {'N': "walls", 'E': "roads", 'S': "walls", 'W': "roads"}
        else:
            self.orientation = "v"
            self.snapsto = {'N': "roads", 'E': "walls", 'S': "roads", 'W': "walls"}
        self.surf = pg.transform.scale(pg.image.load("assets/" + self.orientation + "gates/gate.png").convert(),
                                       (gw.tile_s, gw.tile_s * 20 / 15))
        self.rect = self.surf.get_rect(bottomright=(gw.tile_s * (self.pos[0] + 1), gw.tile_s * (self.pos[1] + 1)))
        self.surf.set_colorkey((255, 255, 255), RLEACCEL)

    def to_json(self):
        return {**super().to_json(), **{"orient": self.orientation}}
