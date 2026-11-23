import re

from analyst import llm
from analyst.utils import format_evidence

SYSTEM = (
    "You extract numbers from text. Return JSON only, in this form: "
    '{"rows": [{"source": 1, "item": "Paper A", "metric": "accuracy", "value": 92}]}. '
    "source is the number of the evidence chunk, like [1]. "
    "item is the thing measured (a model, a company, a year ...). "
    "metric is what was measured (accuracy, price, ...). "
    "value must be copied exactly as it is written in the chunk (92% becomes 92). "
    "Use only numbers that appear in the text. Do not invent anything. "
    'If there are no numbers return {"rows": []}.'
)


def numbers_in(text: str) -> list[float]:
    text = re.sub(r"(?<=\d),(?=\d{3}\b)", "", str(text))  # 1,000 -> 1000
    return [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", text)]


def extract_table(evidence: list[dict]) -> tuple[list[dict], list[str]]:
    """Find numbers in the evidence. Returns (rows, warnings).

    The model only says which chunk a number came from. The document name and
    the page are taken from that chunk by the code, and every number is checked
    to be really inside the chunk text.
    """
    data = llm.ask_json(SYSTEM, format_evidence(evidence))
    if not isinstance(data, dict) or not isinstance(data.get("rows"), list):
        raise llm.LLMError("The table extractor got an invalid answer from the LLM.")

    rows, warnings = [], []
    for row in data["rows"]:
        try:
            source = int(row["source"])
            if source < 1:
                raise ValueError
            chunk = evidence[source - 1]
            value = float(str(row["value"]).replace("%", "").replace(",", ""))
            if value not in numbers_in(chunk["content"]):
                raise ValueError
        except (KeyError, TypeError, ValueError, IndexError):
            warnings.append(f"A number from the LLM was rejected because it is not in the evidence: {row}")
            continue
        rows.append({
            "document": chunk["document"],
            "page": chunk["page"],
            "item": str(row.get("item", "")),
            "metric": str(row.get("metric", "")),
            "value": value,
        })
    return rows, warnings
