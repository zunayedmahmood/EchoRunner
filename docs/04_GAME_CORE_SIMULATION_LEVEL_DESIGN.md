# EchoRunner Game Core, Simulation, and Level Design

> Source alignment: This workplan updates the previous Sound-Maze package into **EchoRunner**, a Python + Pygame game with OpenAL spatial audio. It follows the blind-first design doctrine from the supplied Sound-Maze plan, the local-first/accessibility/research workflow from the HCI toolkit guide, and the OpenAL device/context/buffer/source/listener model from the OpenAL Programmer's Guide.

## 1. Core loop

EchoRunner's gameplay loop is:

```text
Listen → infer → choose direction → move → collect → avoid/lure enemies → scan when uncertain → clear level
```

The visual grid is a data structure. The player experiences it as a sequence of sounds and decisions.

## 2. Simulation principles

The simulation must be deterministic and independent from Pygame rendering and OpenAL playback.

Implementation target:

```python
class GameSimulation:
    def step(self, dt: float, commands: list[Command]) -> SimulationFrame:
        ...
```

`SimulationFrame` should include:

```text
player position and direction
enemy positions, directions, and states
collected orb count
remaining orb count
power timer
open directions at current tile
threat model results
events emitted this frame
```

## 3. Coordinate system

Use grid coordinates for logic:

```text
x increases east/right
y increases south/down
```

Convert to OpenAL coordinates:

```text
OpenAL X = grid x
OpenAL Y = 0
OpenAL Z = grid y
```

For listener orientation:

```text
UP/NORTH    at = (0, 0, -1)
DOWN/SOUTH  at = (0, 0, 1)
LEFT/WEST   at = (-1, 0, 0)
RIGHT/EAST  at = (1, 0, 0)
up vector   up = (0, 1, 0)
```

This orientation makes enemy sounds relative to the player's current facing direction.

## 4. Tile grammar

Do not think in pixels. Think in meaningful tiles.

| Tile | Meaning | Audio requirement |
|---|---|---|
| `wall` | Blocks movement | Wall knock on attempted movement; subtle boundary scan |
| `corridor` | Movement path | Movement rhythm and directional continuity |
| `echo_orb` | Main collectible | Soft tick; pitch/rhythm progress variation |
| `junction` | Decision point | Directional open-path cues and scan support |
| `resonance_core` | Power item | Distinct cue before pickup; transformation on collect |
| `enemy_gate` | Enemy origin/return zone | Landmark sound, not a sudden spawn |
| `safe_reorient` | Small recovery pocket | Calm landmark tone and optional reorientation speech |
| `warp` | Shortcut | Entry and exit transition cues |
| `dead_end` | Risk area | Warning texture before trap is introduced |

## 5. Player movement

### 5.1 Movement tick

The player moves one tile per movement interval. Movement speed may increase by level, but beginner levels should remain slow enough for audio comprehension.

Suggested values:

```text
Tutorial: 2.5 tiles/sec
Level 1: 3.0 tiles/sec
Level 2: 3.2 tiles/sec
Level 3: 3.4 tiles/sec
Expert: 3.8–4.2 tiles/sec
```

### 5.2 Queued direction

Input must allow early turns.

```python
if command in movement_commands:
    player.queued_direction = command.direction

if at_tile_center and can_move(player.queued_direction):
    player.direction = player.queued_direction
```

### 5.3 Wall collision

Wall collision should not punish harshly. It should teach.

```text
First wall attempt: wall knock.
Repeated wall attempts: spoken hint in tutorial or beginner mode.
```

## 6. Collectibles

### 6.1 Echo orbs

Echo orbs are the core objective. Audio should make progress satisfying but not exhausting.

Rules:

- play `pellet_tick.wav` when collected;
- raise pitch slightly for consecutive orbs;
- play `pellet_row_clear.wav` when a route segment is cleared;
- provide remaining count only on scan/help, not constantly.

### 6.2 Resonance cores

Resonance cores are power items. They should be placed where reaching them under pressure is meaningful.

Rules:

- cue when nearby;
- activation changes enemy state;
- countdown warns before expiry;
- expiration is unmistakable.

### 6.3 Bonus signals

Optional fruit/bonus equivalents should be original. Call them `signal gems`.

They should lure route risk:

```text
safe path = lower points
risky path = signal gem points
```

## 7. Enemy system

Each enemy has:

```text
id
archetype
position
direction
state
speed
home tile
target logic
audio identity
```

Enemy states:

```text
PATROL / SCATTER
HUNT / CHASE
FRIGHTENED
RETURN_HOME
STUNNED optional
```

Every state transition must emit an audio event.

## 8. Enemy archetypes

### Hunter

Directly pressures the player's current route.

Audio identity:

```text
low pulsing thump, stronger when aligned with player corridor
```

### Ambusher

Targets a tile ahead of the player's current direction.

Audio identity:

```text
sharp forward-leaning pulse, warns before junction traps
```

### Trickster

Uses blended targets or random route shifts.

Audio identity:

```text
warbling tone, never too loud unless high threat
```

### Coward / Guard

Moves toward player when far, retreats or guards routes when near.

Audio identity:

```text
soft oscillating tone; becomes clearer near power items or gates
```

## 9. Threat model

Do not simply sort enemies by Euclidean distance.

Threat calculation should consider:

- route distance through the maze;
- enemy direction;
- player direction;
- enemy speed;
- blocked walls;
- power mode;
- whether the enemy is on an intercept path;
- whether player has a safe turn before collision.

Pseudo-code:

```python
def classify_threat(player, enemy, level):
    route_distance = shortest_path_distance(enemy.tile, player.tile, level.walkable_tiles)
    same_corridor = line_of_sight_corridor(enemy.tile, player.tile, level)
    intercept_time = estimate_intercept_time(player, enemy, level)

    if enemy.state == FRIGHTENED:
        return "frightened"
    if same_corridor and intercept_time < 1.4:
        return "red"
    if intercept_time < 3.0:
        return "amber"
    if route_distance <= 6:
        return "green"
    return "silent"
```

## 10. Level design ladder

| Level | Lesson | New pressure variable |
|---|---|---|
| Tutorial 1 | walls and movement | none |
| Tutorial 2 | junctions | branch choice |
| Tutorial 3 | pellets | collection progress |
| Tutorial 4 | enemy warning | one slow enemy |
| Tutorial 5 | power mode | temporary reversal |
| Level 1 | full basic loop | safe enemy speed |
| Level 2 | crossroad planning | central hub route choices |
| Level 3 | power route | risky reward path |
| Level 4 | double loop | enemy pressure on alternate routes |
| Level 5 | speed | faster movement clock |
| Level 6 | multi-enemy | second relevant enemy cue |
| Expert | silence discipline | lower cue density |

## 11. Level file checklist

Each level JSON must define:

- unique level id;
- name;
- grid;
- legend;
- player start;
- enemy starts;
- total collectibles;
- audio landmarks;
- tutorial triggers if any;
- intended lesson;
- difficulty variables;
- cue density defaults;
- fairness notes;
- trainer notes.

## 12. Fairness rules

A level is unfair if:

- an enemy appears silently near the player;
- a dead end has no audio identity;
- power mode expires without warning;
- exact visual timing is required for turns;
- scan gives too much speech during danger;
- the trainer view contains information the player could never request through sound.

A level is fair when:

- danger is predictable and avoidable;
- losses produce a useful explanation;
- repeated play improves mental mapping;
- audio-only playthrough succeeds.

## 13. Bot testing

Create non-player test bots:

1. **Wall Hugger Bot** — tries to clear maze by always turning left.
2. **Random Bot** — randomly picks legal turns; useful for crash testing.
3. **Safe Scan Bot** — scans at each junction and avoids red/amber threats.
4. **Perfect Bot** — shortest path route with known enemy positions.

Use bots to detect impossible levels, unfair spawn points, and unreachable orbs.

## 14. Required simulation tests

```text
player cannot pass through walls
queued turn executes at junction
pellets are collected once only
level clear occurs when all orbs collected
power mode changes enemy state
power countdown emits warning events
enemy collision creates death cause
red threat outranks pellet cue
replay log can reconstruct a session
```
