"""Camelot wheel key compatibility."""

# Camelot wheel: Inner ring (minor) = A, Outer ring (major) = B
# Moving clockwise adds 1, counterclockwise subtracts 1
# Same number different letter = relative major/minor

CAMELOT_WHEEL = {
    # Minor keys (A)
    "1A": "Abm",  "2A": "Ebm",  "3A": "Bbm",  "4A": "Fm",
    "5A": "Cm",   "6A": "Gm",   "7A": "Dm",   "8A": "Am",
    "9A": "Em",   "10A": "Bm",  "11A": "F#m", "12A": "Dbm",
    # Major keys (B)
    "1B": "B",    "2B": "F#",   "3B": "Db",   "4B": "Ab",
    "5B": "Eb",   "6B": "Bb",   "7B": "F",    "8B": "C",
    "9B": "G",    "10B": "D",   "11B": "A",   "12B": "E",
}

# Reverse lookup: musical key to Camelot
KEY_TO_CAMELOT = {v: k for k, v in CAMELOT_WHEEL.items()}

# Alternative key notations
KEY_ALIASES = {
    # Enharmonic equivalents
    "G#m": "Abm", "D#m": "Ebm", "A#m": "Bbm",
    "C#m": "Dbm", "Gb": "F#", "Cb": "B",
    "Db": "C#", "C#": "Db",
    # Common variations
    "Gbm": "F#m", "Cbm": "Bm",
}


def normalize_key(key: str) -> str:
    """Normalize a musical key to standard notation."""
    key = key.strip()

    # Already Camelot notation
    if key.upper() in CAMELOT_WHEEL:
        return key.upper()

    # Check aliases
    if key in KEY_ALIASES:
        key = KEY_ALIASES[key]

    return key


def to_camelot(key: str) -> str | None:
    """Convert musical key to Camelot notation."""
    key = normalize_key(key)

    # Already Camelot
    if key in CAMELOT_WHEEL:
        return key

    # Musical key
    return KEY_TO_CAMELOT.get(key)


def get_compatible_keys(key: str, extended: bool = True) -> list[str]:
    """
    Get harmonically compatible keys.

    Args:
        key: Camelot key (e.g., "8A", "5B")
        extended: If True, include 2-step compatible keys

    Returns:
        List of compatible Camelot keys

    Compatible keys (1-step):
    - Same key (perfect match)
    - +1 on wheel (energy boost)
    - -1 on wheel (energy drop)
    - Same number, different letter (relative major/minor)

    Extended (2-step):
    - +2 on wheel
    - -2 on wheel
    """
    key = key.upper()
    if key not in CAMELOT_WHEEL:
        return []

    num = int(key[:-1])
    letter = key[-1]

    compatible = [key]  # Same key

    # Adjacent keys on wheel (+1, -1)
    for delta in [1, -1]:
        adj_num = ((num - 1 + delta) % 12) + 1
        compatible.append(f"{adj_num}{letter}")

    # Relative major/minor (same number, different letter)
    other_letter = "B" if letter == "A" else "A"
    compatible.append(f"{num}{other_letter}")

    # Extended: 2-step compatibility
    if extended:
        for delta in [2, -2]:
            adj_num = ((num - 1 + delta) % 12) + 1
            compatible.append(f"{adj_num}{letter}")

    return compatible


def key_compatibility_score(key1: str, key2: str) -> float:
    """
    Score key compatibility between 0 and 1.

    Returns:
        1.0 = same key
        0.9 = 1-step (adjacent or relative)
        0.7 = 2-step (extended compatible)
        0.3 = energy boost/drop (+7 semitones)
        0.0 = clash
    """
    key1 = key1.upper()
    key2 = key2.upper()

    if key1 not in CAMELOT_WHEEL or key2 not in CAMELOT_WHEEL:
        return 0.5  # Unknown, neutral score

    if key1 == key2:
        return 1.0

    # Parse keys
    num1, letter1 = int(key1[:-1]), key1[-1]
    num2, letter2 = int(key2[:-1]), key2[-1]

    # Calculate wheel distance
    wheel_dist = min(
        abs(num1 - num2),
        12 - abs(num1 - num2)
    )

    # Same number, different letter (relative major/minor)
    if num1 == num2 and letter1 != letter2:
        return 0.9

    # Same letter, check wheel distance
    if letter1 == letter2:
        if wheel_dist == 1:
            return 0.9  # Adjacent
        elif wheel_dist == 2:
            return 0.7  # Extended compatible
        elif wheel_dist == 7:
            return 0.3  # Energy boost/drop (dominant relationship)

    # Different letter, adjacent numbers
    if letter1 != letter2 and wheel_dist == 1:
        return 0.6  # Diagonal move

    return 0.0  # Clash


def compute_compatible_keys(track_key: str) -> list[str]:
    """Compute and return compatible keys for a track."""
    return get_compatible_keys(track_key, extended=True)
