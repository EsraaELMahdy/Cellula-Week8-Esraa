# Task 6 Infrastructure as Code

AWS configuration for the Task 5 application. This submission prepares infrastructure; it does not deploy it. Do not run `terraform apply` for this assignment.

## Architecture

The application uses one CPU host because its ChromaDB, session memory, response cache and report registry are local and are not designed for multiple replicas. The infrastructure defines a VPC, public subnet, Internet gateway, route table/association, restricted application security group, CloudWatch log group, EC2 role/policy/profile and one EC2 instance. The instance runs the Task 5 Docker image on port 8000 with one worker.

- `t3.large` provides an illustrative 8-GiB CPU starting point, not a measured capacity guarantee. INT8 speech, OCR and embeddings run locally; OpenRouter provides the LLM.
- A 50-GiB encrypted gp3 root volume contains `/opt/document-ai/data`, bind-mounted as `/data`. ChromaDB and model caches use that directory. The volume is retained on instance termination, but a replacement instance does not automatically reattach it. Backup/restore and migration are future operational work.
- Reports expire after 24 hours when report endpoints run and are capped at 128 files in the active registry. Conversation and response registries are process-local and reset on restart. Uploaded originals are removed after indexing; extracted source text remains in ChromaDB.
- Ingress allows port 8000 only from `allowed_cidr`; SSH is not opened. HTTPS outbound supports model downloads, Docker images, SSM, logs and OpenRouter. HTTP outbound permits first-boot package-repository redirects. The VPC resolver supplies DNS.
- The role can read only the two named SSM parameters and write application log streams. SecureString values are fetched at boot, not passed to Terraform. The design assumes the default AWS-managed SSM key; a customer-managed KMS key needs separately scoped decrypt permission.

This is a restricted single-host deployment design, not a highly available public service. A public browser microphone workflow needs an HTTPS reverse proxy/domain/certificate before deployment; the HTTP endpoint is for a trusted restricted demonstration. It does not provide tenant isolation, shared distributed memory, automated backups, or HA. No deployment or cloud-capacity test is claimed.

## Files and module responsibilities

| Label | Scope | Files |
|---|---|---|
| Person B | Architecture and infrastructure resources | `main.tf`, `user_data.sh.tftpl` |
| Person C | Provider configuration, inputs and outputs | `providers.tf`, `variables.tf`, `outputs.tf`, `terraform.tfvars.example` |
| Person A | Integration, validation and documentation | `verify.py`, `tests/offline.tftest.hcl`, this README, `evidence/` |

Labels follow the agreed work breakdown and organize review responsibilities. They are not a record of individual commits or who executed the recorded commands.

## No-account verification

Tested CLI: Terraform 1.9.8. Provider: `hashicorp/aws` 5.100.0, pinned with `.terraform.lock.hcl`. Internet is needed for the initial provider download; AWS credentials and an AWS account are not needed for the empty-state offline workflow.

```powershell
terraform fmt -check -recursive
terraform init -backend=false -input=false
terraform validate
terraform plan -refresh=false -input=false -var="offline_plan=true"
terraform test
```

Or run `python verify.py` to save actual stdout/stderr and exit codes. `--terraform C:\path\terraform.exe` selects a specific executable. Verification results are in `evidence/verification.json` and numbered text logs.

The standalone `terraform plan` is genuinely executed, not substituted with `terraform test`. With `offline_plan=true`, the real AWS provider uses explicit non-secret placeholder credentials and disables credential validation, metadata discovery, account-ID lookup and region validation. The configuration has no data sources and the command uses `-refresh=false` against empty local state, so the recorded plan requires no AWS API lookup. It checks the graph and provider schemas, not AMI availability, permissions, quotas, Docker image availability or deployment success. Do not reuse this method on a directory containing real infrastructure state.

The separate `terraform test` uses `mock_provider "aws"` and plan-only runs. Assertions check host sizing, disk encryption, IMDSv2, application-only ingress and log retention; a negative test rejects unrestricted ingress. These are mock-provider tests, distinct from the standalone plan.

## Variables

| Variable | Purpose/default |
|---|---|
| `project`, `environment` | Names/tags, `document-ai` and `dev` |
| `region` | `eu-west-1` |
| `offline_plan` | `true` for assignment verification; never apply in this mode |
| `ami_id` | Syntactically valid placeholder; real future AMI must be x86_64 Amazon Linux 2023 |
| `instance_type` | `t3.large`; alternatives validated in code |
| `allowed_cidr` | Documentation-only `203.0.113.10/32`; replace with a trusted client's public range in a future deployment |
| `app_image` | Placeholder public image; build and publish the Task 5 Docker image first |
| `openrouter_parameter_arn` | Existing SSM SecureString ARN for the OpenRouter key |
| `api_token_parameter_arn` | Existing SSM SecureString ARN for the application bearer token |
| `disk_gib` | 50; validated integer range 30–200 |

The example file contains no secrets. No secret values are accepted as Terraform variables. `sensitive=true` would only hide display and would not keep a supplied secret out of state; this design uses parameter references instead.

Outputs derive IDs and the endpoint from actual resources. The endpoint remains `(known after apply)` in the offline plan and is not represented as a working URL.

## Future deployment prerequisites

Future deployment would require its own authorization, actual AWS credentials, verified AMI/region, a published image, two existing SecureString parameters in the same region, a trusted CIDR and appropriate TLS ingress. Replace placeholder values and use `offline_plan=false` only for a separately authorized authenticated plan. User data assumes a publicly pullable image; private registries need explicitly designed authentication. Review costs, backup/restore, application health, package installation and model downloads then. None of those steps were performed for this assignment.

## References

- https://registry.terraform.io/providers/hashicorp/aws/5.100.0/docs
- https://developer.hashicorp.com/terraform/language/tests/mocking
- https://developer.hashicorp.com/terraform/cli/commands/plan
