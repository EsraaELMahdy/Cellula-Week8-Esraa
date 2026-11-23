from pathlib import Path

from docx import Document
from pypdf import PdfReader

SUPPORTED = (".pdf", ".docx", ".txt")


def load_file(path: str) -> list[dict]:
    """Read a file and return a list of pages: {"document", "page", "text"}."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = p.suffix.lower()
    name = p.name

    if ext == ".pdf":
        try:
            reader = PdfReader(str(p))
            return [
                {"document": name, "page": i + 1, "text": page.extract_text() or ""}
                for i, page in enumerate(reader.pages)
            ]
        except Exception as e:
            raise ValueError(f"Could not read the PDF {name}: {e}") from e

    if ext == ".docx":
        try:
            doc = Document(str(p))
        except Exception as e:
            raise ValueError(f"Could not read the DOCX {name}: {e}") from e
        lines = [par.text for par in doc.paragraphs]
        # tables often have the numbers, so we read them too
        for table in doc.tables:
            for row in table.rows:
                lines.append(" | ".join(cell.text for cell in row.cells))
        return [{"document": name, "page": 1, "text": "\n".join(lines)}]

    if ext == ".txt":
        text = p.read_text(encoding="utf-8", errors="ignore")
        return [{"document": name, "page": 1, "text": text}]

    raise ValueError(f"Unsupported file type: {ext or '(none)'}. Use one of {SUPPORTED}")
