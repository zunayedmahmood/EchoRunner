"""Headless test bot runner for EchoRunner game simulation."""
from __future__ import annotations

import random
from pathlib import Path
from echorunner.simulation.engine import GameSimulation, Vec2
from echorunner.input.mapper import Command

def choose_wall_hugger(sim: GameSimulation) -> str:
    curr_dir = sim.player_dir or "up"
    open_dirs = sim.get_open_directions(sim.player_pos)
    
    # Left-hand rule priority relative to current heading
    if curr_dir == "up":
        pref = ["left", "up", "right", "down"]
    elif curr_dir == "left":
        pref = ["down", "left", "up", "right"]
    elif curr_dir == "down":
        pref = ["right", "down", "left", "up"]
    else:  # right
        pref = ["up", "right", "down", "left"]
        
    for d in pref:
        if d in open_dirs:
            return d
    return curr_dir

def choose_random(sim: GameSimulation) -> str:
    open_dirs = sim.get_open_directions(sim.player_pos)
    if not open_dirs:
        return "up"
    curr_dir = sim.player_dir or "up"
    opposite = {"up": "down", "down": "up", "left": "right", "right": "left"}[curr_dir]
    choices = [d for d in open_dirs if d != opposite]
    if choices:
        return random.choice(choices)
    return random.choice(open_dirs)

def choose_safe_scan(sim: GameSimulation) -> str:
    curr_pos = sim.player_pos
    open_dirs = sim.get_open_directions(curr_pos)
    if not open_dirs:
        return "up"
        
    # Check for threats
    dangerous_enemies = []
    for enemy in sim.enemies:
        threat = sim.classify_threat(enemy)
        if threat in ("red", "amber"):
            dangerous_enemies.append(enemy)
            
    offsets = {"up": Vec2(0, -1), "down": Vec2(0, 1), "left": Vec2(-1, 0), "right": Vec2(1, 0)}
    
    if dangerous_enemies:
        best_dir = open_dirs[0]
        max_dist = -1
        for d in open_dirs:
            neighbor = Vec2(curr_pos.x + offsets[d].x, curr_pos.y + offsets[d].y)
            min_enemy_dist = min([sim.shortest_path(neighbor, enemy.tile) for enemy in dangerous_enemies])
            if min_enemy_dist > max_dist:
                max_dist = min_enemy_dist
                best_dir = d
        return best_dir
        
    # No threats: target nearest orb/core
    targets = list(sim.orbs)
    if not targets:
        return open_dirs[0]
        
    best_dir = open_dirs[0]
    min_path_len = 9999
    for d in open_dirs:
        neighbor = Vec2(curr_pos.x + offsets[d].x, curr_pos.y + offsets[d].y)
        for target in targets:
            dist = sim.shortest_path(neighbor, target)
            if dist < min_path_len:
                min_path_len = dist
                best_dir = d
    return best_dir

def choose_perfect(sim: GameSimulation) -> str:
    curr_pos = sim.player_pos
    open_dirs = sim.get_open_directions(curr_pos)
    if not open_dirs:
        return "up"
        
    offsets = {"up": Vec2(0, -1), "down": Vec2(0, 1), "left": Vec2(-1, 0), "right": Vec2(1, 0)}
    
    # Identify tiles occupied by or adjacent to active enemies
    enemy_danger_zones = set()
    for enemy in sim.enemies:
        if enemy.state != "frightened":
            enemy_danger_zones.add(enemy.tile)
            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                enemy_danger_zones.add(Vec2(enemy.tile.x + dx, enemy.tile.y + dy))
                
    def shortest_path_safe(start: Vec2, end: Vec2) -> list[Vec2] | None:
        from collections import deque
        if start == end:
            return [start]
        queue = deque([[start]])
        visited = {start}
        while queue:
            path = queue.popleft()
            curr = path[-1]
            if curr == end:
                return path
            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                neighbor = Vec2(curr.x + dx, curr.y + dy)
                if neighbor in sim.walkable_tiles and neighbor not in visited:
                    if neighbor == end or neighbor not in enemy_danger_zones:
                        visited.add(neighbor)
                        queue.append(path + [neighbor])
        return None

    # Target nearest orb
    nearest_path = None
    for target in sim.orbs:
        path = shortest_path_safe(curr_pos, target)
        if path:
            if nearest_path is None or len(path) < len(nearest_path):
                nearest_path = path
                
    if nearest_path and len(nearest_path) > 1:
        next_tile = nearest_path[1]
        for d, offset in offsets.items():
            if Vec2(curr_pos.x + offset.x, curr_pos.y + offset.y) == next_tile:
                return d
                
    # Fallback to Safe Scan
    return choose_safe_scan(sim)

def run_headless_simulation(level_id: str, bot_type: str, runs: int = 1) -> dict:
    """Runs a headless simulation of the game with the specified bot."""
    workspace_dir = Path(__file__).parent.parent.parent.parent
    
    successes = 0
    total_steps = 0
    total_deaths = 0
    
    dir_to_command = {
        "up": Command.MOVE_UP,
        "down": Command.MOVE_DOWN,
        "left": Command.MOVE_LEFT,
        "right": Command.MOVE_RIGHT,
    }
    
    print(f"\n--- Running headless test: level={level_id}, bot={bot_type}, runs={runs} ---")
    
    for r in range(runs):
        sim = GameSimulation(workspace_dir, level_id)
        steps = 0
        max_steps = 2000
        lives = 3
        
        while len(sim.orbs) > 0 and steps < max_steps and lives > 0:
            # Choose move
            if bot_type == "wall_hugger":
                chosen_dir = choose_wall_hugger(sim)
            elif bot_type == "random":
                chosen_dir = choose_random(sim)
            elif bot_type == "safe_scan":
                chosen_dir = choose_safe_scan(sim)
            elif bot_type == "perfect":
                chosen_dir = choose_perfect(sim)
            else:
                raise ValueError(f"Unknown bot type: {bot_type}")
                
            cmd = dir_to_command[chosen_dir]
            # Advance simulation step (dt = 1/30 second)
            dt = 1.0 / 30.0
            
            # Step the simulation
            sim.step(dt, [cmd])
            
            # Check for events
            for event in sim.events:
                if event.get("type") == "player_killed":
                    lives -= 1
                    total_deaths += 1
                    # Reset player/enemy position as per life lost
                    sim.player_pos = Vec2(1, 1)  # simple fallback reset
                    
            steps += 1
            
        if len(sim.orbs) == 0 and lives > 0:
            successes += 1
            
        total_steps += steps
        
    success_rate = (successes / runs) * 100.0
    avg_steps = total_steps / runs
    
    print(f"Results:")
    print(f"  Success Rate: {success_rate:.1f}% ({successes}/{runs})")
    print(f"  Average Steps: {avg_steps:.1f}")
    print(f"  Total Player Deaths: {total_deaths}")
    print("-" * 50)
    
    return {
        "success_rate": success_rate,
        "avg_steps": avg_steps,
        "total_deaths": total_deaths,
    }
