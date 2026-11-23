import json

import pytest

from analyst import analyst as analyst_module
from analyst import llm
from analyst.analyst import analyze, check_evidence, run_calculation
from analyst.calculator import calculate
from analyst.comparison import compare_documents
from analyst.data_analysis import analyse_table
from analyst.table_extractor import extract_table
from retriever.ingest import ingest_file
from retriever.retrieve import retrieve

EV_A = {"document": "a.pdf", "page": 5, "score": 2.0, "content": "Paper A: the CNN accuracy is 92%."}
EV_B = {"document": "b.pdf", "page": 2, "score": 1.5, "content": "Paper B: the CNN accuracy is 95%."}
EV_C = {"document": "c.pdf", "page": 7, "score": 1.0, "content": "Paper C: the CNN accuracy is 89%."}

TABLE = [
    {"document": "a.pdf", "page": 5, "item": "Paper A", "metric": "accuracy", "value": 92.0},
    {"document": "b.pdf", "page": 2, "item": "Paper B", "metric": "accuracy", "value": 95.0},
    {"document": "c.pdf", "page": 7, "item": "Paper C", "metric": "accuracy", "value": 89.0},
]


def fake_llm(monkeypatch, handler):
    """Replace the LLM call. handler(system, user) returns the text of the answer."""
    monkeypatch.setattr(llm, "ask_llm", handler)


def say(data):
    return json.dumps(data)


# ---------- Calculator ----------

def test_calculator_operations():
    assert calculate("add", [1, 2, 3]) == 6
    assert calculate("multiply", [2, 3, 4]) == 24
    assert calculate("average", [92, 95, 89]) == 92
    assert calculate("difference", [95, 92]) == 3
    assert calculate("divide", [10, 4]) == 2.5
    assert calculate("percent_change", [80, 92]) == 15
    assert calculate("percent_of", [25, 200]) == 12.5


@pytest.mark.parametrize("operation,numbers", [
    ("divide", [1, 0]), ("percent_change", [0, 5]), ("percent_of", [5, 0]),
    ("difference", [1, 2, 3]), ("average", []), ("power", [2, 3]),
])
def test_calculator_rejects_invalid_input(operation, numbers):
    with pytest.raises(ValueError):
        calculate(operation, numbers)


# ---------- Table Extractor ----------

def test_table_extractor_keeps_source_and_rejects_invented_numbers(monkeypatch):
    rows = [
        {"source": 1, "item": "Paper A", "metric": "accuracy", "value": "92%"},
        {"source": 2, "item": "Paper B", "metric": "accuracy", "value": 95},
        {"source": 1, "item": "Paper A", "metric": "recall", "value": 77},   # number is not in the chunk
        {"source": 9, "item": "Paper X", "metric": "accuracy", "value": 92},  # chunk does not exist
        {"source": 0, "item": "Paper Y", "metric": "accuracy", "value": 92},  # bad chunk number
        {"item": "no source", "metric": "accuracy", "value": 92},              # missing field
    ]
    fake_llm(monkeypatch, lambda s, u: say({"rows": rows}))
    table, warnings = extract_table([EV_A, EV_B])
    assert table == [
        {"document": "a.pdf", "page": 5, "item": "Paper A", "metric": "accuracy", "value": 92.0},
        {"document": "b.pdf", "page": 2, "item": "Paper B", "metric": "accuracy", "value": 95.0},
    ]
    assert len(warnings) == 4


def test_table_extractor_invalid_answer(monkeypatch):
    fake_llm(monkeypatch, lambda s, u: say({"something": "else"}))
    with pytest.raises(llm.LLMError):
        extract_table([EV_A])


# ---------- Data Analysis ----------

def test_data_analysis_statistics_and_ranking():
    stats = analyse_table(TABLE)["accuracy"]
    assert stats["count"] == 3
    assert stats["average"] == 92.0
    assert stats["highest"] == {"item": "Paper B", "value": 95.0}
    assert stats["lowest"] == {"item": "Paper C", "value": 89.0}
    assert [r["item"] for r in stats["ranking"]] == ["Paper B", "Paper A", "Paper C"]


def test_data_analysis_empty():
    assert analyse_table([]) == {}


# ---------- run_calculation (uses only table numbers) ----------

def test_calculation_uses_table_numbers(monkeypatch):
    fake_llm(monkeypatch, lambda s, u: say({"operation": "average", "metric": "accuracy", "items": []}))
    calc, warning = run_calculation("average accuracy?", TABLE)
    assert warning == ""
    assert calc["result"] == 92.0
    assert [u["document"] for u in calc["used"]] == ["a.pdf", "b.pdf", "c.pdf"]


def test_calculation_difference_between_two_items(monkeypatch):
    fake_llm(monkeypatch, lambda s, u: say({"operation": "difference", "metric": "accuracy",
                                           "items": ["Paper B", "Paper C"]}))
    calc, _ = run_calculation("how much better is B than C?", TABLE)
    assert calc["result"] == 6.0


def test_calculation_rejects_items_not_in_table(monkeypatch):
    fake_llm(monkeypatch, lambda s, u: say({"operation": "difference", "metric": "accuracy",
                                           "items": ["Paper B", "Paper Z"]}))
    calc, warning = run_calculation("?", TABLE)
    assert calc is None and "Paper Z" in warning


def test_calculation_rejects_unknown_metric(monkeypatch):
    fake_llm(monkeypatch, lambda s, u: say({"operation": "average", "metric": "price", "items": []}))
    calc, warning = run_calculation("?", TABLE)
    assert calc is None and "price" in warning


def test_calculation_none(monkeypatch):
    fake_llm(monkeypatch, lambda s, u: say({"operation": "none"}))
    assert run_calculation("?", TABLE) == (None, "")


# ---------- Document Comparison ----------

def test_comparison_sends_all_documents(monkeypatch):
    seen = {}

    def handler(system, user):
        seen["user"] = user
        return "A and B agree."

    fake_llm(monkeypatch, handler)
    assert compare_documents("compare", [EV_B, EV_A]) == "A and B agree."
    assert "a.pdf, page 5" in seen["user"] and "b.pdf, page 2" in seen["user"]
    assert seen["user"].index("a.pdf") < seen["user"].index("b.pdf")  # sorted by document


def test_comparison_needs_two_documents():
    with pytest.raises(ValueError):
        compare_documents("compare", [EV_A])


# ---------- Feedback loop ----------

def test_analyst_asks_retriever_for_more_evidence(monkeypatch, tmp_path):
    """Real Part A retriever: the first evidence has only paper A, the Analyst must find paper B."""
    (tmp_path / "a.txt").write_text("Paper A reports a CNN accuracy of 92 percent.", encoding="utf-8")
    (tmp_path / "b.txt").write_text("Paper B reports a transformer latency of 40 ms.", encoding="utf-8")
    ingest_file(str(tmp_path / "a.txt"))
    ingest_file(str(tmp_path / "b.txt"))
    evidence = retrieve("Paper A CNN accuracy", max_chunks=1)
    assert [e["document"] for e in evidence] == ["a.txt"]

    def handler(system, user):
        if "check if the evidence" in system:
            if "Paper B reports" in user:
                return say({"enough": True, "missing": ""})
            return say({"enough": False, "missing": "Paper B transformer latency"})
        return "final analysis"

    fake_llm(monkeypatch, handler)
    result = analyze("Compare the CNN accuracy and the transformer latency", evidence)
    assert result["rounds"] == 1
    assert result["searches"] == ["Paper B transformer latency"]
    assert result["enough_evidence"] is True
    assert {e["document"] for e in result["evidence"]} == {"a.txt", "b.txt"}
    assert all(e["page"] == 1 for e in result["evidence"])


def make_endless_loop(monkeypatch):
    """LLM always says 'not enough' with a new query, and each search adds one new chunk."""
    counter = {"checks": 0, "searches": 0}

    def handler(system, user):
        if "check if the evidence" in system:
            counter["checks"] += 1
            return say({"enough": False, "missing": f"query number {counter['checks']}"})
        return "partial analysis"

    def stub_search(question, query, evidence, history=None):
        counter["searches"] += 1
        new = {"document": "x.pdf", "page": counter["searches"], "score": 1, "content": f"text {query}"}
        return evidence + [new], 1

    fake_llm(monkeypatch, handler)
    monkeypatch.setattr(analyst_module, "search_more", stub_search)
    return counter


def test_loop_stops_after_max_rounds(monkeypatch):
    counter = make_endless_loop(monkeypatch)
    result = analyze("question", [EV_A])
    assert result["rounds"] == 3 == counter["searches"]
    assert len(result["searches"]) == 3
    assert result["enough_evidence"] is False


def test_loop_respects_a_custom_max_rounds(monkeypatch):
    make_endless_loop(monkeypatch)
    assert analyze("question", [EV_A], max_rounds=1)["rounds"] == 1
    assert analyze("question", [EV_A], max_rounds=0)["rounds"] == 0


def test_insufficient_evidence_is_reported_honestly(monkeypatch):
    make_endless_loop(monkeypatch)
    result = analyze("question", [EV_A])
    assert result["enough_evidence"] is False
    assert result["missing"].startswith("query number")
    assert "Missing information: query number" in result["analysis"]


def test_loop_stops_when_search_finds_nothing_new(monkeypatch):
    fake_llm(monkeypatch, lambda s, u: say({"enough": False, "missing": "something"})
             if "check if the evidence" in s else "text")
    monkeypatch.setattr(analyst_module, "search_more", lambda q, query, ev, h=None: (ev, 0))
    result = analyze("question", [EV_A])
    assert result["rounds"] == 1 and result["enough_evidence"] is False
    assert any("nothing new" in w for w in result["warnings"])


def test_loop_stops_when_the_same_query_repeats(monkeypatch):
    fake_llm(monkeypatch, lambda s, u: say({"enough": False, "missing": "same query"})
             if "check if the evidence" in s else "text")
    monkeypatch.setattr(analyst_module, "search_more",
                        lambda q, query, ev, h=None: (ev + [{"document": "x", "page": len(ev), "content": "t"}], 1))
    result = analyze("question", [EV_A])
    assert result["rounds"] == 1
    assert any("same search" in w for w in result["warnings"])


def test_retriever_failure_is_reported(monkeypatch):
    fake_llm(monkeypatch, lambda s, u: say({"enough": False, "missing": "more"})
             if "check if the evidence" in s else "text")

    def broken(*args, **kwargs):
        raise RuntimeError("ChromaDB error")

    monkeypatch.setattr(analyst_module, "search_more", broken)
    result = analyze("question", [EV_A])
    assert result["enough_evidence"] is False
    assert any("ChromaDB error" in w for w in result["warnings"])


# ---------- LLM failures: never assume the evidence is enough ----------

def test_llm_failure_is_not_treated_as_enough(monkeypatch):
    def broken(system, user):
        raise llm.LLMError("LLM request failed: timeout")

    fake_llm(monkeypatch, broken)
    result = analyze("question", [EV_A])
    assert result["enough_evidence"] is False
    assert "timeout" in result["missing"]
    assert any("timeout" in w for w in result["warnings"])
    assert result["evidence"] == [EV_A]


def test_invalid_json_is_not_treated_as_enough(monkeypatch):
    fake_llm(monkeypatch, lambda s, u: "sorry, I cannot answer in JSON")
    check = check_evidence("question", [EV_A])
    assert check["enough"] is False and "valid JSON" in check["error"]


def test_json_without_enough_field_is_invalid(monkeypatch):
    fake_llm(monkeypatch, lambda s, u: say({"missing": ""}))
    check = check_evidence("question", [EV_A])
    assert check["enough"] is False and check["error"]


def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(llm.LLMError, match="OPENROUTER_API_KEY"):
        llm.ask_llm("system", "user")
    result = analyze("question", [EV_A])
    assert result["enough_evidence"] is False
    assert any("OPENROUTER_API_KEY" in w for w in result["warnings"])


def test_placeholder_key_is_rejected(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "put_your_key_here")
    with pytest.raises(llm.LLMError, match="OPENROUTER_API_KEY"):
        llm.ask_llm("system", "user")


def test_empty_evidence_asks_the_retriever_then_reports(monkeypatch):
    fake_llm(monkeypatch, lambda s, u: "text")
    monkeypatch.setattr(analyst_module, "search_more", lambda q, query, ev, h=None: (ev, 0))
    result = analyze("What is the accuracy?", [])
    assert result["enough_evidence"] is False
    assert result["evidence"] == [] and result["missing"] == "What is the accuracy?"


def test_malformed_evidence_is_ignored(monkeypatch):
    fake_llm(monkeypatch, lambda s, u: say({"enough": True, "missing": ""})
             if "check if the evidence" in s else "text")
    bad = [{"content": "no document"}, {"document": "a.pdf", "page": 1}, "not a dict", EV_A]
    result = analyze("question", bad)
    assert result["evidence"] == [EV_A]
    assert len(result["warnings"]) == 3


# ---------- Full run of the Analyst ----------

def test_full_analysis_output(monkeypatch):
    def handler(system, user):
        if "check if the evidence" in system:
            return say({"enough": True, "missing": "", "needs_numbers": True, "needs_comparison": True})
        if "extract numbers" in system:
            return say({"rows": [
                {"source": 1, "item": "Paper A", "metric": "accuracy", "value": 92},
                {"source": 2, "item": "Paper B", "metric": "accuracy", "value": 95},
                {"source": 3, "item": "Paper C", "metric": "accuracy", "value": 89}]})
        if "choose one calculation" in system:
            return say({"operation": "average", "metric": "accuracy", "items": []})
        if "compare documents" in system:
            return "Paper B is the best."
        return "The average accuracy is 92%."

    fake_llm(monkeypatch, handler)
    result = analyze(question="What is the average CNN accuracy?", evidence=[EV_A, EV_B, EV_C])

    for key in ["question", "analysis", "enough_evidence", "evidence", "rounds", "searches",
                "calculation", "table", "stats", "comparison"]:
        assert key in result
    assert result["enough_evidence"] is True and result["rounds"] == 0
    assert result["calculation"]["result"] == 92.0
    assert [(r["document"], r["page"]) for r in result["table"]] == [("a.pdf", 5), ("b.pdf", 2), ("c.pdf", 7)]
    assert result["stats"]["accuracy"]["highest"]["item"] == "Paper B"
    assert result["comparison"] == "Paper B is the best."
    assert result["analysis"] == "The average accuracy is 92%."
    assert result["warnings"] == []
