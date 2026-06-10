"""Gameplay rules, collectibles, life loss, and state check logic for EchoRunner."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from echorunner.simulation.enemy import Enemy
    from echorunner.simulation.player import Player
    from echorunner.simulation.world import Vec2


class GameRules:
    """Handles collision detection, pellet collections, and level clear rules."""

    @staticmethod
    def check_collisions(player: Player, enemies: list[Enemy]) -> Enemy | None:
        """Checks if the player has collided with any enemy. Returns the enemy if found."""
        for enemy in enemies:
            if enemy.tile == player.tile:
                return enemy
        return None

    @staticmethod
    def check_collectibles(player_tile: Vec2, collectibles: set[Vec2]) -> bool:
        """Removes a collected orb from the set of active collectibles and returns True."""
        if player_tile in collectibles:
            collectibles.remove(player_tile)
            return True
        return False

    @staticmethod
    def check_level_clear(collectibles: set[Vec2]) -> bool:
        """Checks if all orbs have been collected."""
        return len(collectibles) == 0
