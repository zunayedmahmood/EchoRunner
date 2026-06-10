"""Deterministic core simulation engine for EchoRunner."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import json
import logging
from pathlib import Path
import random
from typing import Any

from echorunner.input.mapper import Command
from echorunner.simulation.world import Vec2

logger = logging.getLogger(__name__)



@dataclass
class EnemyState:
    enemy_id: str
    archetype: str
    tile: Vec2
    direction: str
    state: str = "patrol"
    threat: str = "silent"
    speed: float = 2.0
    home_tile: Vec2 = Vec2(0, 0)
    intercept_estimate: float = 999.0
    player_hint: str = ""
    source_pos: tuple[float, float, float] = (0.0, 0.0, 0.0)
    cue_priority: int = 0



@dataclass
class SimulationFrame:
    player_pos: Vec2
    player_dir: str
    enemies: list[EnemyState]
    collected_orbs: int
    remaining_orbs: int
    power_timer: int
    open_directions: list[str]
    threat_levels: dict[str, str]  # enemy_id -> threat state
    events: list[dict] = field(default_factory=list)


class GameSimulation:
    """Independent, deterministic game simulation engine."""

    def __init__(self, workspace_dir: Path, level_id: str, seed: int = 42) -> None:
        self.workspace_dir = workspace_dir
        self.level_id = level_id
        self.seed = seed
        self.rng = random.Random(seed)
        self.mode_state = "patrol"
        self.mode_ticks = 0

        # Configuration and Grid variables
        self.grid: list[str] = []
        self.width = 0
        self.height = 0
        self.walkable_tiles: set[Vec2] = set()
        self.junctions: set[Vec2] = set()

        # Accessibility and UI variables
        self.low_stress_mode = False
        self.cue_density = "beginner"

        # Gameplay entities state
        self.player_pos = Vec2(0, 0)
        self.player_dir = "right"
        self.player_queued_dir: str | None = None
        self.player_speed = 3.0  # default tiles/sec

        self.enemies: list[EnemyState] = []
        self.orbs: set[Vec2] = set()
        self.power_cores: set[Vec2] = set()
        self.landmarks: list[dict] = []
        self.power_timer = 0
        self.collected_count = 0
        self.total_orbs = 0

        # Accumulated delta times (independent of pygame framerate)
        self.player_accumulator = 0.0
        self.enemy_accumulators: dict[str, float] = {}
        self.power_expired_ticks = 9999

        # Reset lists of events
        self.events: list[dict] = []

        self.load_level()

    def load_level(self) -> None:
        """Loads level JSON configuration and builds static grid sets."""
        if self.level_id.startswith("tutorial_mod_"):
            try:
                module_num = int(self.level_id.split("_")[-1])
            except ValueError:
                module_num = 1
            
            # Setup specific tutorial modules
            if module_num == 1:
                self.grid = ["#######", "#P....#", "#######"]
            elif module_num == 2:
                self.grid = [
                    "#######",
                    "###.#.#",
                    "#P..#.#",
                    "#######"
                ]
            elif module_num == 3:
                self.grid = ["#######", "#P....#", "#######"]
            elif module_num == 4:
                self.grid = ["#######", "#P....#", "#######"]
            elif module_num == 5:
                self.grid = ["#########", "#P......#", "#########"]
            elif module_num == 6:
                self.grid = ["#########", "#P..o...#", "#########"]
            elif module_num == 7:
                # Load real level for final practice
                path = self.workspace_dir / "levels" / "level_01_training_loop.json"
                if path.exists():
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self.grid = data["grid"]
                else:
                    self.grid = ["#######", "#P....#", "#######"]

            self.height = len(self.grid)
            self.width = len(self.grid[0]) if self.height > 0 else 0
            
            for y, row in enumerate(self.grid):
                for x, char in enumerate(row):
                    if char != "#":
                        self.walkable_tiles.add(Vec2(x, y))
                    if char == "P":
                        self.player_pos = Vec2(x, y)
                    elif char == ".":
                        self.orbs.add(Vec2(x, y))
                    elif char == "o":
                        self.orbs.add(Vec2(x, y))
                        self.power_cores.add(Vec2(x, y))

            self.total_orbs = len(self.orbs)

            # Spawn tutorial enemies
            if module_num == 5:
                self.player_pos = Vec2(3, 1)
                start = Vec2(1, 1)
                enemy = EnemyState(
                    enemy_id="tutorial_hunter",
                    archetype="hunter",
                    tile=start,
                    direction="right",
                    state="patrol",
                    speed=1.5,
                    home_tile=start
                )
                self.enemies.append(enemy)
                self.enemy_accumulators[enemy.enemy_id] = 0.0
            elif module_num == 6:
                start = Vec2(7, 1)
                enemy = EnemyState(
                    enemy_id="tutorial_hunter",
                    archetype="hunter",
                    tile=start,
                    direction="left",
                    state="patrol",
                    speed=1.0,
                    home_tile=start
                )
                self.enemies.append(enemy)
                self.enemy_accumulators[enemy.enemy_id] = 0.0
            elif module_num == 7:
                path = self.workspace_dir / "levels" / "level_01_training_loop.json"
                if path.exists():
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    for rule in data.get("enemy_rules", []):
                        start = Vec2(rule["start"][0], rule["start"][1])
                        enemy = EnemyState(
                            enemy_id=rule["id"],
                            archetype=rule["archetype"],
                            tile=start,
                            direction="left",
                            state=rule.get("state", "patrol"),
                            speed=rule.get("speed", 2.0),
                            home_tile=start,
                        )
                        self.enemies.append(enemy)
                        self.enemy_accumulators[enemy.enemy_id] = 0.0

            # Define junctions
            for tile in self.walkable_tiles:
                open_paths = self.get_open_directions(tile)
                if len(open_paths) > 2:
                    self.junctions.add(tile)
            return

        path = self.workspace_dir / "levels" / f"{self.level_id}.json"
        if not path.exists():
            # Fallback tutorial-level stubs
            self.grid = ["#######", "#P....#", "#######"]
            self.player_pos = Vec2(1, 1)
            self.walkable_tiles = {Vec2(x, 1) for x in range(1, 6)}
            self.orbs = {Vec2(x, 1) for x in range(2, 6)}
            self.total_orbs = len(self.orbs)
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.grid = data["grid"]
            self.height = len(self.grid)
            self.width = len(self.grid[0]) if self.height > 0 else 0

            # Parse grid characters
            for y, row in enumerate(self.grid):
                for x, char in enumerate(row):
                    if char != "#":
                        self.walkable_tiles.add(Vec2(x, y))
                    if char == "P":
                        self.player_pos = Vec2(x, y)
                    elif char == ".":
                        self.orbs.add(Vec2(x, y))
                    elif char == "o":
                        self.orbs.add(Vec2(x, y))
                        self.power_cores.add(Vec2(x, y))

            self.total_orbs = len(self.orbs)
            self.landmarks = data.get("audio_landmarks", [])

            # Parse enemy rules
            for rule in data.get("enemy_rules", []):
                start = Vec2(rule["start"][0], rule["start"][1])
                enemy = EnemyState(
                    enemy_id=rule["id"],
                    archetype=rule["archetype"],
                    tile=start,
                    direction="left",
                    state=rule.get("state", "patrol"),
                    speed=rule.get("speed", 2.0),
                    home_tile=start,
                )
                self.enemies.append(enemy)
                self.enemy_accumulators[enemy.enemy_id] = 0.0

            # Define junctions
            for tile in self.walkable_tiles:
                open_paths = self.get_open_directions(tile)
                if len(open_paths) > 2:
                    self.junctions.add(tile)

        except Exception as e:
            logger.error(f"Error parsing level json: {e}")

    def get_open_directions(self, tile: Vec2) -> list[str]:
        """Returns directions from tile that are not walls."""
        open_dirs = []
        directions = {
            "up": Vec2(0, -1),
            "down": Vec2(0, 1),
            "left": Vec2(-1, 0),
            "right": Vec2(1, 0),
        }
        for d, offset in directions.items():
            neighbor = Vec2(tile.x + offset.x, tile.y + offset.y)
            if neighbor in self.walkable_tiles:
                open_dirs.append(d)
        return open_dirs

    def shortest_path(self, start: Vec2, end: Vec2) -> int:
        """BFS helper computing path length between coordinates."""
        if start == end:
            return 0
        queue: deque[tuple[Vec2, int]] = deque([(start, 0)])
        visited = {start}

        while queue:
            curr, dist = queue.popleft()
            if curr == end:
                return dist

            directions = [Vec2(0, -1), Vec2(0, 1), Vec2(-1, 0), Vec2(1, 0)]
            for offset in directions:
                neighbor = Vec2(curr.x + offset.x, curr.y + offset.y)
                if neighbor in self.walkable_tiles and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, dist + 1))
        return 999  # unreachable

    def line_of_sight(self, tile1: Vec2, tile2: Vec2) -> bool:
        """Returns True if tiles share row/column without intervening walls."""
        if tile1.x == tile2.x:
            step = 1 if tile2.y > tile1.y else -1
            for y in range(tile1.y + step, tile2.y, step):
                if Vec2(tile1.x, y) not in self.walkable_tiles:
                    return False
            return True
        elif tile1.y == tile2.y:
            step = 1 if tile2.x > tile1.x else -1
            for x in range(tile1.x + step, tile2.x, step):
                if Vec2(x, tile1.y) not in self.walkable_tiles:
                    return False
            return True
        return False

    def classify_threat(self, enemy: EnemyState) -> str:
        """Categorizes danger levels based on route distance and corridors."""
        # Update source position
        enemy.source_pos = (float(enemy.tile.x), 0.0, float(enemy.tile.y))

        if enemy.state == "frightened":
            enemy.intercept_estimate = 999.0
            enemy.player_hint = "Chase the frightened creature to eat it!"
            enemy.cue_priority = 30
            return "frightened"

        route_dist = self.shortest_path(enemy.tile, self.player_pos)
        same_corridor = self.line_of_sight(enemy.tile, self.player_pos)

        # Estimate intercept time: distance / sum of speeds
        player_speed = self.player_speed
        enemy_speed = enemy.speed * 0.5 if self.low_stress_mode else enemy.speed
        total_speed = player_speed + enemy_speed
        intercept_time = route_dist / total_speed if total_speed > 0 else 999.0
        enemy.intercept_estimate = intercept_time

        red_threshold = 2.0 if self.low_stress_mode else 1.4
        if same_corridor and intercept_time < red_threshold:
            enemy.player_hint = "Run in the opposite direction!"
            enemy.cue_priority = 100
            return "red"
        elif intercept_time < red_threshold:
            enemy.player_hint = "Turn at the next corner!"
            enemy.cue_priority = 90
            return "red"

        if intercept_time < 3.0:
            enemy.player_hint = "Keep moving away from the sound."
            if enemy.tile in self.junctions:
                enemy.cue_priority = 80
            else:
                enemy.cue_priority = 70
            return "amber"

        if route_dist <= 6:
            enemy.player_hint = "An enemy is nearby."
            enemy.cue_priority = 30
            return "green"

        enemy.player_hint = ""
        enemy.cue_priority = 0
        return "silent"

    def step(self, dt: float, commands: list[Command]) -> SimulationFrame:
        """Advances simulation delta times, updating physics, coordinates, and AI."""
        self.events.clear()

        # Update power mode timer
        ticks = int(round(dt * 30))
        if self.power_timer > 0:
            self.power_expired_ticks = 0
            old_timer = self.power_timer
            self.power_timer = max(0, self.power_timer - ticks)
            if self.power_timer == 0:
                self.events.append({"type": "power_expire"})
                for enemy in self.enemies:
                    if enemy.state in ("frightened", "return_home"):
                        self.change_enemy_state(enemy, self.mode_state)
            elif self.power_timer <= 90:
                # Play countdown tick at 90, 60, 30 frames remaining
                if (old_timer // 30) > (self.power_timer // 30):
                    self.events.append({"type": "power_countdown"})
        else:
            self.power_expired_ticks += ticks
            # Update mode timer (Patrol <-> Hunt state machine)
            self.mode_ticks += ticks
            # Transition patrol <-> hunt
            # Patrol lasts 7 seconds (210 ticks), Hunt lasts 20 seconds (600 ticks)
            if self.mode_state == "patrol" and self.mode_ticks >= 210:
                self.mode_state = "hunt"
                self.mode_ticks = 0
                for enemy in self.enemies:
                    if enemy.state == "patrol":
                        self.change_enemy_state(enemy, "hunt")
            elif self.mode_state == "hunt" and self.mode_ticks >= 600:
                self.mode_state = "patrol"
                self.mode_ticks = 0
                for enemy in self.enemies:
                    if enemy.state == "hunt":
                        self.change_enemy_state(enemy, "patrol")


        # Update queued commands
        for cmd in commands:
            if cmd == Command.MOVE_UP:
                self.player_queued_dir = "up"
            elif cmd == Command.MOVE_DOWN:
                self.player_queued_dir = "down"
            elif cmd == Command.MOVE_LEFT:
                self.player_queued_dir = "left"
            elif cmd == Command.MOVE_RIGHT:
                self.player_queued_dir = "right"

        # 1. Update Player Movement Accumulator
        self.player_accumulator += dt
        player_interval = 1.0 / self.player_speed

        if self.player_accumulator >= player_interval:
            self.player_accumulator -= player_interval
            self.move_player()

        # 2. Update Enemy AI Accumulators
        for enemy in self.enemies:
            self.enemy_accumulators[enemy.enemy_id] += dt
            espeed = enemy.speed * 0.5 if self.low_stress_mode else enemy.speed
            enemy_interval = 1.0 / espeed if espeed > 0 else 999.0

            if self.enemy_accumulators[enemy.enemy_id] >= enemy_interval:
                self.enemy_accumulators[enemy.enemy_id] -= enemy_interval
                self.move_enemy(enemy)

        # 3. Check overlaps / collisions
        self.check_collisions()

        # 4. Threat classifications
        threat_levels = {}
        for enemy in self.enemies:
            threat = self.classify_threat(enemy)
            enemy.threat = threat
            threat_levels[enemy.enemy_id] = threat

        return SimulationFrame(
            player_pos=self.player_pos,
            player_dir=self.player_dir,
            enemies=self.enemies,
            collected_orbs=self.collected_count,
            remaining_orbs=len(self.orbs),
            power_timer=self.power_timer,
            open_directions=self.get_open_directions(self.player_pos),
            threat_levels=threat_levels,
            events=list(self.events),
        )

    def move_player(self) -> None:
        """Moves the player based on orientation queue and checks wall hits."""
        d = self.player_queued_dir or self.player_dir
        offset = {
            "up": Vec2(0, -1),
            "down": Vec2(0, 1),
            "left": Vec2(-1, 0),
            "right": Vec2(1, 0),
        }[d]
        target = Vec2(self.player_pos.x + offset.x, self.player_pos.y + offset.y)

        if target in self.walkable_tiles:
            old_pos = self.player_pos
            self.player_pos = target
            self.player_dir = d
            self.events.append({
                "type": "move",
                "from": [old_pos.x, old_pos.y],
                "to": [target.x, target.y],
                "direction": d
            })

            # Junction trigger event
            if self.player_pos in self.junctions:
                self.events.append(
                    {
                        "type": "junction_reached",
                        "pos": self.player_pos,
                        "open_dirs": self.get_open_directions(self.player_pos),
                    }
                )

            # Check collection
            if self.player_pos in self.orbs:
                self.orbs.remove(self.player_pos)
                self.collected_count += 1
                is_core = self.player_pos in self.power_cores

                if is_core:
                    self.power_timer = 360 if self.low_stress_mode else 240
                    for enemy in self.enemies:
                        self.change_enemy_state(enemy, "frightened")
                    self.events.append({"type": "power_activate"})
                else:
                    self.events.append({"type": "orb_collected"})

                if len(self.orbs) == 0:
                    self.events.append({"type": "level_clear"})
            else:
                if self.cue_density != "expert":
                    self.events.append({"type": "footstep"})
        else:
            self.events.append({"type": "wall_knock"})

        self.player_queued_dir = None

    def move_enemy(self, enemy: EnemyState) -> None:
        """Calculates archetype pathing step and updates enemy grid coordinate."""
        target = self.determine_enemy_target(enemy)
        neighbors = self.get_open_directions(enemy.tile)
        if not neighbors:
            return

        # Find best neighboring direction towards target
        best_dir = enemy.direction
        min_dist = 9999

        directions = {
            "up": Vec2(0, -1),
            "down": Vec2(0, 1),
            "left": Vec2(-1, 0),
            "right": Vec2(1, 0),
        }

        # Prevent immediate 180-degree turns unless forced
        opposite = {
            "up": "down",
            "down": "up",
            "left": "right",
            "right": "left",
        }[enemy.direction]

        for d in neighbors:
            if d == opposite and len(neighbors) > 1:
                continue
            offset = directions[d]
            neighbor_pos = Vec2(enemy.tile.x + offset.x, enemy.tile.y + offset.y)
            dist = self.shortest_path(neighbor_pos, target)
            if dist < min_dist:
                min_dist = dist
                best_dir = d

        offset = directions[best_dir]
        enemy.tile = Vec2(enemy.tile.x + offset.x, enemy.tile.y + offset.y)
        enemy.direction = best_dir

    def determine_enemy_target(self, enemy: EnemyState) -> Vec2:
        """Determines target coordinate base on archetype."""
        if enemy.state == "frightened":
            return enemy.home_tile

        if enemy.archetype == "hunter":
            return self.player_pos

        elif enemy.archetype == "ambusher":
            # Target 2-4 tiles ahead of player facing direction
            for steps in (4, 3, 2):
                offset = {
                    "up": Vec2(0, -steps),
                    "down": Vec2(0, steps),
                    "left": Vec2(-steps, 0),
                    "right": Vec2(steps, 0),
                }[self.player_dir]
                target = Vec2(self.player_pos.x + offset.x, self.player_pos.y + offset.y)
                if target in self.walkable_tiles:
                    return target
            return self.player_pos

        elif enemy.archetype == "trickster":
            # Blend player tile (40%), random junction (30%), and route pressure (30%)
            val = self.rng.random()
            if val < 0.4:
                return self.player_pos
            elif val < 0.7 and self.junctions:
                return self.rng.choice(list(self.junctions))
            else:
                if self.walkable_tiles:
                    return self.rng.choice(list(self.walkable_tiles))
                return self.player_pos

        elif enemy.archetype == "coward":
            # Targets player when far, retreats to home or guards power when near
            dist = self.shortest_path(enemy.tile, self.player_pos)
            if dist > 4:
                return self.player_pos
            # Near: Guard power cores if any exist, otherwise retreat to home
            if self.power_cores:
                return list(self.power_cores)[0]
            return enemy.home_tile

        return self.player_pos

    def change_enemy_state(self, enemy: EnemyState, new_state: str) -> None:
        """Helper to modify enemy state and dispatch transition events."""
        if enemy.state != new_state:
            old_state = enemy.state
            enemy.state = new_state
            self.events.append({
                "type": "enemy_state_change",
                "enemy_id": enemy.enemy_id,
                "old_state": old_state,
                "new_state": new_state
            })

    def check_collisions(self) -> None:
        """Checks for overlaps and triggers corresponding events."""
        for enemy in self.enemies:
            if enemy.tile == self.player_pos:
                if self.power_timer > 0:
                    self.events.append(
                        {"type": "enemy_eaten", "enemy_id": enemy.enemy_id}
                    )
                    self.change_enemy_state(enemy, "return_home")
                    enemy.tile = enemy.home_tile
                    self.change_enemy_state(enemy, self.mode_state)
                else:
                    # Player killed
                    # Check if power recently expired (within 3 seconds, i.e., 90 ticks)
                    if self.power_expired_ticks < 90:
                        death_type = "power_ended"
                    elif enemy.archetype == "ambusher":
                        death_type = "ambusher_tip"
                    else:
                        death_type = "hunter_left"
                    self.events.append(
                        {
                            "type": "player_killed",
                            "enemy_id": enemy.enemy_id,
                            "death_type": death_type,
                        }
                    )

