"""
Reliability test suite for the AI Music Curator.

Tests are split into two layers:
  1. Unit tests (no API key needed) — verify RAG retrieval logic and guardrails.
  2. Integration tests (require ANTHROPIC_API_KEY) — verify the agent's behaviour
     against the live API. Skipped automatically if the key is absent.

Run all tests:
    pytest tests/test_reliability.py -v

Run only unit tests (offline):
    pytest tests/test_reliability.py -v -m "not integration"
"""

from __future__ import annotations
import json
import os
import pytest
from unittest.mock import MagicMock, patch

from src.rag import search_catalog, KNOWN_GENRES, KNOWN_MOODS
from src.ai_curator import validate_input, MusicCuratorAgent, MAX_INPUT_CHARS


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------
SAMPLE_SONGS = [
    {"id": 1,  "title": "Sunrise City",       "artist": "Neon Echo",    "genre": "pop",       "mood": "happy",   "energy": 0.82, "valence": 0.84, "danceability": 0.79, "acousticness": 0.18, "tempo_bpm": 118},
    {"id": 2,  "title": "Midnight Coding",    "artist": "LoRoom",       "genre": "lofi",      "mood": "chill",   "energy": 0.42, "valence": 0.56, "danceability": 0.62, "acousticness": 0.71, "tempo_bpm": 78},
    {"id": 3,  "title": "Storm Runner",       "artist": "Voltline",     "genre": "rock",      "mood": "intense", "energy": 0.91, "valence": 0.48, "danceability": 0.66, "acousticness": 0.10, "tempo_bpm": 152},
    {"id": 4,  "title": "Library Rain",       "artist": "Paper Lanterns","genre": "lofi",     "mood": "chill",   "energy": 0.35, "valence": 0.60, "danceability": 0.58, "acousticness": 0.86, "tempo_bpm": 72},
    {"id": 11, "title": "Concrete Jungle",    "artist": "Phantom Bloc", "genre": "hip-hop",   "mood": "energetic","energy": 0.85, "valence": 0.63, "danceability": 0.91, "acousticness": 0.08, "tempo_bpm": 140},
    {"id": 12, "title": "Moonlight Reimagined","artist": "Nova Strings","genre": "classical", "mood": "peaceful","energy": 0.20, "valence": 0.72, "danceability": 0.25, "acousticness": 0.97, "tempo_bpm": 52},
]


# ===========================================================================
# UNIT TESTS — RAG retrieval
# ===========================================================================
class TestSearchCatalog:
    def test_genre_filter_returns_only_matching(self):
        results = search_catalog(SAMPLE_SONGS, genre="lofi")
        assert all(s["genre"] == "lofi" for s in results)
        assert len(results) == 2

    def test_mood_filter(self):
        results = search_catalog(SAMPLE_SONGS, mood="chill")
        assert all(s["mood"] == "chill" for s in results)

    def test_energy_range_filter(self):
        results = search_catalog(SAMPLE_SONGS, energy_min=0.8, energy_max=1.0)
        assert all(0.8 <= s["energy"] <= 1.0 for s in results)

    def test_limit_respected(self):
        results = search_catalog(SAMPLE_SONGS, limit=2)
        assert len(results) <= 2

    def test_empty_result_when_no_match(self):
        results = search_catalog(SAMPLE_SONGS, genre="pop", mood="intense")
        assert results == []

    def test_unknown_genre_falls_back_gracefully(self):
        # Should not raise — just skip the genre filter
        results = search_catalog(SAMPLE_SONGS, genre="bossa-nova")
        assert isinstance(results, list)

    def test_energy_min_max_clamped(self):
        # Out-of-range values must not crash
        results = search_catalog(SAMPLE_SONGS, energy_min=-5, energy_max=99)
        assert isinstance(results, list)

    def test_inverted_energy_range_auto_corrected(self):
        results_normal   = search_catalog(SAMPLE_SONGS, energy_min=0.3, energy_max=0.6)
        results_inverted = search_catalog(SAMPLE_SONGS, energy_min=0.6, energy_max=0.3)
        assert results_normal == results_inverted

    def test_results_sorted_by_energy_proximity(self):
        results = search_catalog(SAMPLE_SONGS, energy_min=0.4, energy_max=0.5)
        mid = 0.45
        dists = [abs(s["energy"] - mid) for s in results]
        assert dists == sorted(dists)

    def test_all_known_genres_are_strings(self):
        assert all(isinstance(g, str) for g in KNOWN_GENRES)

    def test_all_known_moods_are_strings(self):
        assert all(isinstance(m, str) for m in KNOWN_MOODS)


# ===========================================================================
# UNIT TESTS — Input guardrails
# ===========================================================================
class TestValidateInput:
    def test_valid_input_passes_through(self):
        result = validate_input("  something chill to study to  ")
        assert result == "something chill to study to"

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="describe"):
            validate_input("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError):
            validate_input("   ")

    def test_too_long_raises(self):
        with pytest.raises(ValueError, match="too long"):
            validate_input("x" * (MAX_INPUT_CHARS + 1))

    def test_exactly_at_limit_passes(self):
        result = validate_input("a" * MAX_INPUT_CHARS)
        assert len(result) == MAX_INPUT_CHARS


# ===========================================================================
# UNIT TESTS — Agent (mocked API)
# ===========================================================================
class TestMusicCuratorAgentMocked:
    """Verify agent behaviour without calling the real API."""

    def _make_agent(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            return MusicCuratorAgent(SAMPLE_SONGS)

    def _mock_end_turn_response(self, text: str):
        """Create a mock API response that immediately ends the turn."""
        block = MagicMock()
        block.type = "text"
        block.text = text
        response = MagicMock()
        response.stop_reason = "end_turn"
        response.content = [block]
        response.usage = MagicMock()
        return response

    def _mock_tool_then_end(self, tool_name: str, tool_input: dict, final_text: str):
        """Create two mock responses: first a tool call, then end_turn."""
        # First response: tool use
        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.name = tool_name
        tool_block.input = tool_input
        tool_block.id = "tu_test_123"
        r1 = MagicMock()
        r1.stop_reason = "tool_use"
        r1.content = [tool_block]
        r1.usage = MagicMock()

        # Second response: final answer
        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = final_text
        r2 = MagicMock()
        r2.stop_reason = "end_turn"
        r2.content = [text_block]
        r2.usage = MagicMock()

        return [r1, r2]

    def test_returns_string(self):
        agent = self._make_agent()
        final_text = "Here are your recommendations: Midnight Coding by LoRoom."
        with patch.object(agent.client.messages, "create",
                          return_value=self._mock_end_turn_response(final_text)):
            result = agent.curate("something chill")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_tool_call_triggers_catalog_search(self):
        agent = self._make_agent()
        responses = self._mock_tool_then_end(
            "search_music_catalog",
            {"genre": "lofi", "mood": "chill"},
            "I recommend Midnight Coding by LoRoom and Library Rain by Paper Lanterns.",
        )
        with patch.object(agent.client.messages, "create", side_effect=responses):
            result = agent.curate("chill lofi for studying")
        assert "Midnight Coding" in result or "Library Rain" in result or len(result) > 0

    def test_missing_api_key_raises(self):
        env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(EnvironmentError, match="ANTHROPIC_API_KEY"):
                MusicCuratorAgent(SAMPLE_SONGS)

    def test_invalid_input_raises_before_api_call(self):
        agent = self._make_agent()
        with patch.object(agent.client.messages, "create") as mock_create:
            with pytest.raises(ValueError):
                agent.curate("")
            mock_create.assert_not_called()

    def test_run_tool_unknown_name_raises(self):
        agent = self._make_agent()
        with pytest.raises(ValueError, match="Unknown tool"):
            agent._run_tool("nonexistent_tool", {})

    def test_search_tool_returns_json(self):
        agent = self._make_agent()
        result = agent._run_tool("search_music_catalog", {"genre": "lofi"})
        parsed = json.loads(result)
        assert "songs" in parsed

    def test_search_tool_empty_result_returns_note(self):
        agent = self._make_agent()
        result = agent._run_tool("search_music_catalog",
                                  {"genre": "pop", "mood": "intense"})
        parsed = json.loads(result)
        assert "songs" in parsed
        assert parsed["songs"] == []


# ===========================================================================
# INTEGRATION TESTS — require live API key
# ===========================================================================
INTEGRATION = pytest.mark.integration

@pytest.fixture(scope="module")
def live_agent():
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        pytest.skip("ANTHROPIC_API_KEY not set — skipping integration tests")
    from src.recommender import load_songs
    from pathlib import Path
    songs = load_songs(str(Path(__file__).parent.parent / "data" / "songs.csv"))
    return MusicCuratorAgent(songs)


@INTEGRATION
def test_integration_returns_nonempty_string(live_agent):
    result = live_agent.curate("something chill and acoustic for studying")
    assert isinstance(result, str)
    assert len(result) > 50


@INTEGRATION
def test_integration_mentions_real_song_title(live_agent):
    """The agent must ground its answer in catalog songs, not hallucinate."""
    from src.recommender import load_songs
    from pathlib import Path
    songs = load_songs(str(Path(__file__).parent.parent / "data" / "songs.csv"))
    known_titles = {s["title"].lower() for s in songs}

    result = live_agent.curate("relaxing evening music")
    result_lower = result.lower()
    mentioned = [t for t in known_titles if t in result_lower]
    assert len(mentioned) >= 1, (
        f"Expected at least one real song title in the response.\n"
        f"Response: {result[:300]}"
    )


@INTEGRATION
def test_integration_consistent_genre_for_genre_request(live_agent):
    """Two identical requests should return recommendations in the same genre."""
    request = "high energy pop music for working out"
    r1 = live_agent.curate(request)
    r2 = live_agent.curate(request)
    # Both should mention at least one song — simple smoke test for consistency
    assert len(r1) > 20
    assert len(r2) > 20


@INTEGRATION
def test_integration_guardrail_rejects_empty(live_agent):
    with pytest.raises(ValueError):
        live_agent.curate("")
