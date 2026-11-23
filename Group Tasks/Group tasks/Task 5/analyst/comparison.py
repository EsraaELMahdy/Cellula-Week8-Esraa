from analyst import llm
from analyst.utils import format_evidence

SYSTEM = (
    "You compare documents. Use only the evidence given, never your own knowledge. "
    "Write the similarities and the differences between the documents, "
    "and mention the document name and page for every point. "
    "If something is not in the evidence, say it is not mentioned. Keep it short. "
    "Answer in the same language as the question."
)


def count_documents(evidence: list[dict]) -> int:
    return len({e["document"] for e in evidence})


def compare_documents(question: str, evidence: list[dict]) -> str:
    if count_documents(evidence) < 2:
        raise ValueError("Comparison needs evidence from at least 2 documents.")
    # sort by document so the chunks of one file stay together
    ordered = sorted(evidence, key=lambda e: (e["document"], str(e["page"])))
    user_msg = "Question: " + question + "\n\nEvidence:\n" + format_evidence(ordered)
    return llm.ask_llm(SYSTEM, user_msg)
