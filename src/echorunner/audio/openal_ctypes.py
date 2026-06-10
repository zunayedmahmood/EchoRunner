"""Thin ctypes wrapper around OpenAL Soft for EchoRunner."""
from __future__ import annotations

import ctypes
import os
import sys
from typing import Optional

# OpenAL constants
AL_FORMAT_MONO8 = 0x1100
AL_FORMAT_MONO16 = 0x1101
AL_FORMAT_STEREO8 = 0x1102
AL_FORMAT_STEREO16 = 0x1103

AL_SOURCE_RELATIVE = 0x202
AL_LOOPING = 0x1007
AL_POSITION = 0x1004
AL_GAIN = 0x100A
AL_PITCH = 0x1003

AL_ORIENTATION = 0x100F

AL_REFERENCE_DISTANCE = 0x1020
AL_ROLLOFF_FACTOR = 0x1021
AL_MAX_DISTANCE = 0x1023

AL_DISTANCE_MODEL = 0xD000
AL_INVERSE_DISTANCE_CLAMPED = 0xD002

AL_NO_ERROR = 0

ALC_DEFAULT_DEVICE_SPECIFIER = 0x1004
ALC_DEVICE_SPECIFIER = 0x1005
AL_VENDOR = 0xB001
AL_VERSION = 0xB002
AL_RENDERER = 0xB003

AL_SOURCE_STATE = 0x1010
AL_INITIAL = 0x1011
AL_PLAYING = 0x1012
AL_PAUSED = 0x1013
AL_STOPPED = 0x1014

# Types
ALCdevice_p = ctypes.c_void_p
ALCcontext_p = ctypes.c_void_p
ALuint = ctypes.c_uint
ALsizei = ctypes.c_int
ALenum = ctypes.c_int
ALfloat = ctypes.c_float
ALint = ctypes.c_int

# Load library
from pathlib import Path

_lib: ctypes.CDLL | None = None
lib_names: list[str] = []

# Headless fallback state. This is used only when OpenAL Soft is installed but
# no playback device can be opened, which is common in CI and remote servers.
_fallback_mode = False
_FAKE_DEVICE = 1
_FAKE_CONTEXT = 1
_next_buffer_id = 1000
_next_source_id = 2000
_fake_source_states: dict[int, int] = {}

if sys.platform.startswith("win"):
    lib_names = ["OpenAL32.dll", "soft_oal.dll"]
elif sys.platform.startswith("darwin"):
    lib_names = ["libopenal.dylib", "OpenAL.framework/OpenAL"]
else:
    lib_names = ["libopenal.so.1", "libopenal.so"]

# Build search directories
search_dirs: list[Path] = []
if hasattr(sys, "_MEIPASS"):
    search_dirs.append(Path(sys._MEIPASS))
search_dirs.append(Path.cwd())
search_dirs.append(Path(__file__).parent)
search_dirs.append(Path(__file__).parent.parent.parent)

# Try system-wide first
for name in lib_names:
    try:
        _lib = ctypes.CDLL(name)
        break
    except OSError:
        continue

# Try search paths if not loaded
if _lib is None:
    for d in search_dirs:
        for name in lib_names:
            lib_path = d / name
            if lib_path.exists():
                try:
                    _lib = ctypes.CDLL(str(lib_path))
                    break
                except OSError:
                    continue
            # Also check subdirectories or bundle folders
            for sub in ["", "bin", "lib", "OpenAL"]:
                path = d / sub / name
                if path.exists():
                    try:
                        _lib = ctypes.CDLL(str(path))
                        break
                    except OSError:
                        continue
            if _lib is not None:
                break
        if _lib is not None:
            break

# Function prototypes if library loaded successfully
if _lib is not None:
    # alcOpenDevice
    _lib.alcOpenDevice.argtypes = [ctypes.c_char_p]
    _lib.alcOpenDevice.restype = ALCdevice_p

    # alcCloseDevice
    _lib.alcCloseDevice.argtypes = [ALCdevice_p]
    _lib.alcCloseDevice.restype = ctypes.c_bool

    # alcCreateContext
    _lib.alcCreateContext.argtypes = [ALCdevice_p, ctypes.POINTER(ALint)]
    _lib.alcCreateContext.restype = ALCcontext_p

    # alcMakeContextCurrent
    _lib.alcMakeContextCurrent.argtypes = [ALCcontext_p]
    _lib.alcMakeContextCurrent.restype = ctypes.c_bool

    # alcDestroyContext
    _lib.alcDestroyContext.argtypes = [ALCcontext_p]
    _lib.alcDestroyContext.restype = None

    # alGenBuffers
    _lib.alGenBuffers.argtypes = [ALsizei, ctypes.POINTER(ALuint)]
    _lib.alGenBuffers.restype = None

    # alDeleteBuffers
    _lib.alDeleteBuffers.argtypes = [ALsizei, ctypes.POINTER(ALuint)]
    _lib.alDeleteBuffers.restype = None

    # alBufferData
    _lib.alBufferData.argtypes = [ALuint, ALenum, ctypes.c_void_p, ALsizei, ALsizei]
    _lib.alBufferData.restype = None

    # alGenSources
    _lib.alGenSources.argtypes = [ALsizei, ctypes.POINTER(ALuint)]
    _lib.alGenSources.restype = None

    # alDeleteSources
    _lib.alDeleteSources.argtypes = [ALsizei, ctypes.POINTER(ALuint)]
    _lib.alDeleteSources.restype = None

    # alSourcePlay
    _lib.alSourcePlay.argtypes = [ALuint]
    _lib.alSourcePlay.restype = None

    # alSourceStop
    _lib.alSourceStop.argtypes = [ALuint]
    _lib.alSourceStop.restype = None

    # alSource3f
    _lib.alSource3f.argtypes = [ALuint, ALenum, ALfloat, ALfloat, ALfloat]
    _lib.alSource3f.restype = None

    # alSourcef
    _lib.alSourcef.argtypes = [ALuint, ALenum, ALfloat]
    _lib.alSourcef.restype = None

    # alSourcei
    _lib.alSourcei.argtypes = [ALuint, ALenum, ALint]
    _lib.alSourcei.restype = None

    # alListener3f
    _lib.alListener3f.argtypes = [ALenum, ALfloat, ALfloat, ALfloat]
    _lib.alListener3f.restype = None

    # alListenerfv
    _lib.alListenerfv.argtypes = [ALenum, ctypes.POINTER(ALfloat)]
    _lib.alListenerfv.restype = None

    # alGetError
    _lib.alGetError.argtypes = []
    _lib.alGetError.restype = ALenum

    # alDistanceModel
    _lib.alDistanceModel.argtypes = [ALenum]
    _lib.alDistanceModel.restype = None

    # alDopplerFactor
    _lib.alDopplerFactor.argtypes = [ALfloat]
    _lib.alDopplerFactor.restype = None

    # alGetSourcei
    _lib.alGetSourcei.argtypes = [ALuint, ALenum, ctypes.POINTER(ALint)]
    _lib.alGetSourcei.restype = None

    # alcGetString
    _lib.alcGetString.argtypes = [ALCdevice_p, ALenum]
    _lib.alcGetString.restype = ctypes.c_void_p

    # alGetString
    _lib.alGetString.argtypes = [ALenum]
    _lib.alGetString.restype = ctypes.c_char_p


def open_device(devicename: Optional[str] = None) -> Optional[int]:
    """Open an OpenAL audio device.

    OpenAL Soft may be installed while no real playback device is available
    (CI, Docker, remote servers, or lab machines without ALSA/Pulse/PipeWire).
    In that case EchoRunner enters a silent fallback mode: OpenAL calls keep the
    same lifecycle semantics, tests and telemetry continue to run, but no sound
    is emitted. Real desktop players still get the real OpenAL device whenever
    one is available.
    """
    global _fallback_mode
    if _lib is None:
        raise RuntimeError("OpenAL Soft library not loaded. Ensure OpenAL is installed.")
    name_bytes = devicename.encode("utf-8") if devicename else None
    device = _lib.alcOpenDevice(name_bytes)
    if device:
        _fallback_mode = False
        return device

    _fallback_mode = True
    return _FAKE_DEVICE


def close_device(device: int) -> bool:
    """Close the specified OpenAL device."""
    global _fallback_mode
    if _fallback_mode and device == _FAKE_DEVICE:
        _fallback_mode = False
        return True
    if _lib is None:
        return False
    return bool(_lib.alcCloseDevice(device))


def create_context(device: int) -> Optional[int]:
    """Create an OpenAL context and make it current."""
    if _fallback_mode and device == _FAKE_DEVICE:
        return _FAKE_CONTEXT
    if _lib is None:
        return None
    context = _lib.alcCreateContext(device, None)
    if context:
        _lib.alcMakeContextCurrent(context)
        return context
    return None


def destroy_context(context: int) -> None:
    """Destroy the specified OpenAL context after making none current."""
    if _fallback_mode and context == _FAKE_CONTEXT:
        return
    if _lib is not None:
        _lib.alcMakeContextCurrent(None)
        _lib.alcDestroyContext(context)


def gen_buffers(n: int) -> list[int]:
    """Generate n audio buffer names."""
    global _next_buffer_id
    if _fallback_mode:
        ids = list(range(_next_buffer_id, _next_buffer_id + n))
        _next_buffer_id += n
        return ids
    if _lib is None:
        return []
    buffers = (ALuint * n)()
    _lib.alGenBuffers(n, buffers)
    return list(buffers)


def delete_buffers(buffers: list[int]) -> None:
    """Delete a list of audio buffer names."""
    if _fallback_mode:
        return
    if _lib is not None and buffers:
        n = len(buffers)
        bufs = (ALuint * n)(*buffers)
        _lib.alDeleteBuffers(n, bufs)


def buffer_data(buffer: int, format: int, data: bytes, freq: int) -> None:
    """Fill a buffer with audio data."""
    if _fallback_mode or _lib is None:
        return
    size = len(data)
    data_p = ctypes.cast(ctypes.create_string_buffer(data, size), ctypes.c_void_p)
    _lib.alBufferData(buffer, format, data_p, size, freq)


def gen_sources(n: int) -> list[int]:
    """Generate n sound source names."""
    global _next_source_id
    if _fallback_mode:
        ids = list(range(_next_source_id, _next_source_id + n))
        _next_source_id += n
        for source_id in ids:
            _fake_source_states[source_id] = AL_INITIAL
        return ids
    if _lib is None:
        return []
    sources = (ALuint * n)()
    _lib.alGenSources(n, sources)
    return list(sources)


def delete_sources(sources: list[int]) -> None:
    """Delete a list of sound source names."""
    if _fallback_mode:
        for source_id in sources:
            _fake_source_states.pop(source_id, None)
        return
    if _lib is not None and sources:
        n = len(sources)
        srcs = (ALuint * n)(*sources)
        _lib.alDeleteSources(n, srcs)


def source_play(source: int) -> None:
    """Start playing the source."""
    if _fallback_mode:
        _fake_source_states[source] = AL_PLAYING
        return
    if _lib is not None:
        _lib.alSourcePlay(source)


def source_stop(source: int) -> None:
    """Stop playing the source."""
    if _fallback_mode:
        _fake_source_states[source] = AL_STOPPED
        return
    if _lib is not None:
        _lib.alSourceStop(source)


def source_set_position(source: int, position: tuple[float, float, float]) -> None:
    """Set the 3D position of a source."""
    if _fallback_mode:
        return
    if _lib is not None:
        _lib.alSource3f(source, AL_POSITION, position[0], position[1], position[2])


def source_set_gain(source: int, gain: float) -> None:
    """Set the gain (volume) of a source."""
    if _fallback_mode:
        return
    if _lib is not None:
        _lib.alSourcef(source, AL_GAIN, gain)


def source_set_pitch(source: int, pitch: float) -> None:
    """Set the pitch of a source."""
    if _fallback_mode:
        return
    if _lib is not None:
        _lib.alSourcef(source, AL_PITCH, pitch)


def source_set_looping(source: int, looping: bool) -> None:
    """Set whether the source loops automatically."""
    if _fallback_mode:
        return
    if _lib is not None:
        _lib.alSourcei(source, AL_LOOPING, 1 if looping else 0)


def source_set_relative(source: int, relative: bool) -> None:
    """Set whether source coordinates are listener-relative."""
    if _fallback_mode:
        return
    if _lib is not None:
        _lib.alSourcei(source, AL_SOURCE_RELATIVE, 1 if relative else 0)


def source_set_buffer(source: int, buffer: int) -> None:
    """Bind a buffer to a source."""
    if _fallback_mode:
        return
    if _lib is not None:
        # AL_BUFFER is 0x1009
        _lib.alSourcei(source, 0x1009, buffer)


def source_set_distance_params(
    source: int, reference_dist: float, max_dist: float, rolloff: float
) -> None:
    """Set distance attenuation parameters on a source."""
    if _fallback_mode:
        return
    if _lib is not None:
        _lib.alSourcef(source, AL_REFERENCE_DISTANCE, reference_dist)
        _lib.alSourcef(source, AL_MAX_DISTANCE, max_dist)
        _lib.alSourcef(source, AL_ROLLOFF_FACTOR, rolloff)


def listener_set_position(position: tuple[float, float, float]) -> None:
    """Set the 3D position of the listener."""
    if _fallback_mode:
        return
    if _lib is not None:
        _lib.alListener3f(AL_POSITION, position[0], position[1], position[2])


def listener_set_orientation(at: tuple[float, float, float], up: tuple[float, float, float]) -> None:
    """Set the orientation of the listener (at and up vectors)."""
    if _fallback_mode:
        return
    if _lib is not None:
        vals = (ALfloat * 6)(at[0], at[1], at[2], up[0], up[1], up[2])
        _lib.alListenerfv(AL_ORIENTATION, vals)


def get_error() -> int:
    """Get the current OpenAL error code."""
    if _fallback_mode:
        return AL_NO_ERROR
    if _lib is not None:
        return int(_lib.alGetError())
    return AL_NO_ERROR


def distance_model(model: int) -> None:
    """Set the distance attenuation model."""
    if _fallback_mode:
        return
    if _lib is not None:
        _lib.alDistanceModel(model)


def doppler_factor(factor: float) -> None:
    """Set the global Doppler factor."""
    if _fallback_mode:
        return
    if _lib is not None:
        _lib.alDopplerFactor(factor)


def source_get_state(source: int) -> int:
    """Get the play state of a source (e.g., AL_PLAYING, AL_STOPPED)."""
    if _fallback_mode:
        return _fake_source_states.get(source, AL_STOPPED)
    if _lib is not None:
        val = ALint(0)
        _lib.alGetSourcei(source, AL_SOURCE_STATE, ctypes.byref(val))
        return val.value
    return AL_STOPPED


def alc_get_string(device: Optional[int], param: int) -> str | None:
    """Gets an ALC string specifier."""
    if _fallback_mode:
        if param == ALC_DEFAULT_DEVICE_SPECIFIER:
            return "EchoRunner Silent Fallback Device"
        if param == ALC_DEVICE_SPECIFIER:
            return "EchoRunner Silent Fallback Device"
    if _lib is None:
        return None
    res = _lib.alcGetString(device, param)
    if not res:
        return None
    return ctypes.cast(res, ctypes.c_char_p).value.decode("utf-8", errors="replace")


def al_get_string(param: int) -> str | None:
    """Gets an AL string specifier."""
    if _fallback_mode:
        if param == AL_VENDOR:
            return "EchoRunner"
        if param == AL_VERSION:
            return "silent-fallback"
        if param == AL_RENDERER:
            return "No audio device available"
    if _lib is None:
        return None
    res = _lib.alGetString(param)
    return res.decode("utf-8", errors="replace") if res else None


def get_device_list(device: Optional[int]) -> list[str]:
    """Retrieves all available OpenAL playback devices specifiers."""
    if _fallback_mode:
        return ["EchoRunner Silent Fallback Device"]
    if _lib is None:
        return []
    res_ptr = _lib.alcGetString(device, ALC_DEVICE_SPECIFIER)
    if not res_ptr:
        return []

    char_ptr = ctypes.cast(res_ptr, ctypes.POINTER(ctypes.c_char))
    devices = []
    current = []
    i = 0
    while True:
        val = char_ptr[i]
        if val == b'\x00':
            if not current:
                break
            devices.append(b"".join(current).decode("utf-8", errors="replace"))
            current = []
            if char_ptr[i + 1] == b'\x00':
                break
        else:
            current.append(val)
        i += 1
    return devices

