"""
RAG retrieval layer: filter and score the song catalog based on structured query params.

The agent calls search_catalog() as a tool; results become the grounding context
that Claude uses to generate recommendations (Retrieval-Augmented Generation).
"""

from __future__ import annotations
import logging

logger = logging.getLogger(__name__)

# Genres and moods that exist in the catalog — used for input normalisation
KNOWN_GENRES = {
    "pop", "lofi", "rock", "ambient", "hip-hop", "classical",
    "r&b", "country", "electronic", "metal", "soul", "reggae",
    "jazz", "indie pop", "synthwave",
}
KNOWN_MOODS = {
    "happy", "chill", "intense", "peaceful", "energetic",
    "melancholic", "romantic", "nostalgic", "focused", "moody",
    "relaxed", "angry",
}


def search_catalog(
    songs: list[dict],
    genre: str | None = None,
    mood: str | None = None,
    energy_min: float = 0.0,
    energy_max: float = 1.0,
    limit: int = 5,
) -> list[dict]:
    """
    Filter the catalog and return the top `limit` songs ranked by energy proximity.

    Fuzzy genre/mood matching: if the exact value isn't in the catalog we skip
    that filter rather than returning zero results, and log a warning.
    """
    energy_min = max(0.0, min(1.0, float(energy_min)))
    energy_max = max(0.0, min(1.0, float(energy_max)))
    if energy_min > energy_max:
        energy_min, energy_max = energy_max, energy_min

    norm_genre = genre.lower().strip() if genre else None
    norm_mood = mood.lower().strip() if mood else None

    if norm_genre and norm_genre not in KNOWN_GENRES:
        logger.warning("Genre %r not in catalog — genre filter skipped", norm_genre)
        norm_genre = None
    if norm_mood and norm_mood not in KNOWN_MOODS:
        logger.warning("Mood %r not in catalog — mood filter skipped", norm_mood)
        norm_mood = None

    results = []
    for song in songs:
        if norm_genre and song["genre"].lower() != norm_genre:
            continue
        if norm_mood and song["mood"].lower() != norm_mood:
            continue
        if not (energy_min <= song["energy"] <= energy_max):
            continue
        results.append(song)

    mid_energy = (energy_min + energy_max) / 2
    results.sort(key=lambda s: abs(s["energy"] - mid_energy))

    logger.debug(
        "search_catalog(genre=%r, mood=%r, energy=%.2f–%.2f) → %d/%d songs",
        norm_genre, norm_mood, energy_min, energy_max, min(len(results), limit), len(songs),
    )
    return results[:limit]


def catalog_match_quality(
    results: list[dict],
    genre: str | None = None,
    mood: str | None = None,
    energy_min: float = 0.0,
    energy_max: float = 1.0,
) -> float:
    """
    Return a 0.0–1.0 confidence score for how well the top search result
    satisfied the query.

    Weights: genre match 40 %, mood match 30 %, energy proximity 30 %.
    Returns 0.0 when no results were found.
    """
    if not results:
        return 0.0
    top = results[0]
    score = 0.0
    if genre and top["genre"].lower() == genre.lower().strip():
        score += 0.4
    if mood and top["mood"].lower() == mood.lower().strip():
        score += 0.3
    mid = (energy_min + energy_max) / 2
    score += (1.0 - abs(top["energy"] - mid)) * 0.3
    return round(score, 2)


def format_for_context(songs: list[dict]) -> str:
    """Serialise a list of song dicts into a compact string for prompt context."""
    if not songs:
        return "(no songs matched the search criteria)"
    lines = []
    for s in songs:
        lines.append(
            f"- [{s['id']}] \"{s['title']}\" by {s['artist']} "
            f"| genre={s['genre']} mood={s['mood']} "
            f"energy={s['energy']} valence={s['valence']}"
        )
    return "\n".join(lines)
