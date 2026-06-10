# EchoRunner Visual Asset Library and Trainer UI

> Source alignment: This workplan updates the previous Sound-Maze package into **EchoRunner**, a Python + Pygame game with OpenAL spatial audio. It follows the blind-first design doctrine from the supplied Sound-Maze plan, the local-first/accessibility/research workflow from the HCI toolkit guide, and the OpenAL device/context/buffer/source/listener model from the OpenAL Programmer's Guide.

## 1. Role of visual assets

EchoRunner must be playable without vision. Visual assets support:

- trainer dashboard;
- low-vision mode;
- debugging;
- screenshots and communication;
- level editor preview;
- HCI research observation.

Do not use visuals to communicate any state that is not also available through sound or speech.

## 2. Asset library structure

The package includes:

```text
assetLibrary/
├── sprites/
│   ├── png/
│   └── svg/
├── tiles/
│   ├── png/
│   └── svg/
├── backgrounds/
├── ui/
├── atlases/
├── title/
├── manifest.json
└── README.md
```

## 3. Required asset categories

### Player

- `player_echo_runner.png`
- `player_echorunner.png` alias recommended
- high contrast outline;
- visible orientation arrow for trainer.

### Enemies

- `enemy_hunter.png`
- `enemy_ambusher.png`
- `enemy_trickster.png`
- `enemy_coward.png`

Each enemy should have a unique shape and color, but audio identity is more important than visual identity.

### Collectibles

- `pellet_echo_orb.png`
- `power_resonance_core.png`
- `fruit_signal_gem.png`

### Tiles

- wall;
- corridor;
- pellet;
- junction;
- power;
- fruit route;
- enemy gate;
- safe pocket;
- warp;
- unknown/unexplored.

### UI icons

- scan;
- repeat;
- headphones;
- mono;
- keyboard;
- volume;
- danger;
- replay;
- trainer marker;
- audio calibration.

## 4. Trainer dashboard requirements

The trainer dashboard should show:

```text
maze grid
player position and facing direction
enemy positions and states
current top audio cue
recent cue history
threat classification
remaining orbs
power timer
lives
scan result
coaching prompt
telemetry recording status
```

Trainer dashboard mock layout:

```text
+---------------------------------------------------+
| EchoRunner Trainer Dashboard                      |
| Level: Training Loop  Cue: enemy_near_amber       |
+------------------------+--------------------------+
|                        | Player                   |
|        Maze View       | lives: 3                 |
|                        | direction: east          |
|                        | remaining orbs: 24       |
+------------------------+--------------------------+
| Audio Now: right amber threat                     |
| Last scan: left pellets, forward danger           |
| Coach prompt: Ask what the player hears first.    |
+---------------------------------------------------+
```

## 5. Trainer ethics

The trainer should not simply give answers.

Use prompts:

```text
Ask: What did you hear?
Ask: Which direction sounded safe?
Ask: Do you want to scan?
```

Avoid prompts:

```text
Go left now.
Enemy is exactly at row 4 column 6.
Take the hidden route.
```

The trainer view should help teaching, not replace player skill.

## 6. Low-vision visual requirements

For low-vision players:

- high contrast mode;
- scalable UI;
- large text;
- no tiny icons as sole indicators;
- no information by color alone;
- optional reduced motion;
- clear focus outline.

## 7. Asset naming rules

Use stable snake_case names.

Good:

```text
power_resonance_core.png
enemy_hunter_alert.png
icon_audio_calibration.png
```

Bad:

```text
final2.png
new_enemy_blue_REAL.png
pacman_like_sprite.png
```

## 8. Legal originality

Do not use Pac-Man names, ghosts, maze layouts, sounds, sprites, fonts, branding, or copied level designs. EchoRunner must have original characters, original audio, original maps, and original branding.

## 9. Asset implementation checklist

- [x] Every asset has PNG and source SVG where possible.
- [x] Manifest lists asset id, path, category, dimensions, and purpose.
- [x] Trainer view can load every required asset.
- [x] Missing asset fallback exists.
- [x] High-contrast mode is supported.
- [x] Visual asset has audio equivalent.

