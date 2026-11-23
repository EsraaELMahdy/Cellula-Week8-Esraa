import sys

from analyst.analyst import analyze
from retriever.ingest import ingest_file
from retriever.retrieve import retrieve

# usage: python run_analyst.py paper.pdf "What is the average accuracy?"
if len(sys.argv) != 3:
    print('Usage: python run_analyst.py <file.pdf|docx|txt> "<question>"')
    sys.exit(1)

path, question = sys.argv[1], sys.argv[2]

try:
    count = ingest_file(path)
    print(f"Stored {count} chunks from {path}\n")
    evidence = retrieve(question)
    result = analyze(question=question, evidence=evidence)
except (FileNotFoundError, ValueError, RuntimeError) as e:
    print("Error:", e)
    sys.exit(1)

print("ANALYSIS")
print(result["analysis"])

if result["calculation"]:
    c = result["calculation"]
    print(f'\nCALCULATION: {c["operation"]} of {c["metric"]} = {c["result"]}')
    for u in c["used"]:
        print(f'  {u["item"]} = {u["value"]}  ({u["document"]}, page {u["page"]})')

print("\nSOURCES")
for e in result["evidence"]:
    print(f'  {e["document"]}, page {e["page"]} (score {e.get("score", "-")})')

print(f'\nEnough evidence: {result["enough_evidence"]} | extra rounds: {result["rounds"]}')
if result["warnings"]:
    print("WARNINGS")
    for w in result["warnings"]:
        print("  -", w)
