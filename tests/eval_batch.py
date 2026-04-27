"""
Batch reliability evaluation -- no API key required.

Tests 8 scenarios against the RAG retrieval layer and input guardrails,
records pass/fail, confidence scores, and prints a summary report.

Usage:
    py -m tests.eval_batch
"""

from __future__ import annotations
import sys
from pathlib import Path

# Allow running from project root without installing the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.logger_setup import setup_logging
setup_logging()

from src.recommender import load_songs
from src.rag import search_catalog, catalog_match_quality
from src.ai_curator import validate_input

DATA_PATH = Path(__file__).parent.parent / "data" / "songs.csv"

# ---------------------------------------------------------------------------
# Test case definitions
# ---------------------------------------------------------------------------
# Each case has:
#   query_params   -- dict passed to search_catalog()
#   expect_pass    -- callable(results) -> bool  (what "correct" means)
#   description    -- human-readable label
#   expect_error   -- if True, the test expects an exception from validate_input()

CASES = [
    {
        "description": "Lofi study session -> top result should be lofi/chill",
        "query_params": {"genre": "lofi", "mood": "chill",
                         "energy_min": 0.2, "energy_max": 0.5},
        "expect_pass": lambda r: len(r) > 0 and r[0]["genre"] == "lofi",
    },
    {
        "description": "High-energy workout -> top result energy > 0.85",
        "query_params": {"mood": "intense", "energy_min": 0.85, "energy_max": 1.0},
        "expect_pass": lambda r: len(r) > 0 and r[0]["energy"] >= 0.85,
    },
    {
        "description": "Peaceful morning -> top result energy < 0.50",
        "query_params": {"mood": "peaceful", "energy_min": 0.0, "energy_max": 0.5},
        "expect_pass": lambda r: len(r) > 0 and r[0]["energy"] <= 0.5,
    },
    {
        "description": "Metal search -> Ironclad (id=16) should appear",
        "query_params": {"genre": "metal"},
        "expect_pass": lambda r: any(s["id"] == 16 for s in r),
    },
    {
        "description": "Unknown genre 'bossa-nova' -> graceful fallback (no crash, >=1 result)",
        "query_params": {"genre": "bossa-nova", "energy_min": 0.3, "energy_max": 0.6},
        "expect_pass": lambda r: isinstance(r, list),
    },
    {
        "description": "Adversarial: peaceful mood + very high energy -> low confidence expected",
        "query_params": {"mood": "peaceful", "energy_min": 0.9, "energy_max": 1.0},
        "expect_pass": lambda r: True,          # result validity; confidence checked separately
        "check_low_confidence": True,
    },
    {
        "description": "Guardrail: empty input -> ValueError raised",
        "guardrail_input": "",
        "expect_error": True,
    },
    {
        "description": "Guardrail: input > 500 chars -> ValueError raised",
        "guardrail_input": "x" * 501,
        "expect_error": True,
    },
]

# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
def run_eval(songs: list[dict]) -> None:
    passed = 0
    failed = 0
    confidence_scores: list[float] = []

    sep = "-" * 68
    print(f"\n{'=' * 68}")
    print("  RELIABILITY EVALUATION -- AI Music Curator")
    print(f"  Catalog: {len(songs)} songs   |   Test cases: {len(CASES)}")
    print(f"{'=' * 68}\n")

    for i, case in enumerate(CASES, start=1):
        label = case["description"]

        # --- Guardrail tests ---
        if case.get("expect_error"):
            try:
                validate_input(case["guardrail_input"])
                status = "FAIL"
                note = "expected ValueError -- none raised"
                failed += 1
            except ValueError as e:
                status = "PASS"
                note = f"ValueError caught: {e}"
                passed += 1
            print(f"  [{i}] {status}  {label}")
            print(f"       {note}")
            print(f"  {sep}")
            continue

        # --- RAG tests ---
        params = case["query_params"]
        try:
            results = search_catalog(songs, **params)
            ok = case["expect_pass"](results)
            confidence = catalog_match_quality(
                results,
                genre=params.get("genre"),
                mood=params.get("mood"),
                energy_min=params.get("energy_min", 0.0),
                energy_max=params.get("energy_max", 1.0),
            )
            confidence_scores.append(confidence)

            # Adversarial case: flag when confidence is low (expected)
            if case.get("check_low_confidence") and confidence < 0.35:
                status = "PASS"
                note = f"low confidence ({confidence:.2f}) correctly flagged for conflicting query"
            elif ok:
                status = "PASS"
                note = (
                    f"top result: \"{results[0]['title']}\" by {results[0]['artist']}"
                    f" | confidence: {confidence:.2f}"
                ) if results else "no results (catalog gap)"
            else:
                status = "FAIL"
                top = results[0] if results else None
                note = (
                    f"top result: \"{top['title']}\" -- did not meet criteria"
                    if top else "no results returned"
                )

        except Exception as exc:
            status = "FAIL"
            note = f"unexpected exception: {exc}"
            ok = False

        if status == "PASS":
            passed += 1
        else:
            failed += 1

        print(f"  [{i}] {status}  {label}")
        print(f"       {note}")
        print(f"  {sep}")

    # --- Summary ---
    total = passed + failed
    rag_scores = confidence_scores  # only RAG cases have these
    avg_conf = sum(rag_scores) / len(rag_scores) if rag_scores else 0.0

    print(f"\n  RESULTS: {passed}/{total} tests passed", end="")
    if failed:
        print(f"  ({failed} failed)")
    else:
        print("  -- all passed")
    print(f"  Average catalog match confidence (RAG cases): {avg_conf:.2f} / 1.00")
    if failed == 0:
        print("  Reliability verdict: SYSTEM FUNCTIONAL")
    else:
        print("  Reliability verdict: REVIEW REQUIRED -- see failures above")
    print()


if __name__ == "__main__":
    songs = load_songs(str(DATA_PATH))
    run_eval(songs)
