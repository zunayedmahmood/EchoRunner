"""Speech line selection and playback manager for EchoRunner."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from echorunner.audio.openal_backend import CueEvent

if TYPE_CHECKING:
    from echorunner.audio.openal_backend import OpenALBackend
    from echorunner.app import EchoRunnerApp


class SpeechManager:
    """Manages playing self-voicing spoken audio cues in different languages."""

    def __init__(
        self,
        backend: OpenALBackend,
        lang: str = "en",
        app: Optional[EchoRunnerApp] = None,
    ) -> None:
        self.backend = backend
        self.lang = lang
        self.app = app
        self.last_spoken_id: str = ""
        self.last_spoken_text: str = ""

    def speak(self, text_id: str, interrupt: bool = True) -> None:
        """Plays the spoken audio file matching text_id and language."""
        file_id = f"{text_id}_{self.lang}"
        
        # Determine gain and pitch from app settings if available
        gain = 1.0
        pitch = 1.0
        if self.app:
            gain = self.app.speech_volume / 100.0
            pitch = self.app.speech_speed / 100.0

        cue = CueEvent(
            cue_id=text_id,
            file_id=file_id,
            priority=40,  # standard speech priority
            spatial=False,
            source_relative=True,
            interrupt_speech=interrupt,
            gain=gain,
            pitch=pitch,
        )
        self.backend.play_cue(cue)
        self.last_spoken_id = text_id

        # Load text transcript from file
        txt_path = (
            self.backend.workspace_dir
            / "soundLibrary"
            / "speech"
            / self.lang
            / "txt"
            / f"{file_id}.txt"
        )
        if txt_path.exists():
            try:
                with open(txt_path, "r", encoding="utf-8") as f:
                    self.last_spoken_text = f.read().strip()
            except Exception:
                self.last_spoken_text = f"[{text_id}]"
        else:
            self.last_spoken_text = f"[{text_id}]"

    def repeat_last(self) -> None:
        """Repeats the last spoken message."""
        if self.last_spoken_id:
            self.speak(self.last_spoken_id)

