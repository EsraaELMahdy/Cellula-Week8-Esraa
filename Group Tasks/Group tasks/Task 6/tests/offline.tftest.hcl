mock_provider "aws" {}

run "restricted_single_host_plan" {
  command = plan
  assert {
    condition     = aws_instance.app.instance_type == "t3.large"
    error_message = "Host sizing no longer matches the CPU inference design."
  }
  assert {
    condition     = aws_instance.app.root_block_device[0].encrypted
    error_message = "Application disk must be encrypted."
  }
  assert {
    condition     = aws_instance.app.metadata_options[0].http_tokens == "required"
    error_message = "IMDSv2 tokens must be required."
  }
  assert {
    condition     = length(aws_security_group.app.ingress) == 1 && one(aws_security_group.app.ingress).from_port == 8000
    error_message = "Only the application port should accept inbound connections."
  }
  assert {
    condition     = aws_cloudwatch_log_group.app.retention_in_days == 14
    error_message = "Log retention must remain bounded."
  }
}
run "reject_public_ingress" {
  command = plan
  variables { allowed_cidr = "0.0.0.0/0" }
  expect_failures = [var.allowed_cidr]
}
