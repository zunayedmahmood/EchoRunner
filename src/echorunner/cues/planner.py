"""Audio cue priority planner and intent translator for EchoRunner."""
from __future__ import annotations

from typing import TYPE_CHECKING
import math

from echorunner.audio.openal_backend import CueEvent

if TYPE_CHECKING:
    from echorunner.simulation.enemy import Enemy
    from echorunner.simulation.player import Player


class CuePlanner:
    """Translates the current game simulation frame into prioritized OpenAL CueEvents."""

    def __init__(self) -> None:
        pass

    def plan_cues(self, player: Player, enemies: list[Enemy]) -> list[CueEvent]:
        """Analyzes threat states and coordinates to schedule spatial or ambient audio cues."""
        cues: list[CueEvent] = []
        active_threats: list[Enemy] = []

        # 1. Filter out silent threats
        for enemy in enemies:
            if enemy.threat != "silent":
                active_threats.append(enemy)

        # 2. Sort by threat level urgency: red (90) > amber (70) > green (30) > frightened (30)
        def threat_rank(e: Enemy) -> int:
            if e.threat == "red":
                return 3
            if e.threat == "amber":
                return 2
            if e.threat == "green":
                return 1
            return 0

        active_threats.sort(key=threat_rank, reverse=True)

        # 3. Emphasize only the top 2 active threats to prevent masking/clutter (Section 10)
        for i, enemy in enumerate(active_threats[:2]):
            priority = getattr(enemy, "cue_priority", None)
            file_id = "enemy_near_green"

            if enemy.threat == "red":
                if priority is None:
                    priority = 90
                file_id = "enemy_near_red"
            elif enemy.threat == "amber":
                if priority is None:
                    priority = 70
                file_id = "enemy_near_amber"
            elif enemy.threat == "frightened":
                if priority is None:
                    priority = 30
                file_id = "enemy_frightened"
            else:
                if priority is None:
                    priority = 30

            # Apply mixing rules based on enemy archetype (Section 10)
            base_gain = 1.0
            pitch = 1.0

            # Estimate grid/euclidean distance
            dist = math.hypot(enemy.tile.x - player.tile.x, enemy.tile.y - player.tile.y)

            if enemy.archetype == "hunter":
                # Hunter: low pulse, full volume only if top threat
                base_gain = 1.0 if i == 0 else 0.4
                pitch = 0.8
            elif enemy.archetype == "ambusher":
                # Ambusher: sharp ticking, emphasize near junctions
                base_gain = 1.2 if dist < 3.0 else 0.8
                pitch = 1.2
            elif enemy.archetype == "trickster":
                # Trickster: warble, quieter unless near
                base_gain = 0.8 if dist < 4.0 else 0.3
                pitch = 1.0
            elif enemy.archetype == "coward":
                # Coward: soft oscillation
                base_gain = 0.5
                pitch = 0.9

            cues.append(
                CueEvent(
                    cue_id=f"enemy_{enemy.enemy_id}",
                    file_id=file_id,
                    priority=priority,
                    spatial=True,
                    position=(float(enemy.tile.x), 0.0, float(enemy.tile.y)),
                    gain=base_gain,
                    pitch=pitch,
                    reason=f"Enemy {enemy.enemy_id} ({enemy.archetype}) threat={enemy.threat}",
                )
            )

        # Sort planned cues by priority descending
        cues.sort(key=lambda x: x.priority, reverse=True)
        return cues
