# Cellula Technologies — Week 8 Final Submission

This repository contains the Week 8 submission, organized into the two directories requested by the internship team.

## Repository structure

```text
Individual Tasks/
├── Task 0 — Kimi K2 Architecture/
├── Task 1 — Qwen2.5-72B Architecture/
├── Task 2 — Qwen3-ASR-1.7B/
├── Task 3 — GAN Research/
└── Task 4 — Updated CV/
Group Tasks/
├── Task 5 — Agentic System/
├── Task 6 — Infrastructure as Code/
└── TEAM_ROLES.md
```

## Individual tasks

| Task | Deliverable |
|---|---|
| 0 | Three-page IEEE research paper on Kimi K2 architecture |
| 1 | Three-page IEEE research paper on Qwen2.5-72B architecture |
| 2 | IEEE research paper and practical Qwen3-ASR-1.7B experiment with real WER/CER, timing, and licensed audio samples |
| 3 | IEEE research paper on GANs, mathematical foundations, four focal papers, architectures, and applications |
| 4 | ATS-friendly updated CV in PDF |

## Group tasks

Task 5 extends the Week 7 Document Intelligence application with FastAPI, voice queries, image upload and OCR, and an agent that generates styled PDF reports. The voice-query feature belongs to Task 5; no separate Voice Agent project is included.

Task 6 prepares and validates Terraform configuration. It does not deploy cloud resources.

## Team roles

Task 5 and Task 6 ownership for Israa, Mariam, and Alaa is documented in [Group Tasks/TEAM_ROLES.md](Group%20Tasks/TEAM_ROLES.md).

| Member | Task 5 | Task 6 |
|---|---|---|
| Israa (Person A) | FastAPI, orchestration, integration, end-to-end demonstration | Integration, offline validation, documentation and evidence |
| Mariam (Person B) | Voice input, speech-to-text, image validation and OCR | Infrastructure architecture and core resources |
| Alaa (Person C) | Report-generation agent, PDF renderer and report design | Providers, variables, outputs and reusable interfaces |

## Task 2 recorded results

The recorded experiment contains 16 audio inputs from 10 speakers and 48 measured trials. Overall normalized WER is 2.508%, CER is 0.501%, and aggregate RTF is 0.2156. The results archive contains the audio samples, CSV results, environment details, and plot.

## Reproduction and security

Use the Task 2 notebook in Google Colab with a GPU runtime. Keep credentials, private environment files, Terraform state, and cloud secrets out of Git. Report only results and validation steps that were actually performed.
