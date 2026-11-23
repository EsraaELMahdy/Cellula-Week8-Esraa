# Week 8 Group Tasks — Team Roles

Members: Israa, Mariam, and Alaa.

## Task 5 — Agentic System

| Owner | Role | Files / outcomes |
|---|---|---|
| Israa (Person A) | API, orchestration, integration | FastAPI routes and schemas; connect input adapters and report generation to the Week 7 application; end-to-end demo |
| Mariam (Person B) | Voice and OCR inputs | Microphone/audio upload, speech-to-text, image validation and Python OCR; pass normalized text and metadata to the API |
| Alaa (Person C) | Report-generation agent | Structured report content, dynamic style selection, PDF rendering, and report download integration |

## Task 6 — Infrastructure as Code

| Owner | Role | Files / outcomes |
|---|---|---|
| Israa (Person A) | Integration, verification, documentation | Match Terraform to the Task 5 architecture; run and record `terraform fmt -check`, `terraform init -backend=false`, `terraform validate`, and the agreed no-account plan test; maintain the final README |
| Mariam (Person B) | Architecture and core resources | Map the application dependencies and implement justified compute, networking, logging, storage, and permissions resources |
| Alaa (Person C) | Providers, variables, and outputs | Pin provider/Terraform versions; define typed reusable variables, sensitive inputs, outputs, and example configuration |

## Shared interfaces

- Agree the API and Terraform interfaces before parallel implementation.
- Use the existing Week 7 Document Intelligence application as the base after reviewing its current code.
- Keep credentials and private variables out of Git.
- Task 6 prepares infrastructure only. Do not run `terraform apply` against a real cloud provider.
- Record only commands and results that were actually run. A mocked Terraform plan test is not the same as the standalone `terraform plan` command.
