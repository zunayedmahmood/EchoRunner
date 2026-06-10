"""Unit tests for the EchoRunner input mapping and accessibility controls."""
from __future__ import annotations

import os
import pygame
import pytest

from echorunner.app import AppState, EchoRunnerApp
from echorunner.input.mapper import Command, InputMapper


def test_six_key_layout_mapping() -> None:
    """Verifies that enabling the six-key layout updates raw key mappings to home row controls."""
    pygame.init()
    mapper = InputMapper()
    assert mapper.six_key_mode is False

    # Default key mapping
    event_s = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_s)
    assert mapper.map_event(event_s) == Command.MOVE_DOWN

    # Enable home row six-key layout
    mapper.six_key_mode = True
    assert mapper.map_event(event_s) == Command.MOVE_LEFT


def test_app_slider_controls() -> None:
    """Tests slider value step adjustments using Left/Right keys in the Settings menu."""
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    app = EchoRunnerApp()
    app.load_user_settings = lambda: {}
    app.save_current_settings = lambda: None
    app.initialize()

    # Move to settings
    app.transition_to(AppState.SETTINGS)
    app.menu_index = app.menu_items.index("Speech Volume")

    assert app.speech_volume == 70

    # Increase volume
    app.handle_slider_input(pygame.K_RIGHT)
    assert app.speech_volume == 80

    # Decrease volume
    app.handle_slider_input(pygame.K_LEFT)
    assert app.speech_volume == 70

    app.shutdown()


def test_high_contrast_mode_setting() -> None:
    """Verifies that the high-contrast mode setting is toggled and rendered."""
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    app = EchoRunnerApp()
    app.load_user_settings = lambda: {}
    app.save_current_settings = lambda: None
    app.initialize()

    # Move to settings
    app.transition_to(AppState.SETTINGS)
    assert "High-Contrast Mode" in app.menu_items
    
    app.menu_index = app.menu_items.index("High-Contrast Mode")
    assert app.high_contrast_mode is False

    # Execute action to toggle
    app.execute_menu_action()
    assert app.high_contrast_mode is True

    # Test compute scan result
    scan_res = app.compute_scan_result()
    assert scan_res == "clear"

    app.shutdown()


def test_f8_trainer_marker() -> None:
    """Verifies that pressing F8 registers a trainer confusion marker in telemetry."""
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    app = EchoRunnerApp()
    app.load_user_settings = lambda: {}
    app.save_current_settings = lambda: None
    app.initialize()

    event_f8 = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F8)
    assert app.input_mapper.map_event(event_f8) == Command.MARK_CONFUSION

    logged_events = []
    if app.telemetry:
        app.telemetry.log_event = lambda event_type, **kwargs: logged_events.append((event_type, kwargs))

    pygame.event.post(event_f8)
    app.handle_input()

    assert any(ev[0] == "trainer_marker" for ev in logged_events)
    marker_event = [ev for ev in logged_events if ev[0] == "trainer_marker"][0]
    assert marker_event[1]["marker"] == "confusion"

    app.shutdown()



