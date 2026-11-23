locals {
  name = "${var.project}-${var.environment}"
}
resource "aws_vpc" "app" {
  cidr_block           = "10.42.0.0/16"
  enable_dns_hostnames = true
  tags                 = { Name = local.name }
}
resource "aws_subnet" "app" {
  vpc_id                  = aws_vpc.app.id
  cidr_block              = "10.42.1.0/24"
  map_public_ip_on_launch = true
  tags                    = { Name = "${local.name}-public" }
}
resource "aws_internet_gateway" "app" {
  vpc_id = aws_vpc.app.id
}
resource "aws_route_table" "app" {
  vpc_id = aws_vpc.app.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.app.id
  }
}
resource "aws_route_table_association" "app" {
  subnet_id      = aws_subnet.app.id
  route_table_id = aws_route_table.app.id
}
resource "aws_security_group" "app" {
  name_prefix = "${local.name}-"
  description = "Trusted-client application access; no SSH ingress"
  vpc_id      = aws_vpc.app.id
  ingress {
    description = "Private demonstration access; use TLS reverse proxy before public use"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = [var.allowed_cidr]
  }
  egress {
    description = "HTTPS for model downloads, image pulls, SSM, logs and OpenRouter"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    description = "Package repository HTTP redirects during first boot"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
resource "aws_cloudwatch_log_group" "app" {
  name              = "/${local.name}/application"
  retention_in_days = 14
}
resource "aws_iam_role" "app" {
  name = "${local.name}-host"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = "sts:AssumeRole", Principal = { Service = "ec2.amazonaws.com" } }]
  })
}
resource "aws_iam_role_policy" "app" {
  role = aws_iam_role.app.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["ssm:GetParameter"], Resource = [var.openrouter_parameter_arn, var.api_token_parameter_arn] },
      { Effect = "Allow", Action = ["logs:CreateLogStream", "logs:PutLogEvents"], Resource = "${aws_cloudwatch_log_group.app.arn}:*" }
    ]
  })
}
resource "aws_iam_instance_profile" "app" {
  name = "${local.name}-host"
  role = aws_iam_role.app.name
}
resource "aws_instance" "app" {
  ami                         = var.ami_id
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.app.id
  vpc_security_group_ids      = [aws_security_group.app.id]
  iam_instance_profile        = aws_iam_instance_profile.app.name
  associate_public_ip_address = true
  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }
  root_block_device {
    volume_size           = var.disk_gib
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = false
  }
  user_data_replace_on_change = true
  user_data = templatefile("${path.module}/user_data.sh.tftpl", {
    region          = var.region
    app_image       = var.app_image
    key_parameter   = var.openrouter_parameter_arn
    token_parameter = var.api_token_parameter_arn
    log_group       = aws_cloudwatch_log_group.app.name
  })
  depends_on = [aws_route_table_association.app, aws_iam_role_policy.app]
  tags       = { Name = local.name }
}
