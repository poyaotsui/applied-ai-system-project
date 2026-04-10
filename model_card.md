# 🎧 Model Card: Music Recommender Simulation

---

## 1. Model Name

**VibeFinder 1.0**

---

## 2. Goal / Task

VibeFinder tries to predict which songs from a small catalog a specific user will enjoy next, based entirely on the user's stated taste preferences. Given a genre, a mood, and a target energy level, the system ranks every song in the catalog from most to least likely to match — and returns the top five.

It does not learn from behavior. It does not remember past sessions. It makes one prediction per run, based only on what the user tells it right now.

---

## 3. Data Used

| Detail | Value |
|---|---|
| Total songs | 18 |
| Original starter songs | 10 |
| Songs added during the project | 8 (to expand genre and mood diversity) |
| Genres represented | pop, lofi, rock, ambient, synthwave, jazz, indie pop, hip-hop, classical, r&b, country, electronic, metal, soul, reggae |
| Moods represented | happy, chill, intense, relaxed, focused, moody, energetic, peaceful, romantic, nostalgic, melancholic, angry |
| Numerical features per song | energy (0–1), tempo_bpm, valence (0–1), danceability (0–1), acousticness (0–1) |

**Limits of this data:**
- Most genres appear only once or twice. With 18 songs across 15 genres, a user who prefers a rare genre (like classical or metal) gets only one strong match and four weak filler results.
- All song data was hand-crafted for this simulation. The numbers are plausible but not drawn from real audio analysis tools like Spotify's audio features API.
- No behavioral data exists — no play counts, skips, playlist adds, or listening history. The dataset only describes what songs *are*, not what people *do* with them.
- The catalog reflects one curator's idea of what genres and moods to include, which means certain communities and styles (non-Western genres, non-English music, niche subgenres) are completely absent.

---

## 4. Algorithm Summary

The recommender works like a judge scoring songs on a point scale — not like a brain that learns.

For each song in the catalog, it asks three questions:

1. **Does the genre match?** If yes, award 2 points. Genre is the strongest signal because it represents the broadest category of musical style.
2. **Does the mood match?** If yes, award 1.5 points. Mood captures the emotional tone the user is going for.
3. **How close is the energy?** Energy runs from 0 (completely quiet) to 1 (maximum intensity). Instead of just asking "is it energetic?", the system measures the gap between what the song has and what the user wants. A song that is 0.02 away from the target scores almost a full point; a song that is 0.70 away scores very little. This rewards closeness, not just high or low values.

There are two smaller bonuses:
- A song that sounds positive and happy (high valence) gets a small extra lift.
- If the user says they like acoustic music, songs with high acousticness get a small extra lift.

Once every song has a total score, the system sorts them from highest to lowest and returns the top five. That sorting step is called the Ranking Rule — it turns the pile of numbers into an actual recommendation list.

**Maximum possible score: 5.0 points**

---

## 5. Observed Behavior / Biases

### Finding 1 — Categorical bonus can override numerical logic entirely

The clearest example of a flaw came from an adversarial test: a user who said they like ambient music with a peaceful mood but wanted very high energy (0.95). Every peaceful/ambient song in the catalog is naturally low-energy. The system ranked Spacewalk Thoughts first — a song with energy 0.28 — because its genre bonus alone (2.0 points) was large enough to win, even though its energy was 0.67 away from what the user asked for. In a real system, this user would skip that song immediately.

**Root cause**: the genre weight (2.0) is large enough to dominate any combination of smaller signals. A single genre match guarantees a high rank even when other features conflict badly.

### Finding 2 — Rare genres create hollow recommendation lists

With only one song per genre for most genres, a Metal/Angry user gets Ironclad correctly at #1 — but positions 2–5 are filled with Gym Hero (pop/intense), Sunrise City (pop/happy), Rooftop Lights (indie pop/happy), and Concrete Jungle (hip-hop/energetic). These songs share nothing with metal except high energy values. The system has no fallback behavior for underrepresented genres — it simply hands out energy-proximity consolation prizes.

### Finding 3 — Valence boost silently penalizes melancholic users

The system always adds a small bonus for songs that sound positive and upbeat (high valence). A user who explicitly asks for melancholic or moody music is still competing against songs that receive this hidden bonus. There is no way for a user to say "I prefer darker-sounding tracks" — the bias toward happy-sounding songs is always on, for everyone.

### Finding 4 — The system is blind to what happens inside a genre or mood label

"Intense rock" and "intense pop" earn the same mood bonus. A song at 180 BPM (Ironclad) and one at 90 BPM (Coffee Shop Stories) receive no penalty for tempo difference as long as their genre labels happen to match a user's preference. Two songs that would feel completely different to any listener are treated as identical in the features the model actually scores.

---

## 6. Evaluation Process

Six user profiles were tested and all output was reviewed manually.

| Profile | Type | Top Result | Score | Notable Finding |
|---|---|---|---|---|
| High-Energy Pop | Standard | Sunrise City (pop/happy) | 4.89 | Matched intuition exactly |
| Chill Lofi | Standard | Library Rain (lofi/chill) | 4.77 | Matched intuition exactly |
| Deep Intense Rock | Standard | Storm Runner (rock/intense) | 4.74 | Matched intuition exactly |
| Peaceful + High-Energy | Adversarial | Spacewalk Thoughts (ambient/chill, energy 0.28) | 2.66 | Genre won over a 0.67 energy gap — bad result |
| Metal / Angry | Edge case | Ironclad (correct) | 4.65 | Rank 1 correct; ranks 2–5 are unrelated pop/hip-hop |
| Mid-Energy Jazz | Edge case | Coffee Shop Stories (jazz/relaxed) | 4.72 | Correct at rank 1; only one jazz song in catalog |

**Weight-shift experiment** — High-Energy Pop profile, genre weight halved (2.0 → 1.0), energy weight doubled (1.0 → 2.0):

Rooftop Lights (indie pop / happy / energy 0.76) moved from rank 3 to rank 2, displacing Gym Hero (pop / intense / energy 0.93). This felt more intuitive: the user wanted "happy pop," and Rooftop Lights matches the mood while Gym Hero only matches the genre. Reducing the genre weight let emotional intent outweigh category membership, which produced better results for this profile.

**Comparison across profiles**: Standard profiles produced clean, distinct top-3 results with no overlap. Adversarial profiles revealed where the math disagrees with common sense. The experiment confirmed that the default genre weight of 2.0 causes the system to over-commit to category labels at the cost of emotional accuracy.

---

## 7. Intended Use and Non-Intended Use

### Intended Use

- Classroom exploration of how content-based recommender systems work
- Learning how weighted scoring rules translate user preferences into ranked lists
- Demonstrating how small datasets and simple math can produce results that "feel" like recommendations
- Practicing the design decisions involved in weighting features: which signals matter most, and why

### Non-Intended Use

- **Not for real music discovery**: the 18-song catalog is too small and too synthetic to be useful as an actual music tool
- **Not for deployment to real users**: the system has no privacy protections, no feedback loop, and no way to handle preferences it has not seen before
- **Not as evidence that content-based filtering is sufficient**: real platforms require behavioral signals, collaborative filtering, and continuous retraining — this simulation does none of those things
- **Not as a fair representation of diverse musical taste**: the catalog was hand-selected and skews heavily toward Western pop and its adjacent genres

---

## 8. Ideas for Improvement

**1. Add tempo as a scored feature**  
The CSV already has `tempo_bpm` for every song, but the scoring rule ignores it. Adding a `target_tempo` field to the user profile and using the same proximity math (1 − |song_bpm − target_bpm| / max_bpm) would correctly separate fast metal from slow jazz, even when their energy scores happen to be similar.

**2. Make the catalog bigger and more balanced**  
At 18 songs, most genres appear only once. A user who prefers classical or reggae gets one real match and four energy-proximity filler results. Expanding to at least 5–10 songs per genre would let the ranking rule do meaningful work across the whole list instead of just awarding rank 1 and giving up.

**3. Add a `valence_preference` to the user profile**  
Right now the valence boost always rewards happy-sounding songs, regardless of what the user wants. Letting the user declare a preference (e.g., "I like darker music") and turning the valence bonus into a proximity score instead of a fixed lift would remove the hidden bias against melancholic profiles.

---

## 9. Personal Reflection

### Biggest learning moment

The adversarial "Peaceful but High-Energy" profile was the turning point. I expected the system to struggle — but I expected it to struggle in a vague way, like returning slightly wrong results. What actually happened was more concrete: a single genre match worth 2.0 points drowned out an energy mismatch of 0.67 points, and the top recommendation was a song that was the near-opposite of what the energy preference asked for. That made abstract ideas like "filter bubble" and "bias from weights" suddenly feel real. It was not a bug in the code — the math was doing exactly what the weights told it to do. The problem was that I, the designer, had decided genre mattered twice as much as energy without thinking through what happens when those two signals point in opposite directions.

### How AI tools helped — and when I needed to double-check

AI tools were most useful at the "blank page" moments: generating a diverse set of songs in valid CSV format, suggesting which audio features matter most for a content-based recommender, and proposing the Mermaid.js flowchart syntax. They saved time on tasks where the output was easy to verify — if the CSV had the right headers and plausible numbers, it was good to go.

The moments that required careful review were the algorithm design suggestions. When asked to suggest point weights, the AI gave reasonable-sounding numbers without explaining what would happen at the edges. It did not flag the risk that a 2.0 genre weight could dominate a 1.0 energy weight in adversarial cases — that only became visible after actually running the profiles. So the rule I developed: AI suggestions are a starting point, not a finished answer. Running the code and reading the output is the real verification step.

### What surprised me about simple algorithms feeling like recommendations

The three standard profiles — pop, lofi, rock — produced results that felt genuinely right on the first run. No training, no neural network, no user history: just three if-statements and a sort, and the output matched musical intuition. That was more surprising than the adversarial failures. It suggests that for users with clear, consistent taste and a well-stocked catalog, a simple weighted rule can appear "smart" without being smart at all. The appearance of intelligence comes from the data matching the user, not from any real understanding. A user who listens mostly to lofi music and asks for lofi recommendations is going to get good results from almost any algorithm — the data does the work, not the model.

### What I would try next

The experiment that changed my thinking most was the weight-shift — halving genre and doubling energy. It took two lines of code to change and produced noticeably more intuitive results for the emotional intent of the pop/happy profile. I would want to run that experiment across all six profiles to see whether lower genre weight consistently improves results or whether it helps some users and hurts others. That kind of systematic sensitivity analysis — varying one weight at a time and tracking which profiles improve or degrade — is exactly how real teams tune recommendation systems, and this simulation is small enough to do it exhaustively in an afternoon.
