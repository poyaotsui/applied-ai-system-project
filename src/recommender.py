from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import csv

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def score(self, user: UserProfile, song: Song) -> float:
        """
        Scoring Rule: produces a single relevance score for one song.

        Weights reflect how much each feature matters to "vibe" matching:
          - Genre match: 2.0  (strongest signal — genre is the broadest filter)
          - Mood match:  1.5  (second strongest — mood narrows the emotional tone)
          - Energy proximity: up to 1.0  (1 - |user_pref - song_energy|, rewards closeness)
          - Valence boost: up to 0.5  (happier songs get a small lift)
          - Acousticness:  up to 0.5  (only applied when user prefers acoustic)

        A Scoring Rule answers: "How good is this ONE song for this user?"
        A Ranking Rule answers: "Given all scores, which songs rise to the top?"
        Both are needed — scoring alone produces a pile of numbers;
        ranking turns that pile into an ordered recommendation list.
        """
        points = 0.0

        # Categorical features — exact match bonus
        if song.genre == user.favorite_genre:
            points += 2.0
        if song.mood == user.favorite_mood:
            points += 1.5

        # Numerical features — proximity scoring (closer = higher reward)
        energy_proximity = 1.0 - abs(song.energy - user.target_energy)
        points += energy_proximity * 1.0

        # Valence: positivity/happiness of a track (0–1). Small lift for upbeat songs.
        points += song.valence * 0.5

        # Acousticness bonus only when the user prefers acoustic feel
        if user.likes_acoustic:
            points += song.acousticness * 0.5

        return round(points, 4)

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """
        Ranking Rule: sort all songs by score descending, return top k.
        """
        scored = sorted(self.songs, key=lambda s: self.score(user, s), reverse=True)
        return scored[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        reasons = []
        if song.genre == user.favorite_genre:
            reasons.append(f"genre matches your favourite ({song.genre})")
        if song.mood == user.favorite_mood:
            reasons.append(f"mood matches ({song.mood})")
        energy_diff = abs(song.energy - user.target_energy)
        if energy_diff <= 0.15:
            reasons.append(f"energy level ({song.energy}) is close to your target ({user.target_energy})")
        if not reasons:
            reasons.append("overall vibe alignment across energy and valence")
        return "Recommended because: " + "; ".join(reasons) + "."


def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    print(f"Loading songs from {csv_path}...")
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            songs.append({
                "id":           int(row["id"]),
                "title":        row["title"],
                "artist":       row["artist"],
                "genre":        row["genre"],
                "mood":         row["mood"],
                "energy":       float(row["energy"]),
                "tempo_bpm":    float(row["tempo_bpm"]),
                "valence":      float(row["valence"]),
                "danceability": float(row["danceability"]),
                "acousticness": float(row["acousticness"]),
            })
    return songs


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Score a single song and return (total_score, reasons) for display."""
    points = 0.0
    reasons = []

    if song.get("genre") == user_prefs.get("genre"):
        points += 2.0
        reasons.append(f"genre match (+2.0)")

    if song.get("mood") == user_prefs.get("mood"):
        points += 1.5
        reasons.append(f"mood match (+1.5)")

    target_energy = user_prefs.get("energy", 0.5)
    energy_proximity = 1.0 - abs(song["energy"] - target_energy)
    energy_pts = round(energy_proximity * 1.0, 2)
    points += energy_pts
    reasons.append(f"energy proximity (+{energy_pts:.2f})")

    valence_pts = round(song["valence"] * 0.5, 2)
    points += valence_pts
    reasons.append(f"valence boost (+{valence_pts:.2f})")

    return round(points, 4), reasons


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py

    Ranking Rule: score every song, sort descending, return top k.
    Returns list of (song_dict, score, explanation_string).
    """
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        explanation = ", ".join(reasons) if reasons else "general vibe alignment"
        scored.append((song, score, explanation))

    # Ranking Rule: sort by score highest-first
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]
