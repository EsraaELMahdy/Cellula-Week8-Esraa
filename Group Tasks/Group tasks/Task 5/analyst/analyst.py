from analyst import llm
from analyst.calculator import calculate
from analyst.comparison import compare_documents, count_documents
from analyst.data_analysis import analyse_table
from analyst.search_more import search_more
from analyst.table_extractor import extract_table
from analyst.utils import clean_evidence, format_evidence

CHECK_SYSTEM = (
    "You check if the evidence is enough to answer the question. "
    "Judge only by the evidence, not by your own knowledge. "
    "Return JSON only, in this form: "
    '{"enough": true, "missing": "", "needs_numbers": false, "needs_comparison": false}. '
    "If the evidence is not enough, put a short and specific search query for the "
    "missing information in missing. "
    "needs_numbers is true if the answer needs a calculation or a ranking of numbers. "
    "needs_comparison is true if the question compares documents or models."
)

CALC_SYSTEM = (
    "You choose one calculation that answers the question, using the numbers in the table. "
    "Return JSON only, in this form: "
    '{"operation": "average", "metric": "accuracy", "items": []}. '
    "operation is one of: add, multiply, average, difference, divide, percent_change, percent_of, none. "
    "metric must be copied from the table. "
    "items is the list of item names to use, in order (for difference it is first minus second, "
    "for percent_change it is from the first to the second). "
    "Leave items empty to use every item of that metric. "
    'If no calculation is needed, use {"operation": "none"}.'
)

WRITE_SYSTEM = (
    "You are an analyst. Use only the evidence and the numbers you are given. "
    "Explain what the evidence says about the question, compare and conclude. "
    "Mention the document name and page for each fact. "
    "If the evidence is not enough, say clearly what is missing. "
    "Do not invent anything. Answer in the same language as the question."
)


def check_evidence(question: str, evidence: list[dict]) -> dict:
    """Ask the LLM if the evidence is enough. If the LLM fails, we say NOT enough."""
    result = {"enough": False, "missing": "", "needs_numbers": False,
              "needs_comparison": False, "error": ""}
    if not evidence:
        result["missing"] = question
        return result

    try:
        data = llm.ask_json(CHECK_SYSTEM, "Question: " + question + "\n\nEvidence:\n" + format_evidence(evidence))
    except llm.LLMError as e:
        result["error"] = str(e)
        return result

    if not isinstance(data, dict) or not isinstance(data.get("enough"), bool):
        result["error"] = "The LLM gave an invalid answer when checking the evidence."
        return result

    result["enough"] = data["enough"]
    result["missing"] = str(data.get("missing") or "").strip()
    result["needs_numbers"] = data.get("needs_numbers") is True
    result["needs_comparison"] = data.get("needs_comparison") is True
    return result


def run_calculation(question: str, table: list[dict]) -> tuple[dict | None, str]:
    """Choose a calculation with the LLM, but compute it with our own code on table numbers.

    Returns (calculation or None, warning text).
    """
    lines = [f'{r["item"]} | {r["metric"]} | {r["value"]}' for r in table]
    data = llm.ask_json(CALC_SYSTEM, "Question: " + question + "\n\nTable:\n" + "\n".join(lines))
    if not isinstance(data, dict):
        return None, "The LLM gave an invalid calculation plan."
    operation = str(data.get("operation", "none"))
    if operation == "none":
        return None, ""

    metric = str(data.get("metric", "")).lower()
    rows = [r for r in table if r["metric"].lower() == metric]
    items = data.get("items") or []
    if items:
        chosen = []
        for name in items:
            found = [r for r in rows if r["item"].lower() == str(name).lower()]
            if not found:
                return None, f'Calculation skipped: "{name}" with metric "{metric}" is not in the extracted table.'
            chosen.append(found[0])
        rows = chosen
    if not rows:
        return None, f'Calculation skipped: metric "{metric}" is not in the extracted table.'

    try:
        result = calculate(operation, [r["value"] for r in rows])
    except ValueError as e:
        return None, f"Calculation skipped: {e}"

    used = [{"item": r["item"], "value": r["value"], "document": r["document"], "page": r["page"]}
            for r in rows]
    return {"operation": operation, "metric": metric, "used": used, "result": result}, ""


def write_analysis(question, evidence, table, stats, calculation, comparison, enough) -> str:
    parts = ["Question: " + question, "Evidence:\n" + format_evidence(evidence)]
    if table:
        parts.append("Numbers found:\n" + "\n".join(
            f'{r["item"]} | {r["metric"]} | {r["value"]} ({r["document"]}, page {r["page"]})'
            for r in table))
    if stats:
        parts.append("Statistics: " + str(stats))
    if calculation:
        parts.append(f'Calculation: {calculation["operation"]} of {calculation["metric"]} '
                     f'= {calculation["result"]}')
    if comparison:
        parts.append("Comparison:\n" + comparison)
    if not enough:
        parts.append("Note: the evidence is not enough to fully answer the question.")
    return llm.ask_llm(WRITE_SYSTEM, "\n\n".join(parts))


def analyze(question: str, evidence: list[dict], history: list | None = None,
            max_rounds: int = 3) -> dict:
    warnings = []
    evidence, bad = clean_evidence(evidence)
    warnings += bad

    # feedback loop: check the evidence, ask the Retriever for more if something is missing
    asked = []
    rounds = 0
    check = check_evidence(question, evidence)
    while not check["enough"] and check["missing"] and rounds < max_rounds:
        query = check["missing"]
        if query in asked:
            warnings.append(f'Stopped: the same search came again ("{query}").')
            break
        asked.append(query)
        try:
            evidence, added = search_more(question, query, evidence, history)
        except Exception as e:
            warnings.append(f"The Retriever failed: {e}")
            break
        rounds += 1
        if added == 0:
            warnings.append(f'The search "{query}" found nothing new.')
            break
        check = check_evidence(question, evidence)

    if check["error"]:
        warnings.append(check["error"])

    table, stats, calculation, comparison = [], {}, None, None

    if check["needs_numbers"]:
        try:
            table, extra = extract_table(evidence)
            warnings += extra
            stats = analyse_table(table)
            if table:
                calculation, warning = run_calculation(question, table)
                if warning:
                    warnings.append(warning)
        except llm.LLMError as e:
            warnings.append(f"Numbers could not be analysed: {e}")

    if check["needs_comparison"]:
        if count_documents(evidence) < 2:
            warnings.append("Comparison skipped: the evidence comes from only one document.")
        else:
            try:
                comparison = compare_documents(question, evidence)
            except llm.LLMError as e:
                warnings.append(f"Comparison failed: {e}")

    # what is missing, written by the code so it is always reported
    missing = ""
    if not check["enough"]:
        missing = check["missing"] or check["error"] or "The evidence could not be checked."

    try:
        analysis = write_analysis(question, evidence, table, stats, calculation,
                                  comparison, check["enough"])
    except llm.LLMError as e:
        warnings.append(f"The analysis text could not be written: {e}")
        analysis = "The analysis text could not be written. See the evidence, table and stats."
    if missing:
        analysis += "\n\nMissing information: " + missing

    return {
        "question": question,
        "analysis": analysis,
        "enough_evidence": check["enough"],
        "missing": missing,
        "evidence": evidence,
        "rounds": rounds,
        "searches": asked,
        "calculation": calculation,
        "table": table,
        "stats": stats,
        "comparison": comparison,
        "warnings": warnings,
    }
