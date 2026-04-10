"""
Command-line runner for the Music Recommender Simulation.

Run from the project root with:
    python -m src.main
"""

from src.recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}\n")

    # Default taste profile — change these to explore different results
    user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}

    print("=" * 50)
    print(f"  User profile")
    print(f"  Genre : {user_prefs['genre']}")
    print(f"  Mood  : {user_prefs['mood']}")
    print(f"  Energy: {user_prefs['energy']}")
    print("=" * 50)
    print()

    recommendations = recommend_songs(user_prefs, songs, k=5)

    print("Top recommendations:\n")
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"  {rank}. {song['title']}  —  {song['artist']}")
        print(f"     Genre: {song['genre']}  |  Mood: {song['mood']}  |  Energy: {song['energy']}")
        print(f"     Score : {score:.2f}")
        print(f"     Reasons: {explanation}")
        print()


if __name__ == "__main__":
    main()
