# ============================================
# Terraform Backend Bootstrap
# ============================================
# This project creates the necessary resources for the Terraform backend
# It runs ONLY ONCE before the main infrastructure is created
#
# To run:
#   cd bootstrap/
#   terraform init
#   terraform apply

provider "aws" {
  region = var.aws_region
}

locals {
  common_tags = {
    Project   = var.project_name
    ManagedBy = "Terraform-Bootstrap"
    Purpose   = "Backend Storage"
  }
}

# ============================================
# S3 Buckets for each environment
# ============================================

resource "aws_s3_bucket" "terraform_state" {
  for_each = toset(var.environments)

  bucket = "${var.project_name}-terraform-state-${each.value}"

  lifecycle {
    prevent_destroy = true
  }

  tags = merge(
    local.common_tags,
    {
      Name        = "${var.project_name}-tf-state-${each.value}"
      Environment = each.value
    }
  )
}

# Versioning for state recovery
resource "aws_s3_bucket_versioning" "terraform_state" {
  for_each = aws_s3_bucket.terraform_state

  bucket = each.value.id

  versioning_configuration {
    status = "Enabled"
  }
}

# State encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  for_each = aws_s3_bucket.terraform_state

  bucket = each.value.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access (security)
resource "aws_s3_bucket_public_access_block" "terraform_state" {
  for_each = aws_s3_bucket.terraform_state

  bucket = each.value.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ============================================
# Outputs
# ============================================

output "s3_bucket_names" {
  description = "Names of the created S3 buckets"
  value = {
    for env, bucket in aws_s3_bucket.terraform_state :
    env => bucket.id
  }
}
