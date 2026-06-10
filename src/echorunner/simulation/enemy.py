"""Enemy state machine, targeting, and behavior archetypes for EchoRunner."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from echorunner.simulation.world import Vec2


class Enemy:
    """Represents a hostile sound creature in the grid maze."""

    def __init__(self, enemy_id: str, archetype: str, start_tile: Vec2) -> None:
        self.enemy_id = enemy_id
        self.archetype = archetype  # hunter, ambusher, trickster, coward
        self.tile = start_tile
        self.direction = "left"
        self.state = "patrol"  # patrol, hunt, frightened, return_home
        self.threat = "silent"  # silent, green, amber, red

    def update_state(self, new_state: str) -> None:
        """Transitions the enemy into a new AI state."""
        self.state = new_state

    def determine_target(
        self, player_tile: Vec2, player_dir: str, home_tile: Vec2
    ) -> Vec2:
        """Determines the target grid coordinate based on the enemy archetype.

        - Hunter targets the player directly.
        - Ambusher targets tiles ahead of the player's direction.
        - Trickster shifts target points.
        - Coward targets a route close to the player or retreats.
        """
        if self.state == "frightened":
            return home_tile

        # Archetype logic stubs
        if self.archetype == "hunter":
            return player_tile
        elif self.archetype == "ambusher":
            # Target ahead
            return player_tile
        else:
            return player_tile
