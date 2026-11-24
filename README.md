# Cellula Technologies — Week 8 Submission

Esraa ElMahdy — NLP & AI Internship, Cellula Technologies

This repository is organized into the two directories requested by the internship team.

## Repository structure

```text
Individual Tasks/
├── Task 0 — Kimi K2 Architecture/
├── Task 1 — Qwen2.5-72B Architecture/
├── Task 2 — Qwen3-ASR-1.7B/
├── Task 3 — GAN Research/
└── Task 4 — Updated CV/
Group Tasks/
├── Group tasks/
│   ├── Task 5/   (Agentic System)
│   └── Task 6/   (Infrastructure as Code)
└── TEAM_ROLES.md
```

## Individual tasks

| Task | Deliverable |
|---|---|
| 0 | IEEE-format research paper on the Kimi K2 architecture |
| 1 | IEEE-format research paper on the Qwen2.5-72B architecture |
| 2 | IEEE-format paper on Qwen3-ASR-1.7B (architecture analysis and CPU-based evaluation) plus the notebook with its recorded outputs |
| 3 | IEEE-format research paper on Generative Adversarial Networks (mathematical foundations, training, advanced architectures, applications) |
| 4 | Updated CV |

### Task 2 recorded results

The model was run on a Google Colab **CPU** runtime (2 cores, float32, no GPU) on 10 LibriSpeech utterances from 10 different speakers (5 from `test.clean`, 5 from `test.other`).

| Split | Mean WER | Mean CER |
|---|---|---|
| clean | 2.1% | 0.2% |
| other | 3.3% | 0.7% |
| all | 2.7% | 0.5% |

Processing took about 4 seconds per second of audio (real-time factor ≈ 4.0) and the loaded model used about 9.3 GB of RAM. Most counted errors came from punctuation and spelling conventions rather than mis-heard words. The evaluation is small and covers read English speech only; limitations are discussed in the paper.

To reproduce, open `Task2_CPU.ipynb` in Google Colab and run the cells in order. The notebook already contains the outputs from the recorded run.

## Group tasks

Task 5 extends the Week 7 Document Intelligence application with FastAPI, voice queries, image upload with OCR, and an agent that generates styled PDF reports. The voice-query feature belongs to Task 5; no separate Voice Agent project is included.

Task 6 prepares and validates Terraform configuration for hosting the Task 5 application on AWS. It does not deploy cloud resources.

## Team roles

Task 5 and Task 6 ownership is documented in [Group Tasks/TEAM_ROLES.md](Group%20Tasks/TEAM_ROLES.md).

| Member | Task 5 | Task 6 |
|---|---|---|
| Israa (Person A) | FastAPI, orchestration, integration, end-to-end demonstration | Integration, offline validation, documentation and evidence |
| Mariam (Person B) | Voice input, speech-to-text, image validation and OCR | Infrastructure architecture and core resources |
| Alaa (Person C) | Report-generation agent, PDF renderer and report design | Providers, variables, outputs and reusable interfaces |

## Security

Credentials, private environment files, Terraform state, and cloud secrets are kept out of Git.