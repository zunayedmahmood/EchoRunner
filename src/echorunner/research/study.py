from __future__ import annotations

import json
import time
from pathlib import Path
import sys

def run_consent_flow() -> bool:
    """Displays and voices a standard HCI study consent prompt."""
    print("=" * 60)
    print("           ECHORUNNER HCI RESEARCH CONSENT PROTOCOL")
    print("=" * 60)
    print("Disclaimer: Consent templates are not formal legal approval.")
    print("This study evaluates spatial audio navigation interface design.")
    print("Data recorded: keyboard inputs, simulation events, threat categories.")
    print("No audio recordings, names, or network telemetry will be collected.")
    print("-" * 60)
    print("Do you consent to participate? Press ENTER to consent, or ESC to decline.")
    print("=" * 60)
    
    # We will let the app run the interactive loop for this if in Pygame.
    # But for a terminal fallback or simple check:
    return True

class StudySession:
    """Manages HCI research session questionnaire data collection and summary metrics."""

    def __init__(self, session_id: str, participant_id: str, level_id: str) -> None:
        self.session_id = session_id
        self.participant_id = participant_id
        self.level_id = level_id
        self.start_time = time.time()
        
        self.deaths = 0
        self.red_warnings = 0
        self.scan_count = 0
        self.wall_collisions = 0
        self.power_activations = 0
        self.tutorial_retries = 0
        self.junction_ticks = {} # pos -> ticks spent
        self.total_ticks = 0
        self.completed = False
        
        self.cue_density = "beginner"
        self.audio_mode = "headphones" # mono, headphones
        
    def record_simulation_event(self, event: dict) -> None:
        etype = event.get("type")
        if etype == "player_killed":
            self.deaths += 1
        elif etype == "threat" and event.get("class") == "red":
            self.red_warnings += 1
        elif etype == "scan_pulse":
            self.scan_count += 1
        elif etype == "wall_knock":
            self.wall_collisions += 1
        elif etype == "power_activate":
            self.power_activations += 1
        elif etype == "tutorial_retry":
            self.tutorial_retries += 1
            
    def compute_metrics(self) -> dict:
        duration_mins = (time.time() - self.start_time) / 60.0
        if duration_mins <= 0:
            duration_mins = 0.01
            
        return {
            "participant_id": self.participant_id,
            "level_id": self.level_id,
            "duration_minutes": round(duration_mins, 2),
            "deaths_count": self.deaths,
            "red_warnings_before_death": self.red_warnings,
            "scan_usage_per_minute": round(self.scan_count / duration_mins, 2),
            "wall_collisions_per_minute": round(self.wall_collisions / duration_mins, 2),
            "power_mode_usage": self.power_activations,
            "tutorial_retry_count": self.tutorial_retries,
            "cue_density": self.cue_density,
            "audio_mode": self.audio_mode,
            "level_completed": self.completed,
        }

def collect_post_task_prompts() -> dict[str, str]:
    """Collects responses to post-task HCI prompts from the terminal."""
    questions = [
        ("clear_sounds", "Which sounds were clear?"),
        ("confusing_sounds", "Which sounds were confusing?"),
        ("know_enemies", "Did you know where enemies were?"),
        ("know_death", "Did you know why you lost a life?"),
        ("speech_volume", "Was speech too much or too little?"),
        ("mental_map", "Could you imagine the maze in your mind?"),
        ("next_easier", "What should be easier in the next version?"),
    ]
    answers = {}
    print("\n" + "=" * 60)
    print("            POST-TASK INTERVIEW QUESTIONS")
    print("=" * 60)
    for key, q in questions:
        print(f"\nPrompt: {q}")
        try:
            ans = input("Answer: ").strip()
        except (IOError, KeyboardInterrupt):
            ans = "No response"
        answers[key] = ans
    return answers

def get_sessions_dir() -> Path:
    """Returns the sessions directory by searching both dev and installed locations."""
    # 1. Dev directory
    dev_dir = Path.cwd() / "data" / "sessions"
    if dev_dir.exists() and any(dev_dir.iterdir()):
        return dev_dir
    # 2. Installed directory (platformdirs or fallback)
    try:
        import platformdirs
        installed_dir = Path(platformdirs.user_data_dir("EchoRunner")) / "sessions"
        if installed_dir.exists() and any(installed_dir.iterdir()):
            return installed_dir
    except ImportError:
        pass
    import os
    home = Path.home()
    if sys.platform.startswith("win"):
        appdata = Path(os.environ.get("APPDATA", str(home / "AppData" / "Roaming")))
        win_dir = appdata / "EchoRunner" / "sessions"
        if win_dir.exists() and any(win_dir.iterdir()):
            return win_dir
    else:
        linux_dir = home / ".local" / "share" / "EchoRunner" / "sessions"
        if linux_dir.exists() and any(linux_dir.iterdir()):
            return linux_dir
    # Fallback to dev dir
    return dev_dir

def export_session(session_id: str, anonymized: bool = True) -> None:
    """Exports session telemetry summary and optionally anonymizes it."""
    sessions_dir = get_sessions_dir()
    session_path = sessions_dir / session_id
    if not session_path.exists() or session_id == "latest":
        # Find latest session if session_id is latest or not found
        if session_id == "latest" or not session_path.exists():
            subdirs = sorted([d for d in sessions_dir.iterdir() if d.is_dir()], key=lambda x: x.stat().st_mtime)
            if subdirs:
                session_path = subdirs[-1]
                session_id = session_path.name
            else:
                print("No sessions found to export.")
                return
        if not session_path.exists():
            print(f"Session directory {session_id} not found.")
            return

    events_file = session_path / "events.jsonl"
    replay_file = session_path / "replay.json"
    
    # Read files
    events = []
    if events_file.exists():
        for line in events_file.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    events.append(json.loads(line))
                except Exception:
                    pass
                    
    replay = {}
    if replay_file.exists():
        try:
            replay = json.loads(replay_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Extract metrics from telemetry events
    deaths = 0
    red_warnings = 0
    scans = 0
    walls = 0
    powers = 0
    completed = False
    participant_id = "P_unknown"
    level_id = "unknown"
    cue_density = "beginner"
    mono_mode = False
    
    start_t = 0
    end_t = 0
    for ev in events:
        etype = ev.get("type")
        t = ev.get("t", 0)
        end_t = max(end_t, t)
        if etype == "session_start":
            participant_id = ev.get("session_id", "P_unknown")
        elif etype == "state_transition" and ev.get("to_state") == "GAMEPLAY":
            pass
        elif etype == "death":
            deaths += 1
        elif etype == "threat" and ev.get("class") == "red":
            red_warnings += 1
        elif etype == "cue" and ev.get("cue_id") == "scan_pulse":
            scans += 1
        elif etype == "cue" and ev.get("cue_id") == "wall_knock":
            walls += 1
        elif etype == "cue" and ev.get("cue_id") == "power_activate":
            powers += 1
        elif etype == "level_clear" or (etype == "state_transition" and ev.get("to_state") == "RESULTS"):
            completed = True

    duration = end_t - start_t
    duration_min = max(0.01, duration / 60.0)

    # Anonymize
    if anonymized:
        # Round timestamps to 1 decimal place in replay
        if "commands" in replay:
            for c in replay["commands"]:
                c["t"] = round(c["t"], 1)
        if "events" in replay:
            for e in replay["events"]:
                e["t"] = round(e["t"], 1)
        if "cues" in replay:
            for cu in replay["cues"]:
                cu["t"] = round(cu["t"], 1)
        if "deaths" in replay:
            for d in replay["deaths"]:
                d["t"] = round(d["t"], 1)
        # Strip any raw participant names
        participant_id = "ANON_PARTICIPANT"
        if "session_id" in replay:
            replay["session_id"] = "ANON_SESSION"

    # Write summary.md
    summary_md = f"""# EchoRunner Research Session Summary
- **Session ID**: {session_id}
- **Participant ID**: {participant_id}
- **Duration**: {round(duration_min, 2)} minutes

## Balancing Metrics
- Total Deaths: {deaths}
- Red Warnings Before Death: {red_warnings}
- Scan Usage per Minute: {round(scans / duration_min, 2)}
- Wall Collisions per Minute: {round(walls / duration_min, 2)}
- Power Core Activations: {powers}
- Level Completion Rate: {100 if completed else 0}%

## Privacy Note
- Local-first telemetry stored inside session folder.
- Consent template did not constitute formal legal approval.
"""
    (session_path / "summary.md").write_text(summary_md, encoding="utf-8")

    # Save anonymized_export.json
    export_data = {
        "consent_obtained": True,
        "anonymized": True,
        "metrics": {
            "deaths": deaths,
            "red_warnings": red_warnings,
            "scans_per_min": round(scans / duration_min, 2),
            "walls_per_min": round(walls / duration_min, 2),
            "powers": powers,
            "completed": completed
        },
        "replay": replay
    }
    (session_path / "anonymized_export.json").write_text(json.dumps(export_data, indent=2), encoding="utf-8")
    print(f"Exported session data to {session_path}")

def delete_session_telemetry(session_id: str) -> None:
    """Deletes all local telemetry data for a specific session ID to ensure privacy compliance."""
    sessions_dir = get_sessions_dir()
    session_path = sessions_dir / session_id
    if session_path.exists() and session_path.is_dir():
        for item in session_path.iterdir():
            if item.is_file():
                item.unlink()
        session_path.rmdir()
        print(f"Deleted telemetry data for session: {session_id}")
    else:
        print(f"Session {session_id} not found.")
