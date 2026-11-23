import pytest
from docx import Document

from retriever import store
from retriever.chunker import chunk_pages
from retriever.context_selector import select_context
from retriever.ingest import ingest_file
from retriever.keyword import keyword_search
from retriever.loader import load_file
from retriever.metadata_filter import build_filter
from retriever.query_rewriter import rewrite_query
from retriever.reranker import rerank
from retriever.retrieve import retrieve
from retriever.store import get_all_chunks, list_documents, semantic_search

CNN_TEXT = "The CNN model reached an accuracy of 92 percent on the test set."
FOOD_TEXT = "The recipe needs two cups of flour, one egg and a little sugar."


def write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return str(p)


# ---------- loader ----------

def test_load_txt(tmp_path):
    pages = load_file(write(tmp_path, "a.txt", "hello world"))
    assert pages == [{"document": "a.txt", "page": 1, "text": "hello world"}]


def test_load_docx_reads_paragraphs_and_tables(tmp_path):
    doc = Document()
    doc.add_paragraph("Results of the experiment")
    table = doc.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "CNN"
    table.rows[0].cells[1].text = "92"
    doc.save(tmp_path / "r.docx")
    pages = load_file(str(tmp_path / "r.docx"))
    assert "Results of the experiment" in pages[0]["text"]
    assert "CNN | 92" in pages[0]["text"]


def test_load_pdf_keeps_page_numbers(tmp_path, make_pdf):
    path = make_pdf(tmp_path / "p.pdf", ["first page text", "second page text"])
    pages = load_file(str(path))
    assert [p["page"] for p in pages] == [1, 2]
    assert "first page" in pages[0]["text"] and "second page" in pages[1]["text"]
    assert all(p["document"] == "p.pdf" for p in pages)


def test_unsupported_file_type(tmp_path):
    with pytest.raises(ValueError, match="Unsupported"):
        load_file(write(tmp_path, "a.xlsx", "x"))


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        load_file("does_not_exist.pdf")


def test_broken_pdf(tmp_path):
    with pytest.raises(ValueError):
        load_file(write(tmp_path, "bad.pdf", "this is not a pdf"))


def test_empty_file_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="No readable text"):
        ingest_file(write(tmp_path, "empty.txt", "   \n  "))
    assert list_documents() == []


# ---------- chunker ----------

def test_chunks_keep_document_and_page():
    pages = [{"document": "a.pdf", "page": 3, "text": "word " * 400},
             {"document": "a.pdf", "page": 4, "text": "other " * 400}]
    chunks = chunk_pages(pages)
    assert len(chunks) > 2
    assert {(c["document"], c["page"]) for c in chunks} == {("a.pdf", 3), ("a.pdf", 4)}
    assert len({c["chunk_id"] for c in chunks}) == len(chunks)
    assert all(len(c["text"]) <= 500 for c in chunks)


def test_empty_pages_make_no_chunks():
    assert chunk_pages([{"document": "a.pdf", "page": 1, "text": "  "}]) == []


# ---------- store (ChromaDB) ----------

def test_chunks_are_stored(tmp_path):
    n = ingest_file(write(tmp_path, "a.txt", CNN_TEXT))
    stored = get_all_chunks()
    assert n == len(stored) == 1
    assert stored[0]["document"] == "a.txt" and stored[0]["page"] == 1


def test_uploading_again_does_not_duplicate(tmp_path):
    path = write(tmp_path, "a.txt", CNN_TEXT)
    ingest_file(path)
    ingest_file(path)
    assert len(get_all_chunks()) == 1


def test_uploading_again_does_not_delete_other_documents(tmp_path):
    ingest_file(write(tmp_path, "a.txt", CNN_TEXT))
    ingest_file(write(tmp_path, "b.txt", FOOD_TEXT))
    ingest_file(write(tmp_path, "a.txt", "A new version of the first document."))
    assert list_documents() == ["a.txt", "b.txt"]
    assert [c["content"] for c in get_all_chunks({"document": "b.txt"})] == [FOOD_TEXT]
    assert [c["content"] for c in get_all_chunks({"document": "a.txt"})] == ["A new version of the first document."]


# ---------- search ----------

def test_semantic_search_finds_relevant_chunk(tmp_path):
    ingest_file(write(tmp_path, "cnn.txt", CNN_TEXT))
    ingest_file(write(tmp_path, "food.txt", FOOD_TEXT))
    results = semantic_search("What accuracy did the CNN model get?", k=2)
    assert results[0]["document"] == "cnn.txt"
    assert {"document", "page", "content", "score"} <= set(results[0])


def test_keyword_search_finds_exact_term(tmp_path):
    ingest_file(write(tmp_path, "cnn.txt", "We fine-tuned BERT-base for the task. " + CNN_TEXT))
    ingest_file(write(tmp_path, "food.txt", FOOD_TEXT))
    results = keyword_search("BERT-base", k=3)
    assert results[0]["document"] == "cnn.txt"


def test_keyword_search_works_with_a_single_chunk(tmp_path):
    ingest_file(write(tmp_path, "only.txt", CNN_TEXT))
    assert len(keyword_search("accuracy", k=3)) == 1


def test_keyword_search_no_match(tmp_path):
    ingest_file(write(tmp_path, "only.txt", CNN_TEXT))
    assert keyword_search("zebra", k=3) == []


# ---------- metadata filter ----------

def test_filter_by_document_and_page(tmp_path):
    ingest_file(write(tmp_path, "paper.txt", CNN_TEXT))
    assert build_filter("What is the accuracy?") is None
    assert build_filter("According to paper.txt, what is the accuracy?") == {"document": "paper.txt"}
    assert build_filter("What is on page 5?") == {"page": 5}
    assert build_filter("In paper.txt page 2, what is it?") == {"$and": [{"document": "paper.txt"}, {"page": 2}]}


def test_filter_limits_retrieval(tmp_path):
    ingest_file(write(tmp_path, "a.txt", "The model accuracy is 92 percent."))
    ingest_file(write(tmp_path, "b.txt", "The model accuracy is 95 percent."))
    results = retrieve("According to b.txt, what is the model accuracy?")
    assert results and {r["document"] for r in results} == {"b.txt"}


# ---------- reranker and context selector ----------

def test_reranker_puts_best_first():
    candidates = [
        {"document": "f.txt", "page": 1, "score": 0.1, "content": FOOD_TEXT},
        {"document": "c.txt", "page": 1, "score": 0.1, "content": CNN_TEXT},
    ]
    ranked = rerank("What accuracy did the CNN model reach?", candidates)
    assert ranked[0]["document"] == "c.txt"
    assert ranked[0]["score"] >= ranked[1]["score"]
    assert rerank("anything", []) == []


def test_context_selector_removes_duplicates_and_limits():
    items = [{"document": "a", "page": 1, "score": 3, "content": "the cat sat on the mat"},
             {"document": "b", "page": 2, "score": 2, "content": "the cat sat on the mat"},
             {"document": "c", "page": 3, "score": 1, "content": "a totally different sentence"},
             {"document": "d", "page": 4, "score": 0, "content": "one more different text here"}]
    selected = select_context(items, max_chunks=5)
    assert [i["document"] for i in selected] == ["a", "c", "d"]
    assert len(select_context(items, max_chunks=2)) == 2


# ---------- retrieve (all tools together) ----------

def test_retrieve_returns_required_fields(tmp_path):
    ingest_file(write(tmp_path, "cnn.txt", CNN_TEXT))
    ingest_file(write(tmp_path, "food.txt", FOOD_TEXT))
    results = retrieve("What accuracy did the CNN model reach?", max_chunks=2)
    assert results[0]["document"] == "cnn.txt"
    for r in results:
        assert {"document", "page", "content", "score"} <= set(r)


def test_retrieve_on_empty_database():
    assert retrieve("anything at all") == []


def test_retrieve_empty_question():
    with pytest.raises(ValueError):
        retrieve("   ")


def test_extra_query_is_used(tmp_path):
    ingest_file(write(tmp_path, "cnn.txt", CNN_TEXT))
    ingest_file(write(tmp_path, "food.txt", FOOD_TEXT))
    results = retrieve("tell me more", extra_query="flour egg sugar recipe", max_chunks=1)
    assert results[0]["document"] == "food.txt"


# ---------- query rewriter ----------

def test_rewriter_without_history_returns_question():
    assert rewrite_query("What is RAG?") == "What is RAG?"


def test_rewriter_without_key_returns_question(monkeypatch, capsys):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    history = [{"role": "user", "content": "What is RAG?"}]
    assert rewrite_query("What are its limits?", history) == "What are its limits?"
    assert "WARNING" in capsys.readouterr().out
