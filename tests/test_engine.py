import json
from pathlib import Path

import pytest

from audit import run_audit
from engine import SearchEngine, tokenize


def _engine():
    e = SearchEngine()
    e.add("d1", "the reactor design handles mixing and heat")
    e.add("d2", "search engines rank documents by relevance")
    e.add("d3", "reactor kinetics and kinetic models")
    return e


def test_tokenize_is_case_and_punctuation_normalised():
    assert tokenize("Reactor, MODEL'S heat!") == ["reactor", "model's", "heat"]


def test_boolean_and_requires_every_term():
    e = _engine()
    assert e.boolean_and("reactor mixing") == ["d1"]
    assert e.boolean_and("reactor absent") == []
    assert e.boolean_and("") == []


def test_ranked_search_orders_by_relevance():
    e = _engine()
    results = e.search("reactor kinetics")
    assert results[0][0] == "d3"
    assert results[0][1] > results[1][1]


def test_tfidf_mode_remains_available():
    e = _engine()
    results = e.search("reactor kinetics", ranker="tfidf")
    assert results[0][0] == "d3"


def test_ranked_ties_are_deterministic_by_document_name():
    a = SearchEngine()
    a.add("z", "reactor")
    a.add("a", "reactor")
    b = SearchEngine()
    b.add("a", "reactor")
    b.add("z", "reactor")
    assert [d for d, _ in a.search("reactor")] == ["a", "z"]
    assert a.search("reactor") == b.search("reactor")


def test_replacing_document_removes_stale_postings_and_positions():
    e = SearchEngine()
    e.add("doc", "reactor design reactor")
    assert e.boolean_and("reactor") == ["doc"]
    assert e.phrase("reactor design") == ["doc"]
    e.add("doc", "kinetic model only")
    assert e.boolean_and("reactor") == []
    assert e.phrase("reactor design") == []
    assert e.boolean_and("kinetic") == ["doc"]


def test_phrase_queries_need_adjacency_and_order():
    e = _engine()
    assert e.phrase("reactor design") == ["d1"]
    assert e.phrase("design reactor") == []
    assert e.phrase("reactor heat") == []
    assert e.phrase("kinetic models") == ["d3"]


def test_snippet_contains_exact_query_token():
    e = SearchEngine()
    e.add("d", "reactors are plural; a reactor is singular")
    snippet = e.snippet("d", "reactor", width=50).lower()
    assert "a reactor" in snippet


def test_snippet_validates_document_and_width():
    e = _engine()
    with pytest.raises(KeyError):
        e.snippet("missing", "reactor")
    with pytest.raises(ValueError):
        e.snippet("d1", "reactor", width=0)


def test_search_validates_top_k_and_ranker():
    e = _engine()
    assert e.search("reactor", top_k=0) == []
    with pytest.raises(ValueError):
        e.search("reactor", top_k=-1)
    with pytest.raises(ValueError):
        e.search("reactor", ranker="magic")


def test_json_index_roundtrip_preserves_all_modes(tmp_path):
    e = _engine()
    path = tmp_path / "idx.json"
    e.save(path)
    loaded = SearchEngine.load(path)
    assert loaded.search("reactor") == e.search("reactor")
    assert loaded.search("reactor", ranker="tfidf") == e.search("reactor", ranker="tfidf")
    assert loaded.phrase("reactor design") == e.phrase("reactor design")
    assert loaded.boolean_and("reactor mixing") == e.boolean_and("reactor mixing")
    assert loaded.docs == e.docs
    assert json.loads(path.read_text())["format"] == "grep-search-engine-index"


def test_load_rejects_wrong_format_and_version(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"format": "wrong", "version": 1}))
    with pytest.raises(ValueError, match="format"):
        SearchEngine.load(path)
    path.write_text(json.dumps({"format": "grep-search-engine-index", "version": 99}))
    with pytest.raises(ValueError, match="version"):
        SearchEngine.load(path)


def test_load_rejects_invalid_postings(tmp_path):
    e = _engine()
    path = tmp_path / "idx.json"
    e.save(path)
    state = json.loads(path.read_text())
    state["positions"]["reactor"]["d1"] = [999]
    path.write_text(json.dumps(state))
    with pytest.raises(ValueError, match="positions"):
        SearchEngine.load(path)


def test_add_directory_reads_sorted_utf8_text_files(tmp_path):
    (tmp_path / "b.txt").write_text("kinetics", encoding="utf-8")
    (tmp_path / "a.txt").write_text("café reactor", encoding="utf-8")
    e = SearchEngine()
    e.add_directory(tmp_path)
    assert list(e.docs) == ["a", "b"]
    assert e.boolean_and("reactor") == ["a"]


def test_add_directory_rejects_missing_folder(tmp_path):
    with pytest.raises(FileNotFoundError):
        SearchEngine().add_directory(tmp_path / "missing")


def test_stats_are_consistent():
    e = _engine()
    stats = e.stats()
    assert stats["documents"] == 3
    assert stats["tokens"] == sum(len(tokenize(t)) for t in e.docs.values())
    assert stats["unique_terms"] == len(e.index)


def test_small_randomised_known_truth_audit_passes():
    result = run_audit(worlds=3, queries_per_world=5, seed=7)
    assert result["all_checks_passed"] is True
    assert result["boolean_reference_checks"] == 15
    assert result["phrase_reference_checks"] == 15
    assert result["ranking_insertion_order_checks"] == 15
    assert result["roundtrip_query_triplets"] == 15
