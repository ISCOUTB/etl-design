# ============================================
# Module Invocation
# ============================================

locals {
  effective_cert_path = coalesce(var.traefik_cert_path, "/mnt/shared/traefik/${var.environment}")
}

module "swarm_test" {
  source = "../../module/swarm-cluster"

  environment        = var.environment
  project_name       = var.project_name
  manager_count      = var.manager_count
  worker_count       = var.worker_count
  instance_type      = var.instance_type
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
  allowed_ssh_cidr   = var.allowed_ssh_cidr
  tags               = var.tags

  # Shared Filesystem
  traefik_cert_path                = local.effective_cert_path
  enable_shared_fs                 = var.enable_shared_fs
  shared_fs_name                   = var.shared_fs_name
  shared_fs_encrypted              = var.shared_fs_encrypted
  shared_fs_performance_mode       = var.shared_fs_performance_mode
  shared_fs_provisioned_throughput = var.shared_fs_provisioned_throughput
  shared_fs_throughput_mode        = var.shared_fs_throughput_mode
}

# ============================================
# Ansible Provisioning
# ============================================

# Provision Docker on all nodes
resource "null_resource" "ansible_provision_docker" {
  depends_on = [
    module.swarm_test
  ]

  triggers = {
    # Re-run if manager IPs change
    manager_ips = join(",", module.swarm_test.manager_public_ips)
    worker_ips  = join(",", module.swarm_test.worker_public_ips)
    # Re-run if instance count changes
    instance_count = "${var.manager_count}-${var.worker_count}"
  }

  provisioner "local-exec" {
    working_dir = "${path.root}/../../.."
    command     = <<-EOT
      echo "Waiting 60 seconds for instances to be ready..."
      sleep 60
      echo "Installing Docker on all nodes..."
      ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook \
        -i ${module.swarm_test.ansible_inventory} \
        ansible/docker.yml
    EOT
  }

  provisioner "local-exec" {
    when    = destroy
    command = "echo 'Docker provisioner cleanup (if needed)'"
  }
}

# Mount shared FS if needed
resource "null_resource" "ansible_shared_files" {
  depends_on = [
    module.swarm_test,
    null_resource.ansible_provision_docker
  ]

  count = var.enable_shared_fs ? 1 : 0

  triggers = {
    # Re-run if manager IPs change
    manager_ips = join(",", module.swarm_test.manager_public_ips)
    # Re-runn if worker IPs change
    worker_ips = join(",", module.swarm_test.worker_public_ips)
    # Re-run if instance count changes
    instance_count = "${var.manager_count}-${var.worker_count}"
    # Re-run if traefik cert path change
    traefik_cert_path = var.traefik_cert_path
  }

  provisioner "local-exec" {
    working_dir = "${path.root}/../../.."
    command     = <<-EOT
      echo "Mounting shared directories..."
      ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook \
        -i ${module.swarm_test.ansible_inventory} \
        ansible/mount_fs.yml
    EOT
  }
}


# Initialize Docker Swarm cluster
resource "null_resource" "ansible_init_swarm" {
  depends_on = [
    null_resource.ansible_provision_docker
  ]

  triggers = {
    # Re-run if manager IPs change (swarm needs re-init)
    manager_ips = join(",", module.swarm_test.manager_public_ips)
  }

  provisioner "local-exec" {
    working_dir = "${path.root}/../../.."
    command     = <<-EOT
      echo "Initializing Docker Swarm cluster..."
      ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook \
        -i ${module.swarm_test.ansible_inventory} \
        ansible/swarm-init.yml
    EOT
  }

  provisioner "local-exec" {
    when    = destroy
    command = "echo 'Swarm cleanup (nodes will be destroyed)'"
  }
}
