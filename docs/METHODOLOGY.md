# Methodology and audit notes

## Scope

This repository is a small lexical information-retrieval project. It demonstrates indexing, Boolean retrieval, positional phrase search, lexical ranking, snippets, persistence and testing. It is **not** a web search engine, semantic/vector search system, distributed index or benchmark of production-scale latency.

The original 2021 COMP0015 coursework is preserved unchanged in `original/`. The modern rebuild is audited separately.

## Tokenisation

All modes use one tokenizer:

```text
[a-z0-9']+
```

with lower-casing. That gives internally consistent Boolean, phrase and ranking semantics, but it is intentionally simple: there is no stemming, lemmatisation, language detection or Unicode-aware linguistic normalisation.

## Inverted and positional indexes

For each term the engine stores:

- the set of documents containing the term; and
- exact token positions within each document.

Boolean AND search intersects posting sets. Exact phrase search uses positional intersection: for query terms `q_0 ... q_k`, a phrase begins at position `p` only if term `q_i` occurs at `p+i` for every `i`.

## Ranking

The audited default is BM25 with `k1=1.5` and `b=0.75`:

\[
\mathrm{score}(q,d)=\sum_{t\in q}\operatorname{IDF}(t)
\frac{f(t,d)(k_1+1)}{f(t,d)+k_1(1-b+b|d|/\overline{|d|})}.
\]

The positive IDF form is

\[
\operatorname{IDF}(t)=\log\left(1+\frac{N-n_t+0.5}{n_t+0.5}\right).
\]

The older length-normalised TF-IDF score remains available with `--ranker tfidf` for comparison. No claim is made that BM25 is superior on this repository's four sample documents: ranking quality requires relevance judgements, not an attractive ordering from one tiny corpus.

Ranking ties are broken by document name, so insertion order and Python set iteration do not change the returned ordering.

## Document replacement

`add(name, text)` has replacement semantics. The audit found that the previous implementation overwrote `docs[name]` but did not remove old posting lists or positions. Re-indexing a changed document could therefore leave deleted terms searchable. The audited implementation removes all old postings before inserting the replacement.

## Persistence and trust boundary

Version 0.3 persisted the full object state with Python `pickle`. Pickle is convenient for trusted local objects but **must not be loaded from untrusted sources**, because deserialisation can execute arbitrary Python code.

Version 0.4 uses a versioned JSON schema and validates:

- format identifier and schema version;
- document/length key agreement;
- posting document references;
- integer, sorted, unique, in-range token positions; and
- total positional-posting count against stored document length.

The write uses a temporary file followed by an atomic replace. JSON solves the code-execution problem; it does not make arbitrary huge/malicious data harmless, so index files should still be treated as untrusted data and resource limits would matter in a production service.

## Known-truth correctness audit

`python src/audit.py` generates 100 random corpora by default. For 20 random queries per corpus it compares:

1. Boolean AND output with a brute-force token scan;
2. phrase output with a brute-force adjacent-token scan;
3. BM25 ranking across two different document insertion orders; and
4. Boolean, phrase and ranked results before/after a JSON save-load roundtrip.

The default run therefore performs:

- 2,000 Boolean reference comparisons;
- 2,000 phrase reference comparisons;
- 2,000 insertion-order ranking comparisons; and
- 500 roundtrip query triplets (three retrieval modes each).

This is a **correctness/reproducibility audit**. It does not contain human relevance judgements, so it cannot establish search-quality superiority. It also does not establish web-scale latency or memory efficiency.

## Main limitations

- exact lexical matching only; no stemming or semantic retrieval;
- in-memory single-process index;
- no stopword policy;
- no field weighting, metadata filters or query parser;
- no relevance-labelled benchmark such as TREC;
- raw document text is retained for snippets;
- JSON persistence trades safety/auditability for larger files than a compressed binary index;
- no adversarial resource-exhaustion hardening.
