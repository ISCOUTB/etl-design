terraform {
  backend "s3" {
    bucket       = "sloth-terraform-state-production"
    key          = "swarm-cluster/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}
