"""Unit tests for the EchoRunner game workflow state machine."""
from __future__ import annotations

import os
from pathlib import Path
import pytest

from echorunner.app import AppState, EchoRunnerApp
from echorunner.input.mapper import Command


def test_state_machine_init() -> None:
    """Verifies standard state machine transitions on startup and menu choice inputs."""
    # Ensure headless video mode for test execution
    os.environ["SDL_VIDEODRIVER"] = "dummy"

    workspace_dir = Path(__file__).parent.parent.parent
    app = EchoRunnerApp(workspace_dir=workspace_dir)
    app.load_user_settings = lambda: {}
    app.save_current_settings = lambda: None
    app.initialize()

    # Initial state should be AUDIO_CHECK (headphones orientation query)
    assert app.state == AppState.AUDIO_CHECK

    # Confirm headphone test -> Transition to calibration
    app.handle_audio_check_input(Command.CONFIRM)
    assert app.state == AppState.AUDIO_CALIBRATION

    # Confirm calibration correct -> Transition to main menu
    app.handle_calibration_input(Command.CONFIRM)
    assert app.state == AppState.MAIN_MENU

    # Main menu items length check
    assert len(app.menu_items) == 8
    assert app.menu_items[0] == "Start Tutorial"

    # Move selection down
    app.handle_menu_input(Command.MOVE_DOWN)
    assert app.menu_index == 1

    app.shutdown()
