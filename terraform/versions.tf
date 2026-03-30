terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
  }

  # Use local state by default to avoid S3 backend bootstrap issues.
  # Optional: to use remote S3 state later, run:
  # terraform init -reconfigure \
  #   -backend-config="bucket=<existing-bucket-name>" \
  #   -backend-config="key=ecommerce-api/dev/terraform.tfstate" \
  #   -backend-config="region=us-east-1" \
  #   -backend-config="encrypt=true"
  backend "local" {
    path = "terraform.tfstate"
  }
}
