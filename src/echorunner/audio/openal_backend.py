"""High-level OpenAL backend implementation for EchoRunner."""
from __future__ import annotations

import json
import logging
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from echorunner.audio import openal_ctypes

logger = logging.getLogger(__name__)


@dataclass
class CueEvent:
    cue_id: str
    file_id: str
    priority: int
    spatial: bool
    position: Optional[tuple[float, float, float]] = None
    gain: float = 1.0
    pitch: float = 1.0
    loop: bool = False
    source_relative: bool = False
    interrupt_speech: bool = False
    reason: str = ""


class OpenALBackend:
    """Implementation of the OpenAL spatial audio backend using ctypes wrapper."""

    def __init__(self, workspace_dir: Optional[Path] = None) -> None:
        self.workspace_dir = workspace_dir or Path.cwd()
        self.device: Optional[int] = None
        self.context: Optional[int] = None
        self.buffers: Dict[str, int] = {}
        self.source_pool: List[int] = []
        self._source_to_cue: Dict[int, CueEvent] = {}
        self.enabled = False
        self.mono_mode = False

    def _check_error(self, operation: str) -> None:
        """Helper to verify OpenAL error flags."""
        err = openal_ctypes.get_error()
        if err != openal_ctypes.AL_NO_ERROR:
            logger.error(f"OpenAL error after {operation}: {err}")

    def start(self) -> None:
        """Open device, create context, configure distance model, load buffers."""
        try:
            self.device = openal_ctypes.open_device()
            if not self.device:
                raise RuntimeError("Could not open default OpenAL device.")

            self.context = openal_ctypes.create_context(self.device)
            if not self.context:
                openal_ctypes.close_device(self.device)
                self.device = None
                raise RuntimeError("Could not create OpenAL context.")

            self._check_error("OpenAL context creation")

            # Device Diagnostics and Enumeration (Section 4)
            default_device = openal_ctypes.alc_get_string(
                self.device, openal_ctypes.ALC_DEFAULT_DEVICE_SPECIFIER
            ) or "Unknown"
            device_list = openal_ctypes.get_device_list(self.device)
            vendor = openal_ctypes.al_get_string(openal_ctypes.AL_VENDOR) or "Unknown"
            version = openal_ctypes.al_get_string(openal_ctypes.AL_VERSION) or "Unknown"
            renderer = openal_ctypes.al_get_string(openal_ctypes.AL_RENDERER) or "Unknown"

            logger.info(f"Default Playback Device: {default_device}")
            logger.info(f"Available Playback Devices: {device_list}")
            logger.info(
                f"OpenAL System Details: Vendor={vendor}, Version={version}, Renderer={renderer}"
            )

            # Configure distance model and Doppler (Section 9 & 10)
            openal_ctypes.distance_model(openal_ctypes.AL_INVERSE_DISTANCE_CLAMPED)
            openal_ctypes.doppler_factor(0.0)

            # Create source pool (32 sources)
            self.source_pool = openal_ctypes.gen_sources(32)
            self._source_to_cue.clear()

            # Load audio buffers from manifest
            self._load_buffers_from_manifest()

            self.enabled = True
            logger.info("OpenAL backend started successfully.")

        except Exception as e:
            logger.error(f"Failed to start OpenAL backend: {e}")
            self.stop()
            raise RuntimeError(f"OpenAL Init Failure: {e}") from e

    def stop(self) -> None:
        """Stop sources, delete buffers/sources, destroy context, close device."""
        self.enabled = False

        if self.source_pool:
            for src in self.source_pool:
                openal_ctypes.source_stop(src)
            openal_ctypes.delete_sources(self.source_pool)
            self.source_pool.clear()

        if self.buffers:
            openal_ctypes.delete_buffers(list(self.buffers.values()))
            self.buffers.clear()

        if self.context:
            openal_ctypes.destroy_context(self.context)
            self.context = None

        if self.device:
            openal_ctypes.close_device(self.device)
            self.device = None

        self._source_to_cue.clear()
        logger.info("OpenAL backend stopped.")

    def _load_buffers_from_manifest(self) -> None:
        """Load and parse WAV files defined in manifest.json."""
        manifest_path = self.workspace_dir / "soundLibrary" / "manifest.json"
        if not manifest_path.exists():
            logger.warning(f"Audio manifest not found at {manifest_path}")
            return

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)

        assets = manifest_data.get("assets", [])
        for asset in assets:
            file_id = asset.get("id")
            relative_path = asset.get("path")
            if not file_id or not relative_path:
                continue

            full_path = self.workspace_dir / relative_path
            if not full_path.exists():
                logger.warning(f"Audio file missing: {full_path}")
                continue

            try:
                # Load WAV using stdlib wave
                with wave.open(str(full_path), "rb") as w:
                    params = w.getparams()
                    nchannels = params.nchannels
                    sampwidth = params.sampwidth
                    framerate = params.framerate
                    nframes = params.nframes
                    raw_data = w.readframes(nframes)

                # Determine OpenAL format
                if nchannels == 1:
                    if sampwidth == 1:
                        al_format = openal_ctypes.AL_FORMAT_MONO8
                    elif sampwidth == 2:
                        al_format = openal_ctypes.AL_FORMAT_MONO16
                    else:
                        logger.error(
                            f"Unsupported sample width {sampwidth} for mono file {full_path}"
                        )
                        continue
                elif nchannels == 2:
                    if sampwidth == 1:
                        al_format = openal_ctypes.AL_FORMAT_STEREO8
                    elif sampwidth == 2:
                        al_format = openal_ctypes.AL_FORMAT_STEREO16
                    else:
                        logger.error(
                            f"Unsupported sample width {sampwidth} for stereo file {full_path}"
                        )
                        continue
                else:
                    logger.error(
                        f"Unsupported channel count {nchannels} for file {full_path}"
                    )
                    continue

                # Generate buffer and upload data
                buf_id = openal_ctypes.gen_buffers(1)[0]
                openal_ctypes.buffer_data(buf_id, al_format, raw_data, framerate)
                self.buffers[file_id] = buf_id

            except Exception as e:
                logger.error(f"Error loading audio file {full_path}: {e}")

    def update_listener(
        self, position: tuple[float, float, float], direction: str
    ) -> None:
        """Update OpenAL listener position and orientation from player state."""
        if not self.enabled:
            return

        # Collapse orientation coordinates in mono mode
        if self.mono_mode:
            openal_ctypes.listener_set_position((0.0, 0.0, 0.0))
            openal_ctypes.listener_set_orientation((1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
            return

        openal_ctypes.listener_set_position(position)

        d = direction.lower()
        if d in ("up", "north"):
            at = (0.0, 0.0, -1.0)
        elif d in ("down", "south"):
            at = (0.0, 0.0, 1.0)
        elif d in ("left", "west"):
            at = (-1.0, 0.0, 0.0)
        else:  # right / east / default
            at = (1.0, 0.0, 0.0)

        up = (0.0, 1.0, 0.0)
        openal_ctypes.listener_set_orientation(at, up)
        self._check_error("update_listener")

    def _apply_ducking(self) -> None:
        """Computes and applies dynamic decibel gain ducking across active sound sources."""
        if not self.enabled:
            return

        # 1. Determine active priority overrides by scanning active sources
        has_life_lost = False
        has_red_threat = False
        has_power_ending = False
        has_speech = False

        for src, active_cue in list(self._source_to_cue.items()):
            state = openal_ctypes.source_get_state(src)
            if state == openal_ctypes.AL_PLAYING:
                if active_cue.priority >= 100:
                    has_life_lost = True
                elif active_cue.priority >= 90:
                    has_red_threat = True
                elif active_cue.priority == 80:
                    has_power_ending = True
                elif 40 <= active_cue.priority < 70:
                    has_speech = True
            else:
                self._source_to_cue.pop(src, None)

        # 2. Re-apply scaled gain factors to all playing sources
        for src, active_cue in list(self._source_to_cue.items()):
            state = openal_ctypes.source_get_state(src)
            if state != openal_ctypes.AL_PLAYING:
                continue

            target_gain = active_cue.gain

            if has_life_lost:
                # Mute all non-essential sounds
                if active_cue.priority < 100:
                    target_gain = 0.0
            elif has_red_threat:
                # -12 dB for ambience/music, -6 dB for reward clicks/steps
                if active_cue.cue_id in ("ambience", "music"):
                    target_gain *= 0.25
                elif active_cue.cue_id in ("pellet_tick", "move_step_soft"):
                    target_gain *= 0.50
            elif has_speech:
                # -10 dB for ambience/music
                if active_cue.cue_id in ("ambience", "music"):
                    target_gain *= 0.31
            elif has_power_ending:
                # -8 dB for ambience/music
                if active_cue.cue_id in ("ambience", "music"):
                    target_gain *= 0.40

            openal_ctypes.source_set_gain(src, target_gain)

    def play_cue(self, cue: CueEvent) -> None:
        """Play or schedule a cue using source pooling and priority rules."""
        if not self.enabled:
            return

        # Speech interrupt policy: High priority alerts (>=90) interrupt lower priority speech (<70)
        if cue.priority >= 90:
            for src, active_cue in list(self._source_to_cue.items()):
                if active_cue.priority < 70:
                    state = openal_ctypes.source_get_state(src)
                    if state == openal_ctypes.AL_PLAYING:
                        openal_ctypes.source_stop(src)
                        logger.info(
                            f"Interrupting cue {active_cue.cue_id} due to high priority alert {cue.cue_id}"
                        )

        # If this cue is speech and requests interruption, stop other playing speech cues
        if cue.interrupt_speech:
            for src, active_cue in list(self._source_to_cue.items()):
                if active_cue.interrupt_speech and active_cue.cue_id != cue.cue_id:
                    state = openal_ctypes.source_get_state(src)
                    if state == openal_ctypes.AL_PLAYING:
                        openal_ctypes.source_stop(src)
                        logger.info(
                            f"Interrupting speech cue {active_cue.cue_id} for new speech cue {cue.cue_id}"
                        )

        # Resolve buffer
        buf_id = self.buffers.get(cue.file_id) or self.buffers.get(cue.cue_id)
        if not buf_id:
            logger.warning(
                f"No audio buffer found for cue: {cue.file_id} / {cue.cue_id}"
            )
            return

        # Mono Fallback collapses panning coordinates (Section 17).
        # Keep the historical behavior of updating the CueEvent, because the
        # test suite uses that to verify mono coordinates are actually collapsed.
        if self.mono_mode and cue.spatial:
            cue.source_relative = True
            cue.position = (0.0, 0.0, 0.0)

        # If this cue is already active, update its moving source instead of
        # restarting it every frame. This prevents enemy alerts from clicking,
        # reduces OpenAL calls, and keeps spatial tracking smooth.
        for src, active_cue in list(self._source_to_cue.items()):
            state = openal_ctypes.source_get_state(src)
            if state not in (openal_ctypes.AL_PLAYING, openal_ctypes.AL_PAUSED):
                self._source_to_cue.pop(src, None)
                continue
            if active_cue.cue_id == cue.cue_id:
                openal_ctypes.source_set_gain(src, cue.gain)
                openal_ctypes.source_set_pitch(src, cue.pitch)
                openal_ctypes.source_set_looping(src, cue.loop)
                openal_ctypes.source_set_relative(src, cue.source_relative)
                pos = cue.position if cue.position is not None else (0.0, 0.0, 0.0)
                openal_ctypes.source_set_position(src, pos)
                if cue.spatial and not cue.source_relative:
                    openal_ctypes.source_set_distance_params(src, 1.5, 12.0, 1.0)
                else:
                    openal_ctypes.source_set_distance_params(src, 1.0, 100.0, 0.0)
                self._source_to_cue[src] = cue
                self._apply_ducking()
                return

        target_source: Optional[int] = None

        # 1. Look for a stopped or initial source in the pool
        for src in self.source_pool:
            state = openal_ctypes.source_get_state(src)
            if state not in (openal_ctypes.AL_PLAYING, openal_ctypes.AL_PAUSED):
                target_source = src
                break

        # 2. If no free source, evict the lowest priority playing source
        if target_source is None:
            lowest_priority = cue.priority
            lowest_src: Optional[int] = None

            for src in self.source_pool:
                playing_cue = self._source_to_cue.get(src)
                if playing_cue:
                    state = openal_ctypes.source_get_state(src)
                    if state not in (openal_ctypes.AL_PLAYING, openal_ctypes.AL_PAUSED):
                        target_source = src
                        break

                    if playing_cue.priority < lowest_priority:
                        lowest_priority = playing_cue.priority
                        lowest_src = src

            if target_source is None and lowest_src is not None:
                target_source = lowest_src
                openal_ctypes.source_stop(target_source)

        # 3. If we found a source, set its properties and play
        if target_source is not None:
            openal_ctypes.source_set_buffer(target_source, buf_id)
            openal_ctypes.source_set_gain(target_source, cue.gain)
            openal_ctypes.source_set_pitch(target_source, cue.pitch)
            openal_ctypes.source_set_looping(target_source, cue.loop)
            openal_ctypes.source_set_relative(target_source, cue.source_relative)

            pos = cue.position if cue.position is not None else (0.0, 0.0, 0.0)
            openal_ctypes.source_set_position(target_source, pos)

            # Apply distance attenuation for spatial cues (Section 9)
            if cue.spatial and not cue.source_relative:
                # reference_dist = 1.5, max_dist = 12.0, rolloff = 1.0
                openal_ctypes.source_set_distance_params(
                    target_source, 1.5, 12.0, 1.0
                )
            else:
                openal_ctypes.source_set_distance_params(
                    target_source, 1.0, 100.0, 0.0
                )

            openal_ctypes.source_play(target_source)
            self._source_to_cue[target_source] = cue
            self._check_error(f"play_cue {cue.cue_id}")

            # Apply dynamic ducking scaling coefficients
            self._apply_ducking()
        else:
            logger.debug(f"Discarding cue {cue.cue_id} due to lower priority.")

    def get_active_cue_id(self) -> str:
        """Returns the ID of the highest priority active cue currently playing."""
        playing_cues = []
        for src, cue in list(self._source_to_cue.items()):
            state = openal_ctypes.source_get_state(src)
            if state == openal_ctypes.AL_PLAYING:
                playing_cues.append(cue)
        if playing_cues:
            playing_cues.sort(key=lambda x: x.priority, reverse=True)
            return playing_cues[0].cue_id
        return "none"

    def stop_cue(self, cue_id: str) -> None:
        """Stops any active source playing the specified cue_id."""
        for src, cue in list(self._source_to_cue.items()):
            if cue.cue_id == cue_id or cue.file_id == cue_id:
                openal_ctypes.source_stop(src)
                self._source_to_cue.pop(src, None)
                self._apply_ducking()
