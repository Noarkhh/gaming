from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import pygame as pg

from src.ui.button import Button

if TYPE_CHECKING:
    from src.core.cursor import Cursor
    from src.sound.sound_player import SoundPlayer
    from src.graphics.scene import Scene


class ButtonManager:
    def __init__(self, cursor: Cursor, sound_player: SoundPlayer, scene: Scene) -> None:
        Button.manager = self

        self.cursor: Cursor = cursor
        self.sound_player: SoundPlayer = sound_player
        scene.button_manager = self

        self.buttons: pg.sprite.Group[Button] = pg.sprite.Group()

        self.hovered_button: Optional[Button] = None
        self.previous_hovered_button: Optional[Button] = None
        self.held_button: Optional[Button] = None

    def lmb_press(self) -> None:
        if self.hovered_button is not None:
            self.hovered_button.is_held_down = True
            self.hovered_button.play_press_sound()
            self.held_button = self.hovered_button

    def lmb_release(self) -> None:
        if self.hovered_button is self.held_button is not None:
            self.held_button.press()
        self.held_button = None

    def check_for_hovers(self) -> None:
        self.hovered_button = None
        for button in self.buttons:
            if button.rect.collidepoint(pg.mouse.get_pos()):
                self.hovered_button = button
            else:
                button.unhover()

        if self.held_button is not None:
            self.held_button.hover()
        elif self.hovered_button is not None:
            self.hovered_button.hover()

        if self.hovered_button is not None and self.hovered_button is not self.previous_hovered_button:
            self.hovered_button.play_hover_sound()

        self.previous_hovered_button = self.hovered_button


