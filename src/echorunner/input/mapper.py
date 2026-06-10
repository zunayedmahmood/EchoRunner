"""Raw Pygame keys to semantic commands mapper for EchoRunner."""
from __future__ import annotations

from enum import Enum, auto
import pygame


class Command(Enum):
    MOVE_UP = auto()
    MOVE_DOWN = auto()
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()
    SCAN_SHORT = auto()
    SCAN_DEEP = auto()
    REPEAT_LAST = auto()
    HELP = auto()
    CONFIRM = auto()
    BACK = auto()
    PAUSE = auto()
    TOGGLE_TRAINER = auto()
    AUDIO_TEST = auto()
    TOGGLE_CUE_DENSITY = auto()
    MUTE_MUSIC = auto()
    MARK_CONFUSION = auto()



class InputMapper:
    """Maps raw keyboard events into semantic game commands, supporting six-key home row layouts."""

    def __init__(self) -> None:
        self.six_key_mode = False

        self.default_mappings: dict[int, Command] = {
            # Movement (Primary + Alternates)
            pygame.K_UP: Command.MOVE_UP,
            pygame.K_w: Command.MOVE_UP,
            pygame.K_DOWN: Command.MOVE_DOWN,
            pygame.K_s: Command.MOVE_DOWN,
            pygame.K_LEFT: Command.MOVE_LEFT,
            pygame.K_a: Command.MOVE_LEFT,
            pygame.K_RIGHT: Command.MOVE_RIGHT,
            pygame.K_d: Command.MOVE_RIGHT,

            # Menu navigation & validation
            pygame.K_RETURN: Command.CONFIRM,
            pygame.K_KP_ENTER: Command.CONFIRM,
            pygame.K_ESCAPE: Command.BACK,
            pygame.K_BACKSPACE: Command.BACK,

            # Gameplay actions
            pygame.K_p: Command.PAUSE,
            pygame.K_r: Command.REPEAT_LAST,
            pygame.K_F5: Command.REPEAT_LAST,
            pygame.K_h: Command.HELP,
            pygame.K_F1: Command.HELP,

            # Function Keys
            pygame.K_F2: Command.AUDIO_TEST,
            pygame.K_F3: Command.TOGGLE_CUE_DENSITY,
            pygame.K_F8: Command.MARK_CONFUSION,
            pygame.K_F9: Command.TOGGLE_TRAINER,
            pygame.K_F10: Command.MUTE_MUSIC,

        }

        # Six-key Braille home row layouts
        self.six_key_mappings: dict[int, Command] = {
            pygame.K_s: Command.MOVE_LEFT,
            pygame.K_d: Command.MOVE_UP,
            pygame.K_f: Command.SCAN_SHORT,
            pygame.K_j: Command.CONFIRM,
            pygame.K_k: Command.MOVE_DOWN,
            pygame.K_l: Command.MOVE_RIGHT,
        }

    def map_event(self, event: pygame.event.Event) -> Command | None:
        """Converts a pygame event to a Command if applicable, otherwise returns None."""
        if event.type != pygame.KEYDOWN:
            return None

        # Six-key layout overrides
        if self.six_key_mode and event.key in self.six_key_mappings:
            return self.six_key_mappings[event.key]

        # Scan modifiers checks
        if event.key == pygame.K_SPACE:
            mods = pygame.key.get_mods()
            if mods & pygame.KMOD_SHIFT:
                return Command.SCAN_DEEP
            return Command.SCAN_SHORT

        if event.key == pygame.K_KP0:
            return Command.SCAN_SHORT

        if event.key == pygame.K_TAB:
            return Command.SCAN_DEEP

        return self.default_mappings.get(event.key)
