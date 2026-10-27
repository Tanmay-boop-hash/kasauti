# TODO

> Last updated: Sun 25 Oct 2026.
> Deadline: Tue 10 Nov 2026 (challenge close). Internal targets: post live by Sat 7 Nov, submit by Mon 9 Nov.
> Light days (exams): Mondays and Thursdays.

---

## Current status

### Done
- [x] Registered for the challenge; 5,000 credits received
- [x] Measured costs: STT 0.15 min = Rs 0.07; TTS 43 characters = Rs 0.12
- [x] Hello-world scripts for STT and TTS run successfully
- [x] `voicetest/cache.py` and `voicetest/clients.py` written
- [x] `roundtrip.py`: 5 sentences run end to end (cost about Rs 0.52); second run served entirely from cache with no new API requests
- [x] First versions of PROJECT.md, LEARNINGS.md, TODO.md
- [x] Language decided: Python (PROJECT.md decision 8)
- [x] Decided the repo will be public from the start (decision 9)

### Not done yet
- [ ] Choose the repo name
- [ ] `git init`, `.gitignore` (must list `.env`, `.cache/`, `*.wav`, `__pycache__/`), first commit
- [ ] Create the GitHub repo and push
- [ ] `requirements.txt` (the code currently imports `requests` and `python-dotenv`)

---

## Pending tasks (from the plan)

| When | Task | Done when |
|---|---|---|
| Sun 25 Oct | Comparer: decide when "expected" and "heard" match (digits vs words, spacing, trailing `।`). Write `pytest` tests for it. | 10 hand-written sentences run; tests pass without calling the API |
| Mon 26 Oct (light) | More comparer tests only | Edge cases covered: lakh/crore, Devanagari digits, spacing |
| Tue 27 to Wed 28 Oct | Test-case generator (phone numbers, amounts, times, PIN codes) with a fixed seed | 200 cases, identical on every run |
| Thu 29 Oct (light) | README draft | A stranger could install and run it |
| Fri 30 Oct | Phone-line simulator, runner, simple report | **20 sentences run end to end and produce a report** |
| Sat 31 Oct to Sun 1 Nov | Findings: Timbre v3.0 number reading, audio tags, Hinglish, word boosting; about 20 real clips of you reading fake numbers | 3 to 4 clear findings with numbers |
| Mon 2 to Thu 5 Nov | CLI, config file, GitHub Actions for no-API tests, README with findings | A stranger can clone, run, and read results |
| Fri 6 to Sat 7 Nov | 60-second demo video and the post | Post live by Nov 7 |
| Sun 8 to Mon 9 Nov | Submission form | Submitted by Monday night |

**Cut order if time shrinks:** real-clip comparison, latency measurement, word-boost experiment. Keep generator, degrader, report.

**Before final submission:** delete `01_stt_hello.py` and `02_tts_hello.py` (decided: they were only a starting point); add a "Prior work" section to the README based on PROJECT.md section 6.

---

## Known issues and design questions

1. **Comparer must handle formatting differences.** Observed in the first run: STT writes `9876543210` for spoken digits, `₹5,00,000` for "five lakh rupees", `09:30` for "half past nine", and adds a trailing `।`. A raw string comparison would mark these wrong. (LEARNINGS 1.2)
2. **Error attribution.** A text mismatch doesn't say whether TTS or STT was at fault. Plan: keep the cached WAV so we can listen. (LEARNINGS 1.3)
3. **Cache can return stale answers.** The STT cache key uses only the language and the audio bytes, so if Gnani updates the Prisma model, old transcripts are served. This matters for a tool meant to detect model changes. Options to decide on: a `--no-cache` flag, or adding the model version to the key. `transcribe` currently discards the `model` field of the response.
4. **Noise must be deterministic.** If the degrader uses random noise, use a seed. Otherwise the audio bytes change every run and the STT cache never hits. (LEARNINGS 2.1)
5. **SDK vs raw `requests`.** Unverified whether the official SDK accepts Timbre v3.0 voices; we are using raw `requests` for now.
6. **Docs conflict on number handling.** Older v2.5 docs advised pre-formatting numbers as spoken words; the newer normalization guide says it is automatic. Not yet confirmed for v3.0. (LEARNINGS 1.5)
7. **Positioning / novelty.** The core idea has prior art (PROJECT.md section 6). Decide what makes this project different and write it in one sentence. Not yet decided.

---

## Next steps (small and concrete)

1. Pick the repo name.
2. Create `.gitignore` and `requirements.txt`, run `git status` to confirm `.env` is not listed, and make the first commit.
3. Create the GitHub repo and push.
4. Today (Sun 25 Oct): write the comparer as a pure function plus its first pytest tests.

---

## Open questions for you (needed to complete the docs)

- What is explicitly out of scope for this project? (PROJECT.md "Non-goals" is empty.)
- What is the one-sentence positioning of the project, given the prior art in PROJECT.md section 6?