"""Randomised known-truth correctness audit for the search engine.

This is deliberately a correctness/reproducibility benchmark, not a claim
about web-scale retrieval quality. Boolean and phrase results are compared
with a brute-force reference implementation on generated corpora; ranking is
checked for insertion-order invariance; JSON round-trips must preserve all
query modes exactly.
"""
from __future__ import annotations

import argparse
import json
import random
import tempfile
from pathlib import Path

from engine import SearchEngine, tokenize

VOCAB = [
    "reactor", "kinetics", "model", "search", "engine", "index", "python",
    "data", "heat", "mixing", "design", "query", "ranking", "experiment",
    "uncertainty", "parameter", "catalyst", "pressure", "temperature",
    "statistics", "algorithm", "document", "phrase", "token", "science",
]


def brute_boolean(docs: dict[str, str], query: str) -> list[str]:
    q = tokenize(query)
    if not q:
        return []
    return sorted(name for name, text in docs.items()
                  if all(term in set(tokenize(text)) for term in q))


def brute_phrase(docs: dict[str, str], query: str) -> list[str]:
    q = tokenize(query)
    if not q:
        return []
    hits = []
    for name, text in docs.items():
        toks = tokenize(text)
        n = len(q)
        if any(toks[i:i+n] == q for i in range(len(toks) - n + 1)):
            hits.append(name)
    return sorted(hits)


def generate_world(rng: random.Random, n_docs: int = 18) -> dict[str, str]:
    docs = {}
    for i in range(n_docs):
        length = rng.randint(20, 90)
        tokens = [rng.choice(VOCAB) for _ in range(length)]
        # Plant a few exact phrases without making every query trivial.
        if rng.random() < 0.45:
            phrase = rng.sample(VOCAB, 2)
            at = rng.randrange(0, max(1, len(tokens) - 1))
            tokens[at:at+2] = phrase
        docs[f"doc_{i:02d}"] = " ".join(tokens)
    return docs


def run_audit(worlds: int = 100, queries_per_world: int = 20,
              seed: int = 20260917) -> dict:
    rng = random.Random(seed)
    boolean_checks = 0
    phrase_checks = 0
    roundtrip_checks = 0
    order_invariance_checks = 0

    for _ in range(worlds):
        docs = generate_world(rng)
        engine = SearchEngine()
        for name, text in docs.items():
            engine.add(name, text)

        shuffled = list(docs.items())
        rng.shuffle(shuffled)
        engine_shuffled = SearchEngine()
        for name, text in shuffled:
            engine_shuffled.add(name, text)

        queries = []
        for _ in range(queries_per_world):
            qlen = rng.choice([1, 2, 2, 3])
            query = " ".join(rng.sample(VOCAB, qlen))
            queries.append(query)

            expected_and = brute_boolean(docs, query)
            expected_phrase = brute_phrase(docs, query)
            assert engine.boolean_and(query) == expected_and
            assert engine.phrase(query) == expected_phrase
            boolean_checks += 1
            phrase_checks += 1

            assert engine.search(query, top_k=10) == engine_shuffled.search(query, top_k=10)
            order_invariance_checks += 1

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "index.json"
            engine.save(path)
            loaded = SearchEngine.load(path)
            for query in queries[:5]:
                assert loaded.boolean_and(query) == engine.boolean_and(query)
                assert loaded.phrase(query) == engine.phrase(query)
                assert loaded.search(query, top_k=10) == engine.search(query, top_k=10)
                roundtrip_checks += 1

    return {
        "seed": seed,
        "worlds": worlds,
        "queries_per_world": queries_per_world,
        "boolean_reference_checks": boolean_checks,
        "phrase_reference_checks": phrase_checks,
        "ranking_insertion_order_checks": order_invariance_checks,
        "roundtrip_query_triplets": roundtrip_checks,
        "all_checks_passed": True,
        "scope_note": (
            "Generated-corpus correctness/reproducibility audit only; no human "
            "relevance judgements, web-scale latency or semantic-retrieval claim."
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--worlds", type=int, default=100)
    ap.add_argument("--queries", type=int, default=20)
    ap.add_argument("--seed", type=int, default=20260917)
    ap.add_argument("--out", type=Path,
                    default=Path("reports/correctness_audit.json"))
    args = ap.parse_args()
    result = run_audit(args.worlds, args.queries, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
