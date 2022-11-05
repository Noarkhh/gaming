import pygame as pg
from pygame import RLEACCEL


class Spritesheet:
    def __init__(self):
        self.edges_sorted = [(), ('N',), ('E',), ('S',), ('W',), ('N', 'E'), ('E', 'S'), ('S', 'W'), ('N', 'W'),
                             ('N', 'S'), ('E', 'W'), ('N', 'E', 'S'), ('E', 'S', 'W'),
                             ('N', 'S', 'W'), ('N', 'E', 'W'), ('N', 'E', 'S', 'W')]
        self.snappers_sorted = ["road", "wall", "vgate", "hgate", "farmland", "demolish", "bridge"]
        self.snappers_sheet = pg.image.load("assets/snapper_sheet.png")
        # self.structures_sheet = pg.image.load("assets/structures_sheet.png")

    def get_snapper_surf(self, gw, edges, name, surf_ratio=(1, 1)):

        target_rect = pg.Rect(self.edges_sorted.index(edges) * 15,
                              self.snappers_sorted.index(name) * 20,
                              surf_ratio[0] * 15,
                              surf_ratio[1] * 15)
        new_surf = pg.Surface(target_rect.size)
        new_surf.blit(self.snappers_sheet, (0, 0), target_rect)
        new_surf.set_colorkey((255, 255, 255), RLEACCEL)
        return pg.transform.scale(new_surf, (surf_ratio[0] * gw.tile_s, surf_ratio[1] * gw.tile_s))


class Scene(pg.sprite.Sprite):
    def __init__(self, gw):
        super().__init__()
        self.surf = pg.transform.scale(gw.map_surf, (gw.width_pixels, gw.height_pixels))
        self.surf_raw = self.surf.copy()
        self.rect = pg.Rect(((self.surf.get_width() - gw.WINDOW_WIDTH) // 2,
                             (self.surf.get_height() - gw.WINDOW_HEIGHT) // 2,
                             gw.WINDOW_WIDTH, gw.WINDOW_HEIGHT))
        self.surf_rendered = self.surf.subsurface(self.rect)
        self.move_velocity = (0, 0)
        self.move_velocity_decrement = (0, 0)
        self.to_decrement = 0
        self.retardation_period = 30

    def move_screen_border(self, gw):
        if gw.button_handler.hovered_button is None:
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

    def move_screen_drag(self, gw):
        new_rect = self.rect.move(self.move_velocity[0], self.move_velocity[1])
        if new_rect.left >= 0 and new_rect.right <= gw.width_pixels:
            self.rect.move_ip(self.move_velocity[0], 0)
        elif new_rect.left < 0:
            self.rect.left = 0
        elif new_rect.right > gw.width_pixels:
            self.rect.right = gw.width_pixels

        if new_rect.top >= 0 and new_rect.bottom < gw.height_pixels:
            self.rect.move_ip(0, self.move_velocity[1])
        elif new_rect.top < 0:
            self.rect.top = 0
        elif new_rect.bottom > gw.height_pixels:
            self.rect.bottom = gw.height_pixels

        self.surf_rendered = self.surf.subsurface(self.rect)


class Entities(pg.sprite.Group):
    def draw(self, scene):
        sprites = self.sprites()
        for spr in sorted(sprites, key=lambda spr: spr.pos[1]):
            if spr.rect.colliderect(scene.rect):
                scene.image.blit(spr.surf, spr.rect)
        self.lostsprites = []


def zoom(gw, button, factor):
    if (gw.tile_s <= 15 and factor < 1) or (gw.tile_s >= 120 and factor > 1):
        return

    gw.tile_s = int(gw.tile_s * factor)
    gw.width_pixels = int(gw.width_pixels * factor)
    gw.height_pixels = int(gw.height_pixels * factor)
    gw.scene.image = pg.transform.scale(gw.scene.image, (gw.width_pixels, gw.height_pixels))
    gw.scene.surf_raw = pg.transform.scale(gw.scene.surf_raw, (gw.width_pixels, gw.height_pixels))
    gw.cursor.image = pg.transform.scale(gw.cursor.image, (gw.tile_s, gw.tile_s))
    gw.cursor.surf_demolish = pg.transform.scale(gw.cursor.surf_demolish_raw, (gw.tile_s, gw.tile_s))
    gw.hud.minimap.update_zoom(gw)

    if gw.cursor.held_structure is not None:
        gw.cursor.held_structure.image = pg.transform.scale(gw.cursor.held_structure.image, (
            gw.cursor.held_structure.surf_ratio[0] * gw.tile_s, gw.cursor.held_structure.surf_ratio[1] * gw.tile_s))

    for struct in gw.structs:
        struct.update_zoom(gw)

    if gw.scene.rect.centerx * factor + gw.scene.rect.width / 2 > gw.width_pixels:
        gw.scene.rect.right = gw.width_pixels
    elif gw.scene.rect.centerx * factor - gw.scene.rect.width / 2 < 0:
        gw.scene.rect.left = 0
    else:
        gw.scene.rect.centerx = int(gw.scene.rect.centerx * factor)

    if gw.scene.rect.centery * factor + gw.scene.rect.height / 2 > gw.height_pixels:
        gw.scene.rect.bottom = gw.height_pixels
    elif gw.scene.rect.centery * factor - gw.scene.rect.height / 2 < 0:
        gw.scene.rect.top = 0
    else:
        gw.scene.rect.centery = int(gw.scene.rect.centery * factor)