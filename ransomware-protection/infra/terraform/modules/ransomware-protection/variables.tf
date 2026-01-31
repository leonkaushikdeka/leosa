variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
  default     = "ransomware-protection"
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

variable "api_replicas" {
  description = "Number of API replicas"
  type        = number
  default     = 3
}

variable "frontend_replicas" {
  description = "Number of frontend replicas"
  type        = number
  default     = 2
}

variable "enable_aws_provider" {
  description = "Enable AWS cloud provider integration"
  type        = bool
  default     = true
}

variable "enable_azure_provider" {
  description = "Enable Azure cloud provider integration"
  type        = bool
  default     = false
}

variable "enable_gcp_provider" {
  description = "Enable GCP cloud provider integration"
  type        = bool
  default     = false
}
