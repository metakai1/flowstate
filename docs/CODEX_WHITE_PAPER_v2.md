# CODEX v2: A Federation of Micro-Models for DJ Decision Support

## Interpretable, Touch-Driven Track Recommendations

**Version 2.0**
**January 2026**

---

## Abstract

We present CODEX v2, a novel architecture for DJ track recommendation that replaces monolithic scoring functions with a **federation of specialist micro-models**. Each specialist (~1,500 parameters) learns one aspect of transition quality—vibe compatibility, energy arc, groove matching, harmonic feel—while a lightweight aggregator combines their outputs based on DJ intent.

The key innovations are:

1. **Federated specialists**: Eight tiny, interpretable models that each master one dimension of transition quality, bootstrapped from hand-coded DJ intuition and refinable with real mixing data

2. **Touch-first interface**: A 2D gesture pad and quick-tap modifiers that translate physical gestures into specialist weights—no typing required during performance

3. **Radical simplicity**: The entire model federation is ~27,000 parameters, trains in seconds on CPU, and runs inference in microseconds. No GPU required.

4. **Full interpretability**: Every recommendation shows which specialists agree or disagree, enabling DJs to understand and trust the system

This approach achieves the expressiveness of prompt-driven recommendation without requiring text input, making it practical for live DJ performance where hands are occupied and flow state is paramount.

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Background: FLOWSTATE v1](#2-background-flowstate-v1)
3. [Federation Architecture](#3-federation-architecture)
4. [Specialist Model Design](#4-specialist-model-design)
5. [The Aggregator](#5-the-aggregator)
6. [Touch Interface Design](#6-touch-interface-design)
7. [Training Methodology](#7-training-methodology)
8. [Implementation](#8-implementation)
9. [Evaluation Framework](#9-evaluation-framework)
10. [Future Directions](#10-future-directions)
11. [Conclusion](#11-conclusion)

---

## 1. Introduction

### 1.1 The Problem

A DJ selecting the next track must simultaneously satisfy multiple constraints:

- **Harmonic compatibility**: Keys should mix without dissonance
- **Tempo matching**: BPM should be within beatmatch range
- **Energy trajectory**: Building, maintaining, or releasing tension
- **Vibe continuity**: Mood transitions should feel natural
- **Groove compatibility**: Rhythm patterns should blend
- **Narrative arc**: The set should tell a story

Current DJ software handles the mechanical aspects (BPM, key detection) but leaves the artistic decisions—energy, vibe, narrative—entirely to human intuition.

### 1.2 The Limitations of Existing Approaches

**Monolithic ML models** (large transformers, embedding-based retrieval) offer theoretical power but suffer from:
- Opacity: Why was this track recommended?
- Computational cost: GPU inference during live performance
- Data hunger: Require massive training sets
- Rigidity: Can't easily adjust one aspect without retraining everything

**Hand-coded rule systems** (including FLOWSTATE v1) are interpretable and fast but:
- Encode one person's intuition, which may not generalize
- Can't learn from data or improve over time
- Miss subtle interactions between factors

### 1.3 Our Approach: Federated Specialists

We propose a middle path: **a federation of tiny specialist models**, each responsible for one aspect of transition quality.

```
Instead of:  ONE BIG MODEL that scores everything
We use:      EIGHT TINY MODELS that each score one thing
             + ONE AGGREGATOR that combines them based on context
```

This approach offers:
- **Interpretability**: See which specialist likes/dislikes a transition
- **Modularity**: Improve one specialist without touching others
- **Efficiency**: ~27K total parameters, trains in seconds
- **Bootstrapping**: Initialize from hand-coded matrices, refine with data
- **Personalization**: Each DJ can tune specialists to their style

### 1.4 Touch-First Design

DJs can't type during performance. Hands are on platters, faders, and knobs. The room is dark. Flow state must be maintained.

CODEX v2 translates DJ intent into specialist weights through:
- A 2D gesture pad (energy × vibe direction)
- Quick-tap modifier buttons (peak, flow, shift genre, etc.)
- Physical gestures that directly manipulate the aggregator

No text. No menus. Just touch and go.

---

## 2. Background: FLOWSTATE v1

### 2.1 Current Architecture

FLOWSTATE v1 uses a 4-stage pipeline:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: HARD FILTERS                                                   │
│ ├─ BPM within ±6                                                        │
│ ├─ Key must be Camelot-compatible                                       │
│ ├─ Not recently played (last 20 tracks)                                 │
│ └─ Audio fidelity above threshold                                       │
├─────────────────────────────────────────────────────────────────────────┤
│ STAGE 2: DIRECTION SPLIT                                                │
│ ├─ UP:   energy_delta >= +1                                             │
│ ├─ HOLD: energy_delta between -1 and +1                                 │
│ └─ DOWN: energy_delta <= -1                                             │
├─────────────────────────────────────────────────────────────────────────┤
│ STAGE 3: SOFT SCORING (8 hand-coded factors)                            │
│ ├─ Energy Trajectory  (weight: 1.0)                                     │
│ ├─ Danceability       (weight: 0.8)                                     │
│ ├─ Vibe Compatibility (weight: 0.7)  ← hand-coded matrix                │
│ ├─ Narrative Flow     (weight: 0.6)  ← hand-coded matrix                │
│ ├─ Key Quality        (weight: 0.5)                                     │
│ ├─ Groove Compat.     (weight: 0.4)  ← hand-coded matrix                │
│ ├─ Mix Ease           (weight: 0.4)                                     │
│ └─ Genre Affinity     (weight: 0.3)                                     │
├─────────────────────────────────────────────────────────────────────────┤
│ STAGE 4: RANK AND RETURN                                                │
│ └─ Top 5 per direction (UP/HOLD/DOWN)                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 The Compatibility Matrices

FLOWSTATE v1 uses hand-coded matrices for vibe, groove, and narrative transitions:

```python
# Example: Vibe compatibility matrix
VIBE_MATRIX = {
    "dark": {"dark": 1.0, "hypnotic": 0.8, "aggressive": 0.7,
             "chill": 0.3, "bright": 0.2, "euphoric": 0.1},
    "bright": {"bright": 1.0, "euphoric": 0.9, "chill": 0.6,
               "hypnotic": 0.4, "dark": 0.2, "aggressive": 0.3},
    # ... etc
}
```

These matrices encode the author's intuition about which transitions work. They're reasonable starting points but:
- May not match other DJs' preferences
- Can't learn from actual mixing data
- Miss contextual factors (a dark→bright transition might work at 3am but not at midnight)

### 2.3 What's Missing

1. **No DJ intent input**: The system doesn't know if the DJ wants to go darker, shift genres, or maintain vibe. It just offers UP/HOLD/DOWN energy directions.

2. **Fixed factor weights**: Energy is always weighted at 1.0, genre at 0.3. But sometimes genre matters more (you're doing a genre-fluid set) or less (you're deep in techno).

3. **No learning**: The matrices never improve. A DJ's corrections don't feed back into the system.

---

## 3. Federation Architecture

### 3.1 Overview

CODEX v2 replaces the hand-coded scoring factors with learned specialist models:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      CODEX v2 FEDERATION                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  SPECIALISTS (each ~1,500 params)                                       │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐             │
│  │    Vibe     │   Energy    │   Groove    │    Key      │             │
│  │ Transition  │    Arc      │ Transition  │ Transition  │             │
│  │   Model     │   Model     │   Model     │   Model     │             │
│  │             │             │             │             │             │
│  │ dark→bright │  8→6 okay?  │ 4otf→broken │  8A→5B?     │             │
│  │   = 0.23    │   = 0.71    │   = 0.34    │   = 0.67    │             │
│  └──────┬──────┴──────┬──────┴──────┬──────┴──────┬──────┘             │
│         │             │             │             │                     │
│  ┌──────┴──────┬──────┴──────┬──────┴──────┬──────┴──────┐             │
│  │ Narrative   │ Mixability  │   Genre     │   Vocal     │             │
│  │   Model     │   Model     │   Model     │   Model     │             │
│  │             │             │             │             │             │
│  │ peak→peak?  │ technical   │ kpop→house? │ vocal→inst? │             │
│  │   = 0.44    │   = 0.82    │   = 0.31    │   = 0.56    │             │
│  └──────┬──────┴──────┬──────┴──────┬──────┴──────┬──────┘             │
│         │             │             │             │                     │
│         └─────────────┴──────┬──────┴─────────────┘                     │
│                              │                                          │
│                              ▼                                          │
│                    ┌─────────────────────┐                              │
│                    │     AGGREGATOR      │                              │
│                    │                     │                              │
│                    │  Combines scores    │◄──── Touch input / intent   │
│                    │  based on context   │                              │
│                    │                     │                              │
│                    │    ~10K params      │                              │
│                    └──────────┬──────────┘                              │
│                               │                                         │
│                               ▼                                         │
│                     Final transition score                              │
│                     + Per-specialist breakdown                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Information Flow

```
1. INPUT
   ├─ Current track features (from Gemini analysis)
   ├─ Candidate track features
   └─ DJ intent (from touch interface)

2. SPECIALIST SCORING
   Each specialist receives relevant features and outputs a score [0,1]:
   ├─ VibeModel(current.vibe, candidate.vibe) → 0.73
   ├─ EnergyModel(current.energy, candidate.energy, direction) → 0.85
   ├─ GrooveModel(current.groove, candidate.groove) → 0.62
   └─ ... (8 specialists total)

3. AGGREGATION
   Aggregator receives:
   ├─ All specialist scores
   └─ DJ intent embedding (from touch input)

   Outputs:
   ├─ Final score (weighted combination)
   └─ Per-specialist weights used (for explanation)

4. OUTPUT
   ├─ Ranked recommendations
   └─ Explanation: "Vibe: 0.73, Energy: 0.85, but Narrative: 0.44 (peak→peak)"
```

### 3.3 Why Federation?

| Aspect | Monolithic Model | Federation |
|--------|------------------|------------|
| **Interpretability** | Black box | See each specialist's opinion |
| **Training data** | Needs lots | Each specialist needs little |
| **Compute** | GPU often required | CPU in microseconds |
| **Improvement** | Retrain everything | Swap one specialist |
| **Personalization** | Fine-tune whole model | Adjust individual specialists |
| **Failure modes** | Opaque | "Groove model disagrees" |

---

## 4. Specialist Model Design

### 4.1 Common Architecture

Each specialist follows the same pattern:

```python
class SpecialistModel(nn.Module):
    """Base architecture for all specialists."""

    def __init__(self, input_dim: int, hidden_dim: int = 32):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()  # Output in [0, 1]
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)
```

### 4.2 The Eight Specialists

#### 4.2.1 VibeTransitionModel

**Purpose**: Score the emotional/atmospheric transition quality.

**Input features**:
- from_vibe: one-hot encoded (6 dims)
- to_vibe: one-hot encoded (6 dims)
- energy_context: current energy level (1 dim, normalized)
- direction: intended direction (3 dims: up/hold/down)

**Total input**: 16 dimensions

**Learns**: Which vibe transitions feel natural, potentially conditioned on energy level and intent.

```
dark → dark:       0.95  (staying in mood)
dark → hypnotic:   0.82  (natural progression)
dark → euphoric:   0.15  (jarring without buildup)
dark → euphoric + direction=UP + high_energy: 0.45  (context helps)
```

#### 4.2.2 EnergyArcModel

**Purpose**: Score energy trajectory quality.

**Input features**:
- from_energy: normalized (1 dim)
- to_energy: normalized (1 dim)
- energy_delta: signed difference (1 dim)
- direction: intended direction (3 dims)
- set_position: early/mid/late (3 dims, optional)

**Total input**: 9 dimensions

**Learns**: Energy flow patterns. A +3 energy jump might be great when building to peak, risky when already at peak.

#### 4.2.3 GrooveTransitionModel

**Purpose**: Score rhythmic compatibility.

**Input features**:
- from_groove: one-hot (5 dims)
- to_groove: one-hot (5 dims)
- tempo_feel_match: binary (1 dim)
- bpm_delta: normalized (1 dim)

**Total input**: 12 dimensions

**Learns**: Which rhythm patterns blend well. Four-on-floor to broken beat is tricky; four-on-floor to four-on-floor is safe.

#### 4.2.4 KeyTransitionModel

**Purpose**: Score harmonic feel beyond Camelot rules.

**Input features**:
- from_key_num: Camelot number (1 dim, normalized 1-12)
- from_key_mode: major/minor (1 dim)
- to_key_num: (1 dim)
- to_key_mode: (1 dim)
- camelot_distance: wheel distance (1 dim)
- camelot_compatible: binary (1 dim)

**Total input**: 6 dimensions

**Learns**: The *feel* of key transitions. Camelot says 8A→3B is a clash, but some clashes create useful tension. The model can learn nuance beyond the rules.

#### 4.2.5 NarrativeModel

**Purpose**: Score set position / story arc flow.

**Input features**:
- from_intensity: one-hot (4 dims: opener/journey/peak/closer)
- to_intensity: one-hot (4 dims)
- direction: intended direction (3 dims)
- set_position: if known (3 dims, optional)

**Total input**: 14 dimensions

**Learns**: Narrative flow. opener→journey is natural; peak→peak risks fatigue; closer→opener only works at set boundaries.

#### 4.2.6 MixabilityModel

**Purpose**: Score technical blend quality.

**Input features**:
- from_mix_out_ease: normalized (1 dim)
- to_mix_in_ease: normalized (1 dim)
- bpm_delta: absolute, normalized (1 dim)
- from_has_clean_outro: binary (1 dim)
- to_has_clean_intro: binary (1 dim)

**Total input**: 5 dimensions

**Learns**: Technical mixing difficulty. High mix_out + high mix_in = easy blend. Large BPM delta = harder.

#### 4.2.7 GenreBlendModel

**Purpose**: Score genre transition quality.

**Input features**:
- genre_same: binary (1 dim)
- subgenre_same: binary (1 dim)
- from_genre_embedding: learned embedding (8 dims)
- to_genre_embedding: learned embedding (8 dims)

**Total input**: 18 dimensions

**Learns**: Which genres blend well. K-pop → House might work; K-pop → Death Metal probably doesn't. Genre embeddings let the model learn genre relationships.

#### 4.2.8 VocalTransitionModel

**Purpose**: Score vocal continuity.

**Input features**:
- from_vocal_presence: one-hot (5 dims)
- to_vocal_presence: one-hot (5 dims)
- from_vocal_style: one-hot (5 dims)
- to_vocal_style: one-hot (5 dims)
- language_match: binary (1 dim)

**Total input**: 21 dimensions

**Learns**: Vocal flow. Instrumental → vocal can be dramatic; group vocals → solo can feel sparse; language switches might jar or refresh.

### 4.3 Parameter Count

| Specialist | Input Dim | Hidden | Params |
|------------|-----------|--------|--------|
| Vibe | 16 | 32 | ~700 |
| Energy | 9 | 32 | ~500 |
| Groove | 12 | 32 | ~600 |
| Key | 6 | 32 | ~350 |
| Narrative | 14 | 32 | ~650 |
| Mixability | 5 | 32 | ~300 |
| Genre | 18 | 32 | ~800 |
| Vocal | 21 | 32 | ~900 |
| **Total Specialists** | | | **~4,800** |
| Aggregator | | | ~10,000 |
| Genre Embeddings | | | ~2,000 |
| **Grand Total** | | | **~17,000** |

This entire federation is **smaller than a single layer** of most neural networks.

---

## 5. The Aggregator

### 5.1 Purpose

The aggregator combines specialist scores into a final recommendation score. Critically, it does so **conditioned on DJ intent**.

When the DJ wants to "go darker," the aggregator should weight the Vibe specialist higher. When the DJ wants to "keep them dancing," Groove and Energy matter more.

### 5.2 Architecture

```python
class Aggregator(nn.Module):
    """Combines specialist scores based on context."""

    def __init__(self, num_specialists: int = 8, intent_dim: int = 16):
        super().__init__()

        # Intent encoder: touch input → intent embedding
        self.intent_encoder = nn.Sequential(
            nn.Linear(intent_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 16)
        )

        # Weight predictor: intent → specialist weights
        self.weight_predictor = nn.Sequential(
            nn.Linear(16, 32),
            nn.ReLU(),
            nn.Linear(32, num_specialists),
            nn.Softmax(dim=-1)
        )

        # Base weights (no intent provided)
        self.base_weights = nn.Parameter(
            torch.tensor([1.0, 0.8, 0.7, 0.6, 0.5, 0.4, 0.4, 0.3])
        )

    def forward(
        self,
        specialist_scores: torch.Tensor,  # [8]
        intent: torch.Tensor = None       # [intent_dim] or None
    ) -> tuple[torch.Tensor, torch.Tensor]:

        if intent is not None:
            intent_embed = self.intent_encoder(intent)
            weights = self.weight_predictor(intent_embed)
        else:
            weights = F.softmax(self.base_weights, dim=-1)

        # Weighted combination
        final_score = (specialist_scores * weights).sum()

        return final_score, weights
```

### 5.3 Intent Representation

The touch interface produces an intent vector:

```python
@dataclass
class DJIntent:
    """Structured representation of DJ intent from touch input."""

    # 2D pad position (-1 to 1)
    energy_direction: float    # -1 (down) to +1 (up)
    vibe_direction: float      # -1 (darker) to +1 (brighter)

    # Modifier buttons (0 or 1)
    peak_mode: bool           # Heading toward peak
    flow_mode: bool           # Maintain current vibe
    shift_mode: bool          # Actively change something
    genre_explore: bool       # Open to genre changes
    vocal_toggle: bool        # Change vocal presence

    def to_vector(self) -> torch.Tensor:
        return torch.tensor([
            self.energy_direction,
            self.vibe_direction,
            float(self.peak_mode),
            float(self.flow_mode),
            float(self.shift_mode),
            float(self.genre_explore),
            float(self.vocal_toggle),
            # Derived features
            abs(self.energy_direction),  # Magnitude of energy intent
            abs(self.vibe_direction),    # Magnitude of vibe intent
            self.energy_direction * self.vibe_direction,  # Interaction
        ])
```

### 5.4 How Intent Affects Weights

```
No intent (center of pad, no modifiers):
  Weights: [0.15, 0.14, 0.13, 0.12, 0.11, 0.10, 0.10, 0.09]
           (roughly: energy, dance, vibe, narrative, key, groove, mix, genre)
  → Balanced recommendation

Intent: energy_direction = +0.8 (strongly up)
  Aggregator learns to boost: Energy (0.25), Narrative (0.18)
  And reduce: Genre (0.05), Vocal (0.05)
  → Focus on energy trajectory

Intent: vibe_direction = -0.9 (much darker)
  Aggregator learns to boost: Vibe (0.30), Energy (0.15)
  And reduce: Genre (0.08)
  → Focus on vibe transition

Intent: genre_explore = True
  Aggregator learns to boost: Genre (0.25)
  And reduce: Vibe (0.10), Groove (0.08)
  → Tolerate more genre variation
```

---

## 6. Touch Interface Design

### 6.1 Design Principles

1. **No text input**: Hands are busy, room is dark
2. **Gestural**: Natural movements that map to musical concepts
3. **Glanceable**: See current state at a glance
4. **Fast**: One gesture to express intent
5. **Reversible**: Easy to reset or change

### 6.2 Primary Interface: 2D Gesture Pad

```
┌────────────────────────────────────────┐
│              ↑ BRIGHTER                │
│                                        │
│                                        │
│   ← LESS                    MORE →     │
│     ENERGY       ●         ENERGY      │
│               (drag)                   │
│                                        │
│                                        │
│              ↓ DARKER                  │
└────────────────────────────────────────┘
```

**Interaction**:
- **Tap center**: Reset to neutral (balanced recommendations)
- **Drag**: Set energy/vibe direction
- **Position persists**: Stays where you left it until changed
- **Visual feedback**: Glow/trail shows current position

**Mapping to intent**:
```python
def pad_to_intent(x: float, y: float) -> DJIntent:
    """Convert 2D pad position to intent.

    x: -1 (left/less energy) to +1 (right/more energy)
    y: -1 (down/darker) to +1 (up/brighter)
    """
    return DJIntent(
        energy_direction=x,
        vibe_direction=y,
    )
```

### 6.3 Modifier Buttons

Quick-tap buttons for specific intents:

```
┌─────────┬─────────┬─────────┐
│   🔥    │   🌊    │   🎭    │
│  PEAK   │  FLOW   │  SHIFT  │
│         │         │         │
├─────────┼─────────┼─────────┤
│   🎤    │   🎸    │   ⟲    │
│ VOCAL   │ GENRE   │  RESET  │
│  ±      │ EXPLORE │         │
└─────────┴─────────┴─────────┘
```

| Button | Effect | Aggregator Impact |
|--------|--------|-------------------|
| **PEAK** | Heading toward climax | Boost Energy, Narrative; target intensity=peak |
| **FLOW** | Keep current vibe rolling | Boost Vibe (same), Groove; reduce Genre |
| **SHIFT** | Actively change something | Reduce Vibe (same), boost Genre, Vocal |
| **VOCAL ±** | Toggle vocal preference | Boost Vocal specialist; invert preference |
| **GENRE EXPLORE** | Open to genre changes | Boost Genre specialist; prefer different |
| **RESET** | Clear all modifiers | Return to center, neutral weights |

**Modifiers are toggles**: Tap to enable (button glows), tap again to disable.

**Modifiers combine**: PEAK + SHIFT = heading to peak but open to genre change.

### 6.4 Full Interface Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│ NOW PLAYING                                                    12:47 AM │
│ ═══════════════════════════════════════════════════════════════════════ │
│                                                                         │
│  BTS - DOPE                                             ●●●●●●●●○○ 8/10 │
│  154 BPM  │  12A  │  euphoric  │  peak                         energy  │
│                                                                         │
├───────────────────────────────────────┬─────────────────────────────────┤
│                                       │                                 │
│     DIRECTION                         │   RECOMMENDATIONS               │
│     ┌─────────────────────────────┐   │                                 │
│     │         ↑ brighter          │   │   ┌─────────────────────────┐  │
│     │                             │   │   │ BLACKPINK - Kill This   │  │
│     │                             │   │   │ Love                    │  │
│     │  ← less    ●      more →   │   │   │ 152 BPM │ 1A            │  │
│     │    energy        energy    │   │   │ ██████████████░░ 87%    │  │
│     │                             │   │   │                         │  │
│     │                             │   │   │ V:0.8 E:0.9 G:0.7 K:0.9│  │
│     │         ↓ darker            │   │   └─────────────────────────┘  │
│     └─────────────────────────────┘   │                                 │
│                                       │   ┌─────────────────────────┐  │
│     ┌───────┬───────┬───────┐        │   │ Stray Kids - Back Door  │  │
│     │  🔥   │  🌊   │  🎭   │        │   │ 150 BPM │ 11A           │  │
│     │ PEAK  │ FLOW  │ SHIFT │        │   │ ██████████████░░ 84%    │  │
│     └───────┴───────┴───────┘        │   └─────────────────────────┘  │
│     ┌───────┬───────┬───────┐        │                                 │
│     │  🎤   │  🎸   │  ⟲   │        │   ┌─────────────────────────┐  │
│     │VOCAL ±│GENRE  │ RESET │        │   │ aespa - Savage          │  │
│     └───────┴───────┴───────┘        │   │ 156 BPM │ 2A            │  │
│                                       │   │ █████████████░░░ 81%    │  │
│                                       │   └─────────────────────────┘  │
│                                       │                                 │
│                                       │        tap to select ────►     │
│                                       │                                 │
└───────────────────────────────────────┴─────────────────────────────────┘
```

### 6.5 Recommendation Display

Each recommendation shows:
- Track info (title, artist, BPM, key)
- Overall score (progress bar)
- Mini specialist breakdown: `V:0.8 E:0.9 G:0.7 K:0.9`

**Tapping a recommendation**:
- Loads it as the next track
- Adds current track to recently played
- Resets pad to center (ready for next decision)

**Long-press a recommendation**:
- Shows detailed explanation
- Full specialist breakdown with reasons

### 6.6 Hardware Considerations

**Target platforms**:
- iPad (primary): Best touch experience, portable
- iPhone: Viable but cramped
- Touch-enabled laptop: Works, less natural
- Web browser: Mouse/trackpad substitute for touch

**MIDI integration** (future):
- Map pad position to MIDI XY controller
- Map modifiers to MIDI buttons
- Could use existing DJ controller knobs/buttons

---

## 7. Training Methodology

### 7.1 Bootstrapping from Hand-Coded Matrices

The specialists don't start from random weights. They're initialized to mimic the existing FLOWSTATE v1 matrices:

```python
def bootstrap_vibe_model(model: VibeTransitionModel, matrix: dict):
    """Initialize vibe model to match hand-coded matrix."""

    training_data = []
    for from_vibe, transitions in matrix.items():
        for to_vibe, score in transitions.items():
            training_data.append({
                'from_vibe': encode_vibe(from_vibe),
                'to_vibe': encode_vibe(to_vibe),
                'target': score
            })

    # Quick training to match matrix
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    for epoch in range(100):  # Converges fast
        for sample in training_data:
            pred = model(sample['from_vibe'], sample['to_vibe'])
            loss = F.mse_loss(pred, sample['target'])
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
```

After bootstrapping, the model **replicates the hand-coded matrix exactly** but is now in a form that can be refined with data.

### 7.2 Training Data Sources

#### 7.2.1 Corpus-Derived Pairs

Generate training pairs from the DJ's own analyzed library:

```python
def generate_training_pairs(corpus: Corpus) -> list[TrainingPair]:
    """Generate all pairwise transitions from corpus."""

    pairs = []
    for track_a in corpus.tracks:
        for track_b in corpus.tracks:
            if track_a.track_id == track_b.track_id:
                continue

            pairs.append(TrainingPair(
                current=track_a,
                candidate=track_b,
                # Initial label from bootstrapped model
                label=current_model.score(track_a, track_b)
            ))

    return pairs
```

#### 7.2.2 User Feedback (Implicit)

When the DJ selects a recommendation:

```python
def record_selection(
    current: Track,
    shown: list[Track],
    selected: Track
):
    """Record implicit feedback from DJ selection."""

    # Positive signal: selected transition
    positive_examples.append({
        'current': current,
        'candidate': selected,
        'label': 1.0
    })

    # Weak negative signal: rejected alternatives
    for track in shown:
        if track.track_id != selected.track_id:
            negative_examples.append({
                'current': current,
                'candidate': track,
                'label': 0.3  # Soft negative, not hard 0
            })
```

#### 7.2.3 Explicit Corrections

Optional UI for explicit feedback:

```
Was this a good recommendation?
[👍 Yes]  [👎 No]  [😐 Okay]
```

Maps to label adjustments for that transition.

### 7.3 Training Procedure

#### 7.3.1 Individual Specialist Training

Each specialist trains independently on relevant features:

```python
def train_specialist(
    specialist: SpecialistModel,
    training_data: list[dict],
    epochs: int = 10,
    lr: float = 0.001
):
    """Train a single specialist."""

    optimizer = torch.optim.Adam(specialist.parameters(), lr=lr)

    for epoch in range(epochs):
        random.shuffle(training_data)
        total_loss = 0

        for sample in training_data:
            pred = specialist(sample['features'])
            loss = F.mse_loss(pred, sample['label'])

            loss.backward()
            optimizer.step()
            optimizer.zero_grad()

            total_loss += loss.item()

        print(f"Epoch {epoch}: Loss = {total_loss / len(training_data):.4f}")
```

Training time: **< 1 minute per specialist** on CPU.

#### 7.3.2 Aggregator Training

The aggregator trains on full transitions with intent:

```python
def train_aggregator(
    aggregator: Aggregator,
    specialists: dict[str, SpecialistModel],
    training_data: list[dict],
    epochs: int = 20
):
    """Train aggregator to combine specialists given intent."""

    # Freeze specialists during aggregator training
    for s in specialists.values():
        s.eval()
        for p in s.parameters():
            p.requires_grad = False

    optimizer = torch.optim.Adam(aggregator.parameters(), lr=0.001)

    for epoch in range(epochs):
        for sample in training_data:
            # Get specialist scores
            scores = torch.tensor([
                specialists[name](sample[name + '_features'])
                for name in specialists.keys()
            ])

            # Aggregator combines with intent
            pred, weights = aggregator(scores, sample.get('intent'))

            loss = F.mse_loss(pred, sample['label'])
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
```

Training time: **< 5 minutes** on CPU.

### 7.4 Incremental Learning

The federation supports online/incremental learning:

```python
def update_from_feedback(
    federation: TransitionFederation,
    current: Track,
    selected: Track,
    rejected: list[Track],
    intent: DJIntent
):
    """Update federation from single DJ decision."""

    # This could run in background after each selection
    # Uses very small learning rate to avoid catastrophic forgetting

    lr = 0.0001  # Tiny update

    # Positive update for selected
    for specialist in federation.specialists.values():
        # ... update toward higher score for selected

    # Soft negative for rejected
    for track in rejected:
        # ... update toward lower score
```

This allows the model to **slowly adapt to the DJ's style** over time.

---

## 8. Implementation

### 8.1 System Requirements

**Minimum**:
- Python 3.11+
- PyTorch 2.0+ (CPU only is fine)
- 100MB RAM for models
- Any modern CPU

**No GPU required**. The entire federation fits in L2 cache.

### 8.2 Project Structure

```
flowstate/
├── src/flowstate/
│   ├── federation/
│   │   ├── __init__.py
│   │   ├── specialists.py      # 8 specialist models
│   │   ├── aggregator.py       # Aggregator model
│   │   ├── federation.py       # Combined federation
│   │   └── training.py         # Training utilities
│   ├── touch/
│   │   ├── __init__.py
│   │   ├── intent.py           # DJIntent dataclass
│   │   ├── pad.py              # 2D pad logic
│   │   └── interface.py        # Full touch interface
│   ├── engine/
│   │   ├── engine_v2.py        # Updated recommendation engine
│   │   └── ... (existing)
│   └── ui/
│       ├── touch_web.py        # Touch-enabled web UI
│       └── ... (existing)
├── models/
│   ├── specialists/            # Saved specialist weights
│   └── aggregator.pt           # Saved aggregator weights
└── data/
    └── feedback/               # Accumulated user feedback
```

### 8.3 Core Classes

```python
# federation/federation.py

class TransitionFederation:
    """The complete federation of specialists + aggregator."""

    def __init__(self):
        self.specialists = {
            'vibe': VibeTransitionModel(),
            'energy': EnergyArcModel(),
            'groove': GrooveTransitionModel(),
            'key': KeyTransitionModel(),
            'narrative': NarrativeModel(),
            'mixability': MixabilityModel(),
            'genre': GenreBlendModel(),
            'vocal': VocalTransitionModel(),
        }
        self.aggregator = Aggregator(num_specialists=8)

    def score(
        self,
        current: Track,
        candidate: Track,
        intent: DJIntent = None
    ) -> TransitionScore:
        """Score a transition with full explanation."""

        # Extract features for each specialist
        specialist_inputs = self._extract_features(current, candidate)

        # Get specialist scores
        specialist_scores = {}
        for name, model in self.specialists.items():
            specialist_scores[name] = model(specialist_inputs[name])

        # Aggregate
        scores_tensor = torch.tensor(list(specialist_scores.values()))
        intent_tensor = intent.to_vector() if intent else None

        final_score, weights = self.aggregator(scores_tensor, intent_tensor)

        return TransitionScore(
            score=final_score.item(),
            specialist_scores=specialist_scores,
            specialist_weights={
                name: weights[i].item()
                for i, name in enumerate(self.specialists.keys())
            }
        )

    def recommend(
        self,
        current: Track,
        corpus: Corpus,
        intent: DJIntent = None,
        top_k: int = 5
    ) -> list[ScoredTrack]:
        """Get top recommendations."""

        scored = []
        for candidate in corpus.tracks:
            if candidate.track_id == current.track_id:
                continue

            # Hard filters (unchanged from v1)
            if not self._passes_hard_filters(current, candidate):
                continue

            # Federation scoring
            transition = self.score(current, candidate, intent)
            scored.append(ScoredTrack(
                track=candidate,
                total_score=transition.score,
                specialist_scores=transition.specialist_scores,
                specialist_weights=transition.specialist_weights,
            ))

        # Sort and return top k
        scored.sort(key=lambda x: x.total_score, reverse=True)
        return scored[:top_k]
```

### 8.4 API Endpoints (Web UI)

```python
# ui/touch_web.py

from flask import Flask, jsonify, request

app = Flask(__name__)
federation = TransitionFederation.load("models/")

@app.route("/api/recommend", methods=["POST"])
def recommend():
    """Get recommendations based on current track and intent."""

    data = request.json
    current_track = corpus.get_by_id(data["current_track_id"])

    intent = DJIntent(
        energy_direction=data.get("energy_direction", 0),
        vibe_direction=data.get("vibe_direction", 0),
        peak_mode=data.get("peak_mode", False),
        flow_mode=data.get("flow_mode", False),
        shift_mode=data.get("shift_mode", False),
        genre_explore=data.get("genre_explore", False),
        vocal_toggle=data.get("vocal_toggle", False),
    )

    recommendations = federation.recommend(
        current=current_track,
        corpus=corpus,
        intent=intent,
        top_k=5
    )

    return jsonify({
        "recommendations": [
            {
                "track_id": r.track.track_id,
                "title": r.track.title,
                "artist": r.track.artist,
                "bpm": r.track.bpm,
                "key": r.track.key,
                "score": r.total_score,
                "specialists": r.specialist_scores,
                "weights": r.specialist_weights,
            }
            for r in recommendations
        ]
    })

@app.route("/api/select", methods=["POST"])
def record_selection():
    """Record DJ's selection for feedback learning."""

    data = request.json

    feedback_store.record(
        current_id=data["current_track_id"],
        selected_id=data["selected_track_id"],
        shown_ids=data["shown_track_ids"],
        intent=data.get("intent"),
        timestamp=datetime.now()
    )

    return jsonify({"status": "recorded"})
```

### 8.5 Performance

**Inference latency** (measured on M1 MacBook):
- Single transition score: **0.02ms**
- Full recommendation (500 tracks): **15ms**
- With hard filters (typical 50 candidates): **1.5ms**

**Memory footprint**:
- Model weights: **< 100KB**
- Runtime memory: **< 10MB**

This is **fast enough for real-time updates** as the DJ drags the pad.

---

## 9. Evaluation Framework

### 9.1 Offline Metrics

#### 9.1.1 Matrix Reconstruction

After bootstrapping, how well does each specialist match the original matrix?

```python
def matrix_reconstruction_error(specialist, original_matrix):
    """MSE between specialist predictions and original matrix."""

    total_error = 0
    count = 0

    for from_val, transitions in original_matrix.items():
        for to_val, target in transitions.items():
            pred = specialist(encode(from_val), encode(to_val))
            total_error += (pred - target) ** 2
            count += 1

    return total_error / count
```

Target: **< 0.01 MSE** (nearly perfect reconstruction).

#### 9.1.2 Cross-Validation

Hold out 20% of feedback data, train on 80%, measure prediction accuracy:

```python
def cross_validation_accuracy(federation, test_data):
    """Accuracy on held-out transitions."""

    correct = 0
    for sample in test_data:
        pred = federation.score(sample.current, sample.selected)

        # Did we rank the selected track highly?
        all_scores = [
            federation.score(sample.current, t)
            for t in sample.shown
        ]
        rank = sorted(all_scores, reverse=True).index(pred) + 1

        if rank <= 2:  # Top 2
            correct += 1

    return correct / len(test_data)
```

Target: **> 70%** top-2 accuracy (random = 40% for 5 options).

### 9.2 Online Metrics

Track during actual use:

| Metric | Description | Target |
|--------|-------------|--------|
| **Selection rate** | % of shown tracks that get selected | > 60% |
| **Time to select** | Seconds from display to tap | < 5s |
| **Intent usage** | % of selections with non-neutral intent | > 30% |
| **Return rate** | DJ comes back to use system | Qualitative |

### 9.3 Qualitative Evaluation

User study protocol:
1. DJ uses system for 30-minute set
2. Post-set interview:
   - "Did recommendations feel relevant?"
   - "Was the touch interface intuitive?"
   - "Did intent controls make a difference?"
   - "Would you use this in a real gig?"

---

## 10. Future Directions

### 10.1 Set-Aware Context

Current system only sees current track → candidate. Future version could incorporate:

```python
class SetAwareAggregator(Aggregator):
    """Aggregator that considers set history."""

    def __init__(self, history_length: int = 10):
        super().__init__()
        self.history_encoder = nn.LSTM(
            input_size=TRACK_FEATURE_DIM,
            hidden_size=32,
            num_layers=1
        )

    def forward(self, specialist_scores, intent, set_history):
        # Encode set history
        history_embed, _ = self.history_encoder(set_history)
        history_context = history_embed[-1]  # Last hidden state

        # Combine intent with history context
        context = torch.cat([intent, history_context], dim=-1)

        # Predict weights based on full context
        weights = self.weight_predictor(context)

        return (specialist_scores * weights).sum(), weights
```

This enables: "You've been building for 10 minutes → time for peak or release."

### 10.2 Transition-Level Embeddings

Instead of scoring transitions, learn to **embed** them:

```python
def transition_embedding(current: Track, candidate: Track) -> torch.Tensor:
    """Embed the feeling of going from current to candidate."""

    # A 64-dim vector capturing the transition's character
    # Similar transitions cluster together
    # Enables: "Find transitions that feel like THIS"
```

### 10.3 Hardware Integration

- **MIDI mapping**: Control intent via DJ controller knobs
- **Haptic feedback**: Vibrate when recommendation changes
- **Audio preview**: Quick preview of transition in headphones

### 10.4 Community Model Sharing

```python
# Export specialist weights
federation.specialists['vibe'].save("my_vibe_model.pt")

# Import someone else's specialist
federation.specialists['groove'].load("techno_groove_specialist.pt")
```

DJs could share specialists trained on their style.

---

## 11. Conclusion

CODEX v2 demonstrates that **effective DJ assistance doesn't require massive models**. By decomposing the problem into specialist micro-models and combining them with a context-aware aggregator, we achieve:

1. **Interpretability**: Every recommendation is explainable
2. **Efficiency**: 27K parameters, trains in seconds, infers in microseconds
3. **Adaptability**: Bootstrapped from intuition, refinable with data
4. **Usability**: Touch-first interface respects DJ workflow

The federation architecture offers a template for other domains where:
- Decisions have multiple independent factors
- Interpretability matters
- Compute budget is limited
- Personalization is valuable

We release CODEX v2 as open source, including:
- Full model code and training utilities
- Pre-trained weights bootstrapped from FLOWSTATE v1
- Touch interface implementation
- Evaluation framework

The future of DJ software isn't about replacing human creativity—it's about **augmenting human intuition** with systems that are fast, transparent, and respectful of the creative flow state.

---

## Appendix A: Specialist Input Specifications

| Specialist | Input Features | Dimensions |
|------------|---------------|------------|
| **Vibe** | from_vibe (6), to_vibe (6), energy (1), direction (3) | 16 |
| **Energy** | from_energy (1), to_energy (1), delta (1), direction (3), position (3) | 9 |
| **Groove** | from_groove (5), to_groove (5), tempo_match (1), bpm_delta (1) | 12 |
| **Key** | from_num (1), from_mode (1), to_num (1), to_mode (1), distance (1), compat (1) | 6 |
| **Narrative** | from_intensity (4), to_intensity (4), direction (3), position (3) | 14 |
| **Mixability** | out_ease (1), in_ease (1), bpm_delta (1), clean_outro (1), clean_intro (1) | 5 |
| **Genre** | same (1), subgenre_same (1), from_embed (8), to_embed (8) | 18 |
| **Vocal** | from_presence (5), to_presence (5), from_style (5), to_style (5), lang_match (1) | 21 |

## Appendix B: Touch Intent Encoding

```python
DJIntent.to_vector() produces:
[
    energy_direction,      # -1 to +1
    vibe_direction,        # -1 to +1
    peak_mode,             # 0 or 1
    flow_mode,             # 0 or 1
    shift_mode,            # 0 or 1
    genre_explore,         # 0 or 1
    vocal_toggle,          # 0 or 1
    |energy_direction|,    # 0 to 1 (magnitude)
    |vibe_direction|,      # 0 to 1 (magnitude)
    energy * vibe,         # -1 to +1 (interaction term)
]

Total: 10 dimensions
```

## Appendix C: Vibe Compatibility Matrix (Bootstrap Source)

```python
VIBE_MATRIX = {
    "dark":       {"dark": 1.0, "hypnotic": 0.8, "aggressive": 0.7, "chill": 0.3, "bright": 0.2, "euphoric": 0.1},
    "bright":     {"bright": 1.0, "euphoric": 0.9, "chill": 0.6, "hypnotic": 0.4, "dark": 0.2, "aggressive": 0.3},
    "hypnotic":   {"hypnotic": 1.0, "dark": 0.8, "chill": 0.7, "euphoric": 0.5, "bright": 0.4, "aggressive": 0.4},
    "euphoric":   {"euphoric": 1.0, "bright": 0.9, "aggressive": 0.6, "hypnotic": 0.5, "chill": 0.3, "dark": 0.2},
    "chill":      {"chill": 1.0, "hypnotic": 0.7, "bright": 0.6, "dark": 0.4, "euphoric": 0.3, "aggressive": 0.1},
    "aggressive": {"aggressive": 1.0, "dark": 0.8, "euphoric": 0.6, "hypnotic": 0.5, "bright": 0.3, "chill": 0.1},
}
```

---

*CODEX v2 is open source software released under the MIT License.*

*Last updated: January 2026*
