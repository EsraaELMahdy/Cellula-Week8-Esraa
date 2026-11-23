"""Coordinates Part A -> Part B -> Part C."""
from retriever.retrieve import retrieve
from analyst.analyst import analyze
from answer_agent.agent import answer_question


def run_workflow(question: str, history=None, max_rounds=3):
    if not question or not question.strip():
        raise ValueError("Question cannot be empty")
    evidence = retrieve(question, history=history)
    analysis = analyze(question, evidence, history=history, max_rounds=max_rounds)
    response = answer_question(question, analysis, history=history)
    response["rounds"] = analysis.get("rounds", 0)
    response["searches"] = analysis.get("searches", [])
    response["analysis"] = analysis.get("analysis", "")
    response["results"] = {key: analysis.get(key) for key in ["calculation", "table", "stats", "comparison"]}
    return response
