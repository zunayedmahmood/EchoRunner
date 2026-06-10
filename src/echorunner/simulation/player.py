"""Player movement and state representation for EchoRunner."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from echorunner.simulation.world import Vec2


class Player:
    """Represents the player runner within the simulation grid."""

    def __init__(self, start_tile: Vec2) -> None:
        self.tile = start_tile
        self.direction = "right"
        self.queued_direction: str | None = None

    def queue_turn(self, direction: str) -> None:
        """Queues a turn to be executed at the next available junction."""
        self.queued_direction = direction

    def move_to(self, target_tile: Vec2, direction: str) -> None:
        """Moves the player to a target tile and updates their facing direction."""
        self.tile = target_tile
        self.direction = direction
