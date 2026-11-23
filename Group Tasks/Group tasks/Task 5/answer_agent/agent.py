"""Grounded answer generation using the existing Part B LLM adapter."""
from analyst import llm
from .formatter import format_sources, format_response

SYSTEM = """You are the Answer Agent in a document-question-answering system.
Use ONLY the provided analysis and document evidence. Never invent facts or sources.
Write in the language of the user's question. Cite factual claims inline using
[filename, p. N], exactly as listed in the provided evidence. Do not cite a source
that is not provided. If evidence is insufficient, clearly state the limitation.
Provide a clear, concise final answer, using a table when appropriate."""


def answer_question(question: str, analysis_result: dict, history=None) -> dict:
    evidence = analysis_result.get("evidence") or []
    sources = format_sources(evidence)
    sufficient = analysis_result.get("enough_evidence", False)
    warnings = list(analysis_result.get("warnings") or [])

    history_text = "\n".join(
        f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
        for msg in (history or [])[-10:]
    )

    if not evidence:
        return format_response("I couldn't find supporting evidence in the uploaded documents.", [], False, warnings)
    context = "\n\n".join(
        f'[{e.get("document")}, p. {e.get("page")}]\n{e.get("content", "")}'
        for e in evidence
    )
    
    prompt = (
        f"Conversation history:\n{history_text or 'No previous messages.'}\n\n"
        f"Current question: {question}\n\n"
        f"Analysis: {analysis_result.get('analysis', '')}\n\n"
        f"Evidence:\n{context}\n\n"
        f"Enough evidence: {sufficient}\n"
        f"Missing: {analysis_result.get('missing', '')}"
    )

    try:
        answer = llm.ask_llm(SYSTEM, prompt)
    except llm.LLMError as exc:
        warnings.append(f"Answer generation failed: {exc}")
        answer = analysis_result.get("analysis") or "Unable to generate an answer."
    if not sufficient:
        missing = analysis_result.get("missing")
        if missing:
            answer += f"\n\nInsufficient evidence: {missing}"
    return format_response(answer, sources, sufficient, warnings)
