# Changelog

## 0.4.0 — defensibility audit

- Fixed stale postings when a document is re-indexed under an existing name.
- Made ranked ties deterministic by document name.
- Added BM25 as the default lexical ranker; retained the earlier TF-IDF mode for comparison.
- Replaced pickle persistence with a safe versioned JSON representation and invariant validation.
- Made index writes atomic through temporary-file replacement.
- Made snippets anchor to exact query tokens rather than raw substring search.
- Added explicit input validation and UTF-8 directory reads.
- Added a randomized known-truth correctness/reproducibility audit against brute-force reference retrieval.
- Added `docs/METHODOLOGY.md` and machine-readable audit output.
- Expanded the full pytest state from 10 to 22 passing tests (including the five preserved coursework tests).

## 0.3.0, update round 9

Index persistence: save and load the whole index (postings, positions, documents, tokens) through pickle, exposed as save-index and load-index flags so a large corpus is indexed once, not per query.

## 0.2.0, update round 4

Added phrase queries through positional postings: the index now records token positions and the engine resolves exact adjacent sequences, exposed as a phrase flag on the CLI.

## 0.1.0

Initial release.
