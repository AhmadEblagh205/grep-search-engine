"""Interactive search over a folder of text files.

Usage:
    python src/cli.py
    python src/cli.py --query "kinetic models"
    python src/cli.py --query "reactor mixing" --and
    python src/cli.py --query "reactor design" --phrase
"""
import argparse
from pathlib import Path

from engine import SearchEngine

ROOT = Path(__file__).resolve().parents[1]


def show(engine: SearchEngine, query: str, use_and: bool,
         phrase: bool = False, ranker: str = "bm25") -> None:
    if phrase:
        hits = engine.phrase(query)
        print(f"phrase search - {len(hits)} document(s) contain the exact sequence:")
        for doc in hits:
            print(f"  {doc}: {engine.snippet(doc, query)}")
        return
    if use_and:
        hits = engine.boolean_and(query)
        print(f"AND search - {len(hits)} document(s) contain every term:")
        for doc in hits:
            print(f"  {doc}: {engine.snippet(doc, query)}")
        return

    results = engine.search(query, ranker=ranker)
    if not results:
        print("  no matches")
    for rank, (doc, score) in enumerate(results, 1):
        print(f"  {rank}. {doc}  ({ranker} {score:.4f})")
        print(f"     {engine.snippet(doc, query)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=ROOT / "data" / "sample")
    ap.add_argument("--query", help="run one query and exit")
    ap.add_argument("--and", dest="use_and", action="store_true",
                    help="Boolean AND instead of ranked search")
    ap.add_argument("--phrase", action="store_true",
                    help="exact adjacent-token match")
    ap.add_argument("--ranker", choices=["bm25", "tfidf"], default="bm25",
                    help="lexical ranker for normal search (default: bm25)")
    ap.add_argument("--save-index", metavar="PATH",
                    help="index the corpus and persist a safe versioned JSON index")
    ap.add_argument("--load-index", metavar="PATH",
                    help="skip corpus indexing and load a saved JSON index")
    args = ap.parse_args()

    if args.load_index:
        engine = SearchEngine.load(args.load_index)
        stats = engine.stats()
        print(f"Loaded index: {stats['documents']} documents, "
              f"{stats['unique_terms']} unique terms")
    else:
        engine = SearchEngine()
        engine.add_directory(args.dir)
        stats = engine.stats()
        print(f"Indexed {stats['documents']} documents, "
              f"{stats['unique_terms']} unique terms from {args.dir}")

    if args.save_index:
        engine.save(args.save_index)
        print(f"Saved versioned JSON index -> {args.save_index}")

    if args.query:
        show(engine, args.query, args.use_and, args.phrase, args.ranker)
        return

    print("Type a query (blank line to quit). Prefix with AND: for Boolean search.")
    while True:
        try:
            query = input("search> ").strip()
        except EOFError:
            break
        if not query:
            break
        if query.upper().startswith("AND:"):
            show(engine, query[4:], True, ranker=args.ranker)
        else:
            show(engine, query, False, ranker=args.ranker)


if __name__ == "__main__":
    main()
