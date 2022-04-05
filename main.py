from functions import *
from gameworld import GameWorld
from pygame.locals import (K_SPACE,
                           KEYDOWN,
                           QUIT,
                           K_ESCAPE,
                           K_n,
                           K_x,
                           K_q,
                           K_F3)

if __name__ == "__main__":

    pg.init()
    pg.mixer.init()
    gw = GameWorld()

    tile_statistics = TileStatistics(gw)
    build_menu = BuildMenu(gw)
    minimap = Minimap(gw)
    top_bar = TopBar(gw)

    prev_pos = (0, 0)

    clock = pg.time.Clock()
    press_hold, remove_hold = False, False
    display_stats, display_build_menu = True, True
    structure_ghost = None
    on_button = False
    curr_button, prev_button = None, None

    gw.speech_channel.play(gw.sounds["General_Startgame"])
    running = True
    # ------ MAIN LOOP -------
    while running:

        pressed_keys = pg.key.get_pressed()
        # checking events
        if gw.MOUSE_STEERING:
            on_button = False
            for button in gw.buttons:
                if button.rect.collidepoint(pg.mouse.get_pos()):
                    curr_button = button
                    on_button = True

            if not on_button:
                gw.cursor.update(gw)
                curr_button = None
        else:
            gw.cursor.update_arrows(gw, pressed_keys)

        for event in pg.event.get():
            if event.type == QUIT:
                running = False
            if event.type == KEYDOWN:

                if event.key in gw.key_structure_dict:  # picking up a chosen structure
                    gw.cursor.hold = gw.key_structure_dict[event.key]([0, 0], gw)
                    gw.cursor.ghost = Ghost(gw)
                    gw.sounds["menusl_" + str(randint(1, 3))].play()

                if event.key == K_n:
                    gw.cursor.hold = None

                if event.key == K_q and isinstance(gw.cursor.hold, Gate):
                    gw.cursor.hold.rotate(gw)

                if event.key == pg.K_c and isinstance((gw.struct_map[gw.cursor.pos[0]][gw.cursor.pos[1]]), House):
                    gw.struct_map[gw.cursor.pos[0]][gw.cursor.pos[1]].update_profit(gw)

                if event.key == pg.K_j and isinstance((gw.struct_map[gw.cursor.pos[0]][gw.cursor.pos[1]]), Wall):
                    for x in gw.surrounded_tiles:
                        print(x)

                if event.key == K_F3:
                    display_stats = not display_stats

                if event.key == pg.K_KP_PLUS and gw.tile_s < 120:
                    zoom(gw, 2, minimap)

                if event.key == pg.K_KP_MINUS and gw.tile_s > 15:
                    zoom(gw, 0.5, minimap)

                if event.key == pg.K_e:
                    if display_build_menu:
                        gw.buttons.difference_update(build_menu.buttons)
                    else:
                        build_menu = BuildMenu(gw)
                    display_build_menu = not display_build_menu

                if event.key == K_ESCAPE:
                    menu_open = True
                    pause_menu = PauseMenu(gw)
                    prev_button = None
                    load = False
                    while menu_open:
                        on_button = False
                        curr_button = None
                        gw.screen.blit(pause_menu.surf, pause_menu.rect)
                        for button in pause_menu.buttons:
                            if button.rect.collidepoint(pg.mouse.get_pos()):
                                curr_button = button
                                on_button = True
                                curr_button.hovered(gw)
                        if pg.mouse.get_pressed(num_buttons=3)[0] and on_button:
                            curr_button.pressed(gw)
                            menu_open, running, load = curr_button.press(gw, press_hold)
                            if not press_hold:
                                gw.sounds["woodpush2"].play()
                            press_hold = True
                        else:
                            press_hold = False
                        if curr_button is not None and prev_button is not curr_button:
                            gw.sounds["woodrollover" + str(randint(2, 5))].play()
                        prev_button = curr_button
                        if load:
                            with open("saves/savefile.json", "r") as f:
                                gw = GameWorld()
                                gw.from_json(json.load(f))
                                if display_build_menu:
                                    build_menu = BuildMenu(gw)

                        for event in pg.event.get():
                            if event.type == KEYDOWN and event.key == K_ESCAPE:
                                menu_open = False
                                break
                        pg.display.flip()

        if pressed_keys[K_SPACE] or pg.mouse.get_pressed(num_buttons=3)[0]:  # placing down held structure
            if not on_button:
                place_structure(gw, prev_pos, press_hold)
            else:
                curr_button.press(gw, press_hold)
            press_hold = True
        else:
            press_hold = False

        if pressed_keys[K_x]:  # removing a structure
            if remove_structure(gw, remove_hold):
                remove_hold = True
        else:
            remove_hold = False
        prev_pos = tuple(gw.cursor.pos)
        gw.background.move_screen(gw)

        for struct in gw.structs:
            struct.get_profit(gw)

        if gw.vault.gold < -50:
            running = False

        gw.entities.draw(gw.background)
        if curr_button is None:
            gw.cursor.draw(gw)


        # if gw.cursor.hold is not None:
        #     gw.cursor.ghost.update(gw, gw.cursor)
        #     gw.background.surf.blit(gw.cursor.ghost.surf, gw.cursor.ghost.rect)

        # gw.background.surf.blit(gw.cursor.surf, gw.cursor.rect)

        if gw.SOUNDTRACK and not gw.soundtrack_channel.get_busy():
            gw.soundtrack_channel.play(gw.tracks[randint(0, 13)])
        if randint(1, 200000) == 1: gw.sounds["Random_Events13"].play()

        gw.screen.blit(gw.background.surf_rendered, (0, 0))

        if display_stats:
            gw.global_statistics.update_global_stats(gw)
            tile_statistics.update_tile_stats(gw.cursor.pos, gw)
        if display_build_menu:
            gw.screen.blit(build_menu.surf, build_menu.rect)
        minimap.update_minimap(gw)
        top_bar.update(gw)

        if curr_button is not None:
            if not press_hold:
                if prev_button is not curr_button:
                    gw.sounds["woodrollover" + str(randint(2, 5))].play()
                curr_button.hovered(gw)
            else:
                curr_button.pressed(gw)
        prev_button = curr_button

        gw.background.surf_rendered.blit(gw.background.surf_raw.subsurface(gw.background.rect), (0, 0))
        pg.display.flip()

        clock.tick(gw.TICK_RATE)
    pg.quit()
