# Ransomware Protection Platform

AI-Driven Ransomware Protection for Hybrid Clouds

## Overview

A comprehensive, enterprise-grade ransomware detection and response platform designed to protect hybrid cloud environments. The platform leverages advanced AI/ML algorithms for real-time threat detection, automated response mechanisms, and seamless integration with major cloud providers.

## Features

- **Real-time Threat Detection**: AI-powered analysis using ensemble models combining anomaly detection, behavioral analysis, and signature matching
- **Automated Response**: Configurable auto-response actions including host quarantine, network isolation, and process termination
- **Multi-Cloud Support**: Native integration with AWS, Azure, and GCP for hybrid cloud environments
- **Zero Trust Architecture**: Defense-in-depth security model with microsegmentation support
- **Compliance Ready**: Built-in compliance reporting for GDPR, DPDPA, ISO 27001, and SOC2
- **Scalable Architecture**: Microservices design deployed on Kubernetes with horizontal scaling

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + TypeScript)             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   API Gateway (FastAPI)                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │ Auth        │ │ Alerts      │ │ Hosts                   ││
│  │ Endpoints   │ │ Endpoints   │ │ Endpoints               ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │ Events      │ │ Dashboard   │ │ ML Models               ││
│  │ Endpoints   │ │ Endpoints   │ │ Endpoints               ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Event Processing Pipeline                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │ Normalizer  │ │ Threat      │ │ Ransomware              ││
│  │             │ │ Intel       │ │ Detector (ML)           ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
│  ┌─────────────┐ ┌─────────────┐                           │
│  │ Behavior    │ │ Alert       │                           │
│  │ Analyzer    │ │ Generator   │                           │
│  └─────────────┘ └─────────────┘                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Enforcement Engine                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │ Quarantine  │ │ Network     │ │ Cloud Provider          ││
│  │ Host        │ │ Isolation   │ │ Integration             ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │ PostgreSQL  │ │ Redis       │ │ Kafka / Elasticsearch   ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Database**: PostgreSQL (async), Redis
- **Message Queue**: Apache Kafka
- **ML Framework**: PyTorch, scikit-learn, XGBoost

### Frontend
- **Framework**: React 18 with TypeScript
- **State Management**: TanStack Query
- **Styling**: Tailwind CSS
- **Charts**: Recharts

### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Kubernetes
- **IaC**: Terraform
- **Monitoring**: Prometheus, Grafana

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- kubectl configured
- Terraform 1.5+

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ransomware-protection
   ```

2. **Set up the backend**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev,ml]"
   ```

3. **Set up the frontend**
   ```bash
   cd frontend
   npm install
   ```

4. **Configure environment**
   ```bash
   cp config/settings.yaml.example config/settings.yaml
   # Edit config/settings.yaml with your settings
   ```

5. **Start infrastructure services**
   ```bash
   docker-compose up -d
   ```

6. **Run the application**
   ```bash
   # Backend
   uvicorn src.main:app --reload

   # Frontend (in a separate terminal)
   cd frontend
   npm run dev
   ```

### Kubernetes Deployment

```bash
# Apply Kubernetes manifests
kubectl apply -f infra/kubernetes/base/

# Or deploy with Terraform
cd infra/terraform
terraform init
terraform apply
```

## API Documentation

Once the application is running, access the API documentation at:
- Swagger UI: http://localhost:8080/api/docs
- ReDoc: http://localhost:8080/api/redoc

## Configuration

All configuration is managed through `config/settings.yaml`. Key sections:

```yaml
app:
  environment: "development"
  debug: true

database:
  postgres:
    host: "localhost"
    port: 5432

ml:
  detection_threshold: 0.85
  model_type: "ensemble"

detection:
  scan_interval_seconds: 60

response:
  auto_response_enabled: true
```

## Cloud Provider Setup

### AWS
```yaml
cloud_providers:
  aws:
    enabled: true
    region: "ap-south-1"
    access_key: "${AWS_ACCESS_KEY}"
    secret_key: "${AWS_SECRET_KEY}"
```

### Azure
```yaml
cloud_providers:
  azure:
    enabled: true
    tenant_id: "${AZURE_TENANT_ID}"
    client_id: "${AZURE_CLIENT_ID}"
    client_secret: "${AZURE_CLIENT_SECRET}"
```

### GCP
```yaml
cloud_providers:
  gcp:
    enabled: true
    project_id: "${GCP_PROJECT_ID}"
    credentials_path: "${GCP_CREDENTIALS_PATH}"
```

## ML Models

The platform uses an ensemble of three detection models:

1. **Anomaly Detector**: Isolation Forest for detecting unusual patterns
2. **Behavior Analyzer**: XGBoost classifier for process behavior analysis
3. **Signature Detector**: Pattern matching for known ransomware indicators

### Model Training

```bash
python -m src.ml.training.train_models --data data/training/ransomware_samples.csv
```

## Testing

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# End-to-end tests
pytest tests/e2e/ -v

# Run with coverage
pytest --cov=src --cov-report=html
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Security

For security vulnerabilities, please email security@example.com instead of opening a public issue.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, email support@example.com or join our Slack channel.
