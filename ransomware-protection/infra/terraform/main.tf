terraform {
  required_version = ">= 1.5.0"

  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.24"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12"
    }
  }

  backend "s3" {
    bucket = "ransomware-protection-terraform-state"
    key    = "state/terraform.tfstate"
    region = "ap-south-1"
  }
}

provider "kubernetes" {
  config_path = "~/.kube/config"
}

provider "helm" {
  kubernetes {
    config_path = "~/.kube/config"
  }
}

module "ransomware_protection" {
  source = "./modules/ransomware-protection"

  namespace              = "ransomware-protection"
  postgres_password      = var.postgres_password
  redis_password         = var.redis_password
  jwt_secret_key         = var.jwt_secret_key
  aws_access_key         = var.aws_access_key
  aws_secret_key         = var.aws_secret_key
  azure_tenant_id        = var.azure_tenant_id
  azure_client_id        = var.azure_client_id
  azure_client_secret    = var.azure_client_secret
  gcp_project_id         = var.gcp_project_id
  gcp_credentials_path   = var.gcp_credentials_path

  api_replicas           = 3
  frontend_replicas      = 2

  enable_aws_provider    = true
  enable_azure_provider  = false
  enable_gcp_provider    = false
}

variable "postgres_password" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
}

variable "redis_password" {
  description = "Redis password"
  type        = string
  sensitive   = true
}

variable "jwt_secret_key" {
  description = "JWT secret key"
  type        = string
  sensitive   = true
}

variable "aws_access_key" {
  description = "AWS access key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "aws_secret_key" {
  description = "AWS secret key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "azure_tenant_id" {
  description = "Azure tenant ID"
  type        = string
  default     = ""
  sensitive   = true
}

variable "azure_client_id" {
  description = "Azure client ID"
  type        = string
  default     = ""
  sensitive   = true
}

variable "azure_client_secret" {
  description = "Azure client secret"
  type        = string
  default     = ""
  sensitive   = true
}

variable "gcp_project_id" {
  description = "GCP project ID"
  type        = string
  default     = ""
}

variable "gcp_credentials_path" {
  description = "Path to GCP credentials file"
  type        = string
  default     = ""
}
