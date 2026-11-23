# Verification evidence

## Application checks

`pytest_results.txt` records the actual baseline plus Task 5 regression run. `application_verification.json` records the Python/package versions, baseline Git commit and verification boundaries. Offline regression tests replace downloaded retrieval models and external LLM calls with mocks; these tests do not prove live model answer quality.

`live_demo.json` records separate real RapidOCR and Faster-Whisper execution through the API. The English image and speech adapters are real; answering is explicitly extractive. The synthetic spoken question is transcribed and used to retrieve the image-derived revenue passage. It is not a microphone or team-member recording. HTTP status, timing, file hashes, extracted text, transcript and selected styles are included.

`sample_report_blue.pdf` and `sample_report_purple.pdf` are actual downloadable API-generated reports of the same application response with different agent-selected designs. `long_report_fixture.pdf` is a synthetic pagination/results-table stress fixture; `arabic_layout_fixture.pdf` is a short Arabic rendering fixture. These two fixtures are not model experiments or business results. All report pages were rendered and visually inspected.

`localhost_http.json` records a real Uvicorn HTTP health request and serving of the expected UI controls. JavaScript syntax was checked separately with Node. Browser microphone permission/device recording was not exercised by this automated run. No live OpenRouter success, Docker build or cloud deployment is claimed.

Terraform evidence is independent, under the Task 6 `evidence/` directory. Its standalone AWS-provider plan and mock-provider test results are clearly distinguished.
