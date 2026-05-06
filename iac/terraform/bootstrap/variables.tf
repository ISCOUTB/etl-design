variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "sloth"
}

variable "environments" {
  description = "Environments to create S3 and DynamoDB for"
  type        = list(string)
  default     = ["staging", "production"]
}
