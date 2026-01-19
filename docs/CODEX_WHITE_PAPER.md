# CODEX: A Privacy-First Framework for Prompt-Driven Music Recommendation

## An Open-Source System for Semantic Music Understanding and Natural Language DJ Assistance

**Version 0.1 - Draft**
**January 2026**

---

## Abstract

Current music recommendation systems rely on collaborative filtering ("listeners who liked X also liked Y") or low-level audio features that fail to capture the semantic qualities DJs and music professionals need: energy trajectories, mixability, emotional arcs, and narrative flow. We present CODEX (Contextual Open DJ Embedding eXchange), an open-source framework that combines large language model-extracted musical semantics with transfer learning from pre-trained audio models to enable natural language-driven track recommendation.

CODEX introduces three key innovations: (1) a standardized feature schema capturing DJ-specific musical attributes extracted via multimodal LLMs, (2) a two-stage embedding architecture combining audio understanding from pre-trained models (MERT, CLAP) with semantic feature encoding, and (3) a prompt-aware ranking system that interprets natural language DJ intent ("give me something darker with similar energy") to score track transitions.

Critically, CODEX is designed as a **privacy-first, local-first system**. While base models are trained on public datasets, all user music analysis and recommendation inference runs entirely on the DJ's local machine. No listening data, music files, or personal library information ever leaves the user's control.

We release the full framework including: pre-trained model weights, training code, feature extraction pipelines, and a reference implementation (FLOWSTATE) demonstrating real-time DJ assistance with Rekordbox integration.

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Background and Related Work](#2-background-and-related-work)
3. [System Architecture](#3-system-architecture)
4. [Feature Schema Specification](#4-feature-schema-specification)
5. [Embedding Model Design](#5-embedding-model-design)
6. [Prompt-Aware Ranking System](#6-prompt-aware-ranking-system)
7. [Training Methodology](#7-training-methodology)
8. [Local Fine-Tuning and Privacy Architecture](#8-local-fine-tuning-and-privacy-architecture)
9. [Evaluation Framework](#9-evaluation-framework)
10. [Implementation Roadmap](#10-implementation-roadmap)
11. [Conclusion](#11-conclusion)
12. [References](#12-references)

---

## 1. Introduction

### 1.1 The Problem

A DJ constructing a live set faces a complex, real-time decision problem: given the current track and the desired emotional trajectory, which track should come next? This decision involves multiple simultaneous constraints:

- **Harmonic compatibility**: Keys should mix without dissonance
- **Tempo matching**: BPM should be within mixable range (typically ±6%)
- **Energy trajectory**: Building, maintaining, or releasing tension
- **Narrative coherence**: The "story" of the set should flow naturally
- **Technical mixability**: Some tracks have clean intro/outro points; others don't
- **Vibe continuity**: Abrupt mood shifts can disrupt the dancefloor

Existing tools address subsets of this problem:
- Key detection software handles harmonic compatibility
- BPM analysis handles tempo matching
- But **energy, narrative, vibe, and mixability** remain manual judgments

Professional DJs develop intuition over years of practice. Our goal is to encode this intuition computationally while keeping the DJ in creative control.

### 1.2 Why Natural Language?

Current DJ software presents recommendations as sorted lists with numeric scores. This forces the DJ to translate their creative intent ("I want to shift the vibe darker while maintaining energy") into parameter manipulation (energy ≥ 7, vibe = dark, BPM ± 5).

Natural language input offers:
- **Expressive power**: "Build tension without going full peak" is hard to express as sliders
- **Speed**: Spoken or typed intent is faster than menu navigation during a live set
- **Intuitive mental model**: DJs think in musical terms, not database queries

### 1.3 Privacy as a Core Requirement

Music libraries are deeply personal. They represent years of curation, reveal listening habits, and may contain unreleased material. Any recommendation system that uploads library data to external servers is fundamentally incompatible with professional DJ workflows.

CODEX is designed from the ground up for **local-first operation**:
- Base models are trained on public datasets and distributed as downloadable weights
- User music is analyzed locally (using the user's own API keys for LLM analysis)
- All recommendation inference runs on-device
- Optional fine-tuning happens locally
- No telemetry, no cloud sync, no data collection

### 1.4 Contributions

This paper presents:

1. **CODEX Feature Schema**: A standardized 30+ field specification for DJ-relevant musical attributes, designed for extraction via multimodal LLMs

2. **codex-embed**: A pre-trained embedding model that combines MERT audio understanding with semantic feature encoding to produce track embeddings suitable for similarity search and recommendation

3. **codex-rank**: A prompt-aware cross-encoder that scores track pairs given natural language DJ intent

4. **codex-train**: An open-source training framework enabling community contribution and local fine-tuning

5. **FLOWSTATE**: A reference implementation demonstrating real-time DJ assistance with Rekordbox integration

---

## 2. Background and Related Work

### 2.1 Music Information Retrieval (MIR)

The field of Music Information Retrieval has developed extensive techniques for extracting musical features from audio:

**Low-level features** (spectral centroid, MFCCs, chroma) capture acoustic properties but lack semantic meaning. A "bright" synth and a "bright" guitar have different spectral profiles despite sharing a perceptual quality.

**Mid-level features** (beat tracking, key detection, onset detection) capture structural elements. Libraries like Essentia [1] and librosa [2] provide robust extraction pipelines.

**High-level features** (genre, mood, energy) require learned representations. Traditional approaches used hand-engineered features with classifiers (SVM, random forests). Modern approaches use deep learning.

### 2.2 Pre-trained Audio Models

Recent advances in self-supervised learning have produced powerful audio foundation models:

**MERT (Music Embedding Representation Transformer)** [3]: A 330M parameter model trained on 160,000 hours of music using masked acoustic modeling. MERT learns to predict masked portions of audio, forcing it to understand temporal structure, harmony, and rhythm. It achieves state-of-the-art results across 14 music understanding tasks.

**CLAP (Contrastive Language-Audio Pretraining)** [4]: Trained on audio-text pairs, CLAP learns a joint embedding space where audio and natural language descriptions are aligned. "Upbeat electronic dance music" and actual EDM tracks have similar embeddings.

**MusicNN** [5]: Convolutional networks trained for music tagging on the Million Song Dataset. Smaller and faster than transformer models, suitable for edge deployment.

**OpenL3** [6]: General audio embeddings trained via audio-visual correspondence. Produces 6144-dimensional embeddings capturing acoustic content.

These models encode **general musical knowledge** but lack domain-specific understanding of DJ workflows.

### 2.3 Music Recommendation Systems

**Collaborative filtering** (Spotify, Apple Music) recommends based on listening patterns across users. Strengths: discovers unexpected connections. Weaknesses: cold start problem, popularity bias, no understanding of *why* tracks are similar.

**Content-based filtering** uses audio features to find similar tracks. Strengths: works for any track with audio. Weaknesses: limited to acoustic similarity, doesn't capture contextual appropriateness.

**Hybrid systems** combine both approaches. Modern streaming services use deep learning to fuse collaborative signals with audio embeddings [7].

**DJ-specific systems** are rare in the literature. Mixed In Key [8] provides harmonic analysis. Rekordbox and Serato offer basic recommendation features. Academic work on DJ transitions exists [9] but focuses on mix point detection rather than track selection.

### 2.4 Large Language Models for Music Understanding

The emergence of multimodal LLMs (GPT-4V, Gemini, Claude) enables a new approach: directly asking an AI to analyze music. These models can:
- Listen to audio and describe its characteristics
- Extract structured metadata (BPM, key, mood, energy)
- Provide subjective assessments (mixability, vibe, narrative role)
- Generate natural language descriptions

This capability is central to CODEX. Rather than engineering features, we leverage LLMs to extract semantically rich descriptions that encode human-level musical understanding.

### 2.5 Transfer Learning in Audio

Transfer learning—using knowledge from one task to improve performance on another—is well-established in audio processing:

- Speech recognition models adapt to new languages with limited data
- Sound event detection models transfer across acoustic environments
- Music tagging models transfer across genres

The key insight: **low and mid-level audio understanding is universal**. A model trained on diverse music learns what "a beat" is, what "energy" sounds like, how melodies work. This knowledge transfers even when the target domain (e.g., K-pop for DJ sets) differs from training data.

CODEX exploits this through a two-stage approach:
1. Use pre-trained models (MERT, CLAP) for general audio understanding
2. Add lightweight adaptation layers for DJ-specific semantics

---

## 3. System Architecture

### 3.1 Overview

CODEX consists of five layers, each independently useful but most powerful in combination:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CODEX ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  LAYER 1: FEATURE EXTRACTION                                            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Input: Audio file (MP3, FLAC, WAV, etc.)                        │   │
│  │ Process: Multimodal LLM analysis (Gemini, GPT-4, etc.)          │   │
│  │ Output: CODEX Feature Schema (30+ structured fields)            │   │
│  │ Location: User's machine, user's API key                        │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                               │                                         │
│                               ▼                                         │
│  LAYER 2: AUDIO EMBEDDING                                               │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Input: Raw audio waveform                                        │   │
│  │ Process: Pre-trained MERT encoder (frozen or fine-tuned)        │   │
│  │ Output: 768-dimensional audio embedding                         │   │
│  │ Purpose: Captures acoustic properties models can't verbalize    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                               │                                         │
│                               ▼                                         │
│  LAYER 3: SEMANTIC EMBEDDING                                            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Input: CODEX features (from Layer 1) + Audio embedding (Layer 2)│   │
│  │ Process: codex-embed model (trained fusion network)             │   │
│  │ Output: 384-dimensional track embedding                         │   │
│  │ Purpose: Unified representation for similarity and retrieval    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                               │                                         │
│                               ▼                                         │
│  LAYER 4: PROMPT ENCODING                                               │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Input: Natural language DJ intent                               │   │
│  │ Process: CLAP text encoder or fine-tuned prompt encoder         │   │
│  │ Output: Intent embedding in same space as track embeddings      │   │
│  │ Purpose: Enables semantic search via vector similarity          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                               │                                         │
│                               ▼                                         │
│  LAYER 5: RANKING                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Input: Current track + Candidate tracks + DJ prompt             │   │
│  │ Process: codex-rank cross-encoder                               │   │
│  │ Output: Relevance scores for each candidate                     │   │
│  │ Purpose: Final ranking considering full context                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Data Flow

A typical recommendation request flows through the system as follows:

```
1. USER INPUT
   ├─ Current track: "BTS - Dope" (already in corpus with embedding)
   └─ Prompt: "something darker but keep the energy high"

2. PROMPT ENCODING (Layer 4)
   └─ "something darker but keep the energy high"
      → CLAP text encoder
      → intent_embedding [384 dims]

3. CANDIDATE RETRIEVAL (Layer 3)
   └─ Approximate nearest neighbor search in embedding space
   └─ Filter by hard constraints (BPM ±6%, compatible keys)
   └─ Return top 50 candidates

4. RANKING (Layer 5)
   └─ For each candidate:
      ├─ Input: [current_track, candidate, prompt]
      ├─ codex-rank cross-encoder
      └─ Output: relevance_score (0-1)
   └─ Sort by score, return top 5-10

5. OUTPUT
   └─ Ranked list of recommendations with explanations
```

### 3.3 Inference Modes

CODEX supports multiple inference configurations:

**Full pipeline** (highest quality): All five layers, cross-encoder ranking
- Latency: ~500ms per request
- Best for: Careful track selection, playlist building

**Embedding-only** (fast retrieval): Layers 1-4, vector similarity ranking
- Latency: ~50ms per request
- Best for: Real-time suggestions during live sets

**Feature-only** (rule-based fallback): Layer 1 only, traditional scoring
- Latency: ~10ms per request
- Best for: Systems without ML inference capability

### 3.4 Component Interfaces

Each layer exposes a clean interface for modularity:

```python
# Layer 1: Feature Extraction
class FeatureExtractor(Protocol):
    def extract(self, audio_path: Path) -> CodexFeatures: ...

# Layer 2: Audio Embedding
class AudioEncoder(Protocol):
    def encode(self, audio_path: Path) -> np.ndarray: ...  # [768]

# Layer 3: Semantic Embedding
class TrackEncoder(Protocol):
    def encode(self, features: CodexFeatures,
               audio_embedding: np.ndarray) -> np.ndarray: ...  # [384]

# Layer 4: Prompt Encoding
class PromptEncoder(Protocol):
    def encode(self, prompt: str) -> np.ndarray: ...  # [384]

# Layer 5: Ranking
class Ranker(Protocol):
    def rank(self, current: Track, candidates: list[Track],
             prompt: str) -> list[ScoredTrack]: ...
```

---

## 4. Feature Schema Specification

### 4.1 Design Principles

The CODEX Feature Schema is designed with these principles:

1. **DJ-centric**: Features should map to decisions DJs actually make
2. **Extractable**: Features must be reliably extractable by current LLMs
3. **Actionable**: Each feature should influence recommendation in a clear way
4. **Bounded**: Numeric features have defined ranges for normalization
5. **Interoperable**: Schema should work across analysis providers

### 4.2 Complete Schema

```yaml
codex_schema_version: "1.0"

# ─────────────────────────────────────────────────────────────
# IDENTITY
# ─────────────────────────────────────────────────────────────
identity:
  track_id:
    type: string
    description: Unique identifier (recommended: SHA256 of first 1MB)
    required: true

  title:
    type: string
    description: Track title
    required: true

  artist:
    type: string
    description: Primary artist name
    required: true

  file_path:
    type: string
    description: Relative or absolute path to audio file
    required: true

  duration_seconds:
    type: float
    description: Track duration in seconds
    required: true
    range: [0, 7200]  # Up to 2 hours

# ─────────────────────────────────────────────────────────────
# AUDIO FUNDAMENTALS
# ─────────────────────────────────────────────────────────────
audio_fundamentals:
  bpm:
    type: float
    description: Tempo in beats per minute
    required: true
    range: [60, 200]
    extraction_notes: |
      For half-time or double-time feels, report the felt tempo.
      K-pop often has complex tempo perception; prefer 100-130 range
      when ambiguous.

  key:
    type: string
    description: Musical key in Camelot notation
    required: true
    enum: [1A, 2A, 3A, 4A, 5A, 6A, 7A, 8A, 9A, 10A, 11A, 12A,
           1B, 2B, 3B, 4B, 5B, 6B, 7B, 8B, 9B, 10B, 11B, 12B]
    extraction_notes: |
      A = minor keys, B = major keys.
      Number indicates position on circle of fifths.

  audio_fidelity:
    type: integer
    description: Audio quality assessment
    required: true
    range: [1, 10]
    extraction_notes: |
      10 = Pristine master quality
      7-9 = Good quality, minor artifacts
      4-6 = Acceptable, noticeable compression
      1-3 = Poor quality, significant artifacts

# ─────────────────────────────────────────────────────────────
# ENERGY ATTRIBUTES
# ─────────────────────────────────────────────────────────────
energy:
  energy:
    type: integer
    description: Overall intensity and power level
    required: true
    range: [1, 10]
    extraction_notes: |
      1-2: Ambient, downtempo, minimal
      3-4: Chill, relaxed groove
      5-6: Mid-energy, steady movement
      7-8: High energy, driving
      9-10: Peak intensity, maximum power

  danceability:
    type: integer
    description: How much the track invites physical movement
    required: true
    range: [1, 10]
    extraction_notes: |
      Consider: beat clarity, groove strength, rhythmic hooks
      High danceability doesn't require high energy

  intensity:
    type: string
    description: Narrative role in a DJ set
    required: true
    enum: [opener, journey, peak, closer]
    extraction_notes: |
      opener: Set-starting material, builds anticipation
      journey: Main body of set, maintains flow
      peak: Climactic moments, maximum impact
      closer: Wind-down, resolution, farewell

# ─────────────────────────────────────────────────────────────
# VIBE AND MOOD
# ─────────────────────────────────────────────────────────────
vibe:
  vibe:
    type: string
    description: Primary emotional/atmospheric quality
    required: true
    enum: [dark, bright, hypnotic, euphoric, chill, aggressive]
    extraction_notes: |
      dark: Minor keys, heavy bass, ominous atmosphere
      bright: Major keys, uplifting, positive energy
      hypnotic: Repetitive, trance-inducing, meditative
      euphoric: Emotional peaks, anthemic, transcendent
      chill: Relaxed, smooth, easy-going
      aggressive: Hard-hitting, intense, confrontational

  mood_tags:
    type: array[string]
    description: Freeform mood descriptors
    required: true
    min_items: 3
    max_items: 7
    extraction_notes: |
      Examples: confident, melancholic, playful, mysterious,
      triumphant, sensual, nostalgic, rebellious, dreamy

# ─────────────────────────────────────────────────────────────
# RHYTHM AND GROOVE
# ─────────────────────────────────────────────────────────────
rhythm:
  groove_style:
    type: string
    description: Fundamental rhythmic pattern
    required: true
    enum: [four-on-floor, broken, swung, syncopated, linear]
    extraction_notes: |
      four-on-floor: Kick on every beat (house, techno)
      broken: Breakbeat, drum & bass patterns
      swung: Shuffle feel, triplet swing
      syncopated: Off-beat emphasis, funk influence
      linear: No repeating pattern, progressive

  tempo_feel:
    type: string
    description: Perceived tempo relative to BPM
    required: true
    enum: [straight, double-time, half-time]
    extraction_notes: |
      A 140 BPM track can feel like 70 (half-time) or 140 (straight)

# ─────────────────────────────────────────────────────────────
# MIXABILITY
# ─────────────────────────────────────────────────────────────
mixability:
  mix_in_ease:
    type: integer
    description: How easy is it to mix INTO this track
    required: true
    range: [1, 10]
    extraction_notes: |
      Consider: intro length, intro clarity, rhythmic consistency
      10 = Long, clean intro with steady beat
      1 = Abrupt start, irregular rhythm, hard to cue

  mix_out_ease:
    type: integer
    description: How easy is it to mix OUT OF this track
    required: true
    range: [1, 10]
    extraction_notes: |
      Consider: outro length, outro clarity, clean exit points
      10 = Long, clean outro with steady beat
      1 = Abrupt end, no clear exit point

  mixability_notes:
    type: string
    description: Freeform mixing tips and warnings
    required: false
    extraction_notes: |
      Examples: "Long spoken intro - wait for beat at 0:32"
      "False ending at 3:15, real outro at 3:45"
      "Key change in final chorus"

# ─────────────────────────────────────────────────────────────
# VOCALS
# ─────────────────────────────────────────────────────────────
vocals:
  vocal_presence:
    type: string
    description: Type of vocals present
    required: true
    enum: [instrumental, male, female, mixed, group]

  vocal_style:
    type: string
    description: Vocal delivery style
    required: true
    enum: [rap, singing, both, chant, spoken, none]

  language:
    type: string
    description: Primary language of vocals
    required: false
    enum: [korean, english, japanese, spanish, portuguese,
           french, german, italian, chinese, mixed, other]

# ─────────────────────────────────────────────────────────────
# STRUCTURE
# ─────────────────────────────────────────────────────────────
structure:
  structure:
    type: array[string]
    description: Ordered list of track sections
    required: true
    extraction_notes: |
      Use: intro, verse, prechorus, chorus, drop, breakdown,
           bridge, outro, build, instrumental

  drop_intensity:
    type: integer
    description: Intensity of main drop/climax (if present)
    required: false
    range: [1, 10]
    extraction_notes: |
      null if track has no distinct drop

# ─────────────────────────────────────────────────────────────
# PRODUCTION
# ─────────────────────────────────────────────────────────────
production:
  instrumentation:
    type: array[string]
    description: Prominent instruments/sounds
    required: true
    min_items: 3
    max_items: 8
    extraction_notes: |
      Examples: 808 bass, arpeggiated synth, acoustic guitar,
      live drums, orchestral strings, vocal chops

  production_style:
    type: string
    description: Overall production aesthetic
    required: true
    enum: [clean, distorted, filtered, lo-fi, polished,
           raw, layered, minimal, maximalist]

  production_quality:
    type: integer
    description: Technical production quality
    required: true
    range: [1, 10]
    extraction_notes: |
      Assess: mixing clarity, mastering loudness,
      frequency balance, stereo image

# ─────────────────────────────────────────────────────────────
# GENRE AND CONTEXT
# ─────────────────────────────────────────────────────────────
genre:
  genre:
    type: string
    description: Primary genre classification
    required: true

  subgenre:
    type: string
    description: More specific genre classification
    required: false

  similar_artists:
    type: array[string]
    description: Artists with similar sound
    required: true
    min_items: 2
    max_items: 5

# ─────────────────────────────────────────────────────────────
# DESCRIPTION
# ─────────────────────────────────────────────────────────────
description:
  description:
    type: string
    description: Natural language summary of the track
    required: true
    extraction_notes: |
      1-3 sentences describing the track's character,
      notable features, and potential use in a DJ set

# ─────────────────────────────────────────────────────────────
# METADATA
# ─────────────────────────────────────────────────────────────
metadata:
  created_at:
    type: datetime
    description: When this analysis was created
    required: true

  updated_at:
    type: datetime
    description: When this analysis was last updated
    required: true

  analyzer_version:
    type: string
    description: Version of analyzer that created this
    required: true

  analyzer_model:
    type: string
    description: LLM model used for analysis
    required: false
```

### 4.3 Schema Versioning

The schema follows semantic versioning:
- **Major** version: Breaking changes requiring re-analysis
- **Minor** version: New optional fields added
- **Patch** version: Documentation or extraction guidance updates

Corpus files include `schema_version` to ensure compatibility.

### 4.4 Extraction Prompt Template

For reference, here is a condensed version of the prompt used to extract features via multimodal LLM:

```
You are a professional DJ and music analyst. Listen to this track and provide
a detailed analysis in JSON format.

Context from file metadata:
- Title: {title}
- Artist: {artist}
- BPM hint: {bpm_hint}

Provide your analysis using EXACTLY this JSON structure:
{schema_json}

Important guidelines:
- BPM: Report the felt tempo. For K-pop, prefer 100-130 range when ambiguous.
- Key: Use Camelot notation (1A-12B). A = minor, B = major.
- Energy/Danceability: Use full 1-10 range. 5 is average, not "unknown."
- Intensity: Consider where this track fits in a DJ set arc.
- Be specific in mood_tags and instrumentation.
- mixability_notes: Include any DJ tips (intro quirks, false endings, etc.)

Return ONLY the JSON object, no additional text.
```

---

## 5. Embedding Model Design

### 5.1 Design Goals

The `codex-embed` model must:
1. Produce embeddings where **similar tracks cluster together**
2. Support **vector arithmetic** (current + "darker" → target region)
3. Be **fast enough for real-time** retrieval (<50ms per track)
4. Be **small enough for local deployment** (<500MB)
5. Leverage **pre-trained audio understanding** from foundation models

### 5.2 Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         codex-embed ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  INPUT BRANCH A: Audio                                                  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Raw Audio (30s sample, 24kHz)                                    │  │
│  │         │                                                        │  │
│  │         ▼                                                        │  │
│  │ ┌─────────────────────────┐                                      │  │
│  │ │   MERT-v1-330M          │  ◄── Pre-trained, frozen             │  │
│  │ │   (Transformer encoder) │      or LoRA-adapted                 │  │
│  │ └───────────┬─────────────┘                                      │  │
│  │             │                                                    │  │
│  │             ▼                                                    │  │
│  │      [768-dim audio embedding]                                   │  │
│  │             │                                                    │  │
│  │             ▼                                                    │  │
│  │ ┌─────────────────────────┐                                      │  │
│  │ │   Audio Projection      │  ◄── Learned: 768 → 192              │  │
│  │ │   (Linear + LayerNorm)  │                                      │  │
│  │ └───────────┬─────────────┘                                      │  │
│  │             │                                                    │  │
│  │      [192-dim projected audio]                                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                               │                                         │
│                               │                                         │
│  INPUT BRANCH B: Features                                               │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ CODEX Features (structured JSON)                                 │  │
│  │         │                                                        │  │
│  │         ▼                                                        │  │
│  │ ┌─────────────────────────┐                                      │  │
│  │ │   Feature Encoder       │                                      │  │
│  │ │   - Numeric: normalize  │                                      │  │
│  │ │   - Categorical: embed  │                                      │  │
│  │ │   - Text: sentence-BERT │                                      │  │
│  │ └───────────┬─────────────┘                                      │  │
│  │             │                                                    │  │
│  │      [~400-dim concatenated features]                            │  │
│  │             │                                                    │  │
│  │             ▼                                                    │  │
│  │ ┌─────────────────────────┐                                      │  │
│  │ │   Feature MLP           │  ◄── Learned: 400 → 192              │  │
│  │ │   (2 layers, ReLU)      │                                      │  │
│  │ └───────────┬─────────────┘                                      │  │
│  │             │                                                    │  │
│  │      [192-dim projected features]                                │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                               │                                         │
│                               │                                         │
│  FUSION                       ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                                                                  │  │
│  │  [192-dim audio] ⊕ [192-dim features] = [384-dim concatenated]  │  │
│  │             │                                                    │  │
│  │             ▼                                                    │  │
│  │ ┌─────────────────────────┐                                      │  │
│  │ │   Fusion Transformer    │  ◄── 2 layers, 4 heads               │  │
│  │ │   (Cross-attention)     │      Learned from scratch            │  │
│  │ └───────────┬─────────────┘                                      │  │
│  │             │                                                    │  │
│  │             ▼                                                    │  │
│  │ ┌─────────────────────────┐                                      │  │
│  │ │   Output Projection     │  ◄── 384 → 384, L2 normalized        │  │
│  │ └───────────┬─────────────┘                                      │  │
│  │             │                                                    │  │
│  │      [384-dim track embedding]                                   │  │
│  │                                                                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  OUTPUT: Unit-normalized 384-dimensional embedding                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Feature Encoding Details

**Numeric features** (energy, danceability, BPM, etc.):
- Min-max normalization to [0, 1] using schema-defined ranges
- Concatenated into single vector

**Categorical features** (vibe, groove_style, intensity, etc.):
- Learned embedding lookup tables
- 16-dimensional embedding per category
- Concatenated into single vector

**Text features** (mood_tags, description, mixability_notes):
- Encoded via frozen sentence-transformer (all-MiniLM-L6-v2)
- Mean pooling for multi-tag fields
- 384-dimensional per text field

**Total feature vector**: ~400 dimensions before MLP projection

### 5.4 Why Two Branches?

The dual-branch architecture serves complementary purposes:

**Audio branch (MERT)** captures:
- Acoustic texture (timbre, production quality)
- Rhythmic nuances beyond simple BPM
- Harmonic content beyond key label
- Information LLMs might miss or misinterpret

**Feature branch (CODEX schema)** captures:
- High-level semantic concepts (vibe, intensity, narrative role)
- DJ-specific knowledge (mixability, set positioning)
- Structured information suitable for filtering
- Human-interpretable attributes

The fusion transformer learns which modality to trust for different aspects of similarity.

### 5.5 Embedding Space Properties

We design the embedding space to support these operations:

**Similarity search**: `cosine_similarity(track_a, track_b)`
- Tracks with similar vibe, energy, and genre should cluster

**Vector arithmetic**: `track_a + direction_vector`
- "Darker" should have a consistent direction
- "More energy" should have a consistent direction

**Prompt alignment** (via CLAP integration):
- Text prompts map to same space
- "dark aggressive techno" should be near actual dark aggressive techno tracks

### 5.6 Model Size

| Component | Parameters | Size |
|-----------|------------|------|
| MERT encoder (frozen) | 330M | ~1.3GB |
| Audio projection | 150K | <1MB |
| Feature embeddings | 50K | <1MB |
| Feature MLP | 100K | <1MB |
| Fusion transformer | 3M | ~12MB |
| Output projection | 150K | <1MB |
| **Total (inference)** | **~334M** | **~1.3GB** |
| **Without MERT** | **~3.5M** | **~15MB** |

For deployment without GPU, we offer a "lite" mode using pre-computed MERT embeddings stored in the corpus, reducing inference to only the fusion layers (~15MB model).

---

## 6. Prompt-Aware Ranking System

### 6.1 Motivation

Embedding similarity alone cannot capture **conditional preferences**. The DJ's intent changes what "similar" means:

- "More energy" → prioritize energy over vibe
- "Change up the genre" → penalize genre similarity
- "Something that builds tension" → consider intensity progression

The `codex-rank` model learns these conditional scoring functions.

### 6.2 Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         codex-rank ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  INPUTS                                                                 │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                                                                  │  │
│  │  Current Track      Candidate Track        DJ Prompt             │  │
│  │  ┌───────────┐      ┌───────────┐         ┌───────────┐         │  │
│  │  │ embedding │      │ embedding │         │   text    │         │  │
│  │  │  [384]    │      │  [384]    │         │           │         │  │
│  │  └─────┬─────┘      └─────┬─────┘         └─────┬─────┘         │  │
│  │        │                  │                     │               │  │
│  └────────│──────────────────│─────────────────────│───────────────┘  │
│           │                  │                     │                   │
│           │                  │                     ▼                   │
│           │                  │         ┌─────────────────────┐        │
│           │                  │         │   CLAP Text Encoder │        │
│           │                  │         │   (frozen)          │        │
│           │                  │         └──────────┬──────────┘        │
│           │                  │                    │                   │
│           │                  │             [384-dim prompt]           │
│           │                  │                    │                   │
│           ▼                  ▼                    ▼                   │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │                                                                │   │
│  │   CROSS-ENCODER                                                │   │
│  │   ┌────────────────────────────────────────────────────────┐  │   │
│  │   │                                                        │  │   │
│  │   │  [CLS] current [SEP] candidate [SEP] prompt [SEP]     │  │   │
│  │   │                                                        │  │   │
│  │   │  Concatenated input: [1 + 384 + 1 + 384 + 1 + 384 + 1] │  │   │
│  │   │  = 1156 tokens                                         │  │   │
│  │   │                                                        │  │   │
│  │   └────────────────────────────────────────────────────────┘  │   │
│  │                         │                                      │   │
│  │                         ▼                                      │   │
│  │   ┌────────────────────────────────────────────────────────┐  │   │
│  │   │   Transformer Encoder                                  │  │   │
│  │   │   - 6 layers, 8 heads, 512 hidden dim                 │  │   │
│  │   │   - ~25M parameters                                    │  │   │
│  │   └────────────────────────────────────────────────────────┘  │   │
│  │                         │                                      │   │
│  │                    [CLS] output                                │   │
│  │                         │                                      │   │
│  │                         ▼                                      │   │
│  │   ┌────────────────────────────────────────────────────────┐  │   │
│  │   │   Classification Head                                  │  │   │
│  │   │   Linear(512, 1) → Sigmoid                            │  │   │
│  │   └────────────────────────────────────────────────────────┘  │   │
│  │                         │                                      │   │
│  └─────────────────────────│──────────────────────────────────────┘   │
│                            │                                          │
│                            ▼                                          │
│                    relevance_score ∈ [0, 1]                           │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### 6.3 Cross-Encoder vs Bi-Encoder

We use a **cross-encoder** architecture for ranking because:

| Aspect | Bi-Encoder | Cross-Encoder |
|--------|------------|---------------|
| Speed | Fast (embed once, compare many) | Slow (recompute for each pair) |
| Quality | Good for retrieval | Better for nuanced ranking |
| Prompt handling | Prompt changes embedding | Prompt directly influences scoring |

Our two-stage pipeline uses both:
1. **Bi-encoder** (codex-embed): Fast retrieval of top 50 candidates
2. **Cross-encoder** (codex-rank): Precise ranking of candidates with prompt context

### 6.4 Handling Diverse Prompts

DJ prompts vary widely in structure:

```
Concrete:     "something at 128 BPM in a minor key"
Relative:     "more energy, darker vibe"
Comparative:  "similar to what's playing but more aggressive"
Narrative:    "build tension toward a peak"
Negation:     "avoid vocals, keep it instrumental"
Complex:      "darker but not slower, maybe switch genres"
```

The cross-encoder learns to handle these through diverse training data (Section 7).

### 6.5 Explainability

The ranking model can provide explanations by analyzing attention patterns:

```python
def explain_recommendation(current, candidate, prompt):
    """Generate human-readable explanation for ranking decision."""

    # Run forward pass with attention capture
    score, attentions = model.forward_with_attention(current, candidate, prompt)

    # Identify high-attention features
    feature_importance = analyze_cross_attention(attentions)

    # Generate explanation
    reasons = []
    if feature_importance['energy'] > threshold:
        delta = candidate.energy - current.energy
        reasons.append(f"Energy {'increases' if delta > 0 else 'decreases'} by {abs(delta)}")
    if feature_importance['vibe'] > threshold:
        reasons.append(f"Vibe shifts from {current.vibe} to {candidate.vibe}")
    # ... etc

    return {
        'score': score,
        'reasons': reasons,
        'confidence': attention_entropy(attentions)
    }
```

---

## 7. Training Methodology

### 7.1 Training Data Strategy

Training prompt-aware recommendation requires paired examples:
- (current_track, candidate_track, prompt, relevance_label)

We generate this data through three approaches:

#### 7.1.1 Rule-Based Synthesis from Public Datasets

Using MTG-Jamendo (55k tracks with mood/genre/energy labels):

```python
def generate_training_pair(track_a, track_b, corpus):
    """Generate training example from track pair."""

    examples = []

    # Energy-based prompts
    energy_delta = track_b.energy - track_a.energy
    if energy_delta >= 2:
        examples.append({
            'current': track_a,
            'candidate': track_b,
            'prompt': random.choice([
                "more energy",
                "increase the intensity",
                "something more powerful",
                "crank it up"
            ]),
            'label': 1.0  # Positive
        })
        # Negative: track that doesn't increase energy
        negative = sample_track_where(corpus, lambda t: t.energy <= track_a.energy)
        examples.append({
            'current': track_a,
            'candidate': negative,
            'prompt': "more energy",
            'label': 0.0  # Negative
        })

    # Mood-based prompts
    if track_b.mood == 'dark' and track_a.mood != 'dark':
        examples.append({
            'current': track_a,
            'candidate': track_b,
            'prompt': random.choice([
                "something darker",
                "shift to a darker vibe",
                "more ominous"
            ]),
            'label': 1.0
        })

    # Genre-based prompts
    if track_b.genre != track_a.genre:
        examples.append({
            'current': track_a,
            'candidate': track_b,
            'prompt': random.choice([
                "change up the genre",
                "something different",
                "switch styles"
            ]),
            'label': 1.0
        })

    # Similarity prompts
    if are_similar(track_a, track_b):  # Same genre, similar energy
        examples.append({
            'current': track_a,
            'candidate': track_b,
            'prompt': random.choice([
                "more of the same",
                "keep this vibe going",
                "something similar"
            ]),
            'label': 1.0
        })

    return examples
```

#### 7.1.2 LLM-Augmented Prompt Generation

Use an LLM to generate diverse prompt phrasings:

```python
AUGMENTATION_PROMPT = """
Given these two tracks and their relationship, generate 10 different ways
a DJ might ask for this transition:

Track A: {track_a_description}
Track B: {track_b_description}
Relationship: Track B has higher energy and darker mood than Track A

Generate varied, natural phrasings a DJ might use:
1. "more energy, darker feel"
2. ...
"""

# Generate varied prompts for each relationship type
prompt_variations = llm.generate(AUGMENTATION_PROMPT)
```

#### 7.1.3 Hard Negative Mining

Easy negatives (random tracks) don't teach much. We mine hard negatives:

```python
def mine_hard_negatives(track_a, prompt, corpus, model):
    """Find tracks that seem relevant but aren't."""

    # Encode prompt
    prompt_embedding = model.encode_prompt(prompt)

    # Find tracks close in embedding space
    candidates = corpus.nearest_neighbors(track_a.embedding, k=100)

    # Filter to those that DON'T match the prompt semantics
    hard_negatives = []
    for candidate in candidates:
        if prompt_implies_higher_energy(prompt) and candidate.energy <= track_a.energy:
            hard_negatives.append(candidate)
        elif prompt_implies_darker(prompt) and candidate.vibe != 'dark':
            hard_negatives.append(candidate)
        # ... etc

    return hard_negatives
```

### 7.2 Training Procedure

#### 7.2.1 Stage 1: Embedding Model Pre-training

**Objective**: Learn track embeddings where similar tracks cluster

**Data**: MTG-Jamendo + FMA (100k+ tracks with labels)

**Loss**: Contrastive loss (InfoNCE)

```python
def embedding_loss(anchor, positive, negatives, temperature=0.07):
    """InfoNCE contrastive loss."""

    # Positive similarity
    pos_sim = cosine_similarity(anchor, positive) / temperature

    # Negative similarities
    neg_sims = [cosine_similarity(anchor, neg) / temperature for neg in negatives]

    # InfoNCE
    loss = -pos_sim + log(exp(pos_sim) + sum(exp(neg_sims)))

    return loss
```

**Positive pairs**: Tracks with same mood AND similar energy (±2)
**Negative pairs**: Random tracks from different mood categories

**Training details**:
- Batch size: 256
- Learning rate: 1e-4 with cosine decay
- Epochs: 50
- GPU: Single A100 (or 4x V100)
- Time: ~24 hours

#### 7.2.2 Stage 2: Ranker Training

**Objective**: Learn to score (current, candidate, prompt) tuples

**Data**: Synthesized pairs from Stage 1 embeddings (~1M examples)

**Loss**: Binary cross-entropy

```python
def ranking_loss(predictions, labels):
    """BCE loss for ranking."""
    return F.binary_cross_entropy(predictions, labels)
```

**Training details**:
- Batch size: 64
- Learning rate: 2e-5 with linear warmup
- Epochs: 10
- Time: ~8 hours on single GPU

#### 7.2.3 Stage 3: Joint Fine-tuning (Optional)

Fine-tune embedding and ranking models jointly on high-quality data:

```python
def joint_loss(embed_loss, rank_loss, alpha=0.3):
    """Combined loss for joint training."""
    return alpha * embed_loss + (1 - alpha) * rank_loss
```

### 7.3 Evaluation During Training

**Embedding quality metrics**:
- Recall@K: Do correct mood/energy matches appear in top K neighbors?
- Mean Average Precision: Ranking quality of retrieval

**Ranking quality metrics**:
- AUC-ROC: Discrimination between positive and negative pairs
- NDCG: Ranking quality of scored candidates

**Held-out validation**:
- 10% of MTG-Jamendo tracks reserved for validation
- Early stopping on validation loss

---

## 8. Local Fine-Tuning and Privacy Architecture

### 8.1 Privacy Threat Model

We consider these privacy concerns:

1. **Library contents**: What tracks does the user own?
2. **Listening patterns**: What do they play and when?
3. **Musical taste**: What genres/moods do they prefer?
4. **Unreleased material**: Do they have exclusive tracks?

**CODEX guarantee**: None of this information ever leaves the user's machine without explicit action.

### 8.2 Local-Only Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER'S MACHINE                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────┐      ┌─────────────────────┐                  │
│  │  Music Library      │      │  CODEX Models       │                  │
│  │  (audio files)      │      │  (downloaded once)  │                  │
│  └──────────┬──────────┘      └──────────┬──────────┘                  │
│             │                            │                              │
│             ▼                            │                              │
│  ┌─────────────────────┐                 │                              │
│  │  Feature Extraction │◄────────────────┘                              │
│  │  (Gemini API call)  │                                                │
│  └──────────┬──────────┘                                                │
│             │                                                           │
│             │  User's API key, user pays                                │
│             │  Only audio sent, results returned                        │
│             │  No library metadata shared                               │
│             │                                                           │
│             ▼                                                           │
│  ┌─────────────────────┐      ┌─────────────────────┐                  │
│  │  Corpus             │      │  Fine-tuned Adapter │                  │
│  │  (local JSON)       │      │  (optional, local)  │                  │
│  └──────────┬──────────┘      └──────────┬──────────┘                  │
│             │                            │                              │
│             └────────────┬───────────────┘                              │
│                          │                                              │
│                          ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Inference Engine (runs locally)                                │   │
│  │  - Embedding generation                                         │   │
│  │  - Candidate retrieval                                          │   │
│  │  - Ranking                                                      │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                          │                                              │
│                          ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Recommendations (displayed locally)                            │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

External network calls (user-controlled):
  1. Download CODEX models (one-time, from public URL)
  2. Gemini API for feature extraction (user's key, user's cost)

No telemetry. No analytics. No cloud sync.
```

### 8.3 Local Fine-Tuning

Users can adapt the base model to their library without sharing data:

```python
# Local fine-tuning script
def fine_tune_local(corpus_path: Path, base_model_path: Path, output_path: Path):
    """Fine-tune CODEX on user's local corpus."""

    # Load base model
    model = CodexEmbed.load(base_model_path)

    # Freeze most layers, enable LoRA adapters
    model.freeze_base()
    model.enable_lora(rank=8, alpha=16)

    # Load user's corpus
    corpus = Corpus.load(corpus_path)

    # Generate training pairs from user's data
    pairs = generate_contrastive_pairs(corpus)

    # Fine-tune (all computation local)
    trainer = LocalTrainer(
        model=model,
        data=pairs,
        epochs=5,
        lr=1e-4,
        device='cuda' if torch.cuda.is_available() else 'cpu'
    )
    trainer.train()

    # Save adapter weights only (~10MB)
    model.save_lora_weights(output_path)
```

**LoRA (Low-Rank Adaptation)** enables fine-tuning with:
- Minimal additional parameters (~0.1% of base model)
- Fast training (minutes on GPU, ~1 hour on CPU)
- Easy distribution (adapter weights are small)

### 8.4 Optional Community Features

For users who want to participate in improving CODEX:

**Federated learning** (future): Train on distributed data without centralization
- User trains locally, shares only gradient updates
- Server aggregates gradients, distributes improved model
- No raw data ever shared

**Anonymized statistics** (opt-in): Aggregate genre/BPM distributions
- Helps understand what music the community analyzes
- No track identification, no user identification

Both features are **strictly opt-in** with clear disclosure.

---

## 9. Evaluation Framework

### 9.1 Offline Metrics

#### 9.1.1 Embedding Quality

**Retrieval metrics** on held-out test set:

| Metric | Definition | Target |
|--------|------------|--------|
| R@10 | % of correct mood matches in top 10 | >80% |
| R@50 | % of correct mood matches in top 50 | >95% |
| MAP | Mean average precision for mood retrieval | >0.7 |

**Clustering metrics**:

| Metric | Definition | Target |
|--------|------------|--------|
| Silhouette | Cluster separation for mood categories | >0.3 |
| NMI | Normalized mutual information vs. labels | >0.5 |

#### 9.1.2 Ranking Quality

**Classification metrics** on synthetic pairs:

| Metric | Definition | Target |
|--------|------------|--------|
| AUC-ROC | Discrimination accuracy | >0.9 |
| Accuracy | Correct positive/negative classification | >85% |

**Ranking metrics** on candidate lists:

| Metric | Definition | Target |
|--------|------------|--------|
| NDCG@5 | Quality of top 5 ranking | >0.8 |
| MRR | Mean reciprocal rank of best match | >0.7 |

### 9.2 Human Evaluation

Offline metrics don't capture subjective quality. We propose:

#### 9.2.1 DJ Preference Study

Protocol:
1. Professional DJs receive current track + prompt
2. System shows 2 recommendations (CODEX vs baseline)
3. DJ selects preferred recommendation (or tie)
4. Repeat for 100 prompts across 10 DJs

Metrics:
- Win rate vs. random baseline
- Win rate vs. rule-based baseline (current FLOWSTATE)
- Win rate vs. embedding-only (no ranking model)

#### 9.2.2 Set Coherence Evaluation

Protocol:
1. Generate 10-track mini-set using CODEX recommendations
2. Professional DJ rates set coherence (1-10)
3. Compare to human-curated sets

### 9.3 Online Metrics (In Reference App)

For users of FLOWSTATE:

| Metric | Definition | Significance |
|--------|------------|--------------|
| Recommendation acceptance rate | % of suggestions played | User satisfaction |
| Time to selection | Seconds from prompt to play | System utility |
| Session length | Tracks played with CODEX active | Engagement |
| Prompt diversity | Unique prompts per session | Feature utilization |

All metrics computed locally, optionally shared if user opts in.

---

## 10. Implementation Roadmap

### 10.1 Phase 1: Foundation (Months 1-2)

**Deliverables**:
- [ ] CODEX Feature Schema v1.0 specification
- [ ] Feature extraction pipeline using Gemini API
- [ ] Corpus data format and tooling
- [ ] Public dataset preparation (MTG-Jamendo, FMA)

**Milestones**:
- Schema published and documented
- 50k tracks from public datasets processed with schema
- Baseline feature extraction working

### 10.2 Phase 2: Embedding Model (Months 3-4)

**Deliverables**:
- [ ] codex-embed model architecture implementation
- [ ] Training pipeline with contrastive learning
- [ ] Pre-trained weights release (codex-embed-v0.1)
- [ ] Embedding quality benchmarks

**Milestones**:
- Training completes on public data
- R@10 > 75% on held-out test set
- Model weights released on Hugging Face

### 10.3 Phase 3: Ranking Model (Months 5-6)

**Deliverables**:
- [ ] codex-rank cross-encoder implementation
- [ ] Training data synthesis pipeline
- [ ] Pre-trained weights release (codex-rank-v0.1)
- [ ] Ranking quality benchmarks

**Milestones**:
- Synthetic training data generation (>500k pairs)
- AUC-ROC > 0.85 on test set
- Model weights released

### 10.4 Phase 4: Integration (Months 7-8)

**Deliverables**:
- [ ] FLOWSTATE integration with CODEX models
- [ ] Local fine-tuning scripts and documentation
- [ ] Performance optimization for CPU inference
- [ ] User documentation and tutorials

**Milestones**:
- End-to-end recommendation working in FLOWSTATE
- Inference <500ms on consumer hardware
- Documentation complete

### 10.5 Phase 5: Community Release (Month 9+)

**Deliverables**:
- [ ] Open-source release of all code
- [ ] Model weights on Hugging Face
- [ ] Research paper submission
- [ ] Community feedback collection

**Milestones**:
- GitHub repository public
- First external contributors
- DJ community feedback incorporated

### 10.6 Resource Requirements

| Resource | Specification | Purpose |
|----------|--------------|---------|
| Training GPU | 1x A100 80GB or 4x V100 | Model training |
| Storage | 2TB SSD | Audio datasets |
| Gemini API | ~$500-1000 | Feature extraction for public data |
| Human eval | 10 professional DJs | Quality assessment |

---

## 11. Conclusion

CODEX represents a new approach to music recommendation that combines:

1. **Semantic richness**: LLM-extracted features capture DJ-relevant musical qualities that traditional MIR methods miss

2. **Transfer learning efficiency**: Pre-trained audio models provide musical understanding; CODEX adds domain-specific adaptation

3. **Natural language interface**: DJs express intent in their own words rather than manipulating parameters

4. **Privacy-first design**: All user data stays local; base models trained on public data

5. **Open-source ecosystem**: Models, training code, and reference implementation freely available

We believe this framework can meaningfully assist DJs while keeping them in creative control. The natural language interface augments human judgment rather than replacing it—the DJ still decides, but with better-informed options.

Beyond DJ applications, the CODEX approach—combining LLM feature extraction with transfer learning for domain-specific recommendation—may generalize to other creative domains where semantic understanding matters: video editing, sound design, visual art curation.

We invite the community to build on this work: improve the models, expand the feature schema, create new applications. The future of creative AI assistance should be open.

---

## 12. References

[1] Bogdanov, D., et al. "Essentia: An audio analysis library for music information retrieval." International Society for Music Information Retrieval Conference (ISMIR), 2013.

[2] McFee, B., et al. "librosa: Audio and music signal analysis in Python." Proceedings of the 14th Python in Science Conference, 2015.

[3] Li, Y., et al. "MERT: Acoustic Music Understanding Model with Large-Scale Self-supervised Training." arXiv preprint arXiv:2306.00107, 2023.

[4] Elizalde, B., et al. "CLAP: Learning Audio Concepts from Natural Language Supervision." IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP), 2023.

[5] Pons, J., et al. "musicnn: Pre-trained convolutional neural networks for music audio tagging." Late-breaking/demo ISMIR, 2019.

[6] Cramer, J., et al. "Look, Listen, and Learn More: Design Choices for Deep Audio Embeddings." IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP), 2019.

[7] Schedl, M., et al. "Deep Learning in Music Recommendation Systems." Frontiers in Applied Mathematics and Statistics, 2019.

[8] Mixed In Key LLC. "Mixed In Key: Harmonic Mixing Software." https://mixedinkey.com/

[9] Scarfe, R., et al. "Towards Automated DJ Mixing with Neural Crossfade Prediction." ISMIR, 2022.

[10] Hu, E., et al. "LoRA: Low-Rank Adaptation of Large Language Models." arXiv preprint arXiv:2106.09685, 2021.

[11] Defferrard, M., et al. "FMA: A Dataset for Music Analysis." International Society for Music Information Retrieval Conference (ISMIR), 2017.

[12] Bogdanov, D., et al. "The MTG-Jamendo Dataset for Automatic Music Tagging." Machine Learning for Music Discovery Workshop (ICML), 2019.

---

## Appendix A: Camelot Key Compatibility Matrix

```
Camelot wheel relationships for harmonic mixing:

Same key (perfect):     1.0
Adjacent number (±1):   0.9    (e.g., 8A → 7A or 9A)
Relative major/minor:   0.9    (e.g., 8A → 8B)
Two steps:              0.7    (e.g., 8A → 6A or 10A)
Diagonal:               0.6    (e.g., 8A → 7B or 9B)
Dominant (+7 semitones): 0.3   (energy boost, use carefully)
Other:                  0.0    (likely clash)
```

## Appendix B: Example Prompts and Expected Behavior

| Prompt | Expected Behavior |
|--------|-------------------|
| "more energy" | Increase energy score, maintain other attributes |
| "darker vibe" | Shift toward vibe=dark, may reduce energy slightly |
| "build toward a peak" | Gradual energy increase, intensity→peak |
| "keep it rolling" | Similar energy, similar vibe, high danceability |
| "change up the genre" | Different genre, may maintain energy/vibe |
| "something with vocals" | Filter to vocal_presence != instrumental |
| "drop it down" | Reduce energy, shift toward intensity=closer |
| "more aggressive but same tempo" | Increase energy, vibe=aggressive, BPM ±2 |

## Appendix C: Model Card

### codex-embed-v0.1

**Model type**: Track embedding encoder
**Architecture**: MERT-based dual-tower with fusion transformer
**Parameters**: 334M (3.5M trainable with frozen MERT)
**Input**: Audio file + CODEX features
**Output**: 384-dimensional unit-normalized embedding
**Training data**: MTG-Jamendo (55k tracks), FMA subset (50k tracks)
**Intended use**: Music similarity search, recommendation retrieval
**Limitations**: Primarily trained on Western music; may underperform on non-Western genres
**License**: Apache 2.0

### codex-rank-v0.1

**Model type**: Prompt-aware cross-encoder ranker
**Architecture**: Transformer cross-encoder with CLAP text encoding
**Parameters**: 25M
**Input**: Current track embedding + candidate embedding + text prompt
**Output**: Relevance score [0, 1]
**Training data**: 1M synthetic pairs from MTG-Jamendo/FMA
**Intended use**: Re-ranking candidates given DJ intent
**Limitations**: Prompt understanding limited to training distribution
**License**: Apache 2.0

---

*This white paper is a living document. For the latest version, see the CODEX GitHub repository.*

*Last updated: January 2026*
