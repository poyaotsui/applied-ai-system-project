# AI Music Curator

A conversational music recommendation system that combines **Retrieval-Augmented Generation (RAG)** and an **agentic Claude workflow** to turn natural-language requests into curated playlists grounded in a real song catalog.

> Built as an evolution of *VibeFinder 1.0* (Modules 1–3), this project upgrades a rule-based scoring engine into a full AI pipeline with tool use, structured logging, and a reliability test suite.

---

## Table of Contents

1. [Origin: VibeFinder 1.0](#origin-vibefinder-10)
2. [What This Project Does](#what-this-project-does)
3. [Architecture Overview](#architecture-overview)
4. [Setup Instructions](#setup-instructions)
5. [Sample Interactions](#sample-interactions)
6. [Design Decisions](#design-decisions)
7. [Testing Summary](#testing-summary)
8. [Reflection](#reflection)

---

## Origin: VibeFinder 1.0

**Original project:** [ai110-module3show-musicrecommendersimulation-starter](https://github.com/poyaotsui/ai110-module3show-musicrecommendersimulation-starter)

VibeFinder 1.0 was a pure content-based recommender built during Modules 1–3. Given a user's declared genre, mood, and target energy level, it scored every song in an 18-song CSV catalog using a weighted point system (genre match +2.0, mood match +1.5, energy proximity up to +1.0) and returned the top five by rank. The system had no AI layer — every recommendation was deterministic math. Its main value was demonstrating how weighted scoring rules and edge-case testing reveal hidden biases: a 2.0 genre weight was strong enough to return a song with 0.67 energy mismatch as the top result for an adversarial "peaceful but high-energy" profile.

This project replaces the rigid profile format with natural-language input and routes all recommendations through a live Claude model — while keeping the same 18-song catalog as the RAG knowledge base.

---

## What This Project Does

The AI Music Curator accepts free-form requests like *"something to study to late at night"* or *"high-energy workout songs"* and returns a curated playlist with per-song explanations. It matters because:

- It shows how RAG prevents hallucination: Claude is **required** to search the catalog before naming any song.
- It demonstrates a practical agentic loop: Claude can refine its search strategy across multiple tool calls within one conversation turn.
- It produces auditable, logged output — every tool call and API response is written to `logs/curator.log`.

```
User (plain English)
    ↓
Input Guardrails       ← rejects empty / oversized input before any API call
    ↓
Claude (claude-sonnet-4-6)  ← reasons about what to search for
    ↓  tool_use call
search_music_catalog   ← filters data/songs.csv by genre, mood, energy range
    ↓  JSON results
Claude (may search again)   ← grounds its answer in real catalog entries
    ↓
Curated Playlist       ← 3–5 songs with explanations, reviewed by human
```

---

## Architecture Overview

![System Architecture](assets/system-architecture.png)

> If the image above has not been exported yet, see [`assets/system-diagram.md`](assets/system-diagram.md) for the Mermaid source — paste it into [mermaid.live](https://mermaid.live) to render and export as PNG.

The system has five layers:

| Layer | Files | Role |
|---|---|---|
| **Input** | `src/ai_curator.py` → `validate_input()` | Sanitises and length-checks the user's request before any API call |
| **Agentic Loop** | `src/ai_curator.py` → `MusicCuratorAgent` | Runs a Claude conversation with tool use; loops until `stop_reason == end_turn` or the 6-iteration safety cap is hit |
| **RAG Retrieval** | `src/rag.py` → `search_catalog()` | Filters `data/songs.csv` by genre, mood, and energy range; returns ranked JSON the model uses as grounding context |
| **Logging** | `src/logger_setup.py` | Writes every request, tool call, and API response to `logs/curator.log` |
| **Reliability** | `tests/test_reliability.py` | 23 unit tests (offline) + 4 integration tests (live API); covers RAG logic, guardrails, and mocked agent behaviour |

The rule-based simulation from Module 3 is preserved behind the `--simulate` flag so the two approaches can be compared side by side.

---

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- An Anthropic API key ([get one here](https://console.anthropic.com/))

### Steps

**1. Clone the repo**

```bash
git clone https://github.com/poyaotsui/applied-ai-system-project.git
cd applied-ai-system-project
```

**2. Create and activate a virtual environment** (recommended)

```bash
# macOS / Linux
python -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Add your API key**

```bash
cp .env.example .env
# Open .env and replace "your_api_key_here" with your actual key
```

**5. Run the AI curator**

```bash
python -m src.main
```

**6. (Optional) Run the rule-based simulation — no API key needed**

```bash
python -m src.main --simulate
```

**7. Run the test suite**

```bash
# Offline unit tests only (no API key required)
pytest tests/ -v -m "not integration"

# All tests including live API calls
pytest tests/ -v
```

---

## Sample Interactions

### AI Curator Mode

**Example 1 — Late-night study session**

```
You: something chill and low-energy to study to late at night

Curator: searching catalog...

Curator:
Here are three tracks that should keep you focused without pulling
your attention away:

1. **Library Rain** — Paper Lanterns
   Lofi / chill / energy 0.35. One of the quietest tracks in the catalog,
   with high acousticness (0.86) and a slow 72 BPM tempo. Exactly the kind
   of background texture that stays out of the way.

2. **Midnight Coding** — LoRoom
   Lofi / chill / energy 0.42. A slightly busier beat than Library Rain but
   still firmly in low-energy territory. The "chill" mood tag and focused
   production make it a strong pair with late-night work.

3. **Focus Flow** — LoRoom
   Lofi / focused / energy 0.40. The mood label says it all — this track is
   specifically tagged "focused," which puts it a step ahead of general
   chill music when concentration matters.
```

---

**Example 2 — High-energy workout**

```
You: I need something aggressive and high-energy for lifting weights

Curator: searching catalog...

Curator:
These three tracks sit at the high-energy, intense end of the catalog:

1. **Ironclad** — The Riven
   Metal / angry / energy 0.97, tempo 180 BPM. The hardest track in the
   catalog — if you want aggression, this is the ceiling.

2. **Storm Runner** — Voltline
   Rock / intense / energy 0.91, tempo 152 BPM. Slightly more melodic than
   Ironclad but still built for momentum. Good if you want intensity without
   pure metal.

3. **Concrete Jungle** — Phantom Bloc
   Hip-hop / energetic / energy 0.85, danceability 0.91. Brings a rhythmic
   drive that pairs well with repetitive movement — different energy shape
   than rock but equally high output.
```

---

**Example 3 — Quiet Sunday morning**

```
You: peaceful acoustic music for a slow Sunday morning with coffee

Curator: searching catalog...

Curator:
Here are three tracks that fit a slow, acoustic Sunday:

1. **Moonlight Reimagined** — Nova Strings
   Classical / peaceful / energy 0.20, acousticness 0.97. The quietest,
   most acoustic track in the catalog — nearly no percussion, very high
   emotional warmth from the valence score (0.72).

2. **Coffee Shop Stories** — Slow Stereo
   Jazz / relaxed / energy 0.37, acousticness 0.89. Low tempo (90 BPM),
   relaxed mood, and high acousticness. Basically named for this situation.

3. **Island Drift** — Coastal Roots
   Reggae / peaceful / energy 0.48. A little more movement than the first
   two but still peaceful in mood, with a warm valence (0.79) that suits
   a comfortable morning.
```

---

### Rule-Based Simulation Mode (`--simulate`)

The original VibeFinder 1.0 algorithm, run with a Chill Lofi profile:

```
============================================================
  Profile : Chill Lofi
  Genre   : lofi  |  Mood: chill  |  Energy: 0.38
============================================================
  1. Library Rain  —  Paper Lanterns
     Genre: lofi  |  Mood: chill  |  Energy: 0.35
     Score  : 4.77
     Reasons: genre match (+2.0), mood match (+1.5), energy proximity (+0.97), valence boost (+0.30)

  2. Midnight Coding  —  LoRoom
     Genre: lofi  |  Mood: chill  |  Energy: 0.42
     Score  : 4.74
     Reasons: genre match (+2.0), mood match (+1.5), energy proximity (+0.96), valence boost (+0.28)

  3. Focus Flow  —  LoRoom
     Genre: lofi  |  Mood: focused  |  Energy: 0.40
     Score  : 3.27
     Reasons: genre match (+2.0), energy proximity (+0.98), valence boost (+0.29)
```

Notice how Example 1 (AI mode) and this simulation reach the same top-3 songs via completely different paths: the simulation uses exact scoring math; the AI translates "late-night studying" into a catalog search and arrives at the same result through language understanding.

---

## Design Decisions

### Why RAG instead of embedding all songs into the prompt?

At 18 songs the catalog is small enough to fit in one prompt — but that approach does not scale and gives the model no structured way to filter. By exposing a `search_music_catalog` tool, Claude is forced to commit to specific parameters (genre, mood, energy range) before receiving results. This produces auditable queries in the log and prevents the model from mixing retrieved data with training-set knowledge. It also means the catalog can grow to thousands of songs without changing the architecture.

### Why tool use instead of a chain-of-thought prompt?

A chain-of-thought approach would ask Claude to reason about the catalog in its head and name songs from memory. Since Claude was not trained on this specific catalog, that would produce hallucinated titles. Tool use enforces the RAG contract: Claude **cannot** name a song it has not retrieved. If no search is called, no recommendation is written.

### Why keep the Module 3 simulation?

The `--simulate` flag preserves the deterministic baseline so the two systems can be directly compared. The simulation reveals what the AI curator is actually adding: the ability to understand natural language intent ("late-night focus session") rather than requiring the user to know that they want `genre=lofi, mood=chill, energy=0.38`.

### Trade-offs made

| Decision | Benefit | Cost |
|---|---|---|
| Keyword-based retrieval (no vector embeddings) | Zero extra dependencies, fully reproducible | Cannot match semantic synonyms — "dark" will not find "melancholic" unless the user uses the exact catalog mood label |
| 6-iteration safety cap on the agentic loop | Prevents runaway API spend | In theory, a very complex request could need more searches than the cap allows |
| Input capped at 500 characters | Prevents prompt injection and runaway token costs | Users cannot paste long song descriptions |
| No conversation history between turns | Keeps the system stateless and easy to test | Each request is independent — the curator does not remember what it recommended last |

---

## Testing Summary

### What the tests cover

The test suite in [`tests/test_reliability.py`](tests/test_reliability.py) has two layers:

**Unit tests (23 tests, no API key required)**

| Class | What it checks |
|---|---|
| `TestSearchCatalog` | RAG filter logic: genre, mood, energy range, limit, unknown values, inverted ranges, sort order |
| `TestValidateInput` | Guardrails: empty string, whitespace, over-limit length, exact-limit edge case |
| `TestMusicCuratorAgentMocked` | Agent behaviour with a mocked API: returns a string, dispatches tool calls, rejects missing key, blocks bad input before any API call, handles unknown tool names |

**Integration tests (4 tests, requires `ANTHROPIC_API_KEY`)**

These call the live API and verify: non-empty response, at least one real song title appears in the output (grounding check), smoke-test consistency across two identical requests, and that the empty-input guardrail still fires before the API call.

```bash
# Run offline tests
pytest tests/ -v -m "not integration"   # 23 passed

# Run everything (needs API key)
pytest tests/ -v                         # 27 tests
```

### What worked

- The mocked agent tests were the most valuable during development: they let every code path be exercised without spending API credits and caught two bugs in the tool dispatch loop before any live call was made.
- The RAG sort-order test (`test_results_sorted_by_energy_proximity`) caught a one-line off-by-one error in the proximity calculation that would have silently returned worse results.
- The grounding integration test (`test_integration_mentions_real_song_title`) is the most important correctness check: it verifies the system's core promise that Claude's answers reference real catalog entries.

### What didn't work / limitations

- The integration consistency test is a smoke test, not a strict assertion — it checks that both responses are non-empty but not that they return the same songs. True consistency testing would require comparing structured output (song IDs), which would need the agent to return JSON instead of prose.
- The unit tests mock the Anthropic client at the `create` method level, which means changes to how `anthropic` structures its response objects (e.g., after an SDK upgrade) could silently pass all mocks while breaking in production.
- There is no test for the logging system itself — it is verified manually by inspecting `logs/curator.log` after a run.

---

## Reflection

### What this project taught me about AI

The gap between VibeFinder 1.0 and this system is one key insight: **the hard part of recommendation is not the ranking, it is understanding what the user actually wants.** The rule-based system required users to know they wanted `genre=lofi, mood=chill, energy=0.38`. Almost no real user thinks that way. The AI layer does the translation work — converting "I want something to study to" into structured query parameters — and that translation is where language models add the most value over traditional algorithms.

The RAG architecture also clarified something about hallucination that abstract explanations do not: the problem is not that the model lies on purpose, it is that it has no reliable mechanism to distinguish "things I was trained on" from "things in this specific catalog." Making retrieval a required step — not an optional enrichment — is the only architectural fix that actually prevents the problem rather than hoping the model gets it right.

### What this project taught me about problem-solving

Building the test suite before running the agent against the live API forced precision about what "correct" means. The grounding test — does the response contain a real song title? — is obvious in retrospect, but writing it first required deciding what the system's core contract was. That contract (Claude must retrieve before it recommends) shaped every other decision: the system prompt, the tool definition, the iteration cap.

The biggest trade-off I would revisit is the prose output format. Having Claude write natural-language explanations is friendly to read but makes automated quality checks fragile — you cannot easily parse "energy level suits a late-night focus session" back into a structured score. A production version of this system would have the agent return a JSON object (song IDs + rationale strings) and render the prose separately, keeping the recommendation logic testable and the presentation layer flexible.

---

## Project Structure

```
applied-ai-system-project/
├── data/
│   └── songs.csv              # 18-song catalog (9 features per song)
├── src/
│   ├── ai_curator.py          # MusicCuratorAgent — agentic RAG loop
│   ├── rag.py                 # search_catalog() — RAG retrieval layer
│   ├── logger_setup.py        # Centralised logging to logs/curator.log
│   ├── recommender.py         # VibeFinder 1.0 scoring engine (Module 3)
│   └── main.py                # CLI entry point (AI mode + --simulate)
├── tests/
│   ├── test_recommender.py    # Module 3 unit tests
│   └── test_reliability.py    # 23 unit + 4 integration tests
├── assets/
│   └── system-diagram.md      # Mermaid source for architecture diagram
├── logs/                      # Runtime logs (git-ignored)
├── model_card.md              # VibeFinder 1.0 model card
├── pytest.ini
├── requirements.txt
└── .env.example
```

---

## Requirements

```
anthropic>=0.40.0
python-dotenv>=1.0.0
pytest>=8.0.0
```
