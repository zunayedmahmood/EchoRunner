# EchoRunner Audio Grammar, Cue System, and Sound Library

> Source alignment: This workplan updates the previous Sound-Maze package into **EchoRunner**, a Python + Pygame game with OpenAL spatial audio. It follows the blind-first design doctrine from the supplied Sound-Maze plan, the local-first/accessibility/research workflow from the HCI toolkit guide, and the OpenAL device/context/buffer/source/listener model from the OpenAL Programmer's Guide.

## 1. Audio design objective

EchoRunner's audio system must help the player make decisions in real time. The game should not speak paragraphs during action. It should use compact sound grammar:

```text
earcons + spatial position + rhythm + pitch + short speech on request
```

## 2. Information ranges

| Range | Purpose | Cue types |
|---|---|---|
| Immediate tile | confirm movement/collision | step tick, wall knock, orb tick |
| Near field | support reaction | enemy panning, junction cues, power nearby |
| Far field | support planning | requested scan speech, landmark hum, route summary |
| Global state | mode awareness | power active, power ending, level clear, pause |

## 3. Audio priority funnel

```text
1. Collision/life lost
2. Red threat
3. Power ending
4. Amber threat
5. Player-requested scan
6. Junction/open route
7. Pellet/reward
8. Landmark/ambience/music
```

This priority must be implemented in `CuePlanner` and `OpenALBackend`.

## 4. Cue families

### 4.1 Movement and walls

| Cue | File | Meaning |
|---|---|---|
| move step | `move_step_soft.wav` | player moved one tile |
| wall knock | `wall_knock.wav` | blocked by wall |
| turn accepted | `turn_accepted_left/right/up/down.wav` | queued turn executed |

### 4.2 Collectibles

| Cue | File | Meaning |
|---|---|---|
| orb tick | `pellet_tick.wav` | echo orb collected |
| row clear | `pellet_row_clear.wav` | route segment cleared |
| combo | `combo_tick.wav` | repeated collection rhythm |
| signal gem | `fruit_collect.wav` | bonus collected |

### 4.3 Junction and route

| Cue | File | Meaning |
|---|---|---|
| open left | `junction_open_left.wav` | left path available |
| open right | `junction_open_right.wav` | right path available |
| open up/forward | `junction_open_up.wav` | forward/north path available |
| open down/back | `junction_open_down.wav` | back/south path available |
| scan start | `scan_start.wav` | player requested scan |
| scan success | `scan_success.wav` | scan summary ready |

### 4.4 Enemy threat

| Cue | File | Meaning |
|---|---|---|
| green | `enemy_near_green.wav` | enemy nearby but not urgent |
| amber | `enemy_near_amber.wav` | danger soon |
| red | `enemy_near_red.wav` | turn/escape immediately |
| frightened | `enemy_frightened.wav` | enemy vulnerable during power mode |

### 4.5 Power mode

| Cue | File | Meaning |
|---|---|---|
| power near | `power_near.wav` | resonance core nearby |
| activate | `power_activate.wav` | power mode starts |
| countdown | `power_countdown.wav` | power ending soon |
| expire | `power_expire.wav` | danger returns |

### 4.6 Speech

Generated speech files are now included in:

```text
soundLibrary/speech/en/wav/
soundLibrary/speech/bn/wav/
```

These are machine-generated placeholder speech files for implementation and testing. Replace with human-recorded or high-quality TTS later if needed.

## 5. Speech asset categories

| Category | Examples |
|---|---|
| first launch | `first_launch_en.wav`, `first_launch_bn.wav` |
| goal | `game_goal_en.wav`, `game_goal_bn.wav` |
| controls | `controls_full_en.wav`, `controls_full_bn.wav` |
| calibration | `audio_calibration_intro_en.wav`, `headphone_confirm_en.wav` |
| tutorial | `tutorial_walls_en.wav`, `tutorial_enemy_en.wav`, etc. |
| menu | `main_menu_intro_en.wav`, `pause_menu_en.wav` |
| scan | `scan_help_en.wav`, `scan_example_en.wav` |
| death | `death_hunter_left_en.wav`, `death_scan_tip_en.wav` |
| settings | `settings_cue_density_en.wav`, `mono_mode_en.wav` |

## 6. Speech rules

- Speech should be short.
- Gameplay speech should be player-requested when possible.
- Urgent cues interrupt speech.
- Menu speech can be longer.
- Tutorial speech can be replayed.
- Scan speech should summarize decisions, not read the whole grid.

Bad scan:

```text
"Tile one wall, tile two wall, tile three pellet..."
```

Good scan:

```text
"Left has pellets. Forward has danger far. Right is blocked. Back returns to safe loop."
```

## 7. Spatialization rules

Use spatial sources for:

- enemies;
- nearby power cores;
- landmarks;
- route cues;
- collision direction;
- signal gems.

Use listener-relative sources for:

- speech;
- menus;
- global confirmation;
- level clear;
- study prompts.

## 8. Direction encoding

For headphone mode:

```text
left/right: OpenAL panning from source position
front/back: listener orientation + optional pitch/rhythm reinforcement
near/far: gain + rolloff + repetition rate
```

For mono mode:

```text
left: two short ticks
right: three short ticks
forward: higher pitch
back: lower pitch
near: faster repetition
far: slower repetition
```

## 9. Threat sound design

Threat cues should be emotionally readable:

```text
Green: soft, lower urgency, does not mask navigation.
Amber: medium pulse, warns route planning.
Red: sharp urgent cue, ducks other audio.
```

Red must never be subtle.

## 10. Enemy identity loops

Enemy loops should be distinct but not constantly loud.

| Enemy | Sound identity | Mixing rule |
|---|---|---|
| Hunter | low pulse | full volume only when top threat |
| Ambusher | sharp ticking pulse | emphasize at junction traps |
| Trickster | warble | quieter unless near |
| Coward/Guard | soft oscillation | cue when blocking power or escape |

Only the top one or two enemies should be actively emphasized. Others can appear in scan summaries.

## 11. Asset loudness targets

Suggested initial targets:

```text
speech: clear, normalized around -18 LUFS equivalent if processed later
red warning: slightly louder than normal cues, but not painful
pellet: quiet and short
menu: soft and non-fatiguing
enemy loops: low until threat rises
```

Avoid sudden loud sounds. Provide sudden-sound reduction mode.

## 12. Manifest-driven audio

Do not hardcode file paths inside gameplay.

Use manifest:

```json
{
  "cue_id": "enemy_near_red",
  "path": "soundLibrary/wav/enemy_near_red.wav",
  "spatial": true,
  "priority": 100,
  "category": "threat"
}
```

The generated package includes updated manifests.

## 13. Audio QA checklist

For every cue:

- file exists;
- WAV is readable;
- mono/stereo status is known;
- category is correct;
- priority is correct;
- spatial flag is correct;
- speech transcript exists;
- cue is not too long for gameplay;
- urgent cue masks/ducks lower priority cues.

## 14. Replacement plan for final production assets

The generated audio library is a prototype. For release:

1. Keep file names stable.
2. Replace WAV content with professional audio.
3. Re-run audio manifest validator.
4. Re-run blind playtest.
5. Re-tune OpenAL gain/rolloff.
6. Do not change cue meaning without updating tutorial speech.
