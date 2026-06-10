"""Application controller, state machine, and main game loop for EchoRunner."""
from __future__ import annotations

import logging
from enum import Enum, auto
import json
from pathlib import Path
import time
from typing import Optional
import pygame
import yaml

from echorunner.audio.openal_backend import CueEvent, OpenALBackend
from echorunner.audio.speech import SpeechManager
from echorunner.input.mapper import Command, InputMapper
from echorunner.simulation.engine import GameSimulation, SimulationFrame
from echorunner.simulation.enemy import Enemy
from echorunner.simulation.player import Player
from echorunner.simulation.world import Vec2
from echorunner.telemetry.logger import TelemetryLogger
from echorunner.trainer_view.renderer import TrainerView

logger = logging.getLogger(__name__)


class AppState(Enum):
    BOOT = auto()
    AUDIO_CHECK = auto()
    AUDIO_CALIBRATION = auto()
    MAIN_MENU = auto()
    TUTORIAL_MENU = auto()
    TUTORIAL_PLAYING = auto()
    LEVEL_SELECT = auto()
    PLAYING = auto()
    PAUSED = auto()
    LEVEL_CLEAR = auto()
    LIFE_LOST = auto()
    DEATH_REPLAY = auto()
    GAME_OVER = auto()
    RESULTS = auto()
    SETTINGS = auto()
    STUDY_MODE = auto()


class EchoRunnerApp:
    """The central coordinator of the EchoRunner application runtime."""

    def __init__(self, workspace_dir: Optional[Path] = None) -> None:
        import sys
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            self.workspace_dir = Path(sys._MEIPASS)
        else:
            self.workspace_dir = workspace_dir or Path.cwd()

        # Determine runtime paths
        is_frozen = getattr(sys, "frozen", False) or hasattr(sys, "_MEIPASS")
        is_dev = not is_frozen and (self.workspace_dir / "config").exists() and (self.workspace_dir / "assets").exists()
        
        if is_dev:
            self.data_dir = self.workspace_dir / "data"
            self.config_dir = self.workspace_dir / "data"
            self.log_dir = self.workspace_dir / "logs"
        else:
            try:
                import platformdirs
                self.data_dir = Path(platformdirs.user_data_dir("EchoRunner"))
                self.config_dir = Path(platformdirs.user_config_dir("EchoRunner"))
                self.log_dir = Path(platformdirs.user_log_dir("EchoRunner"))
            except ImportError:
                import os
                home = Path.home()
                if sys.platform.startswith("win"):
                    appdata = Path(os.environ.get("APPDATA", str(home / "AppData" / "Roaming")))
                    self.data_dir = appdata / "EchoRunner"
                    self.config_dir = appdata / "EchoRunner"
                    self.log_dir = appdata / "EchoRunner" / "logs"
                else:
                    self.data_dir = home / ".local" / "share" / "EchoRunner"
                    self.config_dir = home / ".config" / "EchoRunner"
                    self.log_dir = home / ".cache" / "EchoRunner" / "logs"

        self.sessions_dir = self.data_dir / "sessions"
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.sessions_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        # Configure file logging
        log_file = self.log_dir / "app.log"
        try:
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
            logging.getLogger().addHandler(file_handler)
        except Exception:
            pass
        self.config: dict = {}
        self.running = False
        self.clock = pygame.time.Clock()

        # State machine
        self.state = AppState.BOOT
        self.state_timer = 0

        # Subsystems
        self.audio_backend: OpenALBackend | None = None
        self.speech_manager: SpeechManager | None = None
        self.input_mapper = InputMapper()
        self.trainer_view: TrainerView | None = None
        self.telemetry: TelemetryLogger | None = None

        # Menu navigation properties
        self.menu_items: list[str] = []
        self.menu_index = 0

        # Calibration state properties
        self.calibration_step = 0

        # Simulation engine reference
        self.simulation: GameSimulation | None = None
        self.level_id = "level_01_training_loop"
        self.lives = 3
        self.score = 0

        # Accessibility and UI variables
        self._mono_mode = False
        self.cue_density = "beginner"
        self.low_stress_mode = False
        self.speech_volume = 70  # percentage
        self.speech_speed = 100  # percentage
        self.first_launch_completed = False
        self.death_reason = "hunter"
        self.high_contrast_mode = False
        self.last_scan_result = "none"
        self.last_enemy_threats = {}
        self.replay_logger = None
        self.study_mode = False
        self.participant_id = ""

    @property
    def mono_mode(self) -> bool:
        return self._mono_mode

    @mono_mode.setter
    def mono_mode(self, value: bool) -> None:
        self._mono_mode = value
        if self.audio_backend:
            self.audio_backend.mono_mode = value

        # UI mirror compatibility references
        self.player = Player(Vec2(1, 1))
        self.enemies: list[Enemy] = []
        self.grid: list[str] = []

        self.tutorial_module = 1
        self.wall_hits = 0
        self.command_queue: list[Command] = []

    def load_config(self) -> None:
        """Loads yaml configuration parameters."""
        config_path = self.workspace_dir / "config" / "defaults.yaml"
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    self.config = yaml.safe_load(f) or {}
                logger.info("Configuration loaded.")
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
                self.config = {}
        else:
            self.config = {}

    def load_user_settings(self) -> dict:
        settings_path = self.config_dir / "settings.json"
        if settings_path.exists():
            try:
                import json
                with open(settings_path, "r", encoding="utf-8") as f:
                    return json.load(f) or {}
            except Exception as e:
                logger.error(f"Error loading user settings: {e}")
        return {}

    def save_current_settings(self) -> None:
        settings = self.load_user_settings()
        settings.update({
            "first_launch_completed": self.first_launch_completed,
            "mono_mode": self.mono_mode,
            "cue_density": self.cue_density,
            "low_stress_mode": self.low_stress_mode,
            "speech_volume": self.speech_volume,
            "speech_speed": self.speech_speed,
            "six_key_mode": self.input_mapper.six_key_mode,
            "high_contrast_mode": self.high_contrast_mode,
        })
        settings_path = self.config_dir / "settings.json"
        try:
            import json
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving user settings: {e}")

    def complete_first_launch(self) -> None:
        self.first_launch_completed = True
        self.save_current_settings()

    def initialize(self, study: bool = False, participant_id: str | None = None, level_id: str | None = None) -> None:
        """Starts all subsystems."""
        self.load_config()
        self.study_mode = study
        self.participant_id = participant_id or f"P_{int(pygame.time.get_ticks())}"
        if level_id:
            self.level_id = level_id

        # Initialize telemetry
        session_id = f"{self.participant_id}_{int(pygame.time.get_ticks())}"
        self.telemetry = TelemetryLogger(
            session_id,
            self.sessions_dir / session_id,
        )

        # Initialize audio
        self.audio_backend = OpenALBackend(self.workspace_dir)
        self.audio_backend.start()
        self.speech_manager = SpeechManager(
            self.audio_backend,
            self.config.get("audio", {}).get("speech_language", "en"),
            app=self,
        )

        # Load user settings or fallback to defaults
        user_settings = self.load_user_settings()
        self.first_launch_completed = user_settings.get("first_launch_completed", False)
        
        audio_cfg = self.config.get("audio", {})
        self.mono_mode = user_settings.get("mono_mode", audio_cfg.get("mono_mode", False))
        self.cue_density = user_settings.get("cue_density", audio_cfg.get("cue_density", "beginner"))
        
        gameplay_cfg = self.config.get("gameplay", {})
        self.low_stress_mode = user_settings.get("low_stress_mode", gameplay_cfg.get("low_stress_mode", False))
        
        self.speech_volume = user_settings.get("speech_volume", int(audio_cfg.get("speech_volume", 0.9) * 100))
        self.speech_speed = user_settings.get("speech_speed", 100)
        self.input_mapper.six_key_mode = user_settings.get("six_key_mode", False)
        self.high_contrast_mode = user_settings.get("high_contrast_mode", False)

        # Initialize Trainer View
        trainer_enabled = self.config.get("trainer_view", {}).get("enabled", True)
        if trainer_enabled:
            self.trainer_view = TrainerView(workspace_dir=self.workspace_dir)
            self.trainer_view.start()
        else:
            pygame.init()
            pygame.display.set_mode((100, 100))

        # Start in correct state
        if self.study_mode:
            pass
        elif self.first_launch_completed:
            self.transition_to(AppState.MAIN_MENU)
        else:
            self.transition_to(AppState.AUDIO_CHECK)
    def play_cue(self, cue: CueEvent) -> None:
        """Plays an audio cue via audio backend and logs to telemetry/replay."""
        if self.audio_backend:
            self.audio_backend.play_cue(cue)
        if self.telemetry:
            self.telemetry.log_event(
                "cue",
                cue_id=cue.cue_id,
                priority=cue.priority
            )
        if getattr(self, "replay_logger", None):
            offset = time.time() - self.telemetry.start_time if self.telemetry else 0.0
            self.replay_logger.record_cue(offset, cue.cue_id, cue.priority)

    def transition_to(self, new_state: AppState) -> None:
        """Transitions the application state machine, logging and starting entry actions."""
        old_state = self.state
        self.state = new_state
        self.state_timer = 0
        self.menu_index = 0
        self.command_queue.clear()

        if self.telemetry:
            self.telemetry.log_event(
                "state_transition",
                from_state=old_state.name,
                to_state=new_state.name,
            )

        logger.info(f"Transitioned from {old_state.name} to {new_state.name}")

        # Entry behaviors
        if new_state == AppState.AUDIO_CHECK:
            if self.speech_manager:
                self.speech_manager.speak("first_launch")

        elif new_state == AppState.AUDIO_CALIBRATION:
            self.calibration_step = 0
            if self.speech_manager:
                self.speech_manager.speak("audio_calibration_intro")

        elif new_state == AppState.MAIN_MENU:
            self.menu_items = [
                "Start Tutorial",
                "Continue Game",
                "Level Select",
                "Audio Calibration",
                "Settings",
                "Trainer Mode",
                "Help",
                "Quit",
            ]
            if self.speech_manager:
                self.speech_manager.speak("main_menu_intro")

        elif new_state == AppState.TUTORIAL_MENU:
            self.menu_items = [
                "Hear walls",
                "Turn at junctions",
                "Collect orbs",
                "Use short scan",
                "Escape enemy",
                "Use resonance core",
                "Play real level",
            ]
            if self.speech_manager:
                self.speech_manager.speak("tutorial_intro")

        elif new_state == AppState.TUTORIAL_PLAYING:
            self.wall_hits = 0
            self.start_tutorial_module(self.tutorial_module)

        elif new_state == AppState.PLAYING:
            self.start_level()

        elif new_state == AppState.PAUSED:
            self.menu_items = [
                "Resume",
                "Repeat goal",
                "Repeat controls",
                "Audio calibration",
                "Cue detail",
                "Restart level",
                "Quit to main menu",
            ]
            if self.speech_manager:
                self.speech_manager.speak("pause_menu")

        elif new_state == AppState.LEVEL_CLEAR:
            if self.audio_backend:
                self.audio_backend.play_cue(
                    CueEvent("level_clear", "level_clear", 50, False)
                )
            if self.speech_manager:
                self.speech_manager.speak("level_clear")

        elif new_state == AppState.LIFE_LOST:
            if self.audio_backend:
                self.audio_backend.play_cue(
                    CueEvent("life_lost", "life_lost", 100, False)
                )
            if self.speech_manager:
                speech_id = f"death_{self.death_reason}"
                if speech_id not in ("death_power_ended", "death_hunter_left", "death_ambusher_tip"):
                    speech_id = "death_hunter_left"
                self.speech_manager.speak(speech_id)

        elif new_state == AppState.DEATH_REPLAY:
            if self.speech_manager:
                speech_id = f"death_{self.death_reason}"
                if speech_id not in ("death_power_ended", "death_hunter_left", "death_ambusher_tip"):
                    speech_id = "death_hunter_left"
                self.speech_manager.speak(speech_id)

        elif new_state == AppState.GAME_OVER:
            if self.speech_manager:
                self.speech_manager.speak("quit_goodbye")

        elif new_state == AppState.SETTINGS:
            self.menu_items = [
                "Cue Density",
                "Mono Mode",
                "Low-Stress Mode",
                "Six-Key Layout",
                "Speech Volume",
                "Speech Speed",
                "High-Contrast Mode",
                "Back to Main Menu",
            ]
            if self.speech_manager:
                self.speech_manager.speak("settings_cue_density")

        elif new_state == AppState.STUDY_MODE:
            if self.speech_manager:
                self.speech_manager.speak("study_mode_intro")

    def run(self) -> None:
        """Main application execution loop."""
        if getattr(self, "study_mode", False):
            # Run consent flow in terminal
            print("\n")
            print("=" * 60)
            print("           ECHORUNNER HCI RESEARCH CONSENT PROTOCOL")
            print("=" * 60)
            print("Disclaimer: The following consent template is for research demonstration purposes and does not constitute formal legal approval.")
            print(f"Participant: {self.participant_id}")
            print(f"Level: {self.level_id}")
            print("Data recorded: keyboard inputs, simulation events, threat categories.")
            print("No audio recordings, names, or network telemetry will be collected.")
            print("-" * 60)
            try:
                ans = input("Do you consent to participate? (y/n): ").strip().lower()
            except (IOError, KeyboardInterrupt):
                ans = "n"
            if ans not in ("y", "yes"):
                print("Consent declined. Exiting.")
                return
            print("Consent obtained. Starting study session...")
            self.transition_to(AppState.PLAYING)

        self.running = True
        logger.info("Entering main application loop.")

        while self.running:
            self.clock.tick(30)
            self.handle_input()
            self.update()
            self.render()

        self.shutdown()

        if getattr(self, "study_mode", False):
            # Collect post-task prompts
            from echorunner.research.study import collect_post_task_prompts, export_session
            answers = collect_post_task_prompts()
            # Save answers to responses.json in session dir
            if self.telemetry:
                resp_file = self.telemetry.output_dir / "responses.json"
                try:
                    resp_file.write_text(json.dumps(answers, indent=2), encoding="utf-8")
                except Exception:
                    pass
                export_session(self.telemetry.session_id, anonymized=True)

    def handle_input(self) -> None:
        """Polls Pygame event queue and routes commands."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type == pygame.KEYDOWN:
                # Custom direct calibration key binding
                if (
                    self.state == AppState.AUDIO_CALIBRATION
                    and event.key == pygame.K_m
                ):
                    self.mono_mode = not self.mono_mode
                    if self.speech_manager:
                        self.speech_manager.speak("mono_mode")
                    self.save_current_settings()
                    continue

                # Slider adjustments using Left/Right arrow keys in Settings
                if self.state == AppState.SETTINGS:
                    if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                        self.handle_slider_input(event.key)
                        continue

            command = self.input_mapper.map_event(event)
            if not command:
                continue

            if self.telemetry:
                self.telemetry.log_event(
                    "command_input", command=command.name, state=self.state.name
                )

            # Global command overrides
            if command == Command.TOGGLE_TRAINER:
                if self.trainer_view:
                    self.trainer_view = None
                    pygame.display.set_mode((100, 100))
                else:
                    self.trainer_view = TrainerView(workspace_dir=self.workspace_dir)
                    self.trainer_view.start()
                if self.audio_backend:
                    self.audio_backend.play_cue(
                        CueEvent(
                            "settings_changed", "settings_changed", 30, False
                        )
                    )
                continue

            if command == Command.AUDIO_TEST:
                self.transition_to(AppState.AUDIO_CALIBRATION)
                continue

            if command == Command.TOGGLE_CUE_DENSITY:
                self.cue_density = (
                    "standard"
                    if self.cue_density == "beginner"
                    else ("expert" if self.cue_density == "standard" else "beginner")
                )
                if self.speech_manager:
                    self.speech_manager.speak("settings_cue_density")
                self.save_current_settings()
                continue

            if command == Command.MARK_CONFUSION:
                if self.telemetry:
                    self.telemetry.log_event(
                        "trainer_marker",
                        marker="confusion",
                        note="trainer marked confusion via F8 key",
                    )
                if self.audio_backend:
                    self.audio_backend.play_cue(
                        CueEvent("settings_changed", "settings_changed", 30, False)
                    )
                continue


            # Add movement inputs to command queue for simulation
            if self.state in (AppState.PLAYING, AppState.TUTORIAL_PLAYING):
                if command in (
                    Command.MOVE_UP,
                    Command.MOVE_DOWN,
                    Command.MOVE_LEFT,
                    Command.MOVE_RIGHT,
                ):
                    self.command_queue.append(command)

            # Route by State
            if self.state in (
                AppState.MAIN_MENU,
                AppState.TUTORIAL_MENU,
                AppState.PAUSED,
                AppState.SETTINGS,
            ):
                self.handle_menu_input(command)
            elif self.state == AppState.AUDIO_CHECK:
                self.handle_audio_check_input(command)
            elif self.state == AppState.AUDIO_CALIBRATION:
                self.handle_calibration_input(command)
            elif self.state == AppState.PLAYING:
                self.handle_playing_input(command)
            elif self.state == AppState.TUTORIAL_PLAYING:
                self.handle_tutorial_playing_input(command)
            elif self.state in (
                AppState.LEVEL_CLEAR,
                AppState.LIFE_LOST,
                AppState.DEATH_REPLAY,
                AppState.GAME_OVER,
            ):
                self.handle_results_input(command)

    def handle_audio_check_input(self, command: Command) -> None:
        """Handles keys in initial Headphone direction choice state."""
        if command == Command.CONFIRM:
            self.transition_to(AppState.AUDIO_CALIBRATION)
        elif command == Command.BACK:
            self.transition_to(AppState.MAIN_MENU)
        elif command == Command.REPEAT_LAST:
            if self.speech_manager:
                self.speech_manager.speak("first_launch")

    def handle_calibration_input(self, command: Command) -> None:
        """Handles confirmation inside AudioCalibration."""
        if command == Command.CONFIRM:
            if self.audio_backend:
                self.audio_backend.play_cue(
                    CueEvent("menu_confirm", "menu_confirm", 30, False)
                )
            self.complete_first_launch()
            self.transition_to(AppState.MAIN_MENU)
        elif command in (Command.SCAN_SHORT, Command.REPEAT_LAST):
            # Reset the calibration state timer to replay sequence
            self.state_timer = 0
            if self.speech_manager:
                self.speech_manager.speak("audio_calibration_intro")

    def handle_menu_input(self, command: Command) -> None:
        """Handles navigation inputs for menus."""
        if command == Command.MOVE_DOWN:
            self.menu_index = (self.menu_index + 1) % len(self.menu_items)
            if self.audio_backend:
                self.audio_backend.play_cue(
                    CueEvent("menu_move", "menu_move", 30, False)
                )
            self.speak_current_menu_item()
        elif command == Command.MOVE_UP:
            self.menu_index = (self.menu_index - 1) % len(self.menu_items)
            if self.audio_backend:
                self.audio_backend.play_cue(
                    CueEvent("menu_move", "menu_move", 30, False)
                )
            self.speak_current_menu_item()
        elif command == Command.CONFIRM:
            if self.audio_backend:
                self.audio_backend.play_cue(
                    CueEvent("menu_confirm", "menu_confirm", 30, False)
                )
            self.execute_menu_action()
        elif command == Command.REPEAT_LAST:
            if self.speech_manager:
                self.speech_manager.repeat_last()
        elif command == Command.HELP:
            if self.speech_manager:
                self.speech_manager.speak("first_launch")
        elif command == Command.BACK:
            if self.audio_backend:
                self.audio_backend.play_cue(
                    CueEvent("menu_back", "menu_back", 30, False)
                )
            if self.state in (AppState.SETTINGS, AppState.TUTORIAL_MENU):
                self.transition_to(AppState.MAIN_MENU)
            elif self.state == AppState.PAUSED:
                self.transition_to(AppState.PLAYING)
            elif self.state == AppState.MAIN_MENU:
                self.running = False

    def speak_current_menu_item(self) -> None:
        """Voices the currently highlighted menu list item using pre-recorded files."""
        if not self.speech_manager:
            return
        item = self.menu_items[self.menu_index]

        if item == "Start Tutorial":
            self.speech_manager.speak("tutorial_intro")
        elif item == "Audio Calibration":
            self.speech_manager.speak("audio_calibration_intro")
        elif item == "Trainer Mode":
            self.speech_manager.speak("trainer_mode")
        elif item == "Quit":
            self.speech_manager.speak("quit_goodbye")
        elif item in ("Cue Density", "Cue Detail"):
            self.speech_manager.speak("settings_cue_density")
        elif item == "Mono Mode":
            self.speech_manager.speak("mono_mode")
        elif item == "Low-Stress Mode":
            self.speech_manager.speak("low_stress_mode")
        elif item == "Speech Volume":
            self.speech_manager.speak("settings_changed")
            logger.info(f"Speech Volume: {self.speech_volume}%")
        elif item == "Speech Speed":
            self.speech_manager.speak("settings_changed")
            logger.info(f"Speech Speed: {self.speech_speed}%")
        elif item == "Help":
            self.speech_manager.speak("first_launch")
        elif item == "High-Contrast Mode":
            self.speech_manager.speak("high_contrast")
        else:
            logger.info(f"Voicing menu: {item}")

    def execute_menu_action(self) -> None:
        """Dispatches action callbacks based on selected menu item."""
        item = self.menu_items[self.menu_index]

        if self.state == AppState.MAIN_MENU:
            if item == "Start Tutorial":
                self.complete_first_launch()
                self.transition_to(AppState.TUTORIAL_MENU)
            elif item == "Continue Game":
                self.transition_to(AppState.PLAYING)
            elif item == "Level Select":
                self.transition_to(AppState.PLAYING)  # directly starts level
            elif item == "Audio Calibration":
                self.transition_to(AppState.AUDIO_CALIBRATION)
            elif item == "Settings":
                self.transition_to(AppState.SETTINGS)
            elif item == "Trainer Mode":
                self.transition_to(AppState.MAIN_MENU)
            elif item == "Help":
                self.complete_first_launch()
                if self.speech_manager:
                    self.speech_manager.speak("first_launch")
            elif item == "Quit":
                self.running = False

        elif self.state == AppState.TUTORIAL_MENU:
            self.tutorial_module = self.menu_index + 1
            self.transition_to(AppState.TUTORIAL_PLAYING)

        elif self.state == AppState.PAUSED:
            if item == "Resume":
                self.transition_to(AppState.PLAYING)
            elif item == "Repeat goal":
                if self.speech_manager:
                    self.speech_manager.speak("game_goal")
            elif item == "Repeat controls":
                if self.speech_manager:
                    self.speech_manager.speak("controls_full")
            elif item == "Audio Calibration":
                self.transition_to(AppState.AUDIO_CALIBRATION)
            elif item in ("Cue Detail", "Cue Density"):
                self.cue_density = (
                    "standard"
                    if self.cue_density == "beginner"
                    else ("expert" if self.cue_density == "standard" else "beginner")
                )
                if self.speech_manager:
                    self.speech_manager.speak("settings_cue_density")
            elif item == "Restart level":
                self.transition_to(AppState.PLAYING)
            elif item == "Quit to main menu":
                self.transition_to(AppState.MAIN_MENU)

        elif self.state == AppState.SETTINGS:
            if item == "Back to Main Menu":
                self.transition_to(AppState.MAIN_MENU)
            elif item == "Mono Mode":
                self.mono_mode = not self.mono_mode
                if self.speech_manager:
                    self.speech_manager.speak("mono_mode")
                self.save_current_settings()
            elif item == "Low-Stress Mode":
                self.low_stress_mode = not self.low_stress_mode
                if self.speech_manager:
                    self.speech_manager.speak("low_stress_mode")
                self.save_current_settings()
            elif item == "Six-Key Layout":
                self.input_mapper.six_key_mode = not self.input_mapper.six_key_mode
                if self.audio_backend:
                    self.audio_backend.play_cue(
                        CueEvent("settings_changed", "settings_changed", 30, False)
                    )
                self.save_current_settings()
                logger.info(f"Six-Key Layout: {self.input_mapper.six_key_mode}")
            elif item == "Cue Density":
                self.cue_density = (
                    "standard"
                    if self.cue_density == "beginner"
                    else ("expert" if self.cue_density == "standard" else "beginner")
                )
                if self.speech_manager:
                    self.speech_manager.speak("settings_cue_density")
                self.save_current_settings()
            elif item == "High-Contrast Mode":
                self.high_contrast_mode = not self.high_contrast_mode
                if self.speech_manager:
                    self.speech_manager.speak("high_contrast")
                self.save_current_settings()

    def handle_slider_input(self, key: int) -> None:
        """Handles slider adjustments for Volume and Speed in Settings."""
        item = self.menu_items[self.menu_index]
        delta = 10 if key == pygame.K_RIGHT else -10

        if item == "Speech Volume":
            self.speech_volume = max(10, min(100, self.speech_volume + delta))
            if self.audio_backend:
                self.audio_backend.play_cue(
                    CueEvent("settings_changed", "settings_changed", 30, False)
                )
            self.save_current_settings()
            logger.info(f"Speech volume {self.speech_volume} percent.")

        elif item == "Speech Speed":
            self.speech_speed = max(50, min(150, self.speech_speed + delta))
            if self.audio_backend:
                self.audio_backend.play_cue(
                    CueEvent("settings_changed", "settings_changed", 30, False)
                )
            self.save_current_settings()
            logger.info(f"Speech speed {self.speech_speed} percent.")

    def handle_playing_input(self, command: Command) -> None:
        """Handles in-game commands."""
        if command == Command.PAUSE:
            self.transition_to(AppState.PAUSED)
        elif command == Command.SCAN_SHORT:
            if self.audio_backend:
                self.audio_backend.play_cue(
                    CueEvent("scan_start", "scan_start", 50, True)
                )
            if self.speech_manager:
                self.speech_manager.speak("scan_example")
            self.last_scan_result = self.compute_scan_result()
        elif command == Command.REPEAT_LAST:
            if self.speech_manager:
                self.speech_manager.repeat_last()
        elif command == Command.HELP:
            if self.speech_manager:
                self.speech_manager.speak("gameplay_help")

    def handle_tutorial_playing_input(self, command: Command) -> None:
        """Delegates input for tutorial mode."""
        if command == Command.BACK:
            self.transition_to(AppState.TUTORIAL_MENU)
        elif command == Command.SCAN_SHORT:
            if self.audio_backend:
                self.audio_backend.play_cue(
                    CueEvent("scan_start", "scan_start", 50, True)
                )
            if self.speech_manager:
                self.speech_manager.speak("scan_example")
            self.last_scan_result = self.compute_scan_result()
            if self.tutorial_module == 4:
                self.complete_tutorial_module()
        elif command == Command.REPEAT_LAST:
            if self.speech_manager:
                self.speech_manager.repeat_last()
        elif command == Command.HELP:
            self.replay_tutorial_instructions()

    def replay_tutorial_instructions(self) -> None:
        """Repeats instructions based on the active tutorial module."""
        if not self.speech_manager:
            return
        m = self.tutorial_module
        if m == 1:
            self.speech_manager.speak("tutorial_walls")
        elif m == 2:
            self.speech_manager.speak("tutorial_junctions")
        elif m == 3:
            self.speech_manager.speak("tutorial_orbs")
        elif m == 4:
            self.speech_manager.speak("tutorial_scan")
        elif m == 5:
            self.speech_manager.speak("tutorial_enemy")
        elif m == 6:
            self.speech_manager.speak("tutorial_power")
        elif m == 7:
            self.speech_manager.speak("tutorial_real_level")

    def handle_results_input(self, command: Command) -> None:
        """Press Enter to proceed from results / death screen."""
        if command == Command.CONFIRM:
            if self.state == AppState.LIFE_LOST:
                self.transition_to(AppState.PLAYING)
            else:
                self.transition_to(AppState.MAIN_MENU)
        elif command == Command.SCAN_SHORT:
            if self.state == AppState.LIFE_LOST:
                self.transition_to(AppState.DEATH_REPLAY)

    def start_tutorial_module(self, module: int) -> None:
        """Loads simulation layouts for tutorial module goals."""
        import random
        seed = random.randint(0, 1000000)
        self.simulation = GameSimulation(self.workspace_dir, f"tutorial_mod_{module}", seed=seed)
        # Apply speeds
        self.simulation.player_speed = 2.5
        self.simulation.low_stress_mode = self.low_stress_mode
        self.simulation.cue_density = self.cue_density
        self.replay_tutorial_instructions()
        self.sync_simulation_to_app()

        from echorunner.telemetry.logger import ReplayLogger
        self.replay_logger = ReplayLogger(
            session_id=self.telemetry.session_id if self.telemetry else "none",
            level_id=f"tutorial_mod_{module}",
            seed=seed,
            output_dir=self.telemetry.output_dir if self.telemetry else self.workspace_dir / "data" / "sessions" / "none"
        )

    def start_level(self) -> None:
        """Starts a standard level play session."""
        import random
        seed = random.randint(0, 1000000)
        self.simulation = GameSimulation(self.workspace_dir, self.level_id, seed=seed)
        self.simulation.player_speed = 3.0
        self.simulation.low_stress_mode = self.low_stress_mode
        self.simulation.cue_density = self.cue_density
        self.lives = 3
        if self.speech_manager:
            self.speech_manager.speak("gameplay_help")
        self.sync_simulation_to_app()

        from echorunner.telemetry.logger import ReplayLogger
        self.replay_logger = ReplayLogger(
            session_id=self.telemetry.session_id if self.telemetry else "none",
            level_id=self.level_id,
            seed=seed,
            output_dir=self.telemetry.output_dir if self.telemetry else self.workspace_dir / "data" / "sessions" / "none"
        )

    def complete_tutorial_module(self) -> None:
        """Completes active module and transitions back to menu."""
        if self.speech_manager:
            self.speech_manager.speak("level_clear")
        self.transition_to(AppState.TUTORIAL_MENU)

    def sync_simulation_to_app(self) -> None:
        """Synchronizes simulation grid & coords back to app variables for the UI mirror."""
        if not self.simulation:
            return
        self.grid = self.simulation.grid
        self.player.tile = self.simulation.player_pos
        self.player.direction = self.simulation.player_dir

        self.enemies.clear()
        for es in self.simulation.enemies:
            # Map EnemyState objects to app Enemy structures
            enemy = Enemy(es.enemy_id, es.archetype, es.tile)
            enemy.direction = es.direction
            enemy.state = es.state
            enemy.threat = es.threat
            self.enemies.append(enemy)

    def update(self) -> None:
        """Triggers updates on the state machine timer and active gameplay variables."""
        if self.state == AppState.AUDIO_CALIBRATION:
            self.update_calibration()
            return

        if self.state not in (AppState.PLAYING, AppState.TUTORIAL_PLAYING):
            return

        if not self.simulation:
            return

        # Advance deterministic simulation step (dt = 1/30 second)
        frame = self.simulation.step(1.0 / 30.0, self.command_queue)
        self.command_queue.clear()

        # Synchronize back
        self.sync_simulation_to_app()

        # Dispatch audio cues from simulation events
        self.dispatch_simulation_events(frame.events)

        # Update OpenAL listener orientation
        if self.audio_backend:
            self.audio_backend.update_listener(
                (float(frame.player_pos.x), 0.0, float(frame.player_pos.y)),
                frame.player_dir,
            )

            # Update enemy audio spatial alerts
            planned = self.cue_planner.plan_cues(self.player, self.enemies)
            for cue in planned:
                self.play_cue(cue)

        # Check tutorial module complete conditions
        if self.state == AppState.TUTORIAL_PLAYING:
            self.update_tutorial_objectives(frame.events)

    def dispatch_simulation_events(self, events: list[dict]) -> None:
        """Parses events emitted by simulation to schedule audio cues."""
        for ev in events:
            t = ev["type"]
            if self.telemetry:
                if t == "move":
                    self.telemetry.log_event("move", **{"from": ev["from"], "to": ev["to"], "direction": ev["direction"]})
                elif t == "player_killed":
                    self.telemetry.log_event("death", cause=ev.get("death_type", "hunter"), tile=[self.player.tile.x, self.player.tile.y])
                    if getattr(self, "replay_logger", None):
                        offset = time.time() - self.telemetry.start_time
                        self.replay_logger.record_death(offset, ev.get("death_type", "hunter"), [self.player.tile.x, self.player.tile.y])
            
            if getattr(self, "replay_logger", None):
                offset = time.time() - self.telemetry.start_time if self.telemetry else 0.0
                self.replay_logger.record_event(offset, t, ev)

            if t == "orb_collected":
                self.play_cue(
                    CueEvent("pellet_tick", "pellet_tick", 20, True)
                )
            elif t == "power_activate":
                self.play_cue(
                    CueEvent("power_activate", "power_activate", 95, True)
                )
            elif t == "power_expire":
                self.play_cue(
                    CueEvent("power_expire", "power_expire", 90, True)
                )
            elif t == "power_countdown":
                self.play_cue(
                    CueEvent("power_countdown", "power_countdown", 95, True)
                )
            elif t == "footstep":
                if self.cue_density == "beginner":
                    self.play_cue(
                        CueEvent(
                            "move_step_soft", "move_step_soft", 10, True
                        )
                    )
            elif t == "wall_knock":
                self.play_cue(
                    CueEvent("wall_knock", "wall_knock", 30, True)
                )
                if self.state == AppState.TUTORIAL_PLAYING and self.tutorial_module == 1:
                    self.wall_hits += 1
                    if self.wall_hits >= 3:
                        if self.speech_manager:
                            self.speech_manager.speak("tutorial_walls")
                        self.wall_hits = 0
            elif t == "junction_reached":
                for d in ev["open_dirs"]:
                    chime_map = {
                        "up": "junction_open_up",
                        "down": "junction_open_down",
                        "left": "junction_open_left",
                        "right": "junction_open_right",
                    }
                    chime = chime_map[d]
                    self.play_cue(
                        CueEvent(chime, chime, 30, False)
                    )
            elif t == "enemy_eaten":
                self.play_cue(
                    CueEvent("fruit_collect", "fruit_collect", 50, True)
                )
            elif t == "player_killed":
                self.lives -= 1
                self.death_reason = ev.get("death_type", "hunter")
                if self.state == AppState.TUTORIAL_PLAYING:
                    # Reset to start
                    if self.simulation:
                        self.simulation.player_pos = Vec2(1, 1)
                    if self.speech_manager:
                        if self.tutorial_module == 5:
                            self.speech_manager.speak("tutorial_enemy")
                        elif self.tutorial_module == 6:
                            self.speech_manager.speak("tutorial_power")
                        else:
                            self.speech_manager.speak("tutorial_walls")
                else:
                    if self.lives > 0:
                        self.transition_to(AppState.LIFE_LOST)
                    else:
                        self.transition_to(AppState.GAME_OVER)
                        if getattr(self, "study_mode", False):
                            self.running = False
            elif t == "level_clear":
                if self.state == AppState.TUTORIAL_PLAYING:
                    self.complete_tutorial_module()
                else:
                    self.transition_to(AppState.LEVEL_CLEAR)
                    if getattr(self, "study_mode", False):
                        self.running = False

    def update_tutorial_objectives(self, events: list[dict]) -> None:
        """Validates simple custom tutorial objectives on frame updates."""
        if not self.simulation:
            return
        m = self.tutorial_module

        if m == 1:
            # Move right to complete
            if self.simulation.player_pos.x >= 5:
                self.complete_tutorial_module()
        elif m == 2:
            # Turn up to complete
            if self.simulation.player_pos.y == 1:
                self.complete_tutorial_module()
        elif m == 5:
            # Escape enemy to end
            if self.simulation.player_pos.x >= 7:
                self.complete_tutorial_module()
        elif m == 6:
            # Complete when enemy is eaten
            if any(ev.get("type") == "enemy_eaten" for ev in events):
                self.complete_tutorial_module()

    def update_calibration(self) -> None:
        """Calibration audio sequence timer."""
        self.state_timer += 1

        # Play left at 90 frames (3 seconds)
        if self.state_timer == 90:
            if self.speech_manager:
                self.speech_manager.last_spoken_text = "Left."
            if self.audio_backend:
                self.audio_backend.play_cue(
                    CueEvent(
                        "calibration_left",
                        "landmark_safe_loop",
                        50,
                        True,
                        position=(-5.0, 0.0, 0.0),
                    )
                )

        # Play center at 180 frames (6 seconds)
        elif self.state_timer == 180:
            if self.speech_manager:
                self.speech_manager.last_spoken_text = "Center."
            if self.audio_backend:
                self.audio_backend.play_cue(
                    CueEvent(
                        "calibration_center",
                        "landmark_safe_loop",
                        50,
                        True,
                        position=(0.0, 0.0, 0.0),
                        source_relative=True,
                    )
                )

        # Play right at 270 frames (9 seconds)
        elif self.state_timer == 270:
            if self.speech_manager:
                self.speech_manager.last_spoken_text = "Right."
            if self.audio_backend:
                self.audio_backend.play_cue(
                    CueEvent(
                        "calibration_right",
                        "landmark_safe_loop",
                        50,
                        True,
                        position=(5.0, 0.0, 0.0),
                    )
                )

        # Ask question at 360 frames (12 seconds)
        elif self.state_timer == 360:
            if self.speech_manager:
                self.speech_manager.speak("headphone_confirm")

    def compute_scan_result(self) -> str:
        """Scans cardinal directions for danger or pellets."""
        if not self.simulation:
            return "clear"
        player_pos = self.simulation.player_pos
        enemies = self.simulation.enemies
        orbs = self.simulation.orbs
        grid = self.simulation.grid
        
        results = []
        directions = {
            "up": Vec2(0, -1),
            "down": Vec2(0, 1),
            "left": Vec2(-1, 0),
            "right": Vec2(1, 0)
        }
        for dir_name, offset in directions.items():
            curr = player_pos + offset
            has_enemy = False
            has_pellet = False
            while True:
                y, x = curr.y, curr.x
                if y < 0 or y >= len(grid) or x < 0 or x >= len(grid[0]) or grid[y][x] == "#":
                    break
                for enemy in enemies:
                    if enemy.tile == curr:
                        has_enemy = True
                if curr in orbs:
                    has_pellet = True
                curr = curr + offset
            if has_enemy:
                results.append(f"{dir_name} danger")
            elif has_pellet:
                results.append(f"{dir_name} pellets")
        
        if results:
            return ", ".join(results)
        return "clear"

    def render(self) -> None:
        """Updates trainer companion dashboard display."""
        if self.trainer_view:
            active_cue_id = "none"
            if self.audio_backend:
                active_cue_id = self.audio_backend.get_active_cue_id()

            instruction = ""
            if self.speech_manager:
                instruction = self.speech_manager.last_spoken_text

            power_timer = self.simulation.power_timer if self.simulation else 0
            level_id = self.simulation.level_id if self.simulation else "none"

            self.trainer_view.render(
                grid=self.grid,
                player=self.player,
                enemies=self.enemies,
                current_cue_id=active_cue_id,
                instruction_text=instruction,
                high_contrast=self.high_contrast_mode,
                power_timer=power_timer,
                lives=self.lives,
                last_scan_result=self.last_scan_result,
                telemetry_recording=(self.telemetry is not None),
                level_id=level_id,
            )

    def shutdown(self) -> None:
        """Cleans up audio contexts and exits pygame modules."""
        logger.info("Shutting down application...")
        if self.replay_logger:
            self.replay_logger.save()
        if self.audio_backend:
            if self.speech_manager:
                self.speech_manager.speak("quit_goodbye")
                pygame.time.wait(1000)
            self.audio_backend.stop()

        pygame.quit()
        logger.info("EchoRunner closed.")
