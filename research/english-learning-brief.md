# English Learning Platform — Research Brief

## Target Audience
Vietnamese speakers who are "mất gốc" (lost foundation) and beginners A1→B2.

## Key Insights

### Vietnamese Learner Pain Points
- **Phonetics**: /θ/, /ð/, /ʃ/, /tʃ/, final consonants, consonant clusters
- **Grammar**: No verb tense conjugation, no articles (a/an/the), pro-drop language
- **Word Order**: Adj after noun ("house beautiful"), SOV confusion
- **Writing**: Latin script but different pronunciation rules

### Competitor Landscape
- Duolingo, MochiMochi, Elsa Speak, eJOY, VOCA, Langmaster
- **Market gap**: No app targets "mất gốc" explicitly with Vietnamese-native grammar explanations

### Recommended Architecture
- **Stack**: Next.js + Tailwind + Redis (SRS) + PostgreSQL (data)
- **SRS**: SM-2+ algorithm with Redis sorted sets
- **TTS**: Amazon Polly / Google Cloud TTS
- **PWA**: Offline support via Service Worker + IndexedDB

### Content Strategy
- **A1**: 50 words/unit, colors/family/food/body/numbers
- **A2**: 100 words/unit, clothing/weather/jobs/time
- **B1**: 200 words/unit, travel/health/education/tech
- **B2**: 300 words/unit, abstract/news/profession/culture

### Exercise Types (ranked by effectiveness)
1. Image + Word + Audio
2. Context Sentence with Audio
3. Minimal Pair Pronunciation Drills
4. Fill-in-the-Blank (Cloze)
5. Multiple Choice (with VN-learner distractors)
6. Sentence Building (scrambled words)
7. Listening Dictation
8. Role-Play Prompts
