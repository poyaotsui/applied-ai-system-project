# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeFinder 1.0**

---

## 2. Intended Use

VibeFinder suggests up to 5 songs from an 18-song catalog based on a user's preferred genre, mood, and energy level. It is designed for classroom exploration — not for real users or production deployment. It assumes the user can express their taste as a small set of explicit preferences (a genre label, a mood label, and a target intensity value), and that those preferences are stable across a session.

---

## 3. How the Model Works

Think of the recommender as a judge at a talent competition who scores each contestant on three categories: genre, mood, and energy. The judge awards 2 points when a song's genre exactly matches what the user said they like, and 1.5 points when the mood matches. For energy, the judge doesn't just ask "is it energetic?" — they ask "is it as energetic as the user wants?" A song at energy 0.82 scores nearly full marks against a user who wants 0.8, while a song at 0.3 scores poorly. There is also a small bonus for songs that are positive and upbeat (called valence), and for acoustic-sounding tracks when the user prefers that feel.

Once every song has a score, the system simply sorts the list from highest to lowest and returns the top results. There is no learning, no memory of what the user liked before, and no awareness of other listeners.

---

## 4. Data

- **Catalog size**: 18 songs across 9 genres and 10 moods
- **Genres represented**: pop, lofi, rock, ambient, synthwave, jazz, indie pop, hip-hop, classical, r&b, country, electronic, metal, soul, reggae (15 distinct genres in 18 rows — most appear only once)
- **Moods represented**: happy, chill, intense, relaxed, focused, moody, energetic, peaceful, romantic, nostalgic, melancholic, angry
- **Changes made**: 8 songs were added to the original 10-song starter file to increase genre and mood diversity
- **Missing representation**: no songs in languages other than English, no non-Western genres, no collaborative signals (playlists, skips, likes) — the dataset reflects a single curator's taste rather than a broad population

---

## 5. Strengths

- **Works well for common genre+mood combinations**: The High-Energy Pop profile correctly surfaced a pop/happy/high-energy song as #1 (score 4.89) and a pop/intense song as #2 (score 3.31). Results matched intuition immediately.
- **Handles rare genres gracefully at rank 1**: Even with only one metal song in the catalog, the Metal/Angry profile correctly placed it at #1 with a near-perfect score of 4.65.
- **Energy proximity produces meaningful separation**: The scoring correctly distinguished Sunrise City (energy 0.82, near target 0.85) from a more distant song — not just "high energy vs low energy" but "how far from exactly what the user wants."
- **Transparent and explainable**: Every recommendation comes with a labeled reason string showing exactly which features contributed and how many points each earned.

---

## 6. Limitations and Bias

### Categorical bonus can override energy logic entirely

The most revealing test was the adversarial profile "Peaceful but High-Energy" (ambient genre, peaceful mood, energy target 0.95). The system ranked Spacewalk Thoughts first — a song with energy 0.28 — because its genre matched (ambient, +2.0 pts). The user's stated energy preference of 0.95 was almost completely ignored: the genre bonus alone was large enough to pull an energetically incompatible song to the top. This is a concrete example of how a high categorical weight can mask a severe numerical mismatch.

### Rare genres create hollow recommendation lists

Both the Metal/Angry and Mid-Energy Jazz profiles expose this: with only one song per genre, positions 2–5 fill with whatever songs are closest in energy regardless of genre or mood. The metal user's slots 2–5 are Gym Hero (pop/intense), Sunrise City (pop/happy), Rooftop Lights (indie pop/happy), and Concrete Jungle (hip-hop/energetic) — all very different from metal. A real user would likely consider these irrelevant.

### Valence boost skews against users who prefer low-energy or melancholic music

The system always awards a small bonus for songs with high valence (positivity/happiness). A user profile that asks for "melancholic" or "moody" music is still penalized by this hidden preference for upbeat songs. There is currently no way for a user to express that they prefer low-valence tracks.

### The system cannot distinguish within a category

"Intense rock" and "intense pop" both earn the same mood bonus. The genre label is the only separator — tempo, time signature, and instrumentation are invisible. A song at 180 BPM (Ironclad) and a song at 90 BPM (Coffee Shop Stories) receive the same treatment as long as their genre labels match, even though they would feel completely different to a listener.

---

## 7. Evaluation

### Profiles tested

| Profile | Top Result | Score | Surprising? |
|---|---|---|---|
| High-Energy Pop | Sunrise City (pop/happy/0.82) | 4.89 | No — expected |
| Chill Lofi | Library Rain (lofi/chill/0.35) | 4.77 | No — expected |
| Deep Intense Rock | Storm Runner (rock/intense/0.91) | 4.74 | No — expected |
| EDGE: Peaceful + High-Energy | Spacewalk Thoughts (ambient/chill/0.28) | 2.66 | **Yes** — genre won over energy |
| EDGE: Metal/Angry | Ironclad (metal/angry/0.97) | 4.65 | No (rank 1 fine, ranks 2–5 are weak) |
| EDGE: Mid-Energy Jazz | Coffee Shop Stories (jazz/relaxed/0.37) | 4.72 | No — only jazz song in catalog |

### What the experiment revealed

A weight-shift experiment was run on the High-Energy Pop profile: genre weight halved from 2.0 → 1.0, energy weight doubled from 1.0 → 2.0.

**Baseline order**: Sunrise City → Gym Hero → Rooftop Lights → Concrete Jungle → Storm Runner

**Experimental order**: Sunrise City → Rooftop Lights → Gym Hero → Concrete Jungle → Storm Runner

Rooftop Lights (indie pop/happy/0.76) jumped from #3 to #2, displacing Gym Hero (pop/intense/0.93). With a smaller genre bonus, Gym Hero's exact-genre advantage shrank enough that Rooftop Lights' mood match + energy proximity combination could beat it. This actually felt more intuitive: a user who wants "happy pop" probably prefers the mood match over the genre match when comparing a pop/intense to an indie-pop/happy song. Halving the genre weight produced recommendations that better reflected the emotional intent of the profile.

### Why "Gym Hero" keeps showing up for Happy Pop users

Gym Hero is a pop song. The genre bonus (+2.0) fires for both Sunrise City and Gym Hero — and since genre is the heaviest weight in the scoring recipe, it guarantees Gym Hero lands in the top two almost every time a pop user is tested, even though its mood is "intense" rather than "happy." Think of it like a bakery recommending a sourdough loaf and a rye loaf to someone who just said they like bread — both are bread (genre match), but only one is the fluffy white loaf they actually had in mind. The system sees "bread" but not "fluffy white."

---

## 8. Future Work

- **Add a `target_tempo` field to UserProfile** to make tempo a scored feature; this would correctly separate fast metal from slow jazz even if their energy scores are similar
- **Normalize catalog size across genres** so rare genres don't force hollow fallback recommendations
- **Add a `valence_preference` field** (low/medium/high) so melancholic users are not silently penalized
- **Implement diversity enforcement**: after selecting the top k songs, check that no single genre appears more than twice, preventing genre lock-in for common genres like pop
- **Move beyond explicit profiles**: collect implicit signals (a "thumbs up/down" after each recommendation) and adjust weights between sessions

---

## 9. Personal Reflection

Building this simulation made it clear why real recommenders use hybrid approaches — content-based filtering alone hits a ceiling as soon as the catalog gets small or a user's preferences conflict with each other. The most instructive moment was the "Peaceful but High-Energy" adversarial profile: a single genre match worth 2.0 points completely overrode an energy preference that would have placed the top song last if only energy were scored. This kind of invisible dominance is exactly how real recommendation systems develop filter bubbles without anyone intending to build one. The math is working correctly; the problem is in the weights, and the weights reflect the designer's assumptions about what matters most to a listener.
