resource "kubernetes_namespace" "this" {
  metadata {
    name = var.namespace
    labels = {
      app.kubernetes.io/name     = "ransomware-protection"
      app.kubernetes.io/version  = "1.0.0"
    }
  }
}

resource "kubernetes_config_map" "config" {
  metadata {
    name      = "ransomware-protection-config"
    namespace = kubernetes_namespace.this.metadata[0].name
  }

  data = {
    APP_NAME                    = "Ransomware Protection Platform"
    APP_VERSION                 = "1.0.0"
    APP_ENVIRONMENT             = "production"
    APP_DEBUG                   = "false"
    APP_HOST                    = "0.0.0.0"
    APP_PORT                    = "8080"
    APP_WORKERS                 = "4"
    APP_LOG_LEVEL               = "INFO"

    DATABASE_HOST               = "ransomware-protection-postgres"
    DATABASE_PORT               = "5432"
    DATABASE_NAME               = "ransomware_protection"
    DATABASE_USERNAME           = "ransomware_protect"

    REDIS_HOST                  = "ransomware-protection-redis"
    REDIS_PORT                  = "6379"
    REDIS_DB                    = "0"

    KAFKA_BOOTSTRAP_SERVERS     = "ransomware-protection-kafka:9092"

    ELASTICSEARCH_HOSTS         = "http://ransomware-protection-elasticsearch:9200"
    ELASTICSEARCH_INDEX         = "ransomware-logs"

    ML_DETECTION_THRESHOLD      = "0.85"
    ML_MODEL_TYPE               = "ensemble"

    SECURITY_RATE_LIMITING_ENABLED = "true"
    SECURITY_REQUESTS_PER_MINUTE   = "100"
    SECURITY_BURST_SIZE            = "20"

    MONITORING_PROMETHEUS_ENABLED  = "true"
    MONITORING_PROMETHEUS_PORT     = "9090"
  }
}

resource "kubernetes_secret" "secrets" {
  metadata {
    name      = "ransomware-protection-secrets"
    namespace = kubernetes_namespace.this.metadata[0].name
  }

  data = {
    postgres-password     = var.postgres_password
    redis-password        = var.redis_password
    jwt-secret-key        = var.jwt_secret_key
    aws-access-key        = var.aws_access_key
    aws-secret-key        = var.aws_secret_key
    azure-tenant-id       = var.azure_tenant_id
    azure-client-id       = var.azure_client_id
    azure-client-secret   = var.azure_client_secret
    gcp-project-id        = var.gcp_project_id
    gcp-credentials-path  = var.gcp_credentials_path
  }

  type = "Opaque"
}

resource "helm_release" "postgres" {
  name       = "ransomware-protection-postgres"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "postgresql"
  version    = "12.x.x"
  namespace  = kubernetes_namespace.this.metadata[0].name

  values = [
    <<-EOT
    auth:
      username: ransomware_protect
      password: ${var.postgres_password}
      database: ransomware_protection
    primary:
      persistence:
        size: 10Gi
    EOT
  ]
}

resource "helm_release" "redis" {
  name       = "ransomware-protection-redis"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "redis"
  version    = "18.x.x"
  namespace  = kubernetes_namespace.this.metadata[0].name

  values = [
    <<-EOT
    auth:
      password: ${var.redis_password}
    master:
      persistence:
        size: 2Gi
    EOT
  ]
}

resource "helm_release" "kafka" {
  name       = "ransomware-protection-kafka"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "kafka"
  version    = "22.x.x"
  namespace  = kubernetes_namespace.this.metadata[0].name

  values = [
    <<-EOT
    persistence:
      size: 20Gi
    replicaCount: 1
    EOT
  ]
}

resource "helm_release" "elasticsearch" {
  name       = "ransomware-protection-elasticsearch"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "elasticsearch"
  version    = "19.x.x"
  namespace  = kubernetes_namespace.this.metadata[0].name

  values = [
    <<-EOT
    persistence:
      size: 20Gi
    master:
      replicaCount: 1
    data:
      replicaCount: 1
    EOT
  ]
}
