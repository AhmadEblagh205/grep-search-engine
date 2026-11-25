# Inverted-Index Search Engine

[![CI](https://github.com/AhmadEblagh205/grep-search-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/AhmadEblagh205/grep-search-engine/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

This is a small lexical search engine that I built twice. The first version was my 2021 UCL COMP0015 coursework, which I keep unchanged in `original/`. The second is my own rebuild in `src/`, which uses the same inverted-index idea and adds phrase search, BM25 ranking, deterministic results and safe index saving. The coursework searched BBC news files. That corpus is not redistributed here, so the original code and tests are kept for provenance only.

## What it does

- Builds an inverted index with positional postings.
- Answers Boolean AND queries and exact adjacent-phrase queries.
- Ranks results with BM25, with the earlier TF-IDF-style score still available.
- Shows context snippets, and breaks ties by document name so results are reproducible.
- Saves and loads the index as versioned JSON. Re-adding a document replaces its old postings.

Everything is standard-library Python.

## Results

The correctness audit (`python src/audit.py`) runs 100 randomly generated corpora with 20 random queries each. The corpora are synthetic, so every answer can be checked against a brute-force reference.

| Check | Comparisons | Result |
|---|---:|---:|
| Boolean AND vs brute-force token scan | 2,000 | 2,000 matched |
| Exact phrase vs brute-force adjacent-token scan | 2,000 | 2,000 matched |
| BM25 ranking across different insertion orders | 2,000 | 2,000 identical |
| save/load query triplets | 500 | 500 identical |

The audit also found a bug in my earlier rebuild. Re-adding a document under the same name left its old terms in the index, so it could still match queries for text it no longer contained. That is fixed and covered by a test. The output is in `reports/correctness_audit.json`.

I have no human relevance judgements, so I make no claim that BM25 ranks better than TF-IDF on the four sample files.

## How to run

```bash
python src/cli.py
python src/cli.py --query "kinetic models"                    # BM25
python src/cli.py --query "kinetic models" --ranker tfidf     # legacy score
python src/cli.py --query "reactor mixing" --and              # Boolean AND
python src/cli.py --query "reactor design" --phrase           # exact phrase
python src/cli.py --save-index search-index.json --query "reactor"
python src/cli.py --load-index search-index.json --query "reactor"
python src/audit.py
pytest -q
```

`pytest -q` runs both the preserved coursework tests and the new suite. The coursework tests can also be run on their own:

```bash
python -m unittest discover original -v
```

Version 0.4 has 22 passing tests, 5 from the coursework and 17 from the rebuild and audit. The original audited archive had 10.

## Notes

This is not a web-scale or semantic search engine, and the audit checks correctness and reproducibility only. The index used to be saved with `pickle`, which can run arbitrary code on load, so it now uses JSON. The bug description, phrase-matching rule, persistence details and ideas for further work are in [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

## Licence

MIT, see [LICENSE](LICENSE).
