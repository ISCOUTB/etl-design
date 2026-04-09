variable "environment" {
  description = "Environment name"
  type        = string
}

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "manager_count" {
  description = "Number of manager nodes"
  type        = number
}

variable "worker_count" {
  description = "Number of worker nodes"
  type        = number
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
}

variable "allowed_ssh_cidr" {
  description = "CIDR block for SSH access"
  type        = list(string)
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}

# ============================ Shared filesystem variables ============================

variable "enable_shared_fs" {
  description = "Enable provisioning of a shared filesystem (EFS) for Swarm workloads"
  type        = bool
  default     = true
}

variable "shared_fs_name" {
  description = "Name prefix for shared filesystem resources"
  type        = string
  default     = "shared-fs"
}

variable "shared_fs_encrypted" {
  description = "Whether EFS should be encrypted at rest"
  type        = bool
  default     = true
}

variable "shared_fs_performance_mode" {
  description = "EFS performance mode"
  type        = string
  default     = "generalPurpose"

  validation {
    condition     = contains(["generalPurpose", "maxIO"], var.shared_fs_performance_mode)
    error_message = "shared_fs_performance_mode must be 'generalPurpose' or 'maxIO'."
  }
}

variable "shared_fs_throughput_mode" {
  description = "EFS throughput mode"
  type        = string
  default     = "bursting"

  validation {
    condition     = contains(["bursting", "provisioned", "elastic"], var.shared_fs_throughput_mode)
    error_message = "shared_fs_throughput_mode must be 'bursting', 'provisioned', or 'elastic'."
  }
}

variable "shared_fs_provisioned_throughput" {
  description = "Provisioned throughput in MiB/s when throughput mode is provisioned"
  type        = number
  default     = null
}

variable "traefik_cert_path" {
  description = "Certificate path for Traefik (must match the path in Ansible inventory template)"
  type        = string
  default     = null
}
