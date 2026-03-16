output "ecr_repository_url" {
  description = "ECR repository URL for FastAPI Docker images"
  value       = aws_ecr_repository.api.repository_url
}

output "eks_cluster_endpoint" {
  description = "EKS cluster API server endpoint"
  value       = aws_eks_cluster.this.endpoint
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.postgres.address
}
