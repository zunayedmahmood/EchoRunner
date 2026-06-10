"""Unit tests for the EchoRunner game simulation rules and AI behaviors."""
from __future__ import annotations

from pathlib import Path
import pytest

from echorunner.input.mapper import Command
from echorunner.simulation.engine import EnemyState, GameSimulation, Vec2


def test_player_cannot_pass_through_walls() -> None:
    """Verifies that the player runner is blocked by wall elements."""
    workspace_dir = Path(__file__).parent.parent.parent
    sim = GameSimulation(workspace_dir, "level_01_training_loop")

    # Set coordinate beside a wall
    sim.player_pos = Vec2(1, 1)
    sim.player_queued_dir = "up"  # wall is at (1, 0)

    sim.move_player()
    assert sim.player_pos == Vec2(1, 1)
    assert any(e["type"] == "wall_knock" for e in sim.events)


def test_pellets_collected_once_only() -> None:
    """Tests that collectibles increment count once and are removed from the map."""
    workspace_dir = Path(__file__).parent.parent.parent
    sim = GameSimulation(workspace_dir, "level_01_training_loop")

    sim.player_pos = Vec2(1, 1)
    sim.orbs = {Vec2(2, 1)}
    sim.collected_count = 0

    sim.player_queued_dir = "right"
    sim.move_player()

    assert sim.player_pos == Vec2(2, 1)
    assert sim.collected_count == 1
    assert Vec2(2, 1) not in sim.orbs

    # Double check re-entry does not trigger reward again
    sim.player_queued_dir = "left"
    sim.move_player()
    sim.player_queued_dir = "right"
    sim.move_player()

    assert sim.collected_count == 1


def test_level_clear_occurs() -> None:
    """Verifies that clear events are dispatched when the remaining orbs count drops to zero."""
    workspace_dir = Path(__file__).parent.parent.parent
    sim = GameSimulation(workspace_dir, "level_01_training_loop")

    sim.player_pos = Vec2(1, 1)
    sim.orbs = {Vec2(2, 1)}

    sim.player_queued_dir = "right"
    sim.move_player()

    assert any(e["type"] == "level_clear" for e in sim.events)


def test_power_mode_changes_enemy_state() -> None:
    """Verifies that grabbing a resonance core activates power mode and changes AI state."""
    workspace_dir = Path(__file__).parent.parent.parent
    sim = GameSimulation(workspace_dir, "level_01_training_loop")

    sim.player_pos = Vec2(1, 1)
    sim.orbs = {Vec2(2, 1)}
    sim.power_cores = {Vec2(2, 1)}

    # Verify initial AI states
    assert all(enemy.state == "patrol" for enemy in sim.enemies)

    sim.player_queued_dir = "right"
    sim.move_player()

    assert sim.power_timer > 0
    assert all(enemy.state == "frightened" for enemy in sim.enemies)
    assert any(e["type"] == "power_activate" for e in sim.events)


def test_enemy_collision_creates_death_cause() -> None:
    """Verifies that player-enemy collisions dispatch player_killed events."""
    workspace_dir = Path(__file__).parent.parent.parent
    sim = GameSimulation(workspace_dir, "level_01_training_loop")

    sim.player_pos = Vec2(1, 1)
    assert len(sim.enemies) > 0
    sim.enemies[0].tile = Vec2(1, 1)

    sim.check_collisions()
    assert any(e["type"] == "player_killed" for e in sim.events)


def test_threat_model_outputs() -> None:
    """Verifies that threat classification sets the correct output parameters on EnemyState."""
    workspace_dir = Path(__file__).parent.parent.parent
    sim = GameSimulation(workspace_dir, "level_01_training_loop")

    sim.player_pos = Vec2(1, 1)
    enemy = sim.enemies[0]
    enemy.tile = Vec2(2, 1)  # corridor distance 1
    enemy.state = "patrol"

    threat_class = sim.classify_threat(enemy)
    assert threat_class == "red"
    assert enemy.intercept_estimate <= 1.4
    assert enemy.source_pos == (2.0, 0.0, 1.0)
    assert enemy.cue_priority == 100
    assert enemy.player_hint == "Run in the opposite direction!"


def test_replay_logger_deterministic_serialization(tmp_path: Path) -> None:
    """Tests the ReplayLogger functionality and serialization structure."""
    from echorunner.telemetry.logger import ReplayLogger
    import json

    logger = ReplayLogger(
        session_id="test_session",
        level_id="test_level",
        seed=12345,
        output_dir=tmp_path
    )

    logger.record_command(0.123, "MOVE_UP")
    logger.record_event(0.234, "footstep", {"pos": Vec2(1, 2)})
    logger.record_cue(0.345, "move_step_soft", 10)
    logger.record_death(0.456, "power_ended", [1, 2])
    logger.save()

    replay_file = tmp_path / "replay.json"
    assert replay_file.exists()

    data = json.loads(replay_file.read_text(encoding="utf-8"))
    assert data["level_id"] == "test_level"
    assert data["random_seed"] == 12345
    assert len(data["commands"]) == 1
    assert data["commands"][0]["cmd"] == "MOVE_UP"
    assert data["commands"][0]["t"] == 0.123
    assert data["events"][0]["pos"] == [1, 2]
    assert data["deaths"][0]["cause"] == "power_ended"


def test_study_anonymization_and_metrics(tmp_path: Path) -> None:
    """Verifies that export_session successfully anonymizes data and computes HCI metrics."""
    from echorunner.research.study import export_session
    import json

    # Setup dummy session directory structure
    session_id = "test_study_session"
    session_dir = tmp_path / "data" / "sessions" / session_id
    session_dir.mkdir(parents=True)

    events_file = session_dir / "events.jsonl"
    events_content = (
        '{"t": 0.0, "type": "session_start", "session_id": "participant_name_123"}\n'
        '{"t": 1.25, "type": "cue", "cue_id": "scan_pulse", "priority": 10}\n'
        '{"t": 2.50, "type": "death", "cause": "hunter", "tile": [1, 2]}\n'
        '{"t": 3.75, "type": "level_clear"}\n'
    )
    events_file.write_text(events_content, encoding="utf-8")

    replay_file = session_dir / "replay.json"
    replay_data = {
        "session_id": "participant_name_123",
        "commands": [{"t": 0.123, "cmd": "MOVE_UP"}],
        "events": [{"t": 1.234, "type": "footstep"}],
        "cues": [{"t": 2.345, "cue_id": "scan_pulse"}],
        "deaths": [{"t": 3.456, "cause": "hunter"}]
    }
    replay_file.write_text(json.dumps(replay_data), encoding="utf-8")

    # Run export in working directory mock (let's patch Path.cwd() inside study)
    import echorunner.research.study
    old_cwd = echorunner.research.study.Path.cwd
    echorunner.research.study.Path.cwd = lambda: tmp_path
    try:
        export_session(session_id, anonymized=True)
    finally:
        echorunner.research.study.Path.cwd = old_cwd

    export_file = session_dir / "anonymized_export.json"
    assert export_file.exists()

    data = json.loads(export_file.read_text(encoding="utf-8"))
    assert data["consent_obtained"] is True
    assert data["metrics"]["deaths"] == 1
    # Check rounded timestamp to 1 decimal place
    assert data["replay"]["commands"][0]["t"] == 0.1
    assert data["replay"]["events"][0]["t"] == 1.2
    assert data["replay"]["cues"][0]["t"] == 2.3
    # Check stripped participant ID
    assert data["replay"]["session_id"] == "ANON_SESSION"

