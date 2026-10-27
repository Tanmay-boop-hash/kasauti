# PROJECT: Voice AI Round-Trip Tester

> Working name: **kasauti** (not final; update this line once the repo name is chosen).
> Last updated: Sun 25 Oct 2026.
> Status key used below: **Decided** (we chose it), **Planned** (agreed in our plan, not built), **Open** (still to decide).

---

## 1. Problem statement and goals

### Problem
Speech recognition (STT) for Indian languages tends to fail on specific, high-stakes things: phone numbers, rupee amounts, times. You only find this out by testing, and getting labelled real recordings is slow and expensive.

### Core idea
Use Gnani's text-to-speech (Timbre) to speak sentences whose exact text we already know, then feed that audio to Gnani's speech-to-text (Prisma) and compare what came back with what we sent. Because we know the right answer, every mismatch is a measurable failure, with no manual labelling.

Target pipeline:

```
generate sentence (known text)
   -> Timbre TTS (speak it)
   -> degrade audio (phone-line quality, noise)      [Planned]
   -> Prisma STT (transcribe it)
   -> normalize + compare expected vs heard           [Planned]
   -> per-entity error report                         [Planned]
```

### Goals
1. Submit a working project to the Great Indian AI Internship Challenge before the **Nov 10, 2026** deadline.
2. Understand every engineering decision well enough to explain it months later (this is why LEARNINGS.md exists).
3. Ship a public GitHub repo, a ~60-second demo video, a LinkedIn post, and a resume-ready write-up.
4. Produce findings people want to read: where does the Prisma + Timbre pair break? Planned experiments: Timbre v3.0 number reading, audio tags (whisper, cough), Hinglish, word boosting.

### Stretch goals (discussed, not committed)
- Suggest STT settings (boost lists, VAD/denoise) from the failures found.
- Run the tests in CI (using cached results, no live API calls).
- Add a latency report.

### Non-goals
Open: not decided yet. Add here once you know what you will deliberately not build.

---

## 2. Requirements and constraints

### Functional requirements (all Planned unless noted)
- Generate test sentences containing known entities (phone numbers, rupee amounts, times, PIN codes), reproducibly (fixed random seed).
- Synthesize and transcribe through Gnani's APIs, with every API result cached on disk. **(Built)**
- Simulate degraded audio (planned ideas: 8 kHz sampling, mu-law compression, added noise).
- Compare expected vs heard at the entity level, tolerating formatting differences (digits vs words, spacing, punctuation).
- Produce a report: failure rate per entity type, with examples.
- Command-line interface, README, and GitHub Actions that run tests needing no API calls.

### Constraints

| Constraint | Detail | Source |
|---|---|---|
| Deadline | Challenge submissions close Nov 10, 2026. Internal targets: post live by Nov 7, submit by Nov 9. | Challenge page / our plan |
| Credits | 5,000 promotional credits. Usage history shows 1 credit = Rs 1 of usage. | Dashboard |
| Measured costs | STT: 0.15 min cost Rs 0.07; 0.03 min cost Rs 0.02. TTS (timbre-v3.0): 43 characters cost Rs 0.12. First 5-sentence round trip cost about Rs 0.52. | Dashboard / Tanmay's run |
| Data rule | Synthetic data only. No real phone numbers, Aadhaar, PAN, account numbers, or recorded calls in the project or demo. | Challenge page |
| Submission | Must name the Gnani models/APIs used and each member's contribution. | Challenge page |
| STT REST limits | Clips up to 60 s; WAV, MP3, OGG, FLAC, AAC, M4A; 8 to 44.1 kHz. | Gnani docs |
| Time | Weekends are heavy-work days; Mondays and Thursdays are light (exams). | Tanmay |
| Secrets | API key lives in `.env`, never committed. | Practice |

---

## 3. Tech stack and why

| Part | Choice | Why |
|---|---|---|
| Language | Python | Decided Sun 25 Oct after weighing TypeScript/Node, Go, Java/Kotlin and Rust (decision 8). Tanmay can write and understand it most easily; the project needs audio maths and `pytest`, which Python covers well; Gnani's official SDK is Python. |
| HTTP | `requests`, calling Gnani REST endpoints directly | Lets us see exactly what is sent and received (good for learning). The official SDK `gnani-vachana` was set aside for now: its docs say it still defaults to Timbre v2.0, it validates voice names on your machine, and its examples describe v2.5. We have not verified that it accepts v3.0 voices. |
| Secrets | `python-dotenv` + `.env` file | Keeps the API key out of the code and out of Git. |
| TTS | Timbre v3.0 (`timbre-v3.0`), voice `Shivani`, `hi-IN`, 16 kHz mono WAV, via `POST /api/v1/tts/inference` | See LEARNINGS.md section 1.5. |
| STT | Prisma v2.5 via `POST /stt/v3` (REST), `hi-IN` | Simplest option for short test clips (the REST endpoint accepts up to 60 s). |
| Cache | Files on disk under `.cache/` | See design decisions below. |
| Tests | `pytest` (Planned) | Tests for the comparer and generator need no API calls. |
| Audio degradation | Open | Not decided how to build the phone-line simulator. |
| Version control | Git + GitHub; GitHub Actions (Planned) | |

---

## 4. Architecture and component responsibilities

### Current layout

```
<repo>/
  voicetest/
    __init__.py     (empty; makes this folder a Python package)
    cache.py        key_for(): turns request inputs into a stable cache filename
    clients.py      synthesize() and transcribe(): the only code that talks to Gnani
  roundtrip.py      demo script: 5 sentences, say them, hear them back, print both
  .env              GNANI_API_KEY=...  (not committed)
  .cache/           tts/<key>.wav and stt/<key>.json  (not committed)
```

### Data flow of one round trip (as built)

```
text
 -> synthesize(text, voice, language, model, speed, sample_rate)
      -> build request payload
      -> key_for(payload) -> .cache/tts/<key>.wav exists? yes: return it
      -> no: POST {BASE}/api/v1/tts/inference -> save bytes -> return path
 -> transcribe(wav_path, language_code)
      -> key_for("stt", language, SHA-256 of audio bytes) -> .cache/stt/<key>.json exists? yes: return transcript
      -> no: POST {BASE}/stt/v3 (multipart upload) -> save JSON -> return transcript
```

### Components and responsibilities

| Component | Status | Responsibility |
|---|---|---|
| `cache.py` | Built | Stable cache keys. |
| `clients.py` | Built | The boundary with Gnani: network calls, auth header, disk cache. Nothing else in the project should call the API directly. |
| `roundtrip.py` | Built | Throwaway demo of the loop. |
| Comparer | Planned | Decide whether "expected" and "heard" mean the same thing (pure logic, no API). |
| Test-case generator | Planned | Produce reproducible sentences with entities (pure logic, no API). |
| Audio degrader | Planned | Make clean audio sound like a phone call. |
| Runner | Planned | Run the test matrix with retries and rate limits, store results. |
| Report | Planned | Turn results into per-entity failure rates and examples. |
| CLI | Planned | Single entry point for running everything. |

---

## 5. Important design decisions and alternatives rejected

| # | Decision | Status | Why | Alternatives |
|---|---|---|---|---|
| 1 | Call the REST API with plain `requests` | Decided | Transparent for learning; avoids unverified SDK behaviour with v3.0 | Official SDK (can revisit later) |
| 2 | Cache every API result on disk, keyed by a hash of the inputs | Decided | Re-runs become instant and free; experiments can be repeated safely | Calling the API on every run (slower, costs credits) |
| 3 | TTS cache key = the full request payload; STT cache key = ("stt", language, SHA-256 of the audio bytes) | Decided | Any changed parameter (voice, speed) gets its own entry automatically; STT is keyed on audio content, not filename | Keying on filenames |
| 4 | Use only synthetic data | Decided | Challenge rule; also reproducible | Real recordings of real numbers (disallowed) |
| 5 | Use Timbre v3.0 as the speaking model | Decided | See LEARNINGS.md 1.5 | Timbre v2.5 (kept as a possible comparison) |
| 6 | Keep pure logic (comparer, generator) separate from API code | Planned | Most tests then cost no credits and run anywhere | Mixing logic and API calls |
| 7 | CI runs only tests that need no live API calls | Planned | Avoid spending credits on every push | Live API calls in CI |
| 8 | Python as the project language | Decided (Sun 25 Oct) | Started in Python by default (the hello scripts), then evaluated afterwards. Fastest for Tanmay to write and understand; strong audio/number libraries and `pytest`; the program mostly waits on network replies, so language speed barely matters; switching cost was small at this stage | TypeScript/Node, Go, Java/Kotlin, Rust, shell + ffmpeg helpers. Revisit if we need a single downloadable binary or a standalone web front end |
| 9 | Public GitHub repo from the start | Decided (Sun 25 Oct) | Nothing secret to protect; few similar posts seen on LinkedIn so far (Tanmay's observation); the API key stays in `.env` | Private until the demo is ready |

### Open design questions
- **Cache vs real testing:** if Gnani updates Prisma, a cache hit returns the old answer. How do we bypass the cache or include the model version in the key? (Details in TODO.md.)
- **What counts as "the same"?** For example "9876543210" vs "98765 43210" vs the digits spoken as words. The comparer's rules are not decided yet.
- **Audio degradation approach:** build mu-law and noise ourselves, or use a tool such as ffmpeg?

---

## 6. Prior art and positioning (found by web search, Sun 25 Oct 2026)

The core loop (speak known text, transcribe it, compare) is **not new**. What exists:

- **Commercial voice-agent testing platforms.** A roundup on cekura.ai/discover/voice-agent-testing-platforms lists tools such as Bluejay and Evalion; others include Vapi's Test Suite (github.com/VapiAI/docs/pull/279/files), Relyable (retellai.com app partner page), FutureAGI Simulate (futureagi.com/platform/simulate) and TestMu AI. They simulate callers with accents and noise presets and support regression runs. They mostly test whole conversations, scored by an LLM against success criteria.
- **Indic ASR evaluation work.**
  - *Voice of India* (arXiv 2604.19151; IIT Madras / AI4Bharat / Josh Talks): closed benchmark of real telephonic speech, scored with OI-WER, which accepts valid spelling variants.
  - Sarvam AI's guide *Evaluating Indian Language ASR* (sarvam.ai/blogs/evaluating-indian-language-asr): argues WER is a poor fit for Indian languages and proposes entity-based scores; releases open-source evaluation code.
  - *The TTS-STT Flywheel* (arXiv 2605.03073): builds synthetic, entity-dense Indic test audio with TTS and finds large entity failures in other commercial and open ASR systems.

Not checked: whether Gnani has internal tooling like this. It is likely they evaluate their models on real data.

### Positioning
**Open.** Candidate one-sentence positioning (not confirmed): *a developer-side regression test for Indic entities (phone numbers, amounts, times) over phone-quality audio on Gnani's stack, with measured findings and tested fixes.* Replace this once decided.