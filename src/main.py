"""
Entry point for the AI Music Curator.

Usage
-----
Interactive AI mode (default):
    python -m src.main

Rule-based simulation mode (Module 3 baseline):
    python -m src.main --simulate

Setup
-----
1. Copy .env.example to .env and set ANTHROPIC_API_KEY.
2. pip install -r requirements.txt
3. Run from the project root directory.
"""

from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env before anything else so ANTHROPIC_API_KEY is available
load_dotenv()

from src.logger_setup import setup_logging
setup_logging()

from src.recommender import load_songs, recommend_songs, score_song
from src.ai_curator import MusicCuratorAgent

DATA_PATH = Path(__file__).parent.parent / "data" / "songs.csv"

# ---------------------------------------------------------------------------
# Simulation mode (Module 3 baseline — no Claude required)
# ---------------------------------------------------------------------------
def _print_profile_header(label: str, prefs: dict) -> None:
    print("=" * 60)
    print(f"  Profile : {label}")
    print(f"  Genre   : {prefs.get('genre', '—')}  |  "
          f"Mood: {prefs.get('mood', '—')}  |  "
          f"Energy: {prefs.get('energy', '—')}")
    print("=" * 60)


def _print_recommendations(recs: list) -> None:
    for rank, (song, score, explanation) in enumerate(recs, start=1):
        print(f"  {rank}. {song['title']}  —  {song['artist']}")
        print(f"     Genre: {song['genre']}  |  Mood: {song['mood']}  |  Energy: {song['energy']}")
        print(f"     Score  : {score:.2f}")
        print(f"     Reasons: {explanation}")
        print()


def run_simulation(songs: list) -> None:
    profiles = [
        ("High-Energy Pop",   {"genre": "pop",     "mood": "happy",   "energy": 0.85}),
        ("Chill Lofi",        {"genre": "lofi",    "mood": "chill",   "energy": 0.38}),
        ("Deep Intense Rock", {"genre": "rock",    "mood": "intense", "energy": 0.91}),
        ("EDGE — Metal/Angry",{"genre": "metal",   "mood": "angry",   "energy": 0.97}),
        ("EDGE — Mid Jazz",   {"genre": "jazz",    "mood": "relaxed", "energy": 0.50}),
    ]
    print(f"\nLoaded {len(songs)} songs from catalog.\n")
    for label, prefs in profiles:
        _print_profile_header(label, prefs)
        recs = recommend_songs(prefs, songs, k=5)
        _print_recommendations(recs)


# ---------------------------------------------------------------------------
# Interactive AI mode
# ---------------------------------------------------------------------------
BANNER = """
╔══════════════════════════════════════════════════════════╗
║            AI Music Curator  (type 'quit' to exit)       ║
║  Powered by Claude + RAG over a real song catalog        ║
╚══════════════════════════════════════════════════════════╝
Describe what you're looking for in plain English.
Examples:
  • "something chill to study to late at night"
  • "high-energy workout songs, preferably pop or hip-hop"
  • "peaceful acoustic music for a Sunday morning"
"""

def run_interactive(songs: list) -> None:
    try:
        agent = MusicCuratorAgent(songs)
    except EnvironmentError as e:
        print(f"\nSetup error: {e}\n")
        sys.exit(1)

    print(BANNER)

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if user_input.lower() in {"quit", "exit", "q"}:
            print("Goodbye!")
            break

        if not user_input:
            continue

        print("\nCurator: searching catalog...\n")
        try:
            result = agent.curate(user_input)
            print(f"Curator:\n{result}\n")
        except ValueError as e:
            print(f"Curator: {e}\n")
        except Exception as e:
            print(f"Curator: Something went wrong — {e}\n")
            print("Check logs/curator.log for details.\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="AI Music Curator")
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Run the rule-based simulation (no Claude API required).",
    )
    args = parser.parse_args()

    songs = load_songs(str(DATA_PATH))

    if args.simulate:
        run_simulation(songs)
    else:
        run_interactive(songs)


if __name__ == "__main__":
    main()
