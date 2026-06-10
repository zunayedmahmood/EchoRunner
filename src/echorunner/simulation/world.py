"""Deterministic simulation structures for EchoRunner."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Vec2:
    x: int
    y: int


@dataclass
class PlayerState:
    tile: Vec2
    direction: str = "right"
    queued_direction: str | None = None


@dataclass
class EnemyState:
    enemy_id: str
    archetype: str
    tile: Vec2
    direction: str
    state: str = "patrol"
    threat: str = "silent"
