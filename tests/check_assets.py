import os
import sys
from pathlib import Path
import pygame

# Initialize headless pygame
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
pygame.display.set_mode((1, 1))

workspace_dir = Path("/home/zunayed-mahmood/storage/Dev/Games/EchoRunner")
asset_paths = {
    "tile_wall": "assetLibrary/tiles/png/tile_wall.png",
    "tile_corridor": "assetLibrary/tiles/png/tile_corridor.png",
    "tile_junction": "assetLibrary/tiles/png/tile_junction.png",
    "tile_pellet": "assetLibrary/tiles/png/tile_pellet.png",
    "tile_power": "assetLibrary/tiles/png/tile_power.png",
    "tile_safe_pocket": "assetLibrary/tiles/png/tile_safe_pocket.png",
    "tile_enemy_gate": "assetLibrary/tiles/png/tile_enemy_gate.png",
    "tile_warp": "assetLibrary/tiles/png/tile_warp.png",
    "tile_unknown": "assetLibrary/tiles/png/tile_unknown.png",
    "player_echo_runner": "assetLibrary/sprites/png/player_echo_runner.png",
    "enemy_hunter": "assetLibrary/sprites/png/enemy_hunter.png",
    "enemy_ambusher": "assetLibrary/sprites/png/enemy_ambusher.png",
    "enemy_trickster": "assetLibrary/sprites/png/enemy_trickster.png",
    "enemy_coward": "assetLibrary/sprites/png/enemy_coward.png",
    "pellet_echo_orb": "assetLibrary/sprites/png/pellet_echo_orb.png",
    "power_resonance_core": "assetLibrary/sprites/png/power_resonance_core.png",
    "fruit_signal_gem": "assetLibrary/sprites/png/fruit_signal_gem.png",
    "life_token": "assetLibrary/sprites/png/life_token.png",
}

for name, rel_path in asset_paths.items():
    full_path = workspace_dir / rel_path
    if not full_path.exists():
        print(f"ERROR: {name} path does not exist: {full_path}")
        continue
    try:
        img = pygame.image.load(str(full_path)).convert_alpha()
        print(f"SUCCESS: {name} loaded successfully, size: {img.get_size()}")
    except Exception as e:
        print(f"FAILED: {name} load failed: {e}")
