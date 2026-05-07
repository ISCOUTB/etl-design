# TODO: Find a way to use variables here
# Maybe the best way for our case is pass the config when initializing terraform with -backend-config
terraform {
  backend "s3" {
    bucket       = "sloth-terraform-state-staging"
    key          = "swarm-cluster/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}
