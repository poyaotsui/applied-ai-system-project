"""
Command-line runner for the Music Recommender Simulation.

Run from the project root with:
    python -m src.main
"""

from src.recommender import load_songs, recommend_songs, score_song


# ---------------------------------------------------------------------------
# Experimental scoring override — doubles energy weight, halves genre weight
# ---------------------------------------------------------------------------
def score_song_experiment(user_prefs: dict, song: dict):
    """Score with genre weight halved (1.0) and energy weight doubled (2.0)."""
    points = 0.0
    reasons = []

    if song.get("genre") == user_prefs.get("genre"):
        points += 1.0                          # was 2.0
        reasons.append("genre match (+1.0 experimental)")

    if song.get("mood") == user_prefs.get("mood"):
        points += 1.5
        reasons.append("mood match (+1.5)")

    target_energy = user_prefs.get("energy", 0.5)
    energy_proximity = 1.0 - abs(song["energy"] - target_energy)
    energy_pts = round(energy_proximity * 2.0, 2)  # was 1.0
    points += energy_pts
    reasons.append(f"energy proximity (+{energy_pts:.2f} experimental)")

    valence_pts = round(song["valence"] * 0.5, 2)
    points += valence_pts
    reasons.append(f"valence boost (+{valence_pts:.2f})")

    return round(points, 4), reasons


def recommend_experiment(user_prefs: dict, songs: list, k: int = 5):
    """Rank songs using the experimental weight configuration."""
    scored = []
    for song in songs:
        score, reasons = score_song_experiment(user_prefs, song)
        explanation = ", ".join(reasons)
        scored.append((song, score, explanation))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------
def print_profile_header(label: str, prefs: dict) -> None:
    print("=" * 60)
    print(f"  Profile: {label}")
    print(f"  Genre : {prefs.get('genre', '—')}  |  Mood: {prefs.get('mood', '—')}  |  Energy: {prefs.get('energy', '—')}")
    print("=" * 60)


def print_recommendations(recs: list) -> None:
    for rank, (song, score, explanation) in enumerate(recs, start=1):
        print(f"  {rank}. {song['title']}  —  {song['artist']}")
        print(f"     Genre: {song['genre']}  |  Mood: {song['mood']}  |  Energy: {song['energy']}")
        print(f"     Score : {score:.2f}")
        print(f"     Reasons: {explanation}")
        print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}\n")

    # ------------------------------------------------------------------
    # Standard profiles
    # ------------------------------------------------------------------
    standard_profiles = [
        ("High-Energy Pop",    {"genre": "pop",   "mood": "happy",   "energy": 0.85}),
        ("Chill Lofi",         {"genre": "lofi",  "mood": "chill",   "energy": 0.38}),
        ("Deep Intense Rock",  {"genre": "rock",  "mood": "intense", "energy": 0.91}),
    ]

    # ------------------------------------------------------------------
    # Adversarial / edge-case profiles
    # ------------------------------------------------------------------
    adversarial_profiles = [
        # Conflicting: user says peaceful but requests near-max energy
        ("EDGE — Peaceful but High-Energy",
         {"genre": "ambient", "mood": "peaceful", "energy": 0.95}),
        # Rare genre: only 1 metal song in catalog
        ("EDGE — Metal / Angry",
         {"genre": "metal",   "mood": "angry",    "energy": 0.97}),
        # Mid-energy neutral: no strong categorical signal should dominate
        ("EDGE — Mid-Energy Jazz",
         {"genre": "jazz",    "mood": "relaxed",  "energy": 0.50}),
    ]

    print("\n" + "#" * 60)
    print("  STANDARD PROFILES")
    print("#" * 60 + "\n")
    for label, prefs in standard_profiles:
        print_profile_header(label, prefs)
        recs = recommend_songs(prefs, songs, k=5)
        print_recommendations(recs)

    print("\n" + "#" * 60)
    print("  ADVERSARIAL / EDGE-CASE PROFILES")
    print("#" * 60 + "\n")
    for label, prefs in adversarial_profiles:
        print_profile_header(label, prefs)
        recs = recommend_songs(prefs, songs, k=5)
        print_recommendations(recs)

    # ------------------------------------------------------------------
    # Experiment: halve genre weight, double energy weight
    # ------------------------------------------------------------------
    print("\n" + "#" * 60)
    print("  EXPERIMENT — genre ×0.5, energy ×2.0  (High-Energy Pop profile)")
    print("#" * 60 + "\n")
    exp_prefs = {"genre": "pop", "mood": "happy", "energy": 0.85}
    print_profile_header("High-Energy Pop (Experimental Weights)", exp_prefs)
    exp_recs = recommend_experiment(exp_prefs, songs, k=5)
    print_recommendations(exp_recs)

    print("\n--- Baseline (original weights) for comparison ---\n")
    print_profile_header("High-Energy Pop (Original Weights)", exp_prefs)
    base_recs = recommend_songs(exp_prefs, songs, k=5)
    print_recommendations(base_recs)


if __name__ == "__main__":
    main()
