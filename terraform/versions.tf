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

  backend "s3" {
    bucket  = "ecommerce-api-tfstate-roma-donskoy-2026"
    key     = "ecommerce-api/dev/terraform.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
}
