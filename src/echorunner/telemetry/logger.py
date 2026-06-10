"""JSONL session logging and research telemetry for EchoRunner."""
from __future__ import annotations

import json
import time
from pathlib import Path


class TelemetryLogger:
    """Manages telemetry session folders and appends events to a JSONL log file."""

    def __init__(self, session_id: str, output_dir: Path | None = None) -> None:
        self.session_id = session_id
        self.output_dir = (
            output_dir or Path.cwd() / "data" / "sessions" / session_id
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.output_dir / "events.jsonl"
        self.start_time = time.time()

        # Log session startup
        self.log_event("session_start", session_id=session_id)

    def log_event(self, event_type: str, **kwargs) -> None:
        """Appends a single structured JSONL event with relative time offset."""
        offset = time.time() - self.start_time
        event = {"t": round(offset, 3), "type": event_type, **kwargs}
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            # Silent fallback / logger shouldn't crash gameplay
            pass


class ReplayLogger:
    """Records deterministic replay sequences for EchoRunner levels."""

    def __init__(self, session_id: str, level_id: str, seed: int, output_dir: Path) -> None:
        self.session_id = session_id
        self.level_id = level_id
        self.seed = seed
        self.output_dir = output_dir
        self.replay_file = self.output_dir / "replay.json"
        
        self.data = {
            "level_id": level_id,
            "random_seed": seed,
            "commands": [],
            "events": [],
            "cues": [],
            "deaths": []
        }
        
    def record_command(self, t: float, cmd: str) -> None:
        self.data["commands"].append({"t": round(t, 3), "cmd": cmd})
        
    def record_event(self, t: float, event_type: str, details: dict) -> None:
        serialized_details = {}
        for k, v in details.items():
            if hasattr(v, "x") and hasattr(v, "y"):
                serialized_details[k] = [v.x, v.y]
            elif isinstance(v, list) and all(hasattr(item, "x") and hasattr(item, "y") for item in v):
                serialized_details[k] = [[item.x, item.y] for item in v]
            else:
                serialized_details[k] = v
        self.data["events"].append({"t": round(t, 3), "type": event_type, **serialized_details})
        
    def record_cue(self, t: float, cue_id: str, priority: int) -> None:
        self.data["cues"].append({"t": round(t, 3), "cue_id": cue_id, "priority": priority})
        
    def record_death(self, t: float, cause: str, tile: list[int]) -> None:
        self.data["deaths"].append({"t": round(t, 3), "cause": cause, "tile": tile})
        
    def save(self) -> None:
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.replay_file.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
        except Exception:
            pass

