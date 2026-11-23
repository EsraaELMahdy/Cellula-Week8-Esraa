"""Person C: bounded design planning; selects tools/styles, never changes evidence."""
import os
from .schemas import ReportStyle


def plan_report(result: dict, brief: str, override: ReportStyle | None = None):
    if override is not None:
        return override, "explicit_style", "Validated style supplied by the user."
    b = brief.lower()
    numeric = bool((result.get("results") or {}).get("table"))
    style = ReportStyle(
        font="serif" if any(w in b for w in ["academic", "serif", "formal", "أكاديمي"]) else "mono" if "mono" in b else "sans",
        orientation="landscape" if numeric or "landscape" in b else "portrait",
        color="#6A2C70" if "purple" in b else "#1E684D" if "green" in b else "#174A75",
        body_size=12 if any(w in b for w in ["large", "accessible", "كبير"]) else 9 if "compact" in b else 10,
        spacing=4 if "compact" in b else 10 if "accessible" in b else 7,
        margin=50 if "formal" in b else 42,
        emphasis="plain" if "plain" in b else "bold",
        page_size="Letter" if "letter" in b else "A4")
    # Optional LLM planner chooses only bounded design fields; output content stays unchanged.
    if os.getenv("REPORT_PLANNER", "rules") == "llm":
        try:
            from analyst.llm import ask_json
            proposed = ask_json(
                "You plan PDF design only. Return a JSON object matching the provided schema. "
                "Do not supply facts, text, paths, font files, code or URLs.",
                f"Brief: {brief}\nSchema: {ReportStyle.model_json_schema()}\n"
                f"Has numerical table: {numeric}; answer characters: {len(result.get('answer', ''))}")
            return ReportStyle.model_validate(proposed), "llm", "LLM plan passed all style bounds."
        except Exception:
            return style, "rules_fallback", "LLM design unavailable; used the bounded local planner."
    return style, "rules", "Local design agent selected tools from the brief and result structure."
