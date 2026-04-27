"""
AI Music Curator — agentic RAG workflow powered by Claude.

Workflow (one conversation turn):
  1. Claude reads the user's natural-language request.
  2. Claude decides what to search for and calls search_music_catalog (tool use).
  3. The tool runs search_catalog() against the real songs CSV (RAG retrieval).
  4. Claude receives the retrieved songs as grounded context.
  5. Claude may search again with different parameters if needed.
  6. Claude writes a final curated playlist with explanations.

The agent loop continues until Claude stops calling tools (stop_reason == "end_turn")
or the safety iteration cap is reached.
"""

from __future__ import annotations
import json
import logging
import os
from typing import Any

import anthropic

from src.rag import search_catalog, KNOWN_GENRES, KNOWN_MOODS

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1024
MAX_ITERATIONS = 6  # safety cap on the agentic loop

# ---------------------------------------------------------------------------
# Tool definition — this is what Claude sees
# ---------------------------------------------------------------------------
TOOLS: list[dict[str, Any]] = [
    {
        "name": "search_music_catalog",
        "description": (
            "Search the music catalog for songs that match specific criteria. "
            "Always call this tool one or more times before writing your final recommendations — "
            "never invent or guess song titles. "
            f"Available genres: {', '.join(sorted(KNOWN_GENRES))}. "
            f"Available moods: {', '.join(sorted(KNOWN_MOODS))}."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "genre": {
                    "type": "string",
                    "description": "Music genre to filter by (optional).",
                },
                "mood": {
                    "type": "string",
                    "description": "Song mood to filter by (optional).",
                },
                "energy_min": {
                    "type": "number",
                    "description": "Minimum energy level 0.0–1.0 (default 0.0).",
                },
                "energy_max": {
                    "type": "number",
                    "description": "Maximum energy level 0.0–1.0 (default 1.0).",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of songs to return (default 5, max 10).",
                },
            },
            "required": [],
        },
    }
]

SYSTEM_PROMPT = """\
You are a knowledgeable music curator AI. Your job is to recommend songs from a \
real catalog based on what the user describes.

Rules you must follow:
1. ALWAYS call search_music_catalog at least once before writing recommendations.
2. Only recommend songs that appeared in search results — never invent titles.
3. You may call the tool multiple times with different parameters to broaden or \
   refine results (e.g. first by genre, then by mood).
4. In your final answer, list 3–5 songs. For each, state the title, artist, and \
   one sentence explaining why it fits the user's request.
5. If no songs match at all, say so honestly and suggest what the user could try instead.
"""


# ---------------------------------------------------------------------------
# Guardrails
# ---------------------------------------------------------------------------
MAX_INPUT_CHARS = 500

def validate_input(text: str) -> str:
    """Raise ValueError with a user-friendly message if input is unsafe/empty."""
    text = text.strip()
    if not text:
        raise ValueError("Please describe what kind of music you're looking for.")
    if len(text) > MAX_INPUT_CHARS:
        raise ValueError(
            f"Request too long ({len(text)} chars). Keep it under {MAX_INPUT_CHARS} characters."
        )
    return text


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------
class MusicCuratorAgent:
    """Stateless agent — create once, call .curate() many times."""

    def __init__(self, songs: list[dict], model: str = MODEL) -> None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY is not set. "
                "Copy .env.example to .env and add your key."
            )
        self.client = anthropic.Anthropic(api_key=api_key)
        self.songs = songs
        self.model = model
        logger.info("MusicCuratorAgent ready | model=%s | catalog_size=%d", model, len(songs))

    # ------------------------------------------------------------------
    # Tool dispatch
    # ------------------------------------------------------------------
    def _run_tool(self, name: str, tool_input: dict) -> str:
        if name == "search_music_catalog":
            results = search_catalog(
                self.songs,
                genre=tool_input.get("genre"),
                mood=tool_input.get("mood"),
                energy_min=tool_input.get("energy_min", 0.0),
                energy_max=tool_input.get("energy_max", 1.0),
                limit=min(tool_input.get("limit", 5), 10),
            )
            logger.info(
                "Tool call: search_music_catalog(%s) → %d results",
                json.dumps(tool_input, separators=(",", ":")),
                len(results),
            )
            if not results:
                return json.dumps({"songs": [], "note": "No songs matched these criteria."})
            return json.dumps({"songs": results})
        raise ValueError(f"Unknown tool: {name!r}")

    # ------------------------------------------------------------------
    # Agentic loop
    # ------------------------------------------------------------------
    def curate(self, user_request: str) -> str:
        """
        Run the full agentic RAG workflow and return the curator's final answer.

        Raises ValueError for bad input, anthropic.APIError on API failures.
        """
        user_request = validate_input(user_request)
        logger.info("Curation request: %r", user_request)

        messages: list[dict] = [{"role": "user", "content": user_request}]
        tool_call_count = 0

        for iteration in range(MAX_ITERATIONS):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )
            logger.debug(
                "API response | iteration=%d stop_reason=%s usage=%s",
                iteration + 1,
                response.stop_reason,
                response.usage,
            )

            # Separate text blocks from tool-use blocks
            tool_uses = [b for b in response.content if b.type == "tool_use"]
            text_parts = [b.text for b in response.content if b.type == "text"]

            # If Claude is done, return its final text
            if response.stop_reason == "end_turn":
                final = "\n".join(text_parts).strip()
                logger.info(
                    "Curation complete | iterations=%d tool_calls=%d chars=%d",
                    iteration + 1,
                    tool_call_count,
                    len(final),
                )
                return final

            # Process tool calls and loop back
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for tu in tool_uses:
                tool_call_count += 1
                result_content = self._run_tool(tu.name, tu.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tu.id,
                    "content": result_content,
                })
            messages.append({"role": "user", "content": tool_results})

        logger.warning("Iteration cap (%d) reached without end_turn", MAX_ITERATIONS)
        return (
            "I searched the catalog but couldn't finish building your playlist. "
            "Please try rephrasing your request."
        )
