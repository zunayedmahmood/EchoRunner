"""Pygame-based trainer visual dashboard renderer for EchoRunner."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional
import pygame

if TYPE_CHECKING:
    from echorunner.simulation.enemy import Enemy
    from echorunner.simulation.player import Player

logger = logging.getLogger(__name__)


class TrainerView:
    """Visual companion display for trainers and accessibility testers."""

    def __init__(
        self,
        width: int = 800,
        height: int = 600,
        workspace_dir: Optional[Path] = None,
    ) -> None:
        self.width = width
        self.height = height
        self.workspace_dir = workspace_dir or Path.cwd()
        self.screen: pygame.Surface | None = None
        self.font: pygame.font.Font | None = None
        self.font_bold: pygame.font.Font | None = None
        self.font_large: pygame.font.Font | None = None
        self._font_mode = ""

        # Assets mapping
        self.assets: dict[str, pygame.Surface] = {}

        # Dashboard history and state
        self.cue_history: list[str] = []

    def start(self) -> None:
        """Initializes the Pygame display window and loads assets."""
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("EchoRunner - Trainer Companion")
        self._check_fonts(high_contrast=False)
        self.load_assets()

    def load_assets(self) -> None:
        """Safely loads visual PNG tiles and sprites with graceful fallbacks."""
        asset_paths = {
            # Tiles
            "tile_wall": "assetLibrary/tiles/png/tile_wall.png",
            "tile_corridor": "assetLibrary/tiles/png/tile_corridor.png",
            "tile_junction": "assetLibrary/tiles/png/tile_junction.png",
            "tile_pellet": "assetLibrary/tiles/png/tile_pellet.png",
            "tile_power": "assetLibrary/tiles/png/tile_power.png",
            "tile_safe_pocket": "assetLibrary/tiles/png/tile_safe_pocket.png",
            "tile_enemy_gate": "assetLibrary/tiles/png/tile_enemy_gate.png",
            "tile_warp": "assetLibrary/tiles/png/tile_warp.png",
            "tile_unknown": "assetLibrary/tiles/png/tile_unknown.png",
            # Sprites
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
            full_path = self.workspace_dir / rel_path
            if full_path.exists():
                try:
                    img = pygame.image.load(str(full_path)).convert_alpha()
                    img = pygame.transform.scale(img, (24, 24))
                    self.assets[name] = img
                except Exception as e:
                    logger.warning(f"Could not load asset {name} from {full_path}: {e}")
            else:
                logger.warning(f"Asset file {name} missing at {full_path}")

    def _check_fonts(self, high_contrast: bool) -> None:
        """Dynamically instantiates scaled fonts based on accessibility modes."""
        target_mode = "hc" if high_contrast else "std"
        if self._font_mode == target_mode and self.font:
            return

        self._font_mode = target_mode
        if not pygame.font.get_init():
            pygame.font.init()

        if high_contrast:
            self.font = pygame.font.SysFont("Arial", 18, bold=True)
            self.font_bold = pygame.font.SysFont("Arial", 20, bold=True)
            self.font_large = pygame.font.SysFont("Arial", 26, bold=True)
        else:
            self.font = pygame.font.SysFont("Arial", 14)
            self.font_bold = pygame.font.SysFont("Arial", 15, bold=True)
            self.font_large = pygame.font.SysFont("Arial", 20, bold=True)

    # Clean custom Pygame drawing helpers for UI icons
    def draw_headphones_icon(self, x: int, y: int, size: int = 16) -> None:
        if not self.screen:
            return
        color = (0, 255, 255)
        pygame.draw.arc(self.screen, color, pygame.Rect(x, y, size, size), 0, 3.14, 2)
        pygame.draw.rect(self.screen, color, pygame.Rect(x, y + size // 2, 3, size // 2))
        pygame.draw.rect(self.screen, color, pygame.Rect(x + size - 3, y + size // 2, 3, size // 2))

    def draw_mono_icon(self, x: int, y: int, size: int = 16) -> None:
        if not self.screen:
            return
        color = (255, 255, 0)
        r = size // 4
        pygame.draw.circle(self.screen, color, (x + r, y + size // 2), r, 1)
        pygame.draw.circle(self.screen, color, (x + size - r, y + size // 2), r, 1)

    def draw_volume_icon(self, x: int, y: int, size: int = 16) -> None:
        if not self.screen:
            return
        color = (0, 255, 0)
        points = [
            (x, y + size // 3),
            (x + size // 3, y + size // 3),
            (x + size // 2 + 2, y + 2),
            (x + size // 2 + 2, y + size - 2),
            (x + size // 3, y + size - size // 3),
            (x, y + size - size // 3)
        ]
        pygame.draw.polygon(self.screen, color, points)
        pygame.draw.arc(self.screen, color, pygame.Rect(x + size // 2, y + 2, size // 2, size - 4), -1.5, 1.5, 1)

    def draw_danger_icon(self, x: int, y: int, size: int = 16) -> None:
        if not self.screen:
            return
        color = (255, 0, 0)
        points = [(x + size // 2, y), (x, y + size), (x + size, y + size)]
        pygame.draw.polygon(self.screen, color, points)
        if self.font:
            ex_surf = self.font.render("!", True, (255, 255, 255))
            self.screen.blit(ex_surf, (x + size // 2 - 2, y + 1))

    def draw_scan_icon(self, x: int, y: int, size: int = 16) -> None:
        if not self.screen:
            return
        color = (255, 165, 0)
        pygame.draw.circle(self.screen, color, (x + size // 2, y + size // 2), size // 2, 1)
        pygame.draw.circle(self.screen, color, (x + size // 2, y + size // 2), size // 4, 1)
        pygame.draw.line(self.screen, color, (x, y + size // 2), (x + size, y + size // 2), 1)

    def draw_telemetry_icon(self, x: int, y: int, size: int = 14) -> None:
        if not self.screen:
            return
        # Pulsing record circle
        ticks = pygame.time.get_ticks()
        color = (255, 0, 0) if (ticks // 500) % 2 == 0 else (100, 0, 0)
        pygame.draw.circle(self.screen, color, (x + size // 2, y + size // 2), size // 2)

    def render(
        self,
        grid: list[str],
        player: Player,
        enemies: list[Enemy],
        current_cue_id: str,
        instruction_text: str = "",
        high_contrast: bool = False,
        power_timer: int = 0,
        lives: int = 3,
        last_scan_result: str = "none",
        telemetry_recording: bool = False,
        level_id: str = "none",
    ) -> None:
        """Renders the comprehensive trainer dashboard."""
        if not self.screen:
            return

        self._check_fonts(high_contrast)

        # 1. Background Fill
        bg_color = (0, 0, 0) if high_contrast else (20, 20, 20)
        self.screen.fill(bg_color)

        # 2. Update cue history
        if current_cue_id and current_cue_id != "none":
            if not self.cue_history or self.cue_history[-1] != current_cue_id:
                self.cue_history.append(current_cue_id)
                if len(self.cue_history) > 4:
                    self.cue_history.pop(0)

        # 3. Draw Header Title and Status Row
        if self.font_large and self.font_bold and self.font:
            title_text = self.font_large.render("EchoRunner Trainer Dashboard", True, (255, 255, 255))
            self.screen.blit(title_text, (20, 10))

            level_str = f"Level: {level_id.replace('_', ' ').title()}"
            lvl_text = self.font_bold.render(level_str, True, (200, 200, 200))
            self.screen.blit(lvl_text, (20, 40))

            # Telemetry status display
            telemetry_x = self.width - 200
            if telemetry_recording:
                self.draw_telemetry_icon(telemetry_x, 42)
                tel_text = self.font_bold.render("Telemetry: Recording", True, (0, 255, 0))
                self.screen.blit(tel_text, (telemetry_x + 18, 40))
            else:
                tel_text = self.font.render("Telemetry: Inactive", True, (120, 120, 120))
                self.screen.blit(tel_text, (telemetry_x, 40))

        # 4. Containers Borders
        border_color = (255, 255, 255) if high_contrast else (60, 60, 60)
        border_width = 4 if high_contrast else 2

        # Maze view container
        pygame.draw.rect(self.screen, (10, 10, 10), pygame.Rect(20, 70, 400, 400))
        pygame.draw.rect(self.screen, border_color, pygame.Rect(20, 70, 400, 400), border_width)

        # Info panel container
        pygame.draw.rect(self.screen, (10, 10, 10), pygame.Rect(440, 70, 340, 400))
        pygame.draw.rect(self.screen, border_color, pygame.Rect(440, 70, 340, 400), border_width)

        # Console area container
        pygame.draw.rect(self.screen, (10, 10, 10), pygame.Rect(20, 480, 760, 110))
        pygame.draw.rect(self.screen, border_color, pygame.Rect(20, 480, 760, 110), border_width)

        # 5. Render 2D grid inside Maze view
        tile_size = 24
        grid_h = len(grid)
        grid_w = len(grid[0]) if grid_h > 0 else 0
        start_x = 20 + (400 - grid_w * tile_size) // 2
        start_y = 70 + (400 - grid_h * tile_size) // 2

        for y, row in enumerate(grid):
            for x, char in enumerate(row):
                rect = pygame.Rect(start_x + x * tile_size, start_y + y * tile_size, tile_size, tile_size)

                # Find tile background
                if char == "#":
                    if high_contrast:
                        pygame.draw.rect(self.screen, (255, 255, 255), rect)
                        pygame.draw.rect(self.screen, (0, 0, 0), rect, 2)
                    else:
                        wall_asset = self.assets.get("tile_wall")
                        if wall_asset:
                            self.screen.blit(wall_asset, rect)
                        else:
                            pygame.draw.rect(self.screen, (50, 50, 50), rect)
                else:
                    # Corridor background
                    corridor_asset = self.assets.get("tile_corridor")
                    if char == "J" or (x, y) in getattr(player, "_junctions_list", []):
                        corridor_asset = self.assets.get("tile_junction")
                    elif char == "R":
                        corridor_asset = self.assets.get("tile_safe_pocket")

                    if not high_contrast and corridor_asset:
                        self.screen.blit(corridor_asset, rect)
                    else:
                        pygame.draw.rect(self.screen, (0, 0, 0), rect)
                        if high_contrast:
                            pygame.draw.rect(self.screen, (50, 50, 50), rect, 1)

                # Draw collectibles
                is_power = (char == "o")
                is_pellet = (char == ".")

                if is_power:
                    if high_contrast:
                        pygame.draw.circle(self.screen, (255, 255, 0), rect.center, 8)
                        pygame.draw.circle(self.screen, (0, 0, 0), rect.center, 8, 2)
                    else:
                        core_asset = self.assets.get("power_resonance_core")
                        if core_asset:
                            self.screen.blit(core_asset, rect)
                        else:
                            pygame.draw.circle(self.screen, (0, 255, 0), rect.center, 6)
                elif is_pellet:
                    if high_contrast:
                        pygame.draw.circle(self.screen, (255, 255, 255), rect.center, 5)
                    else:
                        orb_asset = self.assets.get("pellet_echo_orb")
                        if orb_asset:
                            self.screen.blit(orb_asset, rect)
                        else:
                            pygame.draw.circle(self.screen, (150, 150, 150), rect.center, 3)

        # 6. Render Player
        player_rect = pygame.Rect(
            start_x + player.tile.x * tile_size,
            start_y + player.tile.y * tile_size,
            tile_size,
            tile_size,
        )
        if high_contrast:
            pygame.draw.rect(self.screen, (0, 255, 255), player_rect)
            pygame.draw.rect(self.screen, (255, 255, 255), player_rect, 3)
        else:
            player_img = self.assets.get("player_echo_runner")
            if player_img:
                angles = {"right": 0, "down": 270, "left": 180, "up": 90}
                angle = angles.get(player.direction, 0)
                rot_img = pygame.transform.rotate(player_img, angle)
                self.screen.blit(rot_img, player_rect)
            else:
                pygame.draw.rect(self.screen, (0, 150, 255), player_rect)
                pygame.draw.rect(self.screen, (255, 255, 255), player_rect, 1)

        # Direction arrow overlay (extremely high visibility)
        cx, cy = player_rect.center
        arrow_len = 8
        if player.direction == "right":
            points = [(cx + arrow_len, cy), (cx - 4, cy - 4), (cx - 4, cy + 4)]
        elif player.direction == "left":
            points = [(cx - arrow_len, cy), (cx + 4, cy - 4), (cx + 4, cy + 4)]
        elif player.direction == "up":
            points = [(cx, cy - arrow_len), (cx - 4, cy + 4), (cx + 4, cy + 4)]
        else:
            points = [(cx, cy + arrow_len), (cx - 4, cy - 4), (cx + 4, cy - 4)]
        pygame.draw.polygon(self.screen, (255, 255, 0), points)

        # 7. Render Enemies
        for enemy in enemies:
            enemy_rect = pygame.Rect(
                start_x + enemy.tile.x * tile_size,
                start_y + enemy.tile.y * tile_size,
                tile_size,
                tile_size,
            )
            # Map threat coloring
            if enemy.threat == "red":
                color = (255, 0, 0)
                threat_lbl = "RED"
            elif enemy.threat == "amber":
                color = (255, 165, 0)
                threat_lbl = "AMB"
            else:
                color = (0, 200, 100)
                threat_lbl = "SIL"

            if high_contrast:
                pygame.draw.rect(self.screen, color, enemy_rect)
                pygame.draw.rect(self.screen, (255, 255, 255), enemy_rect, 3)
            else:
                asset_key = f"enemy_{enemy.archetype}"
                enemy_img = self.assets.get(asset_key)
                if enemy_img:
                    self.screen.blit(enemy_img, enemy_rect)
                else:
                    pygame.draw.rect(self.screen, color, enemy_rect)
                # Outer indicator ring
                pygame.draw.rect(self.screen, color, enemy_rect, 2)

            # Draw letter indicator to satisfy "no information by color alone"
            if self.font:
                char_indicator = enemy.archetype[0].upper() if enemy.archetype else "E"
                text_col = (0, 0, 0) if high_contrast else (255, 255, 255)
                lbl_surf = self.font.render(f"{char_indicator}", True, text_col)
                self.screen.blit(lbl_surf, (enemy_rect.x + 8, enemy_rect.y + 4))

        # 8. Render Info Panel (Right Side)
        if self.font_bold and self.font:
            panel_x = 460
            self.screen.blit(self.font_bold.render("PLAYER STATUS", True, (255, 255, 255)), (panel_x, 85))

            # Lives display
            self.screen.blit(self.font.render("Lives:", True, (200, 200, 200)), (panel_x, 120))
            life_img = self.assets.get("life_token")
            for i in range(lives):
                lx = panel_x + 60 + i * 28
                if life_img and not high_contrast:
                    self.screen.blit(life_img, (lx, 115))
                else:
                    pygame.draw.circle(self.screen, (255, 0, 0), (lx + 8, 126), 8)
                    pygame.draw.circle(self.screen, (255, 255, 255), (lx + 8, 126), 8, 1)

            # Facing direction
            self.draw_headphones_icon(panel_x, 158, 14)
            dir_str = f"Direction: {player.direction.upper()}"
            self.screen.blit(self.font.render(dir_str, True, (200, 200, 200)), (panel_x + 22, 155))

            # Orbs remaining
            orbs_rem = sum(row.count(".") + row.count("o") for row in grid)
            self.draw_mono_icon(panel_x, 193, 14)
            self.screen.blit(self.font.render(f"Remaining Orbs: {orbs_rem}", True, (200, 200, 200)), (panel_x + 22, 190))

            # Power active timer
            self.draw_volume_icon(panel_x, 228, 14)
            power_status = f"Power core timer: {power_timer} ticks" if power_timer > 0 else "Power core: Inactive"
            self.screen.blit(self.font.render(power_status, True, (200, 200, 200)), (panel_x + 22, 225))

            # Power Core progress bar gauge
            if power_timer > 0:
                bar_width = 200
                bar_height = 12
                # Maximum duration assumes 15 seconds * 30 ticks = 450 ticks
                fill_w = int(bar_width * min(1.0, power_timer / 450.0))
                
                # Flashing red bar if remaining ticks <= 90 (last 3 seconds)
                bar_color = (0, 255, 0)
                if power_timer <= 90:
                    bar_color = (255, 0, 0) if (pygame.time.get_ticks() // 200) % 2 == 0 else (100, 0, 0)

                pygame.draw.rect(self.screen, (40, 40, 40), pygame.Rect(panel_x + 22, 250, bar_width, bar_height))
                pygame.draw.rect(self.screen, bar_color, pygame.Rect(panel_x + 22, 250, fill_w, bar_height))
                pygame.draw.rect(self.screen, (255, 255, 255), pygame.Rect(panel_x + 22, 250, bar_width, bar_height), 1)

            # Threat level assessment
            highest_threat = "silent"
            for enemy in enemies:
                if enemy.threat == "red":
                    highest_threat = "red"
                    break
                elif enemy.threat == "amber":
                    highest_threat = "amber"

            threat_colors = {"red": (255, 0, 0), "amber": (255, 165, 0), "silent": (0, 255, 0)}
            self.draw_danger_icon(panel_x, 285, 14)
            threat_str = f"Threat Level: {highest_threat.upper()}"
            self.screen.blit(self.font.render(threat_str, True, threat_colors[highest_threat]), (panel_x + 22, 282))

        # 9. Render Bottom Console (Left Area)
        if self.font_bold and self.font:
            cx = 40
            cy = 495
            
            # Active Cue Display
            self.draw_volume_icon(cx - 10, cy + 2, 12)
            cue_txt = f"AUDIO NOW: {current_cue_id}"
            cue_color = (0, 255, 255)
            # Match threat cues color
            if "danger" in current_cue_id or "near" in current_cue_id:
                cue_color = (255, 0, 0)
            self.screen.blit(self.font_bold.render(cue_txt, True, cue_color), (cx + 10, cy))

            # Recent cues history
            history_str = "History: " + (", ".join(self.cue_history) if self.cue_history else "none")
            self.screen.blit(self.font.render(history_str, True, (160, 160, 160)), (cx + 10, cy + 18))

            # Scan result
            self.draw_scan_icon(cx - 10, cy + 40, 12)
            scan_txt = f"Last scan: {last_scan_result}"
            self.screen.blit(self.font.render(scan_txt, True, (200, 200, 200)), (cx + 10, cy + 38))

            # Dynamic ethics coaching prompt
            any_threat = any(e.threat in ("red", "amber") for e in enemies)
            if any_threat:
                coach_prompt = "Ask: Which direction sounded safe?"
            elif last_scan_result != "none" and last_scan_result != "clear":
                coach_prompt = "Ask: What did you hear?"
            else:
                prompts = [
                    "Ask: Do you want to scan?",
                    "Ask: What do you hear right now?",
                    "Ask: Where are the landmarks?",
                ]
                idx = (pygame.time.get_ticks() // 4000) % len(prompts)
                coach_prompt = prompts[idx]

            self.screen.blit(self.font_bold.render(f"Coach prompt: {coach_prompt}", True, (255, 235, 150)), (cx + 10, cy + 58))

            # Instruction Subtitles Wrap
            if instruction_text:
                inst_y = cy + 78
                words = instruction_text.split(" ")
                lines = []
                curr_line = []
                for w in words:
                    test_l = " ".join(curr_line + [w])
                    if self.font.size(test_l)[0] < 700:
                        curr_line.append(w)
                    else:
                        lines.append(" ".join(curr_line))
                        curr_line = [w]
                if curr_line:
                    lines.append(" ".join(curr_line))
                
                # Draw the first line of instruction text wrapped at the very bottom
                if lines:
                    self.screen.blit(self.font.render(f"Speech: \"{lines[0]}\"", True, (255, 255, 100)), (cx + 10, inst_y))

        pygame.display.flip()

    def shutdown(self) -> None:
        """Closes any window assets."""
        pass
