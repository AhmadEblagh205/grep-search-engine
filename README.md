# Inverted-Index Search Engine

[![CI](https://github.com/AhmadEblagh205/grep-search-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/AhmadEblagh205/grep-search-engine/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A small lexical search engine built twice: my original 2021 UCL COMP0015 coursework is preserved unchanged in `original/`, while the audited rebuild in `src/` turns the same inverted-index idea into a more defensible information-retrieval exercise with positional phrase search, BM25 ranking, deterministic results and safe versioned index persistence.

The main lesson from the audit is not that a tiny local engine competes with production search. It is that **retrieval correctness, ranking quality, persistence safety and reproducibility are different claims and need different evidence**.

## From coursework to an auditable search engine

The original coursework maps cleaned words to the BBC-news files containing them and answers multi-word queries by intersecting posting lists. The BBC corpus is not redistributed here; the original code and tests are retained for provenance.

The rebuild adds:

- an inverted index plus positional postings;
- Boolean AND retrieval;
- exact adjacent phrase retrieval;
- BM25 lexical ranking, with the earlier simple TF-IDF score retained for comparison;
- exact-token context snippets;
- deterministic tie-breaking;
- safe, versioned JSON index persistence;
- replacement-safe re-indexing; and
- randomized known-truth correctness audits.

Everything remains standard-library Python.

## A real correctness bug the audit found

The previous rebuild allowed `add("doc", new_text)` to overwrite the stored document text, but it did **not** remove the document from the old term and position postings.

So this sequence:

```python
engine.add("doc", "reactor design reactor")
engine.add("doc", "kinetic model only")
```

could still return `doc` for `reactor` and even for the phrase `reactor design`.

Version 0.4 gives `add()` explicit replacement semantics: all old postings are removed before the new document is indexed. A regression test locks that invariant down.

## Boolean and phrase retrieval

Boolean search intersects posting sets, so a document must contain **every** query token.

Phrase search uses token positions. For terms \(q_0, q_1, \ldots, q_k\), a phrase begins at position \(p\) only when term \(q_i\) occurs at \(p+i\) for every \(i\).

That makes:

```text
reactor design   -> match

design reactor   -> no match
reactor heat     -> no match unless adjacent
```

The semantics are validated against a separate brute-force reference implementation rather than only against hand-written examples.

## Ranking: BM25, but no unsupported relevance claim

Normal ranked search now defaults to BM25. The older TF-IDF-style score remains available via `--ranker tfidf`.

BM25 is useful here because it makes document-length normalisation and term-frequency saturation explicit. But this repository contains no human relevance judgements, so I do **not** claim that BM25 is empirically more relevant than TF-IDF on these four sample files. That would require a labelled retrieval benchmark, not an appealing result order.

Ranking ties are resolved by document name, which makes results reproducible across insertion order and Python set iteration.

## Persistence: why pickle was retired

Version 0.3 saved the index with Python `pickle`. That works for a trusted local object, but loading an untrusted pickle can execute arbitrary Python code.

Version 0.4 therefore uses a versioned JSON format and validates the stored document lengths and positional postings before accepting an index. Writes use a temporary file followed by an atomic replace.

This is a safer serialization boundary; it is not a claim that arbitrary hostile JSON is resource-safe at production scale.

## Known-truth audit

Run:

```bash
python src/audit.py
```

The checked-in default audit generates 100 random corpora and 20 random queries per corpus. It records:

| Check | Comparisons | Result |
|---|---:|---:|
| Boolean AND vs brute-force token scan | 2,000 | 2,000 matched |
| Exact phrase vs brute-force adjacent-token scan | 2,000 | 2,000 matched |
| BM25 ranking across different insertion orders | 2,000 | 2,000 identical |
| save/load query triplets | 500 | 500 identical |

A roundtrip triplet checks Boolean, phrase and ranked output after restoring the index, so those 500 triplets cover 1,500 restored retrieval outputs.

This is a **correctness and reproducibility** experiment. It is deliberately not presented as evidence of semantic search quality, web-scale latency or distributed scalability.

The machine-readable result is in `reports/correctness_audit.json`.

## Usage

```bash
python src/cli.py
python src/cli.py --query "kinetic models"                    # BM25
python src/cli.py --query "kinetic models" --ranker tfidf     # legacy score
python src/cli.py --query "reactor mixing" --and              # Boolean AND
python src/cli.py --query "reactor design" --phrase           # exact phrase
python src/cli.py --save-index search-index.json --query "reactor"
python src/cli.py --load-index search-index.json --query "reactor"
```

The original coursework tests can also be run separately:

```bash
python -m unittest discover original -v
```

## Test state

`pytest -q` runs both the preserved coursework tests and the modern suite.

- original audited archive: **10 passing tests total** (5 coursework + 5 rebuild tests);
- version 0.4: **22 passing tests total** (5 coursework + 17 rebuild/audit tests).

The new tests cover replacement correctness, deterministic ranking, BM25/TF-IDF modes, exact-token snippets, safe persistence validation, malformed indexes, UTF-8 directory loading and a reduced randomized known-truth audit.

## What this project does not claim

It is not:

- a web crawler or web-scale search engine;
- semantic/vector retrieval;
- a distributed index;
- a relevance-labelled benchmark;
- evidence that BM25 beats another ranker on real user judgements;
- a production security/performance audit.

See [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) for the full claim boundary and implementation notes.

## Next technically meaningful extensions

If I developed it further, the highest-value steps would be a relevance-labelled evaluation set (Precision@k/MRR/nDCG), Unicode-aware linguistic preprocessing, field weighting, and then profiling/compression on a genuinely larger corpus. Those would answer questions the current evidence cannot.

## Licence

MIT, see [LICENSE](LICENSE).
