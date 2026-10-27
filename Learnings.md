# LEARNINGS

> Last updated: Sun 25 Oct 2026 (language decision, prior art, how to read results).
> Sections: 1 Concepts, 2 Code explained, 3 Bugs, 4 Mistakes and lessons, 5 Interview questions.

---

## 1. Concepts in simple language

### 1.1 Round-trip testing
We make Timbre (text to speech) say a sentence we already know, then give that audio to Prisma (speech to text) and compare what it wrote with what we sent. Because we know the correct answer in advance, a difference is a measurable failure, with no human labelling.

### 1.2 Inverse text normalization (ITN): what our first run showed
STT output is not a literal word-for-word transcript. Prisma converts spoken forms into written forms ("inverse text normalization"). It is the opposite of the TTS step that converts written forms into spoken ones.

First run (5 sentences, `hi-IN`):

| Said (sent to TTS) | Heard (STT output) | What we learn |
|---|---|---|
| `मेरा नंबर 9876543210 है` | `मेरा नंबर 9876543210 है।` | Digits survive the round trip |
| digits spoken as Hindi words | `मेरा नंबर 9876543210 है।` | Spoken digits are written back as one digit string |
| `पाँच लाख रुपये भेजना है` | `₹5,00,000 भेजना है।` | Words become a rupee amount with Indian comma grouping |
| `₹5,00,000 भेजना है` | `₹5,00,000 भेजना है।` | Amount survives |
| `सुबह साढ़े नौ बजे मिलते हैं` | `सुबह 09:30 बजे मिलते हैं।` | "Half past nine" becomes `09:30` |

Consequences for the comparer: a plain string comparison would mark most of these wrong. The output also adds a trailing `।` (danda) every time. We must compare meaning (normalized form), not raw strings.

### 1.3 Attribution: who made the mistake?
A mismatch could be Timbre reading the text wrongly, Prisma hearing it wrongly, or both. Text alone cannot tell you which. All our audio is saved in `.cache/tts/`, so when something fails we can listen to the clip: if the clip sounds wrong, TTS is at fault; if it sounds right, STT is. Also, our first run only shows the loop works. It does not prove each step is individually correct.

### 1.4 Billing: credits, rupees, and units
Credits and rupees match 1:1 in the usage history, but the two APIs are metered differently:
- STT is billed by **audio duration** (0.15 min cost Rs 0.07; 0.03 min cost Rs 0.02), roughly Rs 0.5 per minute.
- TTS is billed by **characters** (43 characters cost Rs 0.12), roughly Rs 2.8 per 1,000 characters.

So "credits are about equal to rupees" does not mean the two cost the same. A silent pause in an STT clip costs money; a long sentence costs more in TTS. The rates above are rough, computed from rounded dashboard values.

### 1.5 Q1. What changed in Timbre v3.0, and why do we prefer it?
(The model is Timbre **v3.0**. "v0.3" is just the digits swapped.)

What Gnani's docs say changed compared with Timbre v2.5:
- **Voices:** v2.5 has 42 voices, each with one preferred language. v3.0 has 13 voices, and each speaks all 10 supported languages (Hindi, English, Tamil, Telugu, Kannada, Malayalam, Marathi, Punjabi, Bengali, Gujarati).
- **Audio tags:** you can put tags inline in the text, such as `<coughs>`, `<whispers>`, `<laugh>`, `<sigh>`, `<pauses>`, `<shouting>`. With v2.5 the tags are stripped and not spoken.
- **Not interchangeable:** a v2.5 voice name sent to v3.0 (or the reverse) is rejected with a 400 error.

Claims on Gnani's launch page (vendor marketing, **not yet verified by us**): more expressive speech, switching language mid-sentence (beta), reading numbers and IDs correctly without special markup, and first audio in under 150 ms.

Why we use v3.0 in this project:
1. **Harder test material.** Tags like whisper and cough let us make speech closer to real callers, which is useful for stress-testing STT.
2. **One voice, all languages.** We can vary language across the test matrix without changing the voice.
3. **Entity reading is our focus.** The claim about reading numbers and IDs directly matters to us, and we plan to test it rather than trust it.

Caveats: we have not compared v3.0 against v2.5 yet, and the docs are not fully consistent. Earlier v2.5 docs advised writing numbers out as spoken words, while Gnani's newer Text Normalization Guide says conversion is automatic. We have not confirmed which model that applies to. Our digits-as-digits sentence came back correct, which is consistent with automatic handling, but we have not listened to the clip to confirm how it was read.

### 1.6 How to choose a language (decided Sun 25 Oct 2026)
We did not choose Python on purpose; the first scripts simply started in it. We then decided properly:
1. List the hard sub-problems (generating cases, simulating a phone line with maths on audio, comparing Hindi text, many API calls, reports, automated tests).
2. Check which language already has good tools for them.
3. Check vendor support (Gnani's official SDK is Python).
4. Ask how fast you can move in the time you have. This is often the real tiebreaker.
5. Ask how costly it is to switch later (cheap early, grows with every line of code).
6. Write the decision down with a revisit trigger.

Alternatives considered: TypeScript/Node, Go, Java/Kotlin, Rust. Result: Python, mainly because Tanmay writes and understands it most easily. Language speed barely matters here, because the program mostly waits for network replies.
Lesson: deciding after the fact is fine if it is recorded honestly. Do not invent a rationale that was not there at the start.

### 1.7 Why Indic ASR evaluation is more than word error rate (WER)
WER counts every difference from a single reference spelling as an error. Indian languages have several correct forms: a code-mixed word such as "doctor" may appear in Latin script or as "डॉक्टर", and numbers may be digits or spelled out. Voice of India (arXiv 2604.19151) built OI-WER to accept valid spelling variants, and Sarvam's evaluation guide adds scores for whether entities (names, numbers, dates) survive. For us this means: score **entities** (phone numbers, amounts, times) after normalizing them, rather than comparing raw strings.

### 1.8 Why "10 out of 10 correct" proves little
If the system truly failed about 26% of the time, you would still see 10 clean passes roughly 1 time in 20. So 10/10 is consistent with a true failure rate of up to about a quarter. 100/100 passes brings that ceiling down to about 3% (rule of thumb: ceiling is roughly 3 divided by the number of tests). Comparing two conditions needs more still.
Also, clean synthetic speech from Gnani's own TTS may be unusually easy for Gnani's own STT, so passes on clean synthetic audio say little about real callers. That is why the phone-line degradation and a small set of real recordings matter. The interesting results are the *breaking points*: which entity types fail first, and at what noise level.

---

## 2. Code explained

### 2.1 Q2. What `key_for` does in `cache.py`

```python
def key_for(*parts) -> str:
    """Same input -> same key. This is what makes re-runs free."""
    blob = json.dumps(parts, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]
```

**The engineering problem:** before calling the API we need a way to ask "have I already done exactly this request?" The answer is a filename. That filename must be (a) the same every time for the same inputs, (b) different for different inputs, and (c) short and safe to use as a filename, even though the inputs can be long text full of Devanagari characters and quotes.

**What happens step by step** (using a real example from our experiments, `key_for({"text": "नमस्ते", "voice": "Shivani"})`):

1. `*parts` collects all arguments into a tuple. Calling `key_for(payload)` gives `parts = (payload,)`. Calling `key_for("stt", "hi-IN", audio_hash)` gives a tuple of three. This lets one function serve both TTS and STT.
2. `json.dumps(...)` converts the Python objects into **one text string** in a standard format, because a hash function needs bytes or text, not Python dicts. A tuple becomes a JSON list: `[{"text": "नमस्ते", "voice": "Shivani"}]`.
3. `.encode()` converts that text into **bytes** (UTF-8). Hash functions only accept bytes.
4. `hashlib.sha256(...)` computes the fingerprint (explained below).
5. `.hexdigest()` writes that fingerprint as a string of 64 hexadecimal characters.
6. `[:16]` keeps the first 16 of them. For our example this gives `e3553795b17223ea`.

**Each piece:**

- **`blob`**: just a variable name. "Blob" is programmer slang for "one opaque chunk of data". Here it is the single text string that stands for all the inputs. (After `.encode()` it becomes bytes. We checked: `str` before, `bytes` after.)
- **`hashlib`**: Python's standard-library module with hash functions (sha256, md5, and others). Nothing to install.
- **`sha256`**: a hash function. It takes input of any length and produces a fixed 256-bit (32-byte) fingerprint. Properties that matter to us:
  - *Deterministic*: same input, same output, always.
  - *Fixed size*: a 3-word sentence and a whole 30-second audio file both give 32 bytes.
  - *Avalanche effect*: a tiny change gives a completely different result. We checked: the first 16 hex characters for `hello1` are `91e9240f41522398` and for `hello2` are `87298cc2f31fba73`.
  - *One-way*: you cannot rebuild the input from the hash. We do not need to; we only need to recognise the same input again.
- **`hexdigest()`**: the hash is raw bytes (not safe to print or use in a filename). `hexdigest` shows it as 64 characters from `0-9a-f`, which is filename-safe. (`digest()` gives the raw 32 bytes; we checked: 32 bytes vs 64 characters.)
- **`sort_keys=True`**: two Python dicts with the same content but a different key order are equal (`a == b` is `True`), but `json.dumps` writes them in the order they were created, so the text differs. Our check: without sorting, `{"text":..., "voice":...}` gave key `e3553795b17223ea` but the same dict written as `{"voice":..., "text":...}` gave `bed0b211e4c4892b`. That would cause a false cache miss and a wasted API call. Sorting the keys makes the text canonical.
- **`ensure_ascii=False`**: by default `json.dumps` escapes every non-English character: `"नमस्ते"` becomes `"\u0928\u092e\u0938\u094d\u0924\u0947"`. With `False` the real Devanagari characters are kept. For correctness either choice works, as long as it never changes, because both are deterministic. We chose `False` so the text stays readable if we print the blob while debugging. Changing it later would change every key and empty the cache.
- **`default=str`**: if a part contains something JSON does not understand (for example a `Path`), call `str()` on it instead of crashing. Caveat: `str()` of some objects includes memory addresses, which would make keys unstable. Our parts are simple, so this is fine.
- **`[:16]`**: shortens the key to 64 bits, which is plenty. For 5,000 cache entries, the chance that any two collide is about 7 x 10^-13 (we computed it). If the cache ever held millions of entries we should use more characters. A collision would silently return the wrong cached audio.

**Where else this appears:** in `transcribe`, `hashlib.sha256(audio).hexdigest()` fingerprints the *audio file's bytes*, so the same sound maps to the same key regardless of the file's name.

**A consequence worth remembering:** since the STT key depends on the audio bytes, our noise-adding code must be **deterministic** (seeded random noise). If the noise differs every run, the bytes differ, the key differs, and the cache never hits.

### 2.2 Q3. What `BASE = "https://api.vachana.ai"` is

```python
BASE = "https://api.vachana.ai"
```

- **What it is:** a Python variable holding the *root address* of Gnani's API server. Python convention is to write constants in UPPERCASE, which is why we called it `BASE`. The name is ours; the **value is not**: it comes from Gnani's docs, where it is the address used in every example and the default in their Python SDK.
- **Is it an endpoint?** Not by itself. A URL has parts: `https://` (secure connection) + `api.vachana.ai` (which server) + a path (which operation). An **endpoint** is the full address of one specific operation: base + path. We use two:

| Endpoint | Method | Purpose |
|---|---|---|
| `{BASE}/api/v1/tts/inference` | POST | Text to speech |
| `{BASE}/stt/v3` | POST | Speech to text (REST) |

- **Why a variable:** the address is used in several places. Writing it once means a typo can't creep in and changing it later (the SDK docs mention pointing at a different environment) is a one-line edit.
- **Did we create anything?** No. We did not create the server or the address. We only gave Gnani's address a name in our code.

### 2.3 Q4. What `synthesize` and `transcribe` do (in `clients.py`)

These two functions are the **boundary** between our program and Gnani's servers. They are the only code that touches the network and spends credits. The rest of the project is our own logic that will call them. So yes, this is where the main work happens, but the real value of the project lies in what we build around them (generator, degrader, comparer, report).

**`synthesize(text, voice, language, model, speed, sample_rate)`** returns the path of a WAV file.
1. Builds a `payload` dict describing what we want (text, voice, model, language, speed, audio format).
2. Computes the cache path from `key_for(payload)`. Any change (different voice, speed) gives a new key, so it gets its own file automatically.
3. If that file exists, returns it immediately: no network, no credits.
4. Otherwise sends the payload as JSON (`json=payload`) with the API key in the `X-API-Key-ID` header.
5. `r.raise_for_status()` turns an HTTP error (a 400 or 500) into a Python exception, so a failure is never saved to the cache as if it were good audio.
6. Saves `r.content` (the raw audio bytes) into the cache, creating folders as needed (`mkdir(parents=True, exist_ok=True)`), and returns the path.

**`transcribe(wav_path, language_code)`** returns the transcript text.
1. Reads the audio file as bytes.
2. Builds the key from `"stt"`, the language, and the SHA-256 of the audio bytes.
3. If a cached JSON exists, returns its `transcript` field.
4. Otherwise uploads the audio as a multipart form (`files=` for the file, `data=` for the language), the format file-upload endpoints expect.
5. Checks for errors, saves the JSON response, and returns `["transcript"]`.

Both set `timeout=60` so the program doesn't hang forever if the server stops answering.

**Note:** `transcribe` returns only the text. The response also contains `request_id` and `model`, which we currently throw away. The `model` field could help us notice when Gnani updates its model (see TODO.md).

---

## 3. Bugs encountered

None yet. Template for later:

```
### <short title>
- Symptom:
- Root cause:
- Fix:
- How to avoid it next time:
```

---

## 4. Mistakes and lessons

- **We guessed credits might be tight, then measured.** Two dashboard rows showed STT is cheap, which changed the plan (no need to ration test runs). Lesson: measure the cost of an unknown before designing around it.
- **"Credits equal rupees" does not mean TTS and STT cost the same.** They are metered in different units (characters vs minutes). Lesson: check the unit, not just the currency.
- **Don't commit before `.gitignore` exists.** The API key lives in `.env`; if it is committed, rotate the key. Lesson: create `.gitignore` before the first `git add`.
- **We started in Python without choosing it.** The hello scripts just began in Python and the docs had a blank where the reason should be. We then compared alternatives and recorded the decision honestly (section 1.6). Lesson: when a default creeps in, evaluate it explicitly while switching is still cheap.
- **The core idea already has prior art.** Searching only after designing the project showed commercial tools and research papers on similar ideas (PROJECT.md section 6). Lesson: check prior art early, and state how your work differs.

---

## 5. Interview-relevant questions (practice answering out loud)

1. Why hash the inputs instead of using the text itself as the filename? (Section 2.1)
2. What makes a cache key correct? Name two ways a key can go wrong. (`sort_keys`; keys that miss something that matters, such as a model version)
3. Why does the STT cache key use the audio bytes rather than the filename? (Section 2.1)
4. When can a cache hurt rather than help in a testing tool? (Section 2.1 and TODO known issues)
5. What is the difference between a base URL and an endpoint? (Section 2.2)
6. Why separate API code from pure logic? (PROJECT.md decision 6)
7. If a round-trip test fails, how do you tell whether TTS or STT is at fault? (Section 1.3)
8. What is inverse text normalization, and how does it complicate comparing transcripts? (Section 1.2)
9. Why is STT metered by duration but TTS by characters, and what does that mean for how you design test clips? (Section 1.4)
10. How did you pick your language, and what would make you switch? (Section 1.6)
11. Why is word error rate a poor metric for Indian languages, and what would you measure instead? (Section 1.7)
12. You ran 10 tests and all passed. What can you conclude? What if it was 100? (Section 1.8)