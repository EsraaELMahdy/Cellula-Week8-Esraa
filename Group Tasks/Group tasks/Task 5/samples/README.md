# Demonstration inputs

- `sales_image.png`: synthetically rendered English sales report. Ground-truth text is in `sales_reference.txt`. All amounts and the reporting period are illustrative fixture data, not business claims.
- `blank_image.png`: blank synthetic image to verify the no-readable-text response.
- `question.wav`: synthetic Windows SAPI text-to-speech saying “What is the total revenue?”; reference in `question_reference.txt`. It is not a microphone recording or team-member voice.

The actual input hashes, adapter outputs, durations and HTTP statuses are recorded by `scripts/live_demo.py` in `evidence/live_demo.json`. The question can be recorded manually through the UI as an additional browser/device check.
