import hashlib
import math
import os
import re

import pytest

from retriever import reranker, store

# OFFLINE_TESTS=1 replaces ONLY the two downloaded models (embeddings and reranker)
# with very simple word-based versions. Use it when you have no internet.
# It checks that the code works together, but it does NOT test the real models.
OFFLINE = os.getenv("OFFLINE_TESTS") == "1"


def fake_embed(texts):
    vectors = []
    for text in texts:
        vec = [0.0] * 256
        for word in re.findall(r"\w+", text.lower()):
            vec[int(hashlib.md5(word.encode()).hexdigest(), 16) % 256] += 1
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        vectors.append([x / norm for x in vec])
    return vectors


class FakeReranker:
    def rerank(self, query, documents):
        words = set(re.findall(r"\w+", query.lower()))
        for doc in documents:
            yield float(len(words & set(re.findall(r"\w+", doc.lower()))))


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    """Every test gets its own empty ChromaDB folder."""
    monkeypatch.setattr(store, "DB_PATH", str(tmp_path / "db"))
    monkeypatch.setattr(store, "_col", None)
    if OFFLINE:
        monkeypatch.setattr(store, "embed", fake_embed)
        monkeypatch.setattr(reranker, "_get_model", lambda: FakeReranker())


@pytest.fixture
def make_pdf():
    """Create a small PDF where every string in `pages` is one page."""
    def build(path, pages):
        n = len(pages)
        kids = " ".join(f"{4 + 2 * i} 0 R" for i in range(n))
        objs = [
            "<< /Type /Catalog /Pages 2 0 R >>",
            f"<< /Type /Pages /Kids [{kids}] /Count {n} >>",
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        ]
        for i, text in enumerate(pages):
            objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                        f"/Contents {5 + 2 * i} 0 R /Resources << /Font << /F1 3 0 R >> >> >>")
            stream = f"BT /F1 12 Tf 50 700 Td ({text}) Tj ET"
            objs.append(f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream")
        out = "%PDF-1.4\n"
        offsets = []
        for i, obj in enumerate(objs, start=1):
            offsets.append(len(out.encode()))
            out += f"{i} 0 obj\n{obj}\nendobj\n"
        xref = len(out.encode())
        out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n"
        out += "".join(f"{o:010d} 00000 n \n" for o in offsets)
        out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF"
        path.write_bytes(out.encode("latin-1"))
        return path
    return build
