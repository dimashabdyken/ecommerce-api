terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Bootstrap note:
  # 1) Create the bucket resource first using: terraform init -backend=false && terraform apply
  # 2) Update bucket name below to match var.tf_state_bucket_name and run terraform init -reconfigure
  backend "s3" {
    bucket  = "ecommerce-api-terraform-state-change-me"
    key     = "ecommerce-api/dev/terraform.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
}
