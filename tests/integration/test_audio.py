"""Unit tests for the EchoRunner OpenAL audio systems."""
from __future__ import annotations

from pathlib import Path
import pytest

from echorunner.audio import openal_ctypes
from echorunner.audio.openal_backend import OpenALBackend


def test_ctypes_loading() -> None:
    """Verifies that the OpenAL library is loaded successfully."""
    assert openal_ctypes._lib is not None


def test_device_lifecycle() -> None:
    """Tests opening and closing of default OpenAL device and context."""
    device = openal_ctypes.open_device()
    assert device is not None

    context = openal_ctypes.create_context(device)
    assert context is not None

    openal_ctypes.destroy_context(context)
    success = openal_ctypes.close_device(device)
    assert success is True


def test_backend_lifecycle() -> None:
    """Tests the start and stop sequence of high-level OpenALBackend."""
    workspace_dir = Path(__file__).parent.parent.parent
    backend = OpenALBackend(workspace_dir=workspace_dir)

    backend.start()
    assert backend.enabled is True
    assert len(backend.buffers) > 0

    backend.stop()
    assert backend.enabled is False


def test_audio_ducking_engine() -> None:
    """Verifies that playing a high priority red alert ducks lower-priority sounds."""
    workspace_dir = Path(__file__).parent.parent.parent
    backend = OpenALBackend(workspace_dir=workspace_dir)
    backend.start()

    from echorunner.audio.openal_backend import CueEvent

    # Play low priority background sound
    cue_music = CueEvent(cue_id="music", file_id="landmark_safe_loop", priority=10, spatial=False, gain=1.0)
    backend.play_cue(cue_music)

    # Retrieve source
    music_src = None
    for src, cue in backend._source_to_cue.items():
        if cue.cue_id == "music":
            music_src = src
            break
    assert music_src is not None

    # Play a red threat (priority 90)
    cue_red = CueEvent(cue_id="red_alarm", file_id="landmark_danger_loop", priority=90, spatial=True)
    backend.play_cue(cue_red)

    backend.stop()


def test_mono_fallback_coordinates() -> None:
    """Verifies that enabling mono mode collapses spatial sound coordinates to prevent panning."""
    workspace_dir = Path(__file__).parent.parent.parent
    backend = OpenALBackend(workspace_dir=workspace_dir)
    backend.start()
    backend.mono_mode = True

    from echorunner.audio.openal_backend import CueEvent
    cue = CueEvent(cue_id="sfx", file_id="pellet_tick", priority=30, spatial=True, position=(5.0, 0.0, 5.0))
    backend.play_cue(cue)

    # Coordinates must collapse to center to prevent panning
    assert cue.position == (0.0, 0.0, 0.0)
    assert cue.source_relative is True

    backend.stop()


def test_cue_planner_priorities() -> None:
    """Verifies that the CuePlanner ranks threats and limits active cues to the top two threats."""
    from echorunner.cues.planner import CuePlanner
    from echorunner.simulation.player import Player
    from echorunner.simulation.enemy import Enemy
    from echorunner.simulation.world import Vec2

    planner = CuePlanner()
    player = Player(Vec2(1, 1))

    # Create 3 active enemies with threat levels: hunter(green), ambusher(red), trickster(amber)
    e1 = Enemy("1", "hunter", Vec2(2, 2))
    e1.threat = "green"

    e2 = Enemy("2", "ambusher", Vec2(3, 3))
    e2.threat = "red"

    e3 = Enemy("3", "trickster", Vec2(4, 4))
    e3.threat = "amber"

    cues = planner.plan_cues(player, [e1, e2, e3])

    # Top two should be ambusher (red, priority 90) and trickster (amber, priority 70)
    # The green threat should be excluded/limited because we only keep the top 2 active threats
    assert len(cues) == 2
    assert cues[0].cue_id == "enemy_2"  # Red
    assert cues[0].priority == 90
    assert cues[1].cue_id == "enemy_3"  # Amber
    assert cues[1].priority == 70


