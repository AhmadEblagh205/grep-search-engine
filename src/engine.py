"""Small, auditable text-search engine built from first principles.

The engine keeps an inverted index and positional postings, supports Boolean
AND and exact phrase retrieval, and ranks lexical matches with BM25 (or a
legacy TF-IDF mode for comparison). Persisted indexes use a versioned JSON
format rather than pickle so loading an untrusted index does not execute code.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterable

TOKEN_RE = re.compile(r"[a-z0-9']+")
INDEX_FORMAT = "grep-search-engine-index"
INDEX_VERSION = 1


def tokenize(text: str) -> list[str]:
    """Lower-case alphanumeric/apostrophe tokenisation used everywhere."""
    return TOKEN_RE.findall(text.lower())


class SearchEngine:
    """In-memory inverted index with positional postings and lexical ranking."""

    def __init__(self):
        self.docs: dict[str, str] = {}
        self.doc_lengths: dict[str, int] = {}
        self.doc_terms: dict[str, set[str]] = {}
        self.index: dict[str, set[str]] = defaultdict(set)
        self.positions: dict[str, dict[str, list[int]]] = defaultdict(dict)

    # ---------- indexing ----------
    def _remove(self, name: str) -> None:
        """Remove a document and every posting that points to it."""
        if name not in self.docs:
            return
        for term in self.doc_terms.get(name, set()):
            self.index[term].discard(name)
            if not self.index[term]:
                del self.index[term]
            self.positions[term].pop(name, None)
            if not self.positions[term]:
                del self.positions[term]
        self.docs.pop(name, None)
        self.doc_lengths.pop(name, None)
        self.doc_terms.pop(name, None)

    def add(self, name: str, text: str) -> None:
        """Add or replace one document atomically at the logical index level.

        Re-using a document name means replacement. Old postings are removed
        first so deleted words cannot survive as stale search hits.
        """
        if not isinstance(name, str) or not name:
            raise ValueError("document name must be a non-empty string")
        if not isinstance(text, str):
            raise TypeError("document text must be a string")

        tokens = tokenize(text)
        new_positions: dict[str, list[int]] = defaultdict(list)
        for position, term in enumerate(tokens):
            new_positions[term].append(position)

        self._remove(name)
        self.docs[name] = text
        self.doc_lengths[name] = len(tokens)
        self.doc_terms[name] = set(new_positions)
        for term, positions in new_positions.items():
            self.index[term].add(name)
            self.positions[term][name] = positions

    def add_directory(self, folder: str | Path, pattern: str = "*.txt") -> None:
        """Index matching UTF-8 text files from one directory in sorted order."""
        folder = Path(folder)
        if not folder.is_dir():
            raise FileNotFoundError(f"not a directory: {folder}")
        for path in sorted(folder.glob(pattern)):
            if path.is_file():
                self.add(path.stem, path.read_text(encoding="utf-8"))

    # ---------- retrieval ----------
    def boolean_and(self, query: str) -> list[str]:
        """Return documents containing every token in the query."""
        terms = tokenize(query)
        if not terms:
            return []
        posting_sets = [self.index.get(term, set()) for term in terms]
        if any(not postings for postings in posting_sets):
            return []
        return sorted(set.intersection(*posting_sets))

    def phrase(self, query: str) -> list[str]:
        """Return documents containing the exact adjacent token sequence."""
        terms = tokenize(query)
        if not terms:
            return []
        if any(term not in self.index for term in terms):
            return []

        candidates = set.intersection(*(self.index[term] for term in terms))
        hits: list[str] = []
        for doc in sorted(candidates):
            starts = set(self.positions[terms[0]][doc])
            for offset, term in enumerate(terms[1:], 1):
                starts &= {position - offset
                           for position in self.positions[term][doc]}
                if not starts:
                    break
            if starts:
                hits.append(doc)
        return hits

    def _tfidf_score(self, term: str, doc: str) -> float:
        """Legacy length-normalised TF-IDF contribution used for comparison."""
        n_docs = len(self.docs)
        df = len(self.index.get(term, ()))
        if not n_docs or not df or not self.doc_lengths[doc]:
            return 0.0
        tf = len(self.positions[term][doc]) / self.doc_lengths[doc]
        idf = math.log(n_docs / df) + 1.0
        return tf * idf

    def _bm25_score(self, term: str, doc: str,
                    *, k1: float = 1.5, b: float = 0.75) -> float:
        """Robertson/Sparck Jones BM25 term contribution with positive IDF."""
        n_docs = len(self.docs)
        if not n_docs:
            return 0.0
        df = len(self.index.get(term, ()))
        if not df:
            return 0.0
        tf = len(self.positions[term][doc])
        avgdl = sum(self.doc_lengths.values()) / n_docs
        dl = self.doc_lengths[doc]
        if avgdl <= 0:
            return 0.0
        idf = math.log(1.0 + (n_docs - df + 0.5) / (df + 0.5))
        denom = tf + k1 * (1.0 - b + b * dl / avgdl)
        return idf * (tf * (k1 + 1.0) / denom) if denom else 0.0

    def search(self, query: str, top_k: int = 5, *,
               ranker: str = "bm25") -> list[tuple[str, float]]:
        """Rank documents containing at least one query term.

        ``ranker='bm25'`` is the default. ``ranker='tfidf'`` retains the
        previous project's simple TF-IDF scoring for comparison. Ties are
        broken by document name so results are reproducible across runs and
        insertion orders.
        """
        if top_k < 0:
            raise ValueError("top_k must be non-negative")
        if ranker not in {"bm25", "tfidf"}:
            raise ValueError("ranker must be 'bm25' or 'tfidf'")
        if top_k == 0:
            return []

        terms = Counter(tokenize(query))
        scores: dict[str, float] = defaultdict(float)
        for term, qtf in terms.items():
            for doc in self.index.get(term, ()):
                if ranker == "bm25":
                    contribution = self._bm25_score(term, doc)
                else:
                    contribution = self._tfidf_score(term, doc)
                scores[doc] += qtf * contribution

        ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
        return ranked[:top_k]

    def snippet(self, doc: str, query: str, width: int = 90) -> str:
        """Return context around the first exact query token in the document."""
        if doc not in self.docs:
            raise KeyError(doc)
        if width <= 0:
            raise ValueError("width must be positive")
        text = self.docs[doc]
        query_terms = set(tokenize(query))
        first_span = None
        for match in TOKEN_RE.finditer(text.lower()):
            if match.group(0) in query_terms:
                first_span = match.span()
                break
        if first_span is None:
            return text[:width].replace("\n", " ")

        start = max(0, first_span[0] - width // 2)
        end = min(len(text), first_span[1] + width // 2)
        snippet = text[start:end].replace("\n", " ")
        return ("..." if start else "") + snippet + ("..." if end < len(text) else "")

    # ---------- persistence ----------
    def _state(self) -> dict:
        return {
            "format": INDEX_FORMAT,
            "version": INDEX_VERSION,
            "documents": self.docs,
            "doc_lengths": self.doc_lengths,
            "positions": {
                term: {doc: positions for doc, positions in docs.items()}
                for term, docs in self.positions.items()
            },
        }

    def save(self, path: str | Path) -> None:
        """Persist the index as versioned JSON with an atomic file replace.

        Unlike pickle, JSON loading does not execute arbitrary Python code.
        The file should still be treated as untrusted *data*: schema and
        posting invariants are validated on load.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self._state(), ensure_ascii=False,
                             separators=(",", ":"), sort_keys=True)
        with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                delete=False) as tmp:
            tmp.write(payload)
            tmp_path = Path(tmp.name)
        tmp_path.replace(path)

    @classmethod
    def load(cls, path: str | Path) -> "SearchEngine":
        """Load and validate a versioned JSON index."""
        path = Path(path)
        state = json.loads(path.read_text(encoding="utf-8"))
        if state.get("format") != INDEX_FORMAT:
            raise ValueError("unrecognised index format")
        if state.get("version") != INDEX_VERSION:
            raise ValueError(f"unsupported index version: {state.get('version')!r}")
        docs = state.get("documents")
        lengths = state.get("doc_lengths")
        positions = state.get("positions")
        if not isinstance(docs, dict) or not isinstance(lengths, dict) or not isinstance(positions, dict):
            raise ValueError("malformed index state")
        if set(docs) != set(lengths):
            raise ValueError("document/length keys do not match")

        engine = cls()
        engine.docs = {str(name): str(text) for name, text in docs.items()}
        engine.doc_lengths = {}
        engine.doc_terms = {name: set() for name in engine.docs}

        for name, raw_length in lengths.items():
            if not isinstance(raw_length, int) or raw_length < 0:
                raise ValueError("invalid document length")
            engine.doc_lengths[name] = raw_length

        for term, per_doc in positions.items():
            if not isinstance(term, str) or not isinstance(per_doc, dict):
                raise ValueError("malformed positional postings")
            for doc, raw_positions in per_doc.items():
                if doc not in engine.docs or not isinstance(raw_positions, list):
                    raise ValueError("posting references unknown document")
                if (not all(isinstance(p, int) and 0 <= p < engine.doc_lengths[doc]
                            for p in raw_positions)
                        or raw_positions != sorted(set(raw_positions))):
                    raise ValueError("invalid token positions")
                engine.positions[term][doc] = raw_positions
                engine.index[term].add(doc)
                engine.doc_terms[doc].add(term)

        # The saved postings must exactly partition each token position count.
        for doc, length in engine.doc_lengths.items():
            count = sum(len(engine.positions[t][doc])
                        for t in engine.doc_terms[doc])
            if count != length:
                raise ValueError("posting counts do not match document length")
        return engine

    def stats(self) -> dict[str, float | int]:
        """Small corpus/index summary useful for the CLI and audits."""
        n_docs = len(self.docs)
        total_tokens = sum(self.doc_lengths.values())
        return {
            "documents": n_docs,
            "unique_terms": len(self.index),
            "tokens": total_tokens,
            "mean_document_tokens": total_tokens / n_docs if n_docs else 0.0,
        }
