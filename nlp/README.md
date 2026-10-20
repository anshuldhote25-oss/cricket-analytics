# `nlp/` - Multilingual NLP front-end (English · Hindi · Marathi)

Users can ask in **English, Hindi or Marathi**, written in **Devanagari or in Roman letters**
("Hinglish", "Marathi typed in English"). This package turns the raw question into a structured
*frame* before the LLM sees it, and everything here runs offline using only the Python standard library.

```
"powerplay madhe sarvottam economy asleale golandaj dakhva"
   │ normalize_text      Unicode NFC, Devanagari digits -> 0-9, nukta/ZWJ removal, "<" -> "under"
   │ tokenize            numbers | Latin words | Devanagari words
   │ detect_language     -> mr-Latn  (Marathi, Roman letters)
   │ extract_entities    gazetteer + phonetic keys + suffix stemming + fuzzy match
   │                      phase=powerplay, direction=desc, metric=economy_rate, role=bowler
   │ resolve_numbers     "top 10" -> limit,  "economy 7 se kam" -> economy_rate < 7
   │ intent              rules over entities  (+ Naive Bayes fallback)  -> bowling
   │ nlg                 "Top bowlers by economy rate in the powerplay"  + notes for the LLM
   ▼
Frame  ──►  agent.py sends  question + notes  to Llama 3.3 (Groq)  ──►  SQL  ──►  PostgreSQL
```

Greetings, out-of-scope questions (weather, recipes ...) and data we do not hold (IPL, internationals)
are answered **locally, in the user's own language and script**, without calling the LLM.

## NLP concepts → where they live (use this for the report / viva)

| Concept | File | What to point at |
|---|---|---|
| Unicode normalization, tokenization | `normalize.py` | `normalize_text`, `tokenize` |
| Transliteration (Devanagari → Latin) | `normalize.py` | `devanagari_to_latin` |
| Phonetic hashing (Soundex-like) | `normalize.py` | `phonetic_key`: *gendbaaz = gendbaj = गेंदबाज़* |
| Edit distance / fuzzy matching | `normalize.py`, `entities.py` | `levenshtein`, `_fuzzy_lookup` |
| Language & script identification | `lang_id.py` | function-word voting, Marathi suffix cues |
| Morphology, stemming (agglutination) | `stemmer.py` | *नागपूरचे = नागपूर + चे*, *golandajanmadhe* |
| Named-entity recognition (gazetteer) | `lexicon.py`, `entities.py` | longest-match lookup, 900+ surface forms |
| Entity linking across scripts | `entities.py` | `रोहित खडसे` → player *Rohit Khadse* |
| Slot filling, number/threshold parsing | `entities.py` | `resolve_numbers` |
| Text classification (Naive Bayes, from scratch) | `intent.py` | `NaiveBayesIntent`, char n-gram features |
| Rule-based vs learned classifiers | `intent.py`, `evaluate.py` | `rule_intent` baseline vs NB |
| Template-based NLG, localization | `nlg.py` | `MESSAGES`, `describe`, `build_hints` |
| LLM grounding / prompt augmentation | `nlg.py`, `../agent.py` | `build_hints` |
| Evaluation (P/R/F1, confusion matrix) | `evaluate.py` | run it, paste the tables |
| Synthetic data generation | `dataset.py` | template × slot sampling |

## Commands

```bash
python -m nlp "powerplay madhe sarvottam economy asleale golandaj dakhva"   # inspect one question
python -m nlp                       # interactive
python -m nlp.train                 # regenerate training data + retrain Naive Bayes  (nlp/models/intent_nb.json)
python -m nlp.evaluate --errors     # evaluate on nlp/data/intent_test.csv and list every mistake
python -m nlp.lint                  # lexicon sanity check (key collisions, function-word clashes)
python -m unittest nlp.test_pipeline -v
```
The running server also exposes `POST /api/analyze {"question": "..."}`, which returns the whole analysis
(tokens, language scores, entities, notes for the LLM) without calling the LLM or the database.

## Teaching it a new word
Open `lexicon.py`, add the spelling to the right `forms` string, then run `python -m nlp.lint` and
`python -m nlp.evaluate`. Spelling variants that *sound* the same do not need listing (the phonetic key merges
them). A form written `=word` matches only that exact spelling: use it for short words that would otherwise
collide with common Hindi/Marathi words (`=men` vs *mein*, `=pp` vs *aap*).

## Results (78 hand-written questions: 13 en, 17 hi, 15 mr, 17 hi-Latn, 16 mr-Latn)

| Component | Result |
|---|---|
| Language identification | 100 % accuracy |
| Entity / slot extraction (exact-match sets) | P = R = F1 = 1.00 |
| Intent, rule baseline (entities only) | 100 % |
| Intent, Naive Bayes, text features only (no gazetteer) | 93.6 % (macro-F1 0.933) |
| Intent, Naive Bayes, text + entity features | 94.9 % (macro-F1 0.951) |
| Intent, final pipeline (lexicon + rules, NB fallback) | 100 % |

**Read these numbers honestly.** The lexicon and language rules were tuned until this set passed, so it is
effectively a *development* set and the scores are optimistic. Before you
submit: write ~30-50 **fresh** questions (ask classmates to phrase them their own way, especially romanized
Hindi/Marathi), put them in a new CSV with the same columns, and report those numbers separately.
Also note that the rule baseline matching 100 % is expected: with a rich gazetteer the entities already
determine the intent. The Naive Bayes result that matters is the *text-only* row: it shows the classifier
learns from words and character n-grams alone, with no dictionary help.

## Known limitations (good "future work" paragraph)
* Hindi/Marathi romanization has no standard; the lexicon + phonetic keys cover common spellings, not all.
* Player names are matched as full names only (2+ words); a surname alone is not resolved.
* Marathi vs Hindi in Devanagari relies on function words / suffix cues; a very short query (1-2 words) is ambiguous.
* No conversation memory: "now only U19" (ellipsis / coreference resolution) is not handled yet.
* Training data is synthetic (templates); real user logs would improve the classifier.
* The LLM still writes the final explanation text; quality of Roman-script Marathi output depends on the model.

## Ideas to extend the project
1. Add a context window to `/api/query` for follow-up questions (coreference / ellipsis resolution).
2. Compare strategies A/B/C on a multilingual execution-accuracy test: (A) send the raw Hindi/Marathi question to the
   LLM, (B) translate to English first, (C) this pipeline's entities as hints. Measure whether the generated SQL returns the
   same rows.
3. Replace the Naive Bayes with logistic regression or a multilingual embedding model (MuRIL / LaBSE) and compare.
4. Voice input with the browser Web Speech API (`hi-IN`, `mr-IN`).
